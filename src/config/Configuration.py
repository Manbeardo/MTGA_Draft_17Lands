from src.config.CardData import CardData
from src.config.CardLogic import CardLogic
from src.config.Features import Features
from src.config.Settings import Settings


from pydantic import BaseModel, Field


class Configuration(BaseModel):
    """This class groups together the data stored in the config.json file"""
    settings: Settings = Field(default_factory=lambda: Settings())
    card_logic: CardLogic = Field(default_factory=lambda: CardLogic())
    features: Features = Field(default_factory=lambda: Features())
    card_data: CardData = Field(default_factory=lambda: CardData())