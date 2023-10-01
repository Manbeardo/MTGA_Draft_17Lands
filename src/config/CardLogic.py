from src.config.DeckType import DeckType


from pydantic import BaseModel


class CardLogic(BaseModel):
    """This class represents the configuration for card logic within the application"""
    minimum_creatures: int = 9
    minimum_noncreatures: int = 6
    ratings_threshold: int = 500
    alsa_weight: float = 0.0
    iwd_weight: float = 0.0
    deck_mid: DeckType = DeckType(distribution=[
                                  0, 0, 4, 3, 2, 1, 0], maximum_card_count=23, recommended_creature_count=15, cmc_average=3.04)
    deck_aggro: DeckType = DeckType(distribution=[
                                    0, 2, 5, 3, 0, 0, 0], maximum_card_count=24, recommended_creature_count=17, cmc_average=2.40)
    deck_control: DeckType = DeckType(distribution=[
                                      0, 0, 3, 2, 2, 1, 0], maximum_card_count=22, recommended_creature_count=10, cmc_average=3.68)