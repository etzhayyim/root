---
id: adr-2605261030
title: hagukumi (育み) — Care (childcare + eldercare + daily-living) Tier-B Actor R0 Scaffold
status: proposed
doc_type: adr
topic: hagukumi-care
authoritative: true
last_verified: 2026-05-26
authoritative_for:
  - hagukumi actor charter (R0)
  - care domain constitutional gates G1..G14
  - L4 Care Tier care-delivery substrate
related:
  - adr-2605261000
  - adr-2605260100-mitate-diagnostic-routing-charter
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605181100-mst-encrypted-records-signal-keywrap
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605261000 (Liberation Ladder — defines hagukumi as L4 gate)
  - ADR-2605260100 (mitate — diagnostics complement)
  - ADR-2605181100 (encrypted records — privacy invariant)
---

# ADR-2605261030: hagukumi (育み) — Care Tier-B Actor R0 Scaffold

**Date**: 2026-05-26
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify), Council medical advisory ≥1 licensed pediatrician + ≥1 licensed geriatrician for R1+
**ADR Hierarchy**: Parent = ADR-2605261000 (Liberation Ladder — L4 gate). Sibling to mitate (diagnostic-side; ADR-2605260100) and yakushi (drug-side; ADR-2605250500).

## Context

ADR-2605261000 (Liberation Ladder) gates Stage L4 (Care Tier) on hagukumi R2 maturity for childcare ≥40 hr/wk/child + elder care + chronic-care continuity. mitate routes diagnoses, yakushi manufactures drugs — but neither delivers the *daily care labor* that consumes the largest share of subsistence + family time (OECD: ~12-18 hr/wk per parent of young children; ~8-15 hr/wk for elder-caring adult).

Without hagukumi, the L4 gate cannot lift, and adherents at L3 cannot release the 10-15 hr/wk caregiving burden that the Liberation Ladder targets.

## Proposal

Launch **`hagukumi` (育み — "nurturing", continuative form of 育む "to raise/nurture"; multi-generational care echo: nurturing children + nurturing elders is the same verb in Japanese)** as a Tier-B religious-corp actor:

- **Actor DID**: `did:web:etzhayyim.com:hagukumi`
- **Namespace**: `com.etzhayyim.hagukumi.*`
- **R0 scope**: Daily-living care delivery — childcare (ages 2+; under-2 deferred to specialist actor TBD), eldercare (companionship + ADL support; non-medical), chronic-care continuity (post-mitate diagnosis adherence support; non-prescriptive), meal delivery (mitsuho-sourced), respite support. **Excludes**: medical procedures (mitate/yakushi), hospice/palliative terminal (mitate N10), behavioral psych intervention, abuse investigation (state domain), surveillance, in-home recording.
- **R0 robotics**: Hitogata humanoid (R2+ class-A gentle, R0 placeholder only), Sukoyaka (yakushi cold-chain last-mile inheritance for meal delivery), new **Yutori (ゆとり)** class for companionship telepresence (R2+, separate mech-design ADR).
- **14 gates + 10 non-goals** declared before capability lands.
- **5 Pregel cells** (child daily care, elder companionship, chronic continuity, meal delivery, respite support) — all import-time RuntimeError in R0.

## Rationale

1. **Domain separation**: Care delivery (developmental psychology for children + autonomy preservation for elders + chronic-condition adherence support + privacy invariants) is its own actor; mitate handles diagnosis, yakushi handles drugs.
2. **L4 gate dependency**: ADR-2605261000 §6 cannot advance to L4 without hagukumi R2.
3. **Privacy criticality**: Care substrates handle the most sensitive observations (child development, elder cognition, intimate ADL); the ADR-2605181100 encrypted-record envelope must be **structurally enforced**, not policy-enforced.
4. **Multi-generational priority**: ADR-2605192100 §1.3 explicitly prioritizes children + elders. hagukumi is the constitutional delivery vehicle.
5. **Witness quorum**: ADR-2605191524 modified for care context — per-visit attestation by caregiver DID + (consent-bound) care-recipient or family-guardian DID, with **no third-party robot witness** (privacy invariant); Council audit sampling 1-in-100 with care-recipient pre-consent.

## Design

### Actor Manifest

```
20-actors/hagukumi/
├── README.md                     # Overview + R0 scope boundary + privacy invariants
├── CLAUDE.md                     # Actor-local instructions
├── manifest.jsonld               # DID + cell catalog
└── cells/                        # 5 cell scaffolds (import-time RuntimeError)
    ├── child_daily_care/
    ├── elder_companionship/
    ├── chronic_continuity/
    ├── meal_delivery/
    └── respite_support/
```

### Pregel Cells (5, all import-time RuntimeError R0)

| Cell | Purpose | Murakumo node | Input | Output |
|---|---|---|---|---|
| `child_daily_care` | Caregiver-mediated child daily activities (play, learning prep, hygiene, meals) | levi (caregiver verification) | careRecipientDid, careSchedule | careSessionAttestation (encrypted) |
| `elder_companionship` | Daily companion presence (conversation, ADL gentle assist, mitate symptom screening) | levi | careRecipientDid, careSchedule | careSessionAttestation (encrypted) |
| `chronic_continuity` | Post-mitate diagnosis support (medication-reminder adherence, lifestyle adjustment, mitate re-check scheduling) | levi (mitate-paired) | mitateReferralCid | continuitySessionAttestation (encrypted) |
| `meal_delivery` | mitsuho-sourced meal delivery to adherents (cold-chain L4 transport) | simeon + dan (logistics) | mealManifest, deliveryRoute | deliveryAttestation (no recipient PII; aggregate only) |
| `respite_support` | Time-limited caregiver-substitute for primary family caregiver (8-24 hr respite blocks) | levi | primaryCaregiverDid, respiteWindow | respiteSessionAttestation (encrypted) |

### Lexicons (4, deferred to R1+)

```
com.etzhayyim.hagukumi.{
  caregiverAttestation,       # Caregiver onboarding: training + background + Council vetting
  careSessionAttestation,     # Per-session record (encrypted XChaCha20 envelope per ADR-2605181100)
  consentRecord,              # Care-recipient + family-guardian consent (revocable, on-chain)
  silenCareReview             # Council attestation scope (multi-axis: privacy / Wellbecoming / multi-gen)
}
```

**Structural privacy enforcement**: `careSessionAttestation` schema requires `encryptedPayloadCid` field and forbids any plaintext care-session content fields. Aggregate metrics (session-count, duration-median, no PII) publish to liberation Metric Report (ADR-2605261000 §4) only.

### Constitutional Gates (G1–G14, IMMUTABLE per R0)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | All caregiver-assistive firmware (Hitogata, Yutori, Sukoyaka) open-source WASM/Rust Apache 2.0 | §1.12 Transparent Force / open robotics |
| **G2** | **No video stream recording anywhere.** Live video for telepresence permitted; recording prohibited (firmware-level enforcement, ADR-2605181100 §3 invariant) | Privacy invariant constitutional |
| **G3** | 1:1 consent — every care interaction requires care-recipient (≥age 14) or family-guardian (<14) signed XRPC consent **per session**; default-deny | §2(d) Wellbecoming + parental authority |
| **G4** | Caregiver Council vetting: background check + child-protection / elder-protection training certification + ≥3 Council Lv6+ attestations before first session | Adherent safety baseline |
| **G5** | Child cognitive load cap (≤2 hr structured activity per session for under-6; ≤3 hr for 6-12) — Wellbecoming developmental gate | §2(d) Wellbecoming + Konrad Lorenz-aligned developmental science |
| **G6** | Elder autonomy invariant — caregiver may **never** override care-recipient stated preference except in immediate safety threat (mitate emergency keyword fail-safe shared) | §1.3 multi-gen autonomy |
| **G7** | No behavioral modification protocols (no operant conditioning, no token economies, no behavioral-incentive structures for children or adults) | §2(d) Wellbecoming + anti-coercion |
| **G8** | No advertising / no commercial-product promotion in any care setting; mitsuho meals are not "branded", silicon devices are not "marketed" | §2(b) no-ads constitutional invariant |
| **G9** | Human-in-loop required: AI/robot caregivers (Yutori telepresence, Hitogata humanoid) operate only with synchronous human caregiver oversight; **no AI-only care delivery** | §2(d) Wellbecoming + dignity |
| **G10** | 24-hour break invariant — caregivers may not work >12 consecutive hours; ≥12 hr recovery between shifts (mirrors EU Working Time Directive + Charter Rider §2(h) wellbecoming on caregiver side) | Caregiver Wellbecoming |
| **G11** | Emergency escalation to mitate — any care-recipient symptom matching mitate G5 emergency-keyword set triggers immediate mitate-side routing (cross-actor pathway via XRPC) | Safety baseline |
| **G12** | Charter Rider §2(d) Wellbecoming attestation per quarter per caregiver — peer + supervisor + Council sampled | §2(d) Wellbecoming |
| **G13** | No addictive dependency design (gamification / streak / variable reward / FOMO) in any adherent-facing care app; child + elder UI is calm-state-default | §2(d) Wellbecoming + anti-attention-economy |
| **G14** | Multi-generational priority — hagukumi capacity allocates ≥40% to under-18 + ≥30% to over-65 + ≤30% to middle adults; ratio Council-audited quarterly | §1.3 multi-gen invariant |

### Non-Goals (N1–N10, EXCLUDE from R0–R3)

| # | Non-Goal | Deferral |
|---|---|---|
| **N1** | Medical procedures — diagnosis, prescription, injection, dressing change beyond simple ADL | mitate / yakushi domain |
| **N2** | Childcare for under-2 — specialist developmental + safety requirements warrant separate actor | ADR-separate (specialist) |
| **N3** | Hospice / palliative terminal care — mitate N10 + specialist counselor required | ADR-separate (specialist) |
| **N4** | Behavioral psych intervention — requires licensed psychologist; not in hagukumi caregiver scope | Out-of-scope (cross-domain mitate referral) |
| **N5** | Telemedicine consultation — mitate domain | Never |
| **N6** | Pharmaceutical dispensing — yakushi domain | Never |
| **N7** | In-home surveillance (cameras, audio recording, activity tracking) — privacy violation | Never (constitutional carve-out) |
| **N8** | Replacement of legal guardian / parental authority — hagukumi caregiver is **supplement**, never **substitute** | Never |
| **N9** | Genetic counseling — specialist; mitate referral domain | Never |
| **N10** | Abuse investigation — state domain (CPS, APS, police); hagukumi mandatory-report to authorities but does not investigate | Never |

## Roadmap

| Phase | Date | Scope | Murakumo fleet | Gate |
|---|---|---|---|---|
| **R0** | 2026-05-26 | Scaffold only. 5 cells import-time RuntimeError. | No deployment | This ADR (PROPOSED) |
| **R1** | post-Council | Advisory-only — caregiver onboarding pipeline + consent infrastructure + mitate-paired chronic-continuity self-care prompts (no live in-home presence). Up to 50 adherent caregiver-recipient pairs registered. | levi (single node) | Future ADR + ≥1 pediatrician + ≥1 geriatrician on Council medical advisory |
| **R2** | post-R1 | Pilot live care delivery — 5 community centers + ~200 care-recipient ceiling. Hitogata + Yutori R&D parallel; humans-only delivery in R2. Meal delivery from mitsuho R2. **L4 gate eligibility.** | levi + simeon + dan (3 nodes) | Future ADR + 30-day public comment + ≥5 community-site Council attestations |
| **R3** | post-R2 | Community-scale — 50 sites + ~25,000 care-recipient capacity. Yutori telepresence + Hitogata humanoid + Sukoyaka meal delivery + full mesh. **Required for L4 → L5.** | Full 10-node fleet | Future ADR + 60-day public review + Council multi-domain vote |

## Privacy Invariant (CRITICAL — constitutional)

Care substrate handles the most sensitive observations in the entire religious-corp ecosystem. ADR-2605181100 (encrypted records + Signal key-wrap) is **mandatory** for `careSessionAttestation`. Schema-level enforcement:

```
careSessionAttestation = {
  sessionId: string,
  caregiverDid: string,
  careRecipientDidOrPseudonym: string (30-day-rotating-pseudonym per ADR-2605181200),
  encryptedPayloadCid: string,   # REQUIRED
  consentRecordCid: string,      # REQUIRED
  durationMinutes: integer,      # aggregate-only field
  emergencyEscalation: boolean,  # mitate G5 fail-safe trigger
  # NO plaintext content fields; schema validation rejects any non-listed property
}
```

The Pregel cell `child_daily_care` etc. raise `RuntimeError` at import in R0 specifically to prevent any accidental plaintext data flow before R1's encrypted-record framework is Council-attested production-ready.

## Robotics Class

R0–R1: no live robotics; human caregivers only. R2+: Yutori (ゆとり) telepresence — warrants separate mech-design ADR (parallel to hanami robot ADR-2605260230). R2+ optional Hitogata-A (Council-attested gentle-class subset; never alone with care-recipient under G9 human-in-loop).

## Murakumo Placement (R2+ design-only)

- **levi**: caregiver verification + session attestation + consent registry (privacy specialist)
- **simeon**: meal delivery routing (cold-chain inheritance)
- **dan**: meal delivery last-mile (logistics)

(Light footprint — hagukumi is privacy-first, low compute.)

## Consequences

**Positive**:
- L4 Care Tier unblocks once hagukumi R2 deploys.
- Multi-generational priority (§1.3) gains operational delivery.
- Adherent caregiver labor (10-15 hr/wk typical) released into vocational/spiritual time.
- mitate ↔ hagukumi cross-actor pathway makes the diagnostic + care substrate genuinely integrated.

**Negative / risks**:
- Privacy attack surface: care interactions are the most intimate observations; G2 (no recording) + structural lexicon schema enforcement + ADR-2605181100 envelope must hold under R2 scale stress
- Caregiver vetting (G4) is operationally expensive (background + training + Council attestation); slows R1→R2 scale
- Cross-actor coordination (mitate + hagukumi + mitsuho + yakushi) creates dependency chain; one actor's R-phase delay cascades to L4
- Yutori telepresence carries video-stream-privacy risk; G2 + Council-attested firmware critical

## Alternatives Considered

1. **Extend mitate to cover care delivery** — rejected: diagnostic ≠ ongoing care; mitate G7 (no insurance/employer/advertiser data path) doesn't generalize to in-home presence; separate actor needed for proper privacy invariants.
2. **State partnership (route to state-licensed home-care)** — rejected: §2(N4) parallel substrate + ADR-2605215000 no commercial routing; religious-corp must deliver via own actors.
3. **AI-only care delivery** — rejected: G9 + §2(d) Wellbecoming dignity invariant; human-in-loop is constitutional.
4. **Allow under-2 childcare in R0 scope** — rejected: developmental + safety requirements warrant specialist actor; deferring preserves option.

## References

- ADR-2605261000 (Liberation Ladder — L4 gate)
- ADR-2605260100 (mitate diagnostic — cross-actor pair)
- ADR-2605250500 (yakushi — drug supply for chronic continuity)
- ADR-2605181100 (encrypted records — privacy invariant)
- ADR-2605181200 (rotating pseudonym DID — care-recipient identity)
- ADR-2605192100 §1.3 (multi-generational priority — constitutional anchor)
- ADR-2605260230 (hanami robot mech-design — precedent for Yutori class ADR)
