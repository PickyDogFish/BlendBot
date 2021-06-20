from discord.ext.commands import Cog
from discord.ext.commands import command
from ..db import db
from datetime import date, datetime, timedelta

class Admin(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("admin cog ready")





def setup(bot):
    bot.add_cog(Admin(bot))