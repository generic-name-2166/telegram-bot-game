use crate::game::{roll_dice, Player};

pub const BOARD: [Tile; 40] = [
    Tile::new("GO", TileType::Go),
    Tile::new(
        "Old Kent Road",
        TileType::Street(Street::new(60, [2, 10, 30, 90, 160, 250])),
    ),
    Tile::new("Community chest", TileType::Chest),
    Tile::new(
        "Whitechapel Road",
        TileType::Street(Street::new(60, [4, 20, 60, 180, 320, 450])),
    ),
    Tile::new("Income Tax", TileType::TaxIncome),
    Tile::new(
        "Kings Cross Station",
        TileType::Railroad(Railroad::new(200)),
    ),
    Tile::new(
        "The Angel, Islington",
        TileType::Street(Street::new(100, [6, 30, 90, 270, 400, 550])),
    ),
    Tile::new("Chance", TileType::Chance),
    Tile::new(
        "Euston Road",
        TileType::Street(Street::new(100, [6, 30, 90, 270, 400, 550])),
    ),
    Tile::new(
        "Pentonville Road",
        TileType::Street(Street::new(120, [8, 40, 100, 300, 450, 600])),
    ),
    Tile::new("Jail visiting", TileType::JailVisit),
    Tile::new(
        "Pall Mall",
        TileType::Street(Street::new(140, [10, 50, 150, 450, 625, 750])),
    ),
    Tile::new("Electric Company", TileType::Utility(Utility::new(150))),
    Tile::new(
        "Whitehall",
        TileType::Street(Street::new(140, [10, 50, 150, 450, 625, 750])),
    ),
    Tile::new(
        "Northumberland Avenue",
        TileType::Street(Street::new(160, [12, 60, 180, 500, 700, 900])),
    ),
    Tile::new("Marylebone Station", TileType::Railroad(Railroad::new(200))),
    Tile::new(
        "Bow Street",
        TileType::Street(Street::new(180, [14, 70, 200, 550, 750, 950])),
    ),
    Tile::new("Community Chest", TileType::Chest),
    Tile::new(
        "Marlborough Street",
        TileType::Street(Street::new(180, [14, 70, 200, 550, 750, 950])),
    ),
    Tile::new(
        "Vine Street",
        TileType::Street(Street::new(200, [16, 80, 220, 600, 800, 1000])),
    ),
    Tile::new("Free Parking", TileType::Free),
    Tile::new(
        "Strand",
        TileType::Street(Street::new(220, [18, 90, 250, 700, 875, 1050])),
    ),
    Tile::new("Chance", TileType::Chance),
    Tile::new(
        "Fleet Street",
        TileType::Street(Street::new(220, [18, 90, 250, 700, 875, 1050])),
    ),
    Tile::new(
        "Trafalgar Square",
        TileType::Street(Street::new(220, [20, 100, 300, 750, 925, 1100])),
    ),
    Tile::new(
        "Fenchurch St Station",
        TileType::Railroad(Railroad::new(200)),
    ),
    Tile::new(
        "Leicester Square",
        TileType::Street(Street::new(260, [22, 110, 330, 800, 975, 1150])),
    ),
    Tile::new(
        "Coventry Street",
        TileType::Street(Street::new(260, [22, 110, 330, 800, 975, 1150])),
    ),
    Tile::new("Water Works", TileType::Utility(Utility::new(150))),
    Tile::new(
        "Piccadilly",
        TileType::Street(Street::new(280, [24, 120, 360, 850, 1025, 1200])),
    ),
    Tile::new("Go To Jail", TileType::GoToJail),
    Tile::new(
        "Regent Street",
        TileType::Street(Street::new(300, [26, 130, 390, 900, 1100, 1275])),
    ),
    Tile::new(
        "Oxford Street",
        TileType::Street(Street::new(300, [26, 130, 390, 900, 1100, 1275])),
    ),
    Tile::new("Community Chest", TileType::Chest),
    Tile::new(
        "Bond Street",
        TileType::Street(Street::new(300, [28, 150, 450, 1000, 1200, 1400])),
    ),
    Tile::new(
        "Liverpool Street Station",
        TileType::Railroad(Railroad::new(200)),
    ),
    Tile::new("Chance", TileType::Chance),
    Tile::new(
        "Park Lane",
        TileType::Street(Street::new(350, [35, 175, 500, 1100, 1300, 1500])),
    ),
    Tile::new("Super Tax", TileType::TaxLuxury),
    Tile::new(
        "Mayfair",
        TileType::Street(Street::new(400, [50, 100, 600, 1400, 1700, 2000])),
    ),
];

const RAILROADS: [usize; 4] = [5, 15, 25, 35];
pub const UTILITIES: [usize; 2] = [12, 28];

pub trait GetCost {
    fn get_cost(&self) -> isize;
}

#[derive(Clone, Copy)]
pub struct Street {
    pub rent_prices: [isize; 6],
    pub cost: isize,
}

impl Street {
    const fn new(cost: isize, rent_prices: [isize; 6]) -> Self {
        Self { cost, rent_prices }
    }
}

impl GetCost for Street {
    fn get_cost(&self) -> isize {
        self.cost
    }
}

/// Cost
#[derive(Clone, Copy)]
pub struct Railroad {
    cost: isize,
}

impl Railroad {
    const fn new(cost: isize) -> Self {
        Self { cost }
    }
    pub fn calculate_rent(player: &Player) -> isize {
        // The formula - 25 * (2 ^ ({railroad_count} - 1))
        // Rust just requires u32 here for some reason
        let exp: u32 = RAILROADS
            .into_iter()
            .map(|railroad_id| {
                if player.ownership.contains_key(&railroad_id) {
                    1
                } else {
                    0
                }
            })
            .sum::<u32>()
            - 1;

        25 * 2_isize.pow(exp)
    }
}

impl GetCost for Railroad {
    fn get_cost(&self) -> isize {
        self.cost
    }
}

#[derive(Clone, Copy)]
pub struct Utility {
    cost: isize,
}

impl Utility {
    const fn new(cost: isize) -> Self {
        Self { cost }
    }
    pub fn calculate_rent(player: &Player) -> isize {
        let (roll_0, roll_1) = roll_dice();
        let rolled: isize = isize::try_from(roll_0 + roll_1).expect("rolled overflowing integer");
        if player.ownership.contains_key(&UTILITIES[0])
            && player.ownership.contains_key(&UTILITIES[1])
        {
            rolled * 10
        } else {
            rolled * 4
        }
    }
}

impl GetCost for Utility {
    fn get_cost(&self) -> isize {
        self.cost
    }
}

#[derive(Clone, Copy)]
pub enum TileType {
    Street(Street),
    Railroad(Railroad),
    Utility(Utility),
    Chance,
    Chest,
    TaxIncome,
    TaxLuxury,
    Go,
    Free,
    JailVisit,
    GoToJail,
}

#[derive(Clone, Copy)]
pub struct Tile {
    pub name: &'static str,
    pub inner: TileType,
}

impl Tile {
    const fn new(name: &'static str, inner: TileType) -> Self {
        Self { name, inner }
    }
}
