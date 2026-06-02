//! Outbound recipient classification (ADR-2605172200 §3.2).
//!
//! A native openmail message may address a mix of local members (DIDs — delivered
//! in-substrate, no SMTP) and external `smtp:` recipients (relayed out). This module
//! partitions the recipient set and groups the external ones by destination domain
//! so each MX gets one SMTP session. Pure + tested.

use std::collections::BTreeMap;

use crate::routing::{self, Recipient};

/// Where a single recipient should go.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Destination {
    /// A local member — deliver in-substrate to this DID (no SMTP).
    Local(String),
    /// An external mailbox — relay over SMTP. Carries the bare RFC 5322 address.
    External(String),
    /// Unusable address.
    Invalid(String),
}

/// Classify one recipient. Local domains resolve via [`routing::resolve_recipient`];
/// anything else with a well-formed `localpart@domain` is external.
pub fn classify(addr: &str) -> Destination {
    // Strip an optional `smtp:` / `mailto:` URI scheme used by openmail records.
    let bare = addr
        .trim()
        .strip_prefix("smtp:")
        .or_else(|| addr.trim().strip_prefix("mailto:"))
        .unwrap_or(addr.trim());

    match routing::resolve_recipient(bare) {
        Recipient::Did(did) => Destination::Local(did),
        Recipient::NotOurDomain(a) => {
            if is_well_formed(&a) {
                Destination::External(a)
            } else {
                Destination::Invalid(a)
            }
        }
        Recipient::NoSuchUser(a) => Destination::Invalid(a),
    }
}

/// Partition a recipient list into (local DIDs, external addresses, invalid).
pub fn partition(rcpts: &[String]) -> (Vec<String>, Vec<String>, Vec<String>) {
    let mut local = Vec::new();
    let mut external = Vec::new();
    let mut invalid = Vec::new();
    for r in rcpts {
        match classify(r) {
            Destination::Local(did) => local.push(did),
            Destination::External(addr) => external.push(addr),
            Destination::Invalid(addr) => invalid.push(addr),
        }
    }
    (local, external, invalid)
}

/// Group external recipients by their (lowercased) domain so each destination MX
/// receives a single SMTP session covering all its recipients.
pub fn group_by_domain(external: &[String]) -> BTreeMap<String, Vec<String>> {
    let mut map: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for addr in external {
        if let Some(at) = addr.rfind('@') {
            let domain = addr[at + 1..].to_ascii_lowercase();
            map.entry(domain).or_default().push(addr.clone());
        }
    }
    map
}

fn is_well_formed(addr: &str) -> bool {
    match addr.rfind('@') {
        Some(at) => {
            let (local, domain) = (&addr[..at], &addr[at + 1..]);
            !local.is_empty() && domain.contains('.') && !domain.starts_with('.') && !domain.ends_with('.')
        }
        None => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn local_member_classifies_to_did() {
        assert_eq!(
            classify("bob@etzhayyim.com"),
            Destination::Local("did:web:etzhayyim.com:actor:bob".to_string())
        );
    }

    #[test]
    fn external_recipient_classifies_to_external() {
        assert_eq!(
            classify("carol@yahoo.com"),
            Destination::External("carol@yahoo.com".to_string())
        );
    }

    #[test]
    fn smtp_uri_scheme_is_stripped() {
        assert_eq!(
            classify("smtp:dave@corp.example"),
            Destination::External("dave@corp.example".to_string())
        );
        assert_eq!(
            classify("mailto:erin@corp.example"),
            Destination::External("erin@corp.example".to_string())
        );
    }

    #[test]
    fn malformed_external_is_invalid() {
        assert_eq!(classify("nope@localhost"), Destination::Invalid("nope@localhost".into()));
        assert!(matches!(classify("garbage"), Destination::Invalid(_)));
    }

    #[test]
    fn partition_splits_three_ways() {
        let rcpts = vec![
            "bob@etzhayyim.com".to_string(),
            "carol@yahoo.com".to_string(),
            "smtp:dave@corp.example".to_string(),
            "garbage".to_string(),
        ];
        let (local, external, invalid) = partition(&rcpts);
        assert_eq!(local, vec!["did:web:etzhayyim.com:actor:bob"]);
        assert_eq!(external, vec!["carol@yahoo.com", "dave@corp.example"]);
        assert_eq!(invalid, vec!["garbage"]);
    }

    #[test]
    fn group_by_domain_batches_per_mx() {
        let external = vec![
            "a@yahoo.com".to_string(),
            "b@gmail.com".to_string(),
            "c@yahoo.com".to_string(),
        ];
        let groups = group_by_domain(&external);
        assert_eq!(groups.get("yahoo.com").unwrap(), &vec!["a@yahoo.com", "c@yahoo.com"]);
        assert_eq!(groups.get("gmail.com").unwrap(), &vec!["b@gmail.com"]);
    }

    #[test]
    fn group_by_domain_lowercases() {
        let external = vec!["a@YAHOO.com".to_string()];
        let groups = group_by_domain(&external);
        assert!(groups.contains_key("yahoo.com"));
    }
}
