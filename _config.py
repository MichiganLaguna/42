"""custom config

    Returns:
        dict[str: Configparser]: dict["config"]=config.cfg,
                                dict["variable"]=english.cfg|french.cfg depending on settings in config.cfg
    """
import os
from configparser import ConfigParser, ExtendedInterpolation


def custom_config()->dict[str, ConfigParser]:
    config_name = "config.cfg"
    encoding = "utf-8"
    interpolation = ExtendedInterpolation()
    current_folder = os.path.dirname(os.path.abspath(__file__))
    config = ConfigParser(interpolation=interpolation)
    config_file = os.path.join(current_folder, config_name)
    config.read(config_file, encoding=encoding)
    return config
