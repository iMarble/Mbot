"""MIT License

Copyright (c) 2022-Present Marble

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
import datetime
from typing import Union, List, Dict
from discord.ext import commands

import core


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


class ChatModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_user_whitelisted(self, user_id: int) -> bool:
        """Check if a user is whitelisted for chat"""
        async with asqlite.connect(self.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT * FROM chat_whitelist WHERE user_id=?", (user_id,)
                )
                rows = await cursor.fetchall()
                return len(rows) > 0

    async def get_conversation_history(self, user_id: int, limit: int = 20) -> List[Dict[str, str]]:
        """Get conversation history for a user"""
        async with asqlite.connect(self.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT role, content FROM chat_memory 
                       WHERE user_id = ? 
                       ORDER BY timestamp DESC 
                       LIMIT ?""",
                    (user_id, limit * 2)  # Get more to account for pairs
                )
                rows = await cursor.fetchall()
                # Reverse to get chronological order
                messages = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
                return messages

    async def save_message(self, user_id: int, role: str, content: str):
        """Save a message to conversation history"""
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        async with asqlite.connect(self.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """INSERT INTO chat_memory (user_id, role, content, timestamp) 
                       VALUES (?, ?, ?, ?)""",
                    (user_id, role, content, timestamp)
                )
                await conn.commit()

    async def clear_conversation_history(self, user_id: int):
        """Clear conversation history for a user"""
        async with asqlite.connect(self.bot.database_file) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM chat_memory WHERE user_id = ?",
                    (user_id,)
                )
                await conn.commit()

    def fix_markdown(self, text: str) -> str:
        """Fix markdown formatting for Discord"""
        # Discord markdown is mostly compatible, but we need to ensure:
        # 1. Proper line breaks (Discord needs \n)
        # 2. Code blocks are properly formatted
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Ensure code blocks are properly formatted
        # Check for unclosed code blocks
        code_block_count = text.count('```')
        if code_block_count % 2 != 0:
            # Unclosed code block, close it
            text += '\n```'
        
        return text

    async def get_groq_response(self, message_content: str, user_id: int) -> str:
        """Get response from Groq API with conversation history"""
        try:
            api_key = core.config["GROQ"]["api_key"]
            model = core.config["GROQ"].get("model", "llama-3.1-70b-versatile")
        except KeyError:
            return "Error: Groq API configuration not found in config.toml"

        # Get conversation history
        history = await self.get_conversation_history(user_id)
        
        # Build messages list with history + current message
        messages = history.copy()
        messages.append({"role": "user", "content": message_content})

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
        }

        try:
            async with self.bot.session.post(
                url, headers=headers, json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_content = data["choices"][0]["message"]["content"]
                    
                    # Save user message and assistant response to history
                    await self.save_message(user_id, "user", message_content)
                    await self.save_message(user_id, "assistant", response_content)
                    
                    return response_content
                elif response.status == 401:
                    return "Error: Invalid Groq API key"
                elif response.status == 429:
                    return "Error: Rate limit exceeded. Please try again later."
                else:
                    error_text = await response.text()
                    return f"Error: API request failed with status {response.status}: {error_text}"
        except Exception as e:
            return f"Error: Failed to connect to Groq API: {str(e)}"

    def should_respond_to_message(self, message: discord.Message) -> bool:
        """Check if bot should respond to this message"""
        # Check if bot is mentioned
        if self.bot.user in message.mentions:
            return True

        return False

    # @commands.group(invoke_without_command=True)
    # async def chat(self, ctx):
    #     """Chat with the bot using Groq LLM"""
    #     pass

    @commands.group(invoke_without_command=True)
    async def whitelist(self, ctx):
        """Manage chat whitelist"""
        pass

    @whitelist.command(pass_context=True)
    async def add(
        self, ctx, users: commands.Greedy[Union[discord.Member, FetchedUser]] = None
    ):
        """Add users to chat whitelist"""
        if ctx.message.author.id == 450647525469454336:
            if not users:
                await ctx.send("Please specify at least one user to add.")
                return

            try:
                async with asqlite.connect(ctx.bot.database_file) as conn:
                    async with conn.cursor() as cursor:
                        for user in users:
                            await cursor.execute(
                                "SELECT * FROM chat_whitelist WHERE user_id=?", (user.id,)
                            )
                            rows = await cursor.fetchall()
                            if not rows:
                                try:
                                    await cursor.execute(
                                        "INSERT INTO chat_whitelist VALUES(?,?)",
                                        (user.id, str(user)),
                                    )
                                    await conn.commit()
                                    await ctx.send(f"Added {user.mention} to chat whitelist! 👍🏿")
                                except Exception as e:
                                    print(e)
                                    await ctx.send(f"Error adding {user.mention}: {str(e)}")
                            else:
                                await ctx.send(
                                    f"{user.mention} is already whitelisted!"
                                )
            except Exception as e:
                print(e)
                await ctx.send("An error occurred while adding users to whitelist.")
        else:
            await ctx.send("You don't have permissions to use this command!")

    @whitelist.command(pass_context=True)
    async def remove(
        self, ctx, users: commands.Greedy[Union[discord.Member, FetchedUser]] = None
    ):
        """Remove users from chat whitelist"""
        if ctx.message.author.id == 450647525469454336:
            if not users:
                await ctx.send("Please specify at least one user to remove.")
                return

            try:
                async with asqlite.connect(ctx.bot.database_file) as conn:
                    async with conn.cursor() as cursor:
                        for user in users:
                            await cursor.execute(
                                "SELECT * FROM chat_whitelist WHERE user_id=?", (user.id,)
                            )
                            rows = await cursor.fetchall()
                            if rows:
                                try:
                                    await cursor.execute(
                                        "DELETE FROM chat_whitelist WHERE user_id=?",
                                        (user.id,),
                                    )
                                    await conn.commit()
                                    await ctx.send(f"Removed {user.mention} from chat whitelist! 👍🏿")
                                except Exception as e:
                                    print(e)
                                    await ctx.send(f"Error removing {user.mention}: {str(e)}")
                            else:
                                await ctx.send(f"{user.mention} is not whitelisted!")
            except Exception as e:
                print(e)
                await ctx.send("An error occurred while removing users from whitelist.")
        else:
            await ctx.send("You don't have permissions to use this command!")

    @whitelist.command(pass_context=True)
    async def list(self, ctx):
        """List all whitelisted users"""
        if ctx.message.author.id == 450647525469454336:
            try:
                async with asqlite.connect(ctx.bot.database_file) as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT * FROM chat_whitelist")
                        rows = await cursor.fetchall()
                        if rows:
                            user_list = "\n".join([f"• {row[1]} (ID: {row[0]})" for row in rows])
                            embed = discord.Embed(
                                title="Chat Whitelist",
                                description=user_list,
                                colour=discord.Colour.green(),
                            )
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send("No users are currently whitelisted.")
            except Exception as e:
                print(e)
                await ctx.send("An error occurred while fetching the whitelist.")
        else:
            await ctx.send("You don't have permissions to use this command!")

    @commands.command(pass_context=True)
    async def clear_memory(self, ctx):
        """Clear your conversation history with the bot"""
        if not await self.is_user_whitelisted(ctx.author.id):
            await ctx.send("You are not whitelisted to use chat features.")
            return
        
        await self.clear_conversation_history(ctx.author.id)
        await ctx.send("Your conversation history has been cleared! 👍🏿")

    @commands.command(pass_context=True)
    async def clear_user_memory(
        self, ctx, user: Union[discord.Member, FetchedUser] = None
    ):
        """Clear conversation history for a specific user (Admin only)"""
        if ctx.message.author.id != 450647525469454336:
            await ctx.send("You don't have permissions to use this command!")
            return

        if not user:
            await ctx.send("Please specify a user to clear memory for.")
            return

        await self.clear_conversation_history(user.id)
        await ctx.send(f"Cleared conversation history for {user.mention}! 👍🏿")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle messages from whitelisted users"""
        # Ignore bots and DMs
        if message.author.bot or message.guild is None:
            return

        # Check if user is whitelisted
        if not await self.is_user_whitelisted(message.author.id):
            return

        # Check if bot should respond (mentioned or prefix used)
        if not self.should_respond_to_message(message):
            return

        # Extract message content (remove mention/prefix)
        content = message.content

        # Remove bot mention
        if self.bot.user in message.mentions:
            content = content.replace(f"<@{self.bot.user.id}>", "").replace(
                f"<@!{self.bot.user.id}>", ""
            )
            content = content.strip()

        # Remove prefix if present
        if message.guild:
            try:
                prefix = self.bot.prefixes[message.guild.id]
                if content.startswith(prefix):
                    content = content[len(prefix) :].strip()
            except KeyError:
                pass

        if content.startswith("yo bro"):
            content = content[7:].strip()

        # Don't process empty messages
        if not content:
            return

        # Show typing indicator
        async with message.channel.typing():
            # Get response from Groq API with conversation history
            response = await self.get_groq_response(content, message.author.id)
            
            # Fix markdown formatting for Discord
            response = self.fix_markdown(response)

            # Send response (split if too long)
            # Discord has a 2000 character limit per message
            if len(response) > 2000:
                # Split into chunks, trying to preserve code blocks
                chunks = []
                current_chunk = ""
                in_code_block = False
                code_block_lang = ""
                
                for line in response.split('\n'):
                    # Check if line starts/ends code blocks
                    if line.strip().startswith('```'):
                        if in_code_block:
                            # Ending code block
                            current_chunk += line + '\n'
                            if len(current_chunk) > 1900:
                                chunks.append(current_chunk)
                                current_chunk = ""
                            in_code_block = False
                            code_block_lang = ""
                        else:
                            # Starting code block - extract language
                            code_block_lang = line.strip()[3:].strip()
                            if len(current_chunk) + len(line) + 1 > 1900:
                                if current_chunk:
                                    chunks.append(current_chunk)
                                current_chunk = line + '\n'
                            else:
                                current_chunk += line + '\n'
                            in_code_block = True
                    else:
                        # Regular line
                        if len(current_chunk) + len(line) + 1 > 1900:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = line + '\n'
                        else:
                            current_chunk += line + '\n'
                
                # Add remaining chunk
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Send chunks
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(response)


async def setup(bot):
    await bot.add_cog(ChatModule(bot))

