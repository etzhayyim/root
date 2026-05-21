//! `yata-core` — connection / [`Yata`] struct / [`YataError`] for the
//! Rust client.
//!
//! Application code does not import this crate directly; use the
//! [`yata`](https://docs.rs/yata) facade.
//!
//! ## DSN format
//!
//! ```text
//! yatabase://<sk_live_yata_*>@<host>[:<port>]/<database>[?<param>=<value>&...]
//! ```
//!
//! - `sk_live_yata_*` is the same Bearer token used by the
//!   `yatabase.etzhayyim.com` HTTP surfaces (P3.1).  The client passes it
//!   over PG protocol as the password and the server resolves the
//!   `org_did` + `product_scope` via `vertex_api_key` (P2 / P3.2).
//! - `host` defaults to `yatabase.etzhayyim.com`.
//! - `port` defaults to `5432`.
//! - `database` is `yata_<sha256(orgDid)[:16]>` provisioned via
//!   `ai.gftd.apps.yata.provisionDatabase` (P3 BPMN).
//! - Common params: `sslmode=require` (default), `application_name=...`.

#![cfg_attr(docsrs, feature(doc_cfg))]
#![deny(missing_debug_implementations)]
#![warn(missing_docs)]

pub mod connect;
pub mod error;

pub use error::{YataError, Result};
pub use connect::Dsn;

use std::sync::Arc;
use tokio::sync::RwLock;

use yata_schema::VertexSpec;

/// The yatabase client handle.
///
/// `Yata` is `Clone` and `Send + Sync`; cloning shares the underlying
/// connection pool. Drop the last clone to close the pool.
#[derive(Debug, Clone)]
pub struct Yata {
    inner: Arc<YataInner>,
}

#[derive(Debug)]
struct YataInner {
    dsn: Dsn,
    /// `tokio-postgres` connection pool. v0.1 keeps a single connection;
    /// v0.2 will swap for `deadpool-postgres` or similar.
    #[allow(dead_code)]
    conn: RwLock<Option<()>>,
}

impl Yata {
    /// Connect to a yatabase instance and return a client handle.
    ///
    /// ```ignore
    /// let y = yata::Yata::connect("yatabase://sk_live_yata_xxx@yatabase.etzhayyim.com/my-db").await?;
    /// ```
    pub async fn connect(dsn: impl AsRef<str>) -> Result<Self> {
        let parsed = Dsn::parse(dsn.as_ref())?;
        // v0.1 skeleton — actual tokio-postgres connect is wired in 0.2.
        // Returning a handle now lets downstream sub-crates (yata-query,
        // yata-sparql, yata-stream) import-and-test their public API
        // surface without a live yatabase instance.
        Ok(Self {
            inner: Arc::new(YataInner {
                dsn: parsed,
                conn: RwLock::new(None),
            }),
        })
    }

    /// Apply schema for the given vertex / edge tuple. Idempotent
    /// (`CREATE TABLE IF NOT EXISTS`).
    ///
    /// ```ignore
    /// y.migrate::<(Person, Knows)>().await?;
    /// ```
    pub async fn migrate<T: MigrateTuple>(&self) -> Result<()> {
        let _stmts = T::ddl();
        // v0.2 will execute these statements via tokio-postgres.
        Err(YataError::NotImplemented(
            "Yata::migrate is a v0.1 skeleton; DDL emission lives in 0.2",
        ))
    }

    /// Insert a single vertex.
    pub async fn insert<V: VertexSpec>(&self, _v: V) -> Result<()> {
        Err(YataError::NotImplemented(
            "Yata::insert is a v0.1 skeleton; INSERT emission lives in 0.2",
        ))
    }

    /// The DSN this client was created with. Useful for error
    /// reporting + tests.
    pub fn dsn(&self) -> &Dsn {
        &self.inner.dsn
    }
}

/// Trait implemented for tuples of vertex / edge types so that
/// `y.migrate::<(Person, Knows)>()` can take a heterogeneous list.
pub trait MigrateTuple {
    /// Emit the CREATE TABLE statements (one per element).
    fn ddl() -> Vec<String>;
}

impl<V1: VertexSpec> MigrateTuple for (V1,) {
    fn ddl() -> Vec<String> {
        vec![ddl_for::<V1>()]
    }
}

impl<V1: VertexSpec, V2: VertexSpec> MigrateTuple for (V1, V2) {
    fn ddl() -> Vec<String> {
        vec![ddl_for::<V1>(), ddl_for::<V2>()]
    }
}

impl<V1: VertexSpec, V2: VertexSpec, V3: VertexSpec> MigrateTuple for (V1, V2, V3) {
    fn ddl() -> Vec<String> {
        vec![ddl_for::<V1>(), ddl_for::<V2>(), ddl_for::<V3>()]
    }
}

/// Generate a `CREATE TABLE IF NOT EXISTS vertex_<label>` statement
/// from a `VertexSpec`. v0.1 emits a placeholder string; v0.2 emits real
/// PG DDL.
fn ddl_for<V: VertexSpec>() -> String {
    format!(
        "CREATE TABLE IF NOT EXISTS {schema}.vertex_{label} (/* {n} cols */)",
        schema = V::SCHEMA,
        label = V::LABEL,
        n = V::COLUMNS.len(),
    )
}
