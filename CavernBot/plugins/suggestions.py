from disco.bot import Plugin
from disco.api.http import Routes

from disco.types.message import MessageEmbed

from datetime import datetime

from CavernBot.models.Suggestions import Suggestion
from CavernBot.constants import Constants


class SuggestionTypes(object):
    PENDING = 0
    DENIED = 1
    APPROVED = 2
    IMPLEMENTED = 3


class SuggestionsPlugin(Plugin):
    def load(self, ctx):

        # Suggestion ID: {voters: [Snowflakes], timer: GEventTimeout}
        self.vote_cache = {}

        super(SuggestionsPlugin, self).load(ctx)

    def handle_button(self, event, mode, suggestion_id):
        s = Suggestion.get(id=suggestion_id)
        s.approving_moderator = event.member.id
        s.save()

        event.reply(type=6)

        if mode == 'deny':
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
            s.message_id = denied.id
            s.save()

            self.bot.client.api.http(Routes.CHANNELS_MESSAGES_MODIFY,
                                     dict(channel=Constants.SUGGESTIONS_PENDING_CHANNEL, message=event.message.id),
                                     json={"components": [], "embeds": [], "allowed_mentions": {"parse": []},
                                           "content": f"**Suggestion** `{s.id}`: Denied by <@{event.member.id}>\nMoved to: https://discord.com/channels/{event.guild.id}/{Constants.SUGGESTIONS_DENIED_CHANNEL}/{denied.id} "
                                           })

            try:
                member.user.open_dm().send_message(f"An update on Suggestion #**{s.id}**:\nIt has been denied.")
            except:
                pass

    @Plugin.command('suggestion', '<area:str> <description:str...>')
    def suggestion(self, event, area, description, example):
        s = Suggestion.create(user_id=event.member.id, area=area, description=description)
        e = MessageEmbed()
        e.set_footer(text=f"{event.member.user.username}#{event.member.user.discriminator}",
                     icon_url=event.member.user.get_avatar_url())
        e.title = f"ID: {s.id} | {area.title()}"
        e.description = description
        e.timestamp = datetime.utcnow().isoformat()
        if example:
            e.set_image(url=example)

        buttons = [
            {
                "type": 1,
                "components": [
                    {
                        "custom_id": f"approve_{s.id}",
                        "type": 2,
                        "label": "Approve",
                        "style": 2,
                        "emoji": {
                            "name": "✅"
                        }
                    },
                    {
                        "custom_id": f"deny_{s.id}",
                        "type": 2,
                        "label": "Deny",
                        "style": 2,
                        "emoji": {
                            "name": "🚫"
                        }
                    }
                ]
            }
        ]

        message = self.bot.client.api.channels_messages_create(Constants.SUGGESTIONS_PENDING_CHANNEL, embeds=[e],
                                                               components=buttons)
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
