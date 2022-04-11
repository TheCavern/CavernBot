import re
from disco.bot.command import CommandEvent

from CavernBot.constants import Constants
from disco.bot import Bot, Plugin

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

            self.bot.plugins['SuggestionsPlugin'].commands[0].func(event, area, description, example)

        # # Grab the list of commands
        # commands = list(self.bot.get_commands_for_message(
        #     False, {}, guild.prefix, event.message
        # ))
        #
        # # Sorry, nothing to see here :C
        # if not len(commands):
        #     return
        #
        # for command, match in commands:
        #
        #     if command.name == 'settings' and len(commands) > 1:
        #         continue
        #
        #     needed_level = 0
        #     if command.level:
        #         needed_level = command.level
        #
        #     cooldown = 0
        #
        #     if hasattr(command.plugin, 'game'):
        #         if not guild.check_if_listed(game_checker(command.plugin.game), 'enabled'):
        #             return
        #
        #     if command.level == -1 and not event.bot_admin:
        #         return
        #
        #     if not event.bot_admin and event.user_level < needed_level:
        #         continue
        #
        #     try:
        #         command_event = CommandEvent(command, event.message, match)
        #         command_event.bot_admin = event.bot_admin
        #         command_event.user_level = event.user_level
        #         command_event.db_user = user_obj
        #         command_event.db_guild = guild
        #         if command.args:
        #             if len(command_event.args) < command.args.required_length:
        #                 self.dis_cmd_help(command, command_event, event, guild)
        #                 return
        #         command.plugin.execute(command_event)
        #     except:
        #         self.log.exception('Command error:')
        #         return event.reply('It seems that an error has occured! :(')
        # if new_setup:
        #     event.message.reply(
        #         'Hey! I\'ve noticed that I\'m new to the server and have no config, please check out `{}settings` to edit and setup the bot.'.format(
        #             guild.prefix))
        return
