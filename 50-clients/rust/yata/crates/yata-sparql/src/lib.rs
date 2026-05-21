//! `yata-sparql` — SPARQL 1.1 HTTP client.
//!
//! Forwards `SELECT` / `CONSTRUCT` / `ASK` queries to
//! `https://yatabase.etzhayyim.com/sparql` over plain HTTPS POST.  v0.1
//! supports the JSON response format only; XML / TSV are deferred to
//! v0.2.
//!
//! ```ignore
//! use yata::prelude::*;
//! use yata_sparql::SparqlExt;
//!
//! let rows = y.sparql("SELECT ?p WHERE { ?p :knows :alice }").await?;
//! for row in rows {
//!     println!("{:?}", row);
//! }
//! ```

#![cfg_attr(docsrs, feature(doc_cfg))]
#![deny(missing_debug_implementations)]
#![warn(missing_docs)]

use async_trait::async_trait;
use serde::Deserialize;
use yata_core::{Yata, YataError, Result};

/// One row of a SPARQL SELECT result, encoded as `{ var → value }`.
pub type SparqlRow = std::collections::BTreeMap<String, String>;

/// Result envelope returned by the `/sparql` endpoint.
#[derive(Debug, Clone, Deserialize)]
pub struct SparqlResult {
    /// `true` when the server processed the query.
    pub ok: bool,
    /// Number of rows returned.
    #[serde(rename = "rowCount", default)]
    pub row_count: u64,
    /// JSON-encoded array of rows (caller may parse further).
    pub rows: Option<String>,
    /// Translated SQL/PGQ (debug aid).
    #[serde(rename = "translatedSql", default)]
    pub translated_sql: String,
    /// Wall-clock duration in milliseconds.
    #[serde(rename = "elapsedMs", default)]
    pub elapsed_ms: u64,
    /// Server-side error message, if any.
    pub error: Option<String>,
}

/// Extension trait imported via `use yata::prelude::*`.
#[async_trait]
pub trait SparqlExt {
    /// Run a SPARQL 1.1 query and return the result envelope.
    async fn sparql(&self, query: &str) -> Result<SparqlResult>;
}

#[async_trait]
impl SparqlExt for Yata {
    async fn sparql(&self, _query: &str) -> Result<SparqlResult> {
        Err(YataError::NotImplemented(
            "SparqlExt::sparql is a v0.1 skeleton; HTTP transport lives in 0.2",
        ))
    }
}
