from enum import Enum, verify, UNIQUE, auto
from dataclasses import dataclass
from typing import Optional

from src.game import Player, roll_dice


RAILROAD_TILES: frozenset = frozenset({5, 15, 25, 35})
COLOR_SETS: dict[int, frozenset[int]] = {
    1: frozenset((3,)),
    3: frozenset((1,)),
    6: frozenset({8, 9}),
    8: frozenset({6, 9}),
    9: frozenset({6, 8}),
    11: frozenset({13, 14}),
    13: frozenset({11, 14}),
    14: frozenset({11, 13}),
    16: frozenset({18, 19}),
    18: frozenset({16, 19}),
    19: frozenset({16, 18}),
    21: frozenset({23, 24}),
    23: frozenset({21, 24}),
    24: frozenset({21, 23}),
    26: frozenset({27, 29}),
    27: frozenset({26, 29}),
    29: frozenset({26, 27}),
    31: frozenset({32, 34}),
    32: frozenset({31, 34}),
    34: frozenset({31, 31}),
    37: frozenset((39,)),
    39: frozenset((37,)),
}
UTILITIES: dict[int, int] = {
    12: 33,
    33: 12,
}


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
    color: Color
    cost: int
    rent_prices: tuple[int, int, int, int, int, int]

    def calculate_rent(self, owner: Player) -> int:
        position: int = owner.position
        ownership: int = owner.ownership[position]
        if ownership > 1:
            return self.rent_prices[ownership]
        elif all(
            (set_street in owner.ownership) for set_street in COLOR_SETS[position]
        ):
            return self.rent_prices[0] * 2
        # if player full color and no houses, he can double the base rent
        # but we're forcing him for simplicity
        return self.rent_prices[0]


@dataclass(slots=True)
class Railroad:
    cost: int

    def calculate_rent(self, owner: Player) -> int:
        # Power should always be at least 0 because current railroad has an owner
        power = -1
        owned_tiles = owner.ownership.keys()
        for railroad_tile in RAILROAD_TILES:
            if railroad_tile in owned_tiles:
                power += 1
        return 25 * (2**power)


@dataclass(slots=True)
class Utility:
    cost: int

    def calculate_rent(self, owner: Player) -> int:
        has_other: bool = UTILITIES[owner.position] in owner.ownership.keys()
        rolled: int = sum(roll_dice())
        return rolled * (10 if has_other else 4)


class Chance:
    pass


class Chest:
    pass


class TaxIncome:
    pass


class TaxLuxury:
    pass


class Go:
    pass


class Free:
    pass


class JailVisit:
    pass


class GoToJail:
    pass


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
    name: str
    inner: Optional[Street | Railroad | Utility] = None

    def calculate_rent(self, current: Player, players: set[Player]) -> int:
        if (
            isinstance(self.inner, Street)
            or isinstance(self.inner, Railroad)
            or isinstance(self.inner, Utility)
        ):
            position: int = current.position
            owner: Optional[int] = next(
                (player for player in players if position in player.ownership.keys()),
                None,
            )
            if owner is not None and current.user_id != owner.user_id:
                return self.inner.calculate_rent(owner)
        return 0


BOARD: list[Tile] = [
    Tile(type_=TileType.GO, name="GO"),
    Tile(
        type_=TileType.STREET,
        name="Old Kent Road",
        inner=Street(
            color=Color.Brown,
            cost=60,
            rent_prices=(2, 10, 30, 90, 160, 250),
        ),
    ),
    Tile(
        type_=TileType.STREET,
        name="Whitechapel Road",
        inner=Street(
            color=Color.Brown,
            cost=60,
            rent_prices=(4, 20, 60, 180, 320, 450),
        ),
    ),
    Tile(type_=TileType.TAX_INCOME, name="Income Tax"),
    Tile(
        type_=TileType.RAILROAD,
        name="Kings Cross Station",
        inner=Railroad(200),
    ),
    Tile(
        type_=TileType.STREET,
        name="The Angel, Islington",
        inner=Street(
            color=Color.LightBlue,
            cost=100,
            rent_prices=(6, 30, 90, 270, 400, 550),
        ),
    ),
    Tile(type_=TileType.CHANCE, name="Chance"),
    Tile(
        type_=TileType.STREET,
        name="Euston Road",
        inner=Street(
            color=Color.LightBlue,
            cost=100,
            rent_prices=(6, 30, 90, 270, 400, 550),
        ),
    ),
    Tile(
        type_=TileType.STREET,
        name="Pentonville Road",
        inner=Street(
            color=Color.LightBlue,
            cost=120,
            rent_prices=(8, 40, 100, 300, 450, 600),
        ),
    ),
    Tile(type_=TileType.JAIL_VISIT, name="Jail visiting"),
    Tile(
        type_=TileType.STREET,
        name="Pall Mall",
        inner=Street(
            color=Color.Pink,
            cost=140,
            rent_prices=(10, 50, 150, 450, 625, 750),
        ),
    ),
    Tile(
        type_=TileType.UTILITY,
        name="Electric Company",
        inner=Utility(cost=150),
    ),
    Tile(
        type_=TileType.STREET,
        name="Whitehall",
        inner=Street(
            color=Color.Pink,
            cost=140,
            rent_prices=(10, 50, 150, 450, 625, 750),
        ),
    ),
    Tile(
        type_=TileType.STREET,
        name="Northumberland Avenue",
        inner=Street(
            color=Color.Pink,
            cost=160,
            rent_prices=(12, 60, 180, 500, 700, 900),
        ),
    ),
    Tile(
        type_=TileType.RAILROAD,
        name="Marylebone Station",
        inner=Railroad(200),
    ),
    Tile(
        type_=TileType.STREET,
        name="Bow Street",
        inner=Street(
            color=Color.Orange,
            cost=180,
            rent_prices=(14, 70, 200, 550, 750, 950),
        ),
    ),
    Tile(type_=TileType.CHEST, name="Community Chest"),
    Tile(
        type_=TileType.STREET,
        name="Marlborough Street",
        inner=Street(
            color=Color.Orange,
            cost=180,
            rent_prices=(14, 70, 200, 550, 750, 950),
        ),
    ),
    Tile(
        type_=TileType.STREET,
        name="Vine Street",
        inner=Street(
            color=Color.Orange,
            cost=200,
            rent_prices=(16, 80, 220, 600, 800, 1000),
        ),
    ),
    Tile(type_=TileType.FREE, name="Free Parking"),
    Tile(
        type_=TileType.STREET,
        name="Strand",
        inner=Street(
            color=Color.Red,
            cost=220,
            rent_prices=(18, 90, 250, 700, 875, 1050),
        ),
    ),
    Tile(type_=TileType.CHANCE, name="Chance"),
    Tile(
        type_=TileType.STREET,
        name="Fleet Street",
        inner=Street(
            color=Color.Red,
            cost=220,
            rent_prices=(18, 90, 250, 700, 875, 1050),
        ),
    ),
    Tile(
        type_=TileType.STREET,
        name="Trafalgar Square",
        inner=Street(
            color=Color.Red,
            cost=220,
            rent_prices=(20, 100, 300, 750, 925, 1100),
        ),
    ),
    Tile(
        type_=TileType.RAILROAD,
        name="Fenchurch St Station",
        inner=Railroad(200),
    ),
    Tile(
        type_=TileType.STREET,
        name="Leicester Square",
        inner=Street(
            color=Color.Yellow,
            cost=260,
            rent_prices=(22, 110, 330, 800, 975, 1150),
        ),
    ),
    Tile(
        type_=TileType.STREET,
        name="Coventry Street",
        inner=Street(
            color=Color.Yellow,
            cost=260,
            rent_prices=(22, 110, 330, 800, 975, 1150),
        ),
    ),
    Tile(
        type_=TileType.UTILITY,
        name="Water Works",
        inner=Utility(cost=150),
    ),
    Tile(
        type_=TileType.STREET,
        name="Piccadilly",
        inner=Street(
            color=Color.Yellow,
            cost=280,
            rent_prices=(24, 120, 360, 850, 1025, 1200),
        ),
    ),
    Tile(type_=TileType.GO_TO_JAIL, name="Go To Jail"),
    Tile(
        type_=TileType.STREET,
        name="Regent Street",
        inner=Street(
            color=Color.Green,
            cost=300,
            rent_prices=(26, 130, 390, 900, 1100, 1275),
        ),
    ),
    Tile(
        type_=TileType.STREET,
        name="Oxford Street",
        inner=Street(
            color=Color.Green,
            cost=300,
            rent_prices=(26, 130, 390, 900, 1100, 1275),
        ),
    ),
    Tile(type_=TileType.CHEST, name="Community Chest"),
    Tile(
        type_=TileType.STREET,
        name="Bond Street",
        inner=Street(
            color=Color.Green,
            cost=300,
            rent_prices=(28, 150, 450, 1000, 1200, 1400),
        ),
    ),
    Tile(
        type_=TileType.RAILROAD,
        name="Liverpool Street Station",
        inner=Railroad(200),
    ),
    Tile(type_=TileType.CHANCE, name="Chance"),
    Tile(
        type_=TileType.STREET,
        name="Park Lane",
        inner=Street(
            color=Color.DarkBlue,
            cost=350,
            rent_prices=(35, 175, 500, 1100, 1300, 1500),
        ),
    ),
    Tile(type_=TileType.TAX_LUXURY, name="Super Tax"),
    Tile(
        type_=TileType.STREET,
        name="Mayfair",
        inner=Street(
            color=Color.DarkBlue,
            cost=400,
            rent_prices=(50, 100, 600, 1400, 1700, 2000),
        ),
    ),
]

assert len(BOARD) == 40


def find_street(name: str) -> Optional[int]:
    for street_index in COLOR_SETS.keys():
        if BOARD[street_index].name == name:
            return street_index
    for utility_index in UTILITIES.keys():
        if BOARD[utility_index].name == name:
            return utility_index
    for railroad_index in RAILROAD_TILES:
        if BOARD[railroad_index].name == name:
            return railroad_index
    return None
