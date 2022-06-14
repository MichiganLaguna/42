"""Discord bot for the server 42."""
import os
import logging
from configparser import ConfigParser, ExtendedInterpolation
from typing import Union
from time import time
import aiohttp
import discord

CURR_FOLDER = os.path.dirname(os.path.abspath(__file__))

CONFIG = ConfigParser(interpolation=ExtendedInterpolation())
CONFIG_FILE = os.path.join(CURR_FOLDER, 'config.cfg')
CONFIG.read(CONFIG_FILE)

VARIABLE = ConfigParser(interpolation=ExtendedInterpolation())
VARIABLE_FILE = os.path.join(CURR_FOLDER, CONFIG.get("Language", "default_language"))
VARIABLE.read(VARIABLE_FILE)

os.makedirs(CONFIG.get("Logging", "log_dir"), exist_ok=True)
logger = logging.getLogger(CONFIG.get("Logging", "logger"))
# %Y-%m-%d_%H-%M-%S_%Z : old time format for log files
logger.setLevel(CONFIG.getint("Logging", "logger_level"))
handler = logging.FileHandler(
    filename=f"logs/{time()}.log",
    encoding="utf-8",
    mode="w",
)
handler.setFormatter(
    logging.Formatter(CONFIG.get("Logging", "handler_format"))
)
logger.addHandler(handler)

TOKEN = CONFIG.get("Bot", "token")
PREFIX = CONFIG.get("Bot", "prefix")

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self) -> None:
        """Prints when the bot is ready."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def create_invite(self, guild: Union[discord.Guild, discord.ChannelType], *args, **kwargs) -> discord.Invite:
        """Creates an invite for the given guild redirecting to the first text channel or to the channel submited."""
        if isinstance(guild, discord.ChannelType):
            _channel = guild
        elif isinstance(guild, discord.Guild):
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    _channel = channel
        else:
            return None
        return await _channel.create_invite(*args, **kwargs)

    async def on_message(self, message):
        """Prints when a message is sent."""
        if message.author == self.user:
            return

        if message.content.startswith(f"{PREFIX}{VARIABLE.get('OnMessageQ', 'pasta')}") or message.content.startswith(f"{PREFIX}{VARIABLE.get('OnMessageQ', 'pasta_1')}"):
            img = f"{CONFIG.get('Ressources', 'pasta_image_name')}"
            file = discord.File(CONFIG.get("Ressources", "pasta_image"), filename=img)
            embed = discord.Embed(color=int(CONFIG.get("Ressources", "color_0"), 0))
            embed.set_image(url=f"attachment://{img}")
            await message.author.send(embed=embed, file=file)

        if message.content.startswith(f"{PREFIX}{VARIABLE.get('OnMessageQ', 'whereareyou')}"):
            await message.channel.send(f"{VARIABLE.get('OnMessageA', 'whereareyou')}")
            for guild in self.guilds:
                invite = await self.create_invite(guild) # Creates an invite for the guild
                await message.channel.send(invite.url) # Sends the invite to the channel

        if message.content.startswith(f"{PREFIX}cat"):
            async with aiohttp.ClientSession() as session:
                async with session.get("https://aws.random.cat/meow") as resp:
                    if resp.status != 200:
                        answer = f"{resp.status}: {resp.reason}"
                        return await message.channel.send(f"{answer}")
                    data = await resp.json()
                    await message.channel.send(data["file"])

activity = discord.Activity(
    name="How to make good spaghetti",
    type=discord.ActivityType.competing,
)
client = MyClient(activity=activity, intents=discord.Intents.default())

client.run(TOKEN)
