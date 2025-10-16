import random

import gevent
from disco.api.http import APIException
from disco.bot import Plugin
from disco.types.application import InteractionType, InteractionCallbackType
from disco.types.base import snowflake

from disco.types.message import ActionRow, SelectOption, SelectMenuComponent, \
    TextDisplayComponent, MessageFlags, \
    ContainerComponent, ButtonComponent, ButtonStyles

from CavernBot.models import datetime_utc
from CavernBot.models.Suggestions import Suggestion, SuggestionVote
from CavernBot.constants import Constants, cfg, send_you_dont_have_the_right, SuggestionStatus

from gevent.queue import JoinableQueue

from CavernBot.utils.components import suggestion_info_ui_suggestion, suggestion_info_ui_user, pending_suggestion, \
    separator_large, separator_small, suggestion_create_modal, community_voting_suggestion, suggestion_deny, \
    suggestion_denied_user_message, suggestion_community_voting_complete, force_update_suggestion
from CavernBot.utils.graphs import suggestion_stats, suggestion_user_stats

def suggestion_type_to_channel(suggestion_type):
    channel_mappings = {
        SuggestionStatus.PENDING: cfg.discord.suggestions.pending_channel,
        SuggestionStatus.DENIED: cfg.discord.suggestions.denied_channel,
        SuggestionStatus.VOTING: cfg.discord.suggestions.vote_channel,
        SuggestionStatus.APPROVED: cfg.discord.suggestions.approved_channel,
        SuggestionStatus.COMMUNITY_DENIED: cfg.discord.suggestions.denied_channel,
        SuggestionStatus.IMPLEMENTED: cfg.discord.suggestions.implemented_channel,
        SuggestionStatus.FORCED_DENIED: cfg.discord.suggestions.denied_channel,
        SuggestionStatus.FORCED_APPROVED: cfg.discord.suggestions.approved_channel,
        SuggestionStatus.NOT_IMPLEMENTING: cfg.discord.suggestions.not_implementing_channel,
        SuggestionStatus.WORK_IN_PROGRESS: cfg.discord.suggestions.wip_channel,
    }

    return channel_mappings.get(suggestion_type, None)

class Vote:
    suggestion = None
    event = None
    type = None

    def __init__(self, suggestion, event, type):
        self.suggestion = suggestion
        self.event = event
        self.type = type


def check_user(user):
    if user.id in Constants.SUGGESTIONS_SINFO_PERMISSIONS:
        return True

    return False

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

    def update_suggestion_message(self, event, suggestion, new_status, old_status):
        outcome = "Approved" if new_status in [SuggestionStatus.FORCED_APPROVED, SuggestionStatus.IMPLEMENTED,
                                               SuggestionStatus.WORK_IN_PROGRESS] else "Rejected"

        user = self.client.api.users_get(suggestion.user_id)
        components = suggestion_community_voting_complete(suggestion, user, outcome=outcome, old_status=old_status,
                                                          event=event)
        channel_id, message_id = suggestion.message.split("/")

        vote_graph = suggestion_stats(suggestion_id=suggestion.id)

        # What if someone updated their config? Cool, it'll just not update, and go to the else statement
        if (suggestion_type_to_channel(new_status) == suggestion_type_to_channel(old_status)) and snowflake(channel_id) == suggestion_type_to_channel(new_status):
            event.reply(type=InteractionCallbackType.UPDATE_MESSAGE, components=components,
                        attachments = [(f"final_graph_{suggestion.id}.png", vote_graph.getvalue())], flags=MessageFlags.IS_COMPONENTS_V2)

            vote_graph.close()
            return None

        else:
            event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, content=f"Suggestion `{suggestion.id}` Has been updated!", flags=MessageFlags.EPHEMERAL)
            # Delete the old message
            self.client.api.channels_messages_delete(channel_id, message_id)
            # Grab new channel
            new_channel = suggestion_type_to_channel(new_status)
            # Send new message

            vote_graph = suggestion_stats(suggestion_id=suggestion.id)

            new_message = self.client.api.channels_messages_create(new_channel, components=components,
                                                                   attachments = [(f"final_graph_{suggestion.id}.png", vote_graph.getvalue())], flags=MessageFlags.IS_COMPONENTS_V2)

            # Close buffer
            vote_graph.close()
            # Update suggestion's message in DB
            suggestion.message = f"{new_message.channel.id}/{new_message.id}"
            suggestion.save()

            return None

    # Workers Schedule
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

    @Plugin.schedule(3600, init=False)
    def vote_check_schedule(self):
        for suggest in Suggestion.select().where(Suggestion.status == SuggestionStatus.VOTING):
            positive = len(
                SuggestionVote.select().where(SuggestionVote.vote == 1, SuggestionVote.suggestion_id == suggest.id))
            negative = len(
                SuggestionVote.select().where(SuggestionVote.vote == -1, SuggestionVote.suggestion_id == suggest.id))
            total_votes = positive + negative

            if total_votes < 40:
                continue

            try:
                channel_id, message_id = suggest.message
            except:
                continue

            self.bot.client.api.channels_messages_delete(channel_id, message_id)
            user = self.bot.client.api.users_get(suggest.user_id)

            if total_votes >= 60 and positive >= int(total_votes * .70):
                suggest.status = SuggestionStatus.APPROVED

                channel = self.bot.client.api.channels_get(Constants.SUGGESTIONS_APPROVED_CHANNEL)

                components = suggestion_community_voting_complete(suggest, user)

                vote_graph = suggestion_stats(suggestion_id=suggest.id)

                new_message = channel.send_message(components=components, flags=MessageFlags.IS_COMPONENTS_V2, attachments=[(f"final_graph_{suggest.id}.png", vote_graph.getvalue())])

                suggest.message = f"{new_message.channel.id}/{new_message.id}"
                suggest.save()

            elif total_votes >= 40 and negative >= int(total_votes * .80):
                suggest.status = SuggestionStatus.DENIED

                channel = self.bot.client.api.channels_get(Constants.SUGGESTIONS_DENIED_CHANNEL)

                components = suggestion_community_voting_complete(suggest, user, outcome="Denied")

                vote_graph = suggestion_stats(suggestion_id=suggest.id)

                new_message = channel.send_message(components=components, flags=MessageFlags.IS_COMPONENTS_V2,
                                                   attachments=[
                                                       (f"final_graph_{suggest.id}.png", vote_graph.getvalue())])

                suggest.message = f"{new_message.channel.id}/{new_message.id}"
                suggest.save()

            else:
                continue


    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.MESSAGE_COMPONENT and "_" in e.data.custom_id and e.data.custom_id.split("_")[0] in ["upvote", "downvote"])
    def on_voting_button(self, event):
        # Get whether we are upvoting or downvoting, and then getting the suggestion ID.
        data = event.data.custom_id.split("_")

        # Throw the issue at the queue worker :). Thanks Nadle! ~Justin
        self.vote_queue.put(Vote(data[1], event, data[0]))

    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.APPLICATION_COMMAND and e.data.name == "suggestion")
    def base_suggestion_command(self, event):

        match event.data.options[0].name:
            case "info":
                root_command = event.data.options[0]


                if len(root_command.options) > 1:
                    return event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, content="`ERROR` You may not supply both a suggestion id and user.", flags=MessageFlags.EPHEMERAL)

                if not len(root_command.options):
                    option = "user"
                    value = event.member.id
                else:
                    option = root_command.options[0].name
                    value = root_command.options[0].value

                has_info_permissions_by_role = (len(set(event.member.roles) & set(
                    Constants.SUGGESTIONS_SINFO_PERMISSIONS)) > 0)

                has_info_permissions_by_user = (event.member.id in Constants.SUGGESTIONS_SINFO_PERMISSIONS)

                match option:
                    case "suggestion":
                        s = Suggestion.get_or_none(id=value)
                        if not s:
                            return event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, content=f"`ERROR`: Suggestion ID `{value}` does not exist.", flags=MessageFlags.EPHEMERAL)

                        if s.user_id != event.member.id and not has_info_permissions_by_role and not has_info_permissions_by_user:
                            return send_you_dont_have_the_right(event)

                        stats_graph_buffer = suggestion_stats(suggestion_id=s)
                        components = suggestion_info_ui_suggestion(event, s, self.bot.client.api.users_get(s.user_id))

                        event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, components=components, attachments=[(f"stats_{s.id}.png", stats_graph_buffer.getvalue())], flags=(MessageFlags.IS_COMPONENTS_V2 ^ MessageFlags.EPHEMERAL))

                        stats_graph_buffer.close()

                        return None
                    case "user":
                        if value != event.member.id and not has_info_permissions_by_role and not has_info_permissions_by_user:
                            return send_you_dont_have_the_right(event)

                        user_vote_stats = suggestion_stats(user_id=value)
                        user_stats = suggestion_user_stats(user_id=value)
                        components = suggestion_info_ui_user(event, self.bot.client.api.users_get(value))

                        event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, components=components,
                                    attachments=[(f"suggestion_stats_{value}.png", user_stats.getvalue()), (f"vote_stats_{value}.png", user_vote_stats.getvalue())],
                                    flags=(MessageFlags.IS_COMPONENTS_V2 ^ MessageFlags.EPHEMERAL))

                        user_vote_stats.close()
                        user_stats.close()

                        return None


            case "create":

                if Constants.SUGGESTIONS_BANNED_ROLE in event.member.roles:
                    return send_you_dont_have_the_right(event, reason="`ERROR`: You're suggestion banned.")

                if not cfg.discord.suggestions.allow_new:
                    return send_you_dont_have_the_right(event, reason="**New suggestions are currently disabled.**")

                modal = suggestion_create_modal(event)

                return event.reply(type=InteractionCallbackType.MODAL, modal=modal)
        return None

    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.APPLICATION_COMMAND and e.data.name == "deny")
    def suggestion_deny_command(self, event):

        suggestion = Suggestion.get_or_none(id=event.data.options[0].value)
        reason = None
        if len(event.data.options) == 2:
            reason = event.data.options[1].value

        if suggestion is None or suggestion.status != SuggestionStatus.PENDING:
            return event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, content=f"`ERROR` Suggestion `{event.data.options[0].value}` does not exist, or has already been reviewed.", flags=MessageFlags.EPHEMERAL)

        return self.update_pending_suggestion(event, from_command=True, suggestion=suggestion, next_step="deny", reason=reason)



    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.APPLICATION_COMMAND and e.data.name == "approve")
    def suggestion_approve_command(self, event):
        suggestion = Suggestion.get_or_none(id=event.data.options[0].value)

        if suggestion is None or suggestion.status != SuggestionStatus.PENDING:
            return event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                               content=f"`ERROR` Suggestion `{event.data.options[0].value}` does not exist, or has already been reviewed.", flags=MessageFlags.EPHEMERAL)

        return self.update_pending_suggestion(event, from_command=True, suggestion=suggestion, next_step="approve")

    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.MODAL_SUBMIT and e.data.custom_id == "suggestion_modal")
    def suggestion_modal_submit(self, event):

        category = event.data.components[1].component.values[0]
        suggestion_body = event.data.components[2].component.value

        if Constants.MASKED_LINKS_RE.match(suggestion_body):
            suggestion_body = Constants.MASKED_LINKS_RE.sub(suggestion_body, "`*FILTERED*`")

        select_options = [
        ]

        category_config = [cat for cat in cfg.discord.suggestions.categories if cat.get("value") == category][0]

        option = SelectOption(label=category_config.get("name"), value=category_config.get("value"), default=True)
        if category_config.get("emote"):
            matches = Constants.EMOJI_RE.match(category_config.get("emote"))
            if matches:
                option.emoji = {
                    "id": matches.group(3),
                    "name": matches.group(2),
                    "animated": matches.group(1)
                }
            else:
                option.emoji = {
                    "name": category_config.get("emote")
                }

        select_options.append(option)

        category_menu = SelectMenuComponent(custom_id="category_menu", required=False, disabled=True)
        category_menu.options = select_options

        container = ContainerComponent()
        container.components = [
            ActionRow(
                components=[
                    category_menu
                ]
            ),
            separator_small,
            TextDisplayComponent(content=suggestion_body)
        ]

        components = [
            TextDisplayComponent(content=f"# Review Your Suggestion"),
            separator_large,
            container,
            ActionRow(
                components=[
                    ButtonComponent(style=ButtonStyles.SUCCESS, label="Confirm", custom_id=f"suggestion_setup_confirm"),
                    ButtonComponent(style=ButtonStyles.DANGER, label="Deny", custom_id=f"suggestion_setup_deny"),
                ]
            ),
        ]

        return event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, components=components, flags=(MessageFlags.EPHEMERAL ^ MessageFlags.IS_COMPONENTS_V2))

    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.MESSAGE_COMPONENT and e.data.custom_id.startswith("suggestion_setup"))
    def suggestion_setup(self, event):

        part = event.data.custom_id.replace("suggestion_setup_", "")

        container = event.message.components[2]

        selected_category = container.components[0].components[0].options[0].value
        body = container.components[2].content

        match part:
            case "confirm":

                suggestion = Suggestion.create(user_id=event.member.id, category=selected_category, description=body)

                components = pending_suggestion(event, suggestion)

                message = self.client.api.channels_messages_create(Constants.SUGGESTIONS_PENDING_CHANNEL, components=components,
                                                                   flags=MessageFlags.IS_COMPONENTS_V2)

                suggestion.message = f"{message.channel.id}/{message.id}"

                suggestion.save()

                event.reply(type=6)
                event.edit(components=[TextDisplayComponent(content=f"Suggestion `{suggestion.id}` successfully submitted!")])

                return None

            case "deny":
                container = event.message.components[2]

                selected_category = container.components[0].components[0].options[0].value
                body = container.components[2].content

                modal = suggestion_create_modal(event, body=body, selected_category=selected_category)

                return event.reply(type=InteractionCallbackType.MODAL, modal=modal)
        return None

    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.MESSAGE_COMPONENT and e.data.custom_id.startswith("update_pending_"))
    def update_pending_suggestion(self, event, from_command=False, suggestion=None, next_step=None, reason=None):

        suggestion = suggestion or Suggestion.get_or_none(int(event.data.custom_id.replace("update_pending_", "")))
        next_step = next_step or event.data.values[0]

        channel_id, smessage = suggestion.message.split("/")

        pending_message = self.client.api.channels_messages_get(channel_id, smessage)

        if not suggestion:
            return

        match next_step:
            case "approve":
                suggestion.status = SuggestionStatus.VOTING
                suggestion.reviewing_moderator = event.member.id

                components = community_voting_suggestion(event, suggestion, self.bot.client.api.users_get(suggestion.user_id))

                message = self.client.api.channels_messages_create(Constants.SUGGESTIONS_VOTE_CHANNEL, components=components, flags=MessageFlags.IS_COMPONENTS_V2)

                message.start_thread(f"Suggestion {suggestion.id} Thread")

                suggestion.message = f"{message.channel.id}/{message.id}"

                suggestion.save()

                event.reply(type=InteractionCallbackType.DEFERRED_UPDATE_MESSAGE)

                return pending_message.delete()

            case "deny":
                suggestion.status = SuggestionStatus.DENIED
                suggestion.reviewing_moderator = event.member.id

                user = self.client.api.users_get(suggestion.user_id)

                components = suggestion_deny(event, suggestion, user)

                message = self.client.api.channels_messages_create(Constants.SUGGESTIONS_DENIED_CHANNEL, components=components,
                                                                   flags=MessageFlags.IS_COMPONENTS_V2)

                suggestion.message = f"{message.channel.id}/{message.id}"

                suggestion.save()

                if event.type == InteractionType.MESSAGE_COMPONENT:
                    event.reply(type=InteractionCallbackType.DEFERRED_UPDATE_MESSAGE)
                else:
                    event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, content=f"Suggestion {suggestion.id} successfully denied!", flags=MessageFlags.EPHEMERAL)

                pending_message.delete()

                try:
                    user.open_dm().send_message(components=suggestion_denied_user_message(suggestion, reason=reason), flags=MessageFlags.IS_COMPONENTS_V2)
                except APIException as e:
                    self.log.info(f"[Suggestion {suggestion.id}] Unable to DM {user.username} ({user.id}) about suggestion denial.")

                return None

    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.MESSAGE_COMPONENT and e.data.custom_id.startswith("update_approved_"))
    def on_approved_suggestion_menu(self, event):

        depr_to_new = {
            "cm_approved": SuggestionStatus.APPROVED,
            "implemented": SuggestionStatus.IMPLEMENTED,
            "wip": SuggestionStatus.WORK_IN_PROGRESS,
            "wni": SuggestionStatus.NOT_IMPLEMENTING,
        }

        is_staff = (len(set(event.member.roles) & set(
            Constants.STAFF_ROLES)) > 0)

        if not is_staff:
            return send_you_dont_have_the_right(event)

        suggestion = Suggestion.get_or_none(int(event.data.custom_id.replace("update_approved_", "")))
        old_status = suggestion.status

        try:
            new_status = int(event.data.values[0])
        except Exception:
            new_status = depr_to_new[event.data.values[0]]

        if not suggestion:
            event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, content="`ERROR`: Suggestion not found?", flags=MessageFlags.EPHEMERAL)

        if new_status == suggestion.status:
            return event.reply(type=InteractionCallbackType.DEFERRED_UPDATE_MESSAGE)
        else:
            suggestion.status = new_status
            suggestion.updated_by = event.member.id
            suggestion.updated_at = datetime_utc()
            suggestion.save()

            user = self.client.api.users_get(suggestion.user_id)
            return self.update_suggestion_message(event, suggestion, new_status, old_status)
            # components = suggestion_community_voting_complete(suggestion, user, outcome="Approved", old_status=old_status, event=event)
            #
            # return event.reply(type=InteractionCallbackType.UPDATE_MESSAGE, components=components, flags=MessageFlags.IS_COMPONENTS_V2)

    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.APPLICATION_COMMAND and e.data.name == "Update Suggestion")
    def force_update_suggestion(self, event):

        is_staff = (len(set(event.member.roles) & set(
            Constants.STAFF_ROLES)) > 0)

        if not is_staff:
            return send_you_dont_have_the_right(event)

        suggestion_message = list(event.data.resolved.messages.values())[0]

        search_query = f"{suggestion_message.channel_id}/{suggestion_message.id}"

        suggestion = Suggestion.get_or_none(message=search_query)

        if not suggestion:
            return event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, content="`ERROR`: No suggestion found linked to this message.", flags=MessageFlags.EPHEMERAL)

        return event.reply(type=InteractionCallbackType.MODAL, modal=force_update_suggestion(suggestion))

    @Plugin.listen("InteractionCreate", conditional=lambda e: e.type == InteractionType.MODAL_SUBMIT and e.data.custom_id.startswith("force_update_suggestion_"))
    def force_update_suggestion_modal(self, event):

        is_staff = (len(set(event.member.roles) & set(
            Constants.STAFF_ROLES)) > 0)

        if not is_staff:
            return send_you_dont_have_the_right(event)

        try:
            suggestion_id = int(event.data.custom_id.replace("force_update_suggestion_", ""))
        except ValueError:
            self.log.error(f"Unable to determine Suggestion ID from modal custom ID: {event.data.custom_id}")
            return event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                        flags=MessageFlags.EPHEMERAL, content=f"`ERROR`: No suggestion found with id `{event.data.custom_id}`.",)

        suggestion = Suggestion.get_or_none(id=suggestion_id)

        if not suggestion:
            event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                        flags=MessageFlags.EPHEMERAL, content=f"`ERROR`: No suggestion found with id `{suggestion_id}`.",)


        new_status = event.data.components[0].component.values[0]
        old_status = suggestion.status

        if new_status == suggestion.status:
            return event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                        flags=MessageFlags.EPHEMERAL, content=f"`ERROR`: Status selected is the same as current status.")

        suggestion.status = new_status
        suggestion.updated_by = event.member.id
        suggestion.updated_at = datetime_utc()
        suggestion.save()

        return self.update_suggestion_message(event, suggestion, new_status, old_status)