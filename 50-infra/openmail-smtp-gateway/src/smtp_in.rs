//! Inbound SMTP command state machine (RFC 5321 subset).
//!
//! Pure and socket-free: feed it CRLF-stripped lines, get back a reply and, when a
//! `DATA` block terminates, the assembled [`InboundMessage`]. The `daemon` module
//! wraps this with a TCP listener. Keeping the protocol logic here lets the whole
//! command grammar be unit-tested without opening a socket.
//!
//! Supported verbs: `EHLO`/`HELO`, `MAIL FROM`, `RCPT TO`, `DATA`, `RSET`, `NOOP`,
//! `VRFY` (always 252), `QUIT`. STARTTLS/AUTH/pipelining are intentionally out of
//! scope for R0 (see README — TLS termination is expected to sit in front).

/// Hard caps. `MAX_RCPTS` mirrors the openmail lexicon `to` maxLength (100);
/// `MAX_DATA_BYTES` covers a 25 MiB body + header/MIME overhead.
pub const MAX_RCPTS: usize = 100;
pub const MAX_DATA_BYTES: usize = 26 * 1024 * 1024;
/// RFC 5321 §4.5.3.1: a command line (incl. verb) must accept ≥ 512 octets.
pub const MAX_COMMAND_LEN: usize = 998;

/// An SMTP reply. Single-line unless `extra_lines` is non-empty, in which case it
/// renders as an ESMTP multiline reply (`250-ext` … `250 final`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SmtpReply {
    pub code: u16,
    pub text: String,
    /// Capability/continuation lines emitted before the final line (EHLO response).
    pub extra_lines: Vec<String>,
}

impl SmtpReply {
    pub fn new(code: u16, text: impl Into<String>) -> Self {
        Self { code, text: text.into(), extra_lines: Vec::new() }
    }
    /// A multiline reply: each `extra_lines` entry precedes the final `text` line.
    pub fn multiline(code: u16, extra_lines: Vec<String>, final_line: impl Into<String>) -> Self {
        Self { code, text: final_line.into(), extra_lines }
    }
    /// Wire form, CRLF-terminated. Multiline uses `code-line` for all but the last.
    pub fn wire(&self) -> String {
        let mut out = String::new();
        for line in &self.extra_lines {
            out.push_str(&format!("{}-{}\r\n", self.code, line));
        }
        out.push_str(&format!("{} {}\r\n", self.code, self.text));
        out
    }
}

/// A fully received inbound message and its SMTP envelope.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct InboundMessage {
    /// Reverse-path from `MAIL FROM:<...>` (may be empty for a null sender bounce).
    pub mail_from: String,
    /// Forward-paths from `RCPT TO:<...>` (≥ 1).
    pub rcpts: Vec<String>,
    /// Raw RFC 5322 message bytes (dot-unstuffed, terminating "." removed).
    pub data: Vec<u8>,
}

/// What the caller should do after feeding a line.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Event {
    /// Send this reply and keep the connection open.
    Reply(SmtpReply),
    /// A message was fully received. Send `reply` (250 on accept) and the envelope
    /// is in `message`. The session resets to post-EHLO state for the next message.
    Complete { message: InboundMessage, reply: SmtpReply },
    /// Client issued STARTTLS: send `reply` (220), perform the TLS handshake, then
    /// call [`SmtpSession::reset_after_starttls`] before reading the next command
    /// (RFC 3207 — prior EHLO state is discarded).
    StartTls(SmtpReply),
    /// Send this reply and close the connection.
    Quit(SmtpReply),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Phase {
    /// Before EHLO/HELO.
    Start,
    /// After EHLO; awaiting MAIL FROM.
    Greeted,
    /// After MAIL FROM; awaiting RCPT TO (≥1) then DATA.
    Mail,
    /// Inside a DATA block, accumulating body lines.
    Data,
}

/// One SMTP-in conversation.
pub struct SmtpSession {
    phase: Phase,
    /// Hostname this gateway advertises in its greeting/EHLO response.
    hostname: String,
    mail_from: Option<String>,
    rcpts: Vec<String>,
    data: Vec<u8>,
    data_overflow: bool,
    /// True once the connection has been upgraded to TLS (STARTTLS completed).
    tls_active: bool,
}

impl SmtpSession {
    pub fn new(hostname: impl Into<String>) -> Self {
        Self {
            phase: Phase::Start,
            hostname: hostname.into(),
            mail_from: None,
            rcpts: Vec::new(),
            data: Vec::new(),
            data_overflow: false,
            tls_active: false,
        }
    }

    /// Reset after a completed TLS handshake (RFC 3207 §4.2): discard all session
    /// state and require a fresh EHLO over the encrypted channel.
    pub fn reset_after_starttls(&mut self) {
        self.phase = Phase::Start;
        self.mail_from = None;
        self.rcpts.clear();
        self.data.clear();
        self.data_overflow = false;
        self.tls_active = true;
    }

    /// The 220 banner to send immediately on connect.
    pub fn greeting(&self) -> SmtpReply {
        SmtpReply::new(220, format!("{} openmail ESMTP ready", self.hostname))
    }

    /// Reset envelope state but keep the EHLO greeting (RSET, or post-message).
    fn reset_transaction(&mut self) {
        self.mail_from = None;
        self.rcpts.clear();
        self.data.clear();
        self.data_overflow = false;
        if self.phase == Phase::Mail || self.phase == Phase::Data {
            self.phase = Phase::Greeted;
        }
    }

    /// Feed one line (without the trailing CRLF). In DATA mode the line is body
    /// content (or the terminating ".").
    pub fn feed_line(&mut self, line: &str) -> Event {
        if self.phase == Phase::Data {
            return self.feed_data_line(line);
        }
        if line.len() > MAX_COMMAND_LEN {
            return Event::Reply(SmtpReply::new(500, "line too long"));
        }
        self.feed_command(line)
    }

    fn feed_command(&mut self, line: &str) -> Event {
        let (verb, rest) = split_verb(line);
        match verb.as_str() {
            "EHLO" => {
                self.reset_transaction();
                self.phase = Phase::Greeted;
                // Advertise STARTTLS only when not already encrypted.
                let mut exts = vec![format!("{} greets {}", self.hostname, rest.trim())];
                if !self.tls_active {
                    exts.push("STARTTLS".to_string());
                }
                exts.push("8BITMIME".to_string());
                Event::Reply(SmtpReply::multiline(250, exts, format!("SIZE {MAX_DATA_BYTES}")))
            }
            "HELO" => {
                self.reset_transaction();
                self.phase = Phase::Greeted;
                Event::Reply(SmtpReply::new(
                    250,
                    format!("{} greets {}", self.hostname, rest.trim()),
                ))
            }
            "STARTTLS" => {
                if self.tls_active {
                    Event::Reply(SmtpReply::new(503, "already in TLS"))
                } else if self.phase == Phase::Start {
                    Event::Reply(SmtpReply::new(503, "send EHLO first"))
                } else {
                    // Caller performs the handshake, then reset_after_starttls().
                    Event::StartTls(SmtpReply::new(220, "ready to start TLS"))
                }
            }
            "MAIL" => self.cmd_mail(rest),
            "RCPT" => self.cmd_rcpt(rest),
            "DATA" => self.cmd_data(),
            "RSET" => {
                self.reset_transaction();
                Event::Reply(SmtpReply::new(250, "OK"))
            }
            "NOOP" => Event::Reply(SmtpReply::new(250, "OK")),
            "VRFY" => Event::Reply(SmtpReply::new(252, "cannot VRFY; accepting anyway")),
            "QUIT" => Event::Quit(SmtpReply::new(221, format!("{} closing", self.hostname))),
            "" => Event::Reply(SmtpReply::new(500, "empty command")),
            other => Event::Reply(SmtpReply::new(
                502,
                format!("command not implemented: {other}"),
            )),
        }
    }

    fn cmd_mail(&mut self, rest: &str) -> Event {
        if self.phase == Phase::Start {
            return Event::Reply(SmtpReply::new(503, "send EHLO first"));
        }
        // Already in a transaction → RFC 5321 says 503.
        if self.mail_from.is_some() {
            return Event::Reply(SmtpReply::new(503, "sender already given"));
        }
        match parse_path(rest, "FROM") {
            Some(addr) => {
                self.mail_from = Some(addr);
                self.phase = Phase::Mail;
                Event::Reply(SmtpReply::new(250, "OK"))
            }
            None => Event::Reply(SmtpReply::new(501, "syntax: MAIL FROM:<addr>")),
        }
    }

    fn cmd_rcpt(&mut self, rest: &str) -> Event {
        if self.phase != Phase::Mail {
            return Event::Reply(SmtpReply::new(503, "need MAIL FROM first"));
        }
        if self.rcpts.len() >= MAX_RCPTS {
            return Event::Reply(SmtpReply::new(452, "too many recipients"));
        }
        match parse_path(rest, "TO") {
            Some(addr) if !addr.is_empty() => {
                self.rcpts.push(addr);
                Event::Reply(SmtpReply::new(250, "OK"))
            }
            _ => Event::Reply(SmtpReply::new(501, "syntax: RCPT TO:<addr>")),
        }
    }

    fn cmd_data(&mut self) -> Event {
        if self.phase != Phase::Mail || self.rcpts.is_empty() {
            return Event::Reply(SmtpReply::new(503, "need MAIL FROM and ≥1 RCPT TO"));
        }
        self.phase = Phase::Data;
        Event::Reply(SmtpReply::new(354, "start mail input; end with <CRLF>.<CRLF>"))
    }

    fn feed_data_line(&mut self, line: &str) -> Event {
        // End-of-data marker.
        if line == "." {
            let reply = if self.data_overflow {
                self.reset_transaction();
                SmtpReply::new(552, "message exceeds size limit")
            } else {
                SmtpReply::new(250, "OK: message queued")
            };
            if reply.code != 250 {
                return Event::Reply(reply);
            }
            let message = InboundMessage {
                mail_from: self.mail_from.clone().unwrap_or_default(),
                rcpts: std::mem::take(&mut self.rcpts),
                data: std::mem::take(&mut self.data),
            };
            self.reset_transaction();
            return Event::Complete { message, reply };
        }

        // Transparency: a leading dot was doubled by the sender (RFC 5321 §4.5.2).
        let content = line.strip_prefix("..").map(|r| {
            let mut s = String::with_capacity(r.len() + 1);
            s.push('.');
            s.push_str(r);
            s
        });
        let payload = content.as_deref().unwrap_or(line);

        if self.data.len() + payload.len() + 2 > MAX_DATA_BYTES {
            // Keep consuming until "." (per RFC) but remember we'll 552 at the end.
            self.data_overflow = true;
            return Event::Reply(SmtpReply::new(250, "")); // no per-line reply in DATA
        }
        self.data.extend_from_slice(payload.as_bytes());
        self.data.extend_from_slice(b"\r\n");
        // No reply is emitted for body lines; the caller should not write Event
        // replies whose text is empty while in DATA. We signal this with code 0.
        Event::Reply(SmtpReply::new(0, ""))
    }
}

/// Split "VERB rest" → (UPPERCASE verb, rest). Verb is the token up to first space.
fn split_verb(line: &str) -> (String, &str) {
    match line.find(' ') {
        Some(i) => (line[..i].to_ascii_uppercase(), &line[i + 1..]),
        None => (line.to_ascii_uppercase(), ""),
    }
}

/// Parse `KEYWORD:<addr> [params]` (KEYWORD = FROM|TO) → the address inside <>.
/// Tolerates an optional space after the colon and trailing ESMTP params.
fn parse_path(rest: &str, keyword: &str) -> Option<String> {
    // rest looks like "FROM:<a@b> SIZE=1000" (verb already stripped).
    let rest = rest.trim_start();
    let upper = rest.to_ascii_uppercase();
    let prefix = format!("{keyword}:");
    if !upper.starts_with(&prefix) {
        return None;
    }
    let after = rest[prefix.len()..].trim_start();
    let start = after.find('<')?;
    let end = after[start..].find('>')? + start;
    Some(after[start + 1..end].trim().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn drive(session: &mut SmtpSession, line: &str) -> Event {
        session.feed_line(line)
    }

    #[test]
    fn greeting_advertises_hostname() {
        let s = SmtpSession::new("mx.openmail.etzhayyim.com");
        assert_eq!(s.greeting().code, 220);
        assert!(s.greeting().text.contains("mx.openmail.etzhayyim.com"));
        assert!(s.greeting().wire().ends_with("\r\n"));
    }

    #[test]
    fn full_happy_path_yields_envelope_and_body() {
        let mut s = SmtpSession::new("mx.etzhayyim.com");
        match drive(&mut s, "EHLO gmail.com") {
            Event::Reply(r) => {
                assert_eq!(r.code, 250);
                assert!(r.wire().contains("250-STARTTLS"), "EHLO must advertise STARTTLS: {}", r.wire());
            }
            other => panic!("expected multiline 250, got {other:?}"),
        }
        assert_eq!(drive(&mut s, "MAIL FROM:<alice@gmail.com>").as_code(), 250);
        assert_eq!(drive(&mut s, "RCPT TO:<bob@etzhayyim.com>").as_code(), 250);
        assert_eq!(drive(&mut s, "DATA").as_code(), 354);
        let _ = drive(&mut s, "Subject: hi");
        let _ = drive(&mut s, "");
        let _ = drive(&mut s, "Hello Bob");
        let ev = drive(&mut s, ".");
        match ev {
            Event::Complete { message, reply } => {
                assert_eq!(reply.code, 250);
                assert_eq!(message.mail_from, "alice@gmail.com");
                assert_eq!(message.rcpts, vec!["bob@etzhayyim.com"]);
                let body = String::from_utf8(message.data).unwrap();
                assert!(body.contains("Subject: hi\r\n"));
                assert!(body.contains("Hello Bob\r\n"));
            }
            other => panic!("expected Complete, got {other:?}"),
        }
    }

    #[test]
    fn rcpt_before_mail_is_bad_sequence() {
        let mut s = SmtpSession::new("h");
        drive(&mut s, "EHLO x");
        assert_eq!(drive(&mut s, "RCPT TO:<bob@etzhayyim.com>").as_code(), 503);
    }

    #[test]
    fn mail_before_ehlo_is_bad_sequence() {
        let mut s = SmtpSession::new("h");
        assert_eq!(drive(&mut s, "MAIL FROM:<a@b>").as_code(), 503);
    }

    #[test]
    fn data_before_rcpt_is_bad_sequence() {
        let mut s = SmtpSession::new("h");
        drive(&mut s, "EHLO x");
        drive(&mut s, "MAIL FROM:<a@b>");
        assert_eq!(drive(&mut s, "DATA").as_code(), 503);
    }

    #[test]
    fn dot_stuffing_is_reversed() {
        let mut s = SmtpSession::new("h");
        drive(&mut s, "EHLO x");
        drive(&mut s, "MAIL FROM:<a@b>");
        drive(&mut s, "RCPT TO:<bob@etzhayyim.com>");
        drive(&mut s, "DATA");
        drive(&mut s, "..leading dot line"); // wire ".." → body "."
        let ev = drive(&mut s, ".");
        if let Event::Complete { message, .. } = ev {
            let body = String::from_utf8(message.data).unwrap();
            assert!(body.contains(".leading dot line\r\n"), "body={body:?}");
        } else {
            panic!("expected Complete");
        }
    }

    #[test]
    fn multiple_recipients_accumulate() {
        let mut s = SmtpSession::new("h");
        drive(&mut s, "EHLO x");
        drive(&mut s, "MAIL FROM:<a@b>");
        drive(&mut s, "RCPT TO:<bob@etzhayyim.com>");
        drive(&mut s, "RCPT TO:<carol@etzhayyim.com>");
        drive(&mut s, "DATA");
        if let Event::Complete { message, .. } = drive(&mut s, ".") {
            assert_eq!(message.rcpts.len(), 2);
        } else {
            panic!();
        }
    }

    #[test]
    fn too_many_recipients_rejected() {
        let mut s = SmtpSession::new("h");
        drive(&mut s, "EHLO x");
        drive(&mut s, "MAIL FROM:<a@b>");
        for i in 0..MAX_RCPTS {
            assert_eq!(drive(&mut s, &format!("RCPT TO:<u{i}@etzhayyim.com>")).as_code(), 250);
        }
        assert_eq!(drive(&mut s, "RCPT TO:<overflow@etzhayyim.com>").as_code(), 452);
    }

    #[test]
    fn rset_clears_transaction() {
        let mut s = SmtpSession::new("h");
        drive(&mut s, "EHLO x");
        drive(&mut s, "MAIL FROM:<a@b>");
        drive(&mut s, "RCPT TO:<bob@etzhayyim.com>");
        assert_eq!(drive(&mut s, "RSET").as_code(), 250);
        // After RSET, RCPT without MAIL is a bad sequence again.
        assert_eq!(drive(&mut s, "RCPT TO:<bob@etzhayyim.com>").as_code(), 503);
    }

    #[test]
    fn quit_closes() {
        let mut s = SmtpSession::new("h");
        match drive(&mut s, "QUIT") {
            Event::Quit(r) => assert_eq!(r.code, 221),
            other => panic!("expected Quit, got {other:?}"),
        }
    }

    #[test]
    fn second_message_after_complete_reuses_greeting() {
        let mut s = SmtpSession::new("h");
        drive(&mut s, "EHLO x");
        drive(&mut s, "MAIL FROM:<a@b>");
        drive(&mut s, "RCPT TO:<bob@etzhayyim.com>");
        drive(&mut s, "DATA");
        let _ = drive(&mut s, ".");
        // No second EHLO required; MAIL FROM should work directly.
        assert_eq!(drive(&mut s, "MAIL FROM:<c@d>").as_code(), 250);
    }

    #[test]
    fn parse_path_tolerates_params_and_spacing() {
        assert_eq!(parse_path("FROM:<a@b> SIZE=100", "FROM").as_deref(), Some("a@b"));
        assert_eq!(parse_path("FROM: <a@b>", "FROM").as_deref(), Some("a@b"));
        assert_eq!(parse_path("TO:<bob@etzhayyim.com>", "TO").as_deref(), Some("bob@etzhayyim.com"));
        assert_eq!(parse_path("FROM:<>", "FROM").as_deref(), Some("")); // null sender
        assert_eq!(parse_path("FROM:alice", "FROM"), None);
    }

    #[test]
    fn unknown_command_is_502() {
        let mut s = SmtpSession::new("h");
        drive(&mut s, "EHLO x");
        assert_eq!(drive(&mut s, "FROBNICATE now").as_code(), 502);
    }

    // Helper to read a reply code regardless of Event variant.
    impl Event {
        fn as_code(&self) -> u16 {
            match self {
                Event::Reply(r) | Event::Quit(r) | Event::StartTls(r) => r.code,
                Event::Complete { reply, .. } => reply.code,
            }
        }
    }

    // ── STARTTLS ──────────────────────────────────────────────────────────────

    #[test]
    fn ehlo_advertises_starttls_then_starttls_yields_220() {
        let mut s = SmtpSession::new("mx");
        let _ = drive(&mut s, "EHLO client.example");
        match drive(&mut s, "STARTTLS") {
            Event::StartTls(r) => assert_eq!(r.code, 220),
            other => panic!("expected StartTls, got {other:?}"),
        }
    }

    #[test]
    fn starttls_before_ehlo_is_bad_sequence() {
        let mut s = SmtpSession::new("mx");
        assert_eq!(drive(&mut s, "STARTTLS").as_code(), 503);
    }

    #[test]
    fn after_starttls_reset_ehlo_does_not_readvertise_starttls() {
        let mut s = SmtpSession::new("mx");
        let _ = drive(&mut s, "EHLO c");
        let _ = drive(&mut s, "STARTTLS");
        s.reset_after_starttls();
        // Fresh EHLO required; STARTTLS must no longer be offered.
        match drive(&mut s, "EHLO c") {
            Event::Reply(r) => {
                assert_eq!(r.code, 250);
                assert!(!r.wire().contains("STARTTLS"), "must not re-advertise STARTTLS over TLS");
            }
            other => panic!("got {other:?}"),
        }
        // And a second STARTTLS is refused.
        assert_eq!(drive(&mut s, "STARTTLS").as_code(), 503);
    }

    #[test]
    fn helo_is_single_line_no_extensions() {
        let mut s = SmtpSession::new("mx");
        match drive(&mut s, "HELO c") {
            Event::Reply(r) => {
                assert!(r.extra_lines.is_empty());
                assert_eq!(r.code, 250);
            }
            other => panic!("got {other:?}"),
        }
    }
}
