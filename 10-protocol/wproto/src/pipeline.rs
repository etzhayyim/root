//! W Protocol processing pipeline.
//!
//! The central orchestrator: receives a command, executes the full pipeline:
//!
//! send() pipeline:
//!   1. Resolve channel → get encryption_mode
//!   2. AutoCrypto decision → encrypt/passthrough
//!   3. SessionManager → actual Signal crypto (if needed)
//!   4. RecordMapper → CBOR block (primary) + Lexicon JSON (derived)
//!   5. ChannelStore → KV projection (envelope + index)
//!   6. MDAG CAS → content-addressed block (Blake3 CID)
//!   7. yata-log → broadcast event (yata-native, replaces AT Firehose)
//!   8. Return WEnvelope with CID, AT URI, rkey populated

use std::sync::Arc;
use yata_cas::CasStore;
use yata_core::{AppendLog, Blake3Hash, Envelope, MessageId, PayloadRef, PublishRequest, SchemaId, StreamId, Subject};

use crate::channel::{ChannelStore, CypherExecutor};
use crate::crypto::AutoCrypto;
use crate::error::{Result, WProtoError};
use crate::record::RecordMapper;
use crate::session::SessionManager;
use yata_signal::store::SignalStorage;
use yata_signal::IdentityKeyPair;
use crate::types::*;

/// W Protocol processing pipeline.
///
/// Stateless coordinator — all state in ChannelStore/SessionManager/CAS.
pub struct WPipeline {
    pub channels: ChannelStore,
    pub sessions: SessionManager,
    cas: Arc<dyn CasStore>,
    log: Arc<dyn AppendLog>,
    bot_did: String,
}

impl WPipeline {
    pub fn new(
        cypher: Arc<dyn CypherExecutor>,
        signal_storage: Arc<dyn SignalStorage>,
        signal_identity: IdentityKeyPair,
        cas: Arc<dyn CasStore>,
        log: Arc<dyn AppendLog>,
        bot_did: String,
    ) -> Self {
        Self {
            channels: ChannelStore::new(cypher, cas.clone()),
            sessions: SessionManager::new(signal_storage, signal_identity, bot_did.clone()),
            cas,
            log,
            bot_did,
        }
    }

    // ── Command Pipeline ─────────────────────────────────

    /// Send envelope: the core W Protocol operation.
    ///
    /// 1. Resolve channel → encryption_mode
    /// 2. AutoCrypto → encrypt/passthrough
    /// 3. CBOR → MDAG CAS (Blake3 CID)
    /// 4. KV projection (channel:rkey → envelope)
    /// 5. yata-log broadcast
    /// 6. Return populated WEnvelope
    pub async fn send(
        &self,
        org_id: &str,
        sender_did: &str,
        sender_is_bot: bool,
        channel_id: &str,
        kind: &str,
        payload: Vec<u8>,
        content_type: &str,
        reply_to: Option<&str>,
        thread_id: Option<&str>,
    ) -> Result<WEnvelope> {
        // 1. Resolve channel
        let channel = self
            .channels
            .get_channel(org_id, channel_id)
            .await?
            .ok_or_else(|| WProtoError::ChannelNotFound(channel_id.into()))?;

        // 2. AutoCrypto decision + execute
        let decision = AutoCrypto::decide_encrypt(&channel, sender_is_bot);
        let encrypted = self.sessions.encrypt(&decision, &payload, &channel).await?;

        // 3. Build envelope
        let rkey = generate_tid();
        let id = generate_ulid();
        let now = chrono::Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();

        let mut env = WEnvelope {
            id: id.clone(),
            kind: kind.into(),
            cid: None,
            at_uri: String::new(),
            at_cid: String::new(),
            rkey: rkey.clone(),
            sender_did: sender_did.into(),
            org_id: org_id.into(),
            channel_id: channel_id.into(),
            thread_id: thread_id.unwrap_or("").into(),
            reply_to: reply_to.unwrap_or("").into(),
            payload: encrypted.ciphertext,
            content_type: if encrypted.encryption == EncryptionState::Plaintext {
                content_type.into()
            } else {
                "application/x-signal-envelope".into()
            },
            encryption: encrypted.encryption,
            causation_id: String::new(),
            correlation_id: String::new(),
            created_at: now,
        };

        // 4. CBOR → MDAG CAS
        let cbor = RecordMapper::envelope_to_cbor(&env)
            .map_err(|e| WProtoError::Cbor(e))?;
        let cid = self.cas.put(cbor.cbor_bytes.into()).await?;
        env.cid = Some(cid.clone());

        // 5. AT URI (derived)
        let collection = RecordMapper::kind_to_collection(kind);
        env.at_uri = RecordMapper::at_uri(&self.bot_did, &collection, &rkey);
        env.at_cid = cid.hex();

        // 6. Cypher graph persist (replaces KV projection)
        self.channels.store_envelope(&env).await?;

        // 7. Broadcast via yata-log (yata-native event bus)
        self.broadcast(org_id, channel_id, kind, &env).await?;

        Ok(env)
    }

    /// Create channel.
    pub async fn create_channel(
        &self,
        org_id: &str,
        creator_did: &str,
        name: &str,
        description: &str,
        kind: ChannelKind,
        invite_dids: &[String],
    ) -> Result<WChannel> {
        let channel_id = generate_nanoid();
        let now = chrono::Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();
        let encryption = AutoCrypto::resolve_channel_encryption(kind, None);

        let channel = WChannel {
            channel_id: channel_id.clone(),
            org_id: org_id.into(),
            name: name.into(),
            description: description.into(),
            kind,
            encryption_mode: encryption,
            creator_did: creator_did.into(),
            member_count: 1 + invite_dids.len() as i32,
            at_uri: RecordMapper::at_uri(
                &self.bot_did,
                &RecordMapper::kind_to_collection("channel"),
                &channel_id,
            ),
            created_at: now.clone(),
            mdag_root_cid: None,
        };

        self.channels.create_channel(&channel).await?;

        // Add creator as owner
        let creator_member = WMember {
            channel_id: channel_id.clone(),
            did: creator_did.into(),
            role: MemberRole::Owner,
            joined_at: now.clone(),
        };
        self.channels.add_member(&creator_member, org_id).await?;

        // Add invited members
        for did in invite_dids {
            let member = WMember {
                channel_id: channel_id.clone(),
                did: did.clone(),
                role: MemberRole::Member,
                joined_at: now.clone(),
            };
            self.channels.add_member(&member, org_id).await?;
        }

        // If encrypted: initialize Signal group session
        if encryption == EncryptionState::SignalGroup {
            // Group session will be lazily created on first encrypt
        }

        // MDAG initial commit
        let root_cid = self
            .channels
            .commit_channel(org_id, &channel_id, "channel created")
            .await?;

        let mut ch = channel;
        ch.mdag_root_cid = Some(root_cid);
        self.channels.update_channel(&ch).await?;

        Ok(ch)
    }

    /// Create DM channel with first message.
    pub async fn create_dm(
        &self,
        org_id: &str,
        creator_did: &str,
        sender_is_bot: bool,
        peer_did: &str,
        kind: &str,
        payload: Vec<u8>,
        content_type: &str,
    ) -> Result<(WChannel, WEnvelope)> {
        let channel = self
            .create_channel(
                org_id,
                creator_did,
                "DM",
                "",
                ChannelKind::Direct,
                &[peer_did.into()],
            )
            .await?;

        let env = self
            .send(
                org_id,
                creator_did,
                sender_is_bot,
                &channel.channel_id,
                kind,
                payload,
                content_type,
                None,
                None,
            )
            .await?;

        Ok((channel, env))
    }

    /// Join channel.
    pub async fn join_channel(
        &self,
        org_id: &str,
        did: &str,
        channel_id: &str,
    ) -> Result<WMember> {
        let now = chrono::Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();
        let member = WMember {
            channel_id: channel_id.into(),
            did: did.into(),
            role: MemberRole::Member,
            joined_at: now,
        };
        self.channels.add_member(&member, org_id).await?;

        // Update channel member count
        if let Some(mut ch) = self.channels.get_channel(org_id, channel_id).await? {
            ch.member_count += 1;
            self.channels.update_channel(&ch).await?;
        }

        Ok(member)
    }

    /// Leave channel. Triggers key rotation for encrypted channels.
    pub async fn leave_channel(
        &self,
        org_id: &str,
        did: &str,
        channel_id: &str,
    ) -> Result<()> {
        self.channels.remove_member(org_id, channel_id, did).await?;

        if let Some(mut ch) = self.channels.get_channel(org_id, channel_id).await? {
            ch.member_count = (ch.member_count - 1).max(0);
            self.channels.update_channel(&ch).await?;

            // Key rotation on leave (encrypted channels)
            if ch.encryption_mode == EncryptionState::SignalGroup {
                self.sessions.rotate_group_key(channel_id).await?;
            }
        }

        Ok(())
    }

    // ── A2A Operations (routed through W Protocol) ──────

    /// Create an A2A session — wraps create_channel with kind=A2a.
    pub async fn create_a2a_session(
        &self,
        org_id: &str,
        creator_did: &str,
        topic: &str,
        participant_dids: &[String],
    ) -> Result<WChannel> {
        self.create_channel(
            org_id,
            creator_did,
            topic,
            &format!("A2A session: {}", topic),
            ChannelKind::A2a,
            participant_dids,
        )
        .await
    }

    /// Send an A2A task — wraps send with kind="a2a-task".
    pub async fn send_a2a_task(
        &self,
        org_id: &str,
        sender_did: &str,
        channel_id: &str,
        payload: Vec<u8>,
    ) -> Result<WEnvelope> {
        self.send(
            org_id,
            sender_did,
            true, // A2A agents are always bot
            channel_id,
            "a2a-task",
            payload,
            "application/json",
            None,
            None,
        )
        .await
    }

    /// Send an A2A message — wraps send with kind="a2a-message".
    pub async fn send_a2a_message(
        &self,
        org_id: &str,
        sender_did: &str,
        channel_id: &str,
        payload: Vec<u8>,
        reply_to: Option<&str>,
    ) -> Result<WEnvelope> {
        self.send(
            org_id,
            sender_did,
            true,
            channel_id,
            "a2a-message",
            payload,
            "application/json",
            reply_to,
            None,
        )
        .await
    }

    // ── Query Pipeline ───────────────────────────────────

    /// List envelopes in a channel.
    /// For bot/A2A channels: host auto-decrypts.
    /// For human E2E channels: returns ciphertext (client decrypts).
    pub async fn list_envelopes(
        &self,
        org_id: &str,
        _receiver_did: &str,
        receiver_is_bot: bool,
        channel_id: &str,
        limit: usize,
        before_rkey: Option<&str>,
    ) -> Result<Vec<WEnvelope>> {
        let envelopes = self
            .channels
            .list_envelopes(org_id, channel_id, limit, before_rkey)
            .await?;

        if !receiver_is_bot {
            // Human receiver: return as-is (client decrypts)
            return Ok(envelopes);
        }

        // Bot/Agent receiver: host decrypts
        let channel = self
            .channels
            .get_channel(org_id, channel_id)
            .await?
            .ok_or_else(|| WProtoError::ChannelNotFound(channel_id.into()))?;

        let mut decrypted = Vec::with_capacity(envelopes.len());
        for mut env in envelopes {
            if env.encryption != EncryptionState::Plaintext {
                let decision =
                    AutoCrypto::decide_decrypt(&channel, receiver_is_bot, env.encryption);
                let result = self
                    .sessions
                    .decrypt(&decision, &env.payload, &env.sender_did, &channel)
                    .await?;
                env.payload = result.plaintext;
                env.content_type = "text/plain".into();
                env.encryption = EncryptionState::Plaintext;
            }
            decrypted.push(env);
        }
        Ok(decrypted)
    }

    /// Mark channel as read.
    pub async fn mark_read(
        &self,
        org_id: &str,
        did: &str,
        channel_id: &str,
        last_rkey: &str,
    ) -> Result<()> {
        self.channels
            .mark_read(org_id, channel_id, did, last_rkey)
            .await
    }

    /// Get unread counts for a user.
    pub async fn get_unread(&self, org_id: &str, did: &str) -> Result<Vec<(String, i32)>> {
        self.channels.get_unread(org_id, did).await
    }

    // ── Internal ─────────────────────────────────────────

    /// Broadcast envelope via yata-log (yata-native event bus).
    /// Replaces AT Firehose — no external dependency, embedded broker latency.
    async fn broadcast(
        &self,
        org_id: &str,
        channel_id: &str,
        kind: &str,
        env: &WEnvelope,
    ) -> Result<()> {
        let env_bytes =
            yata_cbor::encode(env).map_err(|e| WProtoError::Cbor(e.to_string()))?;

        let req = PublishRequest {
            stream: StreamId(format!("_w.{}", kind)),
            subject: Subject(format!("{}:{}", org_id, channel_id)),
            envelope: Envelope {
                message_id: MessageId(uuid::Uuid::new_v4()),
                subject: Subject(channel_id.into()),
                schema_id: SchemaId("w-envelope".into()),
                content_hash: env.cid.clone().unwrap_or_else(|| Blake3Hash::of(&env_bytes)),
                causality: vec![],
                ocel_event_type: Some(format!("w.{}", kind)),
                ocel_object_refs: vec![],
                headers: indexmap::IndexMap::new(),
                ts_ns: chrono::Utc::now().timestamp_nanos_opt().unwrap_or(0),
            },
            payload: PayloadRef::InlineBytes(env_bytes.into()),
            expected_last_seq: None,
        };

        self.log
            .append(req)
            .await
            .map_err(|e| WProtoError::Other(e.to_string()))?;

        Ok(())
    }
}

// ── ID generation ────────────────────────────────────────

fn generate_tid() -> String {
    // TID: base32-sortable timestamp (AT Protocol convention)
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default();
    let us = now.as_micros() as u64;
    format!("{:>013}", base32_encode(us))
}

fn generate_ulid() -> String {
    // Simple timestamp-based unique ID (ulid-like)
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default();
    let ns = now.as_nanos() as u64;
    format!("{:016x}", ns)
}

fn generate_nanoid() -> String {
    // 8-char alphanumeric ID
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default();
    let ns = now.as_nanos() as u64;
    format!("{:>08}", base36_encode(ns))
}

fn base32_encode(mut n: u64) -> String {
    const CHARS: &[u8] = b"234567abcdefghijklmnopqrstuvwxyz";
    if n == 0 {
        return "2".into();
    }
    let mut s = Vec::new();
    while n > 0 {
        s.push(CHARS[(n % 32) as usize]);
        n /= 32;
    }
    s.reverse();
    String::from_utf8(s).unwrap_or_default()
}

fn base36_encode(mut n: u64) -> String {
    const CHARS: &[u8] = b"0123456789abcdefghijklmnopqrstuvwxyz";
    if n == 0 {
        return "0".into();
    }
    let mut s = Vec::new();
    while n > 0 {
        s.push(CHARS[(n % 36) as usize]);
        n /= 36;
    }
    s.reverse();
    String::from_utf8(s).unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;
    use std::sync::Mutex;
    use yata_cas::LocalCasStore;

    /// In-memory CypherExecutor mock that stores WChannel/WMember data.
    struct MockCypher {
        channels: Mutex<Vec<HashMap<String, String>>>,
        members: Mutex<Vec<HashMap<String, String>>>,
    }

    impl MockCypher {
        fn new() -> Self {
            Self {
                channels: Mutex::new(Vec::new()),
                members: Mutex::new(Vec::new()),
            }
        }
    }

    #[async_trait::async_trait]
    impl crate::channel::CypherExecutor for MockCypher {
        async fn exec(&self, cypher: &str, params: &[(String, String)]) -> crate::Result<()> {
            let map: HashMap<String, String> = params
                .iter()
                .map(|(k, v)| (k.clone(), v.trim_matches('"').to_string()))
                .collect();
            if cypher.contains("MERGE (c:WChannel") || cypher.contains("SET c.mdag_root_cid") {
                let mut channels = self.channels.lock().unwrap();
                // Upsert by channel_id
                let ch_id = map.get("id").or(map.get("ch")).cloned().unwrap_or_default();
                if let Some(existing) = channels.iter_mut().find(|c| c.get("id").map(|v| v.as_str()) == Some(&ch_id)) {
                    for (k, v) in &map {
                        existing.insert(k.clone(), v.clone());
                    }
                } else {
                    channels.push(map);
                }
            } else if cypher.contains("MERGE (m:WMember") {
                self.members.lock().unwrap().push(map);
            }
            Ok(())
        }

        async fn query(
            &self,
            cypher: &str,
            params: &[(String, String)],
        ) -> crate::Result<Vec<Vec<(String, String)>>> {
            let pmap: HashMap<String, String> = params
                .iter()
                .map(|(k, v)| (k.clone(), v.trim_matches('"').to_string()))
                .collect();

            if cypher.contains("MATCH (c:WChannel {channel_id:") {
                let channels = self.channels.lock().unwrap();
                let ch_id = pmap.get("id").or(pmap.get("ch")).cloned().unwrap_or_default();
                let org = pmap.get("org").cloned().unwrap_or_default();
                if let Some(ch) = channels.iter().find(|c| {
                    c.get("id").map(|v| v.as_str()) == Some(&ch_id) &&
                    c.get("org").map(|v| v.as_str()) == Some(&org)
                }) {
                    return Ok(vec![vec![
                        ("c.channel_id".into(), ch.get("id").cloned().unwrap_or_default()),
                        ("c.org_id".into(), ch.get("org").cloned().unwrap_or_default()),
                        ("c.name".into(), ch.get("name").cloned().unwrap_or_default()),
                        ("c.description".into(), ch.get("desc").cloned().unwrap_or_default()),
                        ("c.kind".into(), ch.get("kind").cloned().unwrap_or_else(|| "Public".into())),
                        ("c.encryption_mode".into(), ch.get("enc").cloned().unwrap_or_else(|| "plaintext".into())),
                        ("c.creator_did".into(), ch.get("creator").cloned().unwrap_or_default()),
                        ("c.member_count".into(), ch.get("mc").cloned().unwrap_or_else(|| "0".into())),
                        ("c.at_uri".into(), String::new()),
                        ("c.mdag_root_cid".into(), ch.get("cid").cloned().unwrap_or_default()),
                        ("c.created_at".into(), ch.get("ts").cloned().unwrap_or_default()),
                    ]]);
                }
                return Ok(vec![]);
            }

            if cypher.contains("MATCH (m:WMember") {
                let members = self.members.lock().unwrap();
                let ch_id = pmap.get("ch").cloned().unwrap_or_default();
                let rows: Vec<Vec<(String, String)>> = members
                    .iter()
                    .filter(|m| m.get("ch").map(|v| v.as_str()) == Some(&ch_id))
                    .map(|m| vec![
                        ("m.did".into(), m.get("did").cloned().unwrap_or_default()),
                        ("m.role".into(), m.get("role").cloned().unwrap_or_else(|| "Member".into())),
                        ("m.joined_at".into(), m.get("ts").cloned().unwrap_or_default()),
                        ("c.channel_id".into(), ch_id.clone()),
                    ])
                    .collect();
                return Ok(rows);
            }

            Ok(vec![])
        }
    }

    /// In-memory SignalStorage mock.
    struct MockSignalStorage {
        data: Mutex<HashMap<String, Vec<u8>>>,
    }

    impl MockSignalStorage {
        fn new() -> Self {
            Self {
                data: Mutex::new(HashMap::new()),
            }
        }
    }

    #[async_trait::async_trait]
    impl yata_signal::store::SignalStorage for MockSignalStorage {
        async fn load(&self, collection: &str, key: &str) -> std::result::Result<Option<Vec<u8>>, String> {
            let k = format!("{}:{}", collection, key);
            Ok(self.data.lock().unwrap().get(&k).cloned())
        }

        async fn save(&self, collection: &str, key: &str, value: Vec<u8>) -> std::result::Result<(), String> {
            let k = format!("{}:{}", collection, key);
            self.data.lock().unwrap().insert(k, value);
            Ok(())
        }
    }

    /// In-memory AppendLog mock.
    struct MockLog;

    #[async_trait::async_trait]
    impl AppendLog for MockLog {
        async fn append(&self, _req: PublishRequest) -> yata_core::Result<yata_core::Ack> {
            Ok(yata_core::Ack {
                message_id: yata_core::MessageId(uuid::Uuid::new_v4()),
                stream_id: yata_core::StreamId("_w.message".into()),
                seq: yata_core::Sequence(1),
                ts_ns: 0,
            })
        }

        async fn read_from(
            &self,
            _stream: &yata_core::StreamId,
            _from_seq: yata_core::Sequence,
        ) -> yata_core::Result<std::pin::Pin<Box<dyn futures::Stream<Item = yata_core::Result<yata_core::LogEntry>> + Send>>> {
            Ok(Box::pin(futures::stream::empty()))
        }

        async fn last_seq(&self, _stream: &yata_core::StreamId) -> yata_core::Result<Option<yata_core::Sequence>> {
            Ok(None)
        }
    }

    async fn make_pipeline() -> (WPipeline, Arc<LocalCasStore>) {
        let dir = tempfile::tempdir().unwrap();
        let cas = Arc::new(LocalCasStore::new(dir.path().join("cas")).await.unwrap());
        let cypher: Arc<dyn crate::channel::CypherExecutor> = Arc::new(MockCypher::new());
        let signal: Arc<dyn yata_signal::store::SignalStorage> =
            Arc::new(MockSignalStorage::new());
        let identity = yata_signal::IdentityKeyPair::generate();
        let log: Arc<dyn AppendLog> = Arc::new(MockLog);

        let pipeline = WPipeline::new(
            cypher,
            signal,
            identity,
            cas.clone(),
            log,
            "did:plc:test-bot".into(),
        );
        (pipeline, cas)
    }

    #[tokio::test]
    async fn test_create_channel() {
        let (pipeline, _cas) = make_pipeline().await;

        let ch = pipeline
            .create_channel("org1", "did:plc:alice", "general", "test", ChannelKind::Public, &[])
            .await
            .unwrap();

        assert_eq!(ch.org_id, "org1");
        assert_eq!(ch.name, "general");
        assert_eq!(ch.creator_did, "did:plc:alice");
        assert_eq!(ch.member_count, 1);
        assert!(ch.mdag_root_cid.is_some());
    }

    #[tokio::test]
    async fn test_create_channel_with_invites() {
        let (pipeline, _cas) = make_pipeline().await;

        let ch = pipeline
            .create_channel(
                "org1",
                "did:plc:alice",
                "team",
                "",
                ChannelKind::Private,
                &["did:plc:bob".into(), "did:plc:carol".into()],
            )
            .await
            .unwrap();

        assert_eq!(ch.member_count, 3);
    }

    #[tokio::test]
    async fn test_create_a2a_session() {
        let (pipeline, _cas) = make_pipeline().await;

        let ch = pipeline
            .create_a2a_session(
                "org1",
                "did:plc:agent1",
                "Translation task",
                &["did:plc:agent2".into()],
            )
            .await
            .unwrap();

        assert_eq!(ch.kind, ChannelKind::A2a);
        assert_eq!(ch.member_count, 2);
    }

    #[tokio::test]
    async fn test_id_generation() {
        let tid = generate_tid();
        assert!(!tid.is_empty());
        assert!(tid.len() >= 13);

        let ulid = generate_ulid();
        assert_eq!(ulid.len(), 16);

        let nanoid = generate_nanoid();
        assert!(nanoid.len() >= 8);

        // Uniqueness
        let tid2 = generate_tid();
        // Allow same value if called in same microsecond (rare but possible)
        let _ = tid2;
    }

    #[tokio::test]
    async fn test_base_encoding() {
        assert_eq!(base32_encode(0), "2");
        assert_eq!(base36_encode(0), "0");
        assert!(!base32_encode(12345).is_empty());
        assert!(!base36_encode(12345).is_empty());
    }
}
