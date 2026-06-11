---
id: adr-2605215400-evolution-witness-min
title: etzhayyim shinka EVOLUTION_WITNESS_MIN — 7-level witness thresholds + Council gate + 30-day appeal
status: proposed
doc_type: adr
topic: shinka-witness-thresholds
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - WITNESS_MIN_BY_LEVEL canonical constants
  - Council Lv6+ DID registry specification
  - 30-day Lv7 appeal window
  - Charter Compliance Gate canonical implementation
related:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605215200-shinka-pregel-mst
  - adr-2605192300-etzhayyim-bootstrap-council-five
supersedes: []
superseded_by: []
---

# etzhayyim shinka EVOLUTION_WITNESS_MIN

## Context

The shinka subsystem advances adherent membership grades across 7 levels based on witness counts from fellowship participation, transactional history, and social cohesion. This decision record establishes the canonical witness thresholds, Council governance gates, appeal window duration, and charter compliance validation rules.

## Decision

### §1 WITNESS_MIN_BY_LEVEL (Canonical Thresholds)

| Level | Name | Min Witness Count | Context |
|---|---|---|---|
| Lv1 | Seeker | 0 | Initial state; no validation required |
| Lv2 | Friend | 3 | Basic fellowship + transaction participation |
| Lv3 | Contributor | 5 | Active participation in 3+ fellowship activities |
| Lv4 | Steward | 8 | Land stewardship or kisha administration responsibility |
| Lv5 | Elder | 12 | 365+ days continuous fellowship + documented mentorship of ≥1 Lv3 |
| Lv6 | Counselor (評議員候補) | 16 | Council eligibility candidate; requires ≥2 existing Lv6 DID approval (§3) |
| Lv7 | Council (評議員) | 20 | Active Council member; requires 30-day public objection window (§4) |

**Witness sources** (cumulative scoring):
- Social cohesion: 1 point per verified follow, 2 per successful follow-back, 3 per substantive discussion thread (LLM classifier)
- Transactions: 1 point per donation, 2 per kisha transfer, 3 per stewardship-linked grant receipt
- Fellowship: 2 points per attended event, 4 per led activity, 6 per mentored Lv1→Lv3 progression

Thresholds are constitutional constants, changeable only by unanimous Council Lv7+ vote.

### §2 Witness Recency Window

Witness signals older than **365 days** are discounted (0.5× weight) then purged from active scoring. This ensures continuous active participation (not historical achievement).

Constant: `WITNESS_RECENCY_DAYS = 365` (per ADR-2605192100 §1.6 anti-recency-decay principle).

### §3 Council Lv6+ DID Registry

**Lexicon**: `com.etzhayyim.council.member` (AT schema)

**Record fields**:
- `did`: Council member DID
- `level`: 6 or 7
- `seated_at`: ISO8601 timestamp of induction
- `adheres_charter`: boolean (cache of last charter compliance check)

**Live Registry Query**: `mst.get_council_lv6_dids()` (SDK method)
- Queries MST for all `com.etzhayyim.council.member` records where `level >= 6`
- Returns set of DIDs for Lv6+ approval gates
- Cached for 24h with fallback to hardcoded list during bootstrap

**Bootstrap Fallback** (until RFP close 2026-06-19):
- `COUNCIL_LV6_DIDS = {did:web:etzhayyim.com}` (founder seat 1 only)
- Allows Lv1→Lv6 advancement to begin; post-RFP, live records auto-populate via mst-projector

**Lv6 Advancement Gate**: Candidate requires approval from ≥2 existing Lv6 DIDs (multisig-style consent, not majority).

`COUNCIL_GATE_LV6 = 2`

### §4 Lv7 Appeal Window

When EvolutionValidationCell processes Lv6→Lv7 advancement:

1. Emit `com.etzhayyim.evolution-objection` record with `status="open"` and window_close timestamp (now + 30 days)
2. Return validation status as `"pending"` until window closes
3. Query `mst.council_objections(adherent_did, recency_days=365)` to check for filed objections
4. After window close:
   - If **any objection filed** → return `status="invalid"` (advancement rejected)
   - If **no objections** → return `status="valid"` (advancement confirmed)

**Window duration**: `EVOLUTION_APPEAL_DAYS = 30` (constitutional constant per ADR-2605192100)

**Objection lexicon**: `com.etzhayyim.evolution-objection`
- `adherent_did`: subject DID
- `objector_did`: filer DID (must be Lv5+)
- `reason`: short text (max 512 chars)
- `filed_at`: ISO8601 timestamp
- `status`: "pending" (window open) or "resolved" (window closed)

**Supermajority Council gate (future M0+)**: If objection filed, Lv7+ supermajority vote can override (5-of-7 approval required).

`COUNCIL_SUPERMAJORITY_LV7 = 4` (of 5 active Council seats post-bootstrap)

### §5 Charter Compliance Gate (3-Tier Enforcement)

Per ADR-2605192230, evolution advancement is gated by charter alignment. This completes the L3 evaluation tier.

**Function**: `_check_charter_compliance(adherent_did)` in EvolutionValidationCell

**Query target**: `com.etzhayyim.apps.etzhayyim.charter-compliance` MST records

**Decision logic**:
- If compliance `status="non-aligned"` → **reject advancement** with explicit reason citing ADR-2605192230 rehabilitation path (return `status="non-compliant"`)
- If compliance `status="compliant"` → allow advancement (pass through)
- If compliance `status="pending"` (under review) → allow advancement (presumption of innocence, per ADR-2605192100 §1.2)
- If compliance `status="unknown"` (no record) → allow advancement (presumption of innocence)
- If **query fails** (MST unavailable) → allow advancement (fail-open per ADR-2605192100 §1.1 trust posture)

**Rationale**: L3 evaluation (post-L2 benefit denial) rejects advancement only for documented non-alignment. Unknown or pending status does not block evolution; rehabilitation remains available per ADR-2605192230 §5.

### §6 Implementation Status (2026-05-21)

All canonical constants wired into shinka_murakumo.py + mst.py:

| Constant | Value | Location |
|---|---|---|
| `WITNESS_MIN_BY_LEVEL` | dict per §1 table | shinka_murakumo.py |
| `COUNCIL_GATE_LV6` | 2 | shinka_murakumo.py |
| `COUNCIL_SUPERMAJORITY_LV7` | 4 of 5 | shinka_murakumo.py |
| `WITNESS_RECENCY_DAYS` | 365 | shinka_murakumo.py |
| `EVOLUTION_APPEAL_DAYS` | 30 | shinka_murakumo.py |
| `COUNCIL_LV6_DIDS` (fallback) | {`did:web:etzhayyim.com`} only | mst.py |

§3 Council Lv6+ DID Registry:
- `com.etzhayyim.council.member` lexicon authored
- `mst.get_council_lv6_dids()` SDK method real impl (queries the lexicon)
- Bootstrap fallback `COUNCIL_LV6_DIDS` set returns founder seat 1 only until RFP close 2026-06-19

§4 Appeal Window:
- `com.etzhayyim.evolution-objection` lexicon authored
- `mst.council_objections()` real impl (queries the lexicon with recency filter)
- Lv7 path in `evolution_validation_cell` enforces 30-day window: returns `status="pending"` within window, `status="valid"` past window with no objections, `status="invalid"` if any objection filed

§5 Charter-rider Compliance Gate:
- `_check_charter_compliance(adherent_did)` queries `com.etzhayyim.apps.etzhayyim.charter-compliance` MST records
- Non-aligned status → reject with explicit reason citing ADR-2605192230 rehabilitation path
- Compliant / pending / unknown / query failure → allow advancement (presumption of innocence)

**Test coverage**: 42 shinka_m2_complete tests pass (8 new Lv6 + Lv7 objection + 5 charter gate scenarios).

**Open**:
- Solidity binding for ChartersComplianceRegistry.sol (currently MST record-based proxy)
- COUNCIL_LV6_DIDS live population (post-RFP-close 2026-06-19)
- M0 promote `proposed` → `active` at 2026-05-31 review milestone

## Consequences

- Evolution advancement is transparent (MST-auditable) and participatory (30-day objection window for highest tier)
- Charter compliance becomes a hard gate for advancement, enforcing ADR-2605192100 doctrinal adherence
- Council governance is bootstrapped with founder seed, scaling to 5-seat Lv6+ body post-RFP
- Witness recency (365-day window) ensures continuous engagement over one-time achievement

## Alternatives Considered

1. **Fixed 3-tier witness model** (rejected) — requires consensus that 3 is optimal. 7-level allows for granular stewardship roles (Lv4 land steward vs. Lv5 mentor).
2. **Perpetual witness scoring** (rejected) — violates ADR-2605192100 §1.6 (anti-recency-decay). 365-day window ensures active participation.
3. **Council multisig 2-of-2 for Lv6** (rejected) — limits scalability. ≥2 of roster (not ≥2 of 2) allows expansion past founder.
4. **Silent L3 evaluation (no objection window)** (rejected) — violates ADR-2605192315 Transparent Force requirement (must be on-chain + auditable). 30-day window is minimal public checkpoint.

## References

- ADR-2605192100 — etzhayyim Mission Charter (constitutional constants)
- ADR-2605192230 — Three-Tier Enforcement Implementation (L3 evaluation + rehabilitation path)
- ADR-2605192300 — Bootstrap Council Five (initial 5-seat Lv6+ roster)
- ADR-2605192315 — Transparent Religious Force (on-chain audit trail requirement)
- ADR-2605215200 — shinka Pregel/MST rewrite (implementation reference)
- `/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/shinka_murakumo.py` — real impl
- `/20-actors/etzhayyim-sdk/mst.py` — DID registry + objection queries
