//! W Protocol core types — WIT record equivalents in Rust.

use serde::{Deserialize, Serialize};
use yata_core::Blake3Hash;

/// Encryption state — host manages, app reads.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EncryptionState {
    /// Plaintext (no encryption)
    Plaintext,
    /// Signal 1:1 (X3DH + Double Ratchet)
    Signal1to1,
    /// Signal group (Sender Keys)
    SignalGroup,
    /// Client pre-encrypted (opaque ciphertext, host passes through)
    ClientEncrypted,
}

impl EncryptionState {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Plaintext => "plaintext",
            Self::Signal1to1 => "signal-1to1",
            Self::SignalGroup => "signal-group",
            Self::ClientEncrypted => "client-encrypted",
        }
    }
}

/// Channel kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ChannelKind {
    Public,
    Private,
    Direct,
    GroupDm,
    Bot,
    A2a,
}

impl ChannelKind {
    /// Default encryption mode for this channel kind.
    pub fn default_encryption(&self) -> EncryptionState {
        match self {
            Self::Public => EncryptionState::Plaintext,
            Self::Private => EncryptionState::Plaintext,
            Self::Direct => EncryptionState::Signal1to1,
            Self::GroupDm => EncryptionState::SignalGroup,
            Self::Bot => EncryptionState::Signal1to1,
            Self::A2a => EncryptionState::Signal1to1,
        }
    }
}

/// Member role in a channel.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MemberRole {
    Owner,
    Admin,
    Member,
}

/// Presence status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PresenceStatus {
    Online,
    Away,
    Dnd,
    Offline,
}

/// WEnvelope — the atomic unit of W Protocol.
/// Content-addressed via Blake3 (MDAG CAS).
/// Maps 1:1 to an AT Record.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WEnvelope {
    /// Envelope identity (ulid, idempotency key).
    pub id: String,
    /// Message kind → AT collection NSID: `ai.gftd.w.{kind}`.
    pub kind: String,

    /// MDAG content address (Blake3 hash of CBOR-encoded EnvelopeBlock).
    pub cid: Option<Blake3Hash>,

    /// AT Protocol binding (host-injected).
    pub at_uri: String,
    pub at_cid: String,
    pub rkey: String,

    /// Identity (host-injected from authn context).
    pub sender_did: String,
    pub org_id: String,

    /// Addressing.
    pub channel_id: String,
    pub thread_id: String,
    pub reply_to: String,

    /// Payload — plaintext (host encrypts if channel requires).
    pub payload: Vec<u8>,
    pub content_type: String,

    /// Encryption metadata (host-managed).
    pub encryption: EncryptionState,

    /// Causation chain (CQRS event sourcing).
    pub causation_id: String,
    pub correlation_id: String,

    /// Timestamp (ISO 8601).
    pub created_at: String,
}

/// W Channel.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WChannel {
    pub channel_id: String,
    pub org_id: String,
    pub name: String,
    pub description: String,
    pub kind: ChannelKind,
    pub encryption_mode: EncryptionState,
    pub creator_did: String,
    pub member_count: i32,
    pub at_uri: String,
    pub created_at: String,

    /// MDAG: current channel root CID (latest commit of this channel's envelope chain).
    pub mdag_root_cid: Option<Blake3Hash>,
}

/// W Member.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WMember {
    pub channel_id: String,
    pub did: String,
    pub role: MemberRole,
    pub joined_at: String,
}

/// W Presence.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WPresence {
    pub did: String,
    pub status: PresenceStatus,
    pub status_text: String,
    pub last_active: String,
}

/// Pagination cursor.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WPage {
    pub cursor: String,
    pub limit: i32,
}

/// PreKey bundle for Signal key exchange.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WPreKeyBundle {
    pub did: String,
    pub device_id: String,
    pub identity_key: Vec<u8>,
    pub signed_pre_key: Vec<u8>,
    pub signed_pre_key_sig: Vec<u8>,
    pub signed_pre_key_id: u32,
    pub one_time_pre_key: Option<Vec<u8>>,
    pub one_time_pre_key_id: u32,
}
