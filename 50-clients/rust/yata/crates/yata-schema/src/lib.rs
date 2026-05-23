//! `yata-schema` — schema traits for vertex / edge types.
//!
//! Application code rarely interacts with this crate directly; the
//! [`Vertex`][derive-vertex] / [`Edge`][derive-edge] proc-macros from
//! `yata-derive` emit `impl VertexSpec for T` and `impl EdgeSpec for T`
//! using these traits.
//!
//! [derive-vertex]: https://docs.rs/yata-derive/latest/yata_derive/derive.Vertex.html
//! [derive-edge]:   https://docs.rs/yata-derive/latest/yata_derive/derive.Edge.html
//!
//! ## Example (what `#[derive(Vertex)]` expands to, conceptually)
//!
//! ```ignore
//! impl yata_schema::VertexSpec for Person {
//!     const LABEL: &'static str = "person";
//!     const COLUMNS: &'static [yata_schema::Column] = &[
//!         yata_schema::Column { name: "id",        ty: yata_schema::ColumnType::Varchar, is_pk: true,  is_vector: false, vector_dim: 0 },
//!         yata_schema::Column { name: "name",      ty: yata_schema::ColumnType::Varchar, is_pk: false, is_vector: false, vector_dim: 0 },
//!         yata_schema::Column { name: "age",       ty: yata_schema::ColumnType::Int,     is_pk: false, is_vector: false, vector_dim: 0 },
//!         yata_schema::Column { name: "embedding", ty: yata_schema::ColumnType::RealArray, is_pk: false, is_vector: true, vector_dim: 768 },
//!     ];
//!     fn pk(&self) -> String { self.id.clone() }
//!     fn into_row(self) -> yata_schema::Row { /* serde-encoded map */ todo!() }
//!     fn from_row(row: yata_schema::Row) -> Result<Self, yata_schema::SchemaError> { todo!() }
//! }
//! ```

#![cfg_attr(docsrs, feature(doc_cfg))]
#![deny(missing_debug_implementations)]
#![warn(missing_docs)]

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Column metadata emitted by `#[derive(Vertex)]` / `#[derive(Edge)]`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Column {
    /// Column name in the underlying RisingWave table.
    pub name: &'static str,
    /// SQL-side type as known by the yata client.
    pub ty: ColumnType,
    /// `true` if this column is the (single) primary key for the type.
    pub is_pk: bool,
    /// `true` if this is a `REAL[]` vector column (yata-pgvector hybrid).
    pub is_vector: bool,
    /// Dimensionality when `is_vector == true`. Ignored otherwise.
    pub vector_dim: usize,
}

/// SQL-side type known by the yata client. Maps to RisingWave column types.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum ColumnType {
    /// `VARCHAR` (string).
    Varchar,
    /// `INTEGER`.
    Int,
    /// `BIGINT`.
    BigInt,
    /// `DOUBLE PRECISION`.
    Double,
    /// `BOOLEAN`.
    Boolean,
    /// `DATE`.
    Date,
    /// `TIMESTAMP WITH TIME ZONE`.
    Timestamptz,
    /// `REAL[]` for vector embeddings.
    RealArray,
    /// `VARCHAR` carrying serialised JSON. RisingWave does not have JSONB
    /// promoted columns; the client serialises with `serde_json` on
    /// write and deserialises on read.
    JsonAsVarchar,
}

/// A row encoded as a string-keyed bag. Concrete encoding (TEXT vs binary
/// PG protocol) lives in `yata-core`; this crate is wire-agnostic.
pub type Row = BTreeMap<String, RowValue>;

/// One value within a [`Row`]. Mirrors [`ColumnType`] variants at runtime.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum RowValue {
    /// `VARCHAR`.
    Text(String),
    /// `INTEGER`.
    Int(i32),
    /// `BIGINT`.
    BigInt(i64),
    /// `DOUBLE PRECISION`.
    Double(f64),
    /// `BOOLEAN`.
    Bool(bool),
    /// `REAL[]`.
    RealArray(Vec<f32>),
    /// `NULL`.
    Null,
}

/// Errors raised by `into_row` / `from_row`.
#[derive(Debug, Error)]
pub enum SchemaError {
    /// A required column was missing from the row.
    #[error("column `{0}` is required but missing from row")]
    MissingColumn(String),
    /// A column was present but had the wrong runtime type.
    #[error("column `{column}` has wrong type: expected {expected}, got {actual}")]
    WrongType {
        /// Column name.
        column: String,
        /// Type expected by the trait impl.
        expected: &'static str,
        /// Runtime type actually seen on the wire.
        actual: &'static str,
    },
    /// Vector dimensionality mismatch.
    #[error("vector column `{column}` expected dim {expected}, got {actual}")]
    VectorDim {
        /// Column name.
        column: String,
        /// Dimension declared by the type.
        expected: usize,
        /// Dimension found at runtime.
        actual: usize,
    },
    /// JSON encoding / decoding error wrapping `serde_json`.
    #[error("json codec error: {0}")]
    Json(#[from] serde_json::Error),
}

/// Trait implemented by the `#[derive(Vertex)]` proc-macro.
///
/// Every vertex type carries its label, its column metadata, and the
/// codec functions needed for INSERT / SELECT.
pub trait VertexSpec: Sized + Send + Sync + 'static {
    /// Vertex label as used in `vertex_<label>` table naming.
    const LABEL: &'static str;
    /// Schema namespace (defaults to `"public"` when unset on the derive).
    const SCHEMA: &'static str = "public";
    /// All columns including the primary key, in declaration order.
    const COLUMNS: &'static [Column];

    /// Extract the primary-key value as a string. Used as the AT URI
    /// `rkey` and as the row identifier on INSERT.
    fn pk(&self) -> String;
    /// Encode `self` into a [`Row`] for INSERT.
    fn into_row(self) -> Result<Row, SchemaError>;
    /// Decode a [`Row`] returned by SELECT into `Self`.
    fn from_row(row: Row) -> Result<Self, SchemaError>;
}

/// Trait implemented by the `#[derive(Edge)]` proc-macro.
///
/// Edges always carry `src_vid` + `dst_vid` along with relation
/// properties.
pub trait EdgeSpec: Sized + Send + Sync + 'static {
    /// Edge type as used in `edge_<type>` table naming.
    const EDGE_TYPE: &'static str;
    /// Schema namespace (defaults to `"public"`).
    const SCHEMA: &'static str = "public";
    /// All columns. Implementors must include `src_vid` and `dst_vid`.
    const COLUMNS: &'static [Column];

    /// Extract the primary-key value as a string.
    fn pk(&self) -> String;
    /// Encode `self` into a [`Row`] for INSERT.
    fn into_row(self) -> Result<Row, SchemaError>;
    /// Decode a [`Row`] returned by SELECT into `Self`.
    fn from_row(row: Row) -> Result<Self, SchemaError>;
}

/// Compile-time helper: reject column lists that do not contain exactly
/// one PK. Called by the derive proc-macro at generated-code level.
pub const fn check_single_pk(cols: &'static [Column]) {
    let mut count = 0;
    let mut i = 0;
    while i < cols.len() {
        if cols[i].is_pk {
            count += 1;
        }
        i += 1;
    }
    if count != 1 {
        panic!("yata-schema: every Vertex / Edge must declare exactly one #[yata(pk)] column");
    }
}
