from lib.bot import VOTING_CHANNEL_ID
from discord.ext.commands import Cog
from ..db import db

switcher = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5}

class Reactions(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("reactions cog ready")

    @Cog.listener()
    #works only if msg is cached, so if the bot was running when the message was sent
    async def on_reaction_add(self, reaction, user):
        pass

    @Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        pass

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if (payload.channel_id == VOTING_CHANNEL_ID and not (payload.user_id == self.bot.user.id)):
            print(f"{payload.member.display_name} reacted with {payload.emoji.name}")
            emoji = switcher.get(payload.emoji.name)
            #check if emoji was from 1 to 5 and if voting is still active for this submission
            if emoji != None and db.field("SELECT previousChallengeID FROM currentChallenge WHERE challengeTypeID = 0") == db.field("SELECT challengeID FROM submission WHERE votingMsgID = ?", payload.message_id):
                print("vote added to DB")
                db.execute("REPLACE INTO votes (votingMsgID, voterID, vote) VALUES (?, ?, ?)",payload.message_id, payload.user_id, emoji)
            channel = self.bot.get_channel(payload.channel_id)
            user = self.bot.get_user(payload.user_id)
            msg = await channel.fetch_message(payload.message_id)
            await msg.remove_reaction(payload.emoji, user)


    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        pass

def setup(bot):
    bot.add_cog(Reactions(bot))