//! Config structs and policy enums for inference behavior.

/// Policy when scalar types are incompatible (e.g. int + str).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[repr(u8)]
pub enum IncompatibleScalarPolicy {
    #[default]
    Any,
    Union,
    Error,
}

/// Policy when list elements have heterogeneous types.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[repr(u8)]
pub enum HeterogeneousListPolicy {
    #[default]
    Any,
    Union,
    Error,
}

/// Policy when a field is observed as both dict and non-dict.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[repr(u8)]
pub enum DictMixedPolicy {
    #[default]
    Any,
    Union,
    Error,
}

/// Policy for string-to-date parsing.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[repr(u8)]
pub enum StringDatePolicy {
    #[default]
    Never,
    IsoOnly,
    Aggressive,
}

/// Policy for int + float promotion.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[repr(u8)]
pub enum NumericPromotionPolicy {
    #[default]
    Promote,
    Strict,
}

/// Policy for missing keys across rows.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[repr(u8)]
pub enum MissingKeyPolicy {
    #[default]
    Optional,
}

/// Policy for explicit None values.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[repr(u8)]
pub enum NullPolicy {
    #[default]
    Nullable,
}

/// Inference configuration (V1: built-in policies only).
#[derive(Debug, Clone)]
pub struct InferConfig {
    pub incompatible_scalar_policy: IncompatibleScalarPolicy,
    pub heterogeneous_list_policy: HeterogeneousListPolicy,
    pub dict_mixed_policy: DictMixedPolicy,
    pub string_date_policy: StringDatePolicy,
    pub numeric_promotion: NumericPromotionPolicy,
    pub missing_key_policy: MissingKeyPolicy,
    pub null_policy: NullPolicy,
    /// When true (default), infer int/float from string content (e.g. "42", "3.14").
    pub infer_string_numbers: bool,
    /// When true, infer null and bool from string content ("null"/"true"/"false"/"yes"/"no"). Default false.
    pub infer_string_literals: bool,
    /// Max number of items to sample for inference (default 10_000). 0 = no limit.
    pub sample_size: usize,
}

impl Default for InferConfig {
    fn default() -> Self {
        Self {
            incompatible_scalar_policy: IncompatibleScalarPolicy::Any,
            heterogeneous_list_policy: HeterogeneousListPolicy::Any,
            dict_mixed_policy: DictMixedPolicy::Any,
            string_date_policy: StringDatePolicy::Never,
            numeric_promotion: NumericPromotionPolicy::Promote,
            missing_key_policy: MissingKeyPolicy::Optional,
            null_policy: NullPolicy::Nullable,
            infer_string_numbers: true,
            infer_string_literals: false,
            sample_size: 10_000,
        }
    }
}
