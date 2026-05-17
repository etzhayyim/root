//! WCommitLog: channel-scoped MDAG commit chain.
//!
//! Each channel has its own commit log. Every batch of envelopes
//! (or membership change) creates a new WRootBlock commit.
//!
//! Commit chain enables:
//! - Time-travel: checkout channel state at any past commit
//! - Federation sync: share root CID via AT Protocol, Merkle diff for delta
//! - Audit trail: immutable history of all channel mutations

use std::collections::BTreeMap;
use std::sync::Arc;

use yata_cas::CasStore;
use yata_core::Blake3Hash;

use crate::blocks::*;
use crate::error::{Result, WProtoError};
use crate::types::{WChannel, WEnvelope, WMember};

/// Manages the W Protocol commit chain for a single channel.
pub struct WCommitLog {
    cas: Arc<dyn CasStore>,
    channel_id: String,
    head: Option<Blake3Hash>,
}

impl WCommitLog {
    pub fn new(cas: Arc<dyn CasStore>, channel_id: String) -> Self {
        Self { cas, channel_id, head: None }
    }

    pub fn with_head(cas: Arc<dyn CasStore>, channel_id: String, head: Blake3Hash) -> Self {
        Self { cas, channel_id, head: Some(head) }
    }

    pub fn head(&self) -> Option<&Blake3Hash> {
        self.head.as_ref()
    }

    pub fn channel_id(&self) -> &str {
        &self.channel_id
    }

    /// Commit current channel state: channel metadata + members + envelopes.
    ///
    /// Envelopes are grouped by `kind` for efficient Merkle diff:
    /// unchanged kind groups are skipped in O(1) via CID comparison.
    pub async fn commit(
        &mut self,
        channel: &WChannel,
        members: &[WMember],
        envelopes: &[WEnvelope],
        message: &str,
    ) -> Result<Blake3Hash> {
        let cas = self.cas.as_ref();

        // 1. Serialize channel metadata
        let channel_block = ChannelRootBlock {
            channel_id: channel.channel_id.clone(),
            org_id: channel.org_id.clone(),
            name: channel.name.clone(),
            description: channel.description.clone(),
            kind: channel.kind,
            encryption_mode: channel.encryption_mode,
            creator_did: channel.creator_did.clone(),
        };
        let channel_cid = store_block(cas, &channel_block).await?;

        // 2. Serialize members (sorted by DID for determinism)
        let mut member_cids = Vec::with_capacity(members.len());
        let mut sorted_members: Vec<_> = members.iter().collect();
        sorted_members.sort_by_key(|m| &m.did);
        for m in &sorted_members {
            let block = MemberBlock {
                channel_id: m.channel_id.clone(),
                did: m.did.clone(),
                role: m.role,
                joined_at: m.joined_at.clone(),
            };
            member_cids.push(store_block(cas, &block).await?);
        }

        // 3. Group envelopes by kind, serialize each group
        let mut groups: BTreeMap<String, Vec<Blake3Hash>> = BTreeMap::new();
        for env in envelopes {
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
            let cid = store_block(cas, &block).await?;
            groups.entry(env.kind.clone()).or_default().push(cid);
        }

        // Sort CIDs within each group for deterministic group CID
        let mut envelope_group_cids = Vec::with_capacity(groups.len());
        let total_envelopes: u32 = envelopes.len() as u32;
        for (kind, mut cids) in groups {
            cids.sort_by(|a, b| a.hex().cmp(&b.hex()));
            let group = EnvelopeGroupBlock {
                kind,
                count: cids.len() as u32,
                envelope_cids: cids,
            };
            envelope_group_cids.push(store_block(cas, &group).await?);
        }
        envelope_group_cids.sort_by(|a, b| a.hex().cmp(&b.hex()));

        // 4. Build root block
        let now_ns = chrono::Utc::now().timestamp_nanos_opt().unwrap_or(0);
        let root = WRootBlock {
            version: 1,
            parent: self.head.clone(),
            channel_cid,
            member_cids,
            envelope_groups: envelope_group_cids,
            envelope_count: total_envelopes,
            member_count: sorted_members.len() as u32,
            timestamp_ns: now_ns,
            message: message.to_string(),
        };
        let root_cid = store_block(cas, &root).await?;

        self.head = Some(root_cid.clone());
        Ok(root_cid)
    }

    /// Walk the parent chain to list recent commits (most recent first).
    pub async fn history(&self, limit: usize) -> Result<Vec<(Blake3Hash, WRootBlock)>> {
        let mut results = Vec::new();
        let mut current = self.head.clone();

        while let Some(cid) = current {
            if results.len() >= limit {
                break;
            }
            let root: WRootBlock = fetch_block(self.cas.as_ref(), &cid).await?;
            current = root.parent.clone();
            results.push((cid, root));
        }
        Ok(results)
    }

    /// Load channel metadata at a specific commit.
    pub async fn checkout_channel(&self, root_cid: &Blake3Hash) -> Result<ChannelRootBlock> {
        let root: WRootBlock = fetch_block(self.cas.as_ref(), root_cid).await?;
        fetch_block(self.cas.as_ref(), &root.channel_cid).await
    }

    /// Load all envelopes at a specific commit.
    pub async fn checkout_envelopes(&self, root_cid: &Blake3Hash) -> Result<Vec<EnvelopeBlock>> {
        let root: WRootBlock = fetch_block(self.cas.as_ref(), root_cid).await?;
        let mut envelopes = Vec::new();

        for group_cid in &root.envelope_groups {
            let group: EnvelopeGroupBlock = fetch_block(self.cas.as_ref(), group_cid).await?;
            for env_cid in &group.envelope_cids {
                let env: EnvelopeBlock = fetch_block(self.cas.as_ref(), env_cid).await?;
                envelopes.push(env);
            }
        }
        Ok(envelopes)
    }

    /// Load all members at a specific commit.
    pub async fn checkout_members(&self, root_cid: &Blake3Hash) -> Result<Vec<MemberBlock>> {
        let root: WRootBlock = fetch_block(self.cas.as_ref(), root_cid).await?;
        let mut members = Vec::new();
        for cid in &root.member_cids {
            members.push(fetch_block(self.cas.as_ref(), cid).await?);
        }
        Ok(members)
    }

    /// Compute Merkle diff between two commits.
    pub async fn diff(&self, old: &Blake3Hash, new: &Blake3Hash) -> Result<crate::diff::WDiff> {
        crate::diff::w_diff(old, new, self.cas.as_ref()).await
    }
}

/// Store a CBOR-serializable block in CAS, return its Blake3 CID.
async fn store_block<T: serde::Serialize>(cas: &dyn CasStore, block: &T) -> Result<Blake3Hash> {
    let bytes = yata_cbor::encode(block).map_err(|e| WProtoError::Cbor(e.to_string()))?;
    let cid = cas.put(bytes.into()).await?;
    Ok(cid)
}

/// Fetch and decode a CBOR block from CAS by CID.
async fn fetch_block<T: serde::de::DeserializeOwned>(
    cas: &dyn CasStore,
    cid: &Blake3Hash,
) -> Result<T> {
    let data = cas
        .get(cid)
        .await?
        .ok_or_else(|| WProtoError::EnvelopeNotFound(cid.clone()))?;
    yata_cbor::decode(&data).map_err(|e| WProtoError::Cbor(e.to_string()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::*;
    use yata_cas::LocalCasStore;

    fn test_channel() -> WChannel {
        WChannel {
            channel_id: "ch_test".into(),
            org_id: "org_1".into(),
            name: "general".into(),
            description: "General discussion".into(),
            kind: ChannelKind::Public,
            encryption_mode: EncryptionState::Plaintext,
            creator_did: "did:plc:creator".into(),
            member_count: 2,
            at_uri: "".into(),
            created_at: "2026-03-17T00:00:00Z".into(),
            mdag_root_cid: None,
        }
    }

    fn test_members() -> Vec<WMember> {
        vec![
            WMember {
                channel_id: "ch_test".into(),
                did: "did:plc:alice".into(),
                role: MemberRole::Owner,
                joined_at: "2026-03-17T00:00:00Z".into(),
            },
            WMember {
                channel_id: "ch_test".into(),
                did: "did:plc:bob".into(),
                role: MemberRole::Member,
                joined_at: "2026-03-17T00:01:00Z".into(),
            },
        ]
    }

    fn test_envelope(id: &str, body: &str) -> WEnvelope {
        WEnvelope {
            id: id.into(),
            kind: "message".into(),
            cid: None,
            at_uri: "".into(),
            at_cid: "".into(),
            rkey: format!("rkey_{id}"),
            sender_did: "did:plc:alice".into(),
            org_id: "org_1".into(),
            channel_id: "ch_test".into(),
            thread_id: "".into(),
            reply_to: "".into(),
            payload: body.as_bytes().to_vec(),
            content_type: "text/plain".into(),
            encryption: EncryptionState::Plaintext,
            causation_id: "".into(),
            correlation_id: "".into(),
            created_at: "2026-03-17T12:00:00Z".into(),
        }
    }

    #[tokio::test]
    async fn test_commit_and_checkout() {
        let dir = tempfile::tempdir().unwrap();
        let cas = Arc::new(LocalCasStore::new(dir.path().join("cas")).await.unwrap());
        let mut log = WCommitLog::new(cas, "ch_test".into());

        let channel = test_channel();
        let members = test_members();
        let envelopes = vec![
            test_envelope("e1", "hello"),
            test_envelope("e2", "world"),
        ];

        let c1 = log.commit(&channel, &members, &envelopes, "initial").await.unwrap();
        assert_eq!(log.head(), Some(&c1));

        // Checkout envelopes
        let loaded = log.checkout_envelopes(&c1).await.unwrap();
        assert_eq!(loaded.len(), 2);

        // Checkout members
        let loaded_members = log.checkout_members(&c1).await.unwrap();
        assert_eq!(loaded_members.len(), 2);
        // Members sorted by DID
        assert_eq!(loaded_members[0].did, "did:plc:alice");
        assert_eq!(loaded_members[1].did, "did:plc:bob");

        // Checkout channel
        let loaded_channel = log.checkout_channel(&c1).await.unwrap();
        assert_eq!(loaded_channel.name, "general");
    }

    #[tokio::test]
    async fn test_commit_chain() {
        let dir = tempfile::tempdir().unwrap();
        let cas = Arc::new(LocalCasStore::new(dir.path().join("cas")).await.unwrap());
        let mut log = WCommitLog::new(cas, "ch_test".into());

        let channel = test_channel();
        let members = test_members();

        let e1 = vec![test_envelope("e1", "first")];
        let c1 = log.commit(&channel, &members, &e1, "v1").await.unwrap();

        let e2 = vec![test_envelope("e1", "first"), test_envelope("e2", "second")];
        let c2 = log.commit(&channel, &members, &e2, "v2").await.unwrap();

        let e3 = vec![
            test_envelope("e1", "first"),
            test_envelope("e2", "second"),
            test_envelope("e3", "third"),
        ];
        let c3 = log.commit(&channel, &members, &e3, "v3").await.unwrap();

        // History walks parent chain
        let history = log.history(10).await.unwrap();
        assert_eq!(history.len(), 3);
        assert_eq!(history[0].0, c3);
        assert_eq!(history[1].0, c2);
        assert_eq!(history[2].0, c1);
        assert_eq!(history[0].1.message, "v3");
        assert!(history[2].1.parent.is_none());
    }

    #[tokio::test]
    async fn test_time_travel_checkout() {
        let dir = tempfile::tempdir().unwrap();
        let cas = Arc::new(LocalCasStore::new(dir.path().join("cas")).await.unwrap());
        let mut log = WCommitLog::new(cas, "ch_test".into());

        let channel = test_channel();
        let members = test_members();

        let e1 = vec![test_envelope("e1", "hello")];
        let c1 = log.commit(&channel, &members, &e1, "v1").await.unwrap();

        let e2 = vec![test_envelope("e1", "hello"), test_envelope("e2", "bye")];
        let _c2 = log.commit(&channel, &members, &e2, "v2").await.unwrap();

        // Time-travel: checkout v1 should only have 1 envelope
        let old_envs = log.checkout_envelopes(&c1).await.unwrap();
        assert_eq!(old_envs.len(), 1);
        assert_eq!(old_envs[0].payload, b"hello");
    }

    #[tokio::test]
    async fn test_diff_between_commits() {
        let dir = tempfile::tempdir().unwrap();
        let cas = Arc::new(LocalCasStore::new(dir.path().join("cas")).await.unwrap());
        let mut log = WCommitLog::new(cas, "ch_test".into());

        let channel = test_channel();
        let members = test_members();

        let e1 = vec![test_envelope("e1", "hello")];
        let c1 = log.commit(&channel, &members, &e1, "v1").await.unwrap();

        let e2 = vec![test_envelope("e1", "hello"), test_envelope("e2", "new msg")];
        let c2 = log.commit(&channel, &members, &e2, "v2").await.unwrap();

        let diff = log.diff(&c1, &c2).await.unwrap();
        assert!(!diff.is_empty());
        assert_eq!(diff.added_envelope_cids.len(), 1); // e2 added
    }
}
