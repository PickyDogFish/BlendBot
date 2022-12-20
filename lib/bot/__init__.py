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
DAILY_PING_ROLE = 916450288427225098

#testing server IDs
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
    DAILY_PING_ROLE = 916631404295618630


class Bot(BotBase):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.guild = GUILD_ID
        self.scheduler = AsyncIOScheduler()

        db.autosave(self.scheduler)
        super().__init__(
            command_prefix=PREFIX, 
            owner_ids = OWNER_IDS,
            intents = Intents.all())

    async def setup_hook(self):
        print(COGS)
        for cog in COGS:
            await self.load_extension(f"lib.cogs.{cog}")
            print(f"{cog} cog loaded")

        print("setup complete")

    def run(self):
        if testing:
            with open("./lib/bot/token.1", "r", encoding="utf-8") as tk:
                self.TOKEN = tk.read()
        else:
            with open("./lib/bot/token.0", "r", encoding="utf-8") as tk:
                self.TOKEN = tk.read()
        print("running super with token")
        super().run(self.TOKEN, reconnect = True)
        print("bot running")

    async def get_daily_theme(self):
        return db.field("SELECT themeName FROM challenges WHERE challengeTypeID = 0 ORDER BY challengeID DESC")

    async def move_to_voting(self, channelID, msgID, userID):
        channel = self.get_channel(channelID)

        try:
            msg = await channel.fetch_message(msgID)
            #just double checking if the embed is still there
            if msg.attachments:
                f = msg.attachments[0].url
                format = f.split(".")[-1]
                if format in ["png", "jpg"]:
                    embeded = Embed(title="Has collected 0 votes", colour = 0x5965F2)
                    embeded.set_author(name = self.get_user(userID).display_name, icon_url=self.get_user(userID).display_avatar.url)
                    embeded.set_image(url=f)
                    message = await self.get_channel(VOTING_CHANNEL_ID).send(embed = embeded)

            else:
                #attachment is a video
                attach = await msg.attachments[0].to_file()
                embeded = Embed(title="Has collected 0 votes", colour = 0x5965F2)
                embeded.set_author(name = self.get_user(userID).display_name, icon_url=self.get_user(userID).display_avatar.url)
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
        except:
            await self.get_channel(LOG_CHANNEL_ID).send("Error moving things to voting. Can be caused by user deleting submission.")

    # returns a dict of "userID": "rank" for given list of users. Calculates points up to beforeDate
    async def get_ranks(self, userList, beforeDate):
        ranks = {}
        for user in userList:
            renderXP = db.field("SELECT sum(vote) FROM (SELECT * FROM submissions NATURAL JOIN votes NATURAL JOIN challenges NATURAL JOIN users WHERE endDate > ? AND endDate < ?) WHERE userID = ?", self.get_start_of_year(), beforeDate, user)
            rank = db.field("SELECT COUNT(userID) FROM (SELECT userID, sum(vote) as renderXP FROM (SELECT * FROM submissions NATURAL JOIN votes NATURAL JOIN challenges NATURAL JOIN users WHERE endDate > ? AND endDate < ?) WHERE isInServer = 1 GROUP BY userID) WHERE renderXP >= ?", self.get_start_of_year(), beforeDate, renderXP)
            ranks[user] = rank
        return ranks

    # sums up votes for given challenge, updates renderXP in database, sends vote count message, remakes leaderboard
    async def count_votes(self, challengeID):
        voteCountText = ""
        scores = db.records("SELECT userID, msgID, SUM(vote) FROM submissions NATURAL JOIN votes WHERE challengeID = ? GROUP BY msgID", challengeID)
        isSubmission = False

        for submission in scores:
            isSubmission = True
            try:
                voteCountText += self.get_user(submission[0]).display_name + " collected " + str(submission[2]) + " points\n"
                #assigns the Daily Wizard role if renderXP was 0
                renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", submission[0]) 
                if renderXP == 0:
                    role = get(self.guild.roles, name="Daily Wizard")
                    await self.get_guild(GUILD_ID).get_member(submission[0]).add_roles(role)
                db.execute("UPDATE users SET renderXP = renderXP + ? WHERE userID = ?", submission[2], submission[0])
            except:
                await self.get_channel(LOG_CHANNEL_ID).send("Error while counting pre-vote score")
        
        if isSubmission:
            countTheme, startDate = db.record("SELECT themeName, startDate FROM challenges WHERE challengeID = ?", challengeID)
            voteCountEmbed = Embed(title="Vote counts for " + countTheme + ", which started on " + datetime.fromisoformat(startDate).date().isoformat() + ":", description=voteCountText)
            await self.get_channel(VOTING_CHANNEL_ID).send(embed=voteCountEmbed)
            await self.clear_leaderboard()
            await self.make_leaderboard()

    # sends rank up messages, checks users who submitted for given challengeID
    async def check_ranks(self, previousRanks, userList):
        currRanks = await self.get_ranks(userList, (datetime.utcnow() + timedelta(hours=24)).isoformat(timespec='seconds', sep=' '))
        for user in userList:
            if previousRanks[user] > currRanks[user]:
                userObj = self.get_user(user)
                if userObj != None:
                    await self.get_channel(BOT_SPAM_CHANNEL_ID).send(userObj.mention + f" moved up from {previousRanks[user]}. place to {currRanks[user]}. place!")
                else:
                    await self.get_channel(LOG_CHANNEL_ID).send("ERROR: Could not get user whole checking ranks.")

    # moves all submissions to voting
    async def move_all_submissions_to_voting(self, challengeID):
        themeName = db.field("SELECT themeName FROM challenges WHERE challengeID = ?", challengeID)
        if db.record("SELECT userID, msgID FROM submissions WHERE challengeID = ?", challengeID) != None:
            preSubEmbed = Embed(colour = 0x5965F2, title="Submissions for the theme " + themeName)
            await self.get_channel(VOTING_CHANNEL_ID).send(embed=preSubEmbed)
            submissions = db.records("SELECT userID, msgID FROM submissions WHERE challengeID = ?", challengeID)
            for userID, msgID in submissions:
                votingMsgID = await self.move_to_voting(SUBMIT_CHANNEL_ID, msgID, userID)
                if votingMsgID != -1:
                    db.execute("UPDATE submissions SET votingMsgID = ? WHERE msgID = ?", votingMsgID, msgID)
        else:
            await self.get_channel(VOTING_CHANNEL_ID).send("Looks like there are no submissions for the theme " + themeName)

    async def announce_new_daily_challenge(self):
        challengeID = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 0")
        #creates new challenges entry in db, make announcement, set bot status
        newDailyTheme = db.field("SELECT themeName FROM (SELECT * FROM themes WHERE themeStatus = 1 ORDER BY lastUsed LIMIT 50) WHERE themeStatus = 1 ORDER BY RANDOM() LIMIT 1")
        db.execute("INSERT INTO challenges (themeName, startDate, endDate, votingEndDate) VALUES (?, ?, ?, ?)", newDailyTheme, datetime.utcnow().isoformat(timespec='seconds', sep=' '), (datetime.utcnow() + timedelta(hours=24)).isoformat(timespec='seconds', sep=' '), (datetime.utcnow() + timedelta(days=2)).isoformat(timespec='seconds', sep=' '))
        newChallengeID = db.field("SELECT challengeID, themeName FROM challenges WHERE challengeTypeID = 0 ORDER BY challengeID DESC")
        db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '), newDailyTheme)
        db.execute("UPDATE currentChallenge SET currentChallengeID = ?, previousChallengeID = ? WHERE challengeTypeID = 0", newChallengeID, challengeID)

        dailyPingRole = get(self.guild.roles, name="DailyPing")
        embeded = Embed(colour = 16754726, title="The new theme for the daily challenge is: ", description="**"+newDailyTheme.upper()+ "**")
        await self.get_channel(SUBMIT_CHANNEL_ID).send(dailyPingRole.mention, embed=embeded)
        await self.change_presence(activity=Activity(type=ActivityType.watching, name = "you make " + newDailyTheme))
        #there is a delay on the discord api, so dont change names too often
        await self.get_channel(SUBMIT_CHANNEL_ID).edit(name="Theme-" + newDailyTheme)


    async def daily_challenge(self):
        await self.get_channel(LOG_CHANNEL_ID).send("Running daily challenges function")
        challengeID, previousChallengeID = db.record("SELECT currentChallengeID, previousChallengeID FROM currentChallenge WHERE challengeTypeID = 0")
        previousUsers = db.column("SELECT userID FROM submissions WHERE challengeID = ?", previousChallengeID)
        previousEndDate = db.field("SELECT endDate FROM challenges WHERE challengeID = ?", previousChallengeID)
        previousRanks = await self.get_ranks(previousUsers, previousEndDate)
        await self.count_votes(previousChallengeID)
        await self.check_ranks(previousRanks, previousUsers)

        await self.move_all_submissions_to_voting(challengeID)
        await self.announce_new_daily_challenge()


    async def weekly_challenge(self):
        await self.get_channel(LOG_CHANNEL_ID).send("Reminder to implement weekly challenges")

    async def custom_challenge(self):
        await self.get_channel(LOG_CHANNEL_ID).send("Running custom_challenge function.")
        challengeID = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 2")
        themeName, startDate, endDate, votingEndDate, imageLink = db.record("SELECT themeName, startDate, endDate, votingEndDate, imageLink FROM challenges WHERE challengeID = ?", challengeID)
        previousChallengeID = db.field("SELECT previousChallengeID FROM currentChallenge WHERE challengeTypeID = 2")
        prevThemeName, prevStartDate, prevEndDate, prevVotingEndDate = db.record("SELECT themeName, startDate, endDate, votingEndDate FROM challenges WHERE challengeID = ?", previousChallengeID)
        # if startDate of current custom challenge is in the future, you set it to now, set the appropriate end and voteEnd dates, sends message
        if startDate > datetime.utcnow().isoformat(timespec='seconds', sep=' '):
            numOfDays = (datetime.fromisoformat(endDate) - datetime.fromisoformat(startDate)).days
            numOfVotingDays = (datetime.fromisoformat(votingEndDate) - datetime.fromisoformat(startDate)).days
            print(numOfDays)
            db.execute("UPDATE challenges SET startDate = ?, endDate = ?, votingEndDate = ? WHERE challengeID = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '), (datetime.utcnow() + timedelta(days=numOfDays)).isoformat(timespec='seconds', sep=' '), (datetime.utcnow() + timedelta(days=numOfVotingDays)).isoformat(timespec='seconds', sep=' '), challengeID)

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
        try:
            await self.get_channel(LOG_CHANNEL_ID).send("** <@176764856513462272> " + str(err) + ":   " + str(args) + "**")
        except:
            print("Could not send message")
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
        await self.wait_until_ready()
        if not self.ready:
            self.guild = self.get_guild(GUILD_ID)
            self.scheduler.add_job(self.daily_challenge, CronTrigger(hour=6, minute=0))
            self.scheduler.add_job(self.weekly_challenge, CronTrigger(day_of_week=5, hour=7, minute=0))
            self.scheduler.add_job(self.custom_challenge, CronTrigger(hour=7, minute=0))
            self.scheduler.start()
            lastTheme = db.field("SELECT themeName FROM challenges WHERE challengeID = (SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 0)")
            await self.change_presence(activity=Activity(type=ActivityType.watching, name = "you make " + lastTheme))

            self.ready = True
            print(GUILD_ID)
            print(self.get_guild(GUILD_ID))
            try:
                await self.get_channel(LOG_CHANNEL_ID).send("Bot ready.")
            except:
                print("Could not send message")
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

        scores = db.records("SELECT userID, sum(vote) as renderXP FROM (SELECT * FROM submissions NATURAL JOIN votes NATURAL JOIN challenges NATURAL JOIN users WHERE endDate > ?) WHERE isInServer = 1 GROUP BY userID ORDER BY renderXP DESC", date(date.today().year, 1, 1).strftime("%Y-%m-%d %H:%M:%S"))

        for i in range(len(scores)-1, -1, -1):
            score = scores[i]
            user = self.get_user(score[0])
            sameScore = 0
            for j in range(1, len(scores)-i):
                if score[1] == scores[i+j][1]:
                    sameScore += 1
                else:
                    break 
            if user == None:
                print(f"User {score[0]} not in the server anymore, but isInServer still 1.")
                await self.get_channel(LOG_CHANNEL_ID).send(f"User {score[0]} not in the server anymore, but isInServer still 1.")
            else:
                await self.show_lb_card(user, score[1], i+1 + sameScore)


    async def clear_leaderboard(self):
        msg=[]
        channel = self.get_channel(LB_CHANNEL_ID)
        async for message in channel.history(limit = 200):
            msg.append(message)
        await channel.delete_messages(msg)

    async def show_lb_card(self, curUser, renderXP, place):

        img = Image.new('RGB', (720, 128), color = (30, 30, 30))
        await curUser.display_avatar.replace(size=128, format="png").save(fp="img/pfp.png")
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

    def get_start_of_year(self):
        return date(date.today().year, 1, 1).strftime("%Y-%m-%d %H:%M:%S")

bot = Bot()
