"""MIT License

Copyright (c) 2022 Marble

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asqlite
import discord
from discord.ext import commands
import math
from datetime import datetime
import re

time_regex = re.compile(r"(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimeConverter(commands.Converter):
    async def convert(self, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k] * float(v)
            except KeyError:
                raise commands.BadArgument(
                    "{} is an invalid time-key! h/m/s/d are valid!".format(k)
                )
            except ValueError:
                raise commands.BadArgument("{} is not a number!".format(v))
        return time


class FetchedUser(commands.Converter):
    async def convert(ctx, argument):
        if not argument.isdigit():
            raise commands.BadArgument("Not a valid user ID.")
        try:
            return await ctx.bot.fetch_user(argument)
        except discord.NotFound:
            raise commands.BadArgument("User not found.") from None
        except discord.HTTPException:
            raise commands.BadArgument(
                "An error occurred while fetching the user."
            ) from None


class NoPerms(commands.CommandError):
    def __init__(self):
        super().__init__("LO... No perm")


class channel_blocked(commands.CommandError):
    def __init__(self) -> None:
        super().__init__("Disabled in channel")


def perms():
    async def predicate(ctx):
        async with asqlite.connect(ctx.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT * FROM permissions WHERE user_id=?", (ctx.author.id)
                )
                rows = await cursor.fetchall()
                if rows:
                    for row in rows:
                        if ctx.author.id in row:
                            return True
                else:
                    raise NoPerms()

    return commands.check(predicate)


def disable_channel():
    async def predicate(ctx):
        async with asqlite.connect(ctx.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT * FROM permissions WHERE user_id=?", (ctx.channel.id)
                )
                rows = await cursor.fetchall()
                if rows:
                    for row in rows:
                        if ctx.channel.id not in row:
                            raise channel_blocked()
                else:
                    return True

    return commands.check(predicate)


class botcmnds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.update_members.start()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, NoPerms):
            embed = discord.Embed(description=str(error), colour=discord.Colour.green())
            await ctx.send(embed=embed, delete_after=5)

    @commands.command(pass_context=True)
    @perms()
    async def nick(self, ctx, *, name):
        await ctx.message.guild.me.edit(nick=name)
        await ctx.send(f"Changed nickname to {name}")

    @commands.hybrid_command(pass_context=True)
    @disable_channel()
    async def ping(self, ctx):
        embed = discord.Embed(title="🏓 Pong!", colour=discord.Colour.green())
        embed.add_field(
            name="Message Latency",
            value=f"{math.floor(self.bot.latency * 1000)}ms",
            inline=True,
        )
        embed.set_footer(
            text=f"Requested by {ctx.author.name}", icon_url=f"{ctx.author.avatar.url}"
        )
        embed.timestamp = datetime.now()
        await ctx.send(content=None, embed=embed, ephemeral=True)

    @commands.command(pass_context=True)
    @perms()
    async def say(self, ctx, *, arg):
        try:
            await ctx.message.delete()
        except PermissionError:
            pass
        await ctx.send(arg)

    @commands.hybrid_group(invoke_without_command=True)
    @perms()
    async def reactions(self, ctx):
        pass

    @reactions.command()
    @perms()
    async def start(
        self,
        ctx,
        user: discord.Member,
        reaction: str,
        guild_: str = None,
        endcount: int = 0,
    ):
        if guild_ is None:
            guild = self.bot.get_guild(ctx.guild.id)
        else:
            guild = self.bot.get_guild(int(guild_))
        global emoji
        emoji = discord.utils.get(guild.emojis, name=reaction)
        if emoji is None:
            emoji = reaction
        else:
            emoji = emoji

        reactiondata = (
            user.name,
            user.id,
            ctx.guild.id,
            str(emoji).lstrip("<").rstrip(">"),
            0,
            endcount,
        )
        async with asqlite.connect(ctx.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """INSERT INTO reactions(name,user_id,guild,emote,
                                            start_count,end_count)VALUES(?,?,?,?,?,?)""",
                        reactiondata,
                    )
                    await conn.commit()
                    await ctx.send(
                        f"Started reacting {emoji} on {user} messages!", ephemeral=True
                    )
                except Exception as e:
                    print(e)

    @reactions.command()
    @perms()
    async def stop(self, ctx, user: discord.Member = None):
        async with asqlite.connect(ctx.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "DELETE FROM reactions WHERE user_id=?", (user.id)
                    )
                    await conn.commit()
                    await ctx.send(
                        f"Stopped Reacting on {user} messages!", ephemeral=True
                    )
                except Exception as e:
                    print(e)

    @commands.hybrid_group(invoke_without_command=True)
    async def message(self, ctx):
        pass

    @message.command(pass_context=True)
    @perms()
    async def start(
        self,
        ctx,
        response: str,
        message: str,
        author: discord.User = None,
    ):
        if author is None:
            authorid = 0
        else:
            authorid = author.id
        async with asqlite.connect(ctx.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """INSERT INTO message(channel,author,message,response)
                                            VALUES(?,?,?,?)""",
                        (ctx.channel.id, authorid, message, response),
                    )
                    await conn.commit()
                    await ctx.send("Added message response!", ephemeral=True)
                except Exception as e:
                    print(e)

    @message.command()
    @perms()
    async def stop(self, ctx, channel: discord.TextChannel, message):
        try:
            async with asqlite.connect(ctx.bot.database_file) as conn:
                async with conn.cursor() as cursor:
                    try:
                        await cursor.execute(
                            "DELETE FROM message WHERE channel=? AND message=?",
                            (channel.id, message),
                        )
                        await conn.commit()
                        await ctx.send("Stopped!", ephemeral=True)
                    except Exception as e:
                        print(e)
        except Exception as e:
            print(e)

    @commands.Cog.listener(name="on_message")
    async def message1(self, m):
        async with asqlite.connect(self.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT * FROM reactions")
                data = await cursor.fetchall()
                await cursor.execute("SELECT * FROM message")
                messagedata = await cursor.fetchall()
                if [x for x in data if m.author.id in x]:
                    await cursor.execute(
                        "SELECT * FROM reactions WHERE user_id=?", (m.author.id)
                    )
                    reactiondata = await cursor.fetchall()
                    for i in reactiondata:
                        if i[4] != i[5]:
                            await cursor.execute(
                                """'UPDATE reactions set start_count=?
                                                     where user_id=?""",
                                (i[4] + 1, m.author.id),
                            )
                            await conn.commit()
                        elif i[4] == i[5]:
                            await cursor.execute(
                                """UPDATE reactions set start_count=?
                                                    where user_id=?""",
                                (0, m.author.id),
                            )
                            await conn.commit()
                            await m.add_reaction(i[3])
                if not m.author.bot:
                    if [x for x in messagedata if m.channel.id in x]:
                        await cursor.execute(
                            "SELECT * FROM message where channel=?", (m.channel.id)
                        )
                        messages = await cursor.fetchall()
                        for i in messages:
                            if m.author.id == i[1] and m.content == i[2]:
                                await m.reply(i[3], mention_author=False)
                                return
                            elif i[1] == 0 and m.content == i[2]:
                                await m.channel.send(i[3])


async def setup(bot):
    await bot.add_cog(botcmnds(bot))
