//! Channel state management — Cypher graph + MDAG backed.
//!
//! No KV buckets. All state lives in the Cypher graph (yata-cypher/yata-engine).
//! MDAG provides content-addressed commit chain for federation sync.
//!
//! Graph schema:
//!   (:WChannel {channel_id, org_id, name, description, kind, encryption_mode, creator_did, member_count, mdag_root_cid, created_at})
//!   (:WMember {did, role, joined_at})-[:MEMBER_OF]->(:WChannel)
//!   (:WEnvelope {id, kind, rkey, sender_did, content_type, encryption, mdag_cid, created_at})-[:IN_CHANNEL]->(:WChannel)
//!   (:WEnvelope)-[:REPLY_TO]->(:WEnvelope)

use std::sync::Arc;
use yata_core::Blake3Hash;
use yata_cas::CasStore;

use crate::commit::WCommitLog;
use crate::error::{Result, WProtoError};
use crate::types::*;

/// Cypher query executor trait — implemented by magatama-host via yata-engine.
#[async_trait::async_trait]
pub trait CypherExecutor: Send + Sync {
    /// Execute a Cypher mutation (MERGE/CREATE/DELETE/SET).
    async fn exec(&self, cypher: &str, params: &[(String, String)]) -> Result<()>;
    /// Execute a Cypher query, return rows as JSON maps.
    async fn query(&self, cypher: &str, params: &[(String, String)]) -> Result<Vec<Vec<(String, String)>>>;
}

/// Channel store — Cypher graph + MDAG.
pub struct ChannelStore {
    cypher: Arc<dyn CypherExecutor>,
    cas: Arc<dyn CasStore>,
}

impl ChannelStore {
    pub fn new(cypher: Arc<dyn CypherExecutor>, cas: Arc<dyn CasStore>) -> Self {
        Self { cypher, cas }
    }

    // ── Channel CRUD ──────────────────────────────────────

    pub async fn create_channel(&self, ch: &WChannel) -> Result<()> {
        self.cypher.exec(
            "MERGE (c:WChannel {channel_id: $id, org_id: $org}) \
             SET c.name = $name, c.description = $desc, c.kind = $kind, \
                 c.encryption_mode = $enc, c.creator_did = $creator, \
                 c.member_count = $mc, c.mdag_root_cid = $mdag, c.created_at = $ts",
            &p([
                ("id", &ch.channel_id), ("org", &ch.org_id),
                ("name", &ch.name), ("desc", &ch.description),
                ("kind", &format!("{:?}", ch.kind)), ("enc", ch.encryption_mode.as_str()),
                ("creator", &ch.creator_did), ("mc", &ch.member_count.to_string()),
                ("mdag", &ch.mdag_root_cid.as_ref().map(|c| c.hex()).unwrap_or_default()),
                ("ts", &ch.created_at),
            ]),
        ).await
    }

    pub async fn get_channel(&self, org_id: &str, channel_id: &str) -> Result<Option<WChannel>> {
        let rows = self.cypher.query(
            "MATCH (c:WChannel {channel_id: $id, org_id: $org}) \
             RETURN c.channel_id, c.org_id, c.name, c.description, c.kind, \
                    c.encryption_mode, c.creator_did, c.member_count, \
                    c.at_uri, c.mdag_root_cid, c.created_at",
            &p([("id", channel_id), ("org", org_id)]),
        ).await?;

        if rows.is_empty() { return Ok(None); }
        Ok(Some(row_to_channel(&rows[0])))
    }

    pub async fn update_channel(&self, ch: &WChannel) -> Result<()> {
        self.create_channel(ch).await // MERGE = upsert
    }

    pub async fn list_channels(&self, org_id: &str, member_did: &str) -> Result<Vec<WChannel>> {
        let rows = self.cypher.query(
            "MATCH (m:WMember {did: $did})-[:MEMBER_OF]->(c:WChannel {org_id: $org}) \
             RETURN c.channel_id, c.org_id, c.name, c.description, c.kind, \
                    c.encryption_mode, c.creator_did, c.member_count, \
                    c.at_uri, c.mdag_root_cid, c.created_at \
             ORDER BY c.created_at DESC",
            &p([("did", member_did), ("org", org_id)]),
        ).await?;

        Ok(rows.iter().map(|r| row_to_channel(r)).collect())
    }

    // ── Membership ────────────────────────────────────────

    pub async fn add_member(&self, member: &WMember, org_id: &str) -> Result<()> {
        self.cypher.exec(
            "MATCH (c:WChannel {channel_id: $ch, org_id: $org}) \
             MERGE (m:WMember {did: $did, org_id: $org}) \
             SET m.role = $role, m.joined_at = $ts \
             MERGE (m)-[:MEMBER_OF]->(c)",
            &p([
                ("ch", &member.channel_id), ("org", org_id),
                ("did", &member.did), ("role", &format!("{:?}", member.role)),
                ("ts", &member.joined_at),
            ]),
        ).await
    }

    pub async fn remove_member(&self, org_id: &str, channel_id: &str, did: &str) -> Result<()> {
        self.cypher.exec(
            "MATCH (m:WMember {did: $did, org_id: $org})-[r:MEMBER_OF]->(c:WChannel {channel_id: $ch}) DELETE r",
            &p([("did", did), ("org", org_id), ("ch", channel_id)]),
        ).await
    }

    pub async fn list_members(&self, org_id: &str, channel_id: &str) -> Result<Vec<WMember>> {
        let rows = self.cypher.query(
            "MATCH (m:WMember)-[:MEMBER_OF]->(c:WChannel {channel_id: $ch, org_id: $org}) \
             RETURN m.did, m.role, m.joined_at, c.channel_id",
            &p([("ch", channel_id), ("org", org_id)]),
        ).await?;

        Ok(rows.iter().map(|r| row_to_member(r, channel_id)).collect())
    }

    // ── Envelope persistence ──────────────────────────────

    pub async fn store_envelope(&self, env: &WEnvelope) -> Result<()> {
        self.cypher.exec(
            "MATCH (c:WChannel {channel_id: $ch, org_id: $org}) \
             MERGE (e:WEnvelope {id: $id, org_id: $org}) \
             SET e.kind = $kind, e.rkey = $rkey, e.sender_did = $sender, \
                 e.content_type = $ct, e.encryption = $enc, \
                 e.mdag_cid = $cid, e.created_at = $ts, \
                 e.thread_id = $thread, e.reply_to = $reply \
             MERGE (e)-[:IN_CHANNEL]->(c)",
            &p([
                ("id", &env.id), ("org", &env.org_id), ("ch", &env.channel_id),
                ("kind", &env.kind), ("rkey", &env.rkey), ("sender", &env.sender_did),
                ("ct", &env.content_type), ("enc", env.encryption.as_str()),
                ("cid", &env.cid.as_ref().map(|c| c.hex()).unwrap_or_default()),
                ("ts", &env.created_at),
                ("thread", &env.thread_id), ("reply", &env.reply_to),
            ]),
        ).await?;

        // REPLY_TO edge for thread traversal
        if !env.reply_to.is_empty() {
            self.cypher.exec(
                "MATCH (e:WEnvelope {id: $id}), (p:WEnvelope {rkey: $parent}) \
                 MERGE (e)-[:REPLY_TO]->(p)",
                &p([("id", &env.id), ("parent", &env.reply_to)]),
            ).await?;
        }

        Ok(())
    }

    pub async fn list_envelopes(
        &self,
        org_id: &str,
        channel_id: &str,
        limit: usize,
        before_rkey: Option<&str>,
    ) -> Result<Vec<WEnvelope>> {
        let cypher = if let Some(_before) = before_rkey {
            format!(
                "MATCH (e:WEnvelope)-[:IN_CHANNEL]->(c:WChannel {{channel_id: $ch, org_id: $org}}) \
                 WHERE e.rkey < $before \
                 RETURN e.id, e.kind, e.rkey, e.sender_did, e.content_type, e.encryption, \
                        e.mdag_cid, e.created_at, e.thread_id, e.reply_to, c.channel_id, e.org_id \
                 ORDER BY e.rkey DESC LIMIT {limit}"
            )
        } else {
            format!(
                "MATCH (e:WEnvelope)-[:IN_CHANNEL]->(c:WChannel {{channel_id: $ch, org_id: $org}}) \
                 RETURN e.id, e.kind, e.rkey, e.sender_did, e.content_type, e.encryption, \
                        e.mdag_cid, e.created_at, e.thread_id, e.reply_to, c.channel_id, e.org_id \
                 ORDER BY e.rkey DESC LIMIT {limit}"
            )
        };

        let mut params = vec![
            ("ch".into(), json_str(channel_id)),
            ("org".into(), json_str(org_id)),
        ];
        if let Some(before) = before_rkey {
            params.push(("before".into(), json_str(before)));
        }

        let rows = self.cypher.query(&cypher, &params).await?;

        let mut envelopes: Vec<WEnvelope> = rows.iter().map(|r| row_to_envelope(r)).collect();
        envelopes.reverse(); // chronological order
        Ok(envelopes)
    }

    pub async fn get_thread(&self, org_id: &str, channel_id: &str, root_rkey: &str) -> Result<Vec<WEnvelope>> {
        let rows = self.cypher.query(
            "MATCH (root:WEnvelope {rkey: $rkey})-[:IN_CHANNEL]->(c:WChannel {channel_id: $ch, org_id: $org}) \
             OPTIONAL MATCH (reply:WEnvelope)-[:REPLY_TO*]->(root) \
             WITH collect(root) + collect(reply) AS all \
             UNWIND all AS e \
             RETURN DISTINCT e.id, e.kind, e.rkey, e.sender_did, e.content_type, e.encryption, \
                    e.mdag_cid, e.created_at, e.thread_id, e.reply_to, $ch AS channel_id, e.org_id \
             ORDER BY e.rkey ASC",
            &p([("rkey", root_rkey), ("ch", channel_id), ("org", org_id)]),
        ).await?;

        Ok(rows.iter().map(|r| row_to_envelope(r)).collect())
    }

    pub async fn search(&self, org_id: &str, _query: &str, channel_id: Option<&str>, limit: usize) -> Result<Vec<WEnvelope>> {
        let cypher = if let Some(_ch) = channel_id {
            format!(
                "MATCH (e:WEnvelope)-[:IN_CHANNEL]->(c:WChannel {{channel_id: $ch, org_id: $org}}) \
                 WHERE e.kind = 'message' \
                 RETURN e.id, e.kind, e.rkey, e.sender_did, e.content_type, e.encryption, \
                        e.mdag_cid, e.created_at, e.thread_id, e.reply_to, c.channel_id, e.org_id \
                 ORDER BY e.created_at DESC LIMIT {limit}"
            )
        } else {
            format!(
                "MATCH (e:WEnvelope)-[:IN_CHANNEL]->(c:WChannel {{org_id: $org}}) \
                 WHERE e.kind = 'message' \
                 RETURN e.id, e.kind, e.rkey, e.sender_did, e.content_type, e.encryption, \
                        e.mdag_cid, e.created_at, e.thread_id, e.reply_to, c.channel_id, e.org_id \
                 ORDER BY e.created_at DESC LIMIT {limit}"
            )
        };

        let mut params = vec![("org".into(), json_str(org_id))];
        if let Some(ch) = channel_id {
            params.push(("ch".into(), json_str(ch)));
        }

        let rows = self.cypher.query(&cypher, &params).await?;
        Ok(rows.iter().map(|r| row_to_envelope(r)).collect())
    }

    // ── Unread (graph-based) ──────────────────────────────

    pub async fn mark_read(&self, org_id: &str, channel_id: &str, did: &str, last_rkey: &str) -> Result<()> {
        self.cypher.exec(
            "MATCH (m:WMember {did: $did, org_id: $org})-[:MEMBER_OF]->(c:WChannel {channel_id: $ch}) \
             SET m.last_read_rkey = $rkey",
            &p([("did", did), ("org", org_id), ("ch", channel_id), ("rkey", last_rkey)]),
        ).await
    }

    pub async fn get_unread(&self, org_id: &str, did: &str) -> Result<Vec<(String, i32)>> {
        let rows = self.cypher.query(
            "MATCH (m:WMember {did: $did, org_id: $org})-[:MEMBER_OF]->(c:WChannel) \
             OPTIONAL MATCH (e:WEnvelope)-[:IN_CHANNEL]->(c) WHERE e.rkey > coalesce(m.last_read_rkey, '') \
             RETURN c.channel_id, count(e) AS unread",
            &p([("did", did), ("org", org_id)]),
        ).await?;

        let mut unread = Vec::new();
        for row in &rows {
            let ch_id = col_str(row, "c.channel_id");
            let count = col_str(row, "unread").parse::<i32>().unwrap_or(0);
            if count > 0 {
                unread.push((ch_id, count));
            }
        }
        Ok(unread)
    }

    // ── A2A identity / capability (graph-backed) ────────

    /// Resolve an actor by nanoid from the ActorCard graph.
    pub async fn resolve_actor(&self, nanoid: &str) -> Result<Option<Vec<(String, String)>>> {
        let rows = self
            .cypher
            .query(
                "MATCH (a:ActorCard {nanoid: $nanoid}) \
                 RETURN a.nanoid, a.name, a.description, a.service_user_id, \
                        a.addresses, a.tools, a.protocols, a.capabilities_json",
                &p([("nanoid", nanoid)]),
            )
            .await?;
        if rows.is_empty() {
            Ok(None)
        } else {
            Ok(Some(rows.into_iter().next().unwrap()))
        }
    }

    /// Discover capabilities by tag from the ActorCapability graph.
    pub async fn discover_capability(
        &self,
        tag: &str,
        limit: usize,
    ) -> Result<Vec<Vec<(String, String)>>> {
        self.cypher
            .query(
                &format!(
                    "MATCH (a:ActorCard)-[:PROVIDES]->(c:ActorCapability) \
                     WHERE c.tags CONTAINS $tag \
                     RETURN a.nanoid, c.id, c.description, c.tags, c.phase, c.status \
                     LIMIT {limit}"
                ),
                &p([("tag", tag)]),
            )
            .await
    }

    // ── MDAG commit ───────────────────────────────────────

    pub async fn commit_channel(
        &self,
        org_id: &str,
        channel_id: &str,
        message: &str,
    ) -> Result<Blake3Hash> {
        let channel = self
            .get_channel(org_id, channel_id)
            .await?
            .ok_or_else(|| WProtoError::ChannelNotFound(channel_id.into()))?;

        let members = self.list_members(org_id, channel_id).await?;
        let envelopes = self.list_envelopes(org_id, channel_id, 10000, None).await?;

        let mut log = if let Some(root_cid) = &channel.mdag_root_cid {
            WCommitLog::with_head(self.cas.clone(), channel_id.into(), root_cid.clone())
        } else {
            WCommitLog::new(self.cas.clone(), channel_id.into())
        };

        let root_cid = log.commit(&channel, &members, &envelopes, message).await?;

        // Update graph with new root CID
        self.cypher.exec(
            "MATCH (c:WChannel {channel_id: $ch, org_id: $org}) SET c.mdag_root_cid = $cid",
            &p([("ch", channel_id), ("org", org_id), ("cid", &root_cid.hex())]),
        ).await?;

        Ok(root_cid)
    }
}

// ── Helpers ──────────────────────────────────────────────────

fn p<const N: usize>(pairs: [(&str, &str); N]) -> Vec<(String, String)> {
    pairs.iter().map(|(k, v)| (k.to_string(), json_str(v))).collect()
}

fn json_str(s: &str) -> String {
    serde_json::to_string(s).unwrap_or_else(|_| format!("\"{}\"", s))
}

fn col_str(row: &[(String, String)], name: &str) -> String {
    row.iter()
        .find(|(k, _)| k == name)
        .map(|(_, v)| {
            // Strip JSON quotes if present
            v.trim_matches('"').to_string()
        })
        .unwrap_or_default()
}

fn row_to_channel(row: &[(String, String)]) -> WChannel {
    WChannel {
        channel_id: col_str(row, "c.channel_id"),
        org_id: col_str(row, "c.org_id"),
        name: col_str(row, "c.name"),
        description: col_str(row, "c.description"),
        kind: parse_channel_kind(&col_str(row, "c.kind")),
        encryption_mode: parse_encryption(&col_str(row, "c.encryption_mode")),
        creator_did: col_str(row, "c.creator_did"),
        member_count: col_str(row, "c.member_count").parse().unwrap_or(0),
        at_uri: col_str(row, "c.at_uri"),
        created_at: col_str(row, "c.created_at"),
        mdag_root_cid: {
            let s = col_str(row, "c.mdag_root_cid");
            if s.is_empty() { None } else { Some(blake3_from_hex(&s)) }
        },
    }
}

fn row_to_member(row: &[(String, String)], channel_id: &str) -> WMember {
    WMember {
        channel_id: channel_id.into(),
        did: col_str(row, "m.did"),
        role: parse_member_role(&col_str(row, "m.role")),
        joined_at: col_str(row, "m.joined_at"),
    }
}

fn row_to_envelope(row: &[(String, String)]) -> WEnvelope {
    WEnvelope {
        id: col_str(row, "e.id"),
        kind: col_str(row, "e.kind"),
        cid: {
            let s = col_str(row, "e.mdag_cid");
            if s.is_empty() { None } else { Some(blake3_from_hex(&s)) }
        },
        at_uri: String::new(),
        at_cid: String::new(),
        rkey: col_str(row, "e.rkey"),
        sender_did: col_str(row, "e.sender_did"),
        org_id: col_str(row, "e.org_id"),
        channel_id: col_str(row, "channel_id"),
        thread_id: col_str(row, "e.thread_id"),
        reply_to: col_str(row, "e.reply_to"),
        payload: Vec::new(), // payload stored in MDAG CAS, not graph
        content_type: col_str(row, "e.content_type"),
        encryption: parse_encryption(&col_str(row, "e.encryption")),
        causation_id: String::new(),
        correlation_id: String::new(),
        created_at: col_str(row, "e.created_at"),
    }
}

fn parse_channel_kind(s: &str) -> ChannelKind {
    match s {
        "Public" | "public" => ChannelKind::Public,
        "Private" | "private" => ChannelKind::Private,
        "Direct" | "direct" => ChannelKind::Direct,
        "GroupDm" | "group-dm" => ChannelKind::GroupDm,
        "Bot" | "bot" => ChannelKind::Bot,
        "A2a" | "a2a" => ChannelKind::A2a,
        _ => ChannelKind::Public,
    }
}

fn parse_member_role(s: &str) -> MemberRole {
    match s {
        "Owner" | "owner" => MemberRole::Owner,
        "Admin" | "admin" => MemberRole::Admin,
        _ => MemberRole::Member,
    }
}

fn blake3_from_hex(s: &str) -> Blake3Hash {
    let mut bytes = [0u8; 32];
    for (i, chunk) in s.as_bytes().chunks(2).enumerate() {
        if i >= 32 { break; }
        let hi = hex_nibble(chunk[0]);
        let lo = if chunk.len() > 1 { hex_nibble(chunk[1]) } else { 0 };
        bytes[i] = (hi << 4) | lo;
    }
    Blake3Hash(bytes)
}

fn hex_nibble(c: u8) -> u8 {
    match c {
        b'0'..=b'9' => c - b'0',
        b'a'..=b'f' => c - b'a' + 10,
        b'A'..=b'F' => c - b'A' + 10,
        _ => 0,
    }
}

fn parse_encryption(s: &str) -> EncryptionState {
    match s {
        "signal-1to1" | "Signal1to1" => EncryptionState::Signal1to1,
        "signal-group" | "SignalGroup" => EncryptionState::SignalGroup,
        "client-encrypted" | "ClientEncrypted" => EncryptionState::ClientEncrypted,
        _ => EncryptionState::Plaintext,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;
    use std::sync::Mutex;
    use yata_cas::LocalCasStore;

    /// In-memory CypherExecutor that stores nodes and supports basic queries.
    struct InMemoryCypher {
        channels: Mutex<Vec<WChannel>>,
        members: Mutex<Vec<WMember>>,
        envelopes: Mutex<Vec<WEnvelope>>,
    }

    impl InMemoryCypher {
        fn new() -> Self {
            Self {
                channels: Mutex::new(Vec::new()),
                members: Mutex::new(Vec::new()),
                envelopes: Mutex::new(Vec::new()),
            }
        }
    }

    #[async_trait::async_trait]
    impl CypherExecutor for InMemoryCypher {
        async fn exec(&self, cypher: &str, params: &[(String, String)]) -> Result<()> {
            let map: HashMap<&str, &str> = params
                .iter()
                .map(|(k, v)| (k.as_str(), v.trim_matches('"')))
                .collect();

            if cypher.contains("MERGE (c:WChannel") {
                let mut channels = self.channels.lock().unwrap();
                let ch = WChannel {
                    channel_id: map.get("id").unwrap_or(&"").to_string(),
                    org_id: map.get("org").unwrap_or(&"").to_string(),
                    name: map.get("name").unwrap_or(&"").to_string(),
                    description: map.get("desc").unwrap_or(&"").to_string(),
                    kind: parse_channel_kind(map.get("kind").unwrap_or(&"Public")),
                    encryption_mode: parse_encryption(map.get("enc").unwrap_or(&"plaintext")),
                    creator_did: map.get("creator").unwrap_or(&"").to_string(),
                    member_count: map.get("mc").and_then(|v| v.parse().ok()).unwrap_or(0),
                    at_uri: String::new(),
                    created_at: map.get("ts").unwrap_or(&"").to_string(),
                    mdag_root_cid: None,
                };
                // Upsert
                channels.retain(|c| !(c.channel_id == ch.channel_id && c.org_id == ch.org_id));
                channels.push(ch);
            } else if cypher.contains("MERGE (m:WMember") {
                let mut members = self.members.lock().unwrap();
                let m = WMember {
                    channel_id: map.get("ch").unwrap_or(&"").to_string(),
                    did: map.get("did").unwrap_or(&"").to_string(),
                    role: parse_member_role(map.get("role").unwrap_or(&"Member")),
                    joined_at: map.get("ts").unwrap_or(&"").to_string(),
                };
                members.push(m);
            } else if cypher.contains("MERGE (e:WEnvelope") {
                let mut envelopes = self.envelopes.lock().unwrap();
                let env = WEnvelope {
                    id: map.get("id").unwrap_or(&"").to_string(),
                    kind: map.get("kind").unwrap_or(&"message").to_string(),
                    cid: None,
                    at_uri: String::new(),
                    at_cid: String::new(),
                    rkey: map.get("rkey").unwrap_or(&"").to_string(),
                    sender_did: map.get("sender").unwrap_or(&"").to_string(),
                    org_id: map.get("org").unwrap_or(&"").to_string(),
                    channel_id: map.get("ch").unwrap_or(&"").to_string(),
                    thread_id: map.get("thread").unwrap_or(&"").to_string(),
                    reply_to: map.get("reply").unwrap_or(&"").to_string(),
                    payload: Vec::new(),
                    content_type: map.get("ct").unwrap_or(&"text/plain").to_string(),
                    encryption: parse_encryption(map.get("enc").unwrap_or(&"plaintext")),
                    causation_id: String::new(),
                    correlation_id: String::new(),
                    created_at: map.get("ts").unwrap_or(&"").to_string(),
                };
                envelopes.push(env);
            }
            Ok(())
        }

        async fn query(
            &self,
            cypher: &str,
            params: &[(String, String)],
        ) -> Result<Vec<Vec<(String, String)>>> {
            let map: HashMap<&str, &str> = params
                .iter()
                .map(|(k, v)| (k.as_str(), v.trim_matches('"')))
                .collect();

            if cypher.contains("MATCH (c:WChannel {channel_id:") {
                let channels = self.channels.lock().unwrap();
                let ch_id = map.get("id").unwrap_or(&"");
                let org = map.get("org").unwrap_or(&"");
                if let Some(ch) = channels.iter().find(|c| c.channel_id == *ch_id && c.org_id == *org) {
                    return Ok(vec![vec![
                        ("c.channel_id".into(), ch.channel_id.clone()),
                        ("c.org_id".into(), ch.org_id.clone()),
                        ("c.name".into(), ch.name.clone()),
                        ("c.description".into(), ch.description.clone()),
                        ("c.kind".into(), format!("{:?}", ch.kind)),
                        ("c.encryption_mode".into(), ch.encryption_mode.as_str().into()),
                        ("c.creator_did".into(), ch.creator_did.clone()),
                        ("c.member_count".into(), ch.member_count.to_string()),
                        ("c.at_uri".into(), ch.at_uri.clone()),
                        ("c.mdag_root_cid".into(), String::new()),
                        ("c.created_at".into(), ch.created_at.clone()),
                    ]]);
                }
                return Ok(vec![]);
            }

            if cypher.contains("MATCH (m:WMember") && cypher.contains("MEMBER_OF") {
                let members = self.members.lock().unwrap();
                let ch_id = map.get("ch").unwrap_or(&"");
                let rows: Vec<Vec<(String, String)>> = members
                    .iter()
                    .filter(|m| m.channel_id == *ch_id)
                    .map(|m| {
                        vec![
                            ("m.did".into(), m.did.clone()),
                            ("m.role".into(), format!("{:?}", m.role)),
                            ("m.joined_at".into(), m.joined_at.clone()),
                            ("c.channel_id".into(), m.channel_id.clone()),
                        ]
                    })
                    .collect();
                return Ok(rows);
            }

            Ok(vec![])
        }
    }

    #[tokio::test]
    async fn test_create_and_get_channel() {
        let dir = tempfile::tempdir().unwrap();
        let cas = Arc::new(LocalCasStore::new(dir.path().join("cas")).await.unwrap());
        let cypher: Arc<dyn CypherExecutor> = Arc::new(InMemoryCypher::new());
        let store = ChannelStore::new(cypher, cas);

        let ch = WChannel {
            channel_id: "ch1".into(),
            org_id: "org1".into(),
            name: "general".into(),
            description: "test channel".into(),
            kind: ChannelKind::Public,
            encryption_mode: EncryptionState::Plaintext,
            creator_did: "did:plc:alice".into(),
            member_count: 1,
            at_uri: String::new(),
            created_at: "2026-03-17T00:00:00Z".into(),
            mdag_root_cid: None,
        };

        store.create_channel(&ch).await.unwrap();
        let loaded = store.get_channel("org1", "ch1").await.unwrap();
        assert!(loaded.is_some());
        let loaded = loaded.unwrap();
        assert_eq!(loaded.name, "general");
        assert_eq!(loaded.creator_did, "did:plc:alice");
    }

    #[tokio::test]
    async fn test_add_and_list_members() {
        let dir = tempfile::tempdir().unwrap();
        let cas = Arc::new(LocalCasStore::new(dir.path().join("cas")).await.unwrap());
        let cypher: Arc<dyn CypherExecutor> = Arc::new(InMemoryCypher::new());
        let store = ChannelStore::new(cypher, cas);

        // Create channel first
        let ch = WChannel {
            channel_id: "ch1".into(),
            org_id: "org1".into(),
            name: "test".into(),
            description: "".into(),
            kind: ChannelKind::Public,
            encryption_mode: EncryptionState::Plaintext,
            creator_did: "did:plc:alice".into(),
            member_count: 0,
            at_uri: String::new(),
            created_at: "2026-03-17T00:00:00Z".into(),
            mdag_root_cid: None,
        };
        store.create_channel(&ch).await.unwrap();

        // Add members
        let m1 = WMember {
            channel_id: "ch1".into(),
            did: "did:plc:alice".into(),
            role: MemberRole::Owner,
            joined_at: "2026-03-17T00:00:00Z".into(),
        };
        let m2 = WMember {
            channel_id: "ch1".into(),
            did: "did:plc:bob".into(),
            role: MemberRole::Member,
            joined_at: "2026-03-17T00:01:00Z".into(),
        };
        store.add_member(&m1, "org1").await.unwrap();
        store.add_member(&m2, "org1").await.unwrap();

        let members = store.list_members("org1", "ch1").await.unwrap();
        assert_eq!(members.len(), 2);
    }

    #[tokio::test]
    async fn test_store_envelope() {
        let dir = tempfile::tempdir().unwrap();
        let cas = Arc::new(LocalCasStore::new(dir.path().join("cas")).await.unwrap());
        let cypher: Arc<dyn CypherExecutor> = Arc::new(InMemoryCypher::new());
        let store = ChannelStore::new(cypher, cas);

        let ch = WChannel {
            channel_id: "ch1".into(),
            org_id: "org1".into(),
            name: "test".into(),
            description: "".into(),
            kind: ChannelKind::Public,
            encryption_mode: EncryptionState::Plaintext,
            creator_did: "did:plc:alice".into(),
            member_count: 1,
            at_uri: String::new(),
            created_at: "2026-03-17T00:00:00Z".into(),
            mdag_root_cid: None,
        };
        store.create_channel(&ch).await.unwrap();

        let env = WEnvelope {
            id: "e1".into(),
            kind: "message".into(),
            cid: None,
            at_uri: String::new(),
            at_cid: String::new(),
            rkey: "r001".into(),
            sender_did: "did:plc:alice".into(),
            org_id: "org1".into(),
            channel_id: "ch1".into(),
            thread_id: String::new(),
            reply_to: String::new(),
            payload: b"hello".to_vec(),
            content_type: "text/plain".into(),
            encryption: EncryptionState::Plaintext,
            causation_id: String::new(),
            correlation_id: String::new(),
            created_at: "2026-03-17T12:00:00Z".into(),
        };

        store.store_envelope(&env).await.unwrap();
    }

    #[tokio::test]
    async fn test_parse_helpers() {
        assert_eq!(parse_channel_kind("Public"), ChannelKind::Public);
        assert_eq!(parse_channel_kind("direct"), ChannelKind::Direct);
        assert_eq!(parse_channel_kind("a2a"), ChannelKind::A2a);
        assert_eq!(parse_channel_kind("unknown"), ChannelKind::Public);

        assert_eq!(parse_member_role("Owner"), MemberRole::Owner);
        assert_eq!(parse_member_role("admin"), MemberRole::Admin);
        assert_eq!(parse_member_role("xyz"), MemberRole::Member);

        assert_eq!(parse_encryption("plaintext"), EncryptionState::Plaintext);
        assert_eq!(parse_encryption("signal-1to1"), EncryptionState::Signal1to1);
        assert_eq!(parse_encryption("SignalGroup"), EncryptionState::SignalGroup);
    }

    #[tokio::test]
    async fn test_col_str_and_json_str() {
        let row = vec![
            ("name".into(), "\"hello\"".into()),
            ("count".into(), "42".into()),
        ];
        assert_eq!(col_str(&row, "name"), "hello");
        assert_eq!(col_str(&row, "count"), "42");
        assert_eq!(col_str(&row, "missing"), "");

        let s = json_str("test value");
        assert!(s.starts_with('"'));
        assert!(s.ends_with('"'));
    }
}
