//! W Protocol error types.

use yata_core::Blake3Hash;

pub type Result<T> = std::result::Result<T, WProtoError>;

#[derive(Debug, thiserror::Error)]
pub enum WProtoError {
    #[error("MDAG: {0}")]
    Mdag(#[from] yata_mdag::MdagError),

    #[error("CAS: {0}")]
    Cas(String),

    #[error("CBOR encode/decode: {0}")]
    Cbor(String),

    #[error("Signal crypto: {0}")]
    Signal(String),

    #[error("AT Protocol: {0}")]
    At(String),

    #[error("channel not found: {0}")]
    ChannelNotFound(String),

    #[error("envelope not found: {0}")]
    EnvelopeNotFound(Blake3Hash),

    #[error("encryption mode mismatch: channel requires {expected}, got {actual}")]
    EncryptionMismatch { expected: String, actual: String },

    #[error("unauthorized: {0}")]
    Unauthorized(String),

    #[error("KV: {0}")]
    Kv(String),

    #[error("{0}")]
    Other(String),
}

impl From<yata_cas::CasError> for WProtoError {
    fn from(e: yata_cas::CasError) -> Self {
        Self::Cas(e.to_string())
    }
}
