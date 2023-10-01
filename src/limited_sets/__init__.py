import datetime
import os
from src.limited_sets.SetInfo import SetInfo
from src.logger import create_logger

logger = create_logger()


CUSTOM_SETS = {
    "dbl": SetInfo(arena=["VOW", "MID"], scryfall=["VOW", "MID"], seventeenlands=["DBL"]),
    "sir": SetInfo(arena=["SIR", "SIS"], scryfall=["SIR", "SIS"], seventeenlands=["SIR"]),
    "mat": SetInfo(arena=["MUL", "MOM", "MAT"], scryfall=["MUL", "MOM", "MAT"], seventeenlands=["MAT"]),
}

TOTAL_SCRYFALL_SETS = 50
SET_ARENA_CUBE_START_OFFSET_DAYS = -25
TEMP_LIMITED_SETS = os.path.join("Temp", "temp_set_list.json")


def shift_date(start_date, shifted_days, string_format, next_dow=None):
    '''Shifts a date by a certain number of days'''
    shifted_date_string = ""
    shifted_date = datetime.date.min
    try:
        shifted_date = start_date + datetime.timedelta(days=shifted_days)

        if next_dow and (0 <= next_dow <= 6):
            # Shift the date to the next specified day of the week (0 = Monday, 6 = Sunday)
            shifted_date += datetime.timedelta(
                (next_dow - shifted_date.weekday()) % 7)

        shifted_date_string = shifted_date.strftime(
            string_format) if string_format else ""

    except Exception as error:
        logger.error(error)

    return shifted_date, shifted_date_string


