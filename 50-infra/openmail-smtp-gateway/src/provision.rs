//! Per-member DKIM key provisioning + DNS publication (ADR-2606022800).
//!
//! Option (b) requires each member to publish their *public* DKIM keys in DNS under
//! `etzhayyim.com`. This module assembles the records to publish from a member's
//! public keys (the private keys never leave the member's ARK) and builds the
//! Cloudflare API request to create them. Pure — the actual HTTP call is the daemon
//! edge. With dual-signing a member publishes two selectors: ed25519 + rsa.

use serde_json::{json, Value};

use crate::dkim::{dns_record_name, txt_record, txt_record_rsa};

/// A member's DKIM selector pair under a domain.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MemberDkim {
    pub member: String,
    pub domain: String,
    pub ed25519_selector: String,
    pub rsa_selector: String,
}

/// A single DNS TXT record to publish.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DnsTxtRecord {
    /// Fully-qualified record name (`<selector>._domainkey.<domain>`).
    pub name: String,
    /// Record value (`v=DKIM1; k=...; p=...`).
    pub value: String,
}

/// Default TTL for published DKIM records (1h — short enough to rotate, long enough
/// to be cache-friendly).
pub const DEFAULT_TTL: u32 = 3600;

impl MemberDkim {
    /// Selector convention: `<member>-ed25519` / `<member>-rsa`. `member` is the
    /// handle/localpart; callers should pass an already-validated slug.
    pub fn new(member: impl Into<String>, domain: impl Into<String>) -> Self {
        let member = member.into();
        let domain = domain.into();
        Self {
            ed25519_selector: format!("{member}-ed25519"),
            rsa_selector: format!("{member}-rsa"),
            member,
            domain,
        }
    }

    /// The ed25519 record to publish, given the member's raw 32-byte public key (b64).
    pub fn ed25519_record(&self, public_key_b64: &str) -> DnsTxtRecord {
        DnsTxtRecord {
            name: dns_record_name(&self.ed25519_selector, &self.domain),
            value: txt_record(public_key_b64),
        }
    }

    /// The rsa record to publish, given the member's DER SubjectPublicKeyInfo (b64).
    pub fn rsa_record(&self, public_key_der_b64: &str) -> DnsTxtRecord {
        DnsTxtRecord {
            name: dns_record_name(&self.rsa_selector, &self.domain),
            value: txt_record_rsa(public_key_der_b64),
        }
    }

    /// Both records, ready to publish (the dual-signing requirement).
    pub fn records(&self, ed25519_pub_b64: &str, rsa_pub_der_b64: &str) -> Vec<DnsTxtRecord> {
        vec![
            self.ed25519_record(ed25519_pub_b64),
            self.rsa_record(rsa_pub_der_b64),
        ]
    }
}

/// Build the Cloudflare "create DNS record" request body for a TXT record.
/// POST to `https://api.cloudflare.com/client/v4/zones/<zone_id>/dns_records`.
pub fn cloudflare_create_txt(rec: &DnsTxtRecord, ttl: u32) -> Value {
    json!({
        "type": "TXT",
        "name": rec.name,
        "content": rec.value,
        "ttl": ttl,
        "comment": "openmail per-member DKIM (ADR-2606022800)",
    })
}

/// The Cloudflare API URL for creating records in a zone.
pub fn cloudflare_zone_url(zone_id: &str) -> String {
    format!("https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records")
}

/// One ready-to-issue Cloudflare API call.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CloudflareRequest {
    pub url: String,
    pub body: Value,
}

/// The ARK-enrollment hook's pure output: given a member's freshly-generated *public*
/// keys (the private keys stay in the member's ARK), produce the exact Cloudflare API
/// calls that publish both DKIM selectors. The daemon issues these over HTTP with the
/// CF token; this function holds no secret.
pub fn enrollment_requests(
    member: &str,
    domain: &str,
    zone_id: &str,
    ed25519_pub_b64: &str,
    rsa_pub_der_b64: &str,
    ttl: u32,
) -> Vec<CloudflareRequest> {
    let m = MemberDkim::new(member, domain);
    let url = cloudflare_zone_url(zone_id);
    m.records(ed25519_pub_b64, rsa_pub_der_b64)
        .iter()
        .map(|rec| CloudflareRequest {
            url: url.clone(),
            body: cloudflare_create_txt(rec, ttl),
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn alice() -> MemberDkim {
        MemberDkim::new("alice", "etzhayyim.com")
    }

    #[test]
    fn selectors_follow_convention() {
        let m = alice();
        assert_eq!(m.ed25519_selector, "alice-ed25519");
        assert_eq!(m.rsa_selector, "alice-rsa");
    }

    #[test]
    fn ed25519_record_name_and_value() {
        let rec = alice().ed25519_record("PUBKEYB64");
        assert_eq!(rec.name, "alice-ed25519._domainkey.etzhayyim.com");
        assert_eq!(rec.value, "v=DKIM1; k=ed25519; p=PUBKEYB64");
    }

    #[test]
    fn rsa_record_name_and_value() {
        let rec = alice().rsa_record("DERB64");
        assert_eq!(rec.name, "alice-rsa._domainkey.etzhayyim.com");
        assert_eq!(rec.value, "v=DKIM1; k=rsa; p=DERB64");
    }

    #[test]
    fn records_returns_both_for_dual_signing() {
        let recs = alice().records("ED", "RSA");
        assert_eq!(recs.len(), 2);
        assert!(recs[0].value.contains("k=ed25519"));
        assert!(recs[1].value.contains("k=rsa"));
    }

    #[test]
    fn cloudflare_request_is_well_formed() {
        let rec = alice().ed25519_record("PUB");
        let body = cloudflare_create_txt(&rec, DEFAULT_TTL);
        assert_eq!(body["type"], "TXT");
        assert_eq!(body["name"], "alice-ed25519._domainkey.etzhayyim.com");
        assert_eq!(body["content"], "v=DKIM1; k=ed25519; p=PUB");
        assert_eq!(body["ttl"], 3600);
    }

    #[test]
    fn cloudflare_url_targets_zone() {
        assert_eq!(
            cloudflare_zone_url("abc123"),
            "https://api.cloudflare.com/client/v4/zones/abc123/dns_records"
        );
    }

    /// The provisioning record publishes only PUBLIC material — no private key field
    /// anywhere in the payload (option-b invariant).
    #[test]
    fn provisioning_carries_no_private_material() {
        let body = cloudflare_create_txt(&alice().rsa_record("DER"), DEFAULT_TTL).to_string();
        assert!(!body.to_lowercase().contains("private"));
        assert!(body.contains("p=DER"));
    }

    #[test]
    fn enrollment_emits_two_cloudflare_calls() {
        let reqs = enrollment_requests("alice", "etzhayyim.com", "zone123", "EDPUB", "RSADER", DEFAULT_TTL);
        assert_eq!(reqs.len(), 2);
        for r in &reqs {
            assert_eq!(r.url, "https://api.cloudflare.com/client/v4/zones/zone123/dns_records");
            assert_eq!(r.body["type"], "TXT");
        }
        assert!(reqs[0].body["content"].as_str().unwrap().contains("k=ed25519"));
        assert!(reqs[0].body["name"].as_str().unwrap().starts_with("alice-ed25519._domainkey"));
        assert!(reqs[1].body["content"].as_str().unwrap().contains("k=rsa"));
    }

    #[test]
    fn enrollment_batch_has_no_private_material() {
        let reqs = enrollment_requests("alice", "etzhayyim.com", "z", "EDPUB", "RSADER", DEFAULT_TTL);
        for r in &reqs {
            assert!(!r.body.to_string().to_lowercase().contains("private"));
        }
    }
}
