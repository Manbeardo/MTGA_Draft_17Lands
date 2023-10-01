from dataclasses import dataclass, field


@dataclass
class DeckMetrics:
    cmc_average: float = 0.0
    creature_count: int = 0
    noncreature_count: int = 0
    total_cards: int = 0
    total_non_land_cards: int = 0
    distribution_creatures: list = field(
        default_factory=lambda: [0, 0, 0, 0, 0, 0, 0])
    distribution_noncreatures: list = field(
        default_factory=lambda: [0, 0, 0, 0, 0, 0, 0])
    distribution_all: list = field(
        default_factory=lambda: [0, 0, 0, 0, 0, 0, 0])