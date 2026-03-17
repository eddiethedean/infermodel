//! Top-level inference: walk a sequence of mappings, build schema, return Python-friendly output.

use crate::classify::{classify_value, ValueClass};
use crate::config::{
    DictMixedPolicy, HeterogeneousListPolicy, IncompatibleScalarPolicy, InferConfig,
    MissingKeyPolicy, NullPolicy, NumericPromotionPolicy, StringDatePolicy,
};
use crate::error::InferError;
use crate::merge::{merge_type_specs, value_class_to_type_spec, FieldEvidence};
use crate::serialize::schema_to_python_dict;
use crate::spec::{FieldSpec, ModelSpec, TypeSpec};
use indexmap::IndexMap;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde_json::{Map, Value};
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
        if _config.sample_size > 0 && (total_rows as usize) >= _config.sample_size {
            break;
        }
        let item = item.map_err(|e| InferError::InvalidInput(e.to_string()))?;
        total_rows += 1;

        if let Ok(dict) = item.downcast::<PyDict>() {
            for (key, value) in dict.iter() {
                process_field(py, key, value, &mut field_evidence, _config)?;
            }
        } else if let Ok(items) = item.call_method0("items") {
            let items_iter = items.iter().map_err(|e| {
                InferError::InvalidInput(format!("expected mapping with .items(): {}", e))
            })?;
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
        let spec = evidence.type_spec.unwrap_or(TypeSpec::Any);
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

pub struct InferDiagnostics {
    pub rows_used: u32,
    pub sample_size: usize,
    pub field_evidence: HashMap<String, FieldEvidence>,
}

pub fn infer_schema_with_diagnostics_impl(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
    _config: &InferConfig,
) -> Result<(ModelSpec, InferDiagnostics), InferError> {
    let iter = data
        .iter()
        .map_err(|e| InferError::InvalidInput(format!("expected a sequence (iterable): {}", e)))?;

    let mut field_evidence: HashMap<String, FieldEvidence> = HashMap::new();
    let mut total_rows: u32 = 0;

    for item in iter {
        if _config.sample_size > 0 && (total_rows as usize) >= _config.sample_size {
            break;
        }
        let item = item.map_err(|e| InferError::InvalidInput(e.to_string()))?;
        total_rows += 1;

        if let Ok(dict) = item.downcast::<PyDict>() {
            for (key, value) in dict.iter() {
                process_field(py, key, value, &mut field_evidence, _config)?;
            }
        } else if let Ok(items) = item.call_method0("items") {
            let items_iter = items.iter().map_err(|e| {
                InferError::InvalidInput(format!("expected mapping with .items(): {}", e))
            })?;
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
    for (name, evidence) in &field_evidence {
        let required = evidence.presence_count >= total_rows && total_rows > 0;
        let nullable = evidence.null_count > 0;
        let spec = evidence.type_spec.clone().unwrap_or(TypeSpec::Any);
        fields.insert(
            name.clone(),
            FieldSpec {
                name: name.clone(),
                spec,
                required,
                nullable,
            },
        );
    }

    Ok((
        ModelSpec::with_fields(fields),
        InferDiagnostics {
            rows_used: total_rows,
            sample_size: _config.sample_size,
            field_evidence,
        },
    ))
}

fn process_field(
    py: Python<'_>,
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
    *evidence.type_counts.entry(class.to_string()).or_insert(0) += 1;
    if class == ValueClass::None {
        evidence.null_count += 1;
    } else if class == ValueClass::Dict {
        // Nested dict: recursively infer a nested ModelSpec for this single mapping value.
        // We treat the dict as a one-row dataset, so presence/nullable inside the nested
        // model are computed relative to that row only; merging across rows happens via
        // merge_type_specs on the resulting ModelSpec values.
        let nested_model = infer_single_mapping_schema(py, &value, config)?;
        let spec = TypeSpec::Model(nested_model);
        evidence.type_spec = Some(match &evidence.type_spec {
            Some(existing) => merge_type_specs(existing, &spec, config)?,
            None => spec,
        });
    } else {
        let spec = value_class_to_type_spec(&class, config);
        evidence.type_spec = Some(match &evidence.type_spec {
            Some(existing) => merge_type_specs(existing, &spec, config)?,
            None => spec,
        });
    }
    Ok(())
}

/// Infer a ModelSpec from a single mapping value (dict-like object).
fn infer_single_mapping_schema(
    py: Python<'_>,
    mapping: &Bound<'_, PyAny>,
    config: &InferConfig,
) -> Result<ModelSpec, InferError> {
    // Build a temporary dict-like iterable of one element: the mapping itself.
    // This mirrors the top-level infer_schema_impl logic but is specialized for
    // a single mapping so we don't rely on PyList or additional conversions.
    let mut field_evidence: std::collections::HashMap<String, FieldEvidence> =
        std::collections::HashMap::new();
    let total_rows: u32 = 1;

    if let Ok(dict) = mapping.downcast::<PyDict>() {
        for (key, value) in dict.iter() {
            process_field(py, key, value, &mut field_evidence, config)?;
        }
    } else if let Ok(items) = mapping.call_method0("items") {
        let items_iter = items.iter().map_err(|e| {
            InferError::InvalidInput(format!("expected mapping with .items(): {}", e))
        })?;
        for pair in items_iter {
            let pair = pair.map_err(|e| InferError::InvalidInput(e.to_string()))?;
            let key = pair
                .get_item(0)
                .map_err(|e| InferError::InvalidInput(e.to_string()))?;
            let value = pair
                .get_item(1)
                .map_err(|e| InferError::InvalidInput(e.to_string()))?;
            process_field(py, key, value, &mut field_evidence, config)?;
        }
    } else {
        return Err(InferError::InvalidInput(
            "nested value must be a mapping (e.g. dict) with .items()".to_string(),
        ));
    }

    let mut fields = IndexMap::new();
    for (name, evidence) in field_evidence {
        let required = evidence.presence_count >= total_rows && total_rows > 0;
        let nullable = evidence.null_count > 0;
        let spec = evidence.type_spec.unwrap_or(TypeSpec::Any);
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
/// Entry point: infer schema from iterable of mappings, return Python-dict.
pub fn infer_schema_py(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
    infer_string_numbers: bool,
    infer_string_literals: bool,
    incompatible_scalar_policy: &str,
    heterogeneous_list_policy: &str,
    dict_mixed_policy: &str,
    string_date_policy: &str,
    numeric_promotion: &str,
    missing_key_policy: &str,
    null_policy: &str,
    sample_size: usize,
) -> PyResult<PyObject> {
    let config = InferConfig {
        infer_string_numbers,
        infer_string_literals,
        incompatible_scalar_policy: parse_incompatible_scalar_policy(incompatible_scalar_policy)?,
        heterogeneous_list_policy: parse_heterogeneous_list_policy(heterogeneous_list_policy)?,
        dict_mixed_policy: parse_dict_mixed_policy(dict_mixed_policy)?,
        string_date_policy: parse_string_date_policy(string_date_policy)?,
        numeric_promotion: parse_numeric_promotion_policy(numeric_promotion)?,
        missing_key_policy: parse_missing_key_policy(missing_key_policy)?,
        null_policy: parse_null_policy(null_policy)?,
        sample_size,
        ..InferConfig::default()
    };
    let model = infer_schema_impl(py, data, &config)?;
    let value = schema_to_python_dict(&model);
    Ok(crate::value_to_python(py, &value)?)
}

pub fn infer_schema_with_diagnostics_py(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
    infer_string_numbers: bool,
    infer_string_literals: bool,
    incompatible_scalar_policy: &str,
    heterogeneous_list_policy: &str,
    dict_mixed_policy: &str,
    string_date_policy: &str,
    numeric_promotion: &str,
    missing_key_policy: &str,
    null_policy: &str,
    sample_size: usize,
) -> PyResult<PyObject> {
    let config = InferConfig {
        infer_string_numbers,
        infer_string_literals,
        incompatible_scalar_policy: parse_incompatible_scalar_policy(incompatible_scalar_policy)?,
        heterogeneous_list_policy: parse_heterogeneous_list_policy(heterogeneous_list_policy)?,
        dict_mixed_policy: parse_dict_mixed_policy(dict_mixed_policy)?,
        string_date_policy: parse_string_date_policy(string_date_policy)?,
        numeric_promotion: parse_numeric_promotion_policy(numeric_promotion)?,
        missing_key_policy: parse_missing_key_policy(missing_key_policy)?,
        null_policy: parse_null_policy(null_policy)?,
        sample_size,
        ..InferConfig::default()
    };

    let (model, diag) = infer_schema_with_diagnostics_impl(py, data, &config)?;

    let mut top = Map::new();
    top.insert("schema".to_string(), schema_to_python_dict(&model));

    let mut diag_obj = Map::new();
    diag_obj.insert(
        "rows_used".to_string(),
        Value::Number(diag.rows_used.into()),
    );
    diag_obj.insert(
        "sample_size".to_string(),
        Value::Number((diag.sample_size as u64).into()),
    );
    if diag.sample_size > 0 && (diag.rows_used as usize) >= diag.sample_size {
        diag_obj.insert("maybe_truncated".to_string(), Value::Bool(true));
    } else {
        diag_obj.insert("maybe_truncated".to_string(), Value::Bool(false));
    }

    let mut fields_obj = Map::new();
    for (name, evidence) in diag.field_evidence {
        let mut f = Map::new();
        f.insert(
            "presence_count".to_string(),
            Value::Number(evidence.presence_count.into()),
        );
        f.insert(
            "null_count".to_string(),
            Value::Number(evidence.null_count.into()),
        );
        let missing = diag.rows_used.saturating_sub(evidence.presence_count);
        f.insert("missing_count".to_string(), Value::Number(missing.into()));

        let mut counts = Map::new();
        for (k, v) in evidence.type_counts {
            counts.insert(k, Value::Number(v.into()));
        }
        f.insert("type_counts".to_string(), Value::Object(counts));
        fields_obj.insert(name, Value::Object(f));
    }
    diag_obj.insert("fields".to_string(), Value::Object(fields_obj));

    top.insert("diagnostics".to_string(), Value::Object(diag_obj));
    Ok(crate::value_to_python(py, &Value::Object(top))?)
}

fn parse_incompatible_scalar_policy(s: &str) -> Result<IncompatibleScalarPolicy, InferError> {
    match s {
        "any" => Ok(IncompatibleScalarPolicy::Any),
        "union" => Ok(IncompatibleScalarPolicy::Union),
        "error" => Ok(IncompatibleScalarPolicy::Error),
        _ => Err(InferError::InvalidInput(
            "incompatible_scalar_policy must be one of: any, union, error".to_string(),
        )),
    }
}

fn parse_heterogeneous_list_policy(s: &str) -> Result<HeterogeneousListPolicy, InferError> {
    match s {
        "any" => Ok(HeterogeneousListPolicy::Any),
        "union" => Ok(HeterogeneousListPolicy::Union),
        "error" => Ok(HeterogeneousListPolicy::Error),
        _ => Err(InferError::InvalidInput(
            "heterogeneous_list_policy must be one of: any, union, error".to_string(),
        )),
    }
}

fn parse_dict_mixed_policy(s: &str) -> Result<DictMixedPolicy, InferError> {
    match s {
        "any" => Ok(DictMixedPolicy::Any),
        "union" => Ok(DictMixedPolicy::Union),
        "error" => Ok(DictMixedPolicy::Error),
        _ => Err(InferError::InvalidInput(
            "dict_mixed_policy must be one of: any, union, error".to_string(),
        )),
    }
}

fn parse_string_date_policy(s: &str) -> Result<StringDatePolicy, InferError> {
    match s {
        "never" => Ok(StringDatePolicy::Never),
        "iso_only" => Ok(StringDatePolicy::IsoOnly),
        "aggressive" => Ok(StringDatePolicy::Aggressive),
        _ => Err(InferError::InvalidInput(
            "string_date_policy must be one of: never, iso_only, aggressive".to_string(),
        )),
    }
}

fn parse_numeric_promotion_policy(s: &str) -> Result<NumericPromotionPolicy, InferError> {
    match s {
        "promote" => Ok(NumericPromotionPolicy::Promote),
        "strict" => Ok(NumericPromotionPolicy::Strict),
        _ => Err(InferError::InvalidInput(
            "numeric_promotion must be one of: promote, strict".to_string(),
        )),
    }
}

fn parse_missing_key_policy(s: &str) -> Result<MissingKeyPolicy, InferError> {
    match s {
        "optional" => Ok(MissingKeyPolicy::Optional),
        _ => Err(InferError::InvalidInput(
            "missing_key_policy must be one of: optional".to_string(),
        )),
    }
}

fn parse_null_policy(s: &str) -> Result<NullPolicy, InferError> {
    match s {
        "nullable" => Ok(NullPolicy::Nullable),
        _ => Err(InferError::InvalidInput(
            "null_policy must be one of: nullable".to_string(),
        )),
    }
}
