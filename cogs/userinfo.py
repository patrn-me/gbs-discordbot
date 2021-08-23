import sys
import traceback
from datetime import datetime
import time, timeago

import discord
from discord.ext import commands
import asyncio

import Bot
from Bot import EMOJI_ERROR, EMOJI_OK_BOX, EMOJI_OK_HAND, EMOJI_INFORMATION, logchanbot
from config import config


class UserInfo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage='userinfo', description="Get userinfo")
    async def userinfo(self, ctx, member: discord.Member = None):
        if isinstance(ctx.channel, discord.DMChannel) == True:
            await ctx.send(f'{ctx.author.mention} This command can not be in Direct Message.')
            return
        if member is None:
            member = ctx.author
            userid = str(ctx.author.id)
        else:
            userid = str(member.id)
        try:
            embed = discord.Embed(title="{}'s info".format(member.name), description="Here's what I could find.", timestamp=datetime.utcnow())
            embed.add_field(name="Name", value="{}#{}".format(member.name, member.discriminator), inline=True)
            embed.add_field(name="Display Name", value=member.display_name, inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Status", value=member.status, inline=True)
            embed.add_field(name="Highest role", value=member.top_role)
            embed.add_field(name="Joined", value=str(member.joined_at.strftime("%d-%b-%Y") + ': ' + timeago.format(member.joined_at, datetime.utcnow())))
            embed.add_field(name="Created", value=str(member.created_at.strftime("%d-%b-%Y") + ': ' + timeago.format(member.created_at, datetime.utcnow())))
            embed.set_thumbnail(url=member.avatar_url)
            await ctx.send(embed=embed)
        except Exception as e:
            print(traceback.format_exc())


def setup(bot):
    bot.add_cog(UserInfo(bot))
