//! Reply / thread continuity across the SMTP boundary (ADR-2605172200 §3.3).
//!
//! The bridge keeps a non-canonical `Message-ID ⇄ at-uri` map so threads survive the
//! openmail ⇄ SMTP round-trip:
//!   • outbound: synthesize a deterministic `Message-ID` from the record's at-uri so
//!     replies from the legacy world carry it back in `In-Reply-To`.
//!   • inbound: read `In-Reply-To` / `References`, look the at-uri back up, and set
//!     the openmail `replyTo` / `threadRoot`.
//! Losing the map degrades threading but never loses content (the record is canonical).

use std::collections::HashMap;

/// Synthesize the deterministic `Message-ID` for an openmail record's at-uri. The
/// rkey is embedded so the reverse lookup needs no table for freshly-sent mail.
pub fn synthesize_message_id(rkey: &str, mail_domain: &str) -> String {
    format!("<{rkey}@{mail_domain}>")
}

/// Resolution of an inbound legacy reply against the bridge map.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThreadResolution {
    /// at-uri of the message being replied to (from `In-Reply-To`), if known.
    pub reply_to: Option<String>,
    /// at-uri of the thread root (from the earliest known `References` entry).
    pub thread_root: Option<String>,
    /// True when nothing matched → a new thread starts.
    pub new_thread: bool,
}

/// Bidirectional, non-canonical `Message-ID ⇄ at-uri` store. The trait lets the
/// daemon back it with kotoba while tests use the in-memory impl.
pub trait BridgeThreadMap {
    fn record(&mut self, message_id: &str, at_uri: &str);
    fn at_uri_for(&self, message_id: &str) -> Option<String>;
    fn message_id_for(&self, at_uri: &str) -> Option<String>;
}

/// In-memory bidirectional map.
#[derive(Debug, Default)]
pub struct InMemoryThreadMap {
    by_mid: HashMap<String, String>,
    by_uri: HashMap<String, String>,
}

impl InMemoryThreadMap {
    pub fn new() -> Self {
        Self::default()
    }
}

impl BridgeThreadMap for InMemoryThreadMap {
    fn record(&mut self, message_id: &str, at_uri: &str) {
        self.by_mid.insert(message_id.to_string(), at_uri.to_string());
        self.by_uri.insert(at_uri.to_string(), message_id.to_string());
    }
    fn at_uri_for(&self, message_id: &str) -> Option<String> {
        self.by_mid.get(message_id).cloned()
    }
    fn message_id_for(&self, at_uri: &str) -> Option<String> {
        self.by_uri.get(at_uri).cloned()
    }
}

/// Resolve an inbound reply's threading from its `In-Reply-To` and `References`
/// headers against the bridge map. `references` should be ordered oldest→newest as
/// in RFC 5322. The thread root is the earliest reference we recognise (falling back
/// to the `In-Reply-To` target).
pub fn resolve_thread(
    in_reply_to: Option<&str>,
    references: &[String],
    map: &dyn BridgeThreadMap,
) -> ThreadResolution {
    let reply_to = in_reply_to.and_then(|mid| map.at_uri_for(&normalize_mid(mid)));

    let thread_root = references
        .iter()
        .find_map(|mid| map.at_uri_for(&normalize_mid(mid)))
        .or_else(|| reply_to.clone());

    let new_thread = reply_to.is_none() && thread_root.is_none();
    ThreadResolution { reply_to, thread_root, new_thread }
}

/// Normalise a Message-ID for lookup: trim whitespace; keep the angle brackets
/// (synthesized + stored IDs include them).
fn normalize_mid(mid: &str) -> String {
    mid.trim().to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn message_id_is_deterministic() {
        assert_eq!(
            synthesize_message_id("3l4k2m", "openmail.etzhayyim.com"),
            "<3l4k2m@openmail.etzhayyim.com>"
        );
    }

    #[test]
    fn map_round_trips_both_directions() {
        let mut m = InMemoryThreadMap::new();
        m.record("<mid1@x>", "at://did:web:e/app.openmail.message/rk1");
        assert_eq!(m.at_uri_for("<mid1@x>").as_deref(), Some("at://did:web:e/app.openmail.message/rk1"));
        assert_eq!(m.message_id_for("at://did:web:e/app.openmail.message/rk1").as_deref(), Some("<mid1@x>"));
    }

    #[test]
    fn reply_resolves_to_known_at_uri() {
        let mut m = InMemoryThreadMap::new();
        m.record("<root@x>", "at://e/rk-root");
        let r = resolve_thread(Some("<root@x>"), &[], &m);
        assert_eq!(r.reply_to.as_deref(), Some("at://e/rk-root"));
        assert!(!r.new_thread);
    }

    #[test]
    fn thread_root_taken_from_earliest_known_reference() {
        let mut m = InMemoryThreadMap::new();
        m.record("<root@x>", "at://e/rk-root");
        m.record("<mid2@x>", "at://e/rk-2");
        let refs = vec!["<root@x>".to_string(), "<mid2@x>".to_string()];
        let r = resolve_thread(Some("<mid2@x>"), &refs, &m);
        assert_eq!(r.reply_to.as_deref(), Some("at://e/rk-2"));
        assert_eq!(r.thread_root.as_deref(), Some("at://e/rk-root"));
    }

    #[test]
    fn unknown_reply_starts_new_thread() {
        let m = InMemoryThreadMap::new();
        let r = resolve_thread(Some("<stranger@gmail.com>"), &["<also@x>".to_string()], &m);
        assert!(r.new_thread);
        assert!(r.reply_to.is_none());
        assert!(r.thread_root.is_none());
    }

    #[test]
    fn whitespace_in_in_reply_to_is_tolerated() {
        let mut m = InMemoryThreadMap::new();
        m.record("<root@x>", "at://e/rk-root");
        let r = resolve_thread(Some("  <root@x>  "), &[], &m);
        assert_eq!(r.reply_to.as_deref(), Some("at://e/rk-root"));
    }

    #[test]
    fn thread_root_falls_back_to_reply_to_when_no_refs_known() {
        let mut m = InMemoryThreadMap::new();
        m.record("<root@x>", "at://e/rk-root");
        let r = resolve_thread(Some("<root@x>"), &["<unknown@y>".to_string()], &m);
        assert_eq!(r.thread_root.as_deref(), Some("at://e/rk-root"));
    }
}
