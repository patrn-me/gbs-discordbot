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


class Gbs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage='gbs', description="Check address gbs")
    async def gbs(self, ctx, address: str=None):
        get_balance = 0
        if address is None:
            await ctx.send('`address` is missing.')
            return
        else:
            validate_addr = await erc_validate_address(address)
            if validate_addr is None:
                await ctx.send(f'{ctx.author.mention} address: `{address}` is invalid.')
                return
            else:
                try:
                    get_balance = await erc_get_balance_token(address)
                except Exception as e:
                    print(traceback.format_exc())
        try:
            embed = discord.Embed(title="GoodBoi Society", description="GoodBoi Society on Ethereum", timestamp=datetime.utcnow())
            embed.add_field(name="Address", value="{}".format(address), inline=False)
            embed.add_field(name="Quantity", value="{}".format(get_balance), inline=False)
            embed.set_footer(text=f"Requested by: {ctx.author.mention}")
            await ctx.send(embed=embed)
        except Exception as e:
            print(traceback.format_exc())


def setup(bot):
    bot.add_cog(Gbs(bot))
