from disco.bot import Plugin


class TicketsPlugin(Plugin):
    def load(self, ctx):
        super(TicketsPlugin, self).load(ctx)

    @Plugin.command('test')
    def simp(self):
        pass
