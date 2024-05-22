from typing import Optional, Self
from dataclasses import dataclass
import random

from board import BOARD, Tile, TileType


MAX_HOUSE = 4


def roll_dice() -> tuple[int, int]:
    return random.randint(1, 6), random.randint(1, 6)


@dataclass(slots=True)
class Player:
    user_id: int
    username: Optional[str]
    money: int
    position: int

    @staticmethod
    def initialize(user_id: int, username: Optional[str]) -> Self:
        player: Self = Player(user_id, username, 1500, 0)
        return player

    def roll(self) -> None:
        roll_0, roll_1 = random.randint(1, 6)
        next_position = roll_0 + roll_1 + self.position
        if next_position < 40:
            self.position = next_position
        else:
            self.position = next_position - 40

        tile: Tile = BOARD[self.position]
        if tile.type_ == TileType.STREET:
            # TODO
            pass
