mod board;

use rand::{
    distributions::{Distribution, Uniform},
    rngs::ThreadRng,
    thread_rng,
};
use std::{
    collections::HashMap,
    time::{SystemTime, UNIX_EPOCH},
};

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
    fn stringify(&self) -> &'static str {
        match self {
            Self::Buy => "buy",
            Self::Roll => "roll",
            Self::Auction => "auction",
        }
    }
    fn serialize(&self) -> String {
        self.stringify().to_owned()
    }
    fn deserialize(status: &str) -> Self {
        match status {
            "roll" => Self::Roll,
            "buy" => Self::Buy,
            "auction" => Self::Auction,
            _ => todo!(),
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
    pub fn deserialize(player: &SerPlayer) -> Self {
        Self {
            user_id: player.0,
            username: player.1.clone(),
            ownership: player.2.clone(),
            position: player.3,
            money: player.4,
        }
    }
    pub fn change(&mut self, position: usize, looped: bool, change: Change) {
        self.position = position;
        match (change, looped) {
            (Change::None, false) | (Change::TaxedIncome, true) => {}
            (Change::None, true) => self.money += 200,
            (Change::TaxedIncome, false) => self.money -= 200,
            (Change::TaxedLuxury, _) => self.money -= 100,
        };
    }
    pub fn try_buying(&mut self, name: &str, prop: impl GetCost) -> (PoorOut, bool) {
        let cost: isize = prop.get_cost();
        let (out, success) = if self.money < cost {
            (
                format!(
                    "Not enough money. \n{} in the bank. {} costs {}",
                    self.money, name, cost
                ),
                false,
            )
        } else {
            self.money -= cost;
            self.ownership.insert(self.position, 0);
            (
                format!("Purchased {}. \n{} in the bank.", name, self.money),
                true,
            )
        };

        (PoorOut::new(out, String::new()), success)
    }
    fn win_bid(&mut self, tile_id: usize) {
        let _: Option<u8> = self.ownership.insert(tile_id, 0);
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

fn find_by_id<'game>(players: &'game mut [Player], user_id: usize) -> Option<&'game mut Player> {
    players
        .iter_mut()
        .find(|player: &&'game mut Player| player.user_id == user_id)
}

fn get_now_sec() -> usize {
    let now = SystemTime::now();
    usize::try_from(
        now.duration_since(UNIX_EPOCH)
            .expect("Time went backwards")
            .as_secs(),
    )
    .expect("No overflow from timestamp")
}

pub struct Game {
    current_player: usize,
    players: Vec<Player>,
    status: Status,
    biggest_bid: isize, // 0 means None
    bid_time_sec: usize,
    bidder_id: usize,
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
            biggest_bid: 0,
            bid_time_sec: 0,
            bidder_id: 0,
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
            self.biggest_bid,
            self.bid_time_sec,
            self.bidder_id,
        )
    }
    /// If an auction ends during deserialization, returns Some((money, tile_id))
    /// bidder_id can be got from ser_game
    pub fn deserialize(game: &SerGame) -> (Self, Option<(isize, usize)>) {
        let mut status: Status = Status::deserialize(&game.status);
        let mut current_player: usize = game.current_player;
        let mut players: Vec<Player> = game.players.iter().map(Player::deserialize).collect();
        let bid_time_sec: usize = game.bid_time_sec;

        let maybe_auction: Option<(isize, usize)> = (matches!(status, Status::Auction)
            && (get_now_sec() - bid_time_sec > 10))
            .then(|| -> (isize, usize) {
                // 10 seconds passed, the biggest bid gets the purchase
                status = Status::Roll;

                let player: &Player = &players[current_player];
                let tile_id: usize = player.position;

                if current_player + 1 < players.len() {
                    current_player += 1;
                } else {
                    current_player = 0;
                }

                let bidder: &mut Player = find_by_id(&mut players, game.bidder_id)
                    .expect("bid won't allow invalid players");
                bidder.win_bid(tile_id);

                (bidder.money, tile_id)
            });

        (
            Self {
                current_player,
                players,
                status,
                biggest_bid: game.biggest_bid,
                bid_time_sec,
                bidder_id: game.bidder_id,
            },
            maybe_auction,
        )
    }
    /// Returns result and position, money if they changed
    pub fn roll(&mut self, caller_id: usize) -> (PoorOut, Option<(usize, isize, &'static str)>) {
        if !matches!(self.status, Status::Roll) {
            // Do nothing if it's not the time to roll
            return (PoorOut::empty(), None);
        }

        let player_count: usize = self.players.len();

        let player: &Player = &self.players[self.current_player];

        if player.user_id != caller_id {
            // Do nothing if it's not the callers turn to roll
            return (PoorOut::empty(), None);
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
            return (output, Some((position, player.money, "roll")));
        }

        let has_owner: bool = check_owner(&self.players, &position);

        // TODO
        let player_change: Change = match landed_on.inner {
            TileType::Street(prop) if !has_owner => {
                self.status = Status::Buy;
                output =
                    output.merge_out(&format!("Buy for {} or start an auction.", prop.get_cost()));
                Change::None
            }
            TileType::Railroad(prop) if !has_owner => {
                self.status = Status::Buy;
                output =
                    output.merge_out(&format!("Buy for {} or start an auction.", prop.get_cost()));
                Change::None
            }
            TileType::Utility(prop) if !has_owner => {
                self.status = Status::Buy;
                output =
                    output.merge_out(&format!("Buy for {} or start an auction.", prop.get_cost()));
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

        let player: &mut Player = &mut self.players[self.current_player];

        player.change(position, looped, player_change);
        if matches!(self.status, Status::Roll) {
            self.current_player = if self.current_player + 1 < player_count {
                self.current_player + 1
            } else {
                0
            };
        }

        if looped {
            output = output.merge_out("Passed GO.");
        }
        output = output.merge_out(&format!("{} in the bank.", player.money));

        (
            output,
            Some((position, player.money, self.status.stringify())),
        )
    }
    /// Returns result and money with tile_id if successful
    pub fn buy(&mut self, caller_id: usize) -> (PoorOut, Option<(isize, usize)>) {
        if !matches!(self.status, Status::Buy) {
            // Do nothing if it's not the time to buy
            return (PoorOut::empty(), None);
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
            return (PoorOut::empty(), None);
        } else if let Some(owner) = find_owner(&self.players, &player.position) {
            return (
                PoorOut::new(
                    format!(
                        "This property is already owned by {}",
                        owner.username.as_deref().unwrap_or("None")
                    ),
                    String::new(),
                ),
                None,
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
            (output, Some((player.money, player.position)))
        } else {
            (output, None)
        }
    }
    /// Returns Some(bid_time_sec) if auction starts successfully
    pub fn auction(&mut self, caller_id: usize) -> (PoorOut, Option<usize>) {
        if !matches!(self.status, Status::Buy) {
            // Do nothing if it's not the time to start auctions
            return (PoorOut::empty(), None);
        }

        let player: &Player = &self.players[self.current_player];
        if player.user_id != caller_id {
            // Do nothing if it's not the caller's turn to start auctions
            return (PoorOut::empty(), None);
        } else if player.money < 40 {
            return (
                PoorOut::new(
                    "You don't have enough money to start a bid.".to_owned(),
                    String::new(),
                ),
                None,
            );
        }

        self.status = Status::Auction;
        self.bidder_id = caller_id;
        self.bid_time_sec = get_now_sec();
        self.biggest_bid = 40;

        (
            PoorOut::new(
                "Starting an auction. Starting bid is 40. \n10 seconds to make a bid".to_owned(),
                String::new(),
            ),
            Some(self.bid_time_sec),
        )
    }
    /// Returns Some(bid_time_sec) if bid is accepted
    pub fn bid(&mut self, caller_id: usize, price: isize) -> (PoorOut, Option<usize>) {
        if !matches!(self.status, Status::Auction) {
            // Do nothing if it's not the time to make bids
            return (PoorOut::empty(), None);
        } else if self.biggest_bid >= price {
            return (
                PoorOut::new("Enter a bigger bid".to_owned(), String::new()),
                None,
            );
        }

        self.biggest_bid = price;
        self.bidder_id = caller_id;
        self.bid_time_sec = get_now_sec();

        (
            PoorOut::new(format!("Biggest bid {}", self.biggest_bid), String::new()),
            Some(self.bid_time_sec),
        )
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
    pub fn get_position(&self, user_id: usize) -> usize {
        let Some(player) = self
            .players
            .iter()
            .find(|player: &&Player| player.user_id == user_id)
        else {
            // Return empty map if caller is not a player
            return 101;
        };
        player.position
    }
}
