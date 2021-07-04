import asyncio
import sys
import discord
from discord.ext.commands import Cog
from discord.ext.commands import command
from ..db import db
from datetime import date, datetime, timedelta
import json
from lib.bot import SUBMIT_CHANNEL_ID

class Admin(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("admin cog ready")

    @command(name="clear")
    async def clear(self, ctx, num_of_msgs_to_delete):
        if ctx.author.guild_permissions.administrator:
            list_of_msgs_to_delete = []
            for message in await ctx.channel.history(limit = int(num_of_msgs_to_delete)).flatten():
                list_of_msgs_to_delete.append(message)
            await ctx.channel.delete_messages(list_of_msgs_to_delete)
            last_message = [await ctx.channel.send(str(num_of_msgs_to_delete) + " messages were deleted")]
            await asyncio.sleep(2)
            await message.channel.delete_messages(last_message)

    @command(name="kill")
    async def kill(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await ctx.channel.send("See you soon!")
            sys.exit()

    @command(name="reject")
    async def reject(self, ctx, theme):
        if ctx.author.guild_permissions.administrator:
            db.execute("UPDATE themes SET themeStatus = -1 WHERE themeName = ?", theme)
            await ctx.channel.send("Theme status set to rejected")

    @command(name="approve")
    async def approve(self, ctx, theme):
        if ctx.author.guild_permissions.administrator:
            db.execute("UPDATE themes SET themeStatus = 1 WHERE themeName = ?", theme)
            await ctx.send("Theme status set to approved")

    @command(name="setnotused", aliases = ["setunused"])
    async def not_used(self, ctx, theme):
        if ctx.author.guild_permissions.administrator:
            db.execute("UPDATE themes SET lastUsed = '2011-11-11 11:11:11' WHERE themeName = ?", theme)
            await ctx.channel.send("Theme set to not used")
    
    @command(name="setused")
    async def used(self, ctx, theme):
        if ctx.author.guild_permissions.administrator:
            db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '),theme)
            await ctx.channel.send("Theme set to used")

    #setdaily <themeName> sets the daily theme to the specified themeName
    @command(name="setdaily")
    async def setdaily(self, ctx, theme):
        if ctx.author.guild_permissions.administrator:
            if db.field("SELECT * FROM themes WHERE themeName = ?", theme) != None:
                lastDaily = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 0")
                db.execute("UPDATE challenge SET themeName = ? WHERE challengeID = ?", theme, lastDaily)
                db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '), theme)
                await self.bot.get_channel(831214167897276446).edit(name="Theme-" + theme)
                #await ctx.channel.edit(name="Theme-" + theme)
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name = "you make " + theme))
            else:
                await ctx.channel.send("Theme not in pool")

    @command(name="givexp")
    async def givexp(self, ctx, userID, XPamount):
        print(userID, XPamount)
        if ctx.author.guild_permissions.administrator:
            db.execute("UPDATE users SET renderXP = renderXP + ? WHERE userID = ?", XPamount, userID)
            await ctx.channel.send("Added some XP")


    #puts the old data into the new database, all paths are hardcoded
    @command(name="parseolddata")
    async def parse_old_data(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await self.parse_user_data(ctx=ctx)
            await self.parse_used_themes(ctx=ctx)
            await self.parse_themes(ctx=ctx)
            await self.parse_suggestions(ctx=ctx)
            await ctx.send("Parsed old data")

    async def parse_user_data(self, ctx):
        if ctx.author.guild_permissions.administrator:
            with open("D:\BotGit\levels.json", "r+") as file:
                data = json.load(file)
                for user in data:
                    db.execute("INSERT OR IGNORE INTO users (userID, msgXP, renderXP) VALUES (?,?,?)", user, int(data[user]["messagepoints"]), data[user]["dailypoints"])

    async def parse_themes(self, ctx):
        if ctx.author.guild_permissions.administrator:
            with open("D:/BotGit/themes.txt", "r") as file:
                for line in file:
                    db.execute("INSERT OR IGNORE INTO themes (themeName, themeStatus) VALUES (?,1)", line.strip().replace("_", " "))

    async def parse_used_themes(self, ctx):
        if ctx.author.guild_permissions.administrator:
            with open("D:/BotGit/usedThemes.txt", "r") as file:
                for line in file:
                    db.execute("INSERT OR IGNORE INTO themes (themeName, themeStatus, lastUsed) VALUES (?,1,?)", line.strip().replace("_", " "), datetime.utcnow().isoformat())
    
    async def parse_suggestions(self, ctx):
        if ctx.author.guild_permissions.administrator:
            with open("D:/BotGit/suggestions.txt", "r") as file:
                for line in file:
                    db.execute("INSERT OR IGNORE INTO themes (themeName, themeStatus) VALUES (?,0)", line.strip().replace("_", " "))


    #sends a message of max 100 suggested themes
    @command(name="showsuggestions")
    async def show_suggestions(self, ctx):
        if ctx.author.guild_permissions.administrator:
            listOfSuggestions = db.column("SELECT themeName FROM themes WHERE themeStatus = 0 LIMIT 100")
            await ctx.send(listOfSuggestions)

    #sends a message of max 100 rejected themes
    @command(name="showrejected")
    async def show_rejected(self, ctx):
        if ctx.author.guild_permissions.administrator:
            listOfRejected = db.column("SELECT themeName FROM themes WHERE themeStatus = -1 LIMIT 100")
            await ctx.send(listOfRejected)

    #sends a message of max 100 approved themes
    @command(name="showapproved")
    async def show_rejected(self, ctx):
        if ctx.author.guild_permissions.administrator:
            listOfRejected = db.column("SELECT themeName FROM themes WHERE themeStatus = 1 LIMIT 100")
            await ctx.send(listOfRejected)

def setup(bot):
    bot.add_cog(Admin(bot))