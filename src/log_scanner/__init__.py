"""This module contains the functions that are used for parsing the Arena log"""
import os
import src.constants as constants
import src.file_extractor as FE
from src.logger import create_logger

if not os.path.exists(constants.DRAFT_LOG_FOLDER):
    os.makedirs(constants.DRAFT_LOG_FOLDER)

LOG_TYPE_DRAFT = "draftLog"

logger = create_logger()


def retrieve_card_data(set_data, card):
    card_data = {}
    if (set_data is not None) and (card in set_data["card_ratings"]):
        card_data = set_data["card_ratings"][card]
    else:
        empty_dict = {constants.DATA_FIELD_NAME: card,
                      constants.DATA_FIELD_MANA_COST: "",
                      constants.DATA_FIELD_TYPES: [],
                      constants.DATA_SECTION_IMAGES: []}
        FE.initialize_card_data(empty_dict)
        card_data = empty_dict
    return card_data
