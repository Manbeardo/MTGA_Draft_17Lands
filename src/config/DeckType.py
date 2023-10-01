from pydantic import BaseModel, Field


class DeckType(BaseModel):
    """This class holds the data for the various deck types (Aggro, Mid, and Control)"""
    distribution: list = Field(
        default_factory=lambda: [0, 0, 0, 0, 0, 0, 0])
    maximum_card_count: int = 0
    recommended_creature_count: int = 0
    cmc_average: float = 0.0