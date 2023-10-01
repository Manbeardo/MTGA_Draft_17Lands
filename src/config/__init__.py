"""This module encompasses functions for reading from, writing to, and resetting the configuration file"""
import json
import os
from typing import Tuple
from src.config.Configuration import Configuration
from src.logger import create_logger

CONFIG_FILE = os.path.join(os.getcwd(), "config.json")

logger = create_logger()


def read_configuration(file_location: str = CONFIG_FILE) -> Tuple[Configuration, bool]:
    '''function is responsible for reading the contents of file and storing it as a Configuration object'''
    config_object = Configuration()
    success = False

    try:
        with open(file_location, 'r', encoding="utf8", errors="replace") as data:
            config_data = json.loads(data.read())

        config_object = Configuration.parse_obj(config_data)
        success = True
    except (FileNotFoundError, json.JSONDecodeError) as error:
        logger.error(error)

    return config_object, success


def write_configuration(config_object: Configuration, file_location: str = CONFIG_FILE) -> bool:
    '''function is responsible for writing the contents of a Configuration object to a specified file location'''
    success = False

    try:
        with open(file_location, 'w', encoding="utf8", errors="replace") as data:
            json.dump(config_object.dict(), data, ensure_ascii=False, indent=4)
        success = True
    except (FileNotFoundError, TypeError, OSError) as error:
        logger.error(error)

    return success


def reset_configuration(file_location: str = CONFIG_FILE) -> bool:
    '''function is responsible for reseting the contents of a Configuration object to a specified file location'''
    config_object = Configuration()
    success = False
    try:
        with open(file_location, 'w', encoding="utf8", errors="replace") as data:
            json.dump(config_object.dict(), data, ensure_ascii=False, indent=4)
        success = True
    except (FileNotFoundError, TypeError, OSError) as error:
        logger.error(error)

    return success


if not os.path.exists(CONFIG_FILE):
    reset_configuration(CONFIG_FILE)
