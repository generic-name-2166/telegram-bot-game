use pyo3::{pyclass, pymethods};
use std::collections::HashMap;

#[pyclass]
pub struct PoorResult {
    #[pyo3(get)]
    out: String,
    #[pyo3(get)]
    warning: String,
}

pub fn pass_poor<T>((out, other): (PoorOut, T)) -> (PoorResult, T) {
    (PoorResult::from(out), other)
}

pub struct PoorOut {
    pub out: String,
    pub warning: String,
}

impl PoorOut {
    pub const fn new(out: String, warning: String) -> Self {
        Self { out, warning }
    }
    pub const fn empty() -> Self {
        Self {
            out: String::new(),
            warning: String::new(),
        }
    }
    pub fn merge(self, rhs: Self) -> Self {
        let out: String = match (self.out.is_empty(), rhs.out.is_empty()) {
            (_, true) => self.out,
            (true, false) => rhs.out,
            (false, false) => self.out + " \n" + &rhs.out,
        };
        let warning: String = match (self.warning.is_empty(), rhs.warning.is_empty()) {
            (_, true) => self.warning,
            (true, false) => rhs.warning,
            (false, false) => self.warning + " \n" + &rhs.warning,
        };

        Self { out, warning }
    }
    pub fn merge_out(self, rhs: &str) -> Self {
        Self {
            out: self.out + " \n" + rhs,
            ..self
        }
    }
}

impl From<PoorOut> for PoorResult {
    fn from(value: PoorOut) -> Self {
        Self {
            out: value.out,
            warning: value.warning,
        }
    }
}

pub type SerPlayer = (usize, Option<String>, HashMap<usize, u8>, usize, isize, bool, u8);

#[pyclass]
pub struct SerGame {
    #[pyo3(get)]
    pub current_player: usize,
    #[pyo3(get)]
    pub status: String,
    #[pyo3(get)]
    pub players: Vec<SerPlayer>,
    #[pyo3(get)]
    pub biggest_bid: isize,
    #[pyo3(get)]
    pub bid_time_sec: usize,
    #[pyo3(get)]
    pub bidder_id: usize,
}

#[pymethods]
impl SerGame {
    #[new]
    pub const fn new(
        current_player: usize,
        status: String,
        players: Vec<SerPlayer>,
        biggest_bid: isize,
        bid_time_sec: usize,
        bidder_id: usize,
    ) -> Self {
        Self {
            current_player,
            status,
            players,
            biggest_bid,
            bid_time_sec,
            bidder_id,
        }
    }
}
