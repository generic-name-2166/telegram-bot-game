mod game;
mod io;

use io::PoorResult;
use pyo3::prelude::{
    pyclass, pyfunction, pymethods, pymodule, wrap_pyfunction, Bound, PyModule, PyResult,
};

use crate::game::Game;

#[pyfunction]
fn add(left: usize, right: usize) -> PyResult<String> {
    Ok((left + right).to_string())
}

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
    fn get_status(&mut self) -> String {
        self.inner.get_status()
    }
}

#[pymodule]
fn monopoly(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(add, m)?)?;
    m.add_class::<PyGame>()?;
    Ok(())
}
