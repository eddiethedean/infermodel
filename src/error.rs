//! Package errors for schema inference.

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::PyErr;
use std::fmt;

/// Errors that can occur during schema inference.
#[derive(Debug, Clone)]
pub enum InferError {
    /// Input is not a list of dicts.
    InvalidInput(String),
    /// Policy or config caused an error (e.g. strict mode conflict).
    PolicyError(String),
}

impl fmt::Display for InferError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            InferError::InvalidInput(msg) => write!(f, "invalid input: {}", msg),
            InferError::PolicyError(msg) => write!(f, "policy error: {}", msg),
        }
    }
}

impl std::error::Error for InferError {}

impl From<InferError> for PyErr {
    fn from(e: InferError) -> PyErr {
        match e {
            InferError::InvalidInput(msg) => PyTypeError::new_err(format!("invalid input: {}", msg)),
            InferError::PolicyError(msg) => PyValueError::new_err(format!("policy error: {}", msg)),
        }
    }
}
