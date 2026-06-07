---
id: adr-2605260200-mitate-r1-advisory-self-care-pwa
title: "mitate R1 — self-care advisory PWA (intake + emergency_screen + medication_audit + triage 4 cells active; advisory-only; no 検査 ordering; no Rx; unlimited patient)"
status: proposed
doc_type: adr
topic: mitate-r1-advisory
authoritative: true
last_verified: 2026-05-25
authoritative_for:
  - R1 phase transition from R0 scaffold to operational advisory tier
  - 4 cells (rhinitis_intake / emergency_screen / medication_history_audit / rhinitis_triage) activation procedure
  - mitate-pwa carve-out under 60-apps/mitate-pwa/ (separate from ameno per master Decision F)
  - 8 baseline attestations enumerated for R1 deploy unlock (G1/G2/G3/G5/G8/G9/G11/G13)
  - Bias audit R1 baseline (pre-clinical-data, methodology + monitoring plan only)
  - R1 exit criteria → R2 entry criteria
depends_on:
  - adr-2605260100-mitate-diagnostic-routing-charter
  - adr-2605260115-mitate-condition-1-allergic-rhinitis-perennial
  - adr-2605260130-mitate-condition-2-vasomotor-rhinitis
  - adr-2605260145-mitate-condition-3-chronic-sinusitis
  - adr-2605260160-mitate-condition-4-septal-deviation
  - adr-2605260175-mitate-condition-5-rhinitis-medicamentosa
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605231525-no-server-key-religious-corp-architecture
related:
  - 20-actors/mitate/                                       # R0 scaffold (this transitions to R1 active)
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_{rhinitis_intake,emergency_screen,medication_history_audit,rhinitis_triage}/
  - 60-apps/mitate-pwa/                                     # this ADR creates this tree
  - 50-infra/murakumo/fleet.toml                            # cell placement (levi node, R1 active entries)
supersedes: []
superseded_by: []
---

# mitate R1 — Self-care advisory PWA

**Date:** 2026-05-25
**Author:** Jun Kawasaki
**Status:** Proposed

## Context

mitate R0 (ADR-2605260100 + 5 condition sub-ADRs) established:
- Tier-B actor `mitate` (sibling of yakushi)
- 13 Pregel cells (all import-time RuntimeError gated)
- 8 lexicons (`com.etzhayyim.mitate.*`)
- 14 constitutional gates + 10 non-goals
- 4-phase roadmap R0→R3

R1 phase transitions from scaffold to **operational advisory tier** — the smallest forward step that unlocks real value:

- **4 cells activate**: `rhinitis_intake` + `emergency_screen` + `medication_history_audit` + `rhinitis_triage`
- **9 cells stay gated**: diagnostic ordering (IgE / smear / endoscopy / CT / rhinomanometry) + treatment router + SLIT cohort + ESS planner + outcome followup ― all R2+ scope
- **No 検査 ordering**: R1 triage returns top-3 condition posterior + `escalation = "recommend-md-visit"` or `"self-care-advisory"` only
- **No Rx**: R1 advisory never names Rx-tier medications directly (only `escalation = "recommend-md-{visit, otolaryngology, allergy-specialist}"`)
- **Patient unlimited**: advisory-only is low-marginal-cost; admission throttle = community PWA throughput
- **mitate-pwa carved out under 60-apps/mitate-pwa/** per master Decision F (separate from ameno — medical disclaimer UX integrability + future R2 MD-dashboard view)

R1 surfaces:
1. Self-care environmental advisory for 4/5 conditions (1: allergic / 2: vasomotor / 4: structural / 5: medicamentosa) where lifestyle + OTC manageable for many patients
2. Recommend-MD-visit routing for condition 3 (12-wk gate met) + all G6-flagged groups + all triage escalation paths
3. G5 emergency fail-safe with ER routing — handles real anaphylaxis-like presentations
4. Condition 5 medication audit + 離脱 advisory — yakushi naphazoline closed-loop **half-active** (mitate-side detection live; yakushi-side label-warning update activates at R2 cross-actor aggregation baseline)

## Decision

### Decision 1 — Activate 4 cells (gate removal procedure)

Each cell's `cell.py` requires the following Council attestation to unlock:

| Cell | Required CIDs (Council Lv6+ ≥ 3 multisig) |
|---|---|
| `mitate_rhinitis_intake` | (a) `COUNCIL_CHARTER_ATTESTATION_TX_HASH` (master ADR-2605260100 ratification) <br> (b) `SILEN_MITATE_BASELINE_REVIEW_CID` (silenMitateReview scope `charter-baseline`) <br> (c) `PATIENT_CONSENT_RECEIPT_PROTOCOL_CID` (G1) <br> (d) `ENCRYPTED_ENVELOPE_RECIPIENT_REGISTRY_CID` (G2) <br> (e) `G11_INTAKE_FORM_TEXT_REVIEW_CID` (no addictive design) |
| `mitate_emergency_screen` | (a)+(b) + (c) `ER_ROUTING_PROTOCOL_CID` + (d) `G5_FALSE_NEGATIVE_ADVERSARIAL_TESTING_BASELINE_CID` (Council Lv6+ ≥ 3 + 1 emergency medicine specialist) + (e) `LLM_SECOND_PASS_PROMPT_TEMPLATE_CID` (G12 + G13 frozen) |
| `mitate_medication_history_audit` | (a)+(b) + (c) `CONDITION_5_MEDICATION_AUDIT_BASELINE_CID` + (d) `YAKUSHI_CROSS_ACTOR_SIGNAL_BASELINE_CID` (R1 placeholder = detection-only, yakushi-side aggregation activates R2) + (e) `LICENSED_MD_REGISTRY_CID` (≥ 1 MD) |
| `mitate_rhinitis_triage` | (a)+(b) + per-condition Bayesian prior baselines (1..5) + `LLM_PROMPT_TEMPLATE_TRIAGE_BASELINE_CID` + `G6_ESCALATION_PROTOCOL_BASELINE_CID` + `G3_DISCLAIMER_TEXT_BASELINE_CID` + `LICENSED_MD_REGISTRY_CID` |

Gate removal is a **single atomic commit** that sets all CIDs simultaneously. Partial unlock is a constitutional violation (importing one R1 cell with R2+ cells still gated is the intended state — R2+ cells remain RuntimeError until their own ADR lands).

### Decision 2 — 8 baseline attestations required for R1 deploy

| # | silenMitateReview scope | Council quorum | Specialist co-sign |
|---|---|---|---|
| 1 | `charter-baseline` | Lv6+ ≥ 3 | — |
| 2 | `g3-disclaimer-text-baseline` | Lv6+ ≥ 3 | 1 licensed MD |
| 3 | `g5-emergency-keyword-baseline` | Lv6+ ≥ 3 | 1 emergency medicine specialist |
| 4 | `g5-false-negative-adversarial-testing-baseline` | Lv6+ ≥ 3 | 1 emergency medicine specialist |
| 5 | `g6-escalation-protocol-baseline` | Lv6+ ≥ 3 | 1 licensed MD |
| 6 | `g11-intake-form-text-review` | Lv6+ ≥ 3 | — |
| 7 | `g11-notification-channel-baseline` | Lv6+ ≥ 3 | — |
| 8 | `condition-{1..5}-bayesian-prior-baseline` (5 separate attestations bundled) | Lv6+ ≥ 3 each | 1 licensed MD each |

Total: **8 + 5 = 13 attestation records** required before R1 deploy. Sequencing: attestations 1-7 in any order; attestation 8 (per-condition Bayesian prior) requires #1 + #2 + #5 first.

### Decision 3 — mitate-pwa app carve-out

New app under `60-apps/mitate-pwa/`:

- **Runtime**: T3 TS Native (Cloudflare Worker + Hono + @etzhayyim/kotodama-host-sdk + esbuild) per kotodama default
- **Authentication**: Adherent SBT + passkey ES256 (G1); 30-day rotating pseudonym DID derived at intake time
- **Substrate**: `@etzhayyim/sdk` only (G14); all patient-data writes go to AT MST with `com.etzhayyim.encrypted.*` envelope wrapping
- **Inference**: Murakumo LiteLLM gateway at 127.0.0.1:4000 → gemma4:e4b medical distill variant (G12 + G13)
- **G11 UX invariants** (constitutional, lint-enforced):
  - No streak counter, no score reveal during intake, no progress bar gamification
  - Push notifications only for the 3 urgency-only channels (emergency ack / appointment reminder / AE followup)
  - No re-engagement push for non-completion (intake is single-session by design)
  - No "you may have X" anxiety priming text — disclaimer-first framing
- **Disclaimer-first flow** (G3): every triage verdict screen opens with disclaimer text + acknowledgment checkbox before posterior probabilities or escalation are revealed
- **Embed mode**: NOT enabled at R1 (avoid being framed inside other apps where context lost — privacy + advisory clarity)
- **Languages**: Japanese (ja-JP) primary at R1; English (en-US) secondary if reviewer available. Other languages → wait for G10 bias audit per-language methodology

App structure:

```
60-apps/mitate-pwa/
├── kotodama.jsonld              # APP_NANOID, embedUrl disabled
├── src/app.ts                   # createWorkerExport — intake form + triage display + emergency-escalation overlay
├── svelte/                      # patient-facing UI (Svelte + tailwind)
│   ├── routes/
│   │   ├── +page.svelte         # consent + intake form
│   │   ├── disclaimer/          # G3 disclaimer mandatory acknowledgment
│   │   ├── triage/              # top-3 condition + escalation display
│   │   ├── emergency/           # ER routing instruction overlay (G5)
│   │   └── medication-audit/    # condition-5 離脱 plan display
│   └── lib/
│       ├── consent.ts           # G1 consent receipt issuance
│       ├── envelope.ts          # G2 XChaCha20-Poly1305 envelope wrap (via @etzhayyim/sdk)
│       └── pseudonym.ts         # 30-day rotating DID derivation
├── tests/
│   ├── g3-disclaimer-flow.test.ts
│   ├── g5-emergency-bypass-impossible.test.ts
│   ├── g11-no-addictive-design.test.ts
│   └── g14-substrate-boundary.test.ts
└── README.md
```

The PWA app scaffold itself is a follow-up commit after this ADR ratifies — this ADR locks the contract; the app is implementation.

### Decision 4 — Murakumo fleet.toml R1 activation entries

```toml
# 50-infra/murakumo/fleet.toml — add at R1 ratification
[cells.mitate]
levi = [
  "mitate_rhinitis_intake",
  "mitate_emergency_screen",
  "mitate_medication_history_audit",
  "mitate_rhinitis_triage",
]
# R2+ cells (allergy_ige_panel_order on naphtali, nasal_smear_eosinophil on zebulun,
# nasal_endoscopy_acquire + rhinomanometry on joseph, paranasal_ct_route on simeon,
# treatment_router on levi, slit_cohort_tracker on levi, ess_surgery_planner on levi,
# outcome_qol_followup on levi) NOT activated until R2 ADR.
```

healthzPort range 13070-13082 reserved (per manifest.jsonld R0). R1 activates 13070-13073 (4 ports), 13074-13082 remain ungated.

### Decision 5 — Licensed MD-in-loop requirement (R1 minimum)

R1 requires **≥ 1 licensed MD on Council medical advisory**. Qualification:

- 国内医師免許 (Japanese medical license) OR EU/EEA medical license OR US MD/DO equivalent
- Active practice (last 3 years) preferred but not required (semi-retired adherent-MDs valid)
- DID registered in `LICENSED_MD_REGISTRY_CID` (Council-attested)
- Hardware-token / passkey custody (G13 no-server-key)

R1 MD role:
- Attest condition-specific Bayesian prior baselines (Decision 2 #8 ×5)
- Attest G3 disclaimer text (Decision 2 #2)
- Attest G6 escalation protocol (Decision 2 #5)
- Review G5 false-negative adversarial test results (Decision 2 #4) — paired with emergency medicine specialist
- On-call rotation for `mitate.emergencyEscalation` acknowledgment receipts (G11 urgency-only push)
- Monthly bias audit review (Decision 6)

If R1 MD becomes unavailable (revocation / death / withdrawal), R1 advisory pauses (intake form returns "temporarily unavailable") until replacement MD attestation lands. Council motion required within 30 days.

### Decision 6 — Bias audit R1 baseline (methodology only — no clinical data yet)

R1 has no patient cohort to measure demographic parity on. Instead, R1 attestation registers the **methodology** that R2 will execute against:

- Quarterly measurement schedule (calendar Q1/Q2/Q3/Q4)
- Demographic axes (age 5 brackets / sex 3 categories / language / income proxy postal code)
- Top-3 condition recall + escalation rate per axis
- Treatment plan reading-level (Flesch-Kincaid Japanese / 漢字使用率) per language
- ≥ 5% disparity threshold → `silenMitateReview` scope `bias-audit-corrective-action` with Council Lv6+ ≥ 3 mandate

R1 monthly review (interim, pre-cohort): patient intake count by language + age bracket only, watch for selection bias before R2 starts collecting outcome data.

### Decision 7 — R1 exit criteria → R2 entry criteria

R1 is "complete" when ALL of the following hold for ≥ 90 consecutive days:

1. ≥ 100 patient intakes processed without any G5 fail-safe false negative (verified via independent emergency medicine specialist sampled review of 10% intake)
2. ≥ 5 patient self-reported outcomes (informal — pre-R2 outcome_qol_followup) where R1 advisory was helpful, with no patient harm reported via Council medical advisory channel
3. Bias audit R1 monthly review shows no language / age bracket selection bias > 10% from community baseline
4. yakushi-side label-warning update mechanism design (cross-actor aggregation baseline) drafted and Council-reviewed (pre-R2 dependency)
5. ≥ 2 licensed MD attestations on Council (R2 deploy requires ≥ 2)
6. Hanami robot mechanical design completed and Council attestation in flight (R2 critical path)

R2 entry ADR will reference this R1 exit attestation set.

## Consequences

**Positive**:

- First **operational** religious-corp diagnostic + treatment advisory — the §2(e) anti-gatekeeping value moves from constitutional declaration to delivered patient experience
- Condition 5 medication audit + 離脱 advisory live → adherents with rhinitis medicamentosa get actionable 離脱 protocols immediately, even before R2 yakushi-side label feedback closes the loop
- G5 emergency fail-safe operational — religious-corp gains a real-world fail-safe pattern that R2/R3 (and other future medical actors) inherit
- mitate-pwa as standalone app (not ameno extension) keeps medical disclaimer UX clean and unblocks the R2 MD-dashboard view evolution
- 4-cell activation footprint is minimal (1 Murakumo node `levi`, 4 healthzPorts) — operational complexity stays low while the framework proves out

**Negative / costs**:

- R1 advisory is text-only — no Rx-specific advice, no IgE evidence — many adherent patients will still need MD visit for definitive answers; advisory value is "triage smarter" not "skip the MD"
- Licensed MD bottleneck: 1 MD covers ALL `mitate.emergencyEscalation` ack receipts (G5 on-call), which is workable at R1 scale but not at R2+ — R2 entry criteria #5 (≥ 2 MD) is hard prerequisite
- G5 false-negative adversarial testing requires an emergency medicine specialist — Council medical advisory needs ≥ 1 such specialist before R1 attestation can complete; specialist recruitment is R1 critical path
- yakushi cross-actor signal aggregation is **half-live** at R1 (mitate detects; yakushi does not yet act on aggregated signal); the constitutional closed-loop is incomplete until R2 — this is intentional but creates a "naphazoline detection without label update" gap for ~quarter

**Risks**:

- Patient over-reliance on advisory (Hawthorne-like effect — patients delay needed MD visit because advisory "felt sufficient"); mitigation = G3 disclaimer + bias audit Decision 6 monthly review of "advised-md-visit-but-no-follow-up" signal (R2-onward outcome tracking)
- G5 false negative in production despite adversarial testing — mitigation = 10% sampled review by emergency medicine specialist + monthly Council medical advisory escalation pathway audit
- Patient consent revocation cascade — if many patients revoke consent post-intake, training-data baseline (G9) for R2 model bias measurement is degraded; mitigation = consent receipt protocol Decision 2 #1 includes "revoke without re-questioning" UX + separate consent for analytics vs advisory
- Adversarial intake (synthetic / troll / red-team disguised as patient) skewing condition-5 medication audit signal — mitigation = device fingerprint dedupe (already in lexicon) + rate limiting at PWA layer + bias audit flag

## Alternatives Considered

### A. R1 activates only 2 cells (intake + emergency_screen only — defer triage to R2)

Considered. Reduces R1 complexity and licensed-MD-attestation burden. Rejected because:
- Without triage, R1 returns only emergency escalation + raw symptom acknowledgment — too thin to validate the advisory tier value proposition
- medication_history_audit (condition 5) wants to land at R1 to start collecting the yakushi naphazoline feedback signal pattern even before R2 closes the loop
- The 4-cell minimum is what makes R1 a meaningful "self-care advisory" rather than just "emergency triage"

### B. R1 extends to treatment_router with `escalation = "recommend-md-visit"` only

Considered. treatment_router could be advisory-only at R1 (return INN suggestions for self-care environmental + escalate for everything Rx). Rejected because:
- treatment_router requires per-condition treatment ladder baselines (5 conditions × 4 tiers ~= 20 baseline attestations) — too many to land in single R1 ADR
- INN recommendation without licensed MD per-recommendation co-sign (G4 R2+) blurs the advisory line patients perceive
- Cleaner constitutional break: R1 = "what condition might this be + when to see MD"; R2 = "what treatment options exist + which yakushi product fits"

### C. R1 in ameno PWA (per master Alternative F rejected)

Re-considered briefly for R1 to reduce deploy cost. Rejected — same reasoning as master Alternative F: medical disclaimer UX integrability + R2 MD-dashboard divergence. mitate-pwa standalone is the right shape.

### D. R1 ships without bias audit baseline (defer to first quarterly review with real data)

Rejected. Master charter §G10 requires bias audit baseline before R2+ deploy. R1 registering the methodology (without data) provides the audit framework + monitoring plan + threshold — the data simply accumulates against an already-attested standard. Skipping baseline registration would force a methodology-and-data combined attestation later, which is a worse review pattern (entangles two judgments).

## References

- ADR-2605260100 (mitate master charter — §Decision 4 R1 phase definition)
- ADR-2605260115/130/145/160/175 (5 condition sub-ADRs — Bayesian prior + triage logic per condition)
- ADR-2605181100 (encrypted confidentiality substrate — G2 envelope mechanism)
- ADR-2605231525 (no-server-key invariant — G13 physician + MD key custody)
- ADR-2605215000 (Murakumo-only inference — G12)
- ADR-2605250500 (yakushi master charter — cross-actor sibling, condition-5 closed-loop other half)
- ADR-2605250630 (yakushi Wave 1c R1 — sibling R1 ADR pattern reference)
