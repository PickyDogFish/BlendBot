from discord.ext.commands import Cog
from discord.ext.commands import command
from ..db import db

class Welcome(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("welcome cog ready")

    @Cog.listener()
    async def on_member_join(self, member):
        db.execute("INSERT OR IGNORE INTO users (UserID) VALUES (?)", member.id)
        await self.bot.get_channel(855802065737351178).send(f"Welcome to **{member.guild.name}** {member.mention}!")

    async def on_member_remove(self, member):
        await self.bot.get_channel(855802065737351178).send(f"Sad to see you go {member.mention}!")

    


def setup(bot):
    bot.add_cog(Welcome(bot))