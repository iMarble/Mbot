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
from .useful import NoPerms
from os import listdir
from os.path import isfile, join


cogs_dir = "modules"


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


class reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.guild_only()
    @perms()
    async def reload(self, ctx):
        for extension in [
            f.replace(".py", "") for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))
        ]:
            try:
                await self.bot.reload_extension(cogs_dir + "." + extension)

            except commands.ExtensionError as e:
                await ctx.send(f"{e.__class__.__name__}: {e}")
        await ctx.send("Done\N{OK HAND SIGN}")

    @commands.command(hidden=True)
    @perms()
    async def sync(self, ctx, guild=None):
        try:
            if guild:
                await self.bot.tree.sync(guild=discord.Object(id=int(guild)))
            else:
                await self.bot.tree.sync()
            await ctx.send("synced")
        except:
            pass


async def setup(bot):
    await bot.add_cog(reload(bot))
