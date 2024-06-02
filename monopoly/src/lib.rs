mod game;
mod io;

use pyo3::prelude::{pyclass, pymethods, pymodule, Bound, PyModule, PyResult};

use crate::{
    game::{Game, RollResult},
    io::{pass_poor, PoorResult, SerGame},
};

#[pyclass(name = "Game")]
struct PyGame {
    inner: Game,
}

#[pymethods]
impl PyGame {
    #[new]
    fn new(info: Vec<(usize, Option<String>)>) -> Self {
        Self {
            inner: Game::new(info),
        }
    }
    fn serialize(&self) -> SerGame {
        self.inner.serialize()
    }
    #[staticmethod]
    fn deserialize(game: &SerGame) -> (Self, Option<(isize, usize)>) {
        let (inner, maybe_auction) = Game::deserialize(game);
        (Self { inner }, maybe_auction)
    }
    fn roll(&mut self, caller_id: usize) -> (PoorResult, Option<RollResult>) {
        pass_poor(self.inner.roll(caller_id))
    }
    fn buy(&mut self, caller_id: usize) -> (PoorResult, Option<(isize, usize)>) {
        pass_poor(self.inner.buy(caller_id))
    }
    fn auction(&mut self, caller_id: usize) -> (PoorResult, Option<usize>) {
        pass_poor(self.inner.auction(caller_id))
    }
    fn bid(&mut self, caller_id: usize, price: isize) -> (PoorResult, Option<usize>) {
        pass_poor(self.inner.bid(caller_id, price))
    }
    fn rent(&mut self, caller_id: usize) -> (PoorResult, Option<(isize, usize, isize)>) {
        pass_poor(self.inner.rent(caller_id))
    }
    fn get_status(&self, caller_id: usize) -> String {
        self.inner.get_status(caller_id)
    }
    fn get_position(&self, user_id: usize) -> usize {
        self.inner.get_position(user_id)
    }
    fn build(&mut self, user_id: usize, tile_id: usize) -> (PoorResult, Option<isize>) {
        pass_poor(self.inner.build(user_id, tile_id))
    }
}

#[pymodule]
fn monopoly(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyGame>()?;
    m.add_class::<PoorResult>()?;
    m.add_class::<SerGame>()?;
    Ok(())
}
