//! Signal Protocol re-exports from yata-signal.
//!
//! Consumers use `wproto::signal::*` instead of depending on yata-signal directly.

pub use yata_signal::*;
pub use yata_signal::host_api;
pub use yata_signal::store::SignalStorage;
