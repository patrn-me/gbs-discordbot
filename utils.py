import asyncio
import datetime
import difflib
import re
from enum import Enum

import discord
import numpy as np
from discord.embeds import _EmptyEmbed
from discord.ext.commands import BadArgument, Converter


class MemberLookupConverter(discord.ext.commands.MemberConverter):
    async def convert(self, ctx, mem, guild: discord.Guild = None) -> discord.Member:
        if not ctx.guild:
            ctx.guild = guild

        if not mem.isdigit():
            if isinstance(mem, str):
                members = ctx.guild.members
                if len(mem) > 5 and mem[-5] == '#':
                    # The 5 length is checking to see if #0000 is in the string,
                    # as a#0000 has a length of 6, the minimum for a potential
                    # discriminator lookup.
                    potential_discriminator = mem[-4:]

                    # do the actual lookup and return if found
                    # if it isn't found then we'll do a full name lookup below.
                    result = discord.utils.get(members, name=mem[:-5], discriminator=potential_discriminator)
                    if result is not None:
                        return result

                def pred(m):
                    if m.nick:
                        if " | " in m.nick:
                            names = m.nick.split(" | ")
                            for n in names:
                                if "".join([m.lower() for m in n if m.isalpha()]) == mem:
                                    return True
                        else:
                            if "".join([m.lower() for m in m.nick if m.isalpha()]) == mem:
                                return True
                    return False

                res = discord.utils.find(pred, members)
                if res is not None:
                    return res

            try:
                member = await super().convert(ctx, mem)  # Convert parameter to discord.member
                return member
            except discord.ext.commands.BadArgument:
                pass

            nicks = []
            mems = []
            for m in ctx.guild.members:
                if m.nick:
                    nicks.append(m.nick.lower())
                    mems.append(m)

            res = difflib.get_close_matches(mem.lower(), nicks, n=1, cutoff=0.8)
            if res:
                index = nicks.index(res[0])
                return mems[index]

            desc = f"No members found with the name: {mem}. "
            raise BadArgument(desc)
        else:
            try:
                member = await super().convert(ctx, mem)  # Convert parameter to discord.member
                return member
            except discord.ext.commands.BadArgument:
                raise BadArgument(f"No members found with the name: {mem}"
                                  "Check your spelling and try again!")


class EmbedPaginator:

    def __init__(self, client, ctx, pages):
        self.client = client
        self.ctx = ctx
        self.pages = pages

    async def paginate(self):
        if self.pages:
            pagenum = 0
            embed: discord.Embed = self.pages[pagenum]
            if not isinstance(embed.title, _EmptyEmbed):
                if f" (Page {pagenum + 1}/{len(self.pages)})" not in str(embed.title):
                    embed.title = embed.title + f" (Page {pagenum + 1}/{len(self.pages)})"
            else:
                embed.title = f" (Page {pagenum + 1}/{len(self.pages)})"
            msg = await self.ctx.send(embed=self.pages[pagenum])
            await msg.add_reaction("⏮️")
            await msg.add_reaction("⬅️")
            await msg.add_reaction("⏹️")
            await msg.add_reaction("➡️")
            await msg.add_reaction("⏭️")

            starttime = datetime.datetime.utcnow()
            timeleft = 300  # 5 minute timeout
            while True:
                def check(react, usr):
                    return not usr.bot and react.message.id == msg.id and usr.id == self.ctx.author.id and str(react.emoji) in \
                           ["⏮️", "⬅️", "⏹️", "➡️", "⏭️"]

                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=timeleft, check=check)
                except asyncio.TimeoutError:
                    return await self.end_pagination(msg)

                if msg.guild:
                    await msg.remove_reaction(reaction.emoji, self.ctx.author)
                timeleft = 300 - (datetime.datetime.utcnow() - starttime).seconds
                if str(reaction.emoji) == "⬅️":
                    if pagenum == 0:
                        pagenum = len(self.pages) - 1
                    else:
                        pagenum -= 1
                elif str(reaction.emoji) == "➡️":
                    if pagenum == len(self.pages) - 1:
                        pagenum = 0
                    else:
                        pagenum += 1
                elif str(reaction.emoji) == "⏮️":
                    pagenum = 0
                elif str(reaction.emoji) == "⏭️":
                    pagenum = len(self.pages) - 1
                elif str(reaction.emoji) == "⏹️":
                    return await self.end_pagination(msg)
                else:
                    continue

                embed: discord.Embed = self.pages[pagenum]
                if not isinstance(embed.title, _EmptyEmbed):
                    if f" (Page {pagenum + 1}/{len(self.pages)})" not in str(embed.title):
                        embed.title = embed.title + f" (Page {pagenum + 1}/{len(self.pages)})"
                else:
                    embed.title = f" (Page {pagenum + 1}/{len(self.pages)})"
                await msg.edit(embed=self.pages[pagenum])


    async def end_pagination(self, msg):
        try:
            if self.pages:
                await msg.edit(embed=self.pages[0])
            if not isinstance(msg.channel, discord.DMChannel):
                await msg.clear_reactions()
        except discord.NotFound:
            pass

