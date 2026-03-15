//! PyO3 entry points for infermodel.

mod classify;
mod config;
mod error;
mod infer;
mod merge;
mod serialize;
mod spec;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use serde_json::Value;

/// Convert serde_json::Value to a Python object (dict, list, str, int, float, bool).
pub(crate) fn value_to_python(py: Python<'_>, v: &Value) -> PyResult<PyObject> {
    match v {
        Value::Null => Ok(py.None().into_py(py)),
        Value::Bool(b) => Ok(b.into_py(py)),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.into_py(py))
            } else if let Some(f) = n.as_f64() {
                Ok(f.into_py(py))
            } else {
                Ok(n.as_f64().unwrap_or(0.0).into_py(py))
            }
        }
        Value::String(s) => Ok(s.into_py(py)),
        Value::Array(arr) => {
            let list = PyList::empty_bound(py);
            for item in arr {
                list.append(value_to_python(py, item)?)?;
            }
            Ok(list.into_py(py))
        }
        Value::Object(obj) => {
            let dict = PyDict::new_bound(py);
            for (k, v) in obj {
                dict.set_item(k.as_str(), value_to_python(py, v)?)?;
            }
            Ok(dict.into_py(py))
        }
    }
}

/// Infer a schema from a sequence of mappings (e.g. list of dicts).
///
/// Returns a nested dict with "type": "model", "fields": { name: { type, required, nullable }, ... }.
/// By default, number strings ("42", "3.14") are inferred as int/float; set infer_string_numbers=false to keep all strings as str.
#[pyfunction]
#[pyo3(signature = (data, *, infer_string_numbers=true, infer_string_literals=false))]
fn infer_schema(
    data: &Bound<'_, PyAny>,
    infer_string_numbers: bool,
    infer_string_literals: bool,
) -> PyResult<PyObject> {
    let py = data.py();
    infer::infer_schema_py(py, data, infer_string_numbers, infer_string_literals)
}

#[pymodule]
#[pyo3(name = "_infermodel")]
fn _infermodel(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(infer_schema, m)?)?;
    Ok(())
}
