"""Discord bot for the server 42."""
import logging
from configparser import ConfigParser
from time import time
import aiohttp
import discord

CONFIG = ConfigParser()
FILE_NAME = "config.cfg"
CONFIG.read(FILE_NAME)

logger = logging.getLogger("discord")
# %Y-%m-%d_%H-%M-%S_%Z
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename=f"log/{time()}.log",
    encoding="utf-8",
    mode="w",
)
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

LOG_CHANNEL = CONFIG.getint("Channel", "zbi")
TOKEN = CONFIG.get("Bot", "token")
PREFIX = CONFIG.get("Bot", "prefix")


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        """Prints when the bot is ready."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message):
        """Prints when a message is sent."""
        if message.author == self.user:
            return

        if message.content.startswith(f"{PREFIX}hello"):
            await message.channel.send(f"{PREFIX}hello")

        if message.content.startswith(f"{PREFIX}ping"):
            await message.author.send("Pong!")

        if message.content.startswith(f"{PREFIX}cat"):
            async with aiohttp.ClientSession() as session:
                async with session.get("https://aws.random.cat/meow") as resp:
                    if resp.status != 200:
                        answer = resp.status + resp.reason
                        return await message.channel.send(f"{answer}")
                    data = await resp.json()
                    await message.channel.send(data["file"])


activity = discord.Activity(
    name="How to make good spaghetti",
    type=discord.ActivityType.watching,
)
client = MyClient(activity=activity, intents=discord.Intents.default())
client.run(TOKEN)
