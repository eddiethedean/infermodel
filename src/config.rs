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
        }
    }
}
