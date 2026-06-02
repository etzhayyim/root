//! Outbound RFC 5322 rendering (ADR-2605172200 §3.2).
//!
//! The reverse of kotoba's `EmailIngestor` parse: take a structured message
//! (native record content the gateway already decrypted) and emit RFC 5322 bytes
//! ready for SMTP relay to a legacy recipient. Pure and clock-free — the caller
//! supplies `date` and `message_id` so the function is deterministic and testable.
//!
//! Security: header values are checked for CR/LF (header-injection) and rejected;
//! non-ASCII Subjects are RFC 2047 encoded-words. SMTP dot-stuffing for the DATA
//! phase is a transport concern, provided separately as [`dot_stuff`].

use base64::{engine::general_purpose::STANDARD as B64, Engine as _};

/// A structured outbound message.
#[derive(Debug, Clone)]
pub struct MimeMessage {
    /// e.g. `Alice <alice@etzhayyim.com>`.
    pub from: String,
    /// One or more recipient addresses (bare `carol@yahoo.com` is fine).
    pub to: Vec<String>,
    pub subject: String,
    /// RFC 5322 date string, supplied by caller (e.g. `Mon, 02 Jun 2026 00:00:00 +0000`).
    pub date: String,
    /// e.g. `<rkey.alice@openmail.etzhayyim.com>`.
    pub message_id: String,
    /// UTF-8 text/plain body.
    pub body: String,
    /// Extra headers such as `X-Openmail-At-Uri`, `X-Openmail-Postage-Tx`.
    pub extra_headers: Vec<(String, String)>,
}

#[derive(Debug, PartialEq, Eq)]
pub enum RenderError {
    /// A header value contained CR or LF — refused to prevent header injection.
    HeaderInjection(String),
    /// `to` was empty.
    NoRecipients,
}

impl std::fmt::Display for RenderError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RenderError::HeaderInjection(h) => write!(f, "header injection in {h:?}"),
            RenderError::NoRecipients => write!(f, "no recipients"),
        }
    }
}
impl std::error::Error for RenderError {}

/// Render a message to RFC 5322 bytes (CRLF line endings, headers + blank line + body).
pub fn render_rfc5322(msg: &MimeMessage) -> Result<Vec<u8>, RenderError> {
    if msg.to.is_empty() {
        return Err(RenderError::NoRecipients);
    }

    let mut headers: Vec<(String, String)> = vec![
        ("From".into(), reject_crlf(&msg.from, "From")?),
        ("To".into(), reject_crlf(&msg.to.join(", "), "To")?),
        ("Subject".into(), encode_subject(&msg.subject)),
        ("Date".into(), reject_crlf(&msg.date, "Date")?),
        ("Message-ID".into(), reject_crlf(&msg.message_id, "Message-ID")?),
        ("MIME-Version".into(), "1.0".into()),
        ("Content-Type".into(), "text/plain; charset=utf-8".into()),
        ("Content-Transfer-Encoding".into(), "8bit".into()),
    ];
    for (name, value) in &msg.extra_headers {
        // Header *names* must also be injection-free and token-like.
        if name.contains([':', '\r', '\n']) || name.is_empty() {
            return Err(RenderError::HeaderInjection(name.clone()));
        }
        headers.push((name.clone(), reject_crlf(value, name)?));
    }

    let mut out = String::new();
    for (name, value) in &headers {
        out.push_str(name);
        out.push_str(": ");
        out.push_str(value);
        out.push_str("\r\n");
    }
    out.push_str("\r\n"); // header/body separator
    out.push_str(&normalize_crlf(&msg.body));
    Ok(out.into_bytes())
}

/// Reject a header value containing a bare CR or LF (header-injection guard).
fn reject_crlf(value: &str, header: &str) -> Result<String, RenderError> {
    if value.contains('\r') || value.contains('\n') {
        return Err(RenderError::HeaderInjection(header.to_string()));
    }
    Ok(value.to_string())
}

/// RFC 2047 encode a Subject only when it contains non-ASCII; otherwise pass through
/// (after the CR/LF guard). Encoded form is a single `=?UTF-8?B?...?=` word.
fn encode_subject(subject: &str) -> String {
    if subject.is_ascii() && !subject.contains(['\r', '\n']) {
        return subject.to_string();
    }
    format!("=?UTF-8?B?{}?=", B64.encode(subject.as_bytes()))
}

/// Normalise any mix of `\r\n` / `\n` line endings to canonical CRLF.
fn normalize_crlf(body: &str) -> String {
    let mut out = String::with_capacity(body.len());
    let mut prev_cr = false;
    for ch in body.chars() {
        match ch {
            '\r' => {
                out.push_str("\r\n");
                prev_cr = true;
            }
            '\n' => {
                if !prev_cr {
                    out.push_str("\r\n");
                }
                prev_cr = false;
            }
            other => {
                out.push(other);
                prev_cr = false;
            }
        }
    }
    out
}

/// SMTP DATA transparency (RFC 5321 §4.5.2): any line beginning with `.` gets an
/// extra leading `.`. Apply to the full rendered message just before the DATA
/// transfer; the receiver reverses it.
pub fn dot_stuff(message: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(message.len());
    let mut at_line_start = true;
    for &b in message {
        if at_line_start && b == b'.' {
            out.push(b'.');
        }
        out.push(b);
        at_line_start = b == b'\n';
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample() -> MimeMessage {
        MimeMessage {
            from: "Alice <alice@etzhayyim.com>".into(),
            to: vec!["carol@yahoo.com".into()],
            subject: "Hello".into(),
            date: "Mon, 02 Jun 2026 00:00:00 +0000".into(),
            message_id: "<rk1.alice@openmail.etzhayyim.com>".into(),
            body: "Line one\nLine two\n".into(),
            extra_headers: vec![(
                "X-Openmail-At-Uri".into(),
                "at://did:web:etzhayyim.com:actor:alice/app.openmail.message/rk1".into(),
            )],
        }
    }

    #[test]
    fn renders_headers_blank_line_and_body() {
        let bytes = render_rfc5322(&sample()).unwrap();
        let text = String::from_utf8(bytes).unwrap();
        assert!(text.contains("From: Alice <alice@etzhayyim.com>\r\n"));
        assert!(text.contains("To: carol@yahoo.com\r\n"));
        assert!(text.contains("Subject: Hello\r\n"));
        assert!(text.contains("Message-ID: <rk1.alice@openmail.etzhayyim.com>\r\n"));
        assert!(text.contains("MIME-Version: 1.0\r\n"));
        assert!(text.contains("X-Openmail-At-Uri: at://"));
        // Header/body separator then body with CRLF.
        assert!(text.contains("\r\n\r\nLine one\r\nLine two\r\n"));
    }

    #[test]
    fn multiple_recipients_join_with_comma() {
        let mut m = sample();
        m.to = vec!["carol@yahoo.com".into(), "dave@corp.example".into()];
        let text = String::from_utf8(render_rfc5322(&m).unwrap()).unwrap();
        assert!(text.contains("To: carol@yahoo.com, dave@corp.example\r\n"));
    }

    #[test]
    fn empty_recipients_errors() {
        let mut m = sample();
        m.to.clear();
        assert_eq!(render_rfc5322(&m), Err(RenderError::NoRecipients));
    }

    #[test]
    fn header_injection_in_subject_is_rejected() {
        // A CRLF in the From value must be refused — classic header smuggling.
        let mut m = sample();
        m.from = "Alice <a@b>\r\nBcc: victim@evil.example".into();
        assert_eq!(
            render_rfc5322(&m),
            Err(RenderError::HeaderInjection("From".into()))
        );
    }

    #[test]
    fn injection_via_extra_header_name_is_rejected() {
        let mut m = sample();
        m.extra_headers = vec![("X-Bad\r\nBcc".into(), "x".into())];
        assert!(matches!(
            render_rfc5322(&m),
            Err(RenderError::HeaderInjection(_))
        ));
    }

    #[test]
    fn non_ascii_subject_is_rfc2047_encoded() {
        let mut m = sample();
        m.subject = "こんにちは".into();
        let text = String::from_utf8(render_rfc5322(&m).unwrap()).unwrap();
        // Should appear as an encoded-word, not raw UTF-8 in the header.
        assert!(text.contains("Subject: =?UTF-8?B?"), "text={text}");
        let expected = B64.encode("こんにちは".as_bytes());
        assert!(text.contains(&expected));
    }

    #[test]
    fn crlf_normalisation_is_idempotent() {
        // Body already in CRLF must not become CRCRLF.
        let mut m = sample();
        m.body = "a\r\nb\r\n".into();
        let text = String::from_utf8(render_rfc5322(&m).unwrap()).unwrap();
        assert!(text.ends_with("a\r\nb\r\n"));
        assert!(!text.contains("\r\r"));
    }

    #[test]
    fn dot_stuffing_doubles_leading_dots() {
        let msg = b"normal line\r\n.hidden command\r\n..already\r\n";
        let stuffed = dot_stuff(msg);
        let s = String::from_utf8(stuffed).unwrap();
        assert!(s.contains("\r\n..hidden command\r\n"));
        assert!(s.contains("\r\n...already\r\n"));
        // First line had no leading dot → unchanged.
        assert!(s.starts_with("normal line\r\n"));
    }
}
