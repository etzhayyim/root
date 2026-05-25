//! W Protocol record mapping: WEnvelope → CBOR block → MDAG CAS (Blake3 CID).
//!
//! WIT canonical ABI is the primary format. No JSON in the hot path.

use yata_core::Blake3Hash;

use crate::blocks::EnvelopeBlock;
use crate::types::WEnvelope;

/// Maps W Protocol kinds to AT Protocol collection NSIDs.
pub struct RecordMapper;

/// CBOR-encoded record for MDAG CAS storage (primary).
pub struct CborRecord {
    pub collection: String,
    pub rkey: String,
    pub cbor_bytes: Vec<u8>,
    pub cid: Blake3Hash,
}

impl RecordMapper {
    const NAMESPACE: &'static str = "app.etzhayyim.w";

    /// Map kind → AT collection NSID.
    ///
    /// | kind              | AT collection NSID            |
    /// |-------------------|-------------------------------|
    /// | "message"         | app.etzhayyim.w.message             |
    /// | "channel"         | app.etzhayyim.w.channel             |
    /// | "read-receipt"    | app.etzhayyim.w.readReceipt         |
    /// | "prekey-bundle"   | app.etzhayyim.w.preKeyBundle        |
    /// | "a2a-task"        | app.etzhayyim.a2a.task (passthrough)|
    /// | "yoro.poll"       | app.etzhayyim.w.yoro.poll           |
    pub fn kind_to_collection(kind: &str) -> String {
        match kind {
            // A2A passthrough
            "a2a-task" => "app.etzhayyim.a2a.task".into(),
            "a2a-result" => "app.etzhayyim.a2a.result".into(),
            "a2a-message" => "app.etzhayyim.a2a.message".into(),
            "a2a-session" => "app.etzhayyim.a2a.session".into(),
            // Governance passthrough
            "governance-manifest" => "app.etzhayyim.governance.manifest".into(),
            "governance-delegation" => "app.etzhayyim.governance.delegation".into(),
            "governance-decision" => "app.etzhayyim.governance.decision".into(),
            // Built-in W Protocol kinds (camelCase for AT Lexicon convention)
            "read-receipt" => format!("{}.readReceipt", Self::NAMESPACE),
            "prekey-bundle" => format!("{}.preKeyBundle", Self::NAMESPACE),
            "signal-session" => format!("{}.signalSession", Self::NAMESPACE),
            // Default: app.etzhayyim.w.{kind}
            other => format!("{}.{}", Self::NAMESPACE, other),
        }
    }

    /// Primary path: WEnvelope → CBOR block → MDAG CAS.
    ///
    /// Used for internal storage and wRPC dispatch.
    /// Zero JSON allocation. CBOR is deterministic (same data → same CID).
    pub fn envelope_to_cbor(env: &WEnvelope) -> Result<CborRecord, String> {
        let collection = Self::kind_to_collection(&env.kind);
        let block = EnvelopeBlock {
            id: env.id.clone(),
            kind: env.kind.clone(),
            sender_did: env.sender_did.clone(),
            org_id: env.org_id.clone(),
            channel_id: env.channel_id.clone(),
            thread_id: env.thread_id.clone(),
            reply_to: env.reply_to.clone(),
            payload: env.payload.clone(),
            content_type: env.content_type.clone(),
            encryption: env.encryption,
            causation_id: env.causation_id.clone(),
            correlation_id: env.correlation_id.clone(),
            rkey: env.rkey.clone(),
            created_at: env.created_at.clone(),
        };
        let cbor_bytes = yata_cbor::encode(&block).map_err(|e| e.to_string())?;
        let cid = Blake3Hash::of(&cbor_bytes);
        Ok(CborRecord {
            collection,
            rkey: env.rkey.clone(),
            cbor_bytes,
            cid,
        })
    }

    /// Build AT URI from components.
    pub fn at_uri(did: &str, collection: &str, rkey: &str) -> String {
        format!("at://{}/{}/{}", did, collection, rkey)
    }

    /// All built-in W Protocol collection NSIDs (for magatama.toml Firehose subscription).
    pub fn builtin_collections() -> Vec<&'static str> {
        vec![
            "app.etzhayyim.w.message",
            "app.etzhayyim.w.channel",
            "app.etzhayyim.w.member",
            "app.etzhayyim.w.reaction",
            "app.etzhayyim.w.readReceipt",
            "app.etzhayyim.w.presence",
            "app.etzhayyim.w.preKeyBundle",
            "app.etzhayyim.w.signalSession",
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::*;

    fn test_env() -> WEnvelope {
        WEnvelope {
            id: "01TEST".into(),
            kind: "message".into(),
            cid: None,
            at_uri: "".into(),
            at_cid: "".into(),
            rkey: "tid123".into(),
            sender_did: "did:plc:alice".into(),
            org_id: "org_1".into(),
            channel_id: "ch_1".into(),
            thread_id: "".into(),
            reply_to: "".into(),
            payload: b"hello world".to_vec(),
            content_type: "text/plain".into(),
            encryption: EncryptionState::Plaintext,
            causation_id: "".into(),
            correlation_id: "".into(),
            created_at: "2026-03-17T12:00:00Z".into(),
        }
    }

    #[test]
    fn test_builtin_kind_mapping() {
        assert_eq!(RecordMapper::kind_to_collection("message"), "app.etzhayyim.w.message");
        assert_eq!(RecordMapper::kind_to_collection("channel"), "app.etzhayyim.w.channel");
        assert_eq!(
            RecordMapper::kind_to_collection("read-receipt"),
            "app.etzhayyim.w.readReceipt"
        );
        assert_eq!(
            RecordMapper::kind_to_collection("prekey-bundle"),
            "app.etzhayyim.w.preKeyBundle"
        );
    }

    #[test]
    fn test_a2a_passthrough() {
        assert_eq!(RecordMapper::kind_to_collection("a2a-task"), "app.etzhayyim.a2a.task");
        assert_eq!(
            RecordMapper::kind_to_collection("a2a-result"),
            "app.etzhayyim.a2a.result"
        );
    }

    #[test]
    fn test_governance_passthrough() {
        assert_eq!(
            RecordMapper::kind_to_collection("governance-manifest"),
            "app.etzhayyim.governance.manifest"
        );
    }

    #[test]
    fn test_custom_kind() {
        assert_eq!(
            RecordMapper::kind_to_collection("yoro.poll"),
            "app.etzhayyim.w.yoro.poll"
        );
        assert_eq!(
            RecordMapper::kind_to_collection("bpmn.task"),
            "app.etzhayyim.w.bpmn.task"
        );
    }

    #[test]
    fn test_at_uri() {
        assert_eq!(
            RecordMapper::at_uri("did:plc:abc", "app.etzhayyim.w.message", "3jui7kd2z"),
            "at://did:plc:abc/app.etzhayyim.w.message/3jui7kd2z"
        );
    }

    #[test]
    fn test_builtin_collections() {
        let cols = RecordMapper::builtin_collections();
        assert!(cols.contains(&"app.etzhayyim.w.message"));
        assert!(cols.contains(&"app.etzhayyim.w.channel"));
        assert_eq!(cols.len(), 8);
    }

    #[test]
    fn test_cbor_primary_path() {
        let env = test_env();
        let cbor = RecordMapper::envelope_to_cbor(&env).unwrap();
        assert_eq!(cbor.collection, "app.etzhayyim.w.message");
        assert_eq!(cbor.rkey, "tid123");
        assert!(!cbor.cbor_bytes.is_empty());
        // Deterministic: same input → same CID
        let cbor2 = RecordMapper::envelope_to_cbor(&env).unwrap();
        assert_eq!(cbor.cid, cbor2.cid);
    }

    #[test]
    fn test_different_payload_different_cid() {
        let env1 = test_env();
        let mut env2 = test_env();
        env2.payload = b"different".to_vec();
        let c1 = RecordMapper::envelope_to_cbor(&env1).unwrap();
        let c2 = RecordMapper::envelope_to_cbor(&env2).unwrap();
        assert_ne!(c1.cid, c2.cid);
    }
}
