//! Merge observed types and apply policy (scalar, list, nested model).

use crate::classify::ValueClass;
use crate::config::{DictMixedPolicy, InferConfig};
use crate::spec::{ModelSpec, TypeSpec};
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
    a: &ValueClass,
    b: &ValueClass,
    config: &InferConfig,
) -> Result<TypeSpec, InferError> {
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
    // int + float -> float (with promote policy)
    match (a, b) {
        (ValueClass::Int, ValueClass::Float) | (ValueClass::Float, ValueClass::Int) => {
            match config.numeric_promotion {
                crate::config::NumericPromotionPolicy::Promote => Ok(TypeSpec::Float),
                crate::config::NumericPromotionPolicy::Strict => Ok(TypeSpec::Any),
            }
        }
        _ => Ok(TypeSpec::Any),
    }
}

/// Convert a single ValueClass to TypeSpec (for scalars only).
pub fn value_class_to_type_spec(v: &ValueClass, _config: &InferConfig) -> TypeSpec {
    match v {
        ValueClass::None => TypeSpec::Any,
        ValueClass::Bool => TypeSpec::Bool,
        ValueClass::Int => TypeSpec::Int,
        ValueClass::Float => TypeSpec::Float,
        ValueClass::Str => TypeSpec::String,
        ValueClass::Date => TypeSpec::Date,
        ValueClass::DateTime => TypeSpec::DateTime,
        ValueClass::Time => TypeSpec::Time,
        // Lists and nested models are handled elsewhere (future work for lists).
        ValueClass::List | ValueClass::Other => TypeSpec::Any,
        // Dicts participate in nested model inference; treat as Any at scalar level.
        ValueClass::Dict => TypeSpec::Any,
    }
}

/// Merge two TypeSpec values, including nested models.
pub fn merge_type_specs(
    a: &TypeSpec,
    b: &TypeSpec,
    config: &InferConfig,
) -> Result<TypeSpec, InferError> {
    use TypeSpec::*;
    match (a, b) {
        // Identical types: keep either.
        (x, y) if std::mem::discriminant(x) == std::mem::discriminant(y) => Ok(a.clone()),
        // Promote int/float combinations using scalar rules.
        (Int, Float) | (Float, Int) => merge_scalar_types(&ValueClass::Int, &ValueClass::Float, config),
        // Merging two nested models: merge field-wise.
        (Model(m1), Model(m2)) => Ok(Model(merge_models(m1, m2, config)?)),
        // Dict mixed with non-dict: respect policy (currently Any/Union/Error).
        (Model(_), _other) | (_other, Model(_)) => match config.dict_mixed_policy {
            DictMixedPolicy::Any => Ok(Any),
            DictMixedPolicy::Union => Ok(Union(vec![a.clone(), b.clone()])),
            DictMixedPolicy::Error => Err(InferError::PolicyError(format!(
                "dict/non-dict conflict between {:?} and {:?}",
                a, b
            ))),
        },
        // Fallback: incompatible scalar/list/union mixes go to Any for now.
        _ => Ok(Any),
    }
}

/// Merge two ModelSpec structures field-by-field.
fn merge_models(
    a: &ModelSpec,
    b: &ModelSpec,
    config: &InferConfig,
) -> Result<ModelSpec, InferError> {
    let mut merged = ModelSpec::new();
    // Union of field names from both models.
    for (name, field_a) in &a.fields {
        if let Some(field_b) = b.fields.get(name) {
            let spec = merge_type_specs(&field_a.spec, &field_b.spec, config)?;
            merged.fields.insert(
                name.clone(),
                crate::spec::FieldSpec {
                    name: name.clone(),
                    spec,
                    required: field_a.required && field_b.required,
                    nullable: field_a.nullable || field_b.nullable,
                },
            );
        } else {
            merged.fields.insert(name.clone(), field_a.clone());
        }
    }
    for (name, field_b) in &b.fields {
        if !merged.fields.contains_key(name) {
            merged.fields.insert(name.clone(), field_b.clone());
        }
    }
    Ok(merged)
}
