mod game;
mod io;

use pyo3::prelude::{pyclass, pymethods, pymodule, Bound, PyModule, PyResult};

use crate::{
    game::Game,
    io::{PoorResult, SerGame},
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
    fn roll(&mut self, caller_id: usize) -> PoorResult {
        PoorResult::from(self.inner.roll(caller_id))
    }
    fn buy(&mut self, caller_id: usize) -> PoorResult {
        PoorResult::from(self.inner.buy(caller_id))
    }
    fn auction(&mut self, caller_id: usize) -> PoorResult {
        PoorResult::from(self.inner.auction(caller_id))
    }
    fn bid(&mut self, caller_id: usize, price: isize) -> PoorResult {
        PoorResult::from(self.inner.bid(caller_id, price))
    }
    fn get_status(&self) -> String {
        self.inner.get_status()
    }
    fn serialize(&self) -> SerGame {
        self.inner.serialize()
    }
}

#[pymodule]
fn monopoly(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyGame>()?;
    m.add_class::<PoorResult>()?;
    m.add_class::<SerGame>()?;
    Ok(())
}
