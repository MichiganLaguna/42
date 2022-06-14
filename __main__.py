"""Discord bot for the server 42."""
import os
import logging
from configparser import ConfigParser, ExtendedInterpolation
from typing import Union
import datetime
import pytz
import tzlocal
import discord
import aiohttp



class UTCFormatter(logging.Formatter):
    """override the default formatter to use UTC timezone."""
    def converter(self, timestamp):
        local_time = datetime.datetime.fromtimestamp(timestamp)
        tzinfo = tzlocal.get_localzone()
        return local_time.replace(tzinfo=tzinfo).astimezone(pytz.utc)

    def formatTime(self, record, datefmt=None):
        utc_time = self.converter(record.created)
        if datefmt:
            formatted_time = utc_time.strftime(datefmt)
        else:
            try:
                formatted_time = utc_time.isoformat(timespec='milliseconds')
            except TypeError:
                formatted_time = utc_time.isoformat()
        return formatted_time

CURR_FOLDER = os.path.dirname(os.path.abspath(__file__))

_CONFIG = ConfigParser(interpolation=ExtendedInterpolation())
_CONFIG_FILE = os.path.join(CURR_FOLDER, 'config.cfg')
_CONFIG.read(_CONFIG_FILE, encoding='utf-8')

_VARIABLE = ConfigParser(interpolation=ExtendedInterpolation())
_VARIABLE_FILE = os.path.join(CURR_FOLDER, _CONFIG.get("Language", "default_language"))
_VARIABLE.read(_VARIABLE_FILE, encoding='utf-8')



os.makedirs(_CONFIG.get("Logging", "log_dir"), exist_ok=True)
_logger = logging.getLogger(_CONFIG.get("Logging", "logger"))
_log_name = datetime.datetime.now(tz=pytz.timezone('UTC')).strftime("%Y-%m-%dT%H-%M-%S%z")
_handler = logging.FileHandler(
    filename=f"logs/{_log_name}.log",
    encoding="utf-8",
    mode="w",
)
_handler.setFormatter(
    UTCFormatter(_CONFIG.get("Logging", "handler_format"))
)
_logger.addHandler(_handler)
_logger.setLevel(_CONFIG.getint("Logging", "logger_level"))



_TOKEN = _CONFIG.get("Bot", "token")
_PREFIX = _CONFIG.get("Bot", "prefix")

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self) -> None:
        """Prints when the bot is ready."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def _create_invite(self, guild: Union[discord.Guild, discord.ChannelType], *args, **kwargs) -> discord.Invite:
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

    def _set_to_config(self, config_file: ConfigParser, file: str, new_args: list[tuple[str, str, str]], part: bool=True) -> None:
        """Sets the given args to the config and write them."""
        if not part:
            _list_sections= {f"{arg[0]}":0 for arg in new_args if config_file.has_section(arg[0])}
            for section in _list_sections:
                config_file.remove_section(section)
                config_file.add_section(section)
        for arg in new_args:
            config_file.set(f'{arg[0]}', f'{arg[1]}', f'{arg[2]}')
        with open(file, "w", encoding="utf-8") as _file:
            config_file.write(_file)

    def _update_roles(self, roles: list[discord.Role]):
        """Updates the roles in the config.

        Args:
            roles (list[discord.Role]): list of roles to update
        """
        new_conf = [("Roles", role.name, role.id) for role in roles]
        self._set_to_config(_CONFIG, _CONFIG_FILE, new_conf, False)


    async def on_message(self, message):
        """Prints when a message is sent."""
        if message.author == self.user:
            return

        if message.content.startswith(f"{_PREFIX}{_VARIABLE.get('OnMessageQ', 'pasta')}") or message.content.startswith(f"{_PREFIX}{_VARIABLE.get('OnMessageQ', 'pasta_1')}"):

            img = f"{_CONFIG.get('Ressources', 'pasta_image_name')}"
            file = discord.File(_CONFIG.get("Ressources", "pasta_image"), filename=img)
            embed = discord.Embed(color=int(_CONFIG.get("Ressources", "color_0"), 0))
            embed.set_image(url=f"attachment://{img}")
            await message.author.send(embed=embed, file=file)

        elif message.content.startswith(f"{_PREFIX}cat"):

            async with aiohttp.ClientSession() as session:
                async with session.get("https://aws.random.cat/meow") as resp:
                    if resp.status != 200:
                        answer = f"{resp.status}: {resp.reason}"
                        return await message.channel.send(f"{answer}")
                    data = await resp.json()
                    await message.channel.send(data["file"])

        elif message.content.startswith(f"{_PREFIX}{_VARIABLE.get('OnMessageQ', 'bot_about')}"):

            embed = discord.Embed(color=int(_CONFIG.get("Ressources", "color_0"), 0))
            embed.url = _CONFIG.get("Ressources", "bot_invite")
            embed.title = _VARIABLE.get("OnMessageA", "bot_about_title")
            embed.description = _VARIABLE.get("OnMessageA", "bot_about_description")
            embed.set_author(name=_CONFIG.get("Ressources", "owner_name"), url=_CONFIG.get("Ressources", "bot_github"), icon_url=_CONFIG.get("Ressources", "owner_icon"))
            await message.channel.send(embed=embed)

        elif message.content.startswith(f"{_PREFIX}{_VARIABLE.get('OnMessageQ', 'create_menu')}"):

            embed = discord.Embed(color=int(_CONFIG.get("Ressources", "color_0"), 0))
            embed.title = _VARIABLE.get("OnMessageA", "create_menu_title")
            embed.description = _VARIABLE.get("OnMessageA", "create_menu_description")
            await message.channel.send(embed=embed)

        elif message.content.startswith(f"{_PREFIX}{_VARIABLE.get('OnMessageQ', 'update_roles')}"):
            roles = message.guild.roles
            embed = discord.Embed(color=int(_CONFIG.get("Ressources", "color_0"), 0))
            embed.title = _VARIABLE.get("OnMessageA", "update_roles_title")
            embed.description = "\n".join(f"_{role.name}_" for role in roles)
            await message.channel.send(embed=embed)
            self._update_roles(roles)



activity = discord.Activity(
    name="How to make good spaghetti",
    type=discord.ActivityType.competing,
)
client = MyClient(activity=activity, intents=discord.Intents.default())


client.run(_TOKEN)
