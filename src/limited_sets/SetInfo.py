from pydantic import BaseModel, Field


from typing import List


class SetInfo(BaseModel):
    arena: List[str] = Field(default_factory=list)
    scryfall: List[str] = Field(default_factory=list)
    seventeenlands: List[str] = Field(default_factory=list)
    start_date: str = ""