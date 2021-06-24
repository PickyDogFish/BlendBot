from lib.bot import SUBMIT_CHANNEL_ID
from discord.ext.commands import Cog
from discord.ext.commands import command
from discord import Embed
from random import choice
from ..db import db

class Fun(Cog):
    def __init__(self, bot):
        self.bot=bot

    @command(name="hello", aliases = ["hi", "hey"])
    async def say_hello(self, ctx):
        await ctx.send(f"{choice(('Hello', 'Hi', 'Hey'))} {ctx.author.mention}!")

    @command(name="adduser")
    async def add_user_to_db(self, ctx):
        db.execute("INSERT OR IGNORE INTO users (UserID) VALUES (?)", ctx.author.id)
        await ctx.send(f"Added {ctx.author.mention} to the database!")

    @command(name="suggest")
    async def suggest_theme(self, ctx, *, sugg):
        neki = db.field("SELECT themeName FROM themes WHERE themeName = ?", (sugg))
        if (neki == None):
            db.execute("INSERT INTO themes (themeName) VALUES (?)", sugg)
            await ctx.send("Thank you for suggesting " + sugg + "!")
        else:
            await ctx.send("Theme has already been suggested")

    @command(name="random")
    async def random_theme(self, ctx):
        randomTheme = db.field("SELECT themeName FROM themes WHERE themeStatus = 1 ORDER BY RANDOM() LIMIT 1")
        await ctx.send(randomTheme)

    @command(name="help")
    async def display_help(self, ctx):
        embeded = Embed(title="Daily blend bot help page", colour = 16754726, description = "Here are the user commands:")
        embeded.add_field(name="$help", value="Displays this help page")
        embeded.add_field(name="$daily", value="Tells you the prompt of the day")
        embeded.add_field(name="$random", value="Gives you a random prompt from the pool")
        embeded.add_field(name="$suggest", value="Allows you to suggest a prompt to add to the pool. These suggestions will be manually reviewed")
        await ctx.send(embed = embeded)

    @command(name="submit")
    async def submit_daily(self, ctx):
        if ctx.channel.id != SUBMIT_CHANNEL_ID:
            await ctx.send("Cannot submit in this channel.")
        elif len(ctx.message.attachments) > 0 and ctx.channel.id == SUBMIT_CHANNEL_ID:
            chalID = db.field("SELECT challengeID FROM challenge WHERE challengeTypeID = 0 ORDER BY challengeID DESC")
            if (db.field("SELECT msgID FROM submission WHERE challengeID = ? AND userID = ?", chalID, ctx.author.id) == None):
                db.execute("INSERT INTO submission (userID, msgID, challengeID) VALUES (?, ?, ?)", ctx.author.id, ctx.message.id, chalID)
            else:
                db.execute("UPDATE submission SET msgID = ? WHERE challengeID = ? AND userID = ?", ctx.message.id, chalID, ctx.author.id)
            await ctx.message.add_reaction("✅")

    @command(name="daily")
    async def show_daily(self, ctx):
        await ctx.send(await self.bot.get_daily_theme())
            

    @Cog.listener()
    async def on_ready(self):
        print("fun cog ready")


def setup(bot):
    bot.remove_command('help')
    bot.add_cog(Fun(bot))