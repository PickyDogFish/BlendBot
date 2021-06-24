from datetime import date, datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import Bot as BotBase
from discord import Intents, Embed, Activity, ActivityType
from discord.ext.commands.errors import CommandNotFound
from discord.ext.commands import CommandNotFound
from apscheduler.triggers.cron import CronTrigger
from glob import glob

from ..db import db

PREFIX = "$"
OWNER_IDS = [176764856513462272]
COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]

GENERAL_CHANNEL_ID = 835427910201507860
VOTING_CHANNEL_ID = 835429490464129054
SUBMIT_CHANNEL_ID = 835429505257963550

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

    async def get_daily_theme(self):
        return db.field("SELECT themeName FROM challenge WHERE challengeTypeID = 0 ORDER BY challengeID DESC")

    async def move_to_voting(self, msgID, userID):
        channel = self.get_channel(SUBMIT_CHANNEL_ID)
        msg = await channel.fetch_message(msgID)
        #just double checking if the embed is still there
        if msg.attachments:
            attach = await msg.attachments[0].to_file()
            message = await self.get_channel(VOTING_CHANNEL_ID).send("Todays submission by " + self.get_user(userID).display_name + ":", file = attach)
            await message.add_reaction("1️⃣")
            await message.add_reaction("2️⃣")
            await message.add_reaction("3️⃣")
            await message.add_reaction("4️⃣")
            await message.add_reaction("5️⃣")
            return message.id

    async def daily_challenge(self):
        challengeID, themeName = db.record("SELECT challengeID, themeName FROM challenge WHERE challengeTypeID = 0 ORDER BY challengeID DESC")
        #count votes
        #TODO

        #move things to voting
        if db.record("SELECT userID, msgID FROM submission WHERE challengeID = ?", challengeID) != None:
            msgID, userID = db.record("SELECT msgID, userID FROM submission WHERE challengeID = ?", challengeID)
            votingMsgID = await self.move_to_voting(msgID, userID)
            db.execute("UPDATE submission SET votingMsgID = ? WHERE msgID = ?", votingMsgID, msgID)
        else:
            await self.get_channel(VOTING_CHANNEL_ID).send("Looks like there are no submissions for the theme " + themeName)

        #createsnew challenge entry in db, make announcement, set bot status
        newDailyTheme = db.field("SELECT themeName FROM themes WHERE themeStatus = 1 ORDER BY RANDOM() LIMIT 1")
        db.execute("INSERT INTO challenge (themeName) VALUES (?)", newDailyTheme)
        db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(), newDailyTheme)
        embeded = Embed(colour = 16754726, title="The new theme for the daily challenge is: ", description="**"+newDailyTheme.upper()+ "**")
        await self.get_channel(SUBMIT_CHANNEL_ID).send(embed=embeded)
        await self.change_presence(activity=Activity(type=ActivityType.watching, name = "you make " + newDailyTheme))
        #apparently it can get stuck on renaming the channel (hopefully not a problem when doing once a day)...
        await self.get_channel(SUBMIT_CHANNEL_ID).edit(name="Theme-" + newDailyTheme)
        

    async def on_disconnect(self):
        print("Bot disconnected")

    async def on_connect(self):
        print("Bot connected")

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
            self.scheduler.add_job(self.daily_challenge, CronTrigger(second = 0))
            self.scheduler.start()

            self.ready = True
            print("bot ready")
        else:
            print("bot reconnected")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)

bot = Bot()