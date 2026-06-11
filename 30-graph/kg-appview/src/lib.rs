//! kg-appview — ephemeral in-memory SPARQL AppView for the etzhayyim KG.
//!
//! Stage K2.a of ADR-2605190900. See `README.md` for the IRI mapping
//! and architecture.

pub mod firehose;
pub mod iri;
pub mod load;
pub mod replay;
pub mod server;
pub mod store;
