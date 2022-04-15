import re
from disco.bot import Bot, Plugin

from CavernBot.constants import Constants

SUGGESTION_RE = re.compile(r"([a-zA-Z]*)_(\d*)")


class CorePlugin(Plugin):
    def load(self, ctx):
        super(CorePlugin, self).load(ctx)

    # Basic command handler
    @Plugin.listen('InteractionCreate')
    def on_interaction_create(self, event):

        if event.type == 3:
            if hasattr(event.data, 'custom_id'):
                if event.data.custom_id.startswith('deny_') or event.data.custom_id.startswith('approve_'):
                    idata = SUGGESTION_RE.findall(event.data.custom_id)
                    mode, id = idata[0][0], int(idata[0][1])

                    self.bot.plugins['SuggestionsPlugin'].handle_button(event, mode, id)

        command_name = event.data.name

        if command_name == 'deny':
            sid = None
            reason = None

            for option in event.data.options:
                if option.name == 'id':
                    sid = option.value
                if option.name == 'reason':
                    reason = option.value

            cmd = next((cmd for cmd in self.bot.plugins['SuggestionsPlugin'].commands if cmd.name == command_name),
                       None)
            cmd.func(event, sid, reason=reason)

        if command_name == 'suggestion':
            area = None
            description = None
            example = None

            for option in event.data.options:
                if option.name == 'area':
                    area = option.value
                if option.name == 'description':
                    description = option.value

            if hasattr(event.data, 'resolved') and hasattr(event.data.resolved, 'attachments'):
                for k in event.data.resolved.attachments:
                    example = event.data.resolved.attachments.get(k).url
                    break

            cmd = next((cmd for cmd in self.bot.plugins['SuggestionsPlugin'].commands if cmd.name == command_name),
                       None)
            cmd.func(event, area, description, example)

        if command_name == 'sinfo':

            id = None
            user = None
            has_perms = None

            for x in Constants.SUGGESTIONS_SINFO_PERMISSIONS:
                if x in event.member.roles:
                    has_perms = True
                if event.member.user.id == x:
                    has_perms = True

            for option in event.data.options:
                if option.name == 'id':
                    id = option.value
                if option.name == 'user':
                    user = event.data.resolved.users.get(option.value)

            if id == None and user == None:
                user = event.member.user

            if id != None and user != None:
                event.reply(type=4, content=f"You may not specify both a Suggestion ID and a User to search.",
                            flags=(1 << 6))
                return

            if not has_perms and user != None and user != event.member.user:
                event.reply(type=4, content="**Error**: Permission Denied.",
                            flags=(1 << 6))
                return

            cmd = next(
                (cmd for cmd in self.bot.plugins['SuggestionsPlugin'].commands if cmd.name == command_name),
                None)

            cmd.func(event, id, user, perms=has_perms)

        return
