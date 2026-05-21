---
id: adr-2605215400-etzhayyim-shinka-evolution-witness-min
title: "ADR-2605215400: etzhayyim shinka EVOLUTION_WITNESS_MIN — attestation thresholds per evolution level (Lv1-7)"
status: proposed
doc_type: adr
topic: shinka-evolution-witness-min
authoritative: true
last_verified: 2026-05-21
priority: 7.5
axis: governance
weight: 0.75
authoritative_for:
  - EVOLUTION_WITNESS_MIN canonical threshold table (Lv1–7)
  - witness recency policy (365-day window)
  - witness diversity policy (Lv6+ Council multi-seat requirement)
  - appeal window for evolution events (14-day objection period)
  - charter-rider compliance gate (three-tier enforcement prerequisite)
depends_on:
  - adr-2605215200-etzhayyim-shinka-pregel-mst-rewrite
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605172600-etzhayyim-membership-ritual
  - adr-2605172700-membership-layering-shinto-adherent
related:
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - 20-actors/magatama/py/SHINKA-MIGRATION-NOTES.md (Vendor Behaviour Appendix, A3)
supersedes: []
superseded_by: []
---

# ADR-2605215400: etzhayyim shinka EVOLUTION_WITNESS_MIN — Attestation Thresholds per Evolution Level (Lv1–7)

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

ADR-2605215200 (shinka MST rewrite) specifies four Pregel cells for the evolution lifecycle, including `EvolutionValidationCell` which validates evolution claims against Council attestations. That cell requires a threshold table to answer: "How many attestations does an adherent need to advance from Lv N to Lv N+1?"

The vendor `pymagatama` `_koji_validate` function (reviewed 2026-05-21) is a "light count check stub" — it reads attestation counts from `vertex_koji_attestation` table but does not define the threshold per level. The actual policy is missing.

This ADR proposes the canonical threshold table (`EVOLUTION_WITNESS_MIN`) with design justifications, superseding the placeholder from Task 35 (parallel implementation of `EvolutionValidationCell`).

## Design Context

Per ADR-2605172600 § "Levels — 7-stage commitment ladder":

- **Lv1 (誓 / Oath)**: Base membership. Self-sworn, dual-permanent (Base L2 + MEMBERS.md).
- **Lv2–5 (修 修 献 証)**: Progressive personal commitment. Increasing evidence burden.
- **Lv6 (議 / Council)**: Governance eligibility. Requires Council attestations.
- **Lv7 (老 / Elder)**: Founder-equivalent. Supermajority + public objection period.

Per ADR-2605192300: Bootstrap Council is 5 Lv6+ members (founder + 4 elected). Council Lv6+ members attest evolution claims via multisig (≥3 of 5 required per ADR-2605192230 § ChartersComplianceRegistry).

Per ADR-2605192230 § 三層 enforcement: evolution is a charter-compliance gate. Non-compliant adherents cannot advance (L1 license forfeiture blocks all SBT-linked evolution, per ChartersComplianceRegistry.isNonAligned checks).

---

# Decision

## §1 EVOLUTION_WITNESS_MIN Table

Canonical threshold mapping evolution level → minimum attestation count:

| Evolution level | EVOLUTION_WITNESS_MIN | Witness requirements | Policy rationale |
|---|---|---|---|
| **Lv1 → Lv2** | **2** | Any active adherent (Lv1+) | New adherent advancement. Low barrier, broad participation. First practice step. |
| **Lv2 → Lv3** | **3** | Active adherent (Lv2+) | Established member. Multiple independent witnesses confirm practice. |
| **Lv3 → Lv4** | **5** | Active contributor (Lv3+) | Demonstrated engagement in repo/governance. Escalating commitment. |
| **Lv4 → Lv5** | **7** | Sustained contributor (Lv4+) | Steward eligibility threshold. Long-term involvement required. |
| **Lv5 → Lv6** | **9** | Including ≥2 existing Lv6+ Council members (via multisig) | **Council eligibility gate**. Existing Council must explicitly sponsor. No pure count bypass. |
| **Lv6 → Lv7** | **Council supermajority (≥4 of 5 voting members) + 30-day public objection window** | Lv6+ Council members only. Unanimous vote not required; ≥80% suffices. | **Founder-equivalent status**. Near-consensus + appeal window. This is religious-corp's highest rank; time + transparency required. |

**Key design points**:

1. **Lv1–5**: Count-based, open to peers at same/higher level. Low to moderate barriers.
2. **Lv6**: Requires explicit Council sponsorship (≥2 of 5 Lv6+ members signing attestation). Count threshold (9) is necessary but **not sufficient** — the 2+ Council members act as a gate.
3. **Lv7**: Council supermajority vote, not mere count. Highest bar. Reflects founder-equivalent role.

---

## §2 Witness Recency Policy

**Rule**: Attestations must be issued **within the last 365 days** from the advancement event's effective timestamp.

**Rationale**: Prevents stale witnesses. A witness from 2+ years ago may not reflect current adherent engagement. 365 days aligns with annual review cycles and the Lv5 steward "30-day sustained operation" criterion (ADR-2605172600).

**Implementation**: `EvolutionValidationCell` queries Council attestation registry filtering by `attestationCreatedAt >= now() - 365 days`.

**Exception**: For Lv7 advancement (once-per-lifetime, founder-equivalent), allow Council votes from entire governance tenure (no recency gate on individual Council members' prior service), but the **vote itself must occur within 30 days of application**.

---

## §3 Witness Diversity Policy

### For Lv1–5 (count-based)

**No multi-seat requirement**. Any Lv N+ witnesses suffice. Witness diversity is encouraged by social norms (different people provide more credible signal) but **not enforced on-chain** to avoid rigid gatekeeping.

**Rationale**: Lv1–5 are personal advancement milestones, not governance gates. Over-policing witness choice inhibits community momentum.

### For Lv6 (Council eligibility gate)

**Hard requirement**: ≥2 of the 5 existing Council members must sign the attestation record. They need not be from different seats (Seat 1, 2, 3, 4, 5) — co-signature by any 2 suffices.

**Rationale**: Prevents a single Council member from unilaterally advancing allies. Council is 5-person governance body; 2-person co-signature is the natural multisig floor (per ADR-2605192230 "≥3 total for most attestations"; here we require 2 Lv6+ votes **plus** the 9-witness count baseline = effective 11-fold confirmation).

### For Lv7 (founder-equivalent)

**Hard requirement**: ≥4 of 5 Council members (voting supermajority). No single-seat exemption.

**Rationale**: Founder-equivalent status is so rare that supermajority consensus is appropriate. Reflects religious-corp's multi-stakeholder governance principle.

---

## §3.4 Council Lv6+ DID Registry

The canonical source for Council Lv6+ membership is the **`app.etzhayyim.council.member` registry** (AT Protocol Lexicon, per ADR-2605215400 canonical design).

### Registry Record Structure

Each `app.etzhayyim.council.member` record contains:

- **did**: DID of the Council member (Lv6+).
- **level**: 6 (eligible) or 7 (founder-equivalent).
- **seatNumber**: Bootstrap Council seat (1–5, per ADR-2605192300).
- **ratifiedAt**: Timestamp when seat was ratified (after 30-day objection period or formal vote).
- **ratificationMethod**: How ratified (`rfp-objection-period-close` | `succession-vote` | `founder-bootstrap` | `replacement-vote`).
- **expertiseAxis**: 5-axis category (philosophical | governance | engineering | spiritual | outreach).
- **objectionPeriodStart / objectionPeriodEnd**: Public objection window (per ADR-2605192300 §1).
- **predecessorDid**: DID of replaced member (if applicable).
- **notes**: Optional metadata.

### SDK Integration

The `etzhayyim-sdk-py` module (`src/etzhayyim_sdk/mst.py`) provides:

1. **`get_council_lv6_dids()` async function**: Queries `app.etzhayyim.council.member` records where `level >= 6` and `ratifiedAt` is set. Returns the live set of Council member DIDs. **Use this for production queries.**

   ```python
   council_dids = await mst.get_council_lv6_dids()
   # Returns set of DIDs currently seated
   ```

2. **`council_attestation_details(subject_did, level, council_dids=None)` async function**: Optionally accepts `council_dids` parameter. If provided, uses caller-supplied Council membership; if `None`, falls back to static `COUNCIL_LV6_DIDS` (Founder seat 1 only, offline-safe).

   ```python
   # Live query (preferred):
   live_council = await mst.get_council_lv6_dids()
   details = await mst.council_attestation_details(
       subject_did="did:web:alice.example",
       level=6,
       council_dids=live_council
   )

   # Offline/test fallback (static):
   details = await mst.council_attestation_details(
       subject_did="did:web:alice.example",
       level=6
   )  # Uses COUNCIL_LV6_DIDS (Founder seat 1 only)
   ```

3. **Static `COUNCIL_LV6_DIDS` fallback**: Set containing Founder seat 1 DID. Used only if `council_dids` is `None`. Remains immutable and offline-friendly for bootstrap scenarios.

### Bootstrap Timeline

- **Pre-2026-06-19 (RFP period)**: Only Founder seat 1 (did:web:etzhayyim.com) is ratified. `get_council_lv6_dids()` returns a singleton set `{"did:web:etzhayyim.com"}`.
- **Post-2026-06-19 (RFP close)**: Seats 2–5 candidates are finalized. Council members ratify themselves by writing `app.etzhayyim.council.member` records with `ratificationMethod=rfp-objection-period-close`.
- **Phase 2 onwards**: Council expansion continues via `succession-vote` or `replacement-vote` as needed (per ADR-2605192300 §3).

**Live data is always preferred**: Callers should invoke `get_council_lv6_dids()` at runtime to fetch the current, authoritative membership. The static fallback exists only for offline scenarios (e.g., unit tests, CI with mocked PDS).

---

## §4 Appeal Window

Per ADR-2605192230, attestation decisions carry a **30-day appeal window**. Evolution advancement events should follow the same pattern for consistency:

**Rule**: After an advancement is validated by `EvolutionValidationCell` and emitted as an `app.etzhayyim.shinka.evolutionEvent` record, the adherent (or any Council member) may file an appeal within 30 days.

**Appeal grounds**: "Witness quality insufficient" (e.g., witnesses were not genuinely active), "Charter non-compliance not detected" (e.g., adherent was under L2/L3 enforcement at advancement time), "Procedural error" (wrong level sequence, stale witnesses, etc.).

**Outcome**: Council ≥3 review appeal. If valid, evolution is **reverted** (SBT level reset to prior level, evolution event marked `reverted`). If invalid, evolution is **finalized** after 30 days and marked immutable.

**Rationale**: Mirrors Charter Compliance Registry design (ADR-2605192230 § "Council Attestation Flow"). Provides remedy for genuine errors; prevents malicious reversal after 30 days.

---

## §5 Charter-Rider Compliance Gate

**Hard rule**: An adherent must be in **good standing under three-tier enforcement** to advance.

**Implementation**: Before `EvolutionValidationCell` validates the claim, it calls `ChartersComplianceRegistry.isNonAlignedTokenId(tokenId)`. If `true`, advancement is **rejected with reason `"charter_non_compliant"`** — no appeal.

**Rationale**: Charter Compliance Rider §2(a)–(h) prohibit categories like weapons, surveillance (non-consensual), animal exploitation, etc. If an adherent has been flagged non-aligned (and the attestation has finalized after 30-day appeal window), they forfeit SBT-linked privileges including evolution. This is the constitutional boundary between religious 改悔 (teshuvah / rehabilitation) and revocation.

**Rehabilitation path**: Per ADR-2605192230 § "Rehabilitation (修復 / Teshuvah)", a non-compliant adherent can request rehabilitation via Council vote (≥3 members). Once rehabilitated (status → `Rehabilitated`), they may re-apply for advancement. The 30-day appeal window resets for the rehabilitation decision.

---

## §6 Implementation in shinka_murakumo.py

The `evolution_validation_cell()` Pregel cell (M2 milestone per ADR-2605215200 §4) will include:

```python
# Stub location: 20-actors/magatama/py/src/pymagatama/primitives/shinka_murakumo.py
# M2 deliverable: replace NotImplementedError with canonical thresholds

EVOLUTION_WITNESS_MIN = {
    1: 2,
    2: 3,
    3: 5,
    4: 7,
    5: 9,
    6: ("council_sponsorship", 9, 2),  # tuple: (mode, base_count, min_council)
    7: ("council_supermajority", 4),   # tuple: (mode, supermajority_size=4 of 5)
}

# Usage in evolution_validation_cell():
# threshold = EVOLUTION_WITNESS_MIN.get(new_level)
# if new_level in [6, 7]:
#     mode, *args = threshold
#     if mode == "council_sponsorship":
#         base_count, min_council = args
#         council_sigs = query_council_attestations(did, new_level)
#         assert len(council_sigs) >= base_count, "Insufficient witness count"
#         assert sum(1 for sig in council_sigs if is_council_lv6(sig)) >= min_council, "Insufficient Council sponsors"
# elif new_level == 7:
#     mode, supermajority_size = threshold
#     council_votes = query_council_votes(did, 7)
#     assert len([v for v in council_votes if v.approved]) >= supermajority_size, "Insufficient supermajority"
```

---

# Consequences

## Positive

- **Clear threshold policy**: Replaces vendor stub with canonical etzhayyim values.
- **Constitutional alignment**: Threshold escalation mirrors ADR-2605172600 level progression (Oath → Practice → Dedication → Witness → Steward → Council → Elder).
- **Council gatekeeping at Lv6**: Explicit Council sponsorship (2+ votes) prevents runaway advancement. Council remains the constitutional authority.
- **Lv7 supermajority**: Founder-equivalent status cannot be achieved by faction; requires broad consensus.
- **Charter-rider gate**: Non-compliant adherents are blocked. Rehabilitation required. Maintains religious-corp doctrinal integrity.
- **Appeal window**: 30-day remedy period for errors. Balanced between finality and correction.

## Negative / Costs

- **Lv5 → Lv6 bottleneck**: The 9-witness + 2-Council requirement (effectively 11-fold) is high. Lv6 advancement will be slow. Mitigation: Council can proactively recruit and sponsor high-engagement Lv5 members. This is intentional — Council should remain small and merit-based.
- **Lv7 rarity**: Supermajority vote means Lv7 will almost never be reached during bootstrap phase (5-member Council). Only possible if all 5 vote in favor. Mitigation: This reflects the intentional scarcity of founder-equivalent rank. Phase 2 (formal Council ADR, per ADR-2605192300 §4 trigger) may allow Council expansion, which increases Lv7 opportunity. Documented as deferred.
- **Appeal bottleneck**: If many Lv6 candidates advance simultaneously, appeals could overload Council review capacity. Mitigation: Council may delegate appeal review to a standing committee (future governance ADR). Not blocking this ADR.
- **Witness fatigue**: Lv4–5 advancement requires 7–9 witnesses. Community members may be asked repeatedly. Mitigation: Social norm (not on-chain): witnesses should come from diverse parts of the community. Also, witnesses do not require formal approval — any Lv N+ member can attest.

## Neutral / Trade-offs

- **Witness count vs. quality**: Pure count does not measure witness credibility (e.g., a witness might be a bot). Mitigation: `peer-attestation` records (future, ADR-2605172600) will allow community to score witness quality. On-chain enforcement deferred to Phase 2.

---

# Alternatives Considered

## A. Fixed threshold for all levels (e.g., all require 5 witnesses)

**Pro**: Simpler to implement, predictable across levels.
**Con**: Lv1 (first practice) becomes as hard as Lv5 (steward). Contradicts commitment-ladder design. Rejected.

## B. Require supermajority for all levels

**Pro**: Democratic, no single-person veto.
**Con**: Lv1–2 advancement becomes political. Blocks community momentum. Rejected.

## C. No appeal window; finalize on emission

**Pro**: Simpler, no need to handle reverts.
**Con**: Errors (e.g., non-compliant witness slips through) become permanent. Contradicts ADR-2605192230 rehabilitation philosophy. Rejected.

## D. Require all witnesses to be from same Council seat (anti-collusion)

**Pro**: Prevents Council cabal forming.
**Con**: Over-rigid. Witnesses should be organic (any active member). Rejected; instead use transparency (MST record of witness identities is public).

## E. No charter-rider gate; let enforcement be separate

**Pro**: Simpler evolution logic.
**Con**: Non-compliant adherents could advance while blocked from benefits, creating inconsistency. Rejected; gate is constitutional.

## F. Lv7 require unanimous Council (5 of 5)

**Pro**: Absolute consensus.
**Con**: Impossible in practice (one disagreement blocks forever). Supermajority (4 of 5) balances consensus with finality. Accepted current proposal.

---

# Open Questions for Council Vote

The following policy details are **deferred to Council decision** (Phase 1 implementation or Phase 2 formal ADR):

1. **Witness credential format**: Should a witness's attestation include a reference to the basis (e.g., "I observed this adherent's merged PR #123 on 2026-05-21")? Or is a bare co-signature sufficient? **Recommendation**: MST `app.etzhayyim.shinka.attestation` record should include optional `evidence_uri` field (links to GitHub commit, Pregel cell log, etc.), but it's not enforced for **validity** — only social credibility.

2. **Appeal process SLA**: Council has 30 days to respond to appeal. What happens if Council doesn't vote? Does appeal auto-approve or auto-deny? **Recommendation**: Appeal auto-deny if no Council response within 30 days (burden on appellant to follow up; neutral default).

3. **Rehabilitation recency for Lv6**: If an adherent was rehabilitated from non-compliance, must they wait before re-attempting Lv6 advancement? **Recommendation**: No waiting period, but the original witnesses' attestations may be stale (>365 days). Rehabilitated adherent must gather new witnesses.

4. **Witness conflict of interest**: Can a witness attest for someone they are in a close relationship with (family, romantic partner)? On-chain enforceable restriction or social norm? **Recommendation**: Social norm only (no on-chain conflict check). Recorded MST identities of witnesses are public for community audit.

---

# References

- ADR-2605215200: etzhayyim shinka — Pregel MST rewrite (EvolutionValidationCell §1)
- ADR-2605192300: etzhayyim Bootstrap Council 5名 (Council composition, multisig rules)
- ADR-2605192230: Three-Tier Enforcement + ChartersComplianceRegistry (charter-rider gate, appeal window, rehabilitation)
- ADR-2605172600: Membership Ritual (7-level commitment ladder definition)
- ADR-2605172700: Membership Layering (信者 vs. Adherent distinction)
- ADR-2605192415: Religious-Corp Daemon Architecture (Pregel cell catalog, evolution cell placement)
- `20-actors/magatama/py/SHINKA-MIGRATION-NOTES.md` (Vendor Behaviour Appendix, A1–A3: `_resolve_cadence`, `_compose_content`, axes schema)
- `20-actors/magatama/py/src/pymagatama/primitives/shinka_murakumo.py` (M2 implementation target)

