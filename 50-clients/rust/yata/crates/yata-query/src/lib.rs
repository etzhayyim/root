//! `yata-query` — type-safe SQL/PGQ query builder.
//!
//! Application code uses the fluent builder via the [`Yata`] handle:
//!
//! ```ignore
//! let friends: Vec<Person> = y
//!     .from::<Person>().eq("id", "alice")
//!     .out::<Knows>()
//!     .to::<Person>()
//!     .limit(10)
//!     .fetch().await?;
//!
//! // Hybrid graph + vector
//! let similar: Vec<Person> = y
//!     .from::<Person>()
//!     .knn(&query_vec, 10)
//!     .out::<Knows>()
//!     .fetch().await?;
//! ```
//!
//! v0.1 implements the AST + a `to_sql()` debug emitter; actual
//! execution against tokio-postgres is wired in v0.2 alongside the
//! real `Yata::insert` / `Yata::execute`.

#![cfg_attr(docsrs, feature(doc_cfg))]
#![deny(missing_debug_implementations)]
#![warn(missing_docs)]

use std::marker::PhantomData;

use yata_core::{Yata, YataError, Result};
use yata_schema::{EdgeSpec, VertexSpec};

/// Direction for an `out::<E>()` / `in_::<E>()` traversal.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    /// Outgoing edge (`src_vid` matches the current vertex).
    Out,
    /// Incoming edge (`dst_vid` matches the current vertex).
    In,
    /// Both directions.
    Both,
}

/// Comparison predicate placed on a column.
#[derive(Debug, Clone)]
pub enum Predicate {
    /// `column = value`
    Eq(String, ScalarValue),
    /// `column LIKE value%`
    StartsWith(String, String),
    /// `column IN (values...)`
    In(String, Vec<ScalarValue>),
    /// `column IS NOT NULL`
    NotNull(String),
}

/// A scalar parameter value attached to a predicate.
#[derive(Debug, Clone)]
pub enum ScalarValue {
    /// Text.
    Text(String),
    /// 32-bit signed integer.
    Int(i32),
    /// 64-bit signed integer.
    BigInt(i64),
    /// Double precision float.
    Double(f64),
    /// Boolean.
    Bool(bool),
}

impl<'a> From<&'a str> for ScalarValue {
    fn from(v: &'a str) -> Self { ScalarValue::Text(v.to_string()) }
}
impl From<String> for ScalarValue {
    fn from(v: String) -> Self { ScalarValue::Text(v) }
}
impl From<i32> for ScalarValue {
    fn from(v: i32) -> Self { ScalarValue::Int(v) }
}
impl From<i64> for ScalarValue {
    fn from(v: i64) -> Self { ScalarValue::BigInt(v) }
}
impl From<f64> for ScalarValue {
    fn from(v: f64) -> Self { ScalarValue::Double(v) }
}
impl From<bool> for ScalarValue {
    fn from(v: bool) -> Self { ScalarValue::Bool(v) }
}

/// Optional KNN clause attached to a vertex query.
#[derive(Debug, Clone)]
pub struct KnnClause {
    /// Column to use for vector similarity.
    pub column: String,
    /// Query embedding.
    pub vector: Vec<f32>,
    /// Top-K to return.
    pub k: usize,
}

/// Internal AST node — used to build the query and then emit SQL/PGQ.
#[derive(Debug, Clone)]
pub struct QueryNode {
    /// Vertex/edge label.
    pub label: String,
    /// Predicates accumulated by `eq` / `starts_with` / etc.
    pub predicates: Vec<Predicate>,
    /// KNN clause if `knn(&vec, k)` was called on this node.
    pub knn: Option<KnnClause>,
    /// Direction if this node represents an edge traversal.
    pub direction: Option<Direction>,
}

// ──────────────────────────────────────────────────────────────────────
// VertexQuery — entry point produced by `Yata::from::<V>()`
// ──────────────────────────────────────────────────────────────────────

/// Vertex query stage. Produced by `Yata::from::<V>()`.
#[derive(Debug)]
pub struct VertexQuery<V: VertexSpec> {
    yata: Yata,
    nodes: Vec<QueryNode>,
    limit: Option<usize>,
    _v: PhantomData<V>,
}

impl<V: VertexSpec> VertexQuery<V> {
    /// Add an `=` predicate.
    pub fn eq(mut self, column: &str, value: impl Into<ScalarValue>) -> Self {
        let last = self.nodes.last_mut().expect("at least one node");
        last.predicates.push(Predicate::Eq(column.to_string(), value.into()));
        self
    }

    /// Add a `STARTS WITH` predicate.
    pub fn starts_with(mut self, column: &str, prefix: impl Into<String>) -> Self {
        let last = self.nodes.last_mut().expect("at least one node");
        last.predicates.push(Predicate::StartsWith(column.to_string(), prefix.into()));
        self
    }

    /// Add an `IN (...)` predicate.
    pub fn r#in(mut self, column: &str, values: Vec<ScalarValue>) -> Self {
        let last = self.nodes.last_mut().expect("at least one node");
        last.predicates.push(Predicate::In(column.to_string(), values));
        self
    }

    /// Add an `IS NOT NULL` predicate.
    pub fn not_null(mut self, column: &str) -> Self {
        let last = self.nodes.last_mut().expect("at least one node");
        last.predicates.push(Predicate::NotNull(column.to_string()));
        self
    }

    /// KNN: nearest-neighbour search on the first `vector` column of `V`.
    /// `column` defaults to the conventional `embedding` field; future
    /// versions will resolve from `V::COLUMNS` automatically.
    pub fn knn(mut self, vector: &[f32], k: usize) -> Self {
        let column = V::COLUMNS
            .iter()
            .find(|c| c.is_vector)
            .map(|c| c.name.to_string())
            .unwrap_or_else(|| "embedding".to_string());
        let last = self.nodes.last_mut().expect("at least one node");
        last.knn = Some(KnnClause { column, vector: vector.to_vec(), k });
        self
    }

    /// Traverse along an outgoing edge.
    pub fn out<E: EdgeSpec>(self) -> EdgeQuery<E> {
        EdgeQuery::wrap(self, Direction::Out)
    }

    /// Traverse along an incoming edge.
    pub fn in_<E: EdgeSpec>(self) -> EdgeQuery<E> {
        EdgeQuery::wrap(self, Direction::In)
    }

    /// Apply a `LIMIT n` clause.
    pub fn limit(mut self, n: usize) -> Self {
        self.limit = Some(n);
        self
    }

    /// Render the AST to a debug SQL/PGQ string. Useful for tests.
    pub fn to_sql(&self) -> String {
        render_sql(&self.nodes, self.limit)
    }

    /// Execute the query and return the resulting rows decoded into `V`.
    /// v0.1 returns `NotImplemented`; the wire path is in v0.2.
    pub async fn fetch(self) -> Result<Vec<V>> {
        let _ = self.yata; // suppress unused warning
        Err(YataError::NotImplemented(
            "VertexQuery::fetch is a v0.1 skeleton; tokio-postgres path lives in 0.2",
        ))
    }
}

// ──────────────────────────────────────────────────────────────────────
// EdgeQuery — produced by `.out::<E>()` / `.in_::<E>()`
// ──────────────────────────────────────────────────────────────────────

/// Edge traversal stage.
#[derive(Debug)]
pub struct EdgeQuery<E: EdgeSpec> {
    yata: Yata,
    nodes: Vec<QueryNode>,
    limit: Option<usize>,
    _e: PhantomData<E>,
}

impl<E: EdgeSpec> EdgeQuery<E> {
    fn wrap<V: VertexSpec>(prev: VertexQuery<V>, dir: Direction) -> Self {
        let mut nodes = prev.nodes;
        nodes.push(QueryNode {
            label: E::EDGE_TYPE.to_string(),
            predicates: vec![],
            knn: None,
            direction: Some(dir),
        });
        Self { yata: prev.yata, nodes, limit: prev.limit, _e: PhantomData }
    }

    /// Filter the edge by an `=` predicate.
    pub fn eq(mut self, column: &str, value: impl Into<ScalarValue>) -> Self {
        let last = self.nodes.last_mut().expect("at least one node");
        last.predicates.push(Predicate::Eq(column.to_string(), value.into()));
        self
    }

    /// Continue to the destination vertex.
    pub fn to<V2: VertexSpec>(self) -> VertexQuery<V2> {
        let mut nodes = self.nodes;
        nodes.push(QueryNode {
            label: V2::LABEL.to_string(),
            predicates: vec![],
            knn: None,
            direction: None,
        });
        VertexQuery { yata: self.yata, nodes, limit: self.limit, _v: PhantomData }
    }

    /// Apply a `LIMIT` clause to the eventual fetch.
    pub fn limit(mut self, n: usize) -> Self {
        self.limit = Some(n);
        self
    }

    /// Render the AST to a debug SQL/PGQ string.
    pub fn to_sql(&self) -> String {
        render_sql(&self.nodes, self.limit)
    }
}

// ──────────────────────────────────────────────────────────────────────
// Yata extension — the entry point glued onto the public handle.
// ──────────────────────────────────────────────────────────────────────

/// Extension trait implemented on `Yata` to expose `from::<V>()`. Imported
/// via `use yata::prelude::*`.
pub trait QueryExt {
    /// Start a vertex query against `V`.
    fn from<V: VertexSpec>(&self) -> VertexQuery<V>;
}

impl QueryExt for Yata {
    fn from<V: VertexSpec>(&self) -> VertexQuery<V> {
        VertexQuery {
            yata: self.clone(),
            nodes: vec![QueryNode {
                label: V::LABEL.to_string(),
                predicates: vec![],
                knn: None,
                direction: None,
            }],
            limit: None,
            _v: PhantomData,
        }
    }
}

// ──────────────────────────────────────────────────────────────────────
// Debug SQL renderer — used for tests + v0.1 sanity check.
// ──────────────────────────────────────────────────────────────────────

fn render_sql(nodes: &[QueryNode], limit: Option<usize>) -> String {
    let mut out = String::new();
    for (i, n) in nodes.iter().enumerate() {
        if i > 0 {
            out.push_str(match n.direction {
                Some(Direction::Out)  => " --[out]--> ",
                Some(Direction::In)   => " <--[in]-- ",
                Some(Direction::Both) => " <--[both]--> ",
                None                  => " . ",
            });
        }
        out.push('(');
        out.push_str(&n.label);
        if !n.predicates.is_empty() {
            out.push_str(" {");
            for (pi, p) in n.predicates.iter().enumerate() {
                if pi > 0 { out.push_str(", "); }
                match p {
                    Predicate::Eq(c, v)         => out.push_str(&format!("{c} = {v:?}")),
                    Predicate::StartsWith(c, v) => out.push_str(&format!("{c} STARTS WITH {v:?}")),
                    Predicate::In(c, vs)        => out.push_str(&format!("{c} IN {vs:?}")),
                    Predicate::NotNull(c)       => out.push_str(&format!("{c} IS NOT NULL")),
                }
            }
            out.push('}');
        }
        if let Some(knn) = &n.knn {
            out.push_str(&format!(" KNN({}, k={})", knn.column, knn.k));
        }
        out.push(')');
    }
    if let Some(l) = limit {
        out.push_str(&format!(" LIMIT {l}"));
    }
    out
}
