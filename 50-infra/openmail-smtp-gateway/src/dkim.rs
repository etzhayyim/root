//! DKIM signing + verification (RFC 6376 + RFC 8463 `ed25519-sha256`).
//!
//! This is the cryptographic core of the **option (b)** outbound design: per-member
//! self-signed DKIM with **no platform-held signing key**.
//!
//! ## Key custody (the whole point of option b)
//!
//! - The DKIM *private key* belongs to the member and is derived in their passkey
//!   ARK hierarchy. Signing therefore runs **client-side** — this module is pure
//!   and `wasm32`-compilable so the same canonicalization runs in the member's
//!   browser. The gateway never receives a signing key.
//! - The *public key* is published in DNS as `<selector>._domainkey.etzhayyim.com`
//!   (see [`txt_record`] / [`dns_record_name`]) — public material only.
//! - DMARC aligns because `d=etzhayyim.com` matches the `From:` domain, while the
//!   key that authorises the message is the member's, not the platform's. A leaked
//!   member key forges only that member; revocation is a single TXT delete.
//!
//! The gateway itself uses only [`verify`] (inbound DKIM checks) — it holds no key.
//!
//! ## Correctness
//!
//! Canonicalization is pinned to RFC 8463 Appendix A: [`tests`] verifies the RFC's
//! authoritative `ed25519-sha256` signature against the RFC's public key over the
//! RFC's message. If that passes, the signature-base construction is byte-correct
//! against the spec (i.e. interop-correct with real verifiers like Gmail).
//!
//! ## R0 scope
//!
//! `ed25519-sha256` only. RFC 8463 recommends *also* emitting an `rsa-sha256`
//! signature for receivers that don't yet accept ed25519; that second signer drops
//! in behind the same canonicalization (RSA key also client-held) and is the
//! documented compat follow-up.

use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use ed25519_dalek::{Signature, SigningKey, VerifyingKey};
use rsa::pkcs1v15::{
    Signature as RsaSignature, SigningKey as RsaSigningKey, VerifyingKey as RsaVerifyingKey,
};
use rsa::pkcs8::DecodePublicKey;
use rsa::signature::{SignatureEncoding, Signer as RsaSigner, Verifier as RsaVerifier};
use rsa::{RsaPrivateKey, RsaPublicKey};
use sha2::{Digest, Sha256};

/// `a=` value for the charter-native algorithm (member ARK derives Ed25519).
pub const ALG_ED25519_SHA256: &str = "ed25519-sha256";
/// `a=` value for the RFC 8463 co-signature (receiver-compat; member-held RSA key).
pub const ALG_RSA_SHA256: &str = "rsa-sha256";
/// The `_domainkey` label DKIM mandates between selector and domain.
pub const DOMAINKEY_LABEL: &str = "_domainkey";

#[derive(Debug, PartialEq, Eq)]
pub enum DkimError {
    NoSignatureHeader,
    MissingTag(&'static str),
    BadBase64(&'static str),
    BadKeyLength,
    BadRsaKey,
    UnsupportedAlgorithm(String),
}

impl std::fmt::Display for DkimError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DkimError::NoSignatureHeader => write!(f, "no DKIM-Signature header"),
            DkimError::MissingTag(t) => write!(f, "DKIM-Signature missing {t}= tag"),
            DkimError::BadBase64(t) => write!(f, "DKIM-Signature {t}= not valid base64"),
            DkimError::BadKeyLength => write!(f, "ed25519 key/sig has wrong length"),
            DkimError::BadRsaKey => write!(f, "RSA public key is not valid DER SubjectPublicKeyInfo"),
            DkimError::UnsupportedAlgorithm(a) => write!(f, "unsupported DKIM a={a}"),
        }
    }
}
impl std::error::Error for DkimError {}

/// Parameters for producing a signature (the algorithm + canonicalization are fixed
/// at `ed25519-sha256` / `relaxed/relaxed`).
#[derive(Debug, Clone)]
pub struct SignParams {
    /// `d=` signing domain (e.g. `etzhayyim.com`).
    pub domain: String,
    /// `s=` selector (e.g. the member's key id) — the DNS label under `_domainkey`.
    pub selector: String,
    /// `h=` header names, in order. Repeat a name to oversign (RFC 6376 §5.4.2);
    /// e.g. `["from","to","subject","date","from"]` oversigns `From`.
    pub signed_headers: Vec<String>,
    /// `i=` AUID (optional).
    pub auid: Option<String>,
    /// `t=` signature timestamp (optional; caller supplies — this lib is clock-free).
    pub timestamp: Option<u64>,
}

/// Build the `DKIM-Signature` value up to `b=` (empty) for a given algorithm. Tag
/// order mirrors RFC 8463 Appendix A; `h=` is `":"`-joined.
fn unsigned_value(params: &SignParams, alg: &str, bh: &str) -> String {
    let mut value = format!("v=1; a={alg}; c=relaxed/relaxed; d={}; ", params.domain);
    if let Some(i) = &params.auid {
        value.push_str(&format!("i={i}; "));
    }
    value.push_str("q=dns/txt; ");
    value.push_str(&format!("s={}; ", params.selector));
    if let Some(t) = params.timestamp {
        value.push_str(&format!("t={t}; "));
    }
    value.push_str(&format!("h={}; bh={bh}; b=", params.signed_headers.join(":")));
    value
}

/// Sign `message` (full RFC 5322 bytes, headers + blank line + body) with the
/// member's **Ed25519** key (held client-side; never by the gateway). Returns the
/// `DKIM-Signature:` header to prepend.
pub fn sign(message: &str, params: &SignParams, key: &SigningKey) -> String {
    let (headers, body) = split_message(message);
    let bh = B64.encode(Sha256::digest(relaxed_body(&body).as_bytes()));
    let value = unsigned_value(params, ALG_ED25519_SHA256, &bh);
    let base = signature_base(&headers, &params.signed_headers, &value);
    let digest = Sha256::digest(base.as_bytes());
    let sig = key.sign(&digest); // Ed25519 over the 32-byte SHA-256 digest (RFC 8463)
    let b = B64.encode(sig.to_bytes());
    format!("DKIM-Signature: {value}{b}")
}

/// Sign `message` with the member's **RSA** key (`rsa-sha256`) — the RFC 8463
/// co-signature for receivers that don't yet accept ed25519. The RSA key is also
/// member-held (client-side). Emit this in addition to the ed25519 signature.
pub fn sign_rsa(message: &str, params: &SignParams, key: &RsaPrivateKey) -> String {
    let (headers, body) = split_message(message);
    let bh = B64.encode(Sha256::digest(relaxed_body(&body).as_bytes()));
    let value = unsigned_value(params, ALG_RSA_SHA256, &bh);
    let base = signature_base(&headers, &params.signed_headers, &value);
    // RSASSA-PKCS1-v1_5 over the base; EMSA hashes with SHA-256 internally (RFC 6376).
    let signing_key = RsaSigningKey::<Sha256>::new(key.clone());
    let sig = signing_key.sign(base.as_bytes());
    let b = B64.encode(sig.to_bytes());
    format!("DKIM-Signature: {value}{b}")
}

/// Verify the `DKIM-Signature` already present in `message` against `public_key_b64`
/// (the `p=` value from the signer's DNS TXT record). Dispatches on the `a=` tag:
/// `ed25519-sha256` (p = raw 32-byte key) or `rsa-sha256` (p = DER SubjectPublicKeyInfo).
/// Returns `Ok(true)` only if both the body hash and the signature check out.
pub fn verify(message: &str, public_key_b64: &str) -> Result<bool, DkimError> {
    let (headers, body) = split_message(message);
    let raw_sig = headers
        .iter()
        .find(|(n, _)| n.eq_ignore_ascii_case("dkim-signature"))
        .map(|(_, v)| v.clone())
        .ok_or(DkimError::NoSignatureHeader)?;

    let tags = parse_tags(&raw_sig);
    let alg = strip_ws(&tags_get(&tags, "a").ok_or(DkimError::MissingTag("a"))?);
    let h_tag = tags_get(&tags, "h").ok_or(DkimError::MissingTag("h"))?;
    let bh_tag = strip_ws(&tags_get(&tags, "bh").ok_or(DkimError::MissingTag("bh"))?);
    let b_tag = strip_ws(&tags_get(&tags, "b").ok_or(DkimError::MissingTag("b"))?);

    // 1. Body hash (common to both algorithms).
    let computed_bh = B64.encode(Sha256::digest(relaxed_body(&body).as_bytes()));
    if computed_bh != bh_tag {
        return Ok(false);
    }

    // 2. Header signature. Rebuild the base from the original header with b= emptied.
    let signed_headers: Vec<String> = h_tag.split(':').map(|s| s.trim().to_string()).collect();
    let emptied = strip_b_value(&raw_sig);
    let base = signature_base(&headers, &signed_headers, &emptied);
    let sig_bytes = B64.decode(&b_tag).map_err(|_| DkimError::BadBase64("b"))?;

    match alg.as_str() {
        ALG_ED25519_SHA256 => {
            let digest = Sha256::digest(base.as_bytes());
            let pk_bytes = B64
                .decode(public_key_b64.trim())
                .map_err(|_| DkimError::BadBase64("p"))?;
            let pk: [u8; 32] = pk_bytes.try_into().map_err(|_| DkimError::BadKeyLength)?;
            let vk = VerifyingKey::from_bytes(&pk).map_err(|_| DkimError::BadKeyLength)?;
            let sig_arr: [u8; 64] = sig_bytes.try_into().map_err(|_| DkimError::BadKeyLength)?;
            let sig = Signature::from_bytes(&sig_arr);
            Ok(vk.verify(&digest, &sig).is_ok())
        }
        ALG_RSA_SHA256 => {
            let der = B64
                .decode(public_key_b64.trim())
                .map_err(|_| DkimError::BadBase64("p"))?;
            let pubkey = RsaPublicKey::from_public_key_der(&der).map_err(|_| DkimError::BadRsaKey)?;
            let vk = RsaVerifyingKey::<Sha256>::new(pubkey);
            let sig = match RsaSignature::try_from(sig_bytes.as_slice()) {
                Ok(s) => s,
                Err(_) => return Ok(false),
            };
            // RSASSA-PKCS1-v1_5 verify hashes the base with SHA-256 internally.
            Ok(vk.verify(base.as_bytes(), &sig).is_ok())
        }
        other => Err(DkimError::UnsupportedAlgorithm(other.to_string())),
    }
}

/// Build the DNS TXT record value publishing an Ed25519 public key.
pub fn txt_record(public_key_b64: &str) -> String {
    format!("v=DKIM1; k=ed25519; p={public_key_b64}")
}

/// Build the DNS TXT record value publishing an RSA public key. `public_key_b64`
/// is the DER SubjectPublicKeyInfo, base64 (same form fed to [`verify`]).
pub fn txt_record_rsa(public_key_der_b64: &str) -> String {
    format!("v=DKIM1; k=rsa; p={public_key_der_b64}")
}

/// The fully-qualified DNS name a selector's key is published at.
pub fn dns_record_name(selector: &str, domain: &str) -> String {
    format!("{selector}.{DOMAINKEY_LABEL}.{domain}")
}

// ── canonicalization (RFC 6376 §3.4, relaxed) ──────────────────────────────────

/// Relaxed header canonicalization → `name:value` (lowercased name, unfolded,
/// WSP-compressed, trimmed; no trailing CRLF).
pub fn relaxed_header(name: &str, value: &str) -> String {
    let unfolded = value.replace("\r\n", "");
    let mut compressed = String::with_capacity(unfolded.len());
    let mut prev_ws = false;
    for c in unfolded.chars() {
        if c == ' ' || c == '\t' {
            if !prev_ws {
                compressed.push(' ');
                prev_ws = true;
            }
        } else {
            compressed.push(c);
            prev_ws = false;
        }
    }
    format!("{}:{}", name.trim().to_ascii_lowercase(), compressed.trim())
}

/// The DKIM body hash (`bh=`) of `body`: base64(sha256(relaxed-canonicalized body)).
/// Also the body binding used by postage so one receipt covers exactly this content.
pub fn body_hash(body: &str) -> String {
    B64.encode(Sha256::digest(relaxed_body(body).as_bytes()))
}

/// Relaxed body canonicalization (RFC 6376 §3.4.4).
pub fn relaxed_body(body: &str) -> String {
    let norm = normalize_crlf(body);
    let mut lines: Vec<String> = norm
        .split("\r\n")
        .map(|line| {
            let mut out = String::with_capacity(line.len());
            let mut prev_ws = false;
            for c in line.chars() {
                if c == ' ' || c == '\t' {
                    if !prev_ws {
                        out.push(' ');
                        prev_ws = true;
                    }
                } else {
                    out.push(c);
                    prev_ws = false;
                }
            }
            out.trim_end().to_string()
        })
        .collect();
    while matches!(lines.last(), Some(l) if l.is_empty()) {
        lines.pop();
    }
    if lines.is_empty() {
        return String::new();
    }
    let mut s = lines.join("\r\n");
    s.push_str("\r\n");
    s
}

// ── internals ──────────────────────────────────────────────────────────────────

/// Concatenate the canonicalized signed headers (bottom-up consumption, with
/// oversigning) followed by the canonicalized DKIM-Signature (b= already emptied,
/// no trailing CRLF) — i.e. the exact bytes the algorithm hashes (RFC 6376 §3.7).
fn signature_base(headers: &[(String, String)], h_tags: &[String], dkim_sig_value: &str) -> String {
    let mut data = String::new();
    let mut used: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
    for tag in h_tags {
        let key = tag.trim().to_ascii_lowercase();
        if key.is_empty() {
            continue;
        }
        let instances: Vec<&(String, String)> = headers
            .iter()
            .filter(|(n, _)| n.trim().eq_ignore_ascii_case(&key))
            .collect();
        let count = used.entry(key.clone()).or_insert(0);
        if *count < instances.len() {
            // Bottom-up: the count-th instance from the end.
            let (name, value) = instances[instances.len() - 1 - *count];
            data.push_str(&relaxed_header(name, value));
            data.push_str("\r\n");
        }
        // else: oversigned / nonexistent → contribute nothing (null string).
        *count += 1;
    }
    data.push_str(&relaxed_header("DKIM-Signature", dkim_sig_value));
    data
}

/// Split a message into `(headers, body)`. Headers preserve folding so relaxed
/// canonicalization can unfold them; body is the verbatim remainder.
fn split_message(message: &str) -> (Vec<(String, String)>, String) {
    let norm = normalize_crlf(message);
    let (head, body) = match norm.find("\r\n\r\n") {
        Some(i) => (norm[..i].to_string(), norm[i + 4..].to_string()),
        None => (norm.clone(), String::new()),
    };
    let mut headers: Vec<(String, String)> = Vec::new();
    for line in head.split("\r\n") {
        if line.starts_with(' ') || line.starts_with('\t') {
            if let Some(last) = headers.last_mut() {
                last.1.push_str("\r\n");
                last.1.push_str(line);
            }
        } else if let Some(ci) = line.find(':') {
            headers.push((line[..ci].to_string(), line[ci + 1..].to_string()));
        }
    }
    (headers, body)
}

/// Parse `k=v; k=v; ...` (after unfolding) into ordered pairs. Splits on the first
/// `=` so base64 values containing `=` survive.
fn parse_tags(raw: &str) -> Vec<(String, String)> {
    raw.replace("\r\n", "")
        .split(';')
        .filter_map(|seg| {
            let seg = seg.trim();
            if seg.is_empty() {
                return None;
            }
            let eq = seg.find('=')?;
            Some((seg[..eq].trim().to_string(), seg[eq + 1..].to_string()))
        })
        .collect()
}

fn tags_get(tags: &[(String, String)], key: &str) -> Option<String> {
    tags.iter().find(|(k, _)| k == key).map(|(_, v)| v.clone())
}

/// Remove the `b=` tag's value in place, preserving every other byte/space so the
/// canonicalized result matches the original signer's input.
fn strip_b_value(raw: &str) -> String {
    raw.split(';')
        .map(|seg| {
            if seg.trim_start().starts_with("b=") {
                let pos = seg.find("b=").unwrap();
                seg[..pos + 2].to_string()
            } else {
                seg.to_string()
            }
        })
        .collect::<Vec<_>>()
        .join(";")
}

fn strip_ws(s: &str) -> String {
    s.chars().filter(|c| !c.is_whitespace()).collect()
}

fn normalize_crlf(s: &str) -> String {
    s.replace("\r\n", "\n").replace('\r', "\n").replace('\n', "\r\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── RFC 8463 Appendix A test vector ────────────────────────────────────────
    const RFC_PRIV_SEED_B64: &str = "nWGxne/9WmC6hEr0kuwsxERJxWl7MmkZcDusAxyuf2A=";
    const RFC_PUB_B64: &str = "11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo=";
    const RFC_BH: &str = "2jUSOH9NhtVGCQWNr9BrIAPreKQjO6Sn7XIkfJVOzv8=";

    /// The RFC's message body (verbatim — note the double space after "game.").
    const RFC_BODY: &str =
        "Hi.\r\n\r\nWe lost the game.  Are you hungry yet?\r\n\r\nJoe.\r\n";

    /// The RFC's message WITH its authoritative ed25519 DKIM-Signature prepended,
    /// folded exactly as in Appendix A.
    const RFC_SIGNED_MESSAGE: &str = "DKIM-Signature: v=1; a=ed25519-sha256; c=relaxed/relaxed;\r\n \
d=football.example.com; i=@football.example.com;\r\n \
q=dns/txt; s=brisbane; t=1528637909; h=from : to :\r\n \
subject : date : message-id : from : subject : date;\r\n \
bh=2jUSOH9NhtVGCQWNr9BrIAPreKQjO6Sn7XIkfJVOzv8=;\r\n \
b=/gCrinpcQOoIfuHNQIbq4pgh9kyIK3AQUdt9OdqQehSwhEIug4D11Bus\r\n \
Fa3bT3FY5OsU7ZbnKELq+eXdp1Q1Dw==\r\n\
From: Joe SixPack <joe@football.example.com>\r\n\
To: Suzie Q <suzie@shopping.example.net>\r\n\
Subject: Is dinner ready?\r\n\
Date: Fri, 11 Jul 2003 21:00:37 -0700 (PDT)\r\n\
Message-ID: <20030712040037.46341.5F8J@football.example.com>\r\n\r\n\
Hi.\r\n\r\nWe lost the game.  Are you hungry yet?\r\n\r\nJoe.\r\n";

    /// The message body+headers WITHOUT a DKIM-Signature (for the round-trip test).
    const RFC_UNSIGNED_MESSAGE: &str = "From: Joe SixPack <joe@football.example.com>\r\n\
To: Suzie Q <suzie@shopping.example.net>\r\n\
Subject: Is dinner ready?\r\n\
Date: Fri, 11 Jul 2003 21:00:37 -0700 (PDT)\r\n\
Message-ID: <20030712040037.46341.5F8J@football.example.com>\r\n\r\n\
Hi.\r\n\r\nWe lost the game.  Are you hungry yet?\r\n\r\nJoe.\r\n";

    fn rfc_signing_key() -> SigningKey {
        let seed: [u8; 32] = B64.decode(RFC_PRIV_SEED_B64).unwrap().try_into().unwrap();
        SigningKey::from_bytes(&seed)
    }

    #[test]
    fn relaxed_body_matches_rfc_bh() {
        let bh = B64.encode(Sha256::digest(relaxed_body(RFC_BODY).as_bytes()));
        assert_eq!(bh, RFC_BH, "relaxed body hash must match RFC 8463 Appendix A");
    }

    /// The definitive correctness check: verify the RFC's authoritative signature.
    /// If this passes, the canonicalization + signature-base + ed25519 path is
    /// byte-exact against the spec → interop-correct with real verifiers.
    #[test]
    fn verifies_rfc8463_authoritative_signature() {
        assert_eq!(verify(RFC_SIGNED_MESSAGE, RFC_PUB_B64), Ok(true));
    }

    #[test]
    fn tampered_body_fails_verification() {
        let tampered = RFC_SIGNED_MESSAGE.replace("hungry", "hungrz");
        assert_eq!(verify(&tampered, RFC_PUB_B64), Ok(false));
    }

    #[test]
    fn tampered_signed_header_fails_verification() {
        let tampered = RFC_SIGNED_MESSAGE.replace("Is dinner ready?", "Is dinner cold?");
        assert_eq!(verify(&tampered, RFC_PUB_B64), Ok(false));
    }

    #[test]
    fn wrong_public_key_fails_verification() {
        // A different (valid) ed25519 public key must not verify.
        let other = B64.encode(SigningKey::from_bytes(&[7u8; 32]).verifying_key().to_bytes());
        assert_eq!(verify(RFC_SIGNED_MESSAGE, &other), Ok(false));
    }

    /// Our own signer round-trips through our own verifier (independent of the RFC's
    /// exact tag formatting — proves sign/verify are mutually consistent).
    #[test]
    fn sign_then_verify_round_trips() {
        let params = SignParams {
            domain: "football.example.com".into(),
            selector: "brisbane".into(),
            signed_headers: vec![
                "from".into(),
                "to".into(),
                "subject".into(),
                "date".into(),
                "message-id".into(),
            ],
            auid: Some("@football.example.com".into()),
            timestamp: Some(1528637909),
        };
        let header = sign(RFC_UNSIGNED_MESSAGE, &params, &rfc_signing_key());
        assert!(header.starts_with("DKIM-Signature: "));
        let signed = format!("{header}\r\n{RFC_UNSIGNED_MESSAGE}");
        assert_eq!(verify(&signed, RFC_PUB_B64), Ok(true));
    }

    #[test]
    fn oversigning_from_round_trips() {
        // Oversign From (listed twice though present once) — must still verify.
        let params = SignParams {
            domain: "football.example.com".into(),
            selector: "brisbane".into(),
            signed_headers: vec!["from".into(), "subject".into(), "from".into()],
            auid: None,
            timestamp: None,
        };
        let header = sign(RFC_UNSIGNED_MESSAGE, &params, &rfc_signing_key());
        let signed = format!("{header}\r\n{RFC_UNSIGNED_MESSAGE}");
        assert_eq!(verify(&signed, RFC_PUB_B64), Ok(true));
    }

    #[test]
    fn txt_record_matches_rfc() {
        assert_eq!(
            txt_record(RFC_PUB_B64),
            "v=DKIM1; k=ed25519; p=11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo="
        );
    }

    #[test]
    fn dns_record_name_inserts_domainkey_label() {
        assert_eq!(
            dns_record_name("brisbane", "etzhayyim.com"),
            "brisbane._domainkey.etzhayyim.com"
        );
    }

    #[test]
    fn relaxed_header_lowercases_unfolds_and_compresses() {
        assert_eq!(relaxed_header("From", "  Joe  <joe@x>  "), "from:Joe <joe@x>");
        assert_eq!(relaxed_header("Subject", "a\r\n  b"), "subject:a b");
    }

    #[test]
    fn missing_signature_header_errors() {
        assert_eq!(verify(RFC_UNSIGNED_MESSAGE, RFC_PUB_B64), Err(DkimError::NoSignatureHeader));
    }

    // ── RFC 8463 Appendix A — rsa-sha256 co-signature vector ───────────────────

    /// RSA public key as the DER SubjectPublicKeyInfo base64 from the `test`
    /// selector TXT record (the multi-string p= concatenated).
    const RFC_RSA_PUB_DER_B64: &str = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDkHlOQoBTzWRiGs5V6NpP3idY6Wk08a5qhdR6wy5bdOKb2jLQiY/J16JYi0Qvx/byYzCNb3W91y3FutACDfzwQ/BC/e/8uBsCR+yz1Lxj+PL6lHvqMKrM3rG4hstT5QjvHO9PzoxZyVYLzBfO2EeC3Ip3G+2kryOTIKT+l/K4w3QIDAQAB";

    /// The RFC's RSA private key (PKCS#1 PEM) for the `test` selector.
    const RFC_RSA_PRIV_PEM: &str = "-----BEGIN RSA PRIVATE KEY-----\n\
MIICXQIBAAKBgQDkHlOQoBTzWRiGs5V6NpP3idY6Wk08a5qhdR6wy5bdOKb2jLQi\n\
Y/J16JYi0Qvx/byYzCNb3W91y3FutACDfzwQ/BC/e/8uBsCR+yz1Lxj+PL6lHvqM\n\
KrM3rG4hstT5QjvHO9PzoxZyVYLzBfO2EeC3Ip3G+2kryOTIKT+l/K4w3QIDAQAB\n\
AoGAH0cxOhFZDgzXWhDhnAJDw5s4roOXN4OhjiXa8W7Y3rhX3FJqmJSPuC8N9vQm\n\
6SVbaLAE4SG5mLMueHlh4KXffEpuLEiNp9Ss3O4YfLiQpbRqE7Tm5SxKjvvQoZZe\n\
zHorimOaChRL2it47iuWxzxSiRMv4c+j70GiWdxXnxe4UoECQQDzJB/0U58W7RZy\n\
6enGVj2kWF732CoWFZWzi1FicudrBFoy63QwcowpoCazKtvZGMNlPWnC7x/6o8Gc\n\
uSe0ga2xAkEA8C7PipPm1/1fTRQvj1o/dDmZp243044ZNyxjg+/OPN0oWCbXIGxy\n\
WvmZbXriOWoSALJTjExEgraHEgnXssuk7QJBALl5ICsYMu6hMxO73gnfNayNgPxd\n\
WFV6Z7ULnKyV7HSVYF0hgYOHjeYe9gaMtiJYoo0zGN+L3AAtNP9huqkWlzECQE1a\n\
licIeVlo1e+qJ6Mgqr0Q7Aa7falZ448ccbSFYEPD6oFxiOl9Y9se9iYHZKKfIcst\n\
o7DUw1/hz2Ck4N5JrgUCQQCyKveNvjzkkd8HjYs0SwM0fPjK16//5qDZ2UiDGnOe\n\
uEzxBDAr518Z8VFbR41in3W4Y3yCDgQlLlcETrS+zYcL\n\
-----END RSA PRIVATE KEY-----\n";

    const RFC_RSA_SIGNED_MESSAGE: &str = "DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;\r\n \
d=football.example.com; i=@football.example.com;\r\n \
q=dns/txt; s=test; t=1528637909; h=from : to : subject :\r\n \
date : message-id : from : subject : date;\r\n \
bh=2jUSOH9NhtVGCQWNr9BrIAPreKQjO6Sn7XIkfJVOzv8=;\r\n \
b=F45dVWDfMbQDGHJFlXUNB2HKfbCeLRyhDXgFpEL8GwpsRe0IeIixNTe3\r\n \
DhCVlUrSjV4BwcVcOF6+FF3Zo9Rpo1tFOeS9mPYQTnGdaSGsgeefOsk2Jz\r\n \
dA+L10TeYt9BgDfQNZtKdN1WO//KgIqXP7OdEFE4LjFYNcUxZQ4FADY+8=\r\n\
From: Joe SixPack <joe@football.example.com>\r\n\
To: Suzie Q <suzie@shopping.example.net>\r\n\
Subject: Is dinner ready?\r\n\
Date: Fri, 11 Jul 2003 21:00:37 -0700 (PDT)\r\n\
Message-ID: <20030712040037.46341.5F8J@football.example.com>\r\n\r\n\
Hi.\r\n\r\nWe lost the game.  Are you hungry yet?\r\n\r\nJoe.\r\n";

    /// Definitive RSA correctness: verify the RFC's authoritative rsa-sha256
    /// signature against the RFC's RSA public key.
    #[test]
    fn verifies_rfc8463_authoritative_rsa_signature() {
        assert_eq!(verify(RFC_RSA_SIGNED_MESSAGE, RFC_RSA_PUB_DER_B64), Ok(true));
    }

    #[test]
    fn rsa_tampered_body_fails() {
        let tampered = RFC_RSA_SIGNED_MESSAGE.replace("hungry", "hungrz");
        assert_eq!(verify(&tampered, RFC_RSA_PUB_DER_B64), Ok(false));
    }

    /// Our `sign_rsa` round-trips through our verifier with the RFC private key.
    #[test]
    fn sign_rsa_then_verify_round_trips() {
        use rsa::pkcs1::DecodeRsaPrivateKey;
        let priv_key = RsaPrivateKey::from_pkcs1_pem(RFC_RSA_PRIV_PEM).expect("parse RSA PEM");
        let params = SignParams {
            domain: "football.example.com".into(),
            selector: "test".into(),
            signed_headers: vec![
                "from".into(),
                "to".into(),
                "subject".into(),
                "date".into(),
                "message-id".into(),
            ],
            auid: Some("@football.example.com".into()),
            timestamp: Some(1528637909),
        };
        let header = sign_rsa(RFC_UNSIGNED_MESSAGE, &params, &priv_key);
        assert!(header.contains("a=rsa-sha256"));
        let signed = format!("{header}\r\n{RFC_UNSIGNED_MESSAGE}");
        assert_eq!(verify(&signed, RFC_RSA_PUB_DER_B64), Ok(true));
    }

    #[test]
    fn unsupported_algorithm_errors() {
        let msg = RFC_SIGNED_MESSAGE.replace("a=ed25519-sha256", "a=rsa-sha1");
        assert!(matches!(
            verify(&msg, RFC_PUB_B64),
            Err(DkimError::UnsupportedAlgorithm(_))
        ));
    }
}
