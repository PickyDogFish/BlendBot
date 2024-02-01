import asyncio
import sys
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Cog, command
from discord.ext.commands.core import cooldown
from ..db import db
from datetime import date, datetime, timedelta
import json
from lib.bot import OWNER_IDS, SUBMIT_CHANNEL_ID, GUILD_ID, VERSION
from discord import Embed



class Admin(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("admin cog ready")

    @app_commands.command(name="version", description="Bot version")
    @app_commands.default_permissions(administrator=True)
    async def show_version(self, interaction:discord.Interaction):
        await interaction.response.send_message(VERSION)


    @app_commands.command(name="addusertodb", description="Adds [userID] to the table of users")
    @app_commands.default_permissions(administrator=True)
    async def add_user_to_db(self, interaction:discord.Interaction, user:str):
        db.execute("INSERT OR IGNORE INTO users (UserID) VALUES (?)", int(user))
        await interaction.response.send_message(f"Added {user} to the database!")

    @app_commands.command(name="clear", description="Deletes the last [number] messages")
    @app_commands.default_permissions(administrator=True)
    async def clear(self, interaction=discord.Interaction, number:int=1):
        list_of_msgs_to_delete = []
        async for message in interaction.channel.history(limit = int(number)):
            list_of_msgs_to_delete.append(message)
        await interaction.response.send_message(str(number) + " messages were deleted!", ephemeral=True)
        await interaction.channel.delete_messages(list_of_msgs_to_delete)


    @app_commands.command(name="restart", description="Restarts the bot")
    @app_commands.default_permissions(administrator=True)
    async def restart(self, interaction:discord.Interaction):
        if interaction.user.id in self.bot.owner_ids:
            await interaction.response.send_message("See you soon!")
            sys.exit()
        else:
            await interaction.response.send_message("Only owners can restart the bot!")

    @app_commands.command(name="checkusers", description="Check if users in db are still in the server.")
    @app_commands.default_permissions(administrator=True)
    async def check_users(self, interaction:discord.Interaction):
        users = db.records("SELECT userID, isInServer FROM users")
        guild = self.bot.get_guild(GUILD_ID)
        for index in range(len(users)):
            user = users[index]
            if user[1] == 1 and guild.get_member(user[0]) is None:
                 db.execute("UPDATE users SET isInServer = 0 WHERE userID = ?", user[0])
        await interaction.response.send_message("Checked isInServer.")


    @command(name="givexp")
    async def givexp(self, ctx, userID, XPamount):
        await self.bot.server_log(f"Added {str(XPamount)} XP to {self.bot.get_user(int(userID)).display_name}")
        if ctx.author.guild_permissions.administrator:
            if db.field("SELECT userID FROM users WHERE userID = ?", userID) != None:
                db.execute("UPDATE users SET renderXP = renderXP + ? WHERE userID = ?", XPamount, userID)
                await ctx.send(f"Added {str(XPamount)} XP to {self.bot.get_user(int(userID)).display_name}")
            else:
                await ctx.send("User not in database.")

    dailyGroup = app_commands.Group(name = "daily", description = "Daily challenge command group", default_permissions = discord.Permissions())
    
    @dailyGroup.command(name="run", description = "Runs the daily challenge function")
    async def run_daily_challenge(self, interaction:discord.Interaction):
        await interaction.response.send_message("Ran daily challenge")
        await self.bot.daily_challenge()

    #setdaily <themeName> sets the daily theme to the specified themeName
    @dailyGroup.command(name="set", description= "Sets the daily challenge theme")
    async def setdaily(self, interaction: discord.Interaction, theme: str):
        if db.field("SELECT * FROM themes WHERE themeName = ?", theme) != None:
            lastDaily = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 0")
            db.execute("UPDATE challenges SET themeName = ? WHERE challengeID = ?", theme, lastDaily)
            db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '), theme)
            await self.bot.get_channel(SUBMIT_CHANNEL_ID).edit(name="Theme-" + theme)
            #await ctx.channel.edit(name="Theme-" + theme)
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name = "you make " + theme))
            await interaction.response.send_message(f"The theme has been set to **{theme}**." )
        else:
            await interaction.response.send_message(f"Theme **{theme}** is not in the database.")




    @command(name="sync")
    async def sync_slash_commands(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await self.bot.tree.sync(guild = discord.Object(id = GUILD_ID))
            await ctx.send("Synced slash commands.")

    @command(name="makelb")
    async def show_leaderboard(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await self.bot.clear_leaderboard()
            await self.bot.make_leaderboard()

    @command(name="setcustom")
    async def set_custom_challenge(self,ctx, name, link, numOfDays, numOfVotingDays):
        if ctx.author.guild_permissions.administrator:
            db.execute("INSERT INTO challenges (challengeTypeID, themeName, startDate, endDate, votingEndDate, imageLink) VALUES (2, ?, ?, ?, ?, ?)", name, (datetime.utcnow() + timedelta(days=1)).isoformat(timespec='seconds', sep=' '), (datetime.utcnow()+timedelta(days=int(numOfDays)+1)).isoformat(timespec='seconds', sep=' '),(datetime.utcnow() + timedelta(days=int(numOfVotingDays) + int(numOfDays)+1)).isoformat(timespec='seconds', sep=' '), link)
            newChallengeID = db.field("SELECT challengeID, themeName FROM challenges WHERE challengeTypeID = 2 ORDER BY challengeID DESC")
            previousChallengeID = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 2")
            db.execute("UPDATE currentChallenge SET currentChallengeID = ?, previousChallengeID = ? WHERE challengeTypeID = 2", newChallengeID, previousChallengeID)
            await ctx.send("Set the next custom challenge.")

    @command(name="docustom")
    async def test_custom_challenge(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await self.bot.custom_challenge()


    # @command(name="customSQL")
    # async def run_custom_SQL(self, ctx, *, command):
    #     if ctx.author.id in OWNER_IDS:
    #         await server_log(ctx.author.name + " just ran custom SQL: " + command)
    #         db.execute(command)


    # @command(name="setisinserver")
    # async def set_isinserver(self,ctx):
    #     if ctx.author.id in OWNER_IDS:
    #         users = db.records("SELECT userID FROM users")
    #         for user in users:
    #             userObject = self.bot.get_user(user[0])
    #             if userObject == None:
    #                 db.execute("UPDATE users SET isInServer = 0 WHERE userID = ?", user[0])

    @command(name="adminhelp")
    async def show_admin_help(self, ctx):
        if ctx.author.guild_permissions.administrator:
            helpText = "List of commands, with the prefix **$**:\n\n\n"
            helpText += "`$clear [number]`: Deletes last *number* messages.\n\n"
            helpText += "`$addusertodb [userId]`: Adds user entry into db with userId. \n\n"
            helpText += "`$setnotused [theme_name]`: sets last used date to 2011-11-11 11:11:11.\n\n"
            helpText += "`$setused [theme_name]`: sets last used to today.\n\n"
            helpText += "`$givexp [userID] [xpAmount]`: gives user with userID xpAmount of renderXP. xpAmount can be negative.\n\n"
            helpText += "`$makelb`: remakes the leaderboard.\n\n"
            helpText += "`$setcustom [name] [link] [numOfDays] [numOfVotingDays]`: set things for a custom challenge.\n\n"
            helpText += "`$docustom`: runs the custom challenge function.\n\n"


            embeded = Embed(title="Admin help for 3Daily bot.", colour = 16754726, description = helpText)
            await ctx.send(embed = embeded)

async def setup(bot):
    await bot.add_cog(Admin(bot), guilds = [discord.Object(id = GUILD_ID)])