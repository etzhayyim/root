//! SPF evaluation (RFC 7208) — inbound sender authorization (ADR-2605172200 §3.1).
//!
//! Pure: `ip4`/`ip6`/`all` mechanisms + qualifiers are evaluated directly; the
//! DNS-requiring mechanisms (`a`/`mx`/`include`/`exists`/`ptr`) are delegated to an
//! injected [`SpfResolver`] so first-match order and per-mechanism qualifiers are
//! preserved while the network lookup stays at the daemon edge. Tests use a mock
//! resolver; the daemon supplies a DNS-backed one.

use std::net::{IpAddr, Ipv4Addr, Ipv6Addr};

/// SPF qualifier prefixing a mechanism (`+` pass, `-` fail, `~` softfail, `?` neutral).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Qualifier {
    Pass,
    Fail,
    SoftFail,
    Neutral,
}

/// A parsed SPF mechanism.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Mechanism {
    Ip4(Ipv4Addr, u8),
    Ip6(Ipv6Addr, u8),
    A(Option<String>),
    Mx(Option<String>),
    Include(String),
    Exists(String),
    Ptr(Option<String>),
    All,
}

/// Final SPF result (RFC 7208 §2.6).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpfResult {
    Pass,
    Fail,
    SoftFail,
    Neutral,
    None,
    PermError,
}

/// Resolves the DNS-backed mechanisms. The daemon implements this with real lookups
/// (including `include:` recursion); tests inject a deterministic mock.
pub trait SpfResolver {
    /// Does `ip` match this DNS mechanism (`a`/`mx`/`include`/`exists`/`ptr`)?
    fn mechanism_matches(&self, mechanism: &Mechanism, ip: IpAddr) -> bool;
}

/// A resolver that matches nothing — for evaluating ip-only records.
pub struct NoDnsResolver;
impl SpfResolver for NoDnsResolver {
    fn mechanism_matches(&self, _: &Mechanism, _: IpAddr) -> bool {
        false
    }
}

/// Parse an SPF record (`v=spf1 ...`) into qualifier+mechanism terms.
pub fn parse(record: &str) -> Result<Vec<(Qualifier, Mechanism)>, String> {
    let record = record.trim();
    let mut terms = record.split_whitespace();
    match terms.next() {
        Some(v) if v.eq_ignore_ascii_case("v=spf1") => {}
        _ => return Err("not an spf1 record".into()),
    }
    let mut out = Vec::new();
    for term in terms {
        // Skip modifiers (redirect=, exp=) — handled separately / ignored in R0.
        if term.contains('=') {
            continue;
        }
        let (qual, rest) = match term.as_bytes()[0] {
            b'+' => (Qualifier::Pass, &term[1..]),
            b'-' => (Qualifier::Fail, &term[1..]),
            b'~' => (Qualifier::SoftFail, &term[1..]),
            b'?' => (Qualifier::Neutral, &term[1..]),
            _ => (Qualifier::Pass, term),
        };
        out.push((qual, parse_mechanism(rest)?));
    }
    Ok(out)
}

fn parse_mechanism(s: &str) -> Result<Mechanism, String> {
    let lower = s.to_ascii_lowercase();
    if lower == "all" {
        return Ok(Mechanism::All);
    }
    if let Some(v) = lower.strip_prefix("ip4:") {
        let (addr, prefix) = split_cidr(v, 32)?;
        let ip: Ipv4Addr = addr.parse().map_err(|_| format!("bad ip4: {v}"))?;
        return Ok(Mechanism::Ip4(ip, prefix));
    }
    if let Some(v) = lower.strip_prefix("ip6:") {
        // ip6 may contain ':' so split on the LAST '/'.
        let (addr, prefix) = split_cidr(v, 128)?;
        let ip: Ipv6Addr = addr.parse().map_err(|_| format!("bad ip6: {v}"))?;
        return Ok(Mechanism::Ip6(ip, prefix));
    }
    if lower == "a" {
        return Ok(Mechanism::A(None));
    }
    if let Some(v) = lower.strip_prefix("a:") {
        return Ok(Mechanism::A(Some(v.to_string())));
    }
    if lower == "mx" {
        return Ok(Mechanism::Mx(None));
    }
    if let Some(v) = lower.strip_prefix("mx:") {
        return Ok(Mechanism::Mx(Some(v.to_string())));
    }
    if let Some(v) = lower.strip_prefix("include:") {
        return Ok(Mechanism::Include(v.to_string()));
    }
    if let Some(v) = lower.strip_prefix("exists:") {
        return Ok(Mechanism::Exists(v.to_string()));
    }
    if lower == "ptr" {
        return Ok(Mechanism::Ptr(None));
    }
    if let Some(v) = lower.strip_prefix("ptr:") {
        return Ok(Mechanism::Ptr(Some(v.to_string())));
    }
    Err(format!("unknown mechanism: {s}"))
}

fn split_cidr(v: &str, max: u8) -> Result<(String, u8), String> {
    match v.rsplit_once('/') {
        Some((addr, p)) => {
            let prefix: u8 = p.parse().map_err(|_| format!("bad prefix: {p}"))?;
            if prefix > max {
                return Err(format!("prefix {prefix} > {max}"));
            }
            Ok((addr.to_string(), prefix))
        }
        None => Ok((v.to_string(), max)),
    }
}

/// Evaluate the parsed record against `ip`. First matching mechanism wins (RFC 7208
/// §4.6.2). DNS mechanisms are matched via `resolver`.
pub fn evaluate(
    terms: &[(Qualifier, Mechanism)],
    ip: IpAddr,
    resolver: &dyn SpfResolver,
) -> SpfResult {
    for (qual, mech) in terms {
        let matched = match mech {
            Mechanism::Ip4(net, prefix) => match ip {
                IpAddr::V4(v4) => v4_in_cidr(*net, *prefix, v4),
                IpAddr::V6(_) => false,
            },
            Mechanism::Ip6(net, prefix) => match ip {
                IpAddr::V6(v6) => v6_in_cidr(*net, *prefix, v6),
                IpAddr::V4(_) => false,
            },
            Mechanism::All => true,
            // DNS-backed mechanisms.
            _ => resolver.mechanism_matches(mech, ip),
        };
        if matched {
            return match qual {
                Qualifier::Pass => SpfResult::Pass,
                Qualifier::Fail => SpfResult::Fail,
                Qualifier::SoftFail => SpfResult::SoftFail,
                Qualifier::Neutral => SpfResult::Neutral,
            };
        }
    }
    // No mechanism matched and no `all` present → Neutral (RFC 7208 §4.7 default).
    SpfResult::Neutral
}

/// Parse + evaluate in one shot. A malformed record is a PermError.
pub fn check(record: &str, ip: IpAddr, resolver: &dyn SpfResolver) -> SpfResult {
    match parse(record) {
        Ok(terms) => evaluate(&terms, ip, resolver),
        Err(_) => SpfResult::PermError,
    }
}

fn v4_in_cidr(net: Ipv4Addr, prefix: u8, ip: Ipv4Addr) -> bool {
    if prefix == 0 {
        return true;
    }
    let mask: u32 = u32::MAX << (32 - prefix as u32);
    (u32::from(net) & mask) == (u32::from(ip) & mask)
}

fn v6_in_cidr(net: Ipv6Addr, prefix: u8, ip: Ipv6Addr) -> bool {
    if prefix == 0 {
        return true;
    }
    let mask: u128 = u128::MAX << (128 - prefix as u32);
    (u128::from(net) & mask) == (u128::from(ip) & mask)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ip(s: &str) -> IpAddr {
        s.parse().unwrap()
    }

    #[test]
    fn parses_basic_record() {
        let terms = parse("v=spf1 ip4:192.0.2.0/24 ip6:2001:db8::/32 -all").unwrap();
        assert_eq!(terms.len(), 3);
        assert_eq!(terms[0].0, Qualifier::Pass);
        assert!(matches!(terms[0].1, Mechanism::Ip4(_, 24)));
        assert_eq!(terms[2], (Qualifier::Fail, Mechanism::All));
    }

    #[test]
    fn rejects_non_spf_record() {
        assert!(parse("v=DKIM1; k=rsa").is_err());
    }

    #[test]
    fn ip4_match_passes() {
        let t = parse("v=spf1 ip4:192.0.2.0/24 -all").unwrap();
        assert_eq!(evaluate(&t, ip("192.0.2.55"), &NoDnsResolver), SpfResult::Pass);
    }

    #[test]
    fn ip4_outside_range_hits_all_fail() {
        let t = parse("v=spf1 ip4:192.0.2.0/24 -all").unwrap();
        assert_eq!(evaluate(&t, ip("198.51.100.1"), &NoDnsResolver), SpfResult::Fail);
    }

    #[test]
    fn softfail_all_qualifier() {
        let t = parse("v=spf1 ip4:10.0.0.0/8 ~all").unwrap();
        assert_eq!(evaluate(&t, ip("8.8.8.8"), &NoDnsResolver), SpfResult::SoftFail);
    }

    #[test]
    fn exact_ip4_no_prefix_is_slash32() {
        let t = parse("v=spf1 ip4:203.0.113.7 -all").unwrap();
        assert_eq!(evaluate(&t, ip("203.0.113.7"), &NoDnsResolver), SpfResult::Pass);
        assert_eq!(evaluate(&t, ip("203.0.113.8"), &NoDnsResolver), SpfResult::Fail);
    }

    #[test]
    fn ip6_match() {
        let t = parse("v=spf1 ip6:2001:db8::/32 -all").unwrap();
        assert_eq!(evaluate(&t, ip("2001:db8:1234::1"), &NoDnsResolver), SpfResult::Pass);
        assert_eq!(evaluate(&t, ip("2001:dead::1"), &NoDnsResolver), SpfResult::Fail);
    }

    #[test]
    fn no_all_and_no_match_is_neutral() {
        let t = parse("v=spf1 ip4:192.0.2.0/24").unwrap();
        assert_eq!(evaluate(&t, ip("8.8.8.8"), &NoDnsResolver), SpfResult::Neutral);
    }

    #[test]
    fn malformed_is_permerror() {
        assert_eq!(check("v=spf1 ip4:not-an-ip -all", ip("1.1.1.1"), &NoDnsResolver), SpfResult::PermError);
    }

    // DNS mechanism via injected resolver, preserving order + qualifier.
    struct MockResolver;
    impl SpfResolver for MockResolver {
        fn mechanism_matches(&self, m: &Mechanism, _ip: IpAddr) -> bool {
            matches!(m, Mechanism::Include(d) if d == "_spf.google.com")
        }
    }

    #[test]
    fn include_match_via_resolver_passes() {
        let t = parse("v=spf1 include:_spf.google.com -all").unwrap();
        assert_eq!(evaluate(&t, ip("172.217.0.1"), &MockResolver), SpfResult::Pass);
    }

    #[test]
    fn first_match_wins_order_preserved() {
        // -include matches first (fail) before ~all.
        let t = parse("v=spf1 -include:_spf.google.com ~all").unwrap();
        assert_eq!(evaluate(&t, ip("1.2.3.4"), &MockResolver), SpfResult::Fail);
    }
}
