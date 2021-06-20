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
            print(neki)
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
    async def submit(self, ctx):
        if len(ctx.message.attachments) > 0:
            db.execute("INSERT INTO submissions (userID, msgID)")
            

    @Cog.listener()
    async def on_ready(self):
        print("fun cog ready")


def setup(bot):
    bot.remove_command('help')
    bot.add_cog(Fun(bot))