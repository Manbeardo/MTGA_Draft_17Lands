from enum import Enum


class Result(Enum):
    '''Enumeration class for file integrity results'''
    VALID = 0
    ERROR_MISSING_FILE = 1
    ERROR_UNREADABLE_FILE = 2