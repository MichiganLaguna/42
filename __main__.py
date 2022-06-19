"""Discord bot for the server 42."""
import os
import logging
import logging.handlers
import discord
import _config
import __logging__ as log

LOG_DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
if not os.path.exists(LOG_DIR_PATH):
    os.makedirs(LOG_DIR_PATH)
logger = logging.getLogger("discord")
handler = log.TimedRotatingFileHandler(LOG_DIR_PATH)
formatter = log.UTCFormatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as : {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith("!hello"):
            await message.channel.send("Hello!")

config = _config.custom_config()
BOT_TOKEN = config.get("bot", "token")
PREFIX = config.get("bot", "prefix")
activity = discord.Activity(
    name="How to make good spaghetti",
    type=discord.ActivityType.competing,
)
intents = discord.Intents.all()

client = MyClient(intents=intents, activity=activity)
# .strftime("%Y-%m-%d")


client.run(BOT_TOKEN)
