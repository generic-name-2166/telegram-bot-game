mod board;

use joinery::JoinableIterator;
use lazy_format::lazy_format;
use rand::{
    distributions::{Distribution, Uniform},
    rngs::ThreadRng,
    thread_rng,
};
use std::{
    collections::HashMap,
    fmt::Display,
    time::{SystemTime, UNIX_EPOCH},
};

use crate::{
    game::board::{
        chance_roll, chest_roll, Card, CardEffect, Colour, GetCost, Railroad, Tile, TileType,
        Utility, BOARD, COLOUR_BROWN, COLOUR_DARK_BLUE, COLOUR_GREEN, COLOUR_LIGHT_BLUE,
        COLOUR_ORANGE, COLOUR_PINK, COLOUR_RED, COLOUR_YELLOW,
    },
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

pub struct Player {
    user_id: usize,
    username: Option<String>,
    // tile id to number of houses built
    ownership: HashMap<usize, u8>,
    pub position: usize,
    pub money: isize,
    pub is_jailed: bool,
    pub streak: u8,
}

impl Player {
    pub fn new(user_id: usize, username: Option<String>) -> Self {
        Self {
            user_id,
            username,
            ownership: HashMap::new(),
            position: 0,
            money: 1500,
            is_jailed: false,
            streak: 0,
        }
    }
    pub fn serialize(&self) -> SerPlayer {
        (
            self.user_id,
            self.username.clone(),
            self.ownership.clone(),
            self.position,
            self.money,
            self.is_jailed,
            self.streak,
        )
    }
    pub fn deserialize(player: &SerPlayer) -> Self {
        Self {
            user_id: player.0,
            username: player.1.clone(),
            ownership: player.2.clone(),
            position: player.3,
            money: player.4,
            is_jailed: player.5,
            streak: player.6,
        }
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
        let cost = match BOARD[tile_id].inner {
            TileType::Street(prop) => prop.get_cost(),
            TileType::Railroad(prop) => prop.get_cost(),
            TileType::Utility(prop) => prop.get_cost(),
            TileType::Chance
            | TileType::Chest
            | TileType::Free
            | TileType::Go
            | TileType::GoToJail
            | TileType::JailVisit
            | TileType::TaxIncome
            | TileType::TaxLuxury => unreachable!(),
        };
        self.money -= cost;
    }
    fn go_to_jail(&mut self) {
        self.streak = 0;
        self.is_jailed = true;
        self.position = 10;
    }
    fn roll_card<const IS_CHANCE: bool>(&mut self) -> &'static str {
        let card: Card = if IS_CHANCE {
            chance_roll()
        } else {
            chest_roll()
        };
        match card.effect {
            CardEffect::Assession => {
                // TODO
            }
            CardEffect::GetOutOfJail => {
                // TODO
            }
            CardEffect::GoBack3 => {
                self.position = if self.position >= 3 {
                    self.position - 3
                } else {
                    40 + self.position - 3
                };
            }
            CardEffect::GoToJail => {
                // TODO
            }
            CardEffect::Money(money) => self.money += money,
            CardEffect::NearestStation => {
                self.position = match self.position {
                    ..=4 => 5,
                    5..=14 => 15,
                    15..=24 => 25,
                    25..=35 => 35,
                    _ => 5,
                };
                // TODO rent effects here
            }
            CardEffect::NearestUtility => {
                self.position = match self.position {
                    ..=11 => 12,
                    12..=27 => 28,
                    _ => 12,
                };
                // TODO rent effects here
            }
            CardEffect::PayAll(_money) => {
                // TODO
            }
            CardEffect::Position(position) => {
                if position < self.position {
                    self.money += 200;
                }
                self.position = position;
            }
            CardEffect::Repairs => {
                // TODO
            }
        }
        card.note
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

fn find_by_id_mut(players: &mut [Player], user_id: usize) -> Option<&mut Player> {
    players
        .iter_mut()
        .find(|player: &&mut Player| player.user_id == user_id)
}

fn find_by_id(players: &[Player], user_id: usize) -> Option<&Player> {
    players
        .iter()
        .find(|player: &&Player| player.user_id == user_id)
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

fn format_ownership(row: (&usize, &u8)) -> impl Display {
    let (&tile_id, &house_count) = row;
    let name: &'static str = BOARD[tile_id].name;
    lazy_format!("{tile_id}. {name} - {house_count} house(s)")
}

pub struct Game {
    current_player: usize,
    players: Vec<Player>,
    status: Status,
    biggest_bid: isize, // 0 means None
    bid_time_sec: usize,
    bidder_id: usize,
}

/// position, money, is_jailed, streak, game.status == "buy"
pub type RollResult = (usize, isize, bool, u8, bool);

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

                let bidder: &mut Player = find_by_id_mut(&mut players, game.bidder_id)
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
    /// Returns result and Some((position, money, is_jailed, streak, game.status == "buy")) if changed
    pub fn roll(&mut self, caller_id: usize) -> (PoorOut, Option<RollResult>) {
        if !matches!(self.status, Status::Roll) {
            // Do nothing if it's not the time to roll
            return (PoorOut::empty(), None);
        } else if self.players[self.current_player].user_id != caller_id {
            // Do nothing if it's not the callers turn to roll
            return (PoorOut::empty(), None);
        }

        let player_count: usize = self.players.len();

        let (roll_1, roll_2) = roll_dice();
        let rolled_double: bool = roll_1 == roll_2;

        let move_to: usize = roll_1 + roll_2 + self.players[self.current_player].position;

        let (looped, position) = if move_to >= 40 {
            (true, move_to - 40)
        } else {
            (false, move_to)
        };

        let has_owner: bool = check_owner(&self.players, &position);

        let player: &mut Player = &mut self.players[self.current_player];

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

        if looped {
            player.money += 200;
            output = output.merge_out("Passed GO.");
        }
        player.position = position;

        if rolled_double && player.streak >= 2 {
            output = output.merge_out("Rolled double 3 times in a row, go to jail.");
            player.go_to_jail();
            return (output, Some((10, player.money, true, 0, false)));
        } else if rolled_double {
            player.streak += 1;
        } else {
            player.streak = 0;
        }

        if player.ownership.contains_key(&position) {
            return (
                output,
                Some((position, player.money, false, player.streak, false)),
            );
        }

        // TODO
        match landed_on.inner {
            TileType::Street(prop) if !has_owner => {
                self.status = Status::Buy;
                output =
                    output.merge_out(&format!("Buy for {} or start an auction.", prop.get_cost()));
            }
            TileType::Railroad(prop) if !has_owner => {
                self.status = Status::Buy;
                output =
                    output.merge_out(&format!("Buy for {} or start an auction.", prop.get_cost()));
            }
            TileType::Utility(prop) if !has_owner => {
                self.status = Status::Buy;
                output =
                    output.merge_out(&format!("Buy for {} or start an auction.", prop.get_cost()));
            }
            TileType::Chance => output = output.merge_out(player.roll_card::<true>()),
            TileType::Chest => output = output.merge_out(player.roll_card::<false>()),
            TileType::GoToJail => {
                player.go_to_jail();
                return (output, Some((10, player.money, true, 0, false)));
            }
            // TODO bankruptcy
            TileType::TaxIncome => player.money -= 200,
            TileType::TaxLuxury => player.money -= 100,
            TileType::Street(_)
            | TileType::Railroad(_)
            | TileType::Utility(_)
            | TileType::Free
            | TileType::JailVisit
            | TileType::Go => {}
        };

        let is_roll: bool = matches!(self.status, Status::Roll);

        if is_roll && !rolled_double {
            self.current_player = if self.current_player + 1 < player_count {
                self.current_player + 1
            } else {
                0
            };
        }
        output = output.merge_out(&format!("{} in the bank.", player.money));

        (
            output,
            Some((position, player.money, false, player.streak, !is_roll)),
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
        let tile = BOARD[player.position];
        if player.user_id != caller_id {
            // Do nothing if it's not the caller's turn to start auctions
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
        } else if !matches!(
            tile.inner,
            TileType::Street(_) | TileType::Railroad(_) | TileType::Utility(_)
        ) {
            return (
                PoorOut::new("Non-purchasable tile".to_owned(), String::new()),
                None,
            );
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
    /// Returns Some(caller.money, rentee.user_id, rentee.money) if successful
    pub fn rent(&mut self, caller_id: usize) -> (PoorOut, Option<(isize, usize, isize)>) {
        let rentee: &Player = &self.players[self.current_player];
        if rentee.user_id == caller_id {
            return (
                PoorOut::new("Can't ask rent from yourself".to_owned(), String::new()),
                None,
            );
        }
        let Some((caller_order, caller)) = self
            .players
            .iter()
            .enumerate()
            .find(|(_order, player)| player.user_id == caller_id)
        else {
            // check here if caller is even a player
            return (PoorOut::empty(), None);
        };
        let Some(&house_count) = caller.ownership.get(&rentee.position) else {
            // Caller isn't an owner
            return (PoorOut::empty(), None);
        };
        let property: Tile = BOARD[rentee.position];
        let rent: isize = match property.inner {
            TileType::Street(prop) => prop.rent_prices[usize::from(house_count)],
            TileType::Railroad(_) => Railroad::calculate_rent(caller),
            TileType::Utility(_) => Utility::calculate_rent(caller),
            TileType::Chance
            | TileType::Chest
            | TileType::Free
            | TileType::Go
            | TileType::GoToJail
            | TileType::JailVisit
            | TileType::TaxIncome
            | TileType::TaxLuxury => unreachable!(),
        };

        let caller_name: &str = caller.username.as_deref().unwrap_or("None");
        let rentee_name: &str = rentee.username.as_deref().unwrap_or("None");
        let out: String = format!(
            "{} collected rent from {}. {} now has {}, {} now has {}.",
            caller_name, rentee_name, caller_name, caller.money, rentee_name, rentee.money,
        );
        let result: Option<(isize, usize, isize)> =
            Some((caller.money, rentee.user_id, rentee.money));

        self.players[caller_order].money += rent;
        self.players[self.current_player].money -= rent;

        (PoorOut::new(out, String::new()), result)
    }
    pub fn get_status(&self, caller_id: usize) -> String {
        let player: &Player = &self.players[self.current_player];

        let game_status: String = match self.status {
            Status::Roll => {
                "Waiting for ".to_owned()
                    + player.username.as_deref().unwrap_or("None")
                    + " to roll the dice."
            }
            Status::Buy => {
                "Waiting for ".to_owned()
                    + player.username.as_deref().unwrap_or("None")
                    + " to buy or auction off a property."
            }
            Status::Auction => "Waiting for bid submissions.".to_owned(),
        };

        let Some(caller) = find_by_id(&self.players, caller_id) else {
            return game_status;
        };

        if caller.ownership.is_empty() {
            return game_status;
        }

        let caller_status = caller
            .ownership
            .iter()
            .map(format_ownership)
            .join_with('\n');

        format!(
            "{}\n{} owns:\n{}",
            game_status,
            caller.username.as_deref().unwrap_or("None"),
            caller_status,
        )
    }
    pub fn get_position(&self, user_id: usize) -> usize {
        let Some(player) = find_by_id(&self.players, user_id) else {
            // Return empty map if caller is not a player
            return 101;
        };
        player.position
    }
    /// If successfull, returns Some(caller.money)
    pub fn build(&mut self, user_id: usize, tile_id: usize) -> (PoorOut, Option<isize>) {
        let tile: Tile = BOARD[tile_id];
        let Some(player) = find_by_id_mut(&mut self.players, user_id) else {
            // Not a player
            return (PoorOut::empty(), None);
        };

        let Some(&house_count) = player.ownership.get(&tile_id) else {
            let out: String = "You don't own ".to_owned() + tile.name;
            return (PoorOut::new(out, String::new()), None);
        };

        if !matches!(tile.inner, TileType::Street(_)) {
            let out: String = "Can't build houses on ".to_owned() + tile.name;
            return (PoorOut::new(out, String::new()), None);
        } else if house_count == 5 {
            let out: String = "Can't build any more on ".to_owned() + tile.name;
            return (PoorOut::new(out, String::new()), None);
        }

        let (colour, price): (Colour, isize) = match tile_id {
            1 | 3 => (Colour::Brown, 100),
            6 | 8 | 9 => (Colour::LightBlue, 150),
            11 | 14 | 15 => (Colour::Pink, 300),
            16 | 18 | 19 => (Colour::Orange, 300),
            21 | 23 | 24 => (Colour::Red, 450),
            26 | 27 | 29 => (Colour::Yellow, 450),
            31 | 32 | 34 => (Colour::Green, 600),
            37 | 39 => (Colour::DarkBlue, 400),
            _ => unreachable!(),
        };

        if house_count == 0 {
            // Check full colour ownership
            // Check money
            // Cannot build unevenly
            let full_colour: bool = match colour {
                Colour::Brown => COLOUR_BROWN
                    .iter()
                    .all(|tile_id| player.ownership.contains_key(tile_id)),
                Colour::DarkBlue => COLOUR_DARK_BLUE
                    .iter()
                    .all(|tile_id| player.ownership.contains_key(tile_id)),
                Colour::Green => COLOUR_GREEN
                    .iter()
                    .all(|tile_id| player.ownership.contains_key(tile_id)),
                Colour::LightBlue => COLOUR_LIGHT_BLUE
                    .iter()
                    .all(|tile_id| player.ownership.contains_key(tile_id)),
                Colour::Orange => COLOUR_ORANGE
                    .iter()
                    .all(|tile_id| player.ownership.contains_key(tile_id)),
                Colour::Pink => COLOUR_PINK
                    .iter()
                    .all(|tile_id| player.ownership.contains_key(tile_id)),
                Colour::Red => COLOUR_RED
                    .iter()
                    .all(|tile_id| player.ownership.contains_key(tile_id)),
                Colour::Yellow => COLOUR_YELLOW
                    .iter()
                    .all(|tile_id| player.ownership.contains_key(tile_id)),
            };
            if !full_colour {
                let out: String = "You need to have colour monopoly to build.".to_owned();
                (PoorOut::new(out, String::new()), None)
            } else if player.money < price {
                let out: String = format!(
                    "Not enough money. You have {}, building costs {}.",
                    player.money, price,
                );
                (PoorOut::new(out, String::new()), None)
            } else {
                player.money -= price;
                let out: String = format!("Built 3 houses. {} in the bank", player.money);
                (PoorOut::new(out, String::new()), Some(player.money))
            }
        } else if player.money < price {
            let out: String = format!(
                "Not enough money. You have {}, building costs {}.",
                player.money, price,
            );
            (PoorOut::new(out, String::new()), None)
        } else {
            player.money -= price;
            let _: Option<u8> = player.ownership.insert(tile_id, house_count + 1);

            let out: String = if house_count == 4 {
                format!("Built 3 hotels. {} in the bank", player.money)
            } else {
                format!("Built 3 houses. {} in the bank", player.money)
            };
            (PoorOut::new(out, String::new()), Some(player.money))
        }
    }
}
