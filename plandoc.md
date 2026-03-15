Rust-Backed Pydantic Inference Package Plan

Overview

This package will infer a schema from Python list[dict] data using a Rust core, then convert that inferred schema into a Pydantic model on the Python side. The design goal is to combine:
	•	Rust performance for recursive type inference and schema merging
	•	Python ergonomics for Pydantic model creation
	•	Flexible, swappable inference behavior through configurable policies
	•	A conservative, predictable default inference strategy

The package should solve the problem of taking arbitrary nested dictionaries and turning them into a validated Pydantic model without hardcoding schema logic in application code.

Primary Goals
	•	Accept Python data shaped like list[dict[str, Any]]
	•	Infer field types across rows, including nested dictionaries and lists
	•	Track required vs optional fields separately from nullable vs non-nullable values
	•	Support configurable merge and conflict behavior
	•	Return either:
	•	a Python-friendly schema/spec representation
	•	a dynamically created Pydantic model
	•	Keep the expensive inference logic in Rust
	•	Keep final model emission in Python

Non-Goals for V1
	•	Full custom Python callback hooks inside the Rust inference loop
	•	Aggressive string-to-date or string-to-number guessing by default
	•	Perfect inference for every heterogeneous real-world dataset
	•	Replacing Pydantic internals
	•	Code generation as the primary output format

Core Product Concept

The package will expose two main Python APIs:

schema = infer_schema(data, config=...)
model = infer_model(data, model_name="Record", config=...)

The expected flow is:
	1.	Python passes list[dict] data into Rust
	2.	Rust walks the input and builds an internal schema/spec
	3.	Rust returns a Python-friendly schema structure
	4.	Python converts that structure into type annotations
	5.	Python uses pydantic.create_model(...) to build the final model

Key Design Principles

Conservative by Default

The package should prefer predictable results over over-aggressive guessing.

Examples:
	•	keep strings as strings by default
	•	use Any instead of giant unreadable unions in incompatible cases
	•	promote int + float -> float
	•	treat bool separately from int

Separate Presence from Nullability

Missing keys and explicit None values are different and must be tracked independently.
	•	missing key in some rows -> field is not required
	•	explicit None in observed values -> field is nullable

Separate Inference from Emission

The internal Rust schema representation should be independent of Python/Pydantic model creation.

Configurable Policies

Inference behavior should be controlled through built-in policy options that can later be expanded into named rule sets.

Input Scope

Supported Input in V1
	•	list[dict]
	•	nested dictionaries
	•	lists of primitives
	•	lists of dictionaries
	•	None
	•	primitive Python values such as bool, int, float, str
	•	optionally real Python date, datetime, and time objects

Deferred or Limited in V1
	•	tuples, sets, frozensets
	•	Decimal handling beyond a simple policy choice
	•	advanced union minimization
	•	arbitrary custom Python classes
	•	pandas / Polars direct ingestion

Inference Problems to Solve

Missing Keys

Track field presence count across rows.

Rule:
	•	present in every row -> required
	•	missing in any row -> optional/non-required

Nullability

Track whether a field is ever explicitly None.

Rule:
	•	saw None in any present row -> nullable

Mixed Scalar Types

Support a configurable merge strategy.

Default rules:
	•	int + int -> int
	•	float + float -> float
	•	int + float -> float
	•	bool stays separate from int
	•	incompatible scalar mixes -> Any

Nested Dictionaries

If all observed non-null values are dicts, recursively infer a nested model.

Lists

Infer one item type from all observed list elements.

Default rules:
	•	empty lists provide no evidence
	•	compatible element types unify normally
	•	incompatible list element types -> list[Any]
	•	list of dicts -> list[NestedModel]

Dates vs Strings

Default behavior should not parse strings as dates.

Rule:
	•	actual Python date / datetime objects can be recognized
	•	strings remain str unless an explicit parsing policy is enabled

High-Level Architecture

Rust Core

The Rust core owns:
	•	walking Python input values
	•	classifying values into internal types
	•	recursively merging observed types
	•	applying configurable policies
	•	producing a final schema/spec structure

Rust Responsibilities
	•	performance-critical traversal
	•	merge engine
	•	conflict resolution
	•	required/nullable tracking
	•	nested model inference
	•	list element inference
	•	final schema serialization into Python-friendly output

Python Layer

The Python layer owns:
	•	user-facing API
	•	config convenience wrappers
	•	converting schema/spec output into Python type annotations
	•	creating Pydantic models with pydantic.create_model(...)
	•	optional future code generation

Internal Schema Representation

The most important internal abstraction is the inferred schema/spec.

A likely Rust shape:

struct FieldSpec {
    name: String,
    spec: TypeSpec,
    required: bool,
    nullable: bool,
}

enum TypeSpec {
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

struct ModelSpec {
    fields: BTreeMap<String, FieldSpec>,
}

This representation should remain independent from Pydantic and Python typing objects.

Python-Friendly Returned Schema

Rust should return a serialized, Python-friendly structure such as a nested dict.

Example:

{
    "type": "model",
    "fields": {
        "id": {
            "type": "int",
            "required": True,
            "nullable": False,
        },
        "name": {
            "type": "str",
            "required": False,
            "nullable": True,
        },
    },
}

This simplifies model creation and also gives users introspection access.

Policy System

For V1, flexibility should come from built-in policy enums and config values rather than arbitrary Python callbacks.

Recommended Config Surface

InferConfig(
    incompatible_scalar_policy="any",
    heterogeneous_list_policy="any",
    dict_mixed_policy="any",
    string_date_policy="never",
    numeric_promotion="promote",
    missing_key_policy="optional",
    null_policy="nullable",
)

Candidate Policies

Incompatible Scalar Policy
	•	any
	•	union
	•	error

Heterogeneous List Policy
	•	any
	•	union
	•	error

Dict Mixed Policy
When a field is observed as both dict and non-dict:
	•	any
	•	union
	•	error

String Date Policy
	•	never
	•	iso_only
	•	aggressive

Numeric Promotion Policy
	•	promote
	•	strict

Future Rule Extensibility

After V1, the package can support higher-level rule bundles such as:
	•	strict
	•	pragmatic
	•	api_friendly
	•	data_lake

These named presets can map to sets of lower-level policies.

Python callback hooks should be considered only after the core policy system is stable.

API Design

Main Python Functions

infer_schema(data, config=None)
infer_model(data, model_name="InferredModel", config=None)

Nice-to-Have Convenience APIs

infer_types(data, config=None)
model_from_schema(schema, model_name="InferredModel")

User Experience Goals
	•	simple default path for most users
	•	introspectable schema output
	•	deterministic results
	•	easy nested model support

Rust Crate Layout

Suggested Rust module organization:
	•	lib.rs - PyO3 entry points
	•	config.rs - config structs and enums
	•	spec.rs - core schema/spec types
	•	classify.rs - Python value classification
	•	merge.rs - merge dispatcher and merge logic
	•	infer.rs - top-level inference orchestration
	•	serialize.rs - convert spec into Python-friendly dict output
	•	error.rs - package errors

Python Package Layout

Suggested Python package organization:
	•	__init__.py
	•	api.py - public functions
	•	config.py - Python config wrappers
	•	schema.py - schema dataclasses or helpers
	•	emit_pydantic.py - spec-to-Pydantic conversion
	•	typing_utils.py - Python annotation construction

Development Stack

Rust Side
	•	Rust
	•	PyO3
	•	maturin
	•	serde if useful for internal serialization
	•	std collections or indexmap depending on desired ordering behavior

Python Side
	•	Python 3.10+
	•	Pydantic v2
	•	pytest
	•	maturin develop for local iteration

Implementation Phases

Phase 1: Project Setup
	•	create Rust crate with PyO3 bindings
	•	create Python package wrapper
	•	set up maturin build workflow
	•	configure testing and packaging
	•	choose package name

Deliverable:
	•	package imports successfully in Python
	•	placeholder infer_schema callable works

Phase 2: Core Scalar Inference
	•	support None, bool, int, float, str
	•	implement presence counting
	•	implement nullable tracking
	•	implement scalar merge rules
	•	return serialized schema dict

Deliverable:
	•	infer flat models from basic list[dict]

Phase 3: Nested Dictionaries
	•	recursively infer dict fields
	•	support nested model specs
	•	serialize nested structures back to Python

Deliverable:
	•	nested dicts produce nested schema output

Phase 4: Lists
	•	support list detection
	•	infer list item type across rows
	•	support lists of dicts
	•	apply heterogeneous list policy

Deliverable:
	•	list[str], list[float], list[Any], and list[NestedModel]

Phase 5: Python Pydantic Emission
	•	convert schema dict into Python typing annotations
	•	build nested Pydantic models dynamically
	•	handle required and nullable correctly
	•	expose infer_model(...)

Deliverable:
	•	working end-to-end model creation

Phase 6: Configurable Policies
	•	expose config object in Python
	•	map config to Rust enums
	•	implement built-in policy variants
	•	test strict vs pragmatic behavior

Deliverable:
	•	same dataset can infer differently depending on config

Phase 7: Expanded Type Support

Potential additions:
	•	date
	•	datetime
	•	time
	•	Decimal
	•	tuples/sets as list-like or explicit unsupported errors

Deliverable:
	•	broader real-world compatibility

Testing Strategy

Rust Unit Tests

Test core inference logic independently of Python bindings.

Focus on:
	•	scalar merges
	•	missing key handling
	•	nullability handling
	•	nested model merging
	•	list item merging
	•	conflict policy behavior

Python Integration Tests

Test user-facing behavior from Python.

Focus on:
	•	infer_schema output shape
	•	infer_model return type
	•	nested model creation
	•	optional vs nullable semantics
	•	config mapping correctness

Regression Tests

Maintain a collection of real-world schema edge cases:
	•	sparse fields
	•	mixed numeric data
	•	heterogeneous lists
	•	dict/scalar conflicts
	•	empty lists
	•	empty nested dicts

Performance Considerations

Expected Speedups

Rust should improve performance by moving:
	•	recursive traversal logic
	•	merge logic
	•	repeated hash map operations
	•	nested type resolution

out of Python loops.

Realistic Limitation

Input still begins as Python objects, so some cost remains in crossing the Python/Rust boundary and inspecting Python values.

The main speed benefit comes from avoiding Python-level recursive inference logic, not from eliminating Python entirely.

Performance Benchmarks to Include

Compare against:
	•	a pure Python baseline implementation
	•	naive Pydantic-only approaches
	•	small, medium, and large nested datasets

Metrics:
	•	total inference time
	•	scaling by row count
	•	scaling by nesting depth
	•	scaling by field count

Documentation Plan

The package should include:
	•	README with quick start
	•	explanation of required vs nullable
	•	explanation of policy choices
	•	examples of nested models and lists
	•	performance notes and limitations
	•	API reference

Example Documentation Topics
	•	flat inference example
	•	nested dict example
	•	heterogeneous list behavior
	•	configuring strict vs pragmatic policies
	•	converting inferred schema to a Pydantic model

Risks and Tradeoffs

Risk: Too Much Flexibility Too Early

Trying to support arbitrary Python callbacks inside Rust too early would complicate the architecture and reduce performance.

Mitigation:
	•	start with built-in policy enums only

Risk: Over-Aggressive Inference

Users may dislike automatic guessing such as strings becoming dates.

Mitigation:
	•	conservative defaults
	•	opt-in parsing policies

Risk: Confusing Optional vs Nullable Semantics

This is a common source of bugs.

Mitigation:
	•	track presence and nullability independently throughout inference
	•	document behavior clearly

Risk: Python Binding Complexity

PyO3 interaction with deeply nested Python data can add complexity.

Mitigation:
	•	keep Rust/Python boundary clean
	•	return Python-friendly dict schemas rather than complicated Rust object graphs

Recommended V1 Success Criteria

V1 is successful if it can reliably:
	•	infer flat and nested list[dict] datasets
	•	distinguish required vs nullable
	•	support list element inference
	•	expose configurable policies
	•	create usable nested Pydantic models dynamically
	•	outperform a pure Python inference implementation on medium and large datasets

Suggested Immediate Next Steps
	1.	Choose the package name
	2.	Scaffold the Rust crate and Python wrapper with maturin
	3.	Define the Rust TypeSpec, FieldSpec, and InferConfig types
	4.	Implement flat scalar inference first
	5.	Return schema as a Python dict before attempting Pydantic model generation
	6.	Add nested dict support
	7.	Add list support
	8.	Add the Python emission layer for Pydantic

Candidate Package Positioning

This package can be positioned as:
	•	a Rust-backed schema inference engine for Python dictionaries
	•	a fast path from semi-structured Python data to Pydantic models
	•	a configurable inference tool for API prototypes, ETL validation, and schema discovery

Summary

The best version of this package is not a Rust reimplementation of Pydantic. It is a hybrid system:
	•	Rust handles fast, configurable schema inference
	•	Python handles final Pydantic model construction

That architecture preserves performance, extensibility, and Python usability while keeping the implementation realistic and maintainable.