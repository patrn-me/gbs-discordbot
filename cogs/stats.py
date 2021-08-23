import sys
import traceback
from datetime import datetime
import time, timeago

import discord
from discord.ext import commands
import aiohttp, asyncio
import json

from web3 import Web3
from web3.middleware import geth_poa_middleware

import Bot
from Bot import EMOJI_ERROR, EMOJI_OK_BOX, EMOJI_OK_HAND, EMOJI_INFORMATION, logchanbot
from config import config


class Stats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage='stats', aliases=['stat'], description="Statistic")
    async def stats(self, ctx):
        try:
            # HTTPProvider:
            w3 = Web3(Web3.HTTPProvider(config.gbs.endpoint))

            # inject the poa compatibility middleware to the innermost layer
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            embed = discord.Embed(title="Statistic", description="GoodBoi Society on Ethereum", timestamp=datetime.utcnow())
            
            # Get block number
            timeout = 32
            data = '{"jsonrpc":"2.0", "method":"eth_blockNumber", "params":[], "id":1}'
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(config.gbs.endpoint, headers={'Content-Type': 'application/json'}, json=json.loads(data), timeout=timeout) as response:
                        if response.status == 200:
                            res_data = await response.read()
                            res_data = res_data.decode('utf-8')
                            await session.close()
                            decoded_data = json.loads(res_data)
                            if decoded_data and 'result' in decoded_data:
                                height = int(decoded_data['result'], 16)
                                embed.add_field(name="Network Height", value="{:,.0f}".format(height), inline=False)
            except asyncio.TimeoutError:
                print('TIMEOUT: get block number {}s for TOKEN {}'.format(timeout))
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
            embed.add_field(name="Contract", value="{}".format(config.gbs.contract), inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            print(traceback.format_exc())


def setup(bot):
    bot.add_cog(Stats(bot))
