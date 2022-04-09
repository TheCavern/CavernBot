from disco.bot import Plugin


class SuggestionsPlugin(Plugin):
    def load(self, ctx):
        super(SuggestionsPlugin, self).load(ctx)

    @Plugin.command('suggestion', '<area:str> <description:str...>')
    def suggestion(self, event, area, description):
        pass
