from pydantic import BaseModel


class CardData(BaseModel):
    """This class holds the data used for building a card list from the local Arena files"""
    database_size: int = 0