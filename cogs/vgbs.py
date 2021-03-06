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
            await ctx.send(f'{EMOJI_ERROR} {ctx.author.mention} This command can not be in private.')
            return
        
        if ctx.channel.id != config.gbs.verify_channel:
            try:
                await ctx.message.delete()
                await ctx.send(f'{EMOJI_ERROR} {ctx.author.mention} Please use <#{str(config.gbs.verify_channel)}>')
            except Exception as e:
                print(traceback.format_exc())
            return

        get_balance = 0
        if address is None:
            await ctx.send(f'{ctx.author.mention} `address` is missing.')
            return
        else:
            validate_addr = await erc_validate_address(address)
            if validate_addr is None:
                await ctx.send(f'{ctx.author.mention}: address `{address}` is invalid.')
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
                            # Message should be delete after success
                            try:
                                await ctx.message.delete()
                            except Exception as e:
                                print(traceback.format_exc())

                            if gbs_role and gbs_role not in ctx.author.roles:
                                await ctx.author.add_roles(gbs_role)
                                await ctx.send(f'{ctx.author.mention} You are verified now. Thank you!')
                            elif gbs_role and gbs_role in ctx.author.roles:
                                await ctx.send(f'{ctx.author.mention} You already verified.')
                        return
                except Exception as e:
                    print(traceback.format_exc())
                    return
                    
                # Check if address is already used:
                try:
                    check_address = db_verify_if_address_exists(address)
                    if check_address:
                        await ctx.send(f'{ctx.author.mention}: address `{address}` is already used and verified by other users.')
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
                await ctx.send(f'{ctx.author.mention}: address `{address}` owns nothing besides salt.')
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
                                    await ctx.send(f'{ctx.author.mention} You are verified now. Thank you!')
                                else:
                                    await ctx.send(f'{ctx.author.mention} You have been verified now but you have a role already. Thank you!')
                    else:
                        await ctx.send(f'{ctx.author.mention} OK, address: `{address}` owns some doggo here but not yet verified ownership. Please sign and put your discord ID here: {config.gbs.verify_link}\nYour Discord ID: `{str(ctx.author.id)}`')
                        # Message should be delete after success
                        try:
                            await ctx.message.delete()
                        except Exception as e:
                            print(traceback.format_exc())
                    return
                except Exception as e:
                    print(traceback.format_exc())
        except Exception as e:
            print(traceback.format_exc())


    @commands.has_permissions(manage_messages=True)
    @commands.command(usage='clear', description="Clear all .vgbs command in verified channel")
    async def clear(self, ctx):
        delete_message_text = ".VGBS"
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send(f'{EMOJI_ERROR} {ctx.author.mention} This command can not be in private.')
            return
        # If it is not in verified channel
        if ctx.channel.id != config.gbs.verify_channel:
            try:
                await ctx.message.delete()
                await ctx.send(f'{EMOJI_ERROR} {ctx.author.mention} Please use <#{str(config.gbs.verify_channel)}> only.')
            except Exception as e:
                print(traceback.format_exc())
            return

        count = 0
        try:
            messages = await ctx.channel.history(limit=1000).flatten()
            if messages and len(messages) > 0:
                for each in messages:
                    if each.content.upper().startswith(delete_message_text):
                        count += 1
                        try:
                            await each.delete()
                        except Exception as e:
                            print(traceback.format_exc())
                            break
                            return
                await ctx.author.send(f'{ctx.author.mention} Found {str(count)} message(s) started with {delete_message_text} in {ctx.channel.mention} and deleted.')
        except Exception as e:
            print(traceback.format_exc())

def setup(bot):
    bot.add_cog(Vgbs(bot))
