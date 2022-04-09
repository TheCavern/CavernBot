from disco.bot.command import CommandEvent

from CavernBot.constants import Constants
from CavernBot.database import init_db
from disco.bot import Bot, Plugin


class CorePlugin(Plugin):
    def load(self, ctx):
        # init_db()

        super(CorePlugin, self).load(ctx)

    # Basic command handler
    @Plugin.listen('InteractionCreate')
    def on_interaction_create(self, event):

        command_name = event.data.name

        if command_name == 'suggestion':
            area = None
            description = None
            example = None

            # print(event.raw_data)

            for option in event.raw_data['interaction']['data']['options']:
                if option['name'] == 'area':
                    area = option['value']
                if option['name'] == 'description':
                    description = option['value']

            data = event.raw_data['interaction']['data']
            if data.get('resolved'):
                for k in data['resolved']['attachments']:
                    example = data['resolved']['attachments'][k]['url']
                    break

            self.bot.plugins['SuggestionsPlugin'].commands[0].func(event, area, description, example)
            # content = f"Area: {area}\nDescription: {description}"
            #
            # self.bot.client.api.interactions_create(event.id, event.token, 4, {"content": content})

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
