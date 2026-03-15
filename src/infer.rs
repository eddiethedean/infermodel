//! Top-level inference: walk list[dict], build schema, return Python-friendly output.

use crate::classify::{classify_value, ValueClass};
use crate::config::InferConfig;
use crate::error::InferError;
use crate::merge::{value_class_to_type_spec, FieldEvidence};
use crate::serialize::schema_to_python_dict;
use crate::spec::{FieldSpec, ModelSpec, TypeSpec};
use indexmap::IndexMap;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::types::PyList;
use std::collections::HashMap;

/// Run inference on Python list[dict] and return a schema (ModelSpec).
pub fn infer_schema_impl(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
    _config: &InferConfig,
) -> Result<ModelSpec, InferError> {
    let list = data
        .downcast::<PyList>()
        .map_err(|_| InferError::InvalidInput("expected a list".to_string()))?;

    let mut field_evidence: HashMap<String, FieldEvidence> = HashMap::new();
    let total_rows = list.len();

    for item in list.iter() {
        let dict = item
            .downcast::<PyDict>()
            .map_err(|_| InferError::InvalidInput("expected list of dicts".to_string()))?;

        for (key, value) in dict.iter() {
            let name = key
                .extract::<String>()
                .or_else(|_| key.str().map(|s| s.to_string()))
                .map_err(|_| InferError::InvalidInput("dict keys must be strings".to_string()))?;

            let evidence = field_evidence.entry(name).or_default();
            evidence.presence_count += 1;

            let class = classify_value(&value)
                .map_err(|e| InferError::InvalidInput(e.to_string()))?;
            if class == ValueClass::None {
                evidence.null_count += 1;
            } else {
                let spec = value_class_to_type_spec(&class);
                evidence.type_spec = Some(match &evidence.type_spec {
                    Some(existing) => merge_type_specs(existing, &spec, _config)?,
                    None => spec,
                });
            }
        }
    }

    let mut fields = IndexMap::new();
    for (name, evidence) in field_evidence {
        let total = total_rows as u32;
        let required = evidence.presence_count >= total && total > 0;
        let nullable = evidence.null_count > 0;
        let spec = evidence
            .type_spec
            .unwrap_or(TypeSpec::Any);
        fields.insert(
            name.clone(),
            FieldSpec {
                name,
                spec,
                required,
                nullable,
            },
        );
    }

    Ok(ModelSpec::with_fields(fields))
}

fn merge_type_specs(
    a: &TypeSpec,
    b: &TypeSpec,
    _config: &InferConfig,
) -> Result<TypeSpec, InferError> {
    match (a, b) {
        (TypeSpec::Int, TypeSpec::Float) | (TypeSpec::Float, TypeSpec::Int) => Ok(TypeSpec::Float),
        (x, y) if std::mem::discriminant(x) == std::mem::discriminant(y) => Ok(a.clone()),
        _ => Ok(TypeSpec::Any),
    }
}

/// Entry point: infer schema from list[dict], return Python-dict.
pub fn infer_schema_py(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
) -> PyResult<PyObject> {
    let config = InferConfig::default();
    let model = infer_schema_impl(py, data, &config)?;
    let value = schema_to_python_dict(&model);
    Ok(crate::value_to_python(py, &value)?)
}
