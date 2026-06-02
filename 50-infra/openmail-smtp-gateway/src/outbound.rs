//! Outbound assembly: render a structured message and DKIM-sign it (option b).
//!
//! This ties [`crate::render`] + [`crate::dkim`] into the bytes an SMTP relay sends.
//! The `key` is the member's Ed25519 ARK key — in production this whole function
//! runs **client-side** (it is pure and wasm32-compilable); the gateway receives
//! the already-signed bytes and only relays them, holding no signing key.

use ed25519_dalek::SigningKey;

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
