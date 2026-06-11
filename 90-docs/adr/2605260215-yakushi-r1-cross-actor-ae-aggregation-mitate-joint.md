---
id: adr-2605260215-yakushi-r1-cross-actor-ae-aggregation-mitate-joint
title: "yakushi R1 — cross-actor AE aggregation + dedupe rule (mitate joint; closes naphazoline closed-loop other half; pre-req for mitate R2 + yakushi Wave 1 R2 pilot)"
status: proposed
doc_type: adr
topic: yakushi-mitate-cross-actor-ae
authoritative: true
last_verified: 2026-05-25
authoritative_for:
  - com.etzhayyim.pharma.adverseEventReport-aggregated payload schema (yakushi-side aggregated feed)
  - AE dedupe rule between mitate outcome_qol_followup and yakushi pharma_adverse_event
  - yakushi label-warning data-driven update mechanism (naphazoline closed-loop other half)
  - silenPharmaReview + silenMitateReview joint attestation flow for cross-actor cells
  - LotIdHashed convention (SHA-256) as the only cross-actor primary key (G7 + G10 enforcement)
  - "lot_signal" aggregation cadence (daily) + label warning re-issue cadence (quarterly minimum, on-demand maximum)
  - Cross-actor cell pair: mitate_outcome_qol_followup ↔ yakushi.pharma_post_market_surveillance + yakushi.pharma_packaging
depends_on:
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605260100-mitate-diagnostic-routing-charter
  - adr-2605260175-mitate-condition-5-rhinitis-medicamentosa
  - adr-2605260200-mitate-r1-advisory-self-care-pwa
  - adr-2605181100-mst-encrypted-records-signal-keywrap
related:
  - 20-actors/yakushi/                                         # yakushi sibling actor
  - 20-actors/mitate/                                          # mitate sibling actor
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_adverse_event/             # yakushi-side individual handoff receiver
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_post_market_surveillance/  # yakushi-side aggregated signal receiver
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_packaging/                 # yakushi-side label-warning update producer
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_outcome_qol_followup/      # mitate-side emitter
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_medication_history_audit/  # mitate-side condition 5 detection
  - 00-contracts/lexicons/com/etzhayyim/pharma/adverseEventReport.json
supersedes: []
superseded_by: []
---

# yakushi R1 — Cross-actor AE aggregation + dedupe (mitate joint)

**Date:** 2026-05-25
**Author:** Jun Kawasaki
**Status:** Proposed

## Context

Two prior ADRs left an open question:

- **ADR-2605260175** §Decision 4 (mitate condition 5 — rhinitis medicamentosa) defined mitate's emit toward yakushi: aggregated naphazoline overuse signal → `yakushi.pharma_post_market_surveillance`, individual AE handoff → `yakushi.pharma_adverse_event` (consent-gated)
- **ADR-2605260100** §Decision 8 (mitate master) named the cross-actor lexicon emit boundary but deferred the **dedupe rule** for AE double-counting

Both ADRs left this work labeled "joint mitate-yakushi R1 ADRs". This is that ADR — the **yakushi side** of the mitate↔yakushi naphazoline closed-loop. It locks:

1. Payload schema for the **aggregated** flavor of `com.etzhayyim.pharma.adverseEventReport` (today the lexicon has only the individual flavor; aggregated needs a sibling variant)
2. **AE dedupe rule** so the same patient AE doesn't get counted both in mitate's longitudinal QOL feed and yakushi's intake
3. **Label-warning data-driven update mechanism** — how the aggregated overuse signal actually moves the naphazoline label warning text on the next packaging lot
4. **Joint silen-review flow** — silenMitateReview ↔ silenPharmaReview Council Lv6+ ≥ 3 attestation pairing
5. Cadence (daily aggregation, quarterly minimum label re-issue)

Without this ADR, ADR-2605260175 §Decision 4 cannot ship — mitate medication_history_audit detects but yakushi label warnings stay static. The constitutional self-care closed-loop remains half-active.

## Decision

### Decision 1 — Aggregated AE payload variant

`com.etzhayyim.pharma.adverseEventReport` today is **patient-individual** flavor (encryptedPatientIdentityEnvelope + narrative + symptom codes). The aggregated variant uses the **same NSID** but distinct field shape — distinguishable by `aggregationLevel` enum.

Schema extension (lexicon update is part of this ADR landing):

```jsonc
{
  "aggregationLevel": {
    "type": "string",
    "knownValues": [
      "individual-patient",      // existing — yakushi pharma_adverse_event intake
      "aggregated-lot-window",   // NEW — yakushi pharma_post_market_surveillance daily roll-up
      "aggregated-quarter-summary" // NEW — yakushi pharma_packaging label-warning input
    ],
    "default": "individual-patient"
  },
  "aggregatedPayload": {
    "type": "object",
    "description": "Required when aggregationLevel != 'individual-patient'. Mutually exclusive with encryptedPatientIdentityEnvelope.",
    "properties": {
      "yakushiProductDid": { "type": "string", "format": "did" },
      "lotIdHashRangeStart": { "type": "string", "maxLength": 128 },
      "lotIdHashRangeEnd": { "type": "string", "maxLength": 128 },
      "windowStart": { "type": "string", "format": "datetime" },
      "windowEnd": { "type": "string", "format": "datetime" },
      "patientCountDistinct": { "type": "integer", "minimum": 0 },
      "medianOveruseDurationDays": { "type": "integer", "minimum": 0 },
      "medianDosesPerDay": { "type": "number", "minimum": 0 },
      "withdrawal8weekSuccessRate": { "type": "number", "minimum": 0, "maximum": 1 },
      "severityHistogram": {
        "type": "object",
        "description": "Histogram bucket counts by CIOMS Form III severity. No patient identity."
      },
      "symptomMedDraSocCodes": {
        "type": "array",
        "items": { "type": "string", "maxLength": 32 }
      }
    }
  }
}
```

When `aggregationLevel != "individual-patient"`:

- `encryptedPatientIdentityEnvelope` MUST be absent (G10 enforcement — aggregated must never carry a sealed identity envelope, even encrypted)
- `deviceFingerprintHash` MUST be absent (no per-patient signal at all)
- `narrative` MUST be aggregated-narrative only (template like "n patients reported X..."; no per-patient verbatim text)

The schema extension is backwards-compatible — existing individual-flavor records remain valid.

### Decision 2 — AE dedupe rule (cross-actor primary key)

**Problem**: same patient AE may surface twice — once through mitate `outcome_qol_followup` (patient self-report via PWA), once through yakushi `pharma_adverse_event` (patient AE intake via ameno or yakushi-specific channel). Without dedupe, severity histogram inflates.

**Primary key for dedupe**: `lotIdHashed` (SHA-256 of lot_id) + `severityBucket` + `onsetWeekIso`. All three present → same AE.

Reasoning:
- `lotIdHashed` is the only cross-actor stable key (patient pseudonym DID rotates every 30 days per mitate G2; yakushi side has no patient identity by design)
- `severityBucket` is CIOMS Form III bucket (mild / moderate / severe / serious / life-threatening / fatal) — coarse enough that genuinely distinct AEs don't collide
- `onsetWeekIso` is ISO week of onset — week-level resolution is too coarse for distinct AE collision risk while fine enough to dedupe re-submissions

Implementation (yakushi `pharma_post_market_surveillance` cell):

```
on receiving aggregated payload from mitate.outcome_qol_followup:
  for each (lotIdHashed, severityBucket, onsetWeekIso) tuple in incoming:
    if exists in yakushi.pharma_adverse_event keyed by same tuple within ±1 week:
      → mark as duplicate; do not increment severity histogram
      → record dedupe attestation in silenPharmaReview "ae-dedupe-event"
    else:
      → ingest into aggregated counter
```

Asymmetry note: dedupe runs on the **yakushi side** because yakushi is the canonical post-market-surveillance home (master charter §G5). mitate `outcome_qol_followup` always emits; yakushi decides whether to count. mitate does NOT dedupe outgoing — sending the same AE twice from mitate is acceptable since yakushi-side dedupe is the single source of truth.

### Decision 3 — Label-warning data-driven update mechanism

When the aggregated overuse signal moves a threshold, yakushi `pharma_packaging` cell re-issues the label warning text on the next lot. Thresholds:

| Signal | Threshold | Label warning text update |
|---|---|---|
| `withdrawal8weekSuccessRate` < 0.50 | severity-tier change | Add: "n人中 m人 が 8 週間で完全離脱できませんでした (n=N, period=YYYY-Q)" |
| `medianOveruseDurationDays` > 21 | severity-tier change | Add: "中央値で 22 日連用が観察されています (推奨 ≤ 3-5 日)" |
| `patientCountDistinct` > 100 in single quarter | severity-tier change | Add: "本期間中 N adherent から medicamentosa flag が報告されました" |
| `severityHistogram[severe + life-threatening] / total` > 0.10 | safety-tier change | Add: "重症化 risk が 10% 超え観察されています — 7 日連用前に mitate 経由で離脱 plan を構築してください" |

Label warning re-issue cadence:
- **Minimum cadence**: quarterly (calendar Q1/Q2/Q3/Q4) regardless of signal movement
- **Maximum cadence**: on-demand within 7 days when threshold crossed (faster than batch re-print warrants — printer queue accommodates urgent text update)
- **Patient communication**: existing adherents using current naphazoline lot get push notification on the G11 `ae-followup` channel (one of 3 permitted channels) when label warning materially changes

Implementation (yakushi `pharma_packaging` cell):

```
on quarterly cron OR on threshold-crossed signal from pharma_post_market_surveillance:
  fetch latest aggregated signal payload (Decision 1)
  evaluate thresholds (Decision 3 table)
  if any threshold crossed:
    generate new labelWarningText from G11 label-warning template (Council-attested)
    require silenPharmaReview scope = "label-warning-update-naphazoline" with
      Council Lv6+ ≥ 3 + 1 QP-equivalent + 1 licensed MD (mitate-side liaison)
    on approve:
      attach new labelWarningText to next lot's lotAttestation
      emit ae-followup push to active naphazoline-lot adherent cohort (via mitate)
      record signal attestation chain CIDs in pharma_packaging output
```

### Decision 4 — Joint silen-review flow

Three new silenPharmaReview scopes (lexicon extension):

- `cross-actor-ae-aggregation-baseline` — initial schema lock + dedupe rule activation
- `ae-dedupe-event` — per-event dedupe attestation (high-volume, batched daily into Merkle root commitment)
- `label-warning-update-naphazoline` — per-update label warning text approval

Three new silenMitateReview scopes (lexicon extension):

- `yakushi-cross-actor-signal-aggregation-baseline` (already listed in master ADR §Decision 8; this ADR finalizes the field schema)
- `ae-feed-throttle-baseline` — rate-limiting + back-pressure on mitate→yakushi feed
- `label-warning-update-naphazoline-mitate-cosign` — mitate-side licensed MD co-sign on yakushi label warning update

Pairing: each yakushi review of `label-warning-update-naphazoline` MUST have a paired silenMitateReview of `label-warning-update-naphazoline-mitate-cosign` within ±7 days. Unpaired → automatic deferral, mitate-side licensed MD escalation.

### Decision 5 — Cadence + back-pressure

Daily aggregation cadence at yakushi side (cron: `0 8 * * *`). mitate emits as patients self-report (event-driven, not batched).

Back-pressure: if yakushi aggregation lags > 48 hours, mitate `outcome_qol_followup` queues feed locally (G14 — local queue, never on Kotoba/Datomic) and retries with exponential backoff. After 7 days unacked, mitate escalates via licensed MD on-call channel.

### Decision 6 — Bootstrap path

The mechanism cannot be active until **mitate R2** (when `mitate_outcome_qol_followup` cell is activated — currently R2 scope per master Decision 4). However, the **schema and dedupe rule** must be locked **before** mitate R1 deploys to avoid mid-stream redesign.

So:
- This ADR ratifies at the time of mitate R1 deploy (or immediately after)
- yakushi `pharma_post_market_surveillance` cell R1 activation (sibling to mitate R2 activation): receives aggregated payload only — no individual handoff yet
- yakushi `pharma_packaging` label-warning update mechanism activates when **first quarter of mitate R2 cohort** has data (estimated 90-120 days post-mitate-R2)
- Until then: naphazoline label warning text stays at its initial G11 baseline (no harm, just no data-driven update)

## Consequences

**Positive**:
- Closes the **other half** of the mitate↔yakushi closed-loop — religious-corp gains a data-driven, patient-protective label warning mechanism that's structurally rare in commercial pharma (PMDA/FDA usually update labels on market-wide signals, not adherent cohort signals)
- AE dedupe primary key (lotIdHashed + severityBucket + onsetWeekIso) is **identity-free by design** — G7 + G10 are not "enforced via policy", they're **structurally impossible to violate** (the dedupe key contains no patient-identifying field)
- Joint silen-review pairing (yakushi label update ↔ mitate licensed MD co-sign) prevents one-actor capture of the loop — neither yakushi-side QP-equivalent nor mitate-side licensed MD can unilaterally change label warnings
- Daily aggregation cadence is fast enough to catch outbreak-style signals (e.g. counterfeit-lot adverse reactions appearing in a community) while being batched enough to prevent yakushi side from re-running label generation every minute

**Negative / costs**:
- Schema extension (aggregationLevel enum + aggregatedPayload object) requires lexicon migration — existing 12 individual-flavor records (yakushi Wave 1+1b+1c reference) need backfill with `aggregationLevel: "individual-patient"` default (low-cost migration, no semantic change)
- Label warning update cadence of quarterly minimum + on-demand maximum creates a non-trivial Council attestation load — assume ≤ 4 label updates per year per API across Wave 1 (12 APIs × 4 = 48 attestations/yr) plus on-demand surges; Council Lv6+ medical advisory needs ≥ 4 sitting members for this load (currently Bootstrap RFP is for 4 seats — fits)
- Bootstrap path means label warning data-driven update is **eventually consistent** — first 3-4 months of mitate R2 cohort accumulates without updates; some adherents may receive labels with pre-data baseline warnings during this window
- Per-event `ae-dedupe-event` attestation creates high-volume on-chain footprint — mitigated by daily Merkle root commitment (commit just the root + IPFS-pin the day's full attestation list), but still adds 365 commitments/year

**Risks**:
- **Dedupe key collision** — two genuinely distinct AEs with same (lotIdHashed, severityBucket, onsetWeekIso) get treated as one. Mitigation: severity histogram + symptom MedDRA SOC codes provide secondary check; in 18-month bias audit baseline, Council reviews collision rate
- **Label warning text bloat** — if every threshold movement adds a new sentence, naphazoline label becomes unreadable; mitigation = G11 label-warning-text-template caps total length + Council attestation of every text revision
- **Adverse selection in PWA-reported AE** — patients with worse outcomes more likely to report (selection bias). Mitigation = mitate R2 cohort bias audit per master G10 includes "AE-report selection bias" metric
- **mitate dedupe inversion** — if mitate's own dedupe logic ever activates (against current design), there's nothing on yakushi side to detect; mitigation = mitate `outcome_qol_followup` MUST NOT dedupe outgoing (enforced via cell test) — single source of truth on yakushi side

## Alternatives Considered

### A. Separate lexicon for aggregated AE (e.g. `com.etzhayyim.pharma.adverseEventAggregated`)

Considered. Keeps individual + aggregated visibly distinct at the NSID level. Rejected because:
- Two lexicons share ~70% of fields (lotAttestationUri, severity, MedDRA codes, etc.) — DRY violation
- Cross-actor recipient registry (G7 enforcement) ends up duplicated
- Existing yakushi cells that read `adverseEventReport` would need both-NSID handling
- `aggregationLevel` enum is cleaner — single schema, discriminated union

### B. Dedupe on mitate side (before emit)

Rejected. mitate side has no view of yakushi-side intake (yakushi receives AEs from multiple sources — patient direct via yakushi-pwa, vendor channels for non-yakushi-distributed product, etc.). Single-source-of-truth dedupe must live where all sources converge — yakushi side.

### C. Patient pseudonym DID as dedupe key (instead of lot-hash + severity + week)

Considered. More precise dedupe per actual patient. Rejected because:
- mitate pseudonym DID rotates every 30 days — across rotations, the same patient appears as different DIDs (false negatives)
- yakushi side has **no** patient pseudonym DID by design (G7 + G10) — can't dedupe against something it doesn't store
- The current key (lot-hash + severity + week) is **structurally identity-free**, which is the stronger constitutional property

### D. Label warning re-issue on every signal threshold crossing (no quarterly minimum)

Considered. More responsive to fresh data. Rejected because:
- Council attestation load becomes unbounded (every micro-signal crossing triggers a review)
- Patient confusion: label warning text changing weekly produces "fatigue" (G11 risk)
- Quarterly minimum + on-demand maximum is the right balance — guaranteed updates + emergency responsiveness

## References

- ADR-2605250500 (yakushi master charter — G5 AE public reporting + G10 patient privacy)
- ADR-2605260100 (mitate master charter — §Decision 8 cross-actor lexicon emit boundary)
- ADR-2605260175 (mitate condition 5 — Decision 4 yakushi cross-actor signal)
- ADR-2605260200 (mitate R1 — cells active scope)
- ADR-2605181100 (encrypted confidentiality substrate — G2 envelope + G7 sealed-recipient registry)
- 00-contracts/lexicons/com/etzhayyim/pharma/adverseEventReport.json — schema extension target
- WHO-UMC causality assessment, CIOMS Form III severity (referenced in adverseEventReport)
- ICH E2D Post-Approval Safety Data Management — guidance for aggregated reporting cadence
