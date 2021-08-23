import asyncio
import datetime
import json
import logging
import math
import os
# for randomString
import random
import string
import sys
import time
import traceback

import click
import discord

from discord.ext import commands
from discord.ext.commands import AutoShardedBot, when_mentioned_or
from discord_webhook import DiscordWebhook
from config import config

logging.basicConfig(level=logging.INFO)
MOD_LIST = config.discord.mod_list.split(",")

EMOJI_ERROR = "\u274C"
EMOJI_OK_BOX = "\U0001F197"
EMOJI_OK_HAND = "\U0001F44C"
EMOJI_INFORMATION = "\u2139"

intents = discord.Intents.default()
intents.members = True
intents.presences = True


async def logchanbot(content: str):
    if len(content) > 1500: content = content[:1500]
    try:
        webhook = DiscordWebhook(url=config.discord.botdbghook, content=f'```{discord.utils.escape_markdown(content)}```')
        webhook.execute()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)


# Steal from https://github.com/cree-py/RemixBot/blob/master/bot.py#L49
async def get_prefix(bot, message):
    """Gets the prefix for the guild"""
    pre_cmd = config.discord.prefixCmd
    if isinstance(message.channel, discord.DMChannel):
        extras = [pre_cmd, 'gb!', '?', '.', '+', '!', '-']
        return when_mentioned_or(*extras)(bot, message)
    extras = [pre_cmd, 'gb!', 'gbs!']
    return when_mentioned_or(*extras)(bot, message)


bot = AutoShardedBot(command_prefix=get_prefix, owner_id=config.discord.ownerID, case_insensitive=True, intents=intents)
bot.remove_command('help')
bot.owner_id = config.discord.ownerID


@bot.event
async def on_shard_ready(shard_id):
    print(f'Shard {shard_id} connected')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    bot.start_time = datetime.datetime.now()
    await bot.change_presence(status=discord.Status.online)


@bot.command(usage="load <cog>")
@commands.is_owner()
async def load(ctx, extension):
    """Load specified cog"""
    extension = extension.lower()
    bot.load_extension(f'cogs.{extension}')
    await ctx.send('{} has been loaded.'.format(extension.capitalize()))


@bot.command(usage="unload <cog>")
@commands.is_owner()
async def unload(ctx, extension):
    """Unload specified cog"""
    extension = extension.lower()
    bot.unload_extension(f'cogs.{extension}')
    await ctx.send('{} has been unloaded.'.format(extension.capitalize()))


@bot.command(usage="reload <cog/guilds/utils/all>")
@commands.is_owner()
async def reload(ctx, extension):
    """Reload specified cog"""
    extension = extension.lower()
    bot.reload_extension(f'cogs.{extension}')
    await ctx.send('{} has been reloaded.'.format(extension.capitalize()))


# function to return if input string is ascii
def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def truncate(number, digits) -> float:
    stepper = pow(10.0, digits)
    return math.trunc(stepper * number) / stepper


@click.command()
def main():
    for filename in os.listdir('./cogs/'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')

    bot.run(config.discord.token, reconnect=True)

if __name__ == '__main__':
    main()