//! Thin wrapper around `oxigraph::store::Store`. K2.a uses the default
//! ephemeral in-memory backend; the wrapper exists so K2.b/K2.c can layer
//! additional invariants (write rejection, snapshot accounting) without
//! threading the raw Store through the codebase.

use anyhow::Result;
use oxigraph::store::Store;

pub struct AppStore {
    pub store: Store,
}

impl AppStore {
    pub fn new() -> Result<Self> {
        Ok(Self {
            store: Store::new()?,
        })
    }
}
