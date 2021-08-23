import sys
import traceback
from datetime import datetime

import discord
from discord.ext import commands

import Bot
from Bot import EMOJI_ERROR, EMOJI_OK_BOX, EMOJI_OK_HAND, EMOJI_INFORMATION, logchanbot
from config import config


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return commands.is_owner()


def setup(bot):
    bot.add_cog(Admin(bot))
