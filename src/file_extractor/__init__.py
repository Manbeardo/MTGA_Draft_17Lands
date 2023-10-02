"""This module contains the functions and classes that are used for building the set files and communicating with platforms"""
import sys
import os
import json
import datetime
import itertools
import re
from src import constants
from src.file_extractor.Result import Result
from src.logger import create_logger

logger = create_logger()

if not os.path.exists(constants.SETS_FOLDER):
    os.makedirs(constants.SETS_FOLDER)

if not os.path.exists(constants.TIER_FOLDER):
    os.makedirs(constants.TIER_FOLDER)

if not os.path.exists(constants.TEMP_FOLDER):
    os.makedirs(constants.TEMP_FOLDER)

def initialize_card_data(card_data):
    card_data[constants.DATA_FIELD_DECK_COLORS] = {}
    for color in constants.DECK_COLORS:
        card_data[constants.DATA_FIELD_DECK_COLORS][color] = {
            x: 0.0 for x in constants.DATA_FIELD_17LANDS_DICT if x != constants.DATA_SECTION_IMAGES}


def check_set_data(set_data, ratings_data):
    '''Run through 17Lands card list and determine if there are any cards missing from the assembled set file'''
    for rated_card in ratings_data:
        try:
            card_found = False
            for card_id in set_data:
                card_name = set_data[card_id][constants.DATA_FIELD_NAME].replace(
                    "///", "//")
                if rated_card == card_name:
                    card_found = True
                    break
            if not card_found:
                logger.error("Card %s Missing", rated_card)

        except Exception as error:
            logger.error(error)


def decode_mana_cost(encoded_cost):
    '''Parse the raw card mana_cost field and return the cards cmc and color identity list'''
    decoded_cost = ""
    cmc = 0
    if encoded_cost:
        cost_string = re.sub(r"\(|\)", "", encoded_cost)

        sections = cost_string[1:].split("o")
        for section in sections:
            cmc += int(section) if section.isnumeric() else 1

        decoded_cost = "".join(f"{{{x}}}" for x in sections)

    return decoded_cost, cmc


def retrieve_local_set_list(sets):
    '''Scans the Sets folder and returns a list of valid set files'''
    file_list = []
    main_sets = [v.seventeenlands[0] for k, v in sets.items()]
    for file in os.listdir(constants.SETS_FOLDER):
        try:
            name_segments = file.split("_")
            if len(name_segments) == 3:

                if ((name_segments[0].upper() in main_sets) and
                    (name_segments[1] in constants.LIMITED_TYPES_DICT) and
                        (name_segments[2] == constants.SET_FILE_SUFFIX)):

                    set_name = list(sets.keys())[list(
                        main_sets).index(name_segments[0].upper())]
                    result, json_data = check_file_integrity(
                        os.path.join(constants.SETS_FOLDER, file))
                    if result == Result.VALID:
                        if json_data["meta"]["version"] == 1:
                            start_date, end_date = json_data["meta"]["date_range"].split(
                                "->")
                        else:
                            start_date = json_data["meta"]["start_date"]
                            end_date = json_data["meta"]["end_date"]
                        file_list.append(
                            (set_name, name_segments[1], start_date, end_date))
        except Exception as error:
            logger.error(error)

    return file_list


def search_arena_log_locations(input_location=None):
    '''Searches local directories for the location of the Arena Player.log file'''
    log_location = ""
    try:
        paths = []

        if input_location:
            paths.extend(input_location)

        if sys.platform == constants.PLATFORM_ID_OSX:
            paths.extend([os.path.join(os.path.expanduser(
                '~'), constants.LOG_LOCATION_OSX)])
        else:
            path_list = [constants.WINDOWS_DRIVES,
                         [constants.LOG_LOCATION_WINDOWS]]
            paths.extend([os.path.join(*x)
                         for x in itertools.product(*path_list)])

        for file_path in paths:
            if file_path:
                logger.info("Arena Log: Searching File Path %s", file_path)
                if os.path.exists(file_path):
                    log_location = file_path
                    break

    except Exception as error:
        logger.error(error)
    return log_location


def retrieve_arena_directory(log_location):
    '''Searches the Player.log file for the Arena install location (windows only)'''
    arena_directory = ""
    try:
        # Retrieve the arena directory
        with open(log_location, 'r', encoding="utf-8", errors="replace") as log_file:
            line = log_file.readline()
            location = re.findall(r"'(.*?)/Managed'", line, re.DOTALL)
            if location and os.path.exists(location[0]):
                arena_directory = location[0]

    except Exception as error:
        logger.error(error)
    return arena_directory


def search_local_files(paths, file_prefixes):
    '''Generic function that's used for searching local directories for a file'''
    file_locations = []
    for file_path in paths:
        try:
            if os.path.exists(file_path):
                for prefix in file_prefixes:
                    files = [filename for filename in os.listdir(
                        file_path) if filename.startswith(prefix)]

                    for file in files:
                        file_location = os.path.join(file_path, file)
                        file_locations.append(file_location)

        except Exception as error:
            logger.error(error)

    return file_locations


def extract_types(type_line):
    '''Parses a type string and returns a list of card types'''
    types = []
    if constants.CARD_TYPE_CREATURE in type_line:
        types.append(constants.CARD_TYPE_CREATURE)

    if constants.CARD_TYPE_PLANESWALKER in type_line:
        types.append(constants.CARD_TYPE_PLANESWALKER)

    if constants.CARD_TYPE_LAND in type_line:
        types.append(constants.CARD_TYPE_LAND)

    if constants.CARD_TYPE_INSTANT in type_line:
        types.append(constants.CARD_TYPE_INSTANT)

    if constants.CARD_TYPE_SORCERY in type_line:
        types.append(constants.CARD_TYPE_SORCERY)

    if constants.CARD_TYPE_ENCHANTMENT in type_line:
        types.append(constants.CARD_TYPE_ENCHANTMENT)

    if constants.CARD_TYPE_ARTIFACT in type_line:
        types.append(constants.CARD_TYPE_ARTIFACT)

    return types


def check_date(date):
    '''Checks a date string and returns false if the date is in the future'''
    result = True
    try:
        parts = date.split("-")
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        hour = 0

        if datetime.datetime(year=year, month=month, day=day, hour=hour) > datetime.datetime.now():
            result = False

    except Exception:
        result = False
    return result


def check_file_integrity(filename):
    '''Extracts data from a file to determine if it's formatted correctly'''
    result = Result.VALID
    json_data = {}

    try:
        with open(filename, 'r', encoding="utf-8", errors="replace") as json_file:
            json_data = json_file.read()
    except FileNotFoundError:
        return Result.ERROR_MISSING_FILE, json_data

    try:
        json_data = json.loads(json_data)

        if json_data.get("meta"):
            meta = json_data["meta"]
            version = meta.get("version")
            if version == 1:
                meta.get("date_range", "").split("->")
            else:
                meta.get("start_date")
                meta.get("end_date")
        else:
            return Result.ERROR_UNREADABLE_FILE, json_data

        cards = json_data.get("card_ratings")
        if isinstance(cards, dict) and len(cards) >= 100:
            for card in cards.values():
                card.get(constants.DATA_FIELD_NAME)
                card.get(constants.DATA_FIELD_COLORS)
                card.get(constants.DATA_FIELD_CMC)
                card.get(constants.DATA_FIELD_TYPES)
                card.get("mana_cost")
                card.get(constants.DATA_SECTION_IMAGES)
                deck_colors = card.get(constants.DATA_FIELD_DECK_COLORS, {}).get(
                    constants.FILTER_OPTION_ALL_DECKS, {})
                deck_colors.get(constants.DATA_FIELD_GIHWR)
                deck_colors.get(constants.DATA_FIELD_ALSA)
                deck_colors.get(constants.DATA_FIELD_IWD)
                break
        else:
            return Result.ERROR_UNREADABLE_FILE, json_data

    except json.JSONDecodeError:
        return Result.ERROR_UNREADABLE_FILE, json_data

    return result, json_data


