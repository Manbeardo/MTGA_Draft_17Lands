from src.limited_sets.SetInfo import SetInfo


from pydantic import BaseModel, Field


from typing import Dict


class SetDictionary(BaseModel):
    data: Dict[str, SetInfo] = Field(default_factory=dict)