//! Outbound SMTP *client* — the sending side of the bridge (ADR-2605172200 §3.2).
//!
//! Pure and socket-free, mirroring [`crate::smtp_in`]: drive it with the reply
//! *codes* a remote MX returns, and it yields the next command/action. The `daemon`
//! module wraps it on a TCP stream. This keeps the client conversation, MX-order
//! selection, and retry schedule unit-testable without a network.

use crate::render::dot_stuff;

/// One destination's delivery job. All `rcpts` must share a destination MX (group
/// recipients by domain first — see [`crate::outbound_route`]).
#[derive(Debug, Clone)]
pub struct OutboundMessage {
    /// Envelope reverse-path (`MAIL FROM`). Empty = null sender (bounces).
    pub mail_from: String,
    /// Envelope forward-paths for this MX.
    pub rcpts: Vec<String>,
    /// Full rendered + DKIM-signed RFC 5322 message (NOT yet dot-stuffed).
    pub data: Vec<u8>,
}

/// What the transport should do next, given the last server reply.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Action {
    /// Write this command line (transport appends CRLF).
    Send(String),
    /// Write this payload (already dot-stuffed) followed by the `.` terminator.
    SendData(Vec<u8>),
    /// Perform the TLS handshake now, then send a fresh `EHLO` over the encrypted
    /// channel (RFC 3207). The transport upgrades the socket and re-EHLOs.
    StartTls,
    /// All done — at least one recipient was accepted and the message was queued.
    Done { accepted: Vec<String>, rejected: Vec<String> },
    /// Fatal protocol error — give up on this MX (caller may try the next MX).
    Abort(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Step {
    Greeting,
    Ehlo,
    StartTls,
    MailFrom,
    Rcpt(usize),
    Data,
    Body,
    Quit,
    Finished,
}

/// A single SMTP delivery conversation to one MX.
pub struct SmtpClient {
    ehlo_name: String,
    msg: OutboundMessage,
    step: Step,
    accepted: Vec<String>,
    rejected: Vec<String>,
    use_starttls: bool,
    tls_active: bool,
}

impl SmtpClient {
    pub fn new(ehlo_name: impl Into<String>, msg: OutboundMessage) -> Self {
        Self {
            ehlo_name: ehlo_name.into(),
            msg,
            step: Step::Greeting,
            accepted: Vec::new(),
            rejected: Vec::new(),
            use_starttls: false,
            tls_active: false,
        }
    }

    /// Like [`new`](Self::new) but negotiates STARTTLS after the first EHLO and
    /// re-EHLOs over TLS before `MAIL FROM`.
    pub fn new_with_starttls(ehlo_name: impl Into<String>, msg: OutboundMessage) -> Self {
        let mut c = Self::new(ehlo_name, msg);
        c.use_starttls = true;
        c
    }

    /// Feed the server's reply code; get the next [`Action`]. 2xx = success,
    /// 3xx = intermediate (DATA), 4xx = transient, 5xx = permanent.
    pub fn on_reply(&mut self, code: u16) -> Action {
        match self.step {
            Step::Greeting => {
                if code == 220 {
                    self.step = Step::Ehlo;
                    Action::Send(format!("EHLO {}", self.ehlo_name))
                } else {
                    Action::Abort(format!("expected 220 greeting, got {code}"))
                }
            }
            Step::Ehlo => {
                if (200..300).contains(&code) {
                    if self.use_starttls && !self.tls_active {
                        self.step = Step::StartTls;
                        Action::Send("STARTTLS".into())
                    } else {
                        self.step = Step::MailFrom;
                        Action::Send(format!("MAIL FROM:<{}>", self.msg.mail_from))
                    }
                } else {
                    Action::Abort(format!("EHLO rejected: {code}"))
                }
            }
            Step::StartTls => {
                if code == 220 {
                    // Transport: handshake, then re-EHLO over TLS. The next reply
                    // re-enters Step::Ehlo with tls_active set → proceeds to MAIL FROM.
                    self.tls_active = true;
                    self.step = Step::Ehlo;
                    Action::StartTls
                } else {
                    Action::Abort(format!("STARTTLS rejected: {code}"))
                }
            }
            Step::MailFrom => {
                if code == 250 {
                    if self.msg.rcpts.is_empty() {
                        return Action::Abort("no recipients".into());
                    }
                    self.step = Step::Rcpt(0);
                    Action::Send(format!("RCPT TO:<{}>", self.msg.rcpts[0]))
                } else {
                    Action::Abort(format!("MAIL FROM rejected: {code}"))
                }
            }
            Step::Rcpt(i) => {
                // Record this recipient's outcome, then advance.
                if (200..300).contains(&code) {
                    self.accepted.push(self.msg.rcpts[i].clone());
                } else {
                    self.rejected.push(self.msg.rcpts[i].clone());
                }
                let next = i + 1;
                if next < self.msg.rcpts.len() {
                    self.step = Step::Rcpt(next);
                    Action::Send(format!("RCPT TO:<{}>", self.msg.rcpts[next]))
                } else if self.accepted.is_empty() {
                    // Every recipient was refused — no point sending DATA.
                    self.step = Step::Finished;
                    Action::Abort("all recipients rejected".into())
                } else {
                    self.step = Step::Data;
                    Action::Send("DATA".into())
                }
            }
            Step::Data => {
                if code == 354 {
                    self.step = Step::Body;
                    Action::SendData(dot_stuff(&self.msg.data))
                } else {
                    Action::Abort(format!("DATA rejected: {code}"))
                }
            }
            Step::Body => {
                if code == 250 {
                    self.step = Step::Quit;
                    Action::Send("QUIT".into())
                } else {
                    Action::Abort(format!("message body rejected: {code}"))
                }
            }
            Step::Quit => {
                self.step = Step::Finished;
                Action::Done {
                    accepted: std::mem::take(&mut self.accepted),
                    rejected: std::mem::take(&mut self.rejected),
                }
            }
            Step::Finished => Action::Abort("conversation already finished".into()),
        }
    }
}

// ── MX selection (RFC 5321 §5.1) ───────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MxRecord {
    pub preference: u16,
    pub host: String,
}

/// Order MX hosts by ascending preference (lower = tried first). Equal-preference
/// records keep input order here; a live resolver should shuffle them (RFC 5321
/// §5.1), which the caller can do — kept deterministic for testability.
pub fn select_mx(mut records: Vec<MxRecord>) -> Vec<String> {
    records.sort_by_key(|r| r.preference);
    records.into_iter().map(|r| r.host).collect()
}

/// Exponential retry schedule in seconds (RFC 5321 §4.5.4.1 spirit): quick first
/// retry, then back off, capping total span around 4–5 days. `attempt` 0 → first
/// delay. Returns the full schedule of `max_retries` delays.
pub fn retry_schedule(max_retries: usize) -> Vec<u64> {
    // 5min, 15min, 30min, 1h, 2h, 4h, then daily-ish, capped at 24h.
    const CAP: u64 = 24 * 3600;
    let mut out = Vec::with_capacity(max_retries);
    let mut delay = 300u64;
    for _ in 0..max_retries {
        out.push(delay.min(CAP));
        delay = (delay * 2).min(CAP);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn msg(rcpts: &[&str]) -> OutboundMessage {
        OutboundMessage {
            mail_from: "alice@etzhayyim.com".into(),
            rcpts: rcpts.iter().map(|s| s.to_string()).collect(),
            data: b"Subject: hi\r\n\r\n.dot line\r\nbody\r\n".to_vec(),
        }
    }

    /// Drive a full happy-path conversation through the client.
    #[test]
    fn happy_path_delivers_and_dot_stuffs() {
        let mut c = SmtpClient::new("mx.openmail.etzhayyim.com", msg(&["carol@yahoo.com"]));
        assert_eq!(c.on_reply(220), Action::Send("EHLO mx.openmail.etzhayyim.com".into()));
        assert_eq!(c.on_reply(250), Action::Send("MAIL FROM:<alice@etzhayyim.com>".into()));
        assert_eq!(c.on_reply(250), Action::Send("RCPT TO:<carol@yahoo.com>".into()));
        assert_eq!(c.on_reply(250), Action::Send("DATA".into()));
        match c.on_reply(354) {
            Action::SendData(payload) => {
                let s = String::from_utf8(payload).unwrap();
                // leading-dot line must be stuffed to "..dot line".
                assert!(s.contains("\r\n..dot line\r\n"), "payload={s:?}");
            }
            other => panic!("expected SendData, got {other:?}"),
        }
        assert_eq!(c.on_reply(250), Action::Send("QUIT".into()));
        match c.on_reply(221) {
            Action::Done { accepted, rejected } => {
                assert_eq!(accepted, vec!["carol@yahoo.com"]);
                assert!(rejected.is_empty());
            }
            other => panic!("expected Done, got {other:?}"),
        }
    }

    #[test]
    fn partial_recipient_rejection_still_sends() {
        let mut c = SmtpClient::new("h", msg(&["good@x.com", "bad@x.com"]));
        c.on_reply(220);
        c.on_reply(250); // EHLO
        c.on_reply(250); // MAIL FROM → RCPT good
        // good accepted → RCPT bad
        let a = c.on_reply(250);
        assert_eq!(a, Action::Send("RCPT TO:<bad@x.com>".into()));
        // bad rejected (550) → since one accepted, proceed to DATA
        assert_eq!(c.on_reply(550), Action::Send("DATA".into()));
        c.on_reply(354);
        c.on_reply(250);
        match c.on_reply(221) {
            Action::Done { accepted, rejected } => {
                assert_eq!(accepted, vec!["good@x.com"]);
                assert_eq!(rejected, vec!["bad@x.com"]);
            }
            other => panic!("got {other:?}"),
        }
    }

    #[test]
    fn all_recipients_rejected_aborts_before_data() {
        let mut c = SmtpClient::new("h", msg(&["bad@x.com"]));
        c.on_reply(220);
        c.on_reply(250);
        c.on_reply(250); // → RCPT bad
        match c.on_reply(550) {
            Action::Abort(m) => assert!(m.contains("all recipients rejected")),
            other => panic!("got {other:?}"),
        }
    }

    #[test]
    fn bad_greeting_aborts() {
        let mut c = SmtpClient::new("h", msg(&["x@y.com"]));
        assert!(matches!(c.on_reply(554), Action::Abort(_)));
    }

    #[test]
    fn data_refused_aborts() {
        let mut c = SmtpClient::new("h", msg(&["x@y.com"]));
        c.on_reply(220);
        c.on_reply(250);
        c.on_reply(250);
        c.on_reply(250); // DATA
        assert!(matches!(c.on_reply(503), Action::Abort(_)));
    }

    #[test]
    fn starttls_negotiation_upgrades_then_reehlos() {
        let mut c = SmtpClient::new_with_starttls("mx.openmail.etzhayyim.com", msg(&["carol@yahoo.com"]));
        assert_eq!(c.on_reply(220), Action::Send("EHLO mx.openmail.etzhayyim.com".into()));
        // First EHLO → STARTTLS (not MAIL FROM yet).
        assert_eq!(c.on_reply(250), Action::Send("STARTTLS".into()));
        // 220 → handshake signal; transport upgrades + re-EHLOs.
        assert_eq!(c.on_reply(220), Action::StartTls);
        // After re-EHLO over TLS, proceed to MAIL FROM.
        assert_eq!(c.on_reply(250), Action::Send("MAIL FROM:<alice@etzhayyim.com>".into()));
    }

    #[test]
    fn starttls_rejected_aborts() {
        let mut c = SmtpClient::new_with_starttls("h", msg(&["x@y.com"]));
        c.on_reply(220);
        c.on_reply(250); // → STARTTLS
        assert!(matches!(c.on_reply(454), Action::Abort(_)));
    }

    #[test]
    fn without_starttls_goes_straight_to_mail_from() {
        let mut c = SmtpClient::new("h", msg(&["x@y.com"]));
        c.on_reply(220);
        assert_eq!(c.on_reply(250), Action::Send("MAIL FROM:<alice@etzhayyim.com>".into()));
    }

    #[test]
    fn mx_selected_by_ascending_preference() {
        let recs = vec![
            MxRecord { preference: 20, host: "mx2.example".into() },
            MxRecord { preference: 10, host: "mx1.example".into() },
            MxRecord { preference: 30, host: "mx3.example".into() },
        ];
        assert_eq!(select_mx(recs), vec!["mx1.example", "mx2.example", "mx3.example"]);
    }

    #[test]
    fn retry_schedule_is_increasing_and_capped() {
        let s = retry_schedule(8);
        assert_eq!(s.len(), 8);
        assert_eq!(s[0], 300);
        // monotonic non-decreasing
        for w in s.windows(2) {
            assert!(w[1] >= w[0]);
        }
        // capped at 24h
        assert!(*s.last().unwrap() <= 24 * 3600);
    }
}
