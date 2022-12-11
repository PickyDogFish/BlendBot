from discord.ext.commands import Cog
from discord.ext.commands import command
from ..db import db
from lib.bot import LOG_CHANNEL_ID, WELCOME_CHANNEL_ID

class Welcome(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("welcome cog ready")

    @Cog.listener()
    async def on_member_join(self, member):
        if db.record("SELECT * FROM users WHERE userID = ?", member.id) != None:
            db.execute("UPDATE users SET isInServer = 1 WHERE userID = ?", member.id)
            await self.bot.get_channel(LOG_CHANNEL_ID).send(member.name + "just rejoined the server.")

        db.execute("INSERT OR IGNORE INTO users (UserID) VALUES (?)", member.id)
        await self.bot.get_channel(WELCOME_CHANNEL_ID).send(f"Welcome to **{member.guild.name}** {member.mention}!")

    @Cog.listener()
    async def on_member_remove(self, member):
        #await self.bot.get_channel(855802065737351178).send(f"Sad to see you go {member.mention}!")
        db.execute("UPDATE users SET isInServer = 0 WHERE userID = ?", member.id)

    


async def setup(bot):
    await bot.add_cog(Welcome(bot))