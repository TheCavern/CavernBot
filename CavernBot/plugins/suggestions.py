from disco.bot import Plugin

from disco.types.message import MessageEmbed

from datetime import datetime


class SuggestionsPlugin(Plugin):
    def load(self, ctx):
        super(SuggestionsPlugin, self).load(ctx)

    @Plugin.command('suggestion', '<area:str> <description:str...>')
    def suggestion(self, event, area, description, example):
        e = MessageEmbed()
        e.set_author(name=f"{event.member.user.username}#{event.member.user.discriminator}",
                     icon_url=event.member.user.get_avatar_url())
        e.title = area.title()
        e.description = description
        e.timestamp = datetime.utcnow().isoformat()
        if example:
            e.set_image(url=example)

        self.bot.client.api.interactions_create(event.id, event.token, 4,
                                                {
                                                    "embeds": [e.to_dict()],
                                                    "components": [
                                                        {
                                                            "type": 1,
                                                            "components": [
                                                                {
                                                                    "custom_id": "approve",
                                                                    "type": 2,
                                                                    "label": "Approve",
                                                                    "style": 1
                                                                },
                                                                {
                                                                    "custom_id": "deny",
                                                                    "type": 2,
                                                                    "label": "Deny",
                                                                    "style": 4
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                                )

        return
