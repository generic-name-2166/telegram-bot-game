use pyo3::pyclass;

#[pyclass]
pub struct PoorResult {
    #[pyo3(get)]
    out: String,
    #[pyo3(get)]
    warning: String,
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
}

impl From<PoorOut> for PoorResult {
    fn from(value: PoorOut) -> Self {
        Self {
            out: value.out,
            warning: value.warning,
        }
    }
}
