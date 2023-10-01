from dataclasses import dataclass


@dataclass
class TableInfo:
    reverse: bool = True
    column: str = ""