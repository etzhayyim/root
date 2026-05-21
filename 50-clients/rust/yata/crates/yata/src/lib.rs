//! # `yata` — Rust client for [yatabase](https://yatabase.etzhayyim.com)
//!
//! See the workspace [README](https://github.com/etzhayyim/yata#readme)
//! for a quickstart.
//!
//! ## Public API tour
//!
//! ```ignore
//! use yata::prelude::*;
//!
//! #[derive(Vertex, Debug, Clone)]
//! #[yata(label = "person")]
//! struct Person {
//!     #[yata(pk)] id: String,
//!     name: String,
//!     age: i32,
//!     #[yata(vector(dim = 768))] embedding: Vec<f32>,
//! }
//!
//! let y = Yata::connect("yatabase://sk_live_yata_xxx@yatabase.etzhayyim.com/my-db").await?;
//! y.migrate::<(Person,)>().await?;
//! y.insert(Person { /* ... */ }).await?;
//!
//! let alice_friends: Vec<Person> = y
//!     .from::<Person>().eq("id", "alice")
//!     .limit(10)
//!     .fetch().await?;
//! ```

#![cfg_attr(docsrs, feature(doc_cfg))]
#![deny(missing_debug_implementations)]
#![warn(missing_docs)]

// ── Core re-exports ────────────────────────────────────────────────

pub use yata_core::{Yata, YataError, Result, Dsn, MigrateTuple};
pub use yata_schema::{
    Column, ColumnType, EdgeSpec, Row, RowValue, SchemaError, VertexSpec,
};

// ── Optional re-exports (feature-gated) ────────────────────────────

#[cfg(feature = "derive")]
pub use yata_derive::{Edge, Vertex};

#[cfg(feature = "query")]
pub use yata_query::{
    Direction, EdgeQuery, KnnClause, Predicate, QueryExt, QueryNode,
    ScalarValue, VertexQuery,
};

#[cfg(feature = "sparql")]
pub use yata_sparql::{SparqlExt, SparqlResult, SparqlRow};

#[cfg(feature = "stream")]
pub use yata_stream::{GenericMvEvent, MvRow, MvSubscription, MvSubscriptionExt};

#[cfg(feature = "mcp")]
pub use yata_mcp::{McpServer, ServeConfig};

// ── Prelude ────────────────────────────────────────────────────────

/// Glob-import-friendly module bringing in the canonical types and
/// extension traits.
///
/// ```ignore
/// use yata::prelude::*;
/// ```
pub mod prelude {
    pub use crate::{Yata, YataError, Result, VertexSpec, EdgeSpec};

    #[cfg(feature = "derive")]
    pub use crate::{Vertex, Edge};

    #[cfg(feature = "query")]
    pub use crate::QueryExt;

    #[cfg(feature = "sparql")]
    pub use crate::SparqlExt;

    #[cfg(feature = "stream")]
    pub use crate::MvSubscriptionExt;
}
