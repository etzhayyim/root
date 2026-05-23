//! Error type for the yata client.

use thiserror::Error;
use yata_schema::SchemaError;

/// Result alias used throughout the yata workspace.
pub type Result<T, E = YataError> = std::result::Result<T, E>;

/// All errors raised by the yata client.
#[derive(Debug, Error)]
#[non_exhaustive]
pub enum YataError {
    /// DSN parse failure.
    #[error("invalid yatabase DSN: {0}")]
    Dsn(String),

    /// Schema codec failure (`into_row` / `from_row`).
    #[error(transparent)]
    Schema(#[from] SchemaError),

    /// Underlying tokio-postgres error.
    #[error("postgres error: {0}")]
    Postgres(String),

    /// HTTP error wrapping `reqwest` (sparql / mcp HTTP transport).
    #[error("http error: {0}")]
    Http(String),

    /// Server returned an XRPC / SPARQL error envelope.
    #[error("server error ({status}): {message}")]
    Server {
        /// HTTP status code (or XRPC error class).
        status: u16,
        /// Server-supplied message.
        message: String,
    },

    /// JSON serialisation / deserialisation error.
    #[error("json codec error: {0}")]
    Json(#[from] serde_json::Error),

    /// IO error (TCP / TLS).
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    /// The requested feature is not yet implemented in this v0.1 skeleton.
    #[error("not yet implemented: {0}")]
    NotImplemented(&'static str),
}
