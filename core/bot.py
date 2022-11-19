"""
The MIT License (MIT)

Copyright (c) 2022-Present Marble

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import datetime
import pathlib
import logging

import asqlite
import aiohttp
import discord
from discord.ext import commands

import tomli

import database

with open('core/config.toml', 'rb') as fp:
    config = tomli.load(fp)


class Bot(commands.Bot):
    """Base class for the bot"""
    discord.utils.setup_logging(level=logging.INFO)

    # noinspection PyDunderSlots, PyUnresolvedReferences
    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(command_prefix=None,
                         intents=intents,
                         strip_after_prefix=True)

        self.started: datetime.datetime = datetime.datetime.now(
            tz=datetime.timezone.utc)

    async def setup_hook(self) -> None:
        await self.load_extension('jishaku')
        modules: list[str] = [
            f'{p.parent}.{p.stem}' for p in pathlib.Path('modules').glob('*.py')]

        for module in modules:
            await self.load_extension(module)

        self.database_file = 'database.db'
        self.session = aiohttp.ClientSession()
        self.database = await database.main(self.database_file)

    async def on_ready(self) -> None:
        """called when the bot is ready"""
        print(f'Logged in as {self.user}(ID: {self.user.id})')

    async def get_prefix(self, message):
        try:
            async with asqlite.connect(self.database_file) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT * FROM prefix WHERE guild=?",
                                         (message.guild.id))
                    rows = await cursor.fetchall()
                    prefix_list = []
                    for row in rows:
                        prefix_list.append(row[2])
        except Exception as e:
            print(e)
        return commands.when_mentioned_or('yo bro', *prefix_list)(self,
                                                                  message)

    async def close(self) -> None:
        await super().close()

        await self.session.close()
