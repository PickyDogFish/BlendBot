from datetime import date, datetime, timedelta, time
from glob import glob

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord import Activity, ActivityType, Embed, Intents
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound
from discord.ext.commands.errors import CommandNotFound
from math import sqrt

from ..db import db

PREFIX = "$"
OWNER_IDS = [176764856513462272]
COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]

GENERAL_CHANNEL_ID = 835427910201507860
VOTING_CHANNEL_ID = 835429490464129054
SUBMIT_CHANNEL_ID = 835429505257963550
LB_CHANNEL_ID = 857997935244869652

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
            f = msg.attachments[0].url
            embeded = Embed(title="Has collected 0 votes", colour = 0x5965F2)
            embeded.set_author(name = self.get_user(userID).display_name, icon_url=self.get_user(userID).avatar_url)
            embeded.set_image(url=f)
            message = await self.get_channel(VOTING_CHANNEL_ID).send(embed = embeded)
            #attach = await msg.attachments[0].to_file()
            #message = await self.get_channel(VOTING_CHANNEL_ID).send("Todays submission by " + self.get_user(userID).display_name + ":", file = attach)
            await message.add_reaction("1️⃣")
            await message.add_reaction("2️⃣")
            await message.add_reaction("3️⃣")
            await message.add_reaction("4️⃣")
            await message.add_reaction("5️⃣")
            return message.id



    async def daily_challenge(self):
        challengeID, previousChallengeID = db.record("SELECT currentChallengeID, previousChallengeID FROM currentChallenge WHERE challengeTypeID = 0")
        #count votes
        scores = db.records("SELECT userID, msgID, challengeID, SUM(vote) FROM submission NATURAL JOIN votes WHERE challengeID = ? GROUP BY msgID", previousChallengeID)
        isSubmission = False
        voteCountText = ""
        for submission in scores:
            isSubmission = True
            voteCountText += self.get_user(submission[0]).display_name + " collected " + str(submission[3]) + " points\n"
            db.execute("UPDATE users SET renderXP = renderXP + ? WHERE userID = ?", submission[3], submission[0])
        
        if isSubmission:
            countTheme, startDate = db.record("SELECT themeName, startDate FROM challenge WHERE challengeID = ?", previousChallengeID)
            voteCountEmbed = Embed(title="Vote counts for " + countTheme + ", which started on " + datetime.fromisoformat(startDate).date().isoformat() + ":", description=voteCountText)
            await self.get_channel(VOTING_CHANNEL_ID).send(embed=voteCountEmbed)
            await self.clear_leaderboard()
            await self.make_leaderboard()

        #move things to voting
        themeName = db.field("SELECT themeName FROM challenge WHERE challengeID = ?", challengeID)
        if db.record("SELECT userID, msgID FROM submission WHERE challengeID = ?", challengeID) != None:
            subs = db.records("SELECT userID, msgID FROM submission WHERE challengeID = ?", challengeID)
            for userID, msgID in subs:
                msgID, userID = db.record("SELECT msgID, userID FROM submission WHERE challengeID = ?", challengeID)
                votingMsgID = await self.move_to_voting(msgID, userID)
                db.execute("UPDATE submission SET votingMsgID = ? WHERE msgID = ?", votingMsgID, msgID)
        else:
            await self.get_channel(VOTING_CHANNEL_ID).send("Looks like there are no submissions for the theme " + themeName)

        #createsnew challenge entry in db, make announcement, set bot status
        #TODO make it only select from the pool of not recently used themes
        newDailyTheme = db.field("SELECT themeName FROM (SELECT * FROM themes ORDER BY lastUsed LIMIT 50) AS notUsed WHERE themeStatus = 1 ORDER BY RANDOM() LIMIT 1")
        db.execute("INSERT INTO challenge (themeName, startDate, endDate) VALUES (?, ?, ?)", newDailyTheme, datetime.utcnow().isoformat(timespec='seconds', sep=' '), (datetime.utcnow() + timedelta(hours=24)).isoformat(timespec='seconds', sep=' '))
        newChallengeID = db.field("SELECT challengeID, themeName FROM challenge WHERE challengeTypeID = 0 ORDER BY challengeID DESC")
        db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '), newDailyTheme)
        db.execute("UPDATE currentChallenge SET currentChallengeID = ?, previousChallengeID = ? WHERE challengeTypeID = 0", newChallengeID, challengeID)
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
            self.scheduler.add_job(self.daily_challenge, CronTrigger(hour=6, minute=0))
            self.scheduler.start()

            self.ready = True
            print("bot ready")
        else:
            print("bot reconnected")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)
        
        if message.content.startswith("$dodaily"):
            await self.daily_challenge()

    async def make_leaderboard(self):
        scores = db.records("SELECT userID, renderXP FROM users ORDER BY renderXP DESC LIMIT 10")
        for score in scores:
            user = self.get_user(score[0])
            if user == None:
                print("User not in the server anymore.")
            else:
                text = "Number of points: " + str(score[1]) + "   Level: " + str(int(sqrt(score[1]*40)//10)) + "\n\n"
                embed = Embed(colour = 0xFF0000, title=text)
                embed.set_author(name = user.display_name, icon_url=user.avatar_url)
                await self.get_channel(LB_CHANNEL_ID).send(embed=embed)

    async def clear_leaderboard(self):
        msg=[]
        channel = self.get_channel(LB_CHANNEL_ID)
        #actually 2 days ago, dont ask
        vceraj = datetime.combine(datetime.now().date() - timedelta(days=2), time(0))
        for message in await channel.history(after=vceraj).flatten():
            msg.append(message)
        await channel.delete_messages(msg)

bot = Bot()
