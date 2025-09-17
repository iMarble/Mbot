import asyncio
import asqlite
import discord
from discord.ext import commands
import math
from datetime import datetime
import re
import io

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

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spikeleague_channel_ids = [1415313177318785074, 1415313140865957959, 1415312729186766878, 1415311402608103484]
        self.log_channel_id = 597282327772790796
    
    async def cog_load(self):
        asyncio.create_task(self.get_cache())
    
    async def get_cache(self):
        await self.bot.wait_until_ready()
        self.log_channel = self.bot.get_channel(self.log_channel_id)
        self.spike_league_guild = self.bot.get_guild(1180891625384329277)

        # ROLES
        self.spike_league_masters_role = self.spike_league_guild.get_role(1417842856478904350)
        self.spike_league_apex_role = self.spike_league_guild.get_role(1417928943486369903)
        self.spike_league_risers_role = self.spike_league_guild.get_role(1417929081021792429)
        self.spike_league_open_role = self.spike_league_guild.get_role(1417929166271287326)

        self.channel_role_mapping = {
            1415313177318785074: self.spike_league_masters_role,
            1415313140865957959: self.spike_league_apex_role,
            1415312729186766878: self.spike_league_risers_role,
            1415311402608103484: self.spike_league_open_role,
        }

    @commands.Cog.listener(name="on_voice_state_update")
    async def voice_join(self, member, before, after):
        if after.channel is not None and after.channel.id in self.spikeleague_channel_ids:
            
            await self.log_channel.send(f"{member} joined {after.channel.name}")
            
            if any(role not in member.roles for role in self.channel_role_mapping.values()):
                # Check if the channel ID matches one of the keys in the mapping
                if after.channel.id in self.channel_role_mapping:
                    role_to_add = self.channel_role_mapping[after.channel.id]
                    await member.add_roles(role_to_add)
                    await self.log_channel.send(f"Added role {role_to_add.name} to {member}.")


    @commands.Cog.listener(name="on_voice_state_update")
    async def voice_leave(self, member, before, after):
        # Condition 1: Member leaves a voice channel that is in spikeleague_channel_ids
        if after.channel is None and before.channel.id in self.spikeleague_channel_ids:
            # Log the channel the member left
            await self.log_channel.send(f"{member} left {before.channel.name}")

            # Look up the role to remove based on the before.channel.id
            role_to_remove = self.channel_role_mapping.get(before.channel.id)

            if role_to_remove and role_to_remove in member.roles:
                await member.remove_roles(role_to_remove)
                await self.log_channel.send(f"Removed {role_to_remove.name} role from {member}")

        elif after.channel is not None and before.channel.id in self.spikeleague_channel_ids:
            # Log the channel the member left
            await self.log_channel.send(f"{member} left {before.channel.name}")

            # Look up the role to remove based on the before.channel.id
            role_to_remove = self.channel_role_mapping.get(before.channel.id)

            if role_to_remove and role_to_remove in member.roles:
                await member.remove_roles(role_to_remove)
                await self.log_channel.send(f"Removed {role_to_remove.name} role from {member}")

        # Condition 2: If the member leaves a channel that is not in spikeleague_channel_ids or other conditions
        elif after.channel is None or (after.channel.id not in self.spikeleague_channel_ids and before.channel is not None):
            # Log the channel the member left
            await self.log_channel.send(f"{member} left {before.channel.name}")

            # Loop through the channel-role mapping and remove the corresponding role
            for channel_id, role in self.channel_role_mapping.items():
                if before.channel.id == channel_id and role in member.roles:
                    await member.remove_roles(role)
                    await self.log_channel.send(f"Removed {role.name} role from {member}")

async def setup(bot):
    await bot.add_cog(Listeners(bot))
