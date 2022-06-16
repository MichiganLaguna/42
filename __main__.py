"""Discord bot for the server 42."""
from datetime import datetime
import pytz
import discord
from _logger import custom_logger
import _config
import _client

logger_name = datetime.now(tz=pytz.utc).strftime("%Y-%m-%d")
custom_logger(logger_name)
_= _config.custom_config()
config = _["config"]
variable = _["variable"]

bot_token = config.get("Bot", "token")
bot_prefix = config.get("Bot", "prefix")

activity = discord.Activity(
    name="How to make good spaghetti",
    type=discord.ActivityType.competing,
)
client = _client.MyClient(activity=activity, intents=discord.Intents.default())


client.run(bot_token)
