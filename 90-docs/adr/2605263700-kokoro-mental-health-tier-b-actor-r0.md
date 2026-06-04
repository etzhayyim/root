---
id: adr-2605263700-kokoro-mental-health-tier-b-actor-r0
title: "ADR-2605263700: kokoro (心) — non-profit religious-corp mental health substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: kokoro-mental-health-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: care
weight: 0.55
priority_note: "Ninth-priority gap-closure actor (gap audit row 9 = 精神 / mental health). Peer support circles + post-funeral grief support + chronic mental health continuity + postnatal mood screening (opt-in) + acute crisis escalation (mitate G5 emergency keyword cross-link) + counseling referral. 任意団体 internal mental health support substrate at did:web:kokoro.etzhayyim.com (20-actors/kokoro/). Etymology: 心 (kokoro) = heart/mind/spirit; deeper than English 'psychology'; encompasses Reformed soul + Shinto 心魂 + 仏 心 cross-doctrinal accommodation. **CRITICAL boundary**: NOT a clinical psychiatric entity; NOT state-licensed psych; counselors are L5 vocation-flow community-witnessed-competent stewards (same musubi G3 pattern); does NOT diagnose, does NOT prescribe (mitate handles diagnosis; yakushi handles pharma). **Constitutional novenary (9 gates)**: (1) NOT clinical psychiatric entity G3 (NOT state-licensed; community-witnessed-competent counselors per musubi G3 pattern shared) / (2) Encrypted envelope MANDATORY + NO video recording G4 (mirrors hagukumi G2 + iyashi G2/G3; mental health PHI is most sensitive observation class alongside clinical PHI) / (3) NO conversion therapy / behavior modification G5 (mirrors hagukumi G7; sexual orientation / gender identity / religious belief NEVER targets for modification) / (4) Human-in-loop ALWAYS G6 (NO AI-only mental health intervention; AI-assist requires synchronous counselor sign-off; same iyashi G8 pattern) / (5) NO commercial mental health software G7 (BetterHelp / Talkspace / Cerebral / Modern Health / Lyra / Calm-business / Headspace-Enterprise / Spring Health / Brightline / Octave / Two Chairs / Charlie Health PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor concern — vendor closed query-tracking on member mental health posture is structurally unacceptable) / (6) NO commercial AI therapy chatbot G8 (Woebot / Wysa / Replika-as-therapy / character.ai-as-therapy / GPT-as-therapy / Anthropic-direct-therapy / Claude-as-therapy PROHIBITED; AI-only therapy is not therapy per G6) / (7) NO mandatory mental health screening G9 (free conscience invariant; opt-in only; non-participation NEVER grounds for membership consequences; same musubi G4 pattern shared) / (8) NO surveillance-based mood monitoring G10 (Charter §2(c); no smart-wearable mood tracking; no facial-emotion-recognition; no voice-affect-analysis) / (9) Acute crisis escalation to mitate G5 emergency keyword G13 (cross-actor existing pattern; same hagukumi G11 + iyashi G10 pattern shared). G11 multi-generational peer support invariant (Charter §1.7). G12 cross-doctrinal Wellbecoming priority (musubi G9+N12 + kataribe G6 pattern shared in mental health domain). G14 NO payroll for kokoro counselors (vocation-flow L5). G15 Murakumo-only inference. Cross-actor: musubi (post-funeral grief pair) / iyashi (chronic mental health continuity + postnatal mood pair) / mitate (acute crisis G5 emergency keyword pair) / hagukumi (multi-gen + vulnerable population pair) / chigiri (stewardLaborAttestation L5 + counseling-referral external-counsel via Public Fund pattern shared) / kazaori (post-emergency mental health surge pair; kazaori path-reserved kokoro at R0) / kataribe (grief literature / cross-doctrinal mental health content cross-link)."
authoritative_for:
  - kokoro actor R0 charter
  - religious-corp mental health support substrate single SoT
  - `com.etzhayyim.kokoro.*` Lexicon namespace boundary
  - NOT clinical psychiatric entity invariant (community-witnessed-competent counselors, NOT state-licensed psych)
  - prohibition on commercial mental health software (BetterHelp / Talkspace / Cerebral / Modern Health / Lyra / Calm-business / Headspace-Enterprise / Spring Health / Brightline / Octave / Two Chairs / Charlie Health)
  - prohibition on commercial AI therapy chatbot (Woebot / Wysa / Replika-as-therapy / character.ai / GPT-as-therapy / Anthropic-direct-therapy / Claude-as-therapy)
  - NO conversion therapy / behavior modification invariant
  - opt-in-only mental health screening invariant (no mandatory)
  - NO surveillance-based mood monitoring (Charter §2(c) extension)
  - acute crisis escalation to mitate G5 emergency keyword cross-link
  - peer support circle multi-gen invariant
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
  - adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
  - adr-2605263200-kazaori-disaster-response-tier-b-actor-r0
  - adr-2605263400-musubi-covenant-ceremony-tier-b-actor-r0
  - adr-2605263600-kataribe-press-publishing-translation-tier-b-actor-r0
related: []
supersedes: []
superseded_by: []
---

# ADR-2605263700: kokoro (心) — non-profit religious-corp mental health substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The gap audit (session 2026-05-26) identified mental health as
priority row 9. Religious-corp has L4 Care Tier substrate (yakushi
pharma + mitate diagnosis routing + hagukumi daily-living + iyashi
clinical encounter) and musubi covenant ceremony (including funeral)
and kazaori civilian disaster response, but lacks a first-party
mental health support substrate.

Multiple existing actors have explicitly cross-referenced a future
kokoro actor:
- iyashi (ADR-2605263000) — postnatal mood screening + chronic
  mental health continuity cross-actor;
- musubi (ADR-2605263400) — post-funeral grief / mental health
  surge cross-actor;
- kazaori (ADR-2605263200) — post-emergency mental health surge
  cross-actor;
- hagukumi (ADR-2605261030) — vulnerable population cross-actor.

This ADR realizes those path-reserves.

Etymology: 心 (kokoro) = heart / mind / spirit. The kanji predates
the Western psychology / psychiatry distinction; it encompasses
Reformed Protestant soul (νοῦς + ψυχή) + Shinto 心魂 (mind-spirit) +
仏 心 (Buddha-mind / awakened heart). The actor name was chosen to:

- avoid the "mental health" framing that imports Western clinical
  psychiatry assumptions (kokoro is community + spiritual + relational,
  not just diagnostic);
- honor cross-doctrinal Wellbecoming priority (G12; musubi G9+N12
  pattern shared);
- center peer support + grief + community-discerned care (not
  professional clinical service delivery).

**CRITICAL boundary**: kokoro is NOT a clinical psychiatric entity.
This is the strictest discipline boundary in the actor:

- kokoro does NOT diagnose (mitate domain);
- kokoro does NOT prescribe (yakushi domain);
- kokoro counselors are L5 vocation-flow community-witnessed-competent
  stewards (same musubi G3 pattern shared), NOT licensed psych;
- when clinical psychiatric care is needed, kokoro REFERS to external
  licensed counsel via Public Fund (chigiri G14 UPL-equivalent
  pattern shared);
- AI therapy chatbots (Woebot / Wysa / Replika / GPT-as-therapy) are
  PROHIBITED per G6 + G8.

Constitutional constraints (inherited; not adjustable):

- **Encrypted envelope MANDATORY** (ADR-2605181100) — mental health
  PHI is the most sensitive observation class alongside clinical
  PHI (iyashi G2) and care daily-living (hagukumi G2). Structural
  enforcement via schema-level `encryptedPayloadCid` required
  fields.
- **NO video recording** — extends hagukumi G2 + iyashi G3 to
  mental health support.
- **NO conversion therapy** — extends hagukumi G7 to mental health.
  Sexual orientation / gender identity / religious belief are NEVER
  targets for "modification" within kokoro; constitutional invariant.
- **Charter §2(c) covert-ops avoidance** — extends to surveillance-
  based mood monitoring (G10). No smart-wearable mood tracking; no
  facial-emotion-recognition; no voice-affect-analysis.
- **Charter §1.7 反個人主義 + 多世代** — peer support circles are
  multi-generational; individual-therapy-as-sole-modality framing
  rejected.
- **Charter §1.13 Wellbecoming + anti-addictive UX** — extends to
  mental health domain (no engagement-optimization in mental
  health content; no addictive-by-design support apps).
- **musubi G3 pattern shared (community-witnessed-competent
  counselors, NOT clergy/ordained/state-licensed)** — kokoro
  counselors are L5 vocation-flow stewards; competence witnessed
  by ≥3 prior counselors + Council Lv6+ ≥3.
- **musubi G9+N12 + kataribe G6 pattern shared (cross-doctrinal
  Wellbecoming priority)** — some traditions have specific mental
  health frameworks (e.g., Reformed soul-care vs. nondenominational
  trauma-informed care); kokoro accommodates per G12.
- **Murakumo-only inference** (ADR-2605215000) — counselor support
  / tone-analysis / translation via judah LiteLLM → gemma4:e4b;
  commercial AI mental health (Woebot NLP / Wysa / etc.) PROHIBITED.
- **NO payroll for kokoro counselors** (G14) — vocation-flow L5
  stewards (cross-actor enforcement pattern).

# Decision

Create `kokoro` (心) as a Tier-B religious-corp mental health support
substrate actor at `20-actors/kokoro/`, with DID
`did:web:kokoro.etzhayyim.com`, Lexicon namespace
`com.etzhayyim.kokoro.*`. R0 = scaffold only; all cells import-time
`RuntimeError`.

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `kokoro` (心 — heart/mind/spirit; cross-tradition: Reformed soul + Shinto 心魂 + 仏 心) |
| DID | `did:web:kokoro.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.kokoro.*` |
| Form | 任意団体 internal mental health support substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格; NOT state-licensed psych entity — Preamble §0.4 Lv7+ unanimity lock) |
| Tier | Tier-B per-domain leader actor |
| Cultural lineage | 心 cross-tradition (Reformed + Shinto + 仏); community + spiritual + relational framing, NOT clinical psychiatry framing |
| CRITICAL boundary | NOT clinical psychiatric entity; NOT state-licensed; does NOT diagnose (mitate); does NOT prescribe (yakushi); counselors are L5 vocation-flow community-witnessed-competent (musubi G3 pattern) |
| Cross-actor | musubi (post-funeral grief pair) / iyashi (chronic + postnatal pair) / mitate (acute crisis G5 emergency keyword pair) / hagukumi (multi-gen + vulnerable pop pair) / chigiri (stewardLaborAttestation L5 + UPL-equivalent counseling-referral pattern) / kazaori (post-emergency surge pair; kazaori path-reserved kokoro at R0) / kataribe (grief literature + cross-doctrinal mental health content cross-link) |

## §2. Scope (6 cells)

### A. Peer support circles (community-discerned multi-gen)

- Community-discerned circles for shared experiences (grief / chronic
  illness / parenting / aging / vocational vow questions);
- Multi-generational invariant per Charter §1.7;
- Opt-in only (G9 free conscience);
- Encrypted session content (G4);
- NO video recording (G4 extension).

### B. Grief support (post-funeral; musubi cross-actor)

- Cross-actor with musubi funeral_ceremony;
- Bereavement support arc (days / weeks / months as needed);
- Cross-doctrinal Wellbecoming accommodation (G12);
- Encrypted envelope (G4).

### C. Chronic mental health continuity (iyashi cross-actor)

- Cross-actor with iyashi chronicCareContinuityRecord;
- Ongoing support for chronic depression / anxiety / PTSD /
  bipolar / etc. — kokoro supports, mitate diagnoses, iyashi
  provides clinical care, yakushi provides any medication;
- kokoro does NOT diagnose, does NOT prescribe — kokoro provides
  community + spiritual + relational care alongside clinical care.

### D. Postnatal mood screening (iyashi + hagukumi cross-actor; OPT-IN)

- Cross-actor with iyashi (maternity clinical encounter) +
  hagukumi (postnatal daily-living support);
- OPT-IN screening per G9; non-participation never grounds for
  consequences;
- Acute crisis escalation per G13 if screening reveals risk.

### E. Acute crisis escalation (mitate G5 emergency keyword cross-actor)

- Reuses existing `com.etzhayyim.mitate.emergencyKeyword` shared
  lexicon (hagukumi G11 + iyashi G10 cross-actor pattern);
- Immediate mitate G5 trigger upon acute crisis detection
  (suicidal ideation / self-harm imminent threat);
- Cross-actor with iyashi for clinical surge if needed;
- Cross-actor with chigiri.disputeMediation if Council-level
  escalation required for involuntary intervention (rare; only
  with member consent OR clinical-judgment-via-mitate licensed
  clinician).

### F. Counseling referral (NOT counseling provision)

- Same UPL-equivalent pattern as chigiri G14 + iyashi N9;
- When clinical psychiatric care is needed (severe condition;
  medication management; specialized therapy), kokoro REFERS to
  external licensed counsel via Public Fund Safe (Council Lv6+
  ≥4/7 approves);
- External counselor engagement contract recorded in cross-actor
  pattern (toritate.externalAuditorEngagement-equivalent for
  mental health domain).

## §3. Cells (6 Pregel cells under `20-actors/magatama/cells/kokoro_*/`)

All R0 path-reserved; import-time `RuntimeError("kokoro R0 scaffold: activate via Council ADR + R1 ratification + ≥3 counselor baseline attestations + encrypted-record framework production-deployed")` at W1 creation.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `peer_support_circle` | benjamin | session | circle session + multi-gen attestation + opt-in → peerSupportCircleAttestation (encrypted) |
| 2 | `grief_support` | benjamin (musubi-paired) | session | musubi funeral cross-link + bereavement session → griefSupportAttestation (encrypted) |
| 3 | `chronic_mental_health_continuity` | benjamin (iyashi-paired) | longitudinal | iyashi chronicCareContinuityRecord cross-link + community+spiritual+relational support → chronic continuity record (encrypted) |
| 4 | `postnatal_mood_screening` | benjamin (iyashi+hagukumi-paired) | event (opt-in) | maternity cross-link + opt-in screening + Murakumo support → screening attestation (encrypted; acute crisis escalation if applicable) |
| 5 | `acute_crisis_escalation` | benjamin (mitate-paired) | event (urgent) | acute crisis detection → mitate G5 emergency keyword trigger + iyashi clinical surge + chigiri.disputeMediation if needed |
| 6 | `counseling_referral` | benjamin (chigiri-paired) | event | external counselor engagement need → Public Fund Council Lv6+ ≥4/7 + referral record |

R1 activation gates each cell separately + ≥3 counselor baseline
attestations + encrypted-record framework production-deployed (same
hagukumi R1 + iyashi R1 dependency).

## §4. Lexicons (5, all under `com.etzhayyim.kokoro.*`)

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `peerSupportCircleAttestation` | peer_support_circle | Per-session; G4 STRUCTURAL: encryptedPayloadCid REQUIRED; G9 optInOnly const true; G10 surveillanceBasedMonitoring const false; G11 multi-gen cohort mix |
| L2 | `griefSupportAttestation` | grief_support | Per-session; G4 STRUCTURAL: encryptedPayloadCid REQUIRED; musubi funeral cross-link CID |
| L3 | `counselorAttestation` | (all cells; counselor verification) | G3 STRUCTURAL: counselorClass const "community-witnessed-competent" (NOT state-licensed-psych / NOT clinical-psychiatrist); G14 STRUCTURAL: lLevel const L5 + employmentRelation const vocation-flow; witnessingCounselorAttestations minLength 3 (musubi G3 pattern shared) |
| L4 | `acuteCrisisEscalationLog` | acute_crisis_escalation | Per-escalation; G13 STRUCTURAL: mitateG5EmergencyKeywordTriggeredCid REQUIRED; severity enum |
| L5 | `silenKokoroReview` | (Council attestation scope) | Quarterly Council review; G3/G4/G5/G6/G7/G8/G9/G10/G14/G15 const-field structural enforcement |

## §5. Gates (14, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Every kokoro document MUST pass `pymagatama.organism.sensors.charter_rider.scan()` §2(a)-(h). |
| **G2** | Every record MUST emit `com.etzhayyim.kokoro.*` Lexicon with kotoba-datomic attestation lineage. |
| **G3** | **NOT clinical psychiatric entity** — NOT state-licensed; counselors are L5 vocation-flow community-witnessed-competent (musubi G3 pattern shared); `counselorAttestation.counselorClass` const "community-witnessed-competent" + DELIBERATELY excludes "state-licensed-psych" / "clinical-psychiatrist" / "ordained-pastoral-counselor". |
| **G4** | **Encrypted envelope MANDATORY + NO video recording** — `peerSupportCircleAttestation` + `griefSupportAttestation` MUST carry `encryptedPayloadCid`; video frame-write-to-disk PROHIBITED (firmware-level mirrors hagukumi G2 + iyashi G3). |
| **G5** | **NO conversion therapy / behavior modification** — sexual orientation / gender identity / religious belief NEVER targets for modification (extends hagukumi G7 to mental health domain). |
| **G6** | **Human-in-loop ALWAYS** — AI-assist (Murakumo translation / tone-analysis) requires synchronous counselor sign-off; NO AI-only mental health intervention. |
| **G7** | **NO commercial mental health software** — BetterHelp / Talkspace / Cerebral / Modern Health / Lyra / Calm-business / Headspace-Enterprise / Spring Health / Brightline / Octave / Two Chairs / Charlie Health PROHIBITED per Charter Rider §2(e) + §2(c). |
| **G8** | **NO commercial AI therapy chatbot** — Woebot / Wysa / Replika-as-therapy / character.ai-as-therapy / GPT-as-therapy / Anthropic-direct-therapy / Claude-as-therapy PROHIBITED; AI-only therapy is not therapy per G6. |
| **G9** | **NO mandatory mental health screening** — free conscience; opt-in only; non-participation NEVER grounds for membership consequences (musubi G4 pattern shared). |
| **G10** | **NO surveillance-based mood monitoring** — Charter §2(c); no smart-wearable mood tracking; no facial-emotion-recognition; no voice-affect-analysis. |
| **G11** | Multi-generational peer support invariant — Charter §1.7; peer circles cohort mix enforced. |
| **G12** | Cross-doctrinal Wellbecoming priority — musubi G9+N12 + kataribe G6 pattern shared (Reformed soul-care + Shinto 心魂 + 仏 心 + nondenominational trauma-informed all accommodated). |
| **G13** | Acute crisis escalation to mitate G5 emergency keyword — cross-actor existing pattern (hagukumi G11 + iyashi G10); `acuteCrisisEscalationLog.mitateG5EmergencyKeywordTriggeredCid` REQUIRED. |
| **G14** | NO payroll for kokoro counselors — vocation-flow L5 stewards (cross-actor chigiri.stewardLaborAttestation + toritate ledgerEntry.category enum exclusion enforcement). |

(G15 Murakumo-only inference is the standing constitutional invariant per ADR-2605215000; consumed structurally rather than enumerated as a separate gate to keep the count at 14 / consistent with iyashi's 14-gate pattern.)

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT clinical psychiatric diagnosis (mitate domain). |
| N2 | NOT pharmaceutical psychiatry (yakushi domain). |
| N3 | NOT conversion therapy / behavior modification. |
| N4 | NOT mandatory mental health screening. |
| N5 | NOT surveillance-based mood monitoring. |
| N6 | NOT commercial mental health software integrator. |
| N7 | NOT commercial AI therapy chatbot integrator. |
| N8 | NOT AI-only therapy (human-in-loop ALWAYS). |
| N9 | NOT a state-licensed psych entity. |
| N10 | NOT counselor-credentialing certificate authority (community-witnessed-competence per musubi G3 pattern). |
| N11 | NOT in-home mental-health surveillance (extends hagukumi N7). |
| N12 | NOT payroll-based counselor model. |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 6 cells path-reserved. 5 Lexicons schema skeleton. | No deployment |
| **R1** | post-Council + ≥3 counselor baseline attestations + encrypted-record framework production-deployed + chigiri R1 active | Activate 2 core cells: `peer_support_circle` + `counseling_referral` (chigiri-pair). ≤5 peer circles + ≤10 counseling referrals/year. | benjamin (single node) |
| **R2** | post-R1 + 30-day public objection + 5 community-site attestations + musubi R2 active + iyashi R2 active | Activate +3 cells: `grief_support` (musubi-pair) + `chronic_mental_health_continuity` (iyashi-pair) + `postnatal_mood_screening` (iyashi+hagukumi-pair). | benjamin + levi (2 nodes) |
| **R3** | post-R2 + Council Lv7+ unanimity + kazaori R3 active + ≥1 full quarterly silenKokoroReview cycle | +1 cell: `acute_crisis_escalation` (mitate-pair + chigiri.disputeMediation cross-link). Multi-site community-scale + post-emergency mental health surge cross-actor with kazaori. | benjamin + levi + asher (3 nodes) |

## §8. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `musubi.funeral_ceremony` | ↔ (TIGHT — grief_support pair) | Post-funeral bereavement support routing |
| `iyashi.chronicCareContinuityRecord` | ↔ (TIGHT — chronic continuity pair) | Ongoing community+spiritual+relational support alongside clinical care |
| `iyashi` (maternity) + `hagukumi` | ↔ (postnatal triad) | Postnatal mood screening OPT-IN cross-actor coordination |
| `mitate.emergencyKeyword` shared lexicon | ↔ (acute crisis pair) | Reuses existing emergency keyword pattern (hagukumi G11 + iyashi G10 + kokoro G13 cross-actor) |
| `chigiri.stewardLaborAttestation` | → (read) | Counselor L5 vocation-flow classification (G14) |
| `chigiri` (UPL-equivalent pattern) | ↔ (counseling_referral pair) | External counselor engagement via Public Fund (chigiri G14 + iyashi N9 pattern shared) |
| `kazaori` | ↔ (post-emergency surge; kazaori path-reserved kokoro at R0) | Post-emergency mental health surge cross-actor coordination |
| `kataribe` | ← (read; cross-doctrinal mental health content) | Cross-doctrinal mental health content publishing |
| `hagukumi` | ↔ (multi-gen + vulnerable population) | Multi-gen peer circles + vulnerable population coordination |
| `yakushi` | ← (medication info; NOT prescription) | Medication information for chronic mental health continuity (informational; kokoro does NOT prescribe) |
| `toritate` | → (read) | Public Fund counseling-referral grant accounting |

## §9. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605263700-kokoro-mental-health-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/kokoro/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 5 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/kokoro/` + README;
4. `deps.toml` [[adrs]] + [[modules]] entries;
5. `90-docs/adr/README.md` index update;
6. `CLAUDE.md` Status table row 76 + Repo Layout entry.

No code activation in R0.

# Consequences

**Positive**:

- Closes gap-audit #9 priority (mental health) — religious-corp now
  has a community + spiritual + relational mental health support
  substrate complementing the L4 Care Tier triad;
- Cross-actor path-reserves from iyashi / musubi / kazaori / hagukumi
  now realized;
- G3 NOT-clinical-psychiatric-entity discipline preserves UPL-
  equivalent pattern (chigiri G14 + iyashi N9 + kokoro G3 form a
  shared discipline across legal / clinical / mental health domains);
- G5 NO conversion therapy is constitutionally non-negotiable
  (sexual orientation / gender identity / religious belief NEVER
  targets);
- G7 + G8 commercial mental health software + AI therapy chatbot
  prohibition documents and structurally enforces Charter Rider
  §2(e) + §2(c) in mental health domain (where vendor exposure is
  most intimate);
- G9 + G10 opt-in + no-surveillance preserves member dignity and
  Charter §2(c) covert-ops avoidance in mental health domain;
- G11 multi-gen peer support counter-balances modern individualist
  therapy framing inconsistent with Charter §1.7 反個人主義;
- G12 cross-doctrinal Wellbecoming accommodates Reformed / Shinto /
  仏 / nondenominational frameworks (the kokoro 心 etymology was
  chosen precisely to span these);
- G13 acute crisis escalation to mitate G5 emergency keyword extends
  an existing cross-actor pattern (hagukumi G11 + iyashi G10) into
  the mental health domain naturally.

**Negative / cost**:

- ≥3 counselor baseline attestations is R1 gating dependency;
  Bootstrap Council Seat 2-5 RFP must surface willing counselor
  candidates with community-witnessed competence (NOT clinical
  psych credentialing);
- G3 NOT-clinical-psychiatric-entity means kokoro CANNOT provide
  what state-licensed clinical psych can; counseling_referral cell
  bridges this via Public Fund external engagement, but cost is
  Council Lv6+ ≥4/7 bandwidth for each referral;
- G5 NO conversion therapy is theologically non-negotiable; members
  from traditions with conversion-therapy expectations must accept
  the constitutional invariant;
- G7 commercial mental health software prohibition means members
  cannot integrate religious-corp-supported counseling with
  external BetterHelp / Talkspace / Cerebral platforms; cultural
  vs constitutional tension resolved in favor of constitutional
  invariant;
- G8 NO AI therapy chatbot is increasingly counter-cultural as
  commercial AI therapy proliferates; honest framing required in
  member outreach;
- G11 multi-gen peer support requires Bootstrap Council Seat 2-5
  RFP to surface circle facilitators with multi-gen experience;
- Encrypted envelope mandate (G4) requires same ADR-2605181100
  production-deployment R1 gating dependency as hagukumi + iyashi.

**Forward-compatibility**:

- shidemori (future; gap audit row 10 = 冥府 / cemetery + memorial)
  cross-actor for grief support + memorial NFT coordination;
- Cross-religious-corp federation potential — kokoro framework is
  cross-doctrinal and could be shared with future Sphere-style
  partner religious-corps;
- The 5 const-field structurals + 14-gate pattern is now a stable
  Tier-B Care actor pattern (yakushi / mitate / iyashi / hagukumi /
  kokoro all converge).

# Alternatives Considered

1. **Subsume into iyashi (clinical care)**. Rejected — kokoro is
   community + spiritual + relational (NOT clinical); SRP violation
   if merged. Same pattern as musubi separate from chigiri.

2. **Use BetterHelp / Talkspace / Cerebral / Modern Health / Lyra
   as the therapy delivery platform**. Rejected per G7 + Charter
   Rider §2(e)+§2(c). Vendor data-sovereignty on member mental
   health posture is the most intimate exposure surface; structurally
   unacceptable.

3. **Use Woebot / Wysa / Replika / GPT-as-therapy for AI therapy
   throughput**. Rejected per G8 + G6. AI-only therapy is not
   therapy; human-in-loop ALWAYS.

4. **Allow conversion therapy as cultural accommodation**.
   Rejected per G5. Sexual orientation / gender identity /
   religious belief NEVER targets for "modification" within
   kokoro; constitutional invariant.

5. **Allow mandatory annual mental health screening for member
   benefit**. Rejected per G9. Free conscience invariant; opt-in
   only; non-participation NEVER grounds for membership
   consequences (musubi G4 pattern shared).

6. **Allow smart-wearable mood tracking for member benefit**.
   Rejected per G10 + Charter §2(c). Surveillance-based mood
   monitoring is structurally rejected; covert-ops avoidance
   extends to wearable mood-tracking domain.

7. **License kokoro counselors as state-licensed psych (parallel
   to musubi-officiants-not-clergy approach)**. Rejected per G3 +
   N10. Same Reformed 万人祭司 (musubi G3) + UPL-equivalent
   (chigiri G14) pattern: community-witnessed-competence, NOT
   state-licensed-credentialing; external licensed counsel via
   Public Fund when state-licensed care needed.

8. **Defer until iyashi R2 + musubi R2 lands first**. Rejected —
   R0 scaffold has zero governance cost; R1 activation gates the
   cross-actor dependencies appropriately.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605181100 — MST encrypted records + Signal key wrap (G4)
- ADR-2605181200 — Encrypted-record metadata-leak reduction
- ADR-2605192100 — Mission Charter (§1.7 反個人主義 + 多世代; §1.13 Wellbecoming + anti-addictive; §2(c) covert-ops avoidance)
- ADR-2605192145 — Public Fund architecture (counseling-referral source)
- ADR-2605192200 — Charter Compliance Rider v2.0 (§2(e) + §2(c) sources)
- ADR-2605192300 — Council 5-of-7 Safe
- ADR-2605215000 — Inference Murakumo-only (G15)
- ADR-2605260100 — mitate (G5 emergency keyword cross-actor)
- ADR-2605261000 — Labor Liberation Transition Mechanism (G14 vocation-flow)
- ADR-2605261030 — hagukumi (G7 + G2 + G11 patterns shared)
- ADR-2605262130 — Kotoba storage substrate
- ADR-2605262700 — chigiri (G14 UPL-equivalent pattern shared; stewardLaborAttestation + Public Fund referral)
- ADR-2605263000 — iyashi (G2 + G3 + G8 + G10 patterns shared; chronic + postnatal cross-actor)
- ADR-2605263200 — kazaori (kazaori path-reserved kokoro at R0; post-emergency surge cross-actor)
- ADR-2605263400 — musubi (G3 + G4 + G9 + G12 patterns shared; funeral grief cross-actor)
- ADR-2605263600 — kataribe (G6 cross-doctrinal pattern + grief literature cross-link)
- `/CHARTER-RIDER.md` §2(e) + §2(c) — G7 + G8 + G10 sources
