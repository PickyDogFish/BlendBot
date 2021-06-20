from discord.ext.commands import Cog

class Reactions(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("reactions cog ready")

    @Cog.listener()
    #works only if msg is cached, so if the bot was running when the message was sent
    async def on_reaction_add(self, reaction, user):
        pass

    @Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        pass

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        print(f"{payload.member.display_name} reacted with {payload.emoji.name}")

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        pass

def setup(bot):
    bot.add_cog(Reactions(bot))