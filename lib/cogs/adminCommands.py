import asyncio
import sys
import discord
from discord.ext.commands import Cog
from discord.ext.commands import command
from ..db import db
from datetime import date, datetime, timedelta

class Admin(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("admin cog ready")

    @command(name="themes")
    async def display_themes(self, ctx):
        seznam_tem = db.execute("SELECT themeName FROM themes WHERE themeStatus = 1, used = 0")
        ctx.channel.send(' '.join(seznam_tem))

    @command(name="clear")
    async def clear(self, ctx, num_of_msgs_to_delete):
        if not ctx.author.guild_permission.administrator:
            list_of_msgs_to_delete = []
            for message in await ctx.channel.history(limit = int(num_of_msgs_to_delete)).flatten():
                list_of_msgs_to_delete.append(message)
            await ctx.channel.delete_messages(list_of_msgs_to_delete)
            last_message = [await ctx.channel.send(str(num_of_msgs_to_delete) + "messages were deleted")]
            await asyncio.sleep(2)
            await message.channel.delete_messages(last_message)

    @command(name="kill")
    async def kill(self, ctx):
        if not ctx.author.guild_permission.administrator:
            ctx.channel.send("See you soon!")
            sys.exit()

    @command(name="reject")
    async def reject(self, ctx, theme):
        if not ctx.author.guild_permission.administrator:
            db.execute("UPDATE themes SET themeStatus = -1 WHERE themeName = ?", theme)
            ctx.channel.send("Theme status set to rejected")

    @command(name="approve")
    async def approve(self, ctx, theme):
        if not ctx.author.guild_permission.administrator:
            db.execute("UPDATE themes SET themeStatus = 1 WHERE themeName = ?", theme)
            ctx.channel.send("Theme status set to approved")

    @command(name="used")
    async def used(self, ctx, theme):
        if not ctx.author.guild_permission.administrator:
            db.execute("UPDATE themes SET used = 1 WHERE themeName = ?", theme)
            ctx.channel.send("Theme set to used")

    @command(name="notused")
    async def used(self, ctx, theme):
        if not ctx.author.guild_permission.administrator:
            db.execute("UPDATE themes SET used = 0 WHERE themeName = ?", theme)
            ctx.channel.send("Theme set to not used")

    @command(name="setdaily")
    async def setdaily(self, ctx, theme):
        if not ctx.author.guild_permission.administrator:
            if db.execute("SELECT * FROM themes WHERE themeName = ?", theme) == None:

                # TODO:
                # set daily theme to daily challange
                # change_name()

                await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name = "you make " + theme))
            else:
                ctx.channel.send("Theme not in pool")

    @command(name="givexp")
    async def givexp(self, ctx, userID, XPamount):
        if not ctx.author.guild_permission.administrator:
            db.execute("UPDATE users SET renderXP = renderXP + ? WHERE userID = ?", XPamount, userID)
            ctx.channel.send("Addend some XP")


def setup(bot):
    bot.add_cog(Admin(bot))