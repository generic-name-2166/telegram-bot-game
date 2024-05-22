from enum import Enum, verify, UNIQUE, auto
from dataclasses import dataclass
from typing import Optional


@verify(UNIQUE)
class Color(Enum):
    Brown = auto()
    LightBlue = auto()
    Pink = auto()
    Orange = auto()
    Red = auto()
    Yellow = auto()
    Green = auto()
    DarkBlue = auto()


@dataclass(slots=True)
class Street:
    name: str
    color: Color


@verify(UNIQUE)
class TileType(Enum):
    STREET = auto()
    RAILROAD = auto()
    UTILITY = auto()
    CHANCE = auto()
    CHEST = auto()
    TAX_INCOME = auto()
    TAX_LUXURY = auto()
    GO = auto()
    FREE = auto()
    JAIL_VISIT = auto()
    GO_TO_JAIL = auto()


@dataclass(slots=True)
class Tile:
    type_: TileType
    rent_prices: tuple[int, int, int, int, int, int]
    street: Optional[Street] = None

    def calculate_rent(self) -> int:
        pass
        # TODO


BOARD: list[Tile] = [
    Tile(
        type_=TileType.STREET,
        rent_prices=(2, 10, 30, 90, 160, 250),
        street=Street("Old Kent Road", Color.Brown),
    )
]
