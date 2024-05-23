use pyo3::prelude::{pyfunction, pymodule, PyResult, PyModule, Bound, wrap_pyfunction};

#[pyfunction]
pub fn add(left: usize, right: usize) -> PyResult<String> {
    Ok((left + right).to_string())
}

#[pymodule]
fn monopoly(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(add, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}
