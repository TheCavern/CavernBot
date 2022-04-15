import random
import re
import gevent
from disco.bot import Plugin
from disco.api.http import Routes

from disco.types.message import MessageEmbed, ActionRow

from datetime import datetime

from CavernBot.models.Suggestions import Suggestion, SuggestionVote
from CavernBot.constants import Constants

from gevent.queue import JoinableQueue

SUGGESTION_RE = re.compile(r"([a-zA-Z]*)_(\d*)")


class Vote:
    suggestion = None
    event = None
    type = None

    def __init__(self, suggestion, event, type):
        self.suggestion = suggestion
        self.event = event
        self.type = type


class SuggestionTypes(object):
    PENDING = 0
    DENIED = 1
    VOTING = 2
    APPROVED = 3
    IMPLEMENTED = 4
    FORCED_DENIED = 5
    FORCED_APPROVED = 6


class SuggestionsPlugin(Plugin):
    def load(self, ctx):

        # Suggestion ID: {voters: [Snowflakes], timer: GEventTimeout}

        self.vote_workers = []
        self.vote_worker_count = 1
        self.vote_queue = JoinableQueue()
        self.is_shutdown = False
        self.is_starting = True

        for workerid in range(self.vote_worker_count):
            self.vote_workers.append(self.spawn(self.VoteWorker))

        self.is_starting = False

        super(SuggestionsPlugin, self).load(ctx)

    def unload(self, ctx):
        self.is_shutdown = True
        for i in range(len(self.vote_workers)):
            self.vote_queue.put(StopIteration)

        gevent.joinall(self.vote_workers, timeout=50, raise_error=False)

        super(SuggestionsPlugin, self).unload(ctx)

    def VoteWorker(self):
        self.log.info("Vote Worker Started.")
        while not self.is_shutdown:
            obj = self.vote_queue.get()
            if obj != StopIteration:
                try:
                    obj.event.reply(type=6)

                    svote, created = SuggestionVote.get_or_create(suggestion_id=obj.suggestion,
                                                                  user_id=obj.event.member.id)

                    if obj.type == "upvote" and svote.vote != 1:
                        svote.vote = 1
                        svote.save()
                    elif svote.vote != -1:
                        svote.vote = -1
                        svote.save()

                finally:
                    gevent.sleep(random.randrange(1, 3))
                    self.vote_queue.task_done()
        self.log.info("Vote Worker Shutting Down.")

    @Plugin.schedule(60)
    def update_vote_workers(self):
        if self.is_shutdown or self.is_starting:
            return
        try:
            for index, worker in enumerate(self.vote_workers):
                if worker.dead:
                    self.vote_workers.pop(index)
                    self.log.info(f"Vote Worker {index} has died :(")

            if len(self.vote_workers) < self.vote_worker_count:
                workers_tospawn = self.vote_worker_count - len(self.vote_workers)
                self.log.info(f"Spawning {workers_tospawn} new vote worker(s)")
                for workid in range(workers_tospawn):
                    self.vote_workers.append(self.spawn(self.VoteWorker))
                    gevent.sleep(random.randrange(1, 2))
        except:
            pass

    @Plugin.schedule(3600)
    def vote_check_schedule(self):
        for suggest in Suggestion.select().where(Suggestion.type == SuggestionTypes.VOTING):
            positive = len(
                SuggestionVote.select().where(SuggestionVote.vote == 1, SuggestionVote.suggestion_id == suggest.id))
            negative = len(
                SuggestionVote.select().where(SuggestionVote.vote == -1, SuggestionVote.suggestion_id == suggest.id))
            total_votes = positive + negative

            if total_votes < 20:
                continue

            if total_votes >= 30 and positive >= int(total_votes * .70):
                suggest.type = SuggestionTypes.APPROVED
                suggest.downvotes = negative
                suggest.upvotes = positive

                self.bot.client.api.channels_messages_delete(Constants.SUGGESTIONS_VOTE_CHANNEL, suggest.message_id)
                user = self.bot.client.api.users_get(suggest.user_id)

                channel = self.bot.client.api.channels_get(Constants.SUGGESTIONS_APPROVED_CHANNEL)

                e = MessageEmbed()
                e.set_footer(text=f"{user}",
                             icon_url=user.get_avatar_url())
                if suggest.example:
                    e.set_image(url=suggest.example)
                e.title = f"ID: {suggest.id} | {suggest.area.title()}"
                e.description = f"{suggest.description}\n\n**__Final Vote Stats__**:\nPositive: **{positive}** (`{'%.2f' % (positive / total_votes * 100)}%`)\nNegative: **{negative}** (`{'%.2f' % (negative / total_votes * 100)}%`) "
                e.timestamp = suggest.created_at.isoformat()

                suggest.save()

                channel.send_message(content="Community Approved", embeds=[e])

            elif total_votes >= 20 and negative >= int(total_votes * .80):
                suggest.type = SuggestionTypes.DENIED
                suggest.downvotes = negative
                suggest.upvotes = positive

                self.bot.client.api.channels_messages_delete(Constants.SUGGESTIONS_VOTE_CHANNEL, suggest.message_id)
                user = self.bot.client.api.users_get(suggest.user_id)

                channel = self.bot.client.api.channels_get(Constants.SUGGESTIONS_DENIED_CHANNEL)

                e = MessageEmbed()
                e.set_footer(text=f"{user}",
                             icon_url=user.get_avatar_url())
                if suggest.example:
                    e.set_image(url=suggest.example)
                e.title = f"ID: {suggest.id} | {suggest.area.title()}"
                e.description = f"{suggest.description}\n\n**__Final Vote Stats__**:\nPositive: **{positive}** (`{'%.2f' % (positive / total_votes * 100)}%`)\nNegative: **{negative}** (`{'%.2f' % (negative / total_votes * 100)}%`) "
                e.timestamp = suggest.created_at.isoformat()

                suggest.save()

                channel.send_message(content="Community Denied", embeds=[e])
            else:
                continue

    def handle_button(self, event, mode, suggestion_id):
        s = Suggestion.get(id=suggestion_id)
        s.approving_moderator = event.member.id

        event.reply(type=6)

        channel = event.guild.channels.get(
            Constants.SUGGESTIONS_DENIED_CHANNEL if mode == 'deny' else Constants.SUGGESTIONS_VOTE_CHANNEL)

        s.type = SuggestionTypes.DENIED if mode == 'deny' else SuggestionTypes.VOTING
        member = event.guild.get_member(s.user_id)
        e = MessageEmbed()
        if mode == 'deny':
            e.set_author(name=f"{member.user}",
                         icon_url=member.user.get_avatar_url())
            e.set_footer(text=f"Denied By: {event.member.user}",
                         icon_url=event.member.user.get_avatar_url())
        else:
            e.set_footer(text=f"{member.user}",
                         icon_url=member.user.get_avatar_url())
            if s.example:
                e.set_image(url=s.example)
        e.title = f"ID: {s.id} | {s.area.title()}"
        e.description = s.description
        e.timestamp = s.created_at.isoformat()

        msg = None
        if mode == 'approve':
            buttons = ActionRow()
            buttons.add_component(custom_id=f"upvote_{s.id}", type=2, label="Upvote", style=3)
            buttons.add_component(custom_id=f"downvote_{s.id}", type=2, label="Downvote", style=4)

            msg = channel.send_message(embeds=[e], components=[buttons])
        else:
            msg = channel.send_message(embeds=[e])

        s.message_id = msg.id
        s.save()

        if mode == 'deny':
            self.bot.client.api.http(Routes.CHANNELS_MESSAGES_MODIFY,
                                     dict(channel=Constants.SUGGESTIONS_PENDING_CHANNEL, message=event.message.id),
                                     json={"components": [], "embeds": [], "allowed_mentions": {"parse": []},
                                           "content": f"**Suggestion** `{s.id}`: Denied by <@{event.member.id}>\nMoved to: https://discord.com/channels/{event.guild.id}/{Constants.SUGGESTIONS_DENIED_CHANNEL}/{msg.id} "
                                           })
            try:
                member.user.open_dm().send_message(f"An update on Suggestion #**{s.id}**:\nIt has been denied.")
            except:
                pass
        else:
            self.bot.client.api.http(Routes.CHANNELS_MESSAGES_MODIFY,
                                     dict(channel=Constants.SUGGESTIONS_PENDING_CHANNEL, message=event.message.id),
                                     json={"components": [], "embeds": [], "allowed_mentions": {"parse": []},
                                           "content": f"**Suggestion** `{s.id}`: Approved by <@{event.member.id}>\nMoved to: https://discord.com/channels/{event.guild.id}/{Constants.SUGGESTIONS_VOTE_CHANNEL}/{msg.id} "
                                           })

    @Plugin.listen('InteractionCreate')
    def vote(self, event):
        # self.vote_queue.put()
        if event.type == 3:
            if hasattr(event.data, 'custom_id'):
                if event.data.custom_id.startswith('upvote_') or event.data.custom_id.startswith('downvote_'):
                    idata = SUGGESTION_RE.findall(event.data.custom_id)
                    mode, id = idata[0][0], int(idata[0][1])

                    self.vote_queue.put(Vote(id, event, mode))

    @Plugin.command('suggestion', '<area:str> <description:str...>')
    def suggestion(self, event, area, description, example):
        s = Suggestion.create(user_id=event.member.id, area=area, description=description)
        e = MessageEmbed()
        e.set_footer(text=event.member.user,
                     icon_url=event.member.user.get_avatar_url())
        e.title = f"ID: {s.id} | {area.title()}"
        e.description = description
        e.timestamp = datetime.utcnow().isoformat()
        if example:
            e.set_image(url=example)
            s.example = example

        channel = event.guild.channels.get(Constants.SUGGESTIONS_PENDING_CHANNEL)

        buttons = ActionRow()
        buttons.add_component(custom_id=f"approve_{s.id}", type=2, label="Approve", style=2, emoji={"name": "✅"})
        buttons.add_component(custom_id=f"deny_{s.id}", type=2, label="Deny", style=2, emoji={"name": "🚫"})

        message = channel.send_message(embeds=[e], components=[buttons])
        s.message_id = message.id
        s.save()

        event.reply(type=4, content=f"Suggestion ID: `{s.id}` has been submitted for review by a moderator!",
                    flags=(1 << 6))

        return

    @Plugin.command('deny', '<id:int> [reason:str...]')
    def cmd_deny(self, event, id, reason=None):

        s = Suggestion.get(id=id)
        s.type = SuggestionTypes.DENIED

        channel = event.guild.channels.get(Constants.SUGGESTIONS_DENIED_CHANNEL)
        member = event.guild.get_member(s.user_id)

        e = MessageEmbed()
        e.set_author(name=f"{member.user.username}#{member.user.discriminator}",
                     icon_url=member.user.get_avatar_url())
        e.set_footer(text=f"Denied By: {event.member.user.username}#{event.member.user.discriminator} | ID: {s.id}",
                     icon_url=event.member.user.get_avatar_url())
        e.title = s.area.title()
        e.description = s.description
        e.timestamp = datetime.utcnow().isoformat()

        denied = channel.send_message(embeds=[e])

        msg = f"**Suggestion** `{s.id}`: Denied by <@{event.member.id}>\nMoved to: https://discord.com/channels/{event.guild.id}/{Constants.SUGGESTIONS_DENIED_CHANNEL}/{denied.id}"
        dm_msg = f"An update on Suggestion #**{s.id}**:\nIt has been denied."

        if reason:
            msg += f"\n**Reason**:\n```{reason}```"
            dm_msg += f"\nReason:\n```{reason}```"

        self.bot.client.api.http(Routes.CHANNELS_MESSAGES_MODIFY,
                                 dict(channel=Constants.SUGGESTIONS_PENDING_CHANNEL, message=s.message_id),
                                 json={"components": [], "embeds": [], "allowed_mentions": {"parse": []},
                                       "content": msg
                                       })

        s.message_id = denied.id
        s.save()

        try:
            member.user.open_dm().send_message(dm_msg)
        except:
            pass

        event.reply(type=4, content=f"Suggestion ID: `{s.id}` has been denied!",
                    flags=(1 << 6))
