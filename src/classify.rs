//! Classify Python values into internal type categories.

use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyList, PyLong, PyUnicode};
use std::fmt;

/// For string values, infer type from content based on flags.
/// When infer_string_literals: null-like, boolean-like.
/// When infer_string_numbers: int then float.
fn try_classify_string_content(s: &str, infer_string_numbers: bool, infer_string_literals: bool) -> ValueClass {
    let s = s.trim();
    if s.is_empty() {
        return ValueClass::Str;
    }
    if infer_string_literals {
        if s.eq_ignore_ascii_case("null") || s.eq_ignore_ascii_case("none") || s.eq_ignore_ascii_case("nil") {
            return ValueClass::None;
        }
        if s.eq_ignore_ascii_case("true") || s.eq_ignore_ascii_case("false")
            || s.eq_ignore_ascii_case("yes") || s.eq_ignore_ascii_case("no")
        {
            return ValueClass::Bool;
        }
    }
    if infer_string_numbers {
        if let Ok(_) = s.parse::<i64>() {
            return ValueClass::Int;
        }
        if let Ok(_) = s.parse::<f64>() {
            return ValueClass::Float;
        }
    }
    ValueClass::Str
}

/// Internal classification of a single value (before merging).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ValueClass {
    None,
    Bool,
    Int,
    Float,
    Str,
    Date,
    DateTime,
    Time,
    List,
    Dict,
    /// Unsupported or unknown (e.g. tuple, set) -> treat as Any
    Other,
}

impl fmt::Display for ValueClass {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ValueClass::None => write!(f, "none"),
            ValueClass::Bool => write!(f, "bool"),
            ValueClass::Int => write!(f, "int"),
            ValueClass::Float => write!(f, "float"),
            ValueClass::Str => write!(f, "str"),
            ValueClass::Date => write!(f, "date"),
            ValueClass::DateTime => write!(f, "datetime"),
            ValueClass::Time => write!(f, "time"),
            ValueClass::List => write!(f, "list"),
            ValueClass::Dict => write!(f, "dict"),
            ValueClass::Other => write!(f, "any"),
        }
    }
}

/// Classify a Python value into a [ValueClass].
/// infer_string_numbers (default on): parse "42", "3.14" as int/float. infer_string_literals (default off): parse "null", "true"/"false" etc.
pub fn classify_value(
    value: &Bound<'_, PyAny>,
    infer_string_numbers: bool,
    infer_string_literals: bool,
) -> PyResult<ValueClass> {
    if value.is_none() {
        return Ok(ValueClass::None);
    }
    if value.is_instance_of::<PyBool>() {
        return Ok(ValueClass::Bool);
    }
    if value.is_instance_of::<PyLong>() {
        return Ok(ValueClass::Int);
    }
    if value.is_instance_of::<PyFloat>() {
        return Ok(ValueClass::Float);
    }
    if value.is_instance_of::<PyUnicode>() {
        if infer_string_numbers || infer_string_literals {
            if let Ok(s) = value.extract::<String>() {
                return Ok(try_classify_string_content(&s, infer_string_numbers, infer_string_literals));
            }
        }
        return Ok(ValueClass::Str);
    }
    if value.is_instance_of::<PyList>() {
        return Ok(ValueClass::List);
    }
    if value.is_instance_of::<PyDict>() {
        return Ok(ValueClass::Dict);
    }
    // Optional: detect date, datetime, time via Python isinstance check
    let py = value.py();
    if let (Ok(builtins), Ok(module)) = (py.import_bound("builtins"), py.import_bound("datetime")) {
        if let Ok(isinstance) = builtins.getattr("isinstance") {
            if let Ok(cls) = module.getattr("date") {
                if isinstance.call1((value, cls)).and_then(|r| r.extract::<bool>()).unwrap_or(false) {
                    return Ok(ValueClass::Date);
                }
            }
            if let Ok(cls) = module.getattr("datetime") {
                if isinstance.call1((value, cls)).and_then(|r| r.extract::<bool>()).unwrap_or(false) {
                    return Ok(ValueClass::DateTime);
                }
            }
            if let Ok(cls) = module.getattr("time") {
                if isinstance.call1((value, cls)).and_then(|r| r.extract::<bool>()).unwrap_or(false) {
                    return Ok(ValueClass::Time);
                }
            }
        }
    }
    Ok(ValueClass::Other)
}
