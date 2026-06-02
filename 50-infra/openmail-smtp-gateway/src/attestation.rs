//! Build the `app.openmail.smtpAttestation` record (ADR-2605172200 §2, §3.1).
//!
//! Inbound bridged mail carries an attestation of the sender's DKIM/SPF/DMARC
//! verification so the recipient client can distinguish "legacy bridged, checks
//! passed" from spoofable mail. Pure: maps the verification results to the lexicon's
//! string enums + JSON shape.

use serde_json::{json, Value};

use crate::dmarc::DmarcResult;
use crate::spf::SpfResult;

/// DKIM outcome for the attestation (the lexicon allows pass/fail/neutral/none).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DkimOutcome {
    Pass,
    Fail,
    None,
}

fn dkim_str(d: DkimOutcome) -> &'static str {
    match d {
        DkimOutcome::Pass => "pass",
        DkimOutcome::Fail => "fail",
        DkimOutcome::None => "none",
    }
}

fn spf_str(s: SpfResult) -> &'static str {
    match s {
        SpfResult::Pass => "pass",
        SpfResult::Fail => "fail",
        SpfResult::SoftFail => "softfail",
        SpfResult::Neutral => "neutral",
        SpfResult::None => "none",
        SpfResult::PermError => "permerror",
    }
}

fn dmarc_str(d: &DmarcResult) -> &'static str {
    match d {
        DmarcResult::Pass => "pass",
        DmarcResult::Fail(_) => "fail",
    }
}

/// Build the `app.openmail.smtpAttestation` JSON. `verified_at` is supplied by the
/// caller (this module is clock-free). `spam_score` is the optional inbound filter
/// score (0.0–1.0+).
pub fn build(
    dkim: DkimOutcome,
    spf: SpfResult,
    dmarc: &DmarcResult,
    spam_score: Option<f64>,
    verified_at: &str,
) -> Value {
    let mut v = json!({
        "$type": "app.openmail.smtpAttestation",
        "dkim": dkim_str(dkim),
        "spf": spf_str(spf),
        "dmarc": dmarc_str(dmarc),
        "verifiedAt": verified_at,
    });
    if let Some(score) = spam_score {
        v["spamScore"] = json!(score);
    }
    v
}

/// Whether inbound policy should accept this message (RFC 7489: a DMARC `reject`
/// disposition means refuse at SMTP time). Returns the SMTP rejection reason if it
/// must be refused, else `None` (accept).
pub fn smtp_rejection(dmarc: &DmarcResult) -> Option<(u16, &'static str)> {
    match dmarc {
        DmarcResult::Pass => None,
        DmarcResult::Fail(crate::dmarc::Policy::Reject) => {
            Some((550, "5.7.1 DMARC policy reject"))
        }
        // quarantine / none → accept but flag (recipient-side filtering).
        DmarcResult::Fail(_) => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dmarc::Policy;

    #[test]
    fn builds_passing_attestation() {
        let a = build(DkimOutcome::Pass, SpfResult::Pass, &DmarcResult::Pass, Some(0.02), "2026-06-02T00:00:00Z");
        assert_eq!(a["$type"], "app.openmail.smtpAttestation");
        assert_eq!(a["dkim"], "pass");
        assert_eq!(a["spf"], "pass");
        assert_eq!(a["dmarc"], "pass");
        assert_eq!(a["spamScore"], 0.02);
        assert_eq!(a["verifiedAt"], "2026-06-02T00:00:00Z");
    }

    #[test]
    fn maps_all_spf_results() {
        for (r, s) in [
            (SpfResult::SoftFail, "softfail"),
            (SpfResult::Neutral, "neutral"),
            (SpfResult::PermError, "permerror"),
            (SpfResult::None, "none"),
            (SpfResult::Fail, "fail"),
        ] {
            let a = build(DkimOutcome::None, r, &DmarcResult::Pass, None, "t");
            assert_eq!(a["spf"], s);
        }
    }

    #[test]
    fn spam_score_omitted_when_none() {
        let a = build(DkimOutcome::Fail, SpfResult::Fail, &DmarcResult::Fail(Policy::None), None, "t");
        assert!(a.get("spamScore").is_none());
        assert_eq!(a["dkim"], "fail");
        assert_eq!(a["dmarc"], "fail");
    }

    #[test]
    fn dmarc_reject_yields_smtp_550() {
        assert_eq!(smtp_rejection(&DmarcResult::Fail(Policy::Reject)), Some((550, "5.7.1 DMARC policy reject")));
    }

    #[test]
    fn dmarc_pass_and_quarantine_accept_at_smtp() {
        assert_eq!(smtp_rejection(&DmarcResult::Pass), None);
        assert_eq!(smtp_rejection(&DmarcResult::Fail(Policy::Quarantine)), None);
        assert_eq!(smtp_rejection(&DmarcResult::Fail(Policy::None)), None);
    }
}
