from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import Bot as BotBase

PREFIX = "+"
OWNER_IDS = [176764856513462272]

class Bot(BotBase):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.guild = None
        self.scheduler = AsyncIOScheduler()
        super().__init__(command_prefix=PREFIX, owner_ids = OWNER_IDS)

    def run(self):
        with open("./lib/bot/token", "r", encoding="utf-8") as tk:
            self.TOKEN = tk.read()

        print("bot running")
        super().run(self.TOKEN, reconnect = True)

    async def on_connect(self):
        print("Bot connected")

    async def on_disconnect(self):
        print("Bot disconnected")

    async def on_ready(self):
        if not self.ready:
            print("bot ready")
            self.guild = self.get_guild(831137325299138621)
            self.ready = True

        else:
            print("bot reconnected")

    async def on_message(self):
        pass

bot = Bot()