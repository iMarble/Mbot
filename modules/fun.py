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
import asyncio


class channel_blocked(commands.CommandError):
    def __init__(self) -> None:
        super().__init__("Disabled in channel")


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


class fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guildids = [493063429133697024, 621609685539225620]

    async def cog_load(self):
        asyncio.create_task(self.get_cache())

    async def get_cache(self):
        await self.bot.wait_until_ready()
        klpd = self.bot.get_guild(493063429129502720)
        global girlrole
        girlrole = klpd.get_role(549498411091492864)
        global channel
        channel = self.bot.get_channel(597282327772790796)
        theghoguild = self.bot.get_guild(572454992355524608)
        global letterg
        global letterh
        global lettero
        global theghoemoji
        global klpdemoji
        letterg = discord.utils.get(theghoguild.emojis, name="G_")
        letterh = discord.utils.get(theghoguild.emojis, name="H_")
        lettero = discord.utils.get(theghoguild.emojis, name="O_")
        theghoemoji = discord.utils.get(theghoguild.emojis, name="thegho")
        klpdemoji = discord.utils.get(theghoguild.emojis, name="klpd")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None and not message.author.bot:
            if message.attachments:
                for attachment in message.attachments:
                    await channel.send(attachment.url)
            embed = discord.Embed(
                description=message.content, colour=discord.Colour.random()
            )
            embed.set_footer(
                text=f"""By {message.author},
                                      ID = {message.author.id} messageID = {message.id}"""
            )
            await channel.send(embed=embed)

        if (
            message.content.lower() == "thegho"
            and message.channel.id in self.guildids
            and girlrole not in message.author.roles
        ):
            for i in (letterg, letterh, lettero, theghoemoji, "🤨"):
                if message.author.id != 687745796506255453:
                    await message.add_reaction(str(i))

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if not msg.attachments:
            await channel.send(
                embed=discord.Embed(description=msg.content, color=msg.author.color)
                .set_author(name=str(msg.author), icon_url=str(msg.author.avatar.url))
                .set_footer(text=f"Guild: {msg.guild.name}")
            )
        if msg.attachments:
            for i in msg.attachments:
                await channel.send(
                    embed=discord.Embed(description=msg.content, color=msg.author.color)
                    .set_author(
                        name=str(msg.author), icon_url=str(msg.author.avatar.url)
                    )
                    .set_footer(text=f"Guild: {msg.guild.name}")
                    .set_image(url=i.proxy_url)
                )


async def setup(bot):
    # asyncio.run(main())
    await bot.add_cog(fun(bot))
