import discord
from discord.ext import commands
from .useful import disable_channel


class MyHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return "%s%s %s" % (
            self.context.clean_prefix,
            command.qualified_name,
            command.signature,
        )

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help")
        for cog, _commands in mapping.items():
            filtered = await self.filter_commands(_commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                # if cog_name == "Bots":
                embed.add_field(
                    name=cog_name, value="**\n**".join(command_signatures), inline=False
                )
                # embed.add_field(name='Detail',value="Type help <command> for more details about a
                # command.",inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=self.get_command_signature(command))
        embed.add_field(name="Help", value=command.help)
        alias = command.aliases
        if alias:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_error_message(self, error):
        embed = discord.Embed(title="Error", description=error)
        channel = self.get_destination()
        await channel.send(embed=embed)


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Setting the cog for the help
        help_command = MyHelp()
        help_command.cog = self  # Instance of YourCog class
        bot.help_command = help_command
        bot.help_command.add_check(disable_channel)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
