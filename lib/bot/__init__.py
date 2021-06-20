from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import Bot as BotBase
from discord import Intents, channel
from discord.ext.commands.errors import CommandNotFound
from discord.ext.commands import CommandNotFound
from apscheduler.triggers.cron import CronTrigger
from glob import glob

from ..db import db

PREFIX = "$"
OWNER_IDS = [176764856513462272]
COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]

GENERAL_ID = 835427910201507860

class Bot(BotBase):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.guild = None
        self.scheduler = AsyncIOScheduler()

        db.autosave(self.scheduler)
        super().__init__(
            command_prefix=PREFIX, 
            owner_ids = OWNER_IDS,
            intents = Intents.all())

    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")
            print(f"[cog] cog loaded")

        print("setup complete")

    def run(self):
        
        self.setup()

        with open("./lib/bot/token.0", "r", encoding="utf-8") as tk:
            self.TOKEN = tk.read()

        print("bot running")
        super().run(self.TOKEN, reconnect = True)

    async def on_connect(self):
        print("Bot connected")

    async def daily_challenge(self):
        channel = self.get_channel(GENERAL_ID)
        await channel.send("every minute")

        

    async def on_disconnect(self):
        print("Bot disconnected")

    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            await args[0].send("Something went wrong.")
        raise

    async def on_command_error(self, context, exception):
        if isinstance(exception, CommandNotFound):
            pass
        elif hasattr(exception, "original"):
            raise exception.original
        else:
            raise exception

    async def on_ready(self):
        if not self.ready:
            self.guild = self.get_guild(831137325299138621)
            self.scheduler.add_job(self.daily_challenge, CronTrigger(hour= 15, minute = 30, second = 0))
            self.scheduler.start()



            self.ready = True
            print("bot ready")
        else:
            print("bot reconnected")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)

bot = Bot()