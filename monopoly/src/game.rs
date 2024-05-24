mod board;

use rand::{
    distributions::{Distribution, Uniform},
    rngs::ThreadRng,
    thread_rng,
};
use std::collections::HashMap;

use crate::{
    game::board::{Tile, TileType, BOARD},
    io::PoorOut,
};

pub struct Player {
    user_id: usize,
    username: Option<String>,
    ownership: HashMap<usize, Vec<usize>>,
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
}

fn roll_dice() -> (usize, usize) {
    let mut rng: ThreadRng = thread_rng();
    let side: Uniform<usize> = Uniform::new(1, 7);
    (side.sample(&mut rng), side.sample(&mut rng))
}

pub struct Game {
    current_player: usize,
    players: Vec<Player>,
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
        }
    }
    pub fn roll(&mut self, called_id: usize) -> PoorOut {
        let player_count: usize = self.players.len();

        let player: &mut Player = self
            .players
            .get_mut(self.current_player)
            .expect("pointers have been tracked accurately");

        self.current_player = if self.current_player + 1 < player_count {
            self.current_player + 1
        } else {
            0
        };

        if player.user_id != called_id {
            // Do nothing if it's not the callers turn to roll
            return PoorOut::empty();
        }

        let (roll_1, roll_2) = roll_dice();

        let move_to: usize = roll_1 + roll_2 + player.position;

        let position: usize = if move_to >= 40 {
            player.money += 200;
            move_to - 40
        } else {
            move_to
        };

        let landed_on: Tile = BOARD[position];

        let output: PoorOut = PoorOut::new(
            format!(
                "{:?} has rolled {} and {}. \nNow on {} with {} in the bank.",
                player.username.as_deref(),
                roll_1,
                roll_2,
                landed_on.name,
                player.money,
            ),
            String::new(),
        );

        if player.ownership.contains_key(&position) {
            return output;
        }
        // TODO
        /* match landed_on.inner {
            TileType::Street(_) => todo!(),
            TileType::Railroad(_) => todo!(),
            TileType::Utility(_) => todo!(),
            TileType::Chance => todo!(),
            TileType::Chest => todo!(),
            TileType::GoToJail => todo!(),
            TileType::TaxIncome => todo!(),
            TileType::TaxLuxury => todo!(),
            TileType::Free | TileType::JailVisit | TileType::Go => {}
        } */
        output
    }
    pub fn get_status(&mut self) -> String {
        todo!()
    }
}
