//! Top-level inference: walk a sequence of mappings, build schema, return Python-friendly output.

use crate::classify::{classify_value, ValueClass};
use crate::config::InferConfig;
use crate::error::InferError;
use crate::merge::{value_class_to_type_spec, FieldEvidence};
use crate::serialize::schema_to_python_dict;
use crate::spec::{FieldSpec, ModelSpec, TypeSpec};
use indexmap::IndexMap;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

/// Run inference on a Python sequence of mappings (e.g. list of dicts) and return a schema (ModelSpec).
pub fn infer_schema_impl(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
    _config: &InferConfig,
) -> Result<ModelSpec, InferError> {
    let iter = data
        .iter()
        .map_err(|e| InferError::InvalidInput(format!("expected a sequence (iterable): {}", e)))?;

    let mut field_evidence: HashMap<String, FieldEvidence> = HashMap::new();
    let mut total_rows: u32 = 0;

    for item in iter {
        let item = item.map_err(|e| InferError::InvalidInput(e.to_string()))?;
        total_rows += 1;

        if let Ok(dict) = item.downcast::<PyDict>() {
            for (key, value) in dict.iter() {
                process_field(py, key, value, &mut field_evidence, _config)?;
            }
        } else if let Ok(items) = item.call_method0("items") {
            let items_iter = items
                .iter()
                .map_err(|e| InferError::InvalidInput(format!("expected mapping with .items(): {}", e)))?;
            for pair in items_iter {
                let pair = pair.map_err(|e| InferError::InvalidInput(e.to_string()))?;
                let key = pair
                    .get_item(0)
                    .map_err(|e| InferError::InvalidInput(e.to_string()))?;
                let value = pair
                    .get_item(1)
                    .map_err(|e| InferError::InvalidInput(e.to_string()))?;
                process_field(py, key, value, &mut field_evidence, _config)?;
            }
        } else {
            return Err(InferError::InvalidInput(
                "each sequence element must be a mapping (e.g. dict) with .items()".to_string(),
            ));
        }
    }

    let mut fields = IndexMap::new();
    for (name, evidence) in field_evidence {
        let required = evidence.presence_count >= total_rows && total_rows > 0;
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

fn process_field(
    _py: Python<'_>,
    key: Bound<'_, PyAny>,
    value: Bound<'_, PyAny>,
    field_evidence: &mut HashMap<String, FieldEvidence>,
    config: &InferConfig,
) -> Result<(), InferError> {
    let name = key
        .extract::<String>()
        .or_else(|_| key.str().map(|s| s.to_string()))
        .map_err(|_| InferError::InvalidInput("mapping keys must be strings".to_string()))?;

    let evidence = field_evidence.entry(name).or_default();
    evidence.presence_count += 1;

    let class = classify_value(
        &value,
        config.infer_string_numbers,
        config.infer_string_literals,
    )
    .map_err(|e| InferError::InvalidInput(e.to_string()))?;
    if class == ValueClass::None {
        evidence.null_count += 1;
    } else {
        let spec = value_class_to_type_spec(&class);
        evidence.type_spec = Some(match &evidence.type_spec {
            Some(existing) => merge_type_specs(existing, &spec, config)?,
            None => spec,
        });
    }
    Ok(())
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

/// Entry point: infer schema from sequence of mappings, return Python-dict.
pub fn infer_schema_py(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
    infer_string_numbers: bool,
    infer_string_literals: bool,
) -> PyResult<PyObject> {
    let config = InferConfig {
        infer_string_numbers,
        infer_string_literals,
        ..InferConfig::default()
    };
    let model = infer_schema_impl(py, data, &config)?;
    let value = schema_to_python_dict(&model);
    Ok(crate::value_to_python(py, &value)?)
}
