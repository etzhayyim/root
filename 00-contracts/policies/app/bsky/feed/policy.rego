package app.bsky.feed.post

# kotoba-datomic §4 L2 — policy layer for `app.bsky.feed.post`.
#
# Refs:
#   - ADR-2605192100 §1.13 Eros / Gore, §1.15 non-eschatological
#   - ADR-2605192200 Charter Compliance Rider v2.0 §2(a)..(h)
#   - ADR-2605231400 kotoba-datomic SPEC §4 — (L1, L2, L3) must all accept
#   - 40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/charter_rider.py
#
# Decision shape:
#   {"allow": bool, "reason": string,
#    "violations": [{"category", "evidence"}],
#    "obligations": [string]}

import future.keywords.if
import future.keywords.in
import future.keywords.contains

default allow := false

# ── Schema-side sanity ───────────────────────────────────────────────

missing_text if not input.record.text
missing_text if {
  input.record.text == ""
  not input.record.embed
}

missing_created_at if not input.record.createdAt

over_max_graphemes if count(input.record.text) > 3000

# ── Helpers ──────────────────────────────────────────────────────────

lower_text := lower(input.record.text) if {
  is_string(input.record.text)
}

lower_text := "" if not is_string(input.record.text)

has_allow_context(terms) if {
  some term in terms
  contains(lower_text, term)
}

self_labels contains v if {
  some s in input.record.labels.values
  v := s.val
}

# ── Charter Rider §2(a) WEAPONS ──────────────────────────────────────

violations contains {"category": "2a", "evidence": ev} if {
  some term in [
    "assault rifle", "lethal autonomous", "kinetic weapon", "kinetic strike",
    "cyber-offensive", "cyber offensive", "munition", "warhead",
    "paramilitary contractor", "kill-chain", "kill chain",
  ]
  contains(lower_text, term)
  not has_allow_context([
    "historical", "treaty", "disarm", "ban treaty", "geneva",
    "red cross", "red crescent", "antiwar", "peace research", "forensic",
  ])
  ev := sprintf("matched §2(a) term: %q", [term])
}

# ── §2(b) SPECULATIVE FINANCE ────────────────────────────────────────

violations contains {"category": "2b", "evidence": ev} if {
  some term in [
    "high frequency trading", "high-frequency trading", "hft strategy",
    "predatory loan", "predatory lending", "payday loan",
    "leverage spread", "arbitrage bot", "naked short", "pump and dump",
  ]
  contains(lower_text, term)
  not has_allow_context([
    "critique", "regulator", "prosecute", "fraud report",
    "consumer protection", "academic", "case study",
  ])
  ev := sprintf("matched §2(b) term: %q", [term])
}

# ── §2(c) SURVEILLANCE CAPITALISM ────────────────────────────────────

violations contains {"category": "2c", "evidence": ev} if {
  some term in [
    "ad-tech dsp", "ad-tech ssp", "adtech dsp", "adtech ssp",
    "data broker", "behavioral targeting", "cross-site tracking",
    "fingerprinting sdk", "fingerprinter sdk",
  ]
  contains(lower_text, term)
  not has_allow_context([
    "privacy", "countermeasure", "defense", "defence", "audit",
    "eprivacy", "gdpr", "critique", "investigation",
  ])
  ev := sprintf("matched §2(c) term: %q", [term])
}

# ── §2(d) FOSSIL FUEL EXTRACTION (obvious-only) ──────────────────────

violations contains {"category": "2d", "evidence": ev} if {
  some term in ["new coal field", "new oil field", "greenfield coal", "greenfield oil"]
  contains(lower_text, term)
  ev := sprintf("matched §2(d) term: %q", [term])
}

# ── §2(f) MULTI-GENERATIONAL HARM (obvious-only) ─────────────────────

violations contains {"category": "2f", "evidence": ev} if {
  some term in [
    "germline edit without safety", "biosphere collapse profit",
    "attention monopoly child", "addictive design child",
    "addictive design teen", "addictive design adolescent",
  ]
  contains(lower_text, term)
  ev := sprintf("matched §2(f) term: %q", [term])
}

# ── §2(h) WELLBECOMING SUBORDINATION (obvious-only) ──────────────────

violations contains {"category": "2h", "evidence": ev} if {
  some term in [
    "engagement optimization at any cost",
    "engagement optimisation at any cost",
    "maximize dwell time", "maximise dwell time",
    "dark pattern conversion",
  ]
  contains(lower_text, term)
  ev := sprintf("matched §2(h) term: %q", [term])
}

# ── Advertising ─────────────────────────────────────────────────────

violations contains {"category": "advertising", "evidence": ev} if {
  some term in [
    "sponsored content", "promo code", "use my affiliate",
    "affiliate link", "discount code", "buy now",
    "limited time offer", "click my referral",
  ]
  contains(lower_text, term)
  ev := sprintf("matched advertising term: %q", [term])
}

# ── Eschatology assertion ────────────────────────────────────────────

violations contains {"category": "eschatology", "evidence": ev} if {
  some term in [
    "rapture is coming", "millennial kingdom is at hand",
    "end times prophecy fulfilled",
  ]
  contains(lower_text, term)
  ev := sprintf("matched eschatology assertion: %q", [term])
}

# ── Gore self-label ──────────────────────────────────────────────────

violations contains {"category": "gore", "evidence": "self-label gore (ADR-2605192400)"} if {
  "gore" in self_labels
}

# ── Schema violations (separate so the L3 cell can tell them apart) ─

violations contains {"category": "missing-required", "evidence": "text or createdAt missing"} if missing_text
violations contains {"category": "missing-required", "evidence": "text or createdAt missing"} if missing_created_at
violations contains {"category": "length", "evidence": "text exceeds 3000 chars"} if over_max_graphemes

# ── Aggregation ──────────────────────────────────────────────────────

allow if count(violations) == 0

reason := "ok" if allow
reason := "charter-violation" if not allow

obligations contains "audit_charter_block" if {
  some v in violations
  v.category in {"2a", "2b", "2c", "2d", "2f", "2h", "advertising", "eschatology"}
}
obligations contains "council_review" if {
  some v in violations
  v.category == "gore"
}
obligations contains "client_truncate_or_split" if {
  some v in violations
  v.category == "length"
}
obligations contains "client_fix_required_fields" if {
  some v in violations
  v.category == "missing-required"
}

decision := {
  "allow": allow,
  "reason": reason,
  "violations": [v | some v in violations],
  "obligations": [o | some o in obligations],
}
