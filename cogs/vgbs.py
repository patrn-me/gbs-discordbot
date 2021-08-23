import sys
import traceback
from datetime import datetime
import time, timeago

import discord
from discord.ext import commands
import aiohttp, asyncio
import json

import Bot
from Bot import EMOJI_ERROR, EMOJI_OK_BOX, EMOJI_OK_HAND, EMOJI_INFORMATION, logchanbot, erc_validate_address, erc_get_balance_token
from config import config


class Vgbs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage='vgbs', description="Verify your GoodBoi Society")
    async def vgbs(self, ctx, ids: str=None, address: str=None):
        get_balance = 0
        if address is None or ids is None:
            await ctx.send('`address` or `doggo id` is missing.')
            return
        else:
            validate_addr = await erc_validate_address(address)
            if validate_addr is None:
                await ctx.send(f'Address: `{address}` is invalid.')
                return
            else:
                try:
                    get_balance = await erc_get_balance_token(address)
                except Exception as e:
                    print(traceback.format_exc())
        try:
            if get_balance == 0:
                await ctx.send(f'Address: `{address}` owns nothing besides salt.')
                return
            else:
                await ctx.send(f'OK, address: `{address}` owns some doggo here..')
                return
        except Exception as e:
            print(traceback.format_exc())


def setup(bot):
    bot.add_cog(Vgbs(bot))
