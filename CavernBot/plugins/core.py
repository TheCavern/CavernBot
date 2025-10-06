import re

import yaml
from disco.bot import Plugin
from disco.gateway.events import MessageCreate
from disco.types.application import ApplicationCommandTypes
from dotenv import load_dotenv

from CavernBot.constants import Constants, cfg

SUGGESTION_RE = re.compile(r"([a-zA-Z]*)_(\d*)")


class CorePlugin(Plugin):
    def load(self, ctx):

        # Load all env variables.
        load_dotenv()

        super(CorePlugin, self).load(ctx)

    @Plugin.listen("Ready")
    def on_ready(self, event):
        self.log.info(f"Logged into discord as {self.bot.client.state.me}")

        if cfg.skip_command_registration:
            self.log.info("Skipping command registration due to config value being set.")

        # Register all commands globally.
        with open("./config/commands.yaml", "r", encoding="utf-8") as raw_command_yaml:
            raw_commands = yaml.safe_load(raw_command_yaml)

        to_register = []
        for global_type, global_type_commands in raw_commands['commands']['global'].items():
            if len(global_type_commands):
                self.log.info(f"Found {len(global_type_commands)} {global_type} command(s) to register...")
                for command in global_type_commands:
                    command["type"] = getattr(ApplicationCommandTypes, global_type.upper())
                    to_register.append(command)

        self.log.info(f"Attempting to register {len(to_register)} commands...")

        updated_commands = self.client.api.applications_global_commands_bulk_overwrite(to_register)
        self.log.info(f"Successfully Registered {len(updated_commands)} commands!")


    # Listener for media only channel
    @Plugin.listen('MessageCreate')
    def media_channel(self, event: MessageCreate):
        if event.channel.id != Constants.MEDIA_CHANNEL:
            return
        if hasattr(event.message, 'attachments') and len(event.message.attachments) > 0:
            return
        event.message.delete()
