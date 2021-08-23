import json
import sys
import time
import traceback

import discord
from discord.ext import commands
from googletrans import Translator
from datetime import datetime
import Bot
from config import config

class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        return

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        return

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        return


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        return


    @commands.Cog.listener()
    async def on_message(self, message):
        # should ignore webhook message
        if isinstance(message.channel, discord.DMChannel) == False and message.webhook_id:
            return
        # Ignore bot message too
        if message.author.bot == True:
            return
        return


def setup(bot):
    bot.add_cog(Events(bot))
