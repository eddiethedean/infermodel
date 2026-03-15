//! Convert internal spec into Python-friendly dict output.

use crate::spec::{ModelSpec, TypeSpec};
use serde_json::{Map, Value};

/// Serialize [TypeSpec] to JSON-like value: string for scalar, object for list/model/union.
fn type_spec_to_value(spec: &TypeSpec) -> Value {
    match spec {
        TypeSpec::Any => Value::String("any".to_string()),
        TypeSpec::Bool => Value::String("bool".to_string()),
        TypeSpec::Int => Value::String("int".to_string()),
        TypeSpec::Float => Value::String("float".to_string()),
        TypeSpec::String => Value::String("str".to_string()),
        TypeSpec::Date => Value::String("date".to_string()),
        TypeSpec::DateTime => Value::String("datetime".to_string()),
        TypeSpec::Time => Value::String("time".to_string()),
        TypeSpec::List(item) => {
            let mut m = Map::new();
            m.insert("type".to_string(), Value::String("list".to_string()));
            m.insert("item".to_string(), type_spec_to_value(item));
            Value::Object(m)
        }
        TypeSpec::Model(model) => {
            let mut m = Map::new();
            m.insert("type".to_string(), Value::String("model".to_string()));
            m.insert("fields".to_string(), model_spec_to_value(model));
            Value::Object(m)
        }
        TypeSpec::Union(variants) => {
            let mut m = Map::new();
            m.insert("type".to_string(), Value::String("union".to_string()));
            m.insert(
                "variants".to_string(),
                Value::Array(variants.iter().map(type_spec_to_value).collect()),
            );
            Value::Object(m)
        }
    }
}

/// Serialize [ModelSpec] to a dict of field name -> { type, required, nullable }.
fn model_spec_to_value(model: &ModelSpec) -> Value {
    let fields: Map<String, Value> = model
        .fields
        .iter()
        .map(|(name, f)| {
            let mut m = Map::new();
            m.insert("type".to_string(), type_spec_to_value(&f.spec));
            m.insert("required".to_string(), Value::Bool(f.required));
            m.insert("nullable".to_string(), Value::Bool(f.nullable));
            (name.clone(), Value::Object(m))
        })
        .collect();
    Value::Object(fields)
}

/// Top-level schema: always a model. Returns a dict suitable for Python.
pub fn schema_to_python_dict(model: &ModelSpec) -> Value {
    let mut top = Map::new();
    top.insert("type".to_string(), Value::String("model".to_string()));
    top.insert("fields".to_string(), model_spec_to_value(model));
    Value::Object(top)
}
