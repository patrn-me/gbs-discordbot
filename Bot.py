import asyncio, aiohttp
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

from web3 import Web3
from web3.middleware import geth_poa_middleware

import click
import discord
import sqlite3

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


def db_verify_login(userId: int, address: str):
    con = sqlite3.connect(config.gbs.path_db_verify)
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE LOWER(publicAddress)=? AND username=? LIMIT 1", (address.lower(), str(userId), ))
    result = cur.fetchone()
    con.close()
    if result:
        return result
    return None


def db_turn_verified_on(userId: int, address: str):
    try:
        con = sqlite3.connect(config.gbs.path_db_verify)
        cur = con.cursor()
        cur.execute("UPDATE users SET isVerified=1, verifiedDate=? WHERE LOWER(publicAddress)=? AND username=? AND isVerified=0 LIMIT 1", (int(time.time()), address.lower(), str(userId, )))
        con.commit()
        con.close()
        return True
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
    return None


def db_turn_verified_off(userId: int):
    try:
        con = sqlite3.connect(config.gbs.path_db_verify)
        cur = con.cursor()
        cur.execute("UPDATE users SET isVerified=0, unverifiedDate=? WHERE username=? AND isVerified=1 LIMIT 1", (int(time.time()), str(userId), ))
        con.commit()
        con.close()
        return True
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
    return None


def db_verify_if_address_exists(address: str):
    try:
        con = sqlite3.connect(config.gbs.path_db_verify)
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE LOWER(publicAddress)=? AND isVerified=1 LIMIT 1", (address.lower(), ))
        result = cur.fetchone()
        con.close()
        if result:
            return result
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
    return None


def db_if_user_verified(userId: str):
    con = sqlite3.connect(config.gbs.path_db_verify)
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND isVerified=1 LIMIT 1", (userId, ))
    result = cur.fetchone()
    con.close()
    if result:
        return result
    return None


async def erc_validate_address(address: str):
    try:
        # HTTPProvider:
        w3 = Web3(Web3.HTTPProvider(config.gbs.endpoint))

        # inject the poa compatibility middleware to the innermost layer
        # w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        return w3.toChecksumAddress(address)
    except ValueError:
        pass
        #traceback.print_exc(file=sys.stdout)
    return None


async def erc_get_balance_token(address: str):
    try:
        validate_address = await erc_validate_address(address)
        if validate_address is None: return None

        timeout = 32
        data = '{"jsonrpc":"2.0","method":"eth_call","params":[{"to": "'+config.gbs.contract+'", "data": "0x70a08231000000000000000000000000'+address[2:]+'"}, "latest"],"id":1}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(config.gbs.endpoint, headers={'Content-Type': 'application/json'}, json=json.loads(data), timeout=timeout) as response:
                    if response.status == 200:
                        res_data = await response.read()
                        res_data = res_data.decode('utf-8')
                        await session.close()
                        decoded_data = json.loads(res_data)
                        if decoded_data and 'result' in decoded_data:
                            if decoded_data['result'] == "0x":
                                balance = 0
                            else:
                                balance = int(decoded_data['result'], 16)
                            return balance
        except asyncio.TimeoutError:
            print('TIMEOUT: get balance for {}s'.format(timeout))
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
    except ValueError:
        traceback.print_exc(file=sys.stdout)


async def erc_get_totalsupply_token(contract: str):
    try:
        validate_address = await erc_validate_address(contract)
        if validate_address is None: return None

        # 0x06fdde03 -> [ function ] name
        # 0x095ea7b3 -> [ function ] approve
        # 0x18160ddd -> [ function ] totalSupply    OK
        # 0x23b872dd -> [ function ] transferFrom
        # 0x313ce567 -> [ function ] decimals
        # 0x475a9fa9 -> [ function ] issueTokens
        # 0x70a08231 -> [ function ] balanceOf
        # 0x95d89b41 -> [ function ] symbol
        # 0xa9059cbb -> [ function ] transfer
        # 0xdd62ed3e -> [ function ] allowance
        # 0xddf252ad -> [ event ] Transfer
        # 0x8c5be1e5 -> [ event ] Approval

        # curl http://localhost:8545 \
        # -X POST \
        # -H "Content-Type: application/json" \
        # -d '{"jsonrpc":"2.0","method":"eth_call","params":[{"to": "0x4A94844aC9d93BaE2B48f0b10B20B7EF1225188D", "data": "0x18160ddd"}, "latest"],"id":0}'

        timeout = 32
        data = '{"jsonrpc":"2.0","method":"eth_call","params":[{"to": "'+config.gbs.contract+'", "data": "0x18160ddd"}, "latest"],"id":1}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(config.gbs.endpoint, headers={'Content-Type': 'application/json'}, json=json.loads(data), timeout=timeout) as response:
                    if response.status == 200:
                        res_data = await response.read()
                        res_data = res_data.decode('utf-8')
                        await session.close()
                        decoded_data = json.loads(res_data)
                        if decoded_data and 'result' in decoded_data:
                            if decoded_data['result'] == "0x":
                                supply = 0
                            else:
                                supply = int(decoded_data['result'], 16)
                            return supply
        except asyncio.TimeoutError:
            print('TIMEOUT: get supply for {}s'.format(timeout))
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
    except ValueError:
        traceback.print_exc(file=sys.stdout)


def db_verify_if_address_exists(address: str):
    try:
        con = sqlite3.connect(config.gbs.path_db_verify)
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE LOWER(publicAddress)=? AND isVerified=1 LIMIT 1", (address.lower(), ))
        result = cur.fetchone()
        con.close()
        if result:
            return result
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
    return None


# Check ownership of each address which was verified
async def check_ownership_update():
    INTERVAL_EACH = config.gbs.interval_balance
    while True:
        await asyncio.sleep(INTERVAL_EACH)
        start = time.time()
        try:
            con = sqlite3.connect(config.gbs.path_db_verify)
            cur = con.cursor()
            cur.execute("SELECT username, publicAddress FROM users WHERE isVerified=1")
            result = cur.fetchall()
            if result and len(result) > 0:
                # Check balance
                for item in result:
                    try:
                        get_balance = await erc_get_balance_token(item[1])
                        if get_balance == 0:
                            # If they do not have gbs, Find user
                            get_guild = bot.get_guild(id=config.gbs.guild_watch)
                            get_member_chan = bot.get_channel(id=config.gbs.member_chan)
                            if get_guild:
                                member = get_guild.get_member(int(item[0]))
                                set_verify_off = db_turn_verified_off(member.id)
                                if member and set_verify_off:
                                    try:
                                        await member.send('Your address `{}` does not have any GBS now.'.format(item[1]))
                                    except Exception as e:
                                        print(traceback.format_exc())
                                    try:
                                        gbs_role = discord.utils.get(get_guild.roles, name=config.gbs.role_name)
                                        if gbs_role and member.roles and gbs_role in member.roles:
                                            await member.remove_roles(gbs_role)
                                            # message him
                                            try:
                                                await member.send(f'Your role has been removed!')
                                            except Exception as e:
                                                print(traceback.format_exc())
                                            # message channel
                                            try:
                                                await get_member_chan.send(f'Role of user {member.name}#{member.discriminator} / `{member.id}` has been removed!')
                                            except Exception as e:
                                                print(traceback.format_exc())
                                            print('Remove role of user: {}'.format(item[0]))
                                            
                                    except Exception as e:
                                        print(traceback.format_exc())
                    except Exception as e:
                        print(traceback.format_exc())
        except Exception as e:
            print(e)
        end = time.time()
        await asyncio.sleep(INTERVAL_EACH)


@click.command()
def main():
    bot.loop.create_task(check_ownership_update())
    for filename in os.listdir('./cogs/'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')

    bot.run(config.discord.token, reconnect=True)

if __name__ == '__main__':
    main()