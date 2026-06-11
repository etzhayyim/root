//! Recipient address → DID resolution (ADR-2605172200 §3.4).
//!
//! Inbound mail names a recipient by RFC 5322 address; the gateway must turn that
//! into the DID whose kotoba inbox graph receives the message (`email.ingest`'s
//! `owner_did`). Only addresses in our own domain space are accepted — the gateway
//! is an MX for `etzhayyim.com`, not an open relay.
//!
//! Two forms are supported in R0:
//!   • `<localpart>@etzhayyim.com`           → `did:web:etzhayyim.com:actor:<localpart>`
//!   • `_did_<base32-of-did>@etzhayyim.com`  → the embedded DID verbatim (handle-less fallback)
//!
//! Handle-subdomain delegation (`x@alice.etzhayyim.com`) and real handle→DID
//! resolution are deferred (documented in README) so the resolver stays a pure,
//! offline, fully-tested function.

/// The apex domain this gateway is authoritative for.
pub const APEX_DOMAIN: &str = "etzhayyim.com";
/// Localpart prefix for the address-by-DID fallback.
pub const DID_LOCALPART_PREFIX: &str = "_did_";

/// Outcome of resolving an inbound recipient address.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Recipient {
    /// Deliver to this DID's inbox graph.
    Did(String),
    /// Address is in our domain but names no known mailbox → 550 5.1.1.
    NoSuchUser(String),
    /// Address is not in a domain we serve → 550 5.7.1 (relay denied).
    NotOurDomain(String),
}

/// Resolve an inbound `RCPT TO` address to a delivery target.
pub fn resolve_recipient(addr: &str) -> Recipient {
    let addr = addr.trim();
    let Some((localpart, domain)) = split_address(addr) else {
        return Recipient::NoSuchUser(addr.to_string());
    };
    let domain = domain.to_ascii_lowercase();

    if domain != APEX_DOMAIN {
        return Recipient::NotOurDomain(addr.to_string());
    }

    // Address-by-DID fallback: `_did_<base32>@etzhayyim.com`.
    if let Some(b32) = localpart.strip_prefix(DID_LOCALPART_PREFIX) {
        return match base32_decode(b32).and_then(|bytes| String::from_utf8(bytes).ok()) {
            Some(did) if did.starts_with("did:") => Recipient::Did(did),
            _ => Recipient::NoSuchUser(addr.to_string()),
        };
    }

    if !is_valid_localpart(localpart) {
        return Recipient::NoSuchUser(addr.to_string());
    }
    Recipient::Did(format!("did:web:{APEX_DOMAIN}:actor:{}", localpart.to_ascii_lowercase()))
}

/// Encode a DID into the `_did_<base32>@etzhayyim.com` address form. Inverse of the
/// `_did_` branch in [`resolve_recipient`]; used to mint reply-able addresses for
/// handle-less members.
pub fn did_to_address(did: &str) -> String {
    format!(
        "{DID_LOCALPART_PREFIX}{}@{APEX_DOMAIN}",
        base32_encode(did.as_bytes())
    )
}

fn split_address(addr: &str) -> Option<(&str, &str)> {
    let at = addr.rfind('@')?;
    let local = &addr[..at];
    let domain = &addr[at + 1..];
    if local.is_empty() || domain.is_empty() {
        return None;
    }
    Some((local, domain))
}

/// Conservative localpart charset for the actor mapping (avoids producing malformed
/// DIDs). `did:web` path segments and our actor slugs are `[a-z0-9._-]`.
fn is_valid_localpart(local: &str) -> bool {
    !local.is_empty()
        && local.len() <= 64
        && local
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | '-'))
}

// ── RFC 4648 base32 (lowercase, no padding) ────────────────────────────────────
//
// Inlined to keep the crate dependency-light. Lowercase + unpadded so the result
// is a legal email localpart.

const B32_ALPHABET: &[u8; 32] = b"abcdefghijklmnopqrstuvwxyz234567";

fn base32_encode(input: &[u8]) -> String {
    let mut out = String::new();
    let mut buffer: u32 = 0;
    let mut bits: u32 = 0;
    for &byte in input {
        buffer = (buffer << 8) | byte as u32;
        bits += 8;
        while bits >= 5 {
            bits -= 5;
            let idx = ((buffer >> bits) & 0x1F) as usize;
            out.push(B32_ALPHABET[idx] as char);
        }
    }
    if bits > 0 {
        let idx = ((buffer << (5 - bits)) & 0x1F) as usize;
        out.push(B32_ALPHABET[idx] as char);
    }
    out
}

fn base32_decode(input: &str) -> Option<Vec<u8>> {
    let mut buffer: u32 = 0;
    let mut bits: u32 = 0;
    let mut out = Vec::new();
    for c in input.chars() {
        let val = match c {
            'a'..='z' => c as u32 - 'a' as u32,
            'A'..='Z' => c as u32 - 'A' as u32, // tolerate uppercase on decode
            '2'..='7' => c as u32 - '2' as u32 + 26,
            _ => return None,
        };
        buffer = (buffer << 5) | val;
        bits += 5;
        if bits >= 8 {
            bits -= 8;
            out.push(((buffer >> bits) & 0xFF) as u8);
        }
    }
    Some(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn actor_localpart_maps_to_did_web() {
        assert_eq!(
            resolve_recipient("bob@etzhayyim.com"),
            Recipient::Did("did:web:etzhayyim.com:actor:bob".to_string())
        );
    }

    #[test]
    fn localpart_is_lowercased() {
        assert_eq!(
            resolve_recipient("Bob@etzhayyim.com"),
            Recipient::Did("did:web:etzhayyim.com:actor:bob".to_string())
        );
    }

    #[test]
    fn foreign_domain_is_relay_denied() {
        assert_eq!(
            resolve_recipient("bob@gmail.com"),
            Recipient::NotOurDomain("bob@gmail.com".to_string())
        );
    }

    #[test]
    fn malformed_address_is_no_such_user() {
        assert_eq!(
            resolve_recipient("not-an-address"),
            Recipient::NoSuchUser("not-an-address".to_string())
        );
        assert!(matches!(resolve_recipient("@etzhayyim.com"), Recipient::NoSuchUser(_)));
        assert!(matches!(resolve_recipient("bob@"), Recipient::NoSuchUser(_)));
    }

    #[test]
    fn invalid_localpart_charset_is_no_such_user() {
        assert!(matches!(
            resolve_recipient("a b@etzhayyim.com"),
            Recipient::NoSuchUser(_)
        ));
    }

    #[test]
    fn did_address_round_trips() {
        let did = "did:plc:abc123xyz";
        let addr = did_to_address(did);
        assert!(addr.starts_with("_did_"));
        assert!(addr.ends_with("@etzhayyim.com"));
        assert_eq!(resolve_recipient(&addr), Recipient::Did(did.to_string()));
    }

    #[test]
    fn did_address_round_trips_did_web() {
        let did = "did:web:etzhayyim.com:actor:alice";
        assert_eq!(resolve_recipient(&did_to_address(did)), Recipient::Did(did.to_string()));
    }

    #[test]
    fn did_fallback_rejects_non_did_payload() {
        let addr = format!("{}{}@etzhayyim.com", DID_LOCALPART_PREFIX, base32_encode(b"not-a-did"));
        assert!(matches!(resolve_recipient(&addr), Recipient::NoSuchUser(_)));
    }

    #[test]
    fn base32_round_trips_arbitrary_bytes() {
        for sample in [&b""[..], b"x", b"did:key:z6Mk", b"\x00\xff\x10\x80hello"] {
            let enc = base32_encode(sample);
            assert!(enc.chars().all(|c| c.is_ascii_lowercase() || ('2'..='7').contains(&c)));
            assert_eq!(base32_decode(&enc).unwrap(), sample, "round-trip for {sample:?}");
        }
    }

    #[test]
    fn base32_decode_rejects_padding_and_junk() {
        assert!(base32_decode("aaa=").is_none());
        assert!(base32_decode("a!b").is_none());
    }
}
