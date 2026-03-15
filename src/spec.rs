//! Core schema/spec types for inferred structure.
//!
//! Independent of Pydantic and Python typing; used for merge and serialization.

use indexmap::IndexMap;
use serde::Serialize;

/// Specification for a single field (name, type, required, nullable).
#[derive(Debug, Clone, Serialize)]
pub struct FieldSpec {
    pub name: String,
    #[serde(rename = "type")]
    pub spec: TypeSpec,
    pub required: bool,
    pub nullable: bool,
}

/// Inferred type specification.
#[derive(Debug, Clone, Serialize)]
#[serde(tag = "type", content = "item")]
pub enum TypeSpec {
    Any,
    Bool,
    Int,
    Float,
    String,
    Date,
    DateTime,
    Time,
    List(Box<TypeSpec>),
    Model(ModelSpec),
    Union(Vec<TypeSpec>),
}

/// Specification for a nested model (map of field name -> field spec).
#[derive(Debug, Clone, Default, Serialize)]
pub struct ModelSpec {
    pub fields: IndexMap<String, FieldSpec>,
}

impl ModelSpec {
    pub fn new() -> Self {
        Self {
            fields: IndexMap::new(),
        }
    }

    pub fn with_fields(fields: IndexMap<String, FieldSpec>) -> Self {
        Self { fields }
    }
}
