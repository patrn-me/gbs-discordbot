import logging
import traceback

import discord
from discord.ext import commands

from Bot import logchanbot


class Error(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_command_error(self, ctx: discord.ext.commands.Context, error):
        """Handles command errors"""
        if hasattr(ctx.command, "on_error"):
            return  # Don't interfere with custom error handlers


def setup(client):
    client.add_cog(Error(client))
