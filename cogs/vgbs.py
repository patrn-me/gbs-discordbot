import sys
import traceback
from datetime import datetime
import time, timeago

import discord
from discord.ext import commands
import aiohttp, asyncio
import json

import Bot
from Bot import EMOJI_ERROR, EMOJI_OK_BOX, EMOJI_OK_HAND, EMOJI_INFORMATION, logchanbot, erc_validate_address, erc_get_balance_token, db_verify_login, db_verify_if_address_exists, db_if_user_verified, db_turn_verified_on
from config import config


class Vgbs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage='vgbs', description="Verify your GoodBoi Society")
    async def vgbs(self, ctx, address: str=None):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send(f'{EMOJI_ERROR} This command can not be in private.')
            return

        # TODO: If he is already verified, skip this command
        # TODO: If an address was verified by other user already. Reject.
        
        get_balance = 0
        if address is None:
            await ctx.send('`address` is missing.')
            return
        else:
            validate_addr = await erc_validate_address(address)
            if validate_addr is None:
                await ctx.send(f'Address: `{address}` is invalid.')
                return
            else:
                # Check if user already verified
                try:
                    check_user_verified = db_if_user_verified(str(ctx.author.id))
                    if check_user_verified:
                        # If he doesn't have a role set
                        get_guild = self.bot.get_guild(id=config.gbs.guild_watch)
                        if get_guild:
                            gbs_role = discord.utils.get(ctx.guild.roles, name=config.gbs.role_name)
                            if gbs_role and gbs_role not in ctx.author.roles:
                                await ctx.author.add_roles(gbs_role)
                                await ctx.send(f'You have been verified now. Thank you!')
                            elif gbs_role and gbs_role in ctx.author.roles:
                                await ctx.send('You already verified.')
                        return
                except Exception as e:
                    print(traceback.format_exc())
                    return
                    
                # Check if address is already used:
                try:
                    check_address = db_verify_if_address_exists(address)
                    if check_address:
                        await ctx.send(f'Address: `{address}` is already used and verified by other users.')
                        return
                except Exception as e:
                    print(traceback.format_exc())
                    return
                try:
                    get_balance = await erc_get_balance_token(address)
                except Exception as e:
                    print(traceback.format_exc())
        try:
            if get_balance == 0:
                await ctx.send(f'Address: `{address}` owns nothing besides salt.')
                return
            else:
                try:
                    verify = db_verify_login(ctx.author.id, address)
                    if verify:
                        # Set isVerified, verifiedDate
                        set_verify = db_turn_verified_on(ctx.author.id, address)
                        if set_verify:
                            get_guild = self.bot.get_guild(id=config.gbs.guild_watch)
                            if get_guild:
                                gbs_role = discord.utils.get(ctx.guild.roles, name=config.gbs.role_name)
                                if gbs_role and gbs_role not in ctx.author.roles:
                                    await ctx.author.add_roles(gbs_role)
                                    await ctx.send(f'You have been verified now. Thank you!')
                                else:
                                    await ctx.send(f'You have been verified now but you have a role already. Thank you!')
                    else:
                        await ctx.send(f'OK, address: `{address}` owns some doggo here but not yet verify ownership. Please sign and put your discord ID here: {config.gbs.verify_link}')
                    return
                except Exception as e:
                    print(traceback.format_exc())
        except Exception as e:
            print(traceback.format_exc())


def setup(bot):
    bot.add_cog(Vgbs(bot))
