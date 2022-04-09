from disco.bot import Bot, Plugin

from CavernBot.constants import Constants

class CorePlugin(Plugin):
    def load(self, ctx):
        init_db()

        super(CorePlugin, self).load(ctx)

    # Basic command handler
    @Plugin.listen('InteractionCreate')
    def on_interaction_create(self, event):

        if event.message.channel.type == ChannelType.DM:
            return

        if event.message.author.bot:
            return

        user_obj, created = Users.get_or_create(id=event.message.author.id)

        perms = event.message.channel.get_permissions(self.state.me)

        if not perms.can(Permissions.SEND_MESSAGES):
            return

        event.bot_admin = event.message.author.id in TEMP_BOT_ADMINS
        event.user_level = 0

        has_admin = False

        new_setup = False
        guild = None

        if event.message.guild:
            try:
                guild = Guild.using_id(event.guild.id)
            except Guild.DoesNotExist:
                guild = self.fresh_start(event, event.guild.id)
                new_setup = True
            if len(event.message.member.roles) > 0:
                for x in event.message.member.roles:
                    role = event.message.guild.roles.get(x)
                    if role.permissions.can(Permissions.ADMINISTRATOR):
                        event.user_level = 100
                        has_admin = True
            if guild.referee_role:
                if not has_admin and guild.referee_role in event.message.member.roles:
                    event.user_level = 50

        if event.message.author.bot:
            return

        if not event.message.content.startswith(
                guild.prefix) and event.message.mentions and self.state.me.id in event.message.mentions:
            content = event.message.without_mentions
            content = content.replace(' ', '', -1)
            if 'prefix' in content.lower():
                return event.channel.send_message('Prefix: `{}`'.format(
                    guild.prefix
                ))
            else:
                pass

        # Grab the list of commands
        commands = list(self.bot.get_commands_for_message(
            False, {}, guild.prefix, event.message
        ))

        # Used for cmd cooldowns
        user_ignores_cooldowns = self.cooldown_check(event.message.author.id)

        # Sorry, nothing to see here :C
        if not len(commands):
            return

        for command, match in commands:

            if command.name == 'settings' and len(commands) > 1:
                continue

            needed_level = 0
            if command.level:
                needed_level = command.level

            cooldown = 0

            if hasattr(command.plugin, 'game'):
                if not guild.check_if_listed(game_checker(command.plugin.game), 'enabled'):
                    return

            if command.level == -1 and not event.bot_admin:
                return

            if not event.bot_admin and event.user_level < needed_level:
                continue

            try:
                command_event = CommandEvent(command, event.message, match)
                command_event.bot_admin = event.bot_admin
                command_event.user_level = event.user_level
                command_event.db_user = user_obj
                command_event.db_guild = guild
                if command.args:
                    if len(command_event.args) < command.args.required_length:
                        self.dis_cmd_help(command, command_event, event, guild)
                        return
                command.plugin.execute(command_event)
            except:
                self.log.exception('Command error:')
                return event.reply('It seems that an error has occured! :(')
        if new_setup:
            event.message.reply(
                'Hey! I\'ve noticed that I\'m new to the server and have no config, please check out `{}settings` to edit and setup the bot.'.format(
                    guild.prefix))
        return