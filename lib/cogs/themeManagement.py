import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Cog, command
from lib.bot import LOG_CHANNEL_ID, OWNER_IDS, SUBMIT_CHANNEL_ID, GUILD_ID
from ..db import db

class ThemeManagement(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("Theme management cog ready")


    @app_commands.command(name="suggestions", description="Approve or reject suggested themes.")
    @app_commands.default_permissions(administrator=True)
    async def process_suggestions(self, interaction:discord.Interaction):
        view: discord.ui.View = ThemeView(timeout=None)
        suggestion = db.field("SELECT themeName FROM themes WHERE themeStatus = 0 LIMIT 1")
        message = await interaction.response.send_message(suggestion, view=view)
        view.message = message


    @app_commands.command(name="show", description="Shows a list of things")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(theme_status="Status of themes to show")
    @app_commands.choices(theme_status=[
        app_commands.Choice(name="suggestions", value=1),
        app_commands.Choice(name="rejected", value=2),
        app_commands.Choice(name="approved", value=3),
        app_commands.Choice(name="daily", value=4),
        app_commands.Choice(name="voters", value=5),
    ])
    async def show(self, interaction:discord.Interaction, theme_status:int):
        match theme_status:
            case 1:
                listOfSuggestions = db.column("SELECT themeName FROM themes WHERE themeStatus = 0 LIMIT 50")
                await interaction.response.send_message(listOfSuggestions)
            case 2:
                await interaction.response.send_message("List of all rejected themes: ")
                listOfRejected = db.column("SELECT themeName FROM themes WHERE themeStatus = -1")
                for i in range(50, len(listOfRejected), 50):
                    await interaction.followup.send(listOfRejected[i-50:i])
                    if i+50 > len(listOfRejected):
                        await interaction.followup.send(listOfRejected[i:])
            case 3:
                await interaction.response.send_message("List of all approved themes: ")
                listOfApproved= db.column("SELECT themeName FROM themes WHERE themeStatus = 1")
                for i in range(50, len(listOfApproved), 50):
                    await interaction.followup.send(listOfApproved[i-50:i])
                    if i+50 > len(listOfApproved):
                        await interaction.followup.send(listOfApproved[i:])
            case 4:
                await interaction.response.send_message(db.column("SELECT themeName FROM themes WHERE themeStatus = 1 ORDER BY lastUsed LIMIT 50"))
            case 5:
                voters = db.records("SELECT voterID, count(votingMsgID) as numOfVotes FROM votes GROUP BY voterID ORDER BY numOfVotes DESC")
                names = ""
                for id, count in voters:
                    try:
                        names += self.bot.get_user(id).display_name +": " + str(count) + ", \n"
                    except:
                        pass
                await interaction.response.send_message(names)
            case _:
                await interaction.response.send_message("Please select one of the options")

    @app_commands.command(name="set_used", description="Set if theme recently used")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(set_to="Status to set to")
    @app_commands.choices(set_to=[
        app_commands.Choice(name="used", value=1),
        app_commands.Choice(name="unused", value=2),
    ])
    async def set_theme_used(self, interaction:discord.Interaction, theme:str, set_to:int):
        if db.field("SELECT * FROM themes WHERE themeName = ?", theme) != None:
            match set_to:
                case 1:
                    db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '),theme)
                    await interaction.response.send_message("Theme set to used.")
                case 2:
                    db.execute("UPDATE themes SET lastUsed = '2011-11-11 11:11:11' WHERE themeName = ?", theme)
                    await interaction.response.send_message("Theme set to not used.")
        else:
            await interaction.response.send_message("Theme not found.")

class ThemeView(discord.ui.View):
    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction:discord.Interaction, button:discord.ui.button):
        db.execute("UPDATE themes SET themeStatus = -1 WHERE themeName = ?", interaction.message.content)
        await self.next_theme(interaction, button)
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction:discord.Interaction, button:discord.ui.button):
        db.execute("UPDATE themes SET themeStatus = 1 WHERE themeName = ?", interaction.message.content)
        await self.next_theme(interaction, button)

    async def next_theme(self, interaction:discord.Interaction, button:discord.ui.button):
        suggestion = db.field("SELECT themeName FROM themes WHERE themeStatus = 0 LIMIT 1")
        if suggestion is None:
            for item in self.children:
                item.disabled = True
            await interaction.followup.send("Out of suggestions")
        else:
            await interaction.response.edit_message(content=suggestion)

async def setup(bot):
    await bot.add_cog(ThemeManagement(bot), guilds = [discord.Object(id = GUILD_ID)])