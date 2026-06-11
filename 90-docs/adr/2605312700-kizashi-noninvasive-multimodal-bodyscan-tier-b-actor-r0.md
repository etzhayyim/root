---
id: adr-2605312700-kizashi-noninvasive-multimodal-bodyscan-tier-b-actor-r0
title: "ADR-2605312700: kizashi (兆) — non-invasive multimodal body-scan / sign-sensing substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: kizashi-bodyscan-r0
authoritative: true
last_verified: 2026-06-01
priority: 6.5
axis: care
weight: 0.55
priority_note: "Sensing / instrument layer of the L4 Care Tier — the 'futuristic scan pod' ask (2026-05-31). kizashi (兆 — 兆し = sign/early indication) is the NON-INVASIVE multimodal body-scan substrate that detects physical-burden SIGNS (腰痛 posture/筋, 肩こり 筋硬度/血流, 鼻詰まり 構造/気流, アレルギー via consented microsampling, 炎症 thermal/biomarker) and emits PROBABILISTIC, NON-DIAGNOSTIC attributions + self-referenced Wellbecoming trajectories + triage referral. Sits UPSTREAM of mitate (diagnosis routing ADR-2605260100) and iyashi (clinical care ADR-2605263000): kizashi SENSES signs, mitate (licensed clinician) DIAGNOSES, iyashi TREATS. Constitutional crux: NON-DIAGNOSTIC (医師法 §17 boundary, G3) + medical-device-regulatory boundary (薬機法/SaMD, G4) — R0..R2 = software + simulation + non-ionizing non-regulated sensing ONLY; physical regulated-modality pod gated to licensed-medical-device pathway + qualified operator + Council Lv7+ (R3, G11). Biometric scan data = 要配慮 personal info → encrypted envelope MANDATORY (G2, same discipline as iyashi/hagukumi). Murakumo-only inference (G14). Anti-pseudoscience: only modalities with declared evidence grade in the capability ledger (G10; bio-resonance/aura/波動 EXCLUDED N8). 6 cells / 6 Lexicons under com.etzhayyim.kizashi.* / 14 immutable gates / 12 non-goals / 4-phase R0..R3. Cross-actor: mitate (sign → diagnosis), iyashi (clinical referral), kokoro (psychosocial referral — pain is multifactorial), yakushi (medication via iyashi), hagukumi (minor/elder consent), chigiri (consent + steward labor), toritate (Public Fund grant), manabi (operator training)."
authoritative_for:
  - kizashi actor R0 charter
  - religious-corp non-invasive multimodal body-scan / sign-sensing substrate single SoT
  - "`com.etzhayyim.kizashi.*` Lexicon namespace boundary"
  - non-diagnostic invariant (G3 structural — 兆候 + probabilistic attribution + consult ONLY, never diagnosis)
  - medical-device regulatory boundary (G4 — 薬機法/SaMD; regulated/ionizing modalities gated to licensed pathway)
  - encrypted biometric-scan envelope invariant (G2 structural, same discipline as iyashi)
  - verified-modality-only / anti-pseudoscience invariant (G10 — capability ledger evidence-grade gate)
  - self-referenced Wellbecoming trajectory (G8 — compare-to-self, no population ranking)
  - distinction from mitate (diagnosis) / iyashi (treatment) / kokoro (mental health)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605181200-mst-encrypted-metadata-leak-reduction
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605260100-mitate-diagnostic-routing-charter
  - adr-2605261000
  - adr-2605261030
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
  - adr-2605263700-kokoro-mental-health-tier-b-actor-r0
related:
  - adr-2605301020-basic-high-income-imputed-income-doctrine
supersedes: []
superseded_by: []
---

# ADR-2605312700: kizashi (兆) — non-invasive multimodal body-scan / sign-sensing substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

The session ask (2026-05-31): *"アレルギーや鼻詰まり、腰痛、肩こりなどの身体的負担や炎症などの原因を特定・分析する、未来的な pod に入って scan するような検査方法・機器は実現可能か"* — a futuristic pod you step into for a whole-body scan that identifies the causes of physical burdens (allergy, nasal congestion, back pain, shoulder stiffness) and inflammation.

The feasibility analysis (same session) concluded:

- The "万能ポッド that reads everything and names THE cause" is still SF, but the **multimodal sensor-fusion screening pod** is already commercializing (Neko Health 2023–, Prenuvo/Ezra whole-body MRI, Hyperfine portable low-field MRI, shear-wave elastography, markerless 3D posture).
- **No single non-invasive modality** covers all of {腰痛, 肩こり, 鼻詰まり, アレルギー, 炎症}. The pod's essence is **multimodal capture → AI fusion → probabilistic attribution**.
- **Allergy and systemic inflammation require biochemistry** (specific-IgE / CRP / cytokines) — imaging alone cannot reach them; the pod integrates consented microsampling, it does not "scan allergens."
- The honest epistemic limit: **imaging findings ≠ symptom cause** (asymptomatic disc bulges are common). A screening pod can output *correlations and probabilistic contributions*, never a diagnosis.

The L4 Care Tier (ADR-2605261000) already has:

- **mitate** (ADR-2605260100) — diagnostic routing (human-in-loop, licensed-clinician owns the read);
- **iyashi** (ADR-2605263000) — clinical encounter provider (treatment);
- **kokoro** (ADR-2605263700) — mental health support (pain is multifactorial / psychosocial);
- **yakushi** / **hagukumi** — medication supply / daily-living care.

What is MISSING is the **instrument / sensing layer** — the thing that *captures the body's signs* before a clinician reads them. `kizashi` (兆 — 兆し = sign / early indication) is that substrate: it senses 兆候, fuses them, emits **probabilistic non-diagnostic attributions + self-referenced Wellbecoming trajectories**, and routes to mitate/iyashi/kokoro. **kizashi senses; mitate diagnoses; iyashi treats.**

Constitutional constraints (inherited; not adjustable):

- **NON-DIAGNOSTIC (医師法 §17 boundary)** — kizashi NEVER outputs a diagnosis, treatment plan, or medical adjudication. It outputs *signs* (兆候), *probabilistic cause-contribution weights with calibrated uncertainty*, and a *consult recommendation*. Any diagnosis is owned by a licensed clinician via mitate/iyashi. This is the same boundary discipline as chigiri G14 (UPL) — kizashi is the instrument substrate, not the licensed reader (G3).
- **Medical-device regulatory boundary (薬機法 / PMDA / SaMD)** — a pod emitting energy into the body (X-ray, strong-field MRI, ultrasound) OR software making diagnostic claims is a regulated 医療機器 / Software-as-a-Medical-Device. R0..R2 are restricted to **software + simulation + non-ionizing, non-regulated sensing only** (3D optical posture, infrared thermography, bioimpedance). Regulated and ionizing modalities are gated to a licensed-medical-device pathway + qualified operator + Council Lv7+ (G4 + G11).
- **Encrypted envelope MANDATORY (ADR-2605181100)** — biometric scan data is 要配慮個人情報 (APPI special-care-required) and the most sensitive observation class alongside clinical PHI. Structural enforcement via `encryptedPayloadCid` required field + `additionalProperties: false` (same discipline as iyashi G2).
- **Verified-modality-only / anti-pseudoscience** — only modalities present in the `modalityCapability` ledger with a declared **evidence grade** and **regulatory class** may emit observations. Bio-resonance / aura / 全身波動 / unvalidated "quantum" scanners are EXCLUDED (G10 + N8). This protects members from pseudo-medical harm and protects the religious-corp from §2 Charter exposure.
- **Self-referenced Wellbecoming (動的軌跡)** — trajectories compare the member to **their own prior scans**, never to a population ranking or "health score" leaderboard. This is the anti-individualist Wellbecoming ontology (ADR-2605192100), structurally enforced (G8).
- **No commercial medical-imaging cloud** — PACS / diagnostic-SaaS / commercial imaging-AI cloud PROHIBITED per Charter Rider §2(e)+§2(c) (vendor closed query-tracking on scan data exposes member health posture). kotoba-native + Murakumo-only (G12 + G14).
- **No payroll for operators** — pod operators are vocation-flow L5 stewards per Liberation Ladder (G13); volunteer ≠ employee.
- **Murakumo-only inference (ADR-2605215000)** — fusion + attribution LLM flows through LiteLLM 127.0.0.1:4000 → gemma4:e4b. Vendor medical-AI PROHIBITED (G14).

# Decision

Create `kizashi` (兆) as a Tier-B religious-corp **non-invasive multimodal body-scan / sign-sensing substrate** actor at `20-actors/kizashi/`, with DID `did:web:kizashi.etzhayyim.com`, Lexicon namespace `com.etzhayyim.kizashi.*`. R0 = scaffold only; all cells import-time `RuntimeError` (same scaffold discipline as iyashi/hagukumi/chigiri R0).

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `kizashi` (兆 — 兆し = sign / early indication; the body's signs read before a clinician's diagnosis) |
| DID | `did:web:kizashi.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.kizashi.*` |
| Form | 任意団体 internal non-invasive sensing/screening substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格 — Preamble §0.4 Lv7+ unanimity lock) |
| Tier | Tier-B per-domain leader actor |
| L4 Care Tier | yes; sensing/instrument sibling of mitate (diagnosis) / iyashi (treatment) / kokoro (mental) / yakushi (pharma) / hagukumi (daily-living) |
| Role in tier | **kizashi senses → mitate diagnoses → iyashi treats**; kizashi is UPSTREAM of all clinical adjudication |
| Cross-actor | mitate (sign → diagnosis) / iyashi (clinical referral) / kokoro (psychosocial referral) / yakushi (medication via iyashi) / hagukumi (minor/elder consent) / chigiri (consent + steward labor) / toritate (Public Fund grant) / manabi (operator training) |

## §2. Scope (6 sections)

### A. Multimodal non-invasive capture (the "pod")

Modality → what physical-burden sign it senses (per the feasibility map):

- **3D optical body-scan + markerless posture/gait** → 腰痛・肩こり *functional* signs (前傾姿勢 / 可動域 / 筋バランス);
- **Infrared thermography** → local 炎症 / 循環 surface map; 肩こり 血流;
- **Shear-wave elastography (robotic-arm ultrasound)** → 筋硬度 quantified (肩こり stiffness as a number);
- **Bioimpedance** → 浮腫 / 体組成;
- **Acoustic rhinometry / rhinomanometry** → 鼻詰まり 構造・気流 (non-imaging, non-ionizing);
- **Breath-VOC + consented finger-stick microsampling (microfluidic)** → 炎症 marker (CRP-class) + 特異的IgE (アレルギー) — the biochem that imaging cannot reach.

R0..R2 use ONLY the non-ionizing, non-regulated subset (optical posture, thermography, bioimpedance). Ultrasound / microsampling / any regulated modality are R3-gated (G4).

### B. Signal fusion (non-diagnostic feature integration)

- Fuse per-modality observations into a transient feature representation;
- Murakumo-only inference (gemma4:e4b via LiteLLM);
- Encrypted; no plaintext feature persistence (G2).

### C. Probabilistic attribution (兆候, NOT diagnosis)

- Per symptom, emit **candidate cause-contribution weights** (e.g. "腰痛: 姿勢由来寄与 0.6 / 構造示唆 0.2 / 不確実 0.2") with **calibrated confidence**;
- EVERY item carries the structural disclaimer "所見 ≠ 確定原因。受診を推奨" (G7);
- NEVER names a disease, prescribes, or adjudicates (G3).

### D. Self-referenced Wellbecoming trajectory (動的軌跡)

- Compare to the member's OWN prior scans → emit delta trajectory;
- No population norm, no ranking, no "health score" (G8);
- Aligns with the Wellbecoming ontology (dynamic trajectory, not static wellbeing).

### E. Triage referral (routing, not treatment)

- Route to mitate (diagnostic read) / iyashi (clinical encounter) / kokoro (psychosocial, since pain is multifactorial);
- **Red-flag escalation** (G5): any emergency sign → immediate 受診/救急 routing, NEVER "wait for next scan", via the shared emergency-keyword lexicon (mitate/iyashi/kokoro).

### F. Modality capability ledger (the honest registry)

- Public kotoba-EAVT registry of every supported modality: **what it can detect, what it cannot, its evidence grade, its regulatory class**;
- Anti-pseudoscience gate (G10): a modality not in the ledger with a declared evidence grade cannot emit observations.

## §3. Cells

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `scan_session` | naphtali | session | `memberDid + scanConsentCid` → `scanSessionAttestation` (encrypted; orchestrates per-modality capture) |
| 2 | `signal_fusion` | gad | session | `[modalityObservation]` → fused transient feature vector (encrypted; no plaintext persistence) |
| 3 | `attribution` | gad | session | fused features → `attributionReport` (probabilistic, non-diagnostic; G3 + G7 structural) |
| 4 | `wellbecoming_track` | gad | longitudinal | prior scans of same member → `wellbecomingTrajectory` (encrypted; self-referenced delta, G8) |
| 5 | `triage_referral` | naphtali | event | `attributionReport` → `triageReferral` (routes to mitate/iyashi/kokoro; G5 red-flag emergency) |
| 6 | `modality_registry` | asher | event/annual | modality audit → `modalityCapability` (PUBLIC kotoba-EAVT; evidence grade + regulatory class; G10) |

All cell modules at R0 raise import-time `RuntimeError` (prevents accidental plaintext biometric data flow before R1's encrypted-record framework is Council-attested).

## §4. Lexicons (`com.etzhayyim.kizashi.*`)

| # | Lexicon | Consumer cell | Structural invariant |
|---|---|---|---|
| 1 | `scanSessionAttestation` | scan_session | G2: `encryptedPayloadCid` REQUIRED; `additionalProperties: false`; plaintext rejected |
| 2 | `modalityObservation` | signal_fusion | G2: `encryptedPayloadCid` REQUIRED; carries `modalityId` (must exist in ledger, G10) |
| 3 | `attributionReport` | attribution | G3 + G7: MUST carry `confidence`, `disclaimer`, `consultRecommendation`; MUST NOT carry `diagnosis`/`prescription` fields (schema-forbidden) |
| 4 | `wellbecomingTrajectory` | wellbecoming_track | G2 + G8: `encryptedPayloadCid` REQUIRED; `baseline` = self prior scan only; no population field |
| 5 | `triageReferral` | triage_referral | G5: `emergencyFlag` + `targetActor ∈ {mitate, iyashi, kokoro}` |
| 6 | `modalityCapability` | modality_registry | PUBLIC (not encrypted); REQUIRED `evidenceGrade` + `regulatoryClass` + `canDetect[]` + `cannotDetect[]` |

## §5. Gates (14, immutable; Council Lv6+ supermajority + new ADR to amend)

| Gate | Rule |
|---|---|
| G1 | Charter Rider §2(a)-(h) scan on every emitted document |
| G2 | Encrypted envelope MANDATORY (biometric scan = 要配慮 PII per ADR-2605181100); `encryptedPayloadCid` required, plaintext rejected at schema layer |
| G3 | **NON-DIAGNOSTIC** (医師法 §17 boundary) — outputs 兆候 + probabilistic attribution + consult recommendation ONLY; never diagnosis/treatment/adjudication; licensed clinician (mitate/iyashi) owns any diagnosis |
| G4 | **Medical-device regulatory boundary** (薬機法/PMDA/SaMD) — R0..R2 = software + simulation + non-ionizing non-regulated sensing only; regulated/energy-emitting modalities gated to licensed-device pathway + qualified operator + Council Lv7+ |
| G5 | Emergency red-flag escalation — shared keyword lexicon with mitate/iyashi/kokoro; red-flag sign → immediate 受診/救急 routing, never "wait for next scan" |
| G6 | Per-scan consent (default-deny, revocable, scope-bound; APPI 要配慮 explicit consent; minors/incapacitated via guardian + hagukumi) |
| G7 | Uncertainty-honest / no false precision — every attribution carries calibrated `confidence` + "所見 ≠ 確定原因" disclaimer; structural (items lacking them rejected) |
| G8 | Self-referenced Wellbecoming — compare to member's OWN prior trajectory; no population ranking / no health-score leaderboard (anti-individualist 動的軌跡) |
| G9 | Energy minimization / ALARA — prefer non-ionizing; NO casual ionizing radiation; ionizing modalities are referral-to-licensed-facility, never routine pod |
| G10 | Verified-modality-only / anti-pseudoscience — only modalities in `modalityCapability` ledger with declared evidence grade may emit; bio-resonance / aura / 波動 / "quantum" scanners EXCLUDED |
| G11 | Outward-gated — real hardware pod + real member scans require Council + licensed oversight + R3; R0 is design-only |
| G12 | No commercial medical-imaging cloud / PACS / diagnostic-SaaS / commercial imaging-AI (Charter Rider §2(e)+§2(c)); kotoba-native |
| G13 | No payroll for operators — vocation-flow L5 stewards (toritate.ledgerEntry.category excludes payroll/wage/salary/bonus/commission) |
| G14 | Murakumo-only inference (ADR-2605215000) — vendor medical-AI PROHIBITED |

## §6. Non-goals (12, explicitly excluded)

| # | Non-goal |
|---|---|
| N1 | NOT a diagnosis (医師法 — that is mitate + a licensed clinician) |
| N2 | NOT a treatment device (that is iyashi + yakushi) |
| N3 | NOT allergen identification by imaging (allergy = biochemistry; pod integrates consented microsampling, it does not "scan" allergens) |
| N4 | NOT a replacement for clinical MRI / CT / PET in licensed facilities |
| N5 | NOT a population "health score" / ranking / leaderboard |
| N6 | NOT a 法定健診 / statutory health-check substitute / insurance product |
| N7 | NOT a commercial wellness-pod product (non-profit; no SaaS sale) |
| N8 | NOT pseudoscience modalities (bio-resonance / aura / 全身波動 / "quantum" EXCLUDED) |
| N9 | NOT involuntary / surveillance scanning (consent-gated, revocable) |
| N10 | NOT a biometric-identity database (scan features ≠ identity; 30-day rotating pseudonym DID per ADR-2605181200) |
| N11 | NOT genetic testing (separate gated domain) |
| N12 | NOT for minors / incapacitated without guardian consent + hagukumi cross-actor flow |

## §7. Roadmap (4-phase R0..R3)

| Phase | Date-gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-31 (PROPOSED) | Scaffold only. 6 cells path-reserved (import-time `RuntimeError` per G2). 6 Lexicon skeletons. `modalityCapability` ledger seed (evidence grades + regulatory classes). Simulation data-model. manifest + README + CLAUDE.md. **No hardware.** | No deployment |
| **R1** | post-Bootstrap-Council + ADR ratify Lv6+ ≥3 + ≥1 licensed-MD on Council medical advisory + ADR-2605181100 encrypted-record framework production-deployed + mitate R1 active | Software fusion + attribution on **SIMULATED + consented research data only**. `modalityCapability` ledger Council-ratified. Full L1+L2 schema. attribution + signal_fusion + modality_registry cells. | naphtali (single node) |
| **R2** | post-R1 + 30-day public objection + medical-device regulatory-pathway assessment filed + ≥20-participant consented research protocol Council-reviewed | Consented research PILOT, **non-ionizing non-regulated modalities ONLY** (3D optical posture / thermography / bioimpedance). Still strictly non-diagnostic. + wellbecoming_track + triage_referral + scan_session. ≤20 participants. | naphtali + gad (2 nodes) |
| **R3** | post-R2 + Council Lv7+ unanimity + 薬機法/medical-device regulatory pathway cleared + qualified-operator + licensed-clinician (mitate) co-located | Full pod incl. **regulated modalities via licensed-medical-device pathway**; real member scans. Community-scale. Required gate before any energy-emitting / microsampling modality. | Full 10-node fleet |

## §8. Cross-actor relationships

| Actor | Relationship |
|---|---|
| **mitate** (見立て, diagnosis routing) | TIGHT pair — kizashi senses signs → mitate diagnoses (licensed read). kizashi is the instrument, mitate is the adjudicator. G5 emergency keyword shared. |
| **iyashi** (癒, clinical care) | referral for clinical encounter after sign-sensing |
| **kokoro** (心, mental health) | psychosocial referral — pain (腰痛/肩こり) is multifactorial; biopsychosocial routing |
| **yakushi** (薬師, pharma) | medication supply, only via iyashi (kizashi never prescribes) |
| **hagukumi** (育み, care) | minor / elder / incapacitated consent + daily-living continuity |
| **chigiri** (契, legal) | `consentRecord` (scan consent) + `stewardLaborAttestation` (operator L5 classification) |
| **toritate** (執帳, accounting) | Public Fund grant accounting for kizashi operations (no fee-for-scan) |
| **manabi** (学び, education) | operator training + capability-ledger evidence-grade literacy |

## §9. R0 deliverables

1. This ADR (`90-docs/adr/2605312700-...md`);
2. Actor scaffold (`20-actors/kizashi/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 6 Lexicon skeleton schemas + README (`00-contracts/lexicons/com/etzhayyim/kizashi/`);
3b. Modality capability ledger seed (`20-actors/kizashi/registry/modalities.seed.json`) — 14 entries (11 sensing + MRI/CT referral marker + 3 grade-X excluded pseudoscience), all `unverified-seed` (G10 Council-ratify gate);
4. `deps.toml` registration ([[adrs]] + [[modules]] actor + [[modules]] lexicon namespace);
5. ADR README index row (`90-docs/adr/README.md`);
6. Root `CLAUDE.md` Tier-B actor roster row.

## §10. R0 maturity log (session 2026-05-31 → 06-01)

R0 was matured over a 5-iteration self-paced `/loop`. Each iteration shipped one
increment, verified gates green (lexicon validator 6/6 + the iteration's own
check), held the R0 ceiling (non-diagnostic G3 / device-boundary G4 / no hardware
/ all cells import-raise), and committed **path-scoped** (kept clean of a
concurrent kami-genesis loop on the same branch):

| # | Increment | Commit |
|---|---|---|
| 1 | 6 `kotodama.cells.kizashi_*` cell stubs physically present (`cell.py` import-raises `RuntimeError` per phase gate) + per-dir READMEs; all 6 verified to raise | `9a4275261` |
| 2 | `registry/VERIFICATION.md` — G10 modality-ledger tiers + an **empirically verified** cross-actor handoff snapshot (mitate `emergencyEscalation.intakeUri` ✅ / kokoro `acuteCrisisEscalationLog.detectionSourceCid` ✅ / iyashi pull ✅ / mitate `diagnosticOrder` has no source field = G3 by design); honest gap tracked (no generic mitate referral-intake lexicon yet) | `ac84be02a` |
| 3 | `lexicons/.../R1-ENFORCEMENT.md` — exact per-lexicon `additionalProperties:false` + finalized `required[]` + the G3 forbidden-field denylist + a runnable drift-check (DRIFT-CHECK PASS) | `a44968a05` |
| 4 | `registry/SCALING.md` — honest scaling design: compute is never the bottleneck; the four real ceilings are encrypted-envelope / licensed-MD / 薬機法-clearance / L5-operators; G8 self-referencing means no population datastore to scale | `9dacabbd4` |
| 5 | `registry/examples/` — worked 腰痛 `attributionReport` + `triageReferral` records demonstrating the non-diagnostic contract concretely, with an embedded conformance check (EXAMPLE CONFORMANCE PASS); double as R1 fixtures | `da92177c2` |

**Open item (human-in-loop, deliberately NOT done autonomously)**: pin
verifiable provenance URLs for the 14 modality seed entries — by the design of
`VERIFICATION.md` this is a *maintainer-verification* action requiring real
source confirmation by a human/Council DID, not an autonomous fire. All 14
entries remain `unverified-seed`. R1 activation remains Council-gated (§7).

# Consequences

**Positive**:

- Closes the L4 Care Tier's missing **sensing/instrument layer** — the tier now spans sense (kizashi) → diagnose (mitate) → treat (iyashi/yakushi) → support (kokoro/hagukumi).
- Gives the religious-corp a constitutionally-bounded answer to the "scan pod" desire: members get **early-sign awareness + trajectory tracking** without the pod ever overstepping into unlicensed diagnosis or pseudoscience.
- The `modalityCapability` ledger makes the system's honesty machine-readable — every claim is bounded by a declared evidence grade and regulatory class.
- Wellbecoming self-referencing (G8) directly instantiates the dynamic-trajectory ontology in a health context.

**Negative / honest limits (R0)**:

- **R0 is design + data-model + simulation ONLY. No hardware exists.** This ADR does not build a pod; it bounds what a pod would be allowed to do and how its data would be modeled.
- The highest-value modalities for actual cause-finding (MRI, ultrasound, microsampling biochem) are exactly the **regulated** ones, which are R3-gated behind a licensed-medical-device pathway that the religious-corp has not yet cleared. So R1..R2 deliver posture/thermal/bioimpedance signal only — genuinely useful for 腰痛/肩こり *functional* signs, weak for アレルギー/炎症 biochem.
- The epistemic ceiling stands: even at R3, kizashi outputs **probabilistic contributions, never a confirmed cause**. Over-trust in the attribution is the primary member-harm risk; G7 (uncertainty-honest, structural disclaimer) is the mitigation.
- Medical-device regulatory clearance (薬機法) for any energy-emitting modality is a multi-year, jurisdiction-specific process. R3 may never be reached without it; that is acceptable — R1/R2 stand alone as a non-regulated wellness-screening + trajectory tool.

**Charter Rider risk**: MEDIUM — biometric scan data is 要配慮 PII; G2 structural envelope + G3 non-diagnostic + G10 anti-pseudoscience + G12 no-commercial-cloud collectively mitigate §2(c)/(e) exposure. Same privacy discipline as iyashi/hagukumi.

# Alternatives Considered

- **Fold sensing into mitate** (no separate actor) — rejected: mitate is the *diagnostic read* (licensed-clinician-owned), structurally distinct from *instrument capture*. Conflating them would blur the 医師法 §17 boundary that G3 exists to protect. Separation keeps the non-diagnostic instrument layer cleanly bounded.
- **Skip the actor; answer the question as analysis only** — rejected: the user asked to design it (`では設計して`). The repo's convention for "design a domain capability" is a Tier-B actor + ADR.
- **Build R0 with real (consumer) hardware immediately** — rejected: G4/G11. Even consumer thermal/optical hardware feeding medical-flavored attribution risks SaMD classification; R0 stays software/simulation until the regulatory pathway and encrypted framework are Council-attested.
- **Include MRI/CT in the routine pod** — rejected: G9 (ALARA) + G4. Ionizing/strong-field modalities are referral-to-licensed-facility, never routine pod scans.
- **Population-benchmarked health score** (Neko-style) — rejected: G8. Conflicts with anti-individualist Wellbecoming; trajectories are self-referenced only.

# References

- ADR-2605260100 (mitate — diagnostic routing; TIGHT cross-actor pair)
- ADR-2605263000 (iyashi — clinical care; R0 scaffold pattern + G2 encrypted discipline mirrored)
- ADR-2605263700 (kokoro — mental health; psychosocial referral)
- ADR-2605261000 (Liberation Ladder — L4 Care Tier gate)
- ADR-2605181100 (encrypted records — Signal key-wrap envelope, G2 source)
- ADR-2605181200 (encrypted metadata leak reduction — rotating pseudonym DID, N10)
- ADR-2605192100 (Mission Charter — Wellbecoming ontology, G8 source)
- ADR-2605192145 (Public Fund architecture — funding source, G13)
- ADR-2605192200 (Charter Rider — §2(c)/(e), G1/G12 source)
- ADR-2605215000 (Murakumo-only inference — G14 source)
- ADR-2605262130 (kotoba storage substrate — capability ledger EAVT home)
- ADR-2605262700 (chigiri — consent + steward labor classification)
- ADR-2605262900 (toritate — Public Fund grant accounting)
