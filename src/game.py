from typing import Optional, Self
from dataclasses import dataclass, field
import warnings
import random

from src.board import BOARD, COLOR_SETS, Tile, TileType, find_street


MAX_HOUSE = 4


def roll_dice() -> tuple[int, int]:
    return random.randint(1, 6), random.randint(1, 6)


@dataclass(slots=True)
class Player:
    user_id: int
    username: Optional[str]
    is_ready: bool
    money: int
    position: int
    # Tile position to house count on the tile
    # Hotel counts as 5th house
    # Tiles that don't have houses won't look at the value
    ownership: dict[int, int] = field(default_factory=dict)

    @staticmethod
    def initialize(user_id: int, username: Optional[str]) -> Self:
        player: Self = Player(user_id, username, False, 1500, 0)
        return player

    def roll(self) -> None:
        roll_0, roll_1 = random.randint(1, 6)
        next_position = roll_0 + roll_1 + self.position
        if next_position < 40:
            self.position = next_position
        else:
            self.money += 200
            self.position = next_position - 40

        if self.position in self.ownership.keys():
            # Do nothing on owned tile
            return None

        tile: Tile = BOARD[self.position]
        if tile.type_ == TileType.STREET:
            # TODO
            owner: Optional[Player] = None

    def can_trade(self, index: int) -> bool:
        return index in self.ownership.keys() and not (
            BOARD[index].type_ == TileType.STREET
            and any(
                self.ownership.get(set_index, 0) > 0 for set_index in COLOR_SETS[index]
            )
        )


def find_player(players: list[Player], id: int) -> Player:
    found: Optional[Player] = next(
        (player for player in players if id == player.user_id),
        None,
    )
    if found is None:
        # Falling back to players list
        # If it indexError's, then it's truly over
        # Surely none of this will happen Clueless
        warnings.warn("No player found with this id")
        return players[0]
    return found


@dataclass(slots=True)
class Game:
    in_progress: bool
    # Current player to make a move
    current: int
    players: list[Player]

    def add_player(self, user_id: int, username: str) -> bool:
        if self.in_progress:
            return False
        new = Player.initialize(user_id, username)
        self.players.append(new)
        return True

    def begin(self) -> Optional[str]:
        """Returns None on success, otherwise an error mesage"""
        if self.in_progress:
            return "A game is already in progress"
        elif any(not ready for _player, ready in self.players):
            return "Not all players are ready"
        elif len(self.players) < 2:
            return "Not enough players to start a game"
        self.in_progress = True
        return None

    def roll(self):
        player = self.players[self.current]
        next_player = 0 if self.current + 1 >= len(self.players) else self.current + 1

        player.roll()  # TODO

        self.current = next_player

    def trade(
        self,
        id_0: int,
        id_1: int,
        money: int,
        property0: Optional[str],
        property1: Optional[str],
    ) -> Optional[str]:
        """
        Money can be negative, meaning from player 1 to player 0
        Properties0 is a list of properties to transfer from player0
        Properties1 is a list of properties to transfer from player1
        # TODO make properties lists
        Returns None on succeess, else error message
        """
        player0 = find_player(self.players, id_0)
        player1 = find_player(self.players, id_1)

        prop0: Optional[int] = None
        if property0 is not None:
            prop0: Optional[int] = find_street(property0)
            if prop0 is None:
                return f"Player {player0.username} has no property {property0}"
            elif not player1.can_trade(prop0):
                return f"Player {player0.username} has houses on property {property0}"
        prop1: Optional[int] = None
        if property1 is not None:
            prop1: Optional[int] = find_street(property1)
            if prop1 is None:
                return f"Player {player1.username} has no property {property1}"
            elif not player1.can_trade(prop1):
                return f"Player {player1.username} has houses on property {property1}"

        player0.money += money
        player1.money -= money
        return None

    def serialize(self) -> str:
        # TODO
        pass

    @staticmethod
    def deserialize(data: str) -> Self:
        # TODO
        pass
