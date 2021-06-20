from discord.ext.commands import Cog
from discord.ext.commands import command
from ..db import db
from datetime import date, datetime, timedelta
from random import randint

class Exp(Cog):
    def __init__(self, bot):
        self.bot=bot

    async def add_msg_xp(self, message, xp):
        db.execute("UPDATE users SET msgXP = msgXP + ?, XPLock = ? WHERE userID = ?", randint(3,5), (datetime.utcnow() + timedelta(seconds=60)).isoformat(), message.author.id)

    async def process_msg_xp(self, message):
        msgxp,xplock = db.record("SELECT msgXP, XPLock FROM users WHERE UserID = ?", message.author.id)

        if datetime.fromisoformat(xplock) < datetime.utcnow():
            await self.add_msg_xp(message, msgxp)

    @Cog.listener()
    async def on_ready(self):
        print("exp cog ready")

    @Cog.listener()
    async def on_message(self, message):
        await self.process_msg_xp(message)





def setup(bot):
    bot.add_cog(Exp(bot))