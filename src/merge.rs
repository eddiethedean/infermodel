//! Merge observed types and apply policy (scalar, list, nested model).

use crate::config::InferConfig;
use crate::spec::{TypeSpec};
use crate::error::InferError;

/// Accumulated evidence for a single field across rows.
#[derive(Debug, Default)]
pub struct FieldEvidence {
    pub presence_count: u32,
    pub null_count: u32,
    pub type_spec: Option<TypeSpec>,
}

/// Merge two scalar type specs (e.g. int + float -> float).
pub fn merge_scalar_types(
    a: &crate::classify::ValueClass,
    b: &crate::classify::ValueClass,
    _config: &InferConfig,
) -> Result<TypeSpec, InferError> {
    use crate::classify::ValueClass;
    if a == b {
        return Ok(match a {
            ValueClass::None => TypeSpec::Any,
            ValueClass::Bool => TypeSpec::Bool,
            ValueClass::Int => TypeSpec::Int,
            ValueClass::Float => TypeSpec::Float,
            ValueClass::Str => TypeSpec::String,
            ValueClass::Date => TypeSpec::Date,
            ValueClass::DateTime => TypeSpec::DateTime,
            ValueClass::Time => TypeSpec::Time,
            ValueClass::List | ValueClass::Dict | ValueClass::Other => TypeSpec::Any,
        });
    }
    // int + float -> float (with promote)
    match (a, b) {
        (ValueClass::Int, ValueClass::Float) | (ValueClass::Float, ValueClass::Int) => {
            Ok(TypeSpec::Float)
        }
        _ => Ok(TypeSpec::Any),
    }
}

/// Convert a single ValueClass to TypeSpec (for scalars only).
pub fn value_class_to_type_spec(v: &crate::classify::ValueClass) -> TypeSpec {
    use crate::classify::ValueClass;
    match v {
        ValueClass::None => TypeSpec::Any,
        ValueClass::Bool => TypeSpec::Bool,
        ValueClass::Int => TypeSpec::Int,
        ValueClass::Float => TypeSpec::Float,
        ValueClass::Str => TypeSpec::String,
        ValueClass::Date => TypeSpec::Date,
        ValueClass::DateTime => TypeSpec::DateTime,
        ValueClass::Time => TypeSpec::Time,
        ValueClass::List | ValueClass::Dict | ValueClass::Other => TypeSpec::Any,
    }
}
