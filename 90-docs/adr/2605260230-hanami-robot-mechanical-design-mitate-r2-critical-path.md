---
id: adr-2605260230-hanami-robot-mechanical-design-mitate-r2-critical-path
title: "Hanami (鼻見) robot — mechanical design + safety validation + FDA Class I/II SaMD-equivalent attestation (mitate R2 critical path)"
status: proposed
doc_type: adr
topic: hanami-robot-design
authoritative: true
last_verified: 2026-05-25
authoritative_for:
  - Hanami robot class identity (mitate-native, kuni-umi 8th class sibling)
  - Mechanical design envelope (4mm 軟性スコープ + 6-DOF arm + force-feedback ≤ 0.5 N + autoclave 滅菌対応)
  - Safety validation matrix (5 hazard categories × 4 mitigation layers)
  - FDA Class I/II + PMDA SaMD-equivalent + EU MDR Class IIa attestation pathway (jurisdiction-specific, JP-first)
  - Murakumo image classifier wiring (gemma4:e4b vision distill medical variant, open weights G13)
  - Operator + ENT specialist DID attestation (G4 N≥2 witness invariant)
  - 4-phase build path R0 design → R1 prototype → R2 community-center pilot → R3 multi-site
depends_on:
  - adr-2605260100-mitate-diagnostic-routing-charter
  - adr-2605260145-mitate-condition-3-chronic-sinusitis
  - adr-2605260160-mitate-condition-4-septal-deviation
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-no-server-key-religious-corp-architecture
related:
  - 20-actors/mitate/                                              # owning actor
  - 20-actors/kuni-umi/                                            # robotics class ontology source
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_nasal_endoscopy_acquire/       # the cell that uses Hanami
supersedes: []
superseded_by: []
---

# Hanami robot — mechanical design + safety validation

**Date:** 2026-05-25
**Author:** Jun Kawasaki
**Status:** Proposed

## Context

mitate master charter (ADR-2605260100) declared **Hanami (鼻見)** as a new R2+ robotics class — placeholder only at R0. mitate R1 ADR (ADR-2605260200) §"R1 exit → R2 entry criteria" lists "Hanami robot mechanical design completed and Council attestation in flight" as a hard R2 entry prerequisite.

This ADR locks the design. Without it, mitate R2 (community-center pilot with 100-patient ceiling) cannot proceed past R1 advisory tier.

Hanami sits in the same robotics class system as kuni-umi's 7 existing classes (Otete / Quad / Hitogata / Mimi / Sora / Hoshi / Funamori). It's a **mitate-native** new class (8th by count, but owned by mitate not kuni-umi — same pattern as silicon Wave 2 introducing Funamori).

## Functional requirements (from mitate condition 3 + 4 sub-ADRs)

| Use case | Source ADR | Mechanical requirement |
|---|---|---|
| Chronic sinusitis subtype classification (CRSsNP / CRSwNP / 好酸球性 / 歯性 / 真菌性) | 2605260145 §Decision 2 | 4K image acquisition of 中鼻道 + 鼻茸 visualization + 粘膜性状 capture |
| Septal deviation type classification (C / S / spur) + 下鼻甲介肥大 合併評価 | 2605260160 §Decision 2 | bilateral nasal cavity navigation + structural measurement |
| Patient comfort during awake procedure | mitate master §G11 | force-feedback limit + soft-tip + sedation-free design target |
| Sterile reuse across patients | sterile process invariant | autoclave (134°C, 15 min) compatible |
| Murakumo-only image classification | mitate G12 + G13 | on-device JPEG/H.264 encode → Murakumo gateway upload (NO cloud vendor inference path) |
| ENT specialist remote attestation | mitate G4 N≥2 | live video feed routable to ENT specialist DID for real-time review |

## Decision

### Decision 1 — Mechanical envelope

| Parameter | Value | Rationale |
|---|---|---|
| **Scope diameter** | 4.0 mm ± 0.1 mm | Below 4.0 mm risks insufficient optics + tool channel; above 4.5 mm uncomfortable for adult awake patient; 4.0 mm is industry standard for flexible nasopharyngoscope |
| **Scope length (insertion)** | 300 mm | Reaches choana + upper nasopharynx; longer not required for nasal cavity examination scope |
| **Scope flexibility** | Distal tip articulation ± 130° in 2 planes (4-way bending) | Allows 中鼻道 visualization without forcing patient head position |
| **Optics** | CMOS sensor 1920×1080 @ 60fps, 110° field of view, focal range 3-50 mm | 4K available but 1080p is sufficient for downstream classifier + reduces bandwidth |
| **Illumination** | LED ring, 4500K color temperature, 100 lumen ± 10% with auto-exposure | Color temperature matters for downstream classifier — must be Council-attested and frozen per lot |
| **Arm degrees of freedom** | 6-DOF (3 translational + 3 rotational) | Position + orientation control for scope insertion path |
| **Arm reach** | 600 mm | Reaches patient seated in standard exam chair from beside-the-chair mount |
| **Arm payload** | 2 kg | Scope + cabling + sterile drape weight is < 0.5 kg; 2 kg gives 4× safety margin |
| **Force-feedback limit (hard cutoff)** | **0.5 N** at scope distal tip | Above 0.5 N risks mucosal trauma / epistaxis; this is the **constitutional limit** — arm motor torque physically constrained to prevent exceeding |
| **Force-feedback resolution** | 0.05 N | 10% of cutoff threshold; sufficient for haptic monitoring |
| **Position repeatability** | ± 0.1 mm | Re-imaging consistency across exams (R3 longitudinal patients) |
| **Speed (operational max)** | 50 mm/s linear, 30°/s rotational | Below pain reflex response time; allows operator override-stop within 100 ms reaction window |
| **Sterilization** | Autoclave 134°C × 15 min compatible (scope tip + 50 mm shaft); chemical sterilization (glutaraldehyde 2%) compatible (full scope length) | EN ISO 17665-1 + Spaulding criteria semi-critical device |
| **Tip material** | Medical-grade silicone over titanium core, biocompatibility per ISO 10993-1/-5/-10 | Soft-tip prevents inadvertent mucosal trauma |
| **Cable / fiber bundle** | Hybrid (camera signal + LED power + air/water purge channel), 2.5 mm OD inside 4.0 mm shaft | Air/water purge channel cleans optics mid-procedure without withdrawal |
| **Patient interface** | Disposable nose-tip cover (single-use, biodegradable PLA) | Even with autoclave reuse, the patient-contacting surface is single-use for cross-contamination safety |
| **Operator interface** | Foot pedal (insert/withdraw/freeze-frame) + voice command (frame capture) + emergency stop | Hands-free during procedure |
| **Emergency stop** | Within 100 ms reaction; arm freezes in current position (no automatic retract — operator decides withdraw path) | Avoids automated withdrawal causing additional trauma |

### Decision 2 — Safety validation matrix

5 hazard categories × 4 mitigation layers:

| Hazard | L1 Hardware | L2 Firmware | L3 Operator UX | L4 ENT specialist override |
|---|---|---|---|---|
| **Mucosal trauma (epistaxis)** | 0.5 N hard force cutoff + soft silicone tip | Force telemetry → auto-pause if rising trend detected | Visible force gauge in operator UI + audible warning at 0.3 N | ENT specialist remote stop authority via mitate path-based DID |
| **Excessive depth insertion** | Mechanical stopper at 300 mm | Depth telemetry → auto-pause at 250 mm | Visible depth gauge | ENT specialist remote stop |
| **Patient sudden movement** | Arm compliance mode (back-driveable) | IMU on scope tip → motion detection → freeze | Operator-trigger freeze | ENT specialist remote stop |
| **Cross-contamination** | Autoclave-compatible scope + single-use tip cover | Lot ID tag on tip cover read at attach | Operator UI requires fresh tip cover scan | n/a (sterile chain attested at facility level) |
| **Imaging classifier mis-routing** | All image data goes via Murakumo gateway URL (G12 hardcoded) | Network outbound restricted to Murakumo IP whitelist | Operator UI shows Murakumo connection status indicator | ENT specialist final attestation overrides any AI classification |

Each hazard requires Council Lv6+ ≥ 3 attestation that all four mitigation layers are independently verified in the pre-deploy validation suite.

### Decision 3 — Validation pathway

Pre-deploy validation runs in three phases:

**Phase A — Bench validation** (no human subjects, R1 prototype):
- 1000 actuation cycles at 0.5 N cutoff — verify no force excursion > 0.55 N (10% tolerance)
- Autoclave validation × 100 cycles — verify no optics degradation or mechanical drift
- Network isolation test — verify cannot reach `api.openai.com`, `api.anthropic.com`, `runpod.io`, `aiplatform.googleapis.com`, `bedrock-runtime.*.amazonaws.com` (G12 enforcement)
- Emergency stop reaction test × 100 — verify all < 100 ms

**Phase B — Cadaver / phantom validation** (silicone nasal cavity phantom + cadaveric tissue, R1→R2 transition):
- 50 phantom insertions with 5 operators — verify 0 force-cutoff trips above 0.5 N
- 30 cadaveric tissue insertions with ENT specialist supervision — verify image quality sufficient for top-7 sign visualization (chronic sinusitis subtype) + 弯曲 type classification
- Inter-operator reliability — Cohen's kappa ≥ 0.7 between operators on same phantom imaging

**Phase C — Community-center clinical validation** (R2 pilot, mitate R2 ADR scope):
- First 20 patients: each procedure double-attested (operator DID + ENT specialist DID on live video link, real-time review)
- Patients 21-100 (R2 ceiling): operator DID + ENT specialist DID async attestation within 24 hours
- All 100 patients participate in bias audit demographic axes per master G10
- Any single force-cutoff trip > 0.55 N or operator error rate > 5% pauses pilot until Council review

### Decision 4 — Jurisdiction attestation pathway

Hanami is a **patient-contacting active medical device** — it falls under jurisdiction regulatory frameworks. religious-corp does not seek FDA pre-market approval (vendor-side path), but pursues **SaMD-equivalent + general wellness device attestation** under each jurisdiction's adherent-self-care carve-out where available:

| Jurisdiction | Classification target | Path |
|---|---|---|
| **Japan (PMDA)** | 医療機器 Class II 相当 (low-mid risk; flexible endoscope precedent) | 製造販売届出 + QMS 適合性調査; religious-corp 内 community-center 使用は 業務範囲外 carve-out 適用; if not adequate, R3 path requires 製造販売業許可 + 製造業許可 (薬機法) |
| **United States (FDA)** | Class I + General Wellness Device intended-use carve-out | 21 CFR Part 880 (general hospital devices); Hanami's image data goes to clinician for diagnosis (NOT directly to patient as diagnostic claim) keeps it Class I under FDA General Wellness Policy |
| **EU (EU MDR 2017/745)** | Class IIa (rule 5: invasive transient < 60 min, but classifier-assisted → rule 11 software medical device adjacency) | CE marking via Notified Body; technical file per Annex II + post-market surveillance per Annex III |
| **All others** | Defer to PMDA precedent + jurisdiction-specific attestation in R3 ADR | R3 deploy is jurisdiction-by-jurisdiction |

R2 pilot is **JP only** (PMDA path). R3 multi-jurisdiction expansion needs per-jurisdiction sub-ADR.

### Decision 5 — Build path (4 phases)

| Phase | Scope | Pre-req | Status |
|---|---|---|---|
| **R0 — Design specification (this ADR)** | mechanical envelope + safety matrix + validation plan + jurisdiction path; no physical fabrication | mitate R1 ADR ratified | proposed |
| **R1 — Prototype + Phase A bench validation** | one prototype unit; 1000-cycle force testing; autoclave 100-cycle; network isolation testing | R0 ratified + ≥ 1 ENT specialist on Council medical advisory + manufacturing partner DID registered (kuni-umi class-A sterile sibling for production hand-off) | ⏳ separate ADR |
| **R2 — Phantom + cadaveric validation (Phase B) → community-center deploy (Phase C)** | 5 production units (1 per pilot community-center initially); Phase B + Phase C validation; 100-patient ceiling per mitate R2 ADR | R1 ratified + Phase A validation passed + PMDA 製造販売届出 filed + ≥ 2 licensed MD + 1 ENT specialist on Council + image classifier baseline attested (gemma4:e4b vision distill medical variant) | ⏳ separate ADR |
| **R3 — Multi-site community deployment** | ~50 units across community centers; multi-jurisdiction (US / EU) attestation rollout | R2 ratified + 60-day public review + per-jurisdiction sub-ADR | ⏳ separate ADR |

### Decision 6 — Murakumo image classifier wiring

Hanami captures image/video locally and uploads via Murakumo LiteLLM gateway only (G12). No vendor classifier endpoint is reachable from Hanami device firmware (network whitelist enforces).

Image classifier model: **gemma4:e4b vision distill medical variant** — open weights (G13), trained per ADR-2605250400 gemma-coder-distill recipe adapted for endoscopy domain. Training data is **consent-only + Council-attested IRB-equivalent** per mitate G9.

Classifier output structure (input to mitate `nasal_endoscopy_acquire` cell):

```
{
  "modelVariantCid": "<IPFS CID of frozen weights>",
  "confidence": {"CRSsNP": 0.62, "CRSwNP": 0.18, "eosinophilic": 0.12, "odontogenic": 0.05, "fungal": 0.03},
  "deviationType": null,    // populated when condition 4 indication
  "qualityFlags": {"motion-blur": false, "occlusion": false, "out-of-focus": false},
  "ent_specialist_review_required": true   // ALWAYS true for R2 (G4 N≥2 invariant)
}
```

The classifier confidence is **never** patient-displayed without ENT specialist co-sign (G4) — even the operator UI shows raw image first and classifier output as advisory annotation after specialist review.

### Decision 7 — Open-source release (G13)

Hardware design files (mechanical CAD, firmware source, network whitelist config, classifier training corpus metadata) are Apache 2.0 + Charter Compliance Rider v2.0 — published under `50-infra/hanami-robot/` (R1 ADR creates this directory; this R0 design ADR commits the path reservation only).

External manufacturers (charter-aligned per CHARTER-RIDER §3) may fabricate Hanami units for their own community centers. Cross-religious-corp manufacturing requires `silenMitateReview` scope `hanami-cross-corp-manufacture-attestation`.

## Consequences

**Positive**:
- Unblocks mitate R2 critical path — the single largest dependency for community-center pilot deploy
- 0.5 N hard force cutoff at hardware level (not just firmware) is a **structurally-stronger** patient safety property than typical commercial flexible endoscopes (which rely on operator skill)
- Murakumo-only classifier path (G12) + open-weights (G13) means no commercial vendor lock-in; classifier improvements flow back to all religious-corp deploys via IPFS-pinned weight updates
- Hardware design open-sourced under Charter Rider — other charter-aligned religious-corps can manufacture without IP friction (§2(e) anti-gatekeeping at the device level, not just the knowledge level)
- Jurisdiction-specific attestation path (PMDA-first) is pragmatic — avoids attempting multi-jurisdiction simultaneous launch which would multiply attestation cost without proportionate value

**Negative / costs**:
- ENT specialist on Council medical advisory is now a hard R1 prerequisite (not just R2 as previously implied) — Phase A bench validation alone doesn't strictly need specialist, but Council attestation of Decision 2 safety matrix does
- Manufacturing partner DID registration adds a new external party class — kuni-umi class-A sterile (yakushi sibling reuse for production) is the proposed candidate, but production tooling for 4mm flexible endoscope is non-trivial (precision optics + medical-grade silicone tip molding); R1 ADR will assess in-house vs partner
- Phase B (cadaveric tissue) requires cadaver source — institutional partner with informed consent (家族同意 in JP) needed; this is a new external dependency for religious-corp not previously navigated
- 0.5 N hardware cutoff requires custom motor torque limiter — off-the-shelf 6-DOF arms (UR, Kinova) typically have 10-25 N safety thresholds; modification or custom drive needed
- Image classifier training data accumulation is slow — first 100 patients (R2 pilot) only produces ~100 supervised endoscopy images; baseline classifier comes from public dataset + transfer learning; classifier accuracy at R2 will be modest (estimated 70-75% subtype agreement vs ENT specialist gold standard); R3 cohort improves to projected 85-90%

**Risks**:
- **0.5 N cutoff false positives** during normal navigation (resistance at turbinate edge can transiently spike) — mitigated by 100 ms reaction window + smooth force ramp + operator training; bench Phase A validates false positive rate < 5%
- **PMDA 製造販売届出 path may not extend to community-center use** — fallback is full 製造販売業許可 + 製造業許可 path which adds 12-18 months; Council legal advisor (R2 prerequisite) confirms path before R1 fabrication starts
- **gemma4:e4b vision distill medical variant** does not yet exist (gemma-coder-distill is text-only at present per ADR-2605250400); R1 ADR must include classifier training plan + dataset acquisition (consent-only + Council-attested per G9); without classifier, Hanami is camera-only and operator/specialist do all classification — workable but slower
- **Cross-corp manufacturing** opens supply chain risk surface — counterfeit Hanami units with reduced safety margin could enter community centers under Charter-Rider-claimed branding; mitigation = lot-tagged manufacturing attestation per unit + community-center receiving attestation per `silenMitateReview` scope

## Alternatives Considered

### A. License a commercial flexible nasopharyngoscope + integrate Murakumo gateway only

Considered (e.g. Karl Storz / Olympus / Pentax flexible nasopharyngoscope as scope hardware; religious-corp builds only the 6-DOF arm + classifier + workflow). Rejected because:
- Commercial scope vendors typically require their proprietary image processing software path (vendor lock-in) — incompatible with G12 Murakumo-only
- Vendor scopes lack 0.5 N hardware force cutoff (rely on 10-25 N as typical, expecting operator skill); modification to 0.5 N likely voids vendor warranty + regulatory clearance
- §2(e) anti-gatekeeping mission is to **manufacture-aware**, not just classifier-aware — religious-corp making its own medical device hardware extends the constitutional counter-action

### B. Single-use disposable scope (no autoclave)

Considered. Eliminates cross-contamination risk entirely + simpler manufacturing. Rejected because:
- Single-use 4mm flexible endoscope unit cost is >$200 commercially; community-center economics make this unsustainable for routine examination
- Environmental burden — Charter Rider §2(f) multi-generational consideration weighs against disposable medical device for routine use
- R3 high-volume deploy (estimated 5000 examinations/year per community-center) would generate ~ton/year of single-use scope waste

Single-use tip cover (Decision 1) is the compromise — disposable patient-contact surface + reusable scope body.

### C. Rigid scope instead of flexible

Rejected. Rigid endoscope cannot navigate beyond anterior 1/3 of nasal cavity — would miss middle meatus visualization (chronic sinusitis subtype critical). Patient comfort during awake examination also worse.

### D. Defer Hanami to R3 — R2 uses operator + handheld flexible scope without robot arm

Considered as fallback if R1 prototype fabrication runs into delays. Reasonable interim but rejected as **default** because:
- Without robot arm + force cutoff, the constitutional safety claim weakens (force ceiling depends on operator skill, not hardware)
- Inter-operator reliability (Decision 3 phase B Cohen's kappa ≥ 0.7) much harder to hit with handheld manual operation
- R2 100-patient cohort outcome data is the input to R3 multi-site decision — better R2 data quality justifies R2 robot deploy

Keep Hanami as R2 critical path; if R1 fabrication delays by > 6 months, separate Council motion to consider handheld interim under mitate R2-interim ADR.

### E. Class III medical device path (full pre-market approval)

Considered for thorough regulatory clearance. Rejected because:
- Class III path costs $1-5M USD + 2-5 years typical — incompatible with religious-corp non-profit budget at this stage
- Class IIa (EU MDR) + 製造販売届出 (PMDA) + General Wellness Device (FDA) is the right risk-proportionate framing — Hanami enables diagnosis (specialist makes final call), it does not itself diagnose
- R3 expansion can reconsider Class III if community-center scale justifies regulatory uplift

## References

- ADR-2605260100 (mitate master charter — Hanami declared as new R2+ robotics class)
- ADR-2605260145 (mitate condition 3 — chronic sinusitis subtype classification target)
- ADR-2605260160 (mitate condition 4 — septal deviation type classification target)
- ADR-2605260200 (mitate R1 — R1 exit criteria includes "Hanami mech design Council-attested in flight")
- ADR-2605201400 (kuni-umi planetary infra — robotics class ontology source: Otete / Quad / Hitogata / Mimi / Sora / Hoshi)
- ADR-2605215000 (Murakumo-only inference — G12)
- ADR-2605231525 (no-server-key invariant — G13 device firmware key custody)
- ADR-2605250400 (gemma-coder-distill — recipe adapted for endoscopy vision distill)
- ADR-2605242715 (silicon Wave 2 supply chain — Funamori introduction precedent for new robotics class via non-kuni-umi actor)
- EN ISO 17665-1 (steam sterilization), Spaulding criteria, ISO 10993-1/-5/-10 (biocompatibility)
- 21 CFR Part 880 (FDA general hospital devices), EU MDR 2017/745, 薬機法 (日本)
- WHO-UMC + CIOMS Form III (AE classification — for image classifier bias audit secondary)
