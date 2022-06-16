"""custom logger module."""
import logging
from datetime import datetime
import os
import pytz
import tzlocal

class UTCFormatter(logging.Formatter):
    """override the default formatter to use UTC timezone."""
    def converter(self, timestamp):
        local_time = datetime.fromtimestamp(timestamp)
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

def custom_logger(log_name: str,
                    log_dir_name: str = "logs",
                    log_file_extension: str = ".log",
                    log_file_encoding: str  = "utf-8",
                    log_file_open_mode: str = "a",
                    logger: str="discord",
                    logging_format:str = "%(asctime)s:%(levelname)s:%(name)s: %(message)s",
                    logging_level: int = 10) -> logging.Logger:
    """Return a custom logger.

    Args:
        log_name (str): Name of the log file.
        log_dir_name (str, optional): Directory in wich the log file will be created. Defaults to "logs".
        log_file_extension (str, optional): Extension of log file. Defaults to ".log".
        log_file_encoding (str, optional): Defaults to "utf-8".
        log_file_open_mode (str, optional): a or w. Defaults to "a".
        logger (str, optional): logger to fetch. Defaults to "discord".
        logging_format (_type_, optional): Defaults to "%(asctime)s:%(levelname)s:%(name)s: %(message)s".
        logging_level (int, optional): Defaults to 10 wich is DEBUG.

    Returns:
        logging.Logger: custom logger
    """
    log_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_dir_name)
    log_file_path = os.path.join(log_dir_path, log_name + log_file_extension)
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path)
    _logger = logging.getLogger(logger)
    handler = logging.FileHandler(filename=log_file_path,
                                    encoding=log_file_encoding,
                                    mode=log_file_open_mode)
    formatter = UTCFormatter(logging_format)
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _logger.setLevel(logging_level)
    return _logger