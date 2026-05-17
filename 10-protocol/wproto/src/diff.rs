//! Merkle diff between two W Protocol channel commits.
//!
//! Mirrors yata-mdag's `merkle_diff` pattern but operates on W Protocol blocks:
//! - EnvelopeGroupBlock (grouped by kind) enables O(changed kinds) skip
//! - MemberBlock CID comparison detects membership changes
//! - ChannelRootBlock CID comparison detects metadata changes

use std::collections::{BTreeMap, BTreeSet, HashSet};

use yata_cas::CasStore;
use yata_core::Blake3Hash;

use crate::blocks::*;
use crate::error::{Result, WProtoError};

/// Diff result between two W Protocol channel commits.
#[derive(Debug, Clone, Default)]
pub struct WDiff {
    /// Envelope CIDs added since old commit.
    pub added_envelope_cids: Vec<Blake3Hash>,
    /// Envelope CIDs removed since old commit.
    pub removed_envelope_cids: Vec<Blake3Hash>,
    /// Member CIDs added.
    pub added_member_cids: Vec<Blake3Hash>,
    /// Member CIDs removed.
    pub removed_member_cids: Vec<Blake3Hash>,
    /// New envelope kinds (groups) that appeared.
    pub added_kinds: Vec<String>,
    /// Envelope kinds (groups) that were removed entirely.
    pub removed_kinds: Vec<String>,
    /// Whether channel metadata changed.
    pub channel_changed: bool,
}

impl WDiff {
    pub fn is_empty(&self) -> bool {
        self.added_envelope_cids.is_empty()
            && self.removed_envelope_cids.is_empty()
            && self.added_member_cids.is_empty()
            && self.removed_member_cids.is_empty()
            && self.added_kinds.is_empty()
            && self.removed_kinds.is_empty()
            && !self.channel_changed
    }

    pub fn total_changes(&self) -> usize {
        self.added_envelope_cids.len()
            + self.removed_envelope_cids.len()
            + self.added_member_cids.len()
            + self.removed_member_cids.len()
    }
}

/// Compute Merkle diff between two W Protocol channel root CIDs.
///
/// O(changed kinds + changed envelopes within changed kinds).
/// Unchanged envelope groups are skipped in O(1) via CID comparison.
pub async fn w_diff(
    old_root_cid: &Blake3Hash,
    new_root_cid: &Blake3Hash,
    cas: &dyn CasStore,
) -> Result<WDiff> {
    if old_root_cid == new_root_cid {
        return Ok(WDiff::default());
    }

    let old_root: WRootBlock = fetch(cas, old_root_cid).await?;
    let new_root: WRootBlock = fetch(cas, new_root_cid).await?;

    let mut diff = WDiff::default();
    diff.channel_changed = old_root.channel_cid != new_root.channel_cid;

    // ── Diff envelope groups ────────────────────────────────
    let old_groups = load_group_map(cas, &old_root.envelope_groups).await?;
    let new_groups = load_group_map(cas, &new_root.envelope_groups).await?;

    let all_kinds: BTreeSet<&str> = old_groups
        .keys()
        .chain(new_groups.keys())
        .map(|s| s.as_str())
        .collect();

    for kind in all_kinds {
        match (old_groups.get(kind), new_groups.get(kind)) {
            (None, Some(new_g)) => {
                diff.added_kinds.push(kind.to_string());
                diff.added_envelope_cids.extend(new_g.envelope_cids.clone());
            }
            (Some(old_g), None) => {
                diff.removed_kinds.push(kind.to_string());
                diff.removed_envelope_cids
                    .extend(old_g.envelope_cids.clone());
            }
            (Some(old_g), Some(new_g)) => {
                let old_set: HashSet<_> = old_g.envelope_cids.iter().collect();
                let new_set: HashSet<_> = new_g.envelope_cids.iter().collect();
                for cid in new_set.difference(&old_set) {
                    diff.added_envelope_cids.push((*cid).clone());
                }
                for cid in old_set.difference(&new_set) {
                    diff.removed_envelope_cids.push((*cid).clone());
                }
            }
            (None, None) => unreachable!(),
        }
    }

    // ── Diff members ─────────────────────────────────────────
    let old_members: HashSet<_> = old_root.member_cids.iter().collect();
    let new_members: HashSet<_> = new_root.member_cids.iter().collect();
    for cid in new_members.difference(&old_members) {
        diff.added_member_cids.push((*cid).clone());
    }
    for cid in old_members.difference(&new_members) {
        diff.removed_member_cids.push((*cid).clone());
    }

    Ok(diff)
}

async fn load_group_map(
    cas: &dyn CasStore,
    cids: &[Blake3Hash],
) -> Result<BTreeMap<String, EnvelopeGroupBlock>> {
    let mut map = BTreeMap::new();
    for cid in cids {
        let group: EnvelopeGroupBlock = fetch(cas, cid).await?;
        map.insert(group.kind.clone(), group);
    }
    Ok(map)
}

async fn fetch<T: serde::de::DeserializeOwned>(cas: &dyn CasStore, cid: &Blake3Hash) -> Result<T> {
    let data = cas
        .get(cid)
        .await?
        .ok_or_else(|| WProtoError::EnvelopeNotFound(cid.clone()))?;
    yata_cbor::decode(&data).map_err(|e| WProtoError::Cbor(e.to_string()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::commit::WCommitLog;
    use crate::types::*;
    use yata_cas::LocalCasStore;

    fn ch() -> WChannel {
        WChannel {
            channel_id: "ch1".into(),
            org_id: "org1".into(),
            name: "test".into(),
            description: "".into(),
            kind: ChannelKind::Public,
            encryption_mode: EncryptionState::Plaintext,
            creator_did: "did:plc:x".into(),
            member_count: 1,
            at_uri: "".into(),
            created_at: "2026-03-17T00:00:00Z".into(),
            mdag_root_cid: None,
        }
    }

    fn m() -> Vec<WMember> {
        vec![WMember {
            channel_id: "ch1".into(),
            did: "did:plc:alice".into(),
            role: MemberRole::Owner,
            joined_at: "2026-03-17T00:00:00Z".into(),
        }]
    }

    fn env(id: &str, body: &str) -> WEnvelope {
        WEnvelope {
            id: id.into(),
            kind: "message".into(),
            cid: None,
            at_uri: "".into(),
            at_cid: "".into(),
            rkey: format!("r_{id}"),
            sender_did: "did:plc:alice".into(),
            org_id: "org1".into(),
            channel_id: "ch1".into(),
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
    async fn test_same_root_empty_diff() {
        let dir = tempfile::tempdir().unwrap();
        let cas = std::sync::Arc::new(
            LocalCasStore::new(dir.path().join("cas")).await.unwrap(),
        );
        let mut log = WCommitLog::new(cas.clone(), "ch1".into());
        let c1 = log.commit(&ch(), &m(), &[env("e1", "hi")], "v1").await.unwrap();
        let diff = w_diff(&c1, &c1, cas.as_ref()).await.unwrap();
        assert!(diff.is_empty());
    }

    #[tokio::test]
    async fn test_add_envelope() {
        let dir = tempfile::tempdir().unwrap();
        let cas = std::sync::Arc::new(
            LocalCasStore::new(dir.path().join("cas")).await.unwrap(),
        );
        let mut log = WCommitLog::new(cas.clone(), "ch1".into());

        let c1 = log
            .commit(&ch(), &m(), &[env("e1", "hello")], "v1")
            .await
            .unwrap();
        let c2 = log
            .commit(&ch(), &m(), &[env("e1", "hello"), env("e2", "world")], "v2")
            .await
            .unwrap();

        let diff = w_diff(&c1, &c2, cas.as_ref()).await.unwrap();
        assert_eq!(diff.added_envelope_cids.len(), 1);
        assert_eq!(diff.removed_envelope_cids.len(), 0);
    }

    #[tokio::test]
    async fn test_add_new_kind() {
        let dir = tempfile::tempdir().unwrap();
        let cas = std::sync::Arc::new(
            LocalCasStore::new(dir.path().join("cas")).await.unwrap(),
        );
        let mut log = WCommitLog::new(cas.clone(), "ch1".into());

        let c1 = log
            .commit(&ch(), &m(), &[env("e1", "msg")], "v1")
            .await
            .unwrap();

        let mut reaction = env("r1", "thumbsup");
        reaction.kind = "reaction".into();
        let c2 = log
            .commit(&ch(), &m(), &[env("e1", "msg"), reaction], "v2")
            .await
            .unwrap();

        let diff = w_diff(&c1, &c2, cas.as_ref()).await.unwrap();
        assert!(diff.added_kinds.contains(&"reaction".to_string()));
    }

    #[tokio::test]
    async fn test_member_change() {
        let dir = tempfile::tempdir().unwrap();
        let cas = std::sync::Arc::new(
            LocalCasStore::new(dir.path().join("cas")).await.unwrap(),
        );
        let mut log = WCommitLog::new(cas.clone(), "ch1".into());

        let m1 = m();
        let c1 = log.commit(&ch(), &m1, &[env("e1", "hi")], "v1").await.unwrap();

        let mut m2 = m1.clone();
        m2.push(WMember {
            channel_id: "ch1".into(),
            did: "did:plc:bob".into(),
            role: MemberRole::Member,
            joined_at: "2026-03-17T01:00:00Z".into(),
        });
        let c2 = log.commit(&ch(), &m2, &[env("e1", "hi")], "v2").await.unwrap();

        let diff = w_diff(&c1, &c2, cas.as_ref()).await.unwrap();
        assert_eq!(diff.added_member_cids.len(), 1); // Bob added
    }
}
