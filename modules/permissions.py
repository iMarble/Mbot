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
from typing import Union
from discord.ext import commands


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


class permission_control(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def permissions(self, ctx):
        pass

    @permissions.command(pass_context=True)
    async def add(
        self, ctx, users: commands.Greedy[Union[discord.Member, FetchedUser]] = None
    ):
        if ctx.message.author.id == 450647525469454336:
            try:
                async with asqlite.connect(ctx.bot.database_file) as conn:
                    async with conn.cursor() as cursor:
                        for user in users:
                            await cursor.execute(
                                "SELECT * FROM permissions WHERE user_id=?", (user.id)
                            )
                            rows = await cursor.fetchall()
                            if not rows:
                                try:
                                    await cursor.execute(
                                        "INSERT INTO permissions VALUES(?,?,?)",
                                        (str(user), user.id, 1),
                                    )
                                    await conn.commit()
                                except Exception as e:
                                    print(e)
                                await ctx.send("👍🏿")
                            else:
                                await ctx.send(
                                    f"{user.mention} already have permissions!"
                                )
            except:
                pass
        else:
            await ctx.send("You Don't have permissions to use this command!")

    @permissions.command(pass_context=True)
    async def remove(
        self, ctx, users: commands.Greedy[Union[discord.Member, FetchedUser]] = None
    ):
        if ctx.message.author.id == 450647525469454336:
            try:
                async with asqlite.connect(ctx.bot.database_file) as conn:
                    async with conn.cursor() as cursor:
                        for user in users:
                            await cursor.execute(
                                "SELECT * FROM permissions WHERE user_id=?", (user.id)
                            )
                            rows = await cursor.fetchall()
                            if rows:
                                try:
                                    await cursor.execute(
                                        "DELETE FROM permissions WHERE user_id=?",
                                        (user.id),
                                    )
                                    await conn.commit()
                                    await ctx.send("👍🏿")
                                except Exception as e:
                                    print(e)
            except Exception as e:
                print(e)

        else:
            await ctx.send("You Don't have permissions to use this command!")

    @commands.group(invoke_without_command=True)
    async def channels(self, ctx):
        pass

    @channels.command(pass_context=True)
    async def block(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        if ctx.message.author.id == 450647525469454336:
            try:
                async with asqlite.connect(ctx.bot.database_file) as conn:
                    async with conn.cursor() as cursor:
                        for channel in channels:
                            await cursor.execute(
                                "SELECT * FROM permissions WHERE user_id=?",
                                (channel.id),
                            )
                            rows = await cursor.fetchall()
                            if not rows:
                                try:
                                    await cursor.execute(
                                        "INSERT INTO permissions VALUES(?,?,?)",
                                        (str(channel), channel.id, 0),
                                    )
                                    await conn.commit()
                                except Exception as e:
                                    print(e)
                                await ctx.send("👍🏿")
                            else:
                                await ctx.send(f"Already blocked in {channel.mention}")
            except:
                pass
        else:
            await ctx.send("You Don't have permissions to use this command!")

    @channels.command(pass_context=True)
    async def unblock(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        if ctx.message.author.id == 450647525469454336:
            try:
                async with asqlite.connect(ctx.bot.database_file) as conn:
                    async with conn.cursor() as cursor:
                        for channel in channels:
                            await cursor.execute(
                                "SELECT * FROM permissions WHERE user_id=?",
                                (channel.id),
                            )
                            rows = await cursor.fetchall()
                            if rows:
                                try:
                                    await cursor.execute(
                                        "DELETE FROM permissions WHERE user_id=?",
                                        (channel.id),
                                    )
                                    await conn.commit()
                                    await ctx.send("👍🏿")
                                except Exception as e:
                                    print(e)
            except:
                pass
        else:
            await ctx.send("You Don't have permissions to use this command!")


async def setup(bot):
    await bot.add_cog(permission_control(bot))
