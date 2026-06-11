//! Map inbound delivery outcomes to SMTP reply codes (ADR-2605172200 §3.1).
//!
//! After `DATA`, SMTP returns a single final reply for the whole message. This pure
//! module turns the per-recipient delivery results (from relaying each RCPT to
//! `email.ingest`) into that one code, and into per-recipient codes for bounces/logs.

/// Outcome of delivering the message to one recipient.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Delivery {
    /// `email.ingest` accepted it.
    Delivered,
    /// Local domain but no such mailbox.
    NoSuchUser,
    /// Address is not in a domain we serve.
    RelayDenied,
    /// Temporary failure (network / kotoba 5xx) — sender should retry the message.
    Transient,
    /// Permanent rejection (e.g. too large, malformed).
    PermanentReject,
}

/// The SMTP code + enhanced status for one recipient (for bounce generation / logs).
pub fn recipient_code(d: Delivery) -> (u16, &'static str) {
    match d {
        Delivery::Delivered => (250, "2.1.5 delivered"),
        Delivery::NoSuchUser => (550, "5.1.1 no such user"),
        Delivery::RelayDenied => (550, "5.7.1 relaying denied"),
        Delivery::Transient => (451, "4.3.0 temporary failure, try again later"),
        Delivery::PermanentReject => (554, "5.6.0 message rejected"),
    }
}

/// The single final reply after `DATA`, aggregated across recipients.
///
/// Precedence: any transient failure ⇒ 451 (sender retries the whole message, since
/// SMTP can't selectively re-deliver). Otherwise, all-delivered ⇒ 250; all-failed ⇒
/// 550; a mix of delivered + permanent failures ⇒ 250 (the deliverable copies are
/// queued; the bridge bounces the rest out-of-band).
pub fn final_reply(outcomes: &[Delivery]) -> (u16, String) {
    if outcomes.is_empty() {
        return (554, "5.5.0 no recipients delivered".into());
    }
    if outcomes.contains(&Delivery::Transient) {
        return (451, "4.3.0 temporary failure, try again later".into());
    }
    let delivered = outcomes.iter().filter(|o| **o == Delivery::Delivered).count();
    if delivered == outcomes.len() {
        (250, "2.0.0 message accepted".into())
    } else if delivered == 0 {
        (550, "5.1.1 no recipients could be delivered".into())
    } else {
        (250, "2.0.0 message accepted for deliverable recipients".into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use Delivery::*;

    #[test]
    fn all_delivered_is_250() {
        assert_eq!(final_reply(&[Delivered, Delivered]).0, 250);
    }

    #[test]
    fn any_transient_is_451() {
        assert_eq!(final_reply(&[Delivered, Transient]).0, 451);
        // transient wins even over permanent rejects (sender should retry).
        assert_eq!(final_reply(&[PermanentReject, Transient]).0, 451);
    }

    #[test]
    fn all_failed_is_550() {
        assert_eq!(final_reply(&[NoSuchUser, RelayDenied]).0, 550);
        assert_eq!(final_reply(&[PermanentReject]).0, 550);
    }

    #[test]
    fn mixed_delivered_and_permanent_is_250() {
        assert_eq!(final_reply(&[Delivered, NoSuchUser]).0, 250);
    }

    #[test]
    fn empty_is_554() {
        assert_eq!(final_reply(&[]).0, 554);
    }

    #[test]
    fn recipient_codes_are_in_expected_classes() {
        assert_eq!(recipient_code(Delivered).0, 250);
        assert_eq!(recipient_code(NoSuchUser).0, 550);
        assert_eq!(recipient_code(RelayDenied).0, 550);
        assert_eq!(recipient_code(Transient).0, 451);
        assert_eq!(recipient_code(PermanentReject).0, 554);
    }
}
