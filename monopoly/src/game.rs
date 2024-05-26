mod board;

use rand::{
    distributions::{Distribution, Uniform},
    rngs::ThreadRng,
    thread_rng,
};
use std::collections::HashMap;

use crate::{
    game::board::{GetCost, Tile, TileType, BOARD},
    io::{PoorOut, SerGame, SerPlayer},
};

/// Status is defined by waiting for the next action
enum Status {
    Roll,
    Buy,
    // Auction meaning waiting for all to submit their bids
    Auction,
} // + NotReady in database

impl Status {
    fn serialize(&self) -> String {
        match self {
            Self::Buy => "buy".to_owned(),
            Self::Roll => "roll".to_owned(),
            Self::Auction => "auction".to_owned(),
        }
    }
}

/// Enum to mutate Player instance
pub enum Change {
    None,
    TaxedLuxury,
    TaxedIncome,
}

pub struct Player {
    user_id: usize,
    username: Option<String>,
    // tile id to number of houses built
    ownership: HashMap<usize, u8>,
    pub position: usize,
    pub money: isize,
}

impl Player {
    pub fn new(user_id: usize, username: Option<String>) -> Self {
        Self {
            user_id,
            username,
            ownership: HashMap::new(),
            money: 1500,
            position: 0,
        }
    }
    pub fn serialize(&self) -> SerPlayer {
        (
            self.user_id,
            self.username.clone(),
            self.ownership.clone(),
            self.position,
            self.money,
        )
    }
    pub fn change(&mut self, move_to: usize, looped: bool, change: Change) -> Option<String> {
        self.position = move_to;
        match (change, looped) {
            (Change::None, false) => None,
            (Change::None, true) => {
                self.money += 200;
                Some(format!("Passed GO. \n{} in the bank", self.money,))
            }
            (Change::TaxedIncome, true) => Some(format!("Passed GO. \n{} in the bank", self.money)),
            (Change::TaxedIncome, false) => {
                self.money -= 200;
                Some(format!("{} in the bank", self.money))
            }
            (Change::TaxedLuxury, _) => {
                // Surely no one will ever pass GO and land on luxury tax at the same time
                self.money -= 100;
                Some(format!("{} in the bank", self.money))
            }
        }
    }
    pub fn try_buying(&mut self, name: &str, prop: impl GetCost) -> (PoorOut, bool) {
        let cost: isize = prop.get_cost();
        let (out, success) = if self.money < cost {
            (
                format!(
                    "Not enough money. \nYou have {}. {} costs {}",
                    self.money, name, cost
                ),
                false,
            )
        } else {
            self.money -= cost;
            (
                format!("Purchased {}. \nYou have {} in the bank.", name, self.money),
                true,
            )
        };

        (PoorOut::new(out, String::new()), success)
    }
}

fn roll_dice() -> (usize, usize) {
    let mut rng: ThreadRng = thread_rng();
    let side: Uniform<usize> = Uniform::new(1, 7);
    (side.sample(&mut rng), side.sample(&mut rng))
}

fn check_owner(players: &[Player], position: &usize) -> bool {
    players
        .iter()
        .any(|player: &Player| -> bool { player.ownership.contains_key(position) })
}

fn find_owner<'game>(players: &'game [Player], position: &usize) -> Option<&'game Player> {
    players
        .iter()
        .find(|player: &&'game Player| -> bool { player.ownership.contains_key(position) })
}

pub struct Game {
    current_player: usize,
    players: Vec<Player>,
    status: Status,
}

impl Game {
    pub fn new(info: Vec<(usize, Option<String>)>) -> Self {
        let players: Vec<Player> = info
            .into_iter()
            .map(|(user_id, username)| Player::new(user_id, username))
            .collect();
        Self {
            current_player: 0,
            players,
            status: Status::Roll,
        }
    }
    pub fn serialize(&self) -> SerGame {
        // I could serialize into JSON or something in Rust but Python would have to deserialize anyway
        // Performance losses all around
        SerGame::new(
            self.current_player,
            self.status.serialize(),
            self.players
                .iter()
                .map(Player::serialize)
                .collect::<Vec<_>>(),
        )
    }
    pub fn roll(&mut self, caller_id: usize) -> PoorOut {
        if !matches!(self.status, Status::Roll) {
            // Do nothing if it's not the time to roll
            return PoorOut::empty();
        }

        let player_count: usize = self.players.len();

        let player: &Player = self
            .players
            .get(self.current_player)
            .expect("pointers have been tracked accurately");

        let next_player: usize = if self.current_player + 1 < player_count {
            self.current_player + 1
        } else {
            0
        };

        if player.user_id != caller_id {
            // Do nothing if it's not the callers turn to roll
            return PoorOut::empty();
        }

        let (roll_1, roll_2) = roll_dice();

        let move_to: usize = roll_1 + roll_2 + player.position;

        let (looped, position) = if move_to >= 40 {
            (true, move_to - 40)
        } else {
            (false, move_to)
        };

        let landed_on: Tile = BOARD[position];

        let mut output: PoorOut = PoorOut::new(
            format!(
                "{:?} has rolled {} and {}, now on {}.",
                player.username.as_deref().unwrap_or("None"),
                roll_1,
                roll_2,
                landed_on.name,
            ),
            String::new(),
        );

        if player.ownership.contains_key(&position) {
            return output;
        }

        let has_owner: bool = check_owner(&self.players, &position);

        // TODO
        let player_change: Change = match landed_on.inner {
            TileType::Street(prop) if !has_owner => {
                self.status = Status::Buy;
                output = output.merge_out(&format!(
                    "Buy for {} or start an auction. \n{} in the bank.",
                    prop.get_cost(),
                    player.money,
                ));
                Change::None
            }
            TileType::Railroad(prop) if !has_owner => {
                self.status = Status::Buy;
                output = output.merge_out(&format!(
                    "Buy for {} or start an auction. \n{} in the bank.",
                    prop.get_cost(),
                    player.money,
                ));
                Change::None
            }
            TileType::Utility(prop) if !has_owner => {
                self.status = Status::Buy;
                output = output.merge_out(&format!(
                    "Buy for {} or start an auction. \n{} in the bank.",
                    prop.get_cost(),
                    player.money,
                ));
                Change::None
            }
            TileType::Chance => {
                // TODO
                Change::None
            }
            TileType::Chest => {
                // TODO
                Change::None
            }
            TileType::GoToJail => {
                // TODO
                Change::None
            }
            // TODO bankruptcy
            TileType::TaxIncome => Change::TaxedIncome,
            TileType::TaxLuxury => Change::TaxedLuxury,
            TileType::Street(_)
            | TileType::Railroad(_)
            | TileType::Utility(_)
            | TileType::Free
            | TileType::JailVisit
            | TileType::Go => Change::None,
        };

        let change_out: Option<String> = self
            .players
            .get_mut(self.current_player)
            .expect("pointers have been tracked accurately")
            .change(move_to, looped, player_change);
        if let Some(trace) = change_out {
            output = output.merge_out(&trace);
        }
        self.current_player = next_player;

        output
    }
    pub fn buy(&mut self, caller_id: usize) -> PoorOut {
        if !matches!(self.status, Status::Buy) {
            // Do nothing if it's not the time to buy
            return PoorOut::empty();
        }

        let player: &Player = self
            .players
            .get(self.current_player)
            .expect("pointers have been tracked accurately");

        // Check if can buy
        // Not turn to buy
        // Already has an owner
        // Not enough money
        // Is non-purchasable
        if player.user_id != caller_id {
            // Do nothing if it's not the caller's turn to buy
            return PoorOut::empty();
        } else if let Some(owner) = find_owner(&self.players, &player.position) {
            return PoorOut::new(
                format!(
                    "This property is already owned by {}",
                    owner.username.as_deref().unwrap_or("None")
                ),
                String::new(),
            );
        }

        let tile: Tile = BOARD[player.position];
        let player: &mut Player = self
            .players
            .get_mut(self.current_player)
            .expect("pointers have been tracked accurately");

        let (output, success) = match tile.inner {
            TileType::Street(prop) => player.try_buying(tile.name, prop),
            TileType::Railroad(prop) => player.try_buying(tile.name, prop),
            TileType::Utility(prop) => player.try_buying(tile.name, prop),
            TileType::Chance
            | TileType::Chest
            | TileType::Free
            | TileType::Go
            | TileType::GoToJail
            | TileType::JailVisit
            | TileType::TaxIncome
            | TileType::TaxLuxury => (
                PoorOut::new("Non-purchasable tile".to_owned(), String::new()),
                false,
            ),
        };
        if success {
            self.status = Status::Roll;
        }
        output
    }
    pub fn auction(&mut self, caller_id: usize) -> PoorOut {
        if !matches!(self.status, Status::Buy) {
            // Do nothing if it's not the time to start auctions
            return PoorOut::empty();
        }

        let player: &Player = self
            .players
            .get(self.current_player)
            .expect("pointers have been tracked accurately");
        if player.user_id != caller_id {
            // Do nothing if it's not the caller's turn to start auctions
            return PoorOut::empty();
        }

        self.status = Status::Auction;

        PoorOut::new(
            "Starting an auction. \nAt least one player must bid".to_owned(),
            String::new(),
        )
    }
    pub fn bid(&mut self, _caller_id: usize, _price: isize) -> PoorOut {
        // TODO
        PoorOut::empty()
    }
    pub fn get_status(&self) -> String {
        // TODO more info
        let player: &Player = self
            .players
            .get(self.current_player)
            .expect("pointers have been tracked accurately");

        match self.status {
            Status::Roll => {
                "Waiting for ".to_owned()
                    + player.username.as_deref().unwrap_or("None")
                    + " to roll the dice"
            }
            Status::Buy => {
                "Waiting for ".to_owned()
                    + player.username.as_deref().unwrap_or("None")
                    + " to buy or auction off a property"
            }
            Status::Auction => "Waiting for everyone to submit their bids in DM".to_owned(),
        }
    }
}
