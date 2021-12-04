from datetime import date, datetime, timedelta, time
from glob import glob

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord import Activity, ActivityType, Embed, Intents
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound
from discord.ext.commands.errors import CommandNotFound
from math import sqrt
import discord
from discord.utils import get

from ..db import db

from PIL import Image, ImageDraw, ImageFont

testing = False

PREFIX = "$"
OWNER_IDS = [176764856513462272, 261049658569129984]
COGS=[]
if testing:
    COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]
else:
    COGS = [path.split("/")[-1][:-3] for path in glob("./lib/cogs/*.py")]

GUILD_ID = 831137325299138621
GENERAL_CHANNEL_ID = 831137325877690421
SUBMIT_CHANNEL_ID = 831214167897276446
VOTING_CHANNEL_ID = 831479996878946354
LB_CHANNEL_ID = 838703644026339338
WELCOME_CHANNEL_ID = 831849610426580992
BOT_TESTING_CHANNEL_ID = 833376293969723452
TODO_CHANNEL_ID = 832203986575818802
LOG_CHANNEL_ID = 864912275864158218
BOT_SPAM_CHANNEL_ID = 831471855910780988
CUSTOM_SUBMIT_ID = 867685564211789824

if testing:
    GENERAL_CHANNEL_ID = 835427910201507860
    SUBMIT_CHANNEL_ID = 835429505257963550
    VOTING_CHANNEL_ID = 835429490464129054
    LB_CHANNEL_ID = 857997935244869652
    GUILD_ID = 835427909724143617
    LOG_CHANNEL_ID = 864911454628741160
    BOT_TESTING_CHANNEL_ID = 865206590336532510
    BOT_SPAM_CHANNEL_ID = BOT_TESTING_CHANNEL_ID
    CUSTOM_SUBMIT_ID = 867724649223946240


#testing server ids
#GENERAL_CHANNEL_ID = 835427910201507860
#VOTING_CHANNEL_ID = 835429490464129054
#SUBMIT_CHANNEL_ID = 835429505257963550
#LB_CHANNEL_ID = 857997935244869652

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
            print(f"{cog} cog loaded")

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
        return db.field("SELECT themeName FROM challenges WHERE challengeTypeID = 0 ORDER BY challengeID DESC")

    async def move_to_voting(self, channelID, msgID, userID):
        channel = self.get_channel(channelID)
        msg = await channel.fetch_message(msgID)
        #just double checking if the embed is still there
        if msg.attachments:
            f = msg.attachments[0].url
            format = f.split(".")[-1]
            if format in ["png", "jpg"]:
                embeded = Embed(title="Has collected 0 votes", colour = 0x5965F2)
                embeded.set_author(name = self.get_user(userID).display_name, icon_url=self.get_user(userID).avatar_url)
                embeded.set_image(url=f)
                message = await self.get_channel(VOTING_CHANNEL_ID).send(embed = embeded)

            else:
                #attachment is a video
                attach = await msg.attachments[0].to_file()
                embeded = Embed(title="Has collected 0 votes", colour = 0x5965F2)
                embeded.set_author(name = self.get_user(userID).display_name, icon_url=self.get_user(userID).avatar_url)
                message = await self.get_channel(VOTING_CHANNEL_ID).send(embed=embeded)
                try:
                    await self.get_channel(VOTING_CHANNEL_ID).send(file = attach)
                except:
                    print("error while moving video, possibly file too big")
                    await self.get_channel(VOTING_CHANNEL_ID).send(embed = Embed(colour = 0x5965F2, title="Could not move the submission.", description=f"[Link to original message]({msg.jump_url})"))
            await message.add_reaction("1️⃣")
            await message.add_reaction("2️⃣")
            await message.add_reaction("3️⃣")
            await message.add_reaction("4️⃣")
            await message.add_reaction("5️⃣")
            return message.id



    async def daily_challenge(self):
        await self.get_channel(LOG_CHANNEL_ID).send("Running daily challenges function")
        challengeID, previousChallengeID = db.record("SELECT currentChallengeID, previousChallengeID FROM currentChallenge WHERE challengeTypeID = 0")
        #count votes
        scores = db.records("SELECT userID, msgID, challengeID, SUM(vote) FROM submissions NATURAL JOIN votes WHERE challengeID = ? GROUP BY msgID", previousChallengeID)
        isSubmission = False
        voteCountText = ""

        #saving ranks pre-vote count
        previousRanks = []
        for submission in scores:
            renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0]) 
            previousRanks.append(db.field("SELECT COUNT(userID) FROM users WHERE renderXP >= ?", renderXP))

        for submission in scores:
            isSubmission = True
            voteCountText += self.get_user(submission[0]).display_name + " collected " + str(submission[3]) + " points\n"
            #assigns the Daily Wizard role if renderXP was 0
            renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0]) 
            if renderXP == 0:
                role = get(self.guild.roles, name="Daily Wizard")
                await self.get_guild(GUILD_ID).get_member(submission[0]).add_roles(role)
            db.execute("UPDATE users SET renderXP = renderXP + ? WHERE userID = ?", submission[3], submission[0])
        
        #checking if users moved up in rank, send rank up messages
        tempIndex = 0
        for submission in scores:
            renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0])
            newRank = db.field("SELECT COUNT(userID) FROM users WHERE renderXP >= ?", renderXP)
            print(previousRanks[tempIndex], newRank)
            if previousRanks[tempIndex] > newRank:
                await self.get_channel(BOT_SPAM_CHANNEL_ID).send(self.get_user(submission[0]).mention + f" moved up from {previousRanks[tempIndex]}. place to {newRank}. place!")
            tempIndex += 1

        #if there were any submissions, send the vote counts, remake leaderboard
        if isSubmission:
            countTheme, startDate = db.record("SELECT themeName, startDate FROM challenges WHERE challengeID = ?", previousChallengeID)
            voteCountEmbed = Embed(title="Vote counts for " + countTheme + ", which started on " + datetime.fromisoformat(startDate).date().isoformat() + ":", description=voteCountText)
            await self.get_channel(VOTING_CHANNEL_ID).send(embed=voteCountEmbed)
            await self.clear_leaderboard()
            await self.make_leaderboard()

        #move things to voting
        themeName = db.field("SELECT themeName FROM challenges WHERE challengeID = ?", challengeID)
        if db.record("SELECT userID, msgID FROM submissions WHERE challengeID = ?", challengeID) != None:
            preSubEmbed = Embed(colour = 0x5965F2, title="Submissions for the theme " + themeName)
            await self.get_channel(VOTING_CHANNEL_ID).send(embed=preSubEmbed)
            subs = db.records("SELECT userID, msgID FROM submissions WHERE challengeID = ?", challengeID)
            for userID, msgID in subs:
                votingMsgID = await self.move_to_voting(SUBMIT_CHANNEL_ID, msgID, userID)
                db.execute("UPDATE submissions SET votingMsgID = ? WHERE msgID = ?", votingMsgID, msgID)
        else:
            await self.get_channel(VOTING_CHANNEL_ID).send("Looks like there are no submissions for the theme " + themeName)

        #createsnew challenges entry in db, make announcement, set bot status
        #TODO make it only select from the pool of not recently used themes
        newDailyTheme = db.field("SELECT themeName FROM (SELECT * FROM themes WHERE themeStatus = 1 ORDER BY lastUsed LIMIT 50) AS notUsed WHERE themeStatus = 1 ORDER BY RANDOM() LIMIT 1")
        db.execute("INSERT INTO challenges (themeName, startDate, endDate, votingEndDate) VALUES (?, ?, ?, ?)", newDailyTheme, datetime.utcnow().isoformat(timespec='seconds', sep=' '), (datetime.utcnow() + timedelta(hours=24)).isoformat(timespec='seconds', sep=' '), (datetime.utcnow() + timedelta(days=2)).isoformat(timespec='seconds', sep=' '))
        newChallengeID = db.field("SELECT challengeID, themeName FROM challenges WHERE challengeTypeID = 0 ORDER BY challengeID DESC")
        db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '), newDailyTheme)
        db.execute("UPDATE currentChallenge SET currentChallengeID = ?, previousChallengeID = ? WHERE challengeTypeID = 0", newChallengeID, challengeID)
        embeded = Embed(colour = 16754726, title="<@&916631404295618630>, the new theme for the daily challenge is: ", description="**"+newDailyTheme.upper()+ "**")
        await self.get_channel(SUBMIT_CHANNEL_ID).send(embed=embeded)
        await self.change_presence(activity=Activity(type=ActivityType.watching, name = "you make " + newDailyTheme))
        print(newDailyTheme)
        #apparently it can get stuck on renaming the channel (hopefully not a problem when doing once a day)...
        print(newDailyTheme)
        await self.get_channel(SUBMIT_CHANNEL_ID).edit(name="Theme-" + newDailyTheme)
        print(newDailyTheme)

    async def weekly_challenge(self):
        await self.get_channel(LOG_CHANNEL_ID).send("Reminder to implement weekly challenges")

    async def custom_challenge(self):
        await self.get_channel(LOG_CHANNEL_ID).send("Running custom_challenge function.")
        challengeID = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 2")
        themeName, startDate, endDate, votingEndDate, imageLink = db.record("SELECT themeName, startDate, endDate, votingEndDate, imageLink FROM challenges WHERE challengeID = ?", challengeID)
        previousChallengeID = db.field("SELECT previousChallengeID FROM currentChallenge WHERE challengeTypeID = 2")
        prevThemeName, prevStartDate, prevEndDate, prevVotingEndDate = db.record("SELECT themeName, startDate, endDate, votingEndDate FROM challenges WHERE challengeID = ?", previousChallengeID)
        if startDate > datetime.utcnow().isoformat(timespec='seconds', sep=' '):
            numOfDays = (datetime.fromisoformat(endDate) - datetime.fromisoformat(startDate)).days
            numOfVotingDays = (datetime.fromisoformat(votingEndDate) - datetime.fromisoformat(startDate)).days
            print(numOfDays)
            db.execute("UPDATE challenges SET startDate = ?, endDate = ?, votingEndDate = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '), (datetime.utcnow() + timedelta(days=numOfDays)).isoformat(timespec='seconds', sep=' '), (datetime.utcnow() + timedelta(days=numOfVotingDays)).isoformat(timespec='seconds', sep=' '))

            customChallengeEmbed = Embed(title="Custom challenge: " + themeName, description="You have **" + str(numOfDays) + " days** to submit your artworks.")
            customChallengeEmbed.set_image(url=imageLink)
            print("sending message now")
            await self.get_channel(CUSTOM_SUBMIT_ID).send(embed=customChallengeEmbed)

        #if prevVotingEndDate is today, count the votes for it
        if prevVotingEndDate != None and datetime.fromisoformat(prevVotingEndDate).date() == datetime.utcnow().date():
            await self.get_channel(LOG_CHANNEL_ID).send("Counting votes of previous custom challenge")
            #count votes
            scores = db.records("SELECT userID, msgID, challengeID, SUM(vote) FROM submissions NATURAL JOIN votes WHERE challengeID = ? GROUP BY msgID", previousChallengeID)
            isSubmission = False
            voteCountText = ""

            #saving ranks pre-vote count
            previousRanks = []
            for submission in scores:
                renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0]) 
                previousRanks.append(db.field("SELECT COUNT(userID) FROM users WHERE renderXP >= ?", renderXP))

            for submission in scores:
                isSubmission = True
                voteCountText += self.get_user(submission[0]).display_name + " collected " + str(submission[3]) + " points\n"
                #assigns the Daily Wizard role if renderXP was 0
                renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0]) 
                if renderXP == 0:
                    role = get(self.guild.roles, name="Daily Wizard")
                    await self.get_guild(GUILD_ID).get_member(submission[0]).add_roles(role)
                db.execute("UPDATE users SET renderXP = renderXP + ? WHERE userID = ?", submission[3], submission[0])
            
            #checking if users moved up in rank, send rank up messages
            tempIndex = 0
            for submission in scores:
                renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0])
                newRank = db.field("SELECT COUNT(userID) FROM users WHERE renderXP >= ?", renderXP)
                print(previousRanks[tempIndex], newRank)
                if previousRanks[tempIndex] > newRank:
                    await self.get_channel(BOT_SPAM_CHANNEL_ID).send(self.get_user(submission[0]).mention + f" moved up from {previousRanks[tempIndex]}. place to {newRank}. place!")
                tempIndex += 1

            #if there were any submissions, send the vote counts, remake leaderboard
            if isSubmission:
                voteCountEmbed = Embed(title="Vote counts for the **custom challenge** " + prevThemeName + ", which started on " + datetime.fromisoformat(prevStartDate).date().isoformat() + ":", description=voteCountText)
                await self.get_channel(VOTING_CHANNEL_ID).send(embed=voteCountEmbed)
                await self.clear_leaderboard()
                await self.make_leaderboard()

        #if votingEndDate is today, count the votes for it
        if datetime.fromisoformat(votingEndDate).date() == datetime.utcnow().date():
            await self.get_channel(LOG_CHANNEL_ID).send("Counting votes of current custom challenge")
            #count votes
            scores = db.records("SELECT userID, msgID, challengeID, SUM(vote) FROM submissions NATURAL JOIN votes WHERE challengeID = ? GROUP BY msgID", challengeID)
            isSubmission = False
            voteCountText = ""

            #saving ranks pre-vote count
            previousRanks = []
            for submission in scores:
                renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0]) 
                previousRanks.append(db.field("SELECT COUNT(userID) FROM users WHERE renderXP >= ?", renderXP))

            for submission in scores:
                isSubmission = True
                voteCountText += self.get_user(submission[0]).display_name + " collected " + str(submission[3]) + " points\n"
                #assigns the Daily Wizard role if renderXP was 0
                renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0]) 
                if renderXP == 0:
                    role = get(self.guild.roles, name="Daily Wizard")
                    await self.get_guild(GUILD_ID).get_member(submission[0]).add_roles(role)
                db.execute("UPDATE users SET renderXP = renderXP + ? WHERE userID = ?", submission[3], submission[0])
            
            #checking if users moved up in rank, send rank up messages
            tempIndex = 0
            for submission in scores:
                renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0])
                newRank = db.field("SELECT COUNT(userID) FROM users WHERE renderXP >= ?", renderXP)
                print(previousRanks[tempIndex], newRank)
                if previousRanks[tempIndex] > newRank:
                    await self.get_channel(BOT_SPAM_CHANNEL_ID).send(self.get_user(submission[0]).mention + f" moved up from {previousRanks[tempIndex]}. place to {newRank}. place!")
                tempIndex += 1

            #if there were any submissions, send the vote counts, remake leaderboard
            if isSubmission:
                voteCountEmbed = Embed(title="Vote counts for the **custom challenge** " + themeName + ", which started on " + datetime.fromisoformat(startDate).date().isoformat() + ":", description=voteCountText)
                await self.get_channel(VOTING_CHANNEL_ID).send(embed=voteCountEmbed)
                await self.clear_leaderboard()
                await self.make_leaderboard()

        #if endDate is today, move things to voting
        elif datetime.fromisoformat(endDate).date() == datetime.utcnow().date():
            await self.get_channel(LOG_CHANNEL_ID).send("Moving submissions for custom_challenge to voting")
            if db.record("SELECT userID, msgID FROM submissions WHERE challengeID = ?", challengeID) != None:
                preSubEmbed = Embed(colour = 0x5965F2, title="Submissions for the custom challenge " + themeName)
                await self.get_channel(VOTING_CHANNEL_ID).send(embed=preSubEmbed)
                subs = db.records("SELECT userID, msgID FROM submissions WHERE challengeID = ?", challengeID)
                for userID, msgID in subs:
                    votingMsgID = await self.move_to_voting(CUSTOM_SUBMIT_ID, msgID, userID)
                    db.execute("UPDATE submissions SET votingMsgID = ? WHERE msgID = ?", votingMsgID, msgID)
            else:
                await self.get_channel(VOTING_CHANNEL_ID).send("Looks like there are no submissions for the custom challenge " + themeName)




    async def on_disconnect(self):
        print("Bot disconnected")

    async def on_connect(self):
        try:
            await self.get_channel(LOG_CHANNEL_ID).send("Bot connected.")
        except:
            print("Couldn't send on connect message")
        print("Bot connected")

    async def on_error(self, err, *args, **kwargs):
        await self.get_channel(LOG_CHANNEL_ID).send("** <@176764856513462272> " + str(err) + ":   " + str(args) + "**")
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
            self.guild = self.get_guild(GUILD_ID)
            self.scheduler.add_job(self.daily_challenge, CronTrigger(hour=6, minute=0))
            self.scheduler.add_job(self.weekly_challenge, CronTrigger(day_of_week=5, hour=7, minute=0))
            self.scheduler.add_job(self.custom_challenge, CronTrigger(hour=7, minute=0))
            self.scheduler.start()
            lastTheme = db.field("SELECT themeName FROM challenges WHERE challengeID = (SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 0)")
            await self.change_presence(activity=Activity(type=ActivityType.watching, name = "you make " + lastTheme))

            self.ready = True

            await self.get_channel(LOG_CHANNEL_ID).send("Bot ready.")
            print("bot ready")
        else:
            lastTheme = db.field("SELECT themeName FROM challenges WHERE challengeID = (SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 0)")
            await self.change_presence(activity=Activity(type=ActivityType.watching, name = "you make " + lastTheme))

            await self.get_channel(LOG_CHANNEL_ID).send("Bot ready after reconnect.")
            print("bot reconnected")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)

    async def make_leaderboard(self):
        await self.get_channel(LOG_CHANNEL_ID).send("Making leaderboard.")
        scores = db.records("SELECT userID, renderXP FROM users WHERE renderXP > 0 ORDER BY renderXP DESC LIMIT 100")
        for score in scores:
            user = self.get_user(score[0])
            if user == None:
                print("User not in the server anymore.")
            else:
                await self.show_lb_card(score[0])
                #text = "Number of points: " + str(score[1]) + "   Level: " + str(int(sqrt(score[1]*40)//10)) + "\n\n"
                #embed = Embed(colour = 0xFF0000, title=text)
                #embed.set_author(name = user.display_name, icon_url=user.avatar_url)
                #await self.get_channel(LB_CHANNEL_ID).send(embed=embed)

    async def clear_leaderboard(self):
        msg=[]
        channel = self.get_channel(LB_CHANNEL_ID)
        msgHistory = channel.history(limit = 100)
        if msgHistory != None:
            for message in await msgHistory.flatten():
                msg.append(message)
            await channel.delete_messages(msg)

    async def show_lb_card(self, userID):
        renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", userID)
        place = db.field("SELECT COUNT(userID) FROM users WHERE renderXP >= ?", renderXP)

        curUser = self.get_user(userID)

        img = Image.new('RGB', (720, 128), color = (30, 30, 30))
        await curUser.avatar_url_as(format="png", size=128).save(fp="img/pfp.png")
        pfp = Image.open("img/pfp.png", "r")
        img.paste(pfp, (0,0))

        d = ImageDraw.Draw(img)
        nameWidth, nameHeight = d.textsize(curUser.name, font=ImageFont.truetype('fonts/arial.ttf', 64))
        if nameWidth < 464: 
            d.text((138,30), curUser.name, font=ImageFont.truetype('fonts/arial.ttf', 64), fill=(200, 200, 200))
        else:
            d.text((138,30), curUser.name[0:12] + "...", font=ImageFont.truetype('fonts/arial.ttf', 60), fill=(200, 200, 200))
        d.rectangle((592,0, 720, 128), fill=(200, 200, 0))
        placeWidth, placeHeight = d.textsize(str(place), font=ImageFont.truetype('fonts/arial.ttf', 120))
        xpWidth, xpHeight = d.textsize(str(renderXP), font=ImageFont.truetype('fonts/arial.ttf', 32))
        if placeWidth < 90:
            d.text((656 - placeWidth/2,-18), str(place), font=ImageFont.truetype('fonts/arial.ttf', 120), fill=(0, 0, 0))
            d.text((656 - xpWidth/2,-18 + placeHeight), str(renderXP), font=ImageFont.truetype('fonts/arial.ttf', 32), fill=(30, 30, 30))
        else:
            placeWidth, placeHeight = d.textsize(str(place), font=ImageFont.truetype('fonts/arial.ttf', 90))
            d.text((656 - placeWidth/2, 0), str(place), font=ImageFont.truetype('fonts/arial.ttf', 90), fill=(0, 0, 0))
            d.text((656 - xpWidth/2, 0 + placeHeight), str(renderXP), font=ImageFont.truetype('fonts/arial.ttf', 32), fill=(30, 30, 30))

        img.save('img/lb.png')
        with open('img/lb.png', 'rb') as f:
            pic = discord.File(f)
            await self.get_channel(LB_CHANNEL_ID).send(file=pic)

bot = Bot()
