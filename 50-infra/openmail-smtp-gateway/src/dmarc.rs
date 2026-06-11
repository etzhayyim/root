//! DMARC alignment + disposition (RFC 7489) — inbound (ADR-2605172200 §3.1).
//!
//! Pure: given the `From:` domain, the parsed `_dmarc` record, and the DKIM + SPF
//! results, compute whether DMARC passes and, if not, which policy to apply. The
//! `_dmarc` TXT lookup is the daemon edge.
//!
//! R0 note: the organizational-domain function approximates eTLD+1 as the last two
//! labels — correct for `*.example.com`, wrong for multi-label public suffixes
//! (`example.co.uk`). A Public Suffix List lookup is the documented upgrade.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Policy {
    None,
    Quarantine,
    Reject,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Alignment {
    Strict,
    Relaxed,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DmarcRecord {
    pub policy: Policy,
    pub subdomain_policy: Option<Policy>,
    pub adkim: Alignment,
    pub aspf: Alignment,
    pub pct: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DmarcResult {
    Pass,
    /// DMARC failed; apply this policy (`pct` sampling is the caller's concern).
    Fail(Policy),
}

/// Inputs gathered from the DKIM + SPF checks.
#[derive(Debug, Clone)]
pub struct DmarcInput {
    pub from_domain: String,
    pub dkim_pass: bool,
    pub dkim_d_domain: String,
    pub spf_pass: bool,
    pub spf_mailfrom_domain: String,
}

/// Parse a `_dmarc` TXT record (`v=DMARC1; p=reject; adkim=s; ...`).
pub fn parse(record: &str) -> Result<DmarcRecord, String> {
    let mut tags = std::collections::HashMap::new();
    let mut iter = record.split(';');
    match iter.next().map(|s| s.trim()) {
        Some(v) if v.eq_ignore_ascii_case("v=DMARC1") => {}
        _ => return Err("not a DMARC1 record".into()),
    }
    for seg in iter {
        let seg = seg.trim();
        if seg.is_empty() {
            continue;
        }
        if let Some((k, v)) = seg.split_once('=') {
            tags.insert(k.trim().to_ascii_lowercase(), v.trim().to_string());
        }
    }
    let policy = parse_policy(tags.get("p").ok_or("DMARC missing p=")?)?;
    let subdomain_policy = tags.get("sp").map(|s| parse_policy(s)).transpose()?;
    Ok(DmarcRecord {
        policy,
        subdomain_policy,
        adkim: parse_alignment(tags.get("adkim")),
        aspf: parse_alignment(tags.get("aspf")),
        pct: tags.get("pct").and_then(|s| s.parse().ok()).unwrap_or(100),
    })
}

fn parse_policy(s: &str) -> Result<Policy, String> {
    match s.to_ascii_lowercase().as_str() {
        "none" => Ok(Policy::None),
        "quarantine" => Ok(Policy::Quarantine),
        "reject" => Ok(Policy::Reject),
        other => Err(format!("bad DMARC policy: {other}")),
    }
}

fn parse_alignment(s: Option<&String>) -> Alignment {
    match s.map(|x| x.as_str()) {
        Some("s") => Alignment::Strict,
        _ => Alignment::Relaxed, // default
    }
}

/// Registrable domain approximation: last two labels (R0 — see module note).
pub fn org_domain(domain: &str) -> String {
    let labels: Vec<&str> = domain.trim_end_matches('.').split('.').collect();
    if labels.len() <= 2 {
        domain.trim_end_matches('.').to_ascii_lowercase()
    } else {
        labels[labels.len() - 2..].join(".").to_ascii_lowercase()
    }
}

fn aligned(a: &str, b: &str, mode: Alignment) -> bool {
    let (a, b) = (a.to_ascii_lowercase(), b.to_ascii_lowercase());
    match mode {
        Alignment::Strict => a == b,
        Alignment::Relaxed => org_domain(&a) == org_domain(&b),
    }
}

/// True if the DKIM `d=` domain aligns with the `From:` domain under `mode`.
pub fn dkim_aligned(from_domain: &str, dkim_d_domain: &str, mode: Alignment) -> bool {
    aligned(from_domain, dkim_d_domain, mode)
}

/// True if the SPF `MAIL FROM` domain aligns with the `From:` domain under `mode`.
pub fn spf_aligned(from_domain: &str, mailfrom_domain: &str, mode: Alignment) -> bool {
    aligned(from_domain, mailfrom_domain, mode)
}

/// Evaluate DMARC: passes if an aligned, passing DKIM **or** SPF result exists.
pub fn evaluate(record: &DmarcRecord, input: &DmarcInput) -> DmarcResult {
    let dkim_ok = input.dkim_pass && dkim_aligned(&input.from_domain, &input.dkim_d_domain, record.adkim);
    let spf_ok = input.spf_pass && spf_aligned(&input.from_domain, &input.spf_mailfrom_domain, record.aspf);
    if dkim_ok || spf_ok {
        DmarcResult::Pass
    } else {
        DmarcResult::Fail(record.policy)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rec(p: &str) -> DmarcRecord {
        parse(&format!("v=DMARC1; p={p}")).unwrap()
    }

    #[test]
    fn parses_record_with_all_tags() {
        let r = parse("v=DMARC1; p=reject; sp=quarantine; adkim=s; aspf=r; pct=50").unwrap();
        assert_eq!(r.policy, Policy::Reject);
        assert_eq!(r.subdomain_policy, Some(Policy::Quarantine));
        assert_eq!(r.adkim, Alignment::Strict);
        assert_eq!(r.aspf, Alignment::Relaxed);
        assert_eq!(r.pct, 50);
    }

    #[test]
    fn defaults_relaxed_and_pct_100() {
        let r = rec("none");
        assert_eq!(r.adkim, Alignment::Relaxed);
        assert_eq!(r.aspf, Alignment::Relaxed);
        assert_eq!(r.pct, 100);
    }

    #[test]
    fn rejects_non_dmarc() {
        assert!(parse("v=spf1 -all").is_err());
    }

    #[test]
    fn org_domain_last_two_labels() {
        assert_eq!(org_domain("mail.football.example.com"), "example.com");
        assert_eq!(org_domain("example.com"), "example.com");
        assert_eq!(org_domain("EXAMPLE.COM"), "example.com");
    }

    #[test]
    fn relaxed_dkim_alignment_on_subdomain() {
        assert!(dkim_aligned("etzhayyim.com", "mail.etzhayyim.com", Alignment::Relaxed));
        assert!(!dkim_aligned("etzhayyim.com", "mail.etzhayyim.com", Alignment::Strict));
        assert!(dkim_aligned("etzhayyim.com", "etzhayyim.com", Alignment::Strict));
    }

    #[test]
    fn passes_on_aligned_dkim() {
        let input = DmarcInput {
            from_domain: "etzhayyim.com".into(),
            dkim_pass: true,
            dkim_d_domain: "etzhayyim.com".into(),
            spf_pass: false,
            spf_mailfrom_domain: "bounce.other.com".into(),
        };
        assert_eq!(evaluate(&rec("reject"), &input), DmarcResult::Pass);
    }

    #[test]
    fn passes_on_aligned_spf_even_if_dkim_fails() {
        let input = DmarcInput {
            from_domain: "etzhayyim.com".into(),
            dkim_pass: false,
            dkim_d_domain: "".into(),
            spf_pass: true,
            spf_mailfrom_domain: "mail.etzhayyim.com".into(),
        };
        assert_eq!(evaluate(&rec("reject"), &input), DmarcResult::Pass);
    }

    #[test]
    fn fails_with_policy_when_unaligned() {
        let input = DmarcInput {
            from_domain: "etzhayyim.com".into(),
            dkim_pass: true,
            dkim_d_domain: "evil.example".into(), // passing DKIM but wrong domain
            spf_pass: true,
            spf_mailfrom_domain: "evil.example".into(),
        };
        assert_eq!(evaluate(&rec("quarantine"), &input), DmarcResult::Fail(Policy::Quarantine));
        assert_eq!(evaluate(&rec("reject"), &input), DmarcResult::Fail(Policy::Reject));
    }

    #[test]
    fn dkim_pass_but_not_aligned_does_not_pass_dmarc() {
        // A valid DKIM signature from a foreign domain must NOT authorize From.
        let input = DmarcInput {
            from_domain: "etzhayyim.com".into(),
            dkim_pass: true,
            dkim_d_domain: "mailchimp.com".into(),
            spf_pass: false,
            spf_mailfrom_domain: "x".into(),
        };
        assert!(matches!(evaluate(&rec("reject"), &input), DmarcResult::Fail(_)));
    }
}
