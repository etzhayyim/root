//! Outbound assembly: render a structured message and DKIM-sign it (option b).
//!
//! This ties [`crate::render`] + [`crate::dkim`] into the bytes an SMTP relay sends.
//! The `key` is the member's Ed25519 ARK key — in production this whole function
//! runs **client-side** (it is pure and wasm32-compilable); the gateway receives
//! the already-signed bytes and only relays them, holding no signing key.

use ed25519_dalek::SigningKey;
use rsa::RsaPrivateKey;

use crate::dkim::{self, SignParams};
use crate::render::{self, MimeMessage, RenderError};

/// Default `h=` set for outbound mail: covers the headers a verifier expects and
/// oversigns `From` (the DMARC-aligned identity) to block header-replacement.
pub fn default_signed_headers() -> Vec<String> {
    [
        "from",
        "to",
        "subject",
        "date",
        "message-id",
        "mime-version",
        "content-type",
        "from", // oversign From
    ]
    .iter()
    .map(|s| s.to_string())
    .collect()
}

/// Render `msg` to RFC 5322 and prepend a `DKIM-Signature`. Returns the full signed
/// message ready for SMTP `DATA` (apply [`render::dot_stuff`] at the transport edge).
pub fn render_and_sign(
    msg: &MimeMessage,
    params: &SignParams,
    key: &SigningKey,
) -> Result<Vec<u8>, RenderError> {
    let rendered = render::render_rfc5322(msg)?;
    // Rendered bytes are valid UTF-8 (ASCII headers + RFC 2047 subject + UTF-8 body).
    let rendered_str = String::from_utf8_lossy(&rendered);
    let sig_header = dkim::sign(&rendered_str, params, key);

    let mut out = Vec::with_capacity(sig_header.len() + 2 + rendered.len());
    out.extend_from_slice(sig_header.as_bytes());
    out.extend_from_slice(b"\r\n");
    out.extend_from_slice(&rendered);
    Ok(out)
}

/// Render and prepend **both** an ed25519 and an rsa-sha256 `DKIM-Signature` (RFC
/// 8463 dual-signing for deliverability). `ed_params` / `rsa_params` differ in their
/// selector (each key has its own DNS selector); both keys are member-held. A
/// verifier evaluates each signature independently and a message passes on any one,
/// so receivers that only accept RSA today still validate.
pub fn render_and_dual_sign(
    msg: &MimeMessage,
    ed_params: &SignParams,
    rsa_params: &SignParams,
    ed_key: &SigningKey,
    rsa_key: &RsaPrivateKey,
) -> Result<Vec<u8>, RenderError> {
    let rendered = render::render_rfc5322(msg)?;
    let rendered_str = String::from_utf8_lossy(&rendered);
    let ed_header = dkim::sign(&rendered_str, ed_params, ed_key);
    let rsa_header = dkim::sign_rsa(&rendered_str, rsa_params, rsa_key);

    let mut out = Vec::with_capacity(ed_header.len() + rsa_header.len() + 4 + rendered.len());
    out.extend_from_slice(ed_header.as_bytes());
    out.extend_from_slice(b"\r\n");
    out.extend_from_slice(rsa_header.as_bytes());
    out.extend_from_slice(b"\r\n");
    out.extend_from_slice(&rendered);
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use base64::{engine::general_purpose::STANDARD as B64, Engine as _};

    fn key() -> SigningKey {
        SigningKey::from_bytes(&[42u8; 32])
    }

    fn sample() -> MimeMessage {
        MimeMessage {
            from: "Alice <alice@etzhayyim.com>".into(),
            to: vec!["carol@yahoo.com".into()],
            subject: "Hello from etzhayyim".into(),
            date: "Mon, 02 Jun 2026 00:00:00 +0000".into(),
            message_id: "<rk1.alice@openmail.etzhayyim.com>".into(),
            body: "Hi Carol,\n\nthis is a bridged openmail message.\n".into(),
            extra_headers: vec![],
        }
    }

    fn params() -> SignParams {
        SignParams {
            domain: "etzhayyim.com".into(),
            selector: "alice-key1".into(),
            signed_headers: default_signed_headers(),
            auid: Some("@etzhayyim.com".into()),
            timestamp: Some(1_780_000_000),
        }
    }

    /// Full outbound path: render → sign → the result verifies against the member's
    /// published public key. This is the end-to-end proof of option (b).
    #[test]
    fn rendered_and_signed_message_verifies() {
        let signed = render_and_sign(&sample(), &params(), &key()).unwrap();
        let signed_str = String::from_utf8(signed).unwrap();

        // DKIM header is first, From: follows.
        assert!(signed_str.starts_with("DKIM-Signature: "));
        assert!(signed_str.contains("\r\nFrom: Alice <alice@etzhayyim.com>\r\n"));
        assert!(signed_str.contains("d=etzhayyim.com"));
        assert!(signed_str.contains("s=alice-key1"));

        let pubkey = B64.encode(key().verifying_key().to_bytes());
        assert_eq!(dkim::verify(&signed_str, &pubkey), Ok(true));
    }

    #[test]
    fn tampering_signed_message_breaks_verification() {
        let signed = render_and_sign(&sample(), &params(), &key()).unwrap();
        let mut signed_str = String::from_utf8(signed).unwrap();
        signed_str = signed_str.replace("bridged openmail", "totally different");
        let pubkey = B64.encode(key().verifying_key().to_bytes());
        assert_eq!(dkim::verify(&signed_str, &pubkey), Ok(false));
    }

    /// Dual-signed output carries both headers and the ed25519 signature (checked
    /// first by `verify`) validates over the rendered message.
    #[test]
    fn dual_signed_message_carries_both_and_verifies_ed25519() {
        use rsa::pkcs1::DecodeRsaPrivateKey;
        // A throwaway RSA key parsed from a fixed PEM (RFC 8463 Appendix A test key).
        let rsa_pem = "-----BEGIN RSA PRIVATE KEY-----\n\
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
        let rsa_key = RsaPrivateKey::from_pkcs1_pem(rsa_pem).unwrap();
        let mut rsa_params = params();
        rsa_params.selector = "alice-rsa1".into();

        let out =
            render_and_dual_sign(&sample(), &params(), &rsa_params, &key(), &rsa_key).unwrap();
        let s = String::from_utf8(out).unwrap();

        // Both signature algorithms present.
        assert!(s.contains("a=ed25519-sha256"));
        assert!(s.contains("a=rsa-sha256"));
        assert!(s.contains("s=alice-rsa1"));
        // verify() evaluates the first DKIM-Signature (ed25519) → must pass.
        let ed_pubkey = B64.encode(key().verifying_key().to_bytes());
        assert_eq!(dkim::verify(&s, &ed_pubkey), Ok(true));
    }

    #[test]
    fn dns_publication_value_is_well_formed() {
        let pubkey = B64.encode(key().verifying_key().to_bytes());
        let rec = dkim::txt_record(&pubkey);
        assert!(rec.starts_with("v=DKIM1; k=ed25519; p="));
        assert_eq!(
            dkim::dns_record_name(&params().selector, &params().domain),
            "alice-key1._domainkey.etzhayyim.com"
        );
    }
}
