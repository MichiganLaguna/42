"""Discord bot for the server 42."""
import asyncio
import os
import logging
import logging.handlers
from typing import Any, Optional, Union
import discord
from discord import app_commands
import __config__
import __logging__ as log

LOG_DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
if not os.path.exists(LOG_DIR_PATH):
    os.makedirs(LOG_DIR_PATH)
logger = logging.getLogger("discord")
handler = log.TimedRotatingFileHandler(LOG_DIR_PATH, when='D')
formatter = log.UTCFormatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

CONFIG = __config__.CONFIG()

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.synced = False
        self.role = 773879483765751808
    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=CONFIG.GUILD_TEST_ID))
            self.synced = True
        print(f"We have logged in as {self.user}")

BOT_TOKEN = CONFIG.TOKEN
PREFIX = CONFIG.PREFIX
activity = discord.Activity(
    name="How to make good spaghetti",
    type=discord.ActivityType.competing,
)
client = MyClient(intents=discord.Intents.all(), activity=activity)
tree = app_commands.CommandTree(client)

def make_embed(alert: bool = False, title: str = None, description: str = None) -> discord.Embed:
    color = CONFIG.COLOR_2 if alert else CONFIG.COLOR_0
    embed = discord.Embed(color=color)
    if title is not None:
        embed.title = title
    if description is not None:
        embed.description = description
    return embed

async def not_allowed(interaction: discord.Interaction, role_id: int) -> bool:
    if  interaction.guild.get_role(role_id) not in interaction.user.roles:
        embed = make_embed(alert=True)
        embed.description = f"You are not allowed to use this command, {interaction.user}."
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return True
    return False


@tree.command(name='emotes', description="shows all emojis", guild=discord.Object(id=CONFIG.GUILD_TEST_ID))
async def emojis(interaction: discord.Interaction) -> None:
    if await not_allowed(interaction, CONFIG.TEST_ROLE_ID):
        return
    embed = make_embed(title="Emojis", description="")
    for guild in tree.client.guilds:
        emojis_str = ""
        for emoji in guild.emojis:
            emoji_str="<"
            if emoji.animated:
                emoji_str += "a"
            emoji_str += ":" + emoji.name + ":" + str(emoji.id) + ">"
            emojis_str += f"{emoji_str}:`{emoji_str}`\n"
        embed.description += f"{guild.name}:\n{emojis_str}\n"
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
client.run(BOT_TOKEN)
