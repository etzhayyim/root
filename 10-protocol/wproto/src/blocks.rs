//! W Protocol MDAG blocks — CBOR-serializable content-addressed blocks.
//!
//! Extends yata-mdag's graph block model with W Protocol envelope blocks.
//! Every WEnvelope becomes a content-addressed CBOR block in CAS.
//!
//! Block hierarchy:
//! ```text
//! WRootBlock (channel state root, one per commit)
//!   ├─ ChannelRootBlock (channel metadata)
//!   ├─ EnvelopeGroupBlock (envelopes grouped by kind)
//!   │   └─ EnvelopeBlock (individual envelope)
//!   └─ MemberBlock (channel members)
//! ```

use serde::{Deserialize, Serialize};
use yata_core::Blake3Hash;

use crate::types::{ChannelKind, EncryptionState, MemberRole};

/// Individual envelope stored in CAS.
/// Blake3 CID = content address of CBOR encoding.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct EnvelopeBlock {
    pub id: String,
    pub kind: String,
    pub sender_did: String,
    pub org_id: String,
    pub channel_id: String,
    pub thread_id: String,
    pub reply_to: String,
    /// Plaintext or ciphertext depending on encryption state.
    pub payload: Vec<u8>,
    pub content_type: String,
    pub encryption: EncryptionState,
    pub causation_id: String,
    pub correlation_id: String,
    pub rkey: String,
    pub created_at: String,
}

/// Envelopes grouped by kind (e.g., all "message" envelopes).
/// CID comparison skips unchanged groups during sync → O(changed kinds).
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct EnvelopeGroupBlock {
    pub kind: String,
    /// Sorted CIDs of EnvelopeBlock entries.
    pub envelope_cids: Vec<Blake3Hash>,
    pub count: u32,
}

/// Channel metadata block.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct ChannelRootBlock {
    pub channel_id: String,
    pub org_id: String,
    pub name: String,
    pub description: String,
    pub kind: ChannelKind,
    pub encryption_mode: EncryptionState,
    pub creator_did: String,
}

/// Channel member block.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct MemberBlock {
    pub channel_id: String,
    pub did: String,
    pub role: MemberRole,
    pub joined_at: String,
}

/// W Protocol root block — one per channel commit.
/// CID of this block identifies the entire channel state at a point in time.
///
/// Mirrors yata-mdag's GraphRootBlock pattern:
/// - `parent` links form a commit chain for time-travel
/// - Merkle diff on `envelope_groups` enables O(changed) federation sync
/// - `channel_cid` is the channel metadata (changes rarely)
/// - `member_cids` tracks membership (changes on join/leave)
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct WRootBlock {
    pub version: u64,
    /// Previous root CID (commit chain for time-travel).
    pub parent: Option<Blake3Hash>,
    /// CID of ChannelRootBlock.
    pub channel_cid: Blake3Hash,
    /// CIDs of MemberBlock entries, sorted by DID.
    pub member_cids: Vec<Blake3Hash>,
    /// CIDs of EnvelopeGroupBlock entries, sorted by kind.
    pub envelope_groups: Vec<Blake3Hash>,
    /// Total envelope count across all groups.
    pub envelope_count: u32,
    pub member_count: u32,
    pub timestamp_ns: i64,
    pub message: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_envelope_block_cbor_roundtrip() {
        let block = EnvelopeBlock {
            id: "01HXYZ".into(),
            kind: "message".into(),
            sender_did: "did:plc:abc".into(),
            org_id: "org_123".into(),
            channel_id: "ch_456".into(),
            thread_id: "".into(),
            reply_to: "".into(),
            payload: b"hello world".to_vec(),
            content_type: "text/plain".into(),
            encryption: EncryptionState::Plaintext,
            causation_id: "".into(),
            correlation_id: "".into(),
            rkey: "3jui7kd2z".into(),
            created_at: "2026-03-17T12:00:00Z".into(),
        };
        let bytes = yata_cbor::encode(&block).unwrap();
        let decoded: EnvelopeBlock = yata_cbor::decode(&bytes).unwrap();
        assert_eq!(block, decoded);
    }

    #[test]
    fn test_deterministic_cid() {
        let a = EnvelopeBlock {
            id: "01A".into(),
            kind: "message".into(),
            sender_did: "did:plc:x".into(),
            org_id: "org_1".into(),
            channel_id: "ch_1".into(),
            thread_id: "".into(),
            reply_to: "".into(),
            payload: b"test".to_vec(),
            content_type: "text/plain".into(),
            encryption: EncryptionState::Plaintext,
            causation_id: "".into(),
            correlation_id: "".into(),
            rkey: "tid1".into(),
            created_at: "2026-03-17T00:00:00Z".into(),
        };
        let b = a.clone();
        assert_eq!(
            yata_cbor::cbor_cid(&a).unwrap(),
            yata_cbor::cbor_cid(&b).unwrap()
        );
    }

    #[test]
    fn test_different_payload_different_cid() {
        let a = EnvelopeBlock {
            id: "01A".into(),
            kind: "message".into(),
            sender_did: "did:plc:x".into(),
            org_id: "org_1".into(),
            channel_id: "ch_1".into(),
            thread_id: "".into(),
            reply_to: "".into(),
            payload: b"hello".to_vec(),
            content_type: "text/plain".into(),
            encryption: EncryptionState::Plaintext,
            causation_id: "".into(),
            correlation_id: "".into(),
            rkey: "tid1".into(),
            created_at: "2026-03-17T00:00:00Z".into(),
        };
        let mut b = a.clone();
        b.payload = b"world".to_vec();
        assert_ne!(
            yata_cbor::cbor_cid(&a).unwrap(),
            yata_cbor::cbor_cid(&b).unwrap()
        );
    }

    #[test]
    fn test_wroot_block_roundtrip() {
        let root = WRootBlock {
            version: 1,
            parent: None,
            channel_cid: Blake3Hash::of(b"channel"),
            member_cids: vec![Blake3Hash::of(b"m1"), Blake3Hash::of(b"m2")],
            envelope_groups: vec![Blake3Hash::of(b"eg1")],
            envelope_count: 42,
            member_count: 2,
            timestamp_ns: 1710700800_000_000_000,
            message: "initial commit".into(),
        };
        let bytes = yata_cbor::encode(&root).unwrap();
        let decoded: WRootBlock = yata_cbor::decode(&bytes).unwrap();
        assert_eq!(root, decoded);
    }

    #[test]
    fn test_envelope_group_block_roundtrip() {
        let group = EnvelopeGroupBlock {
            kind: "message".into(),
            envelope_cids: vec![Blake3Hash::of(b"e1"), Blake3Hash::of(b"e2")],
            count: 2,
        };
        let bytes = yata_cbor::encode(&group).unwrap();
        let decoded: EnvelopeGroupBlock = yata_cbor::decode(&bytes).unwrap();
        assert_eq!(group, decoded);
    }
}
