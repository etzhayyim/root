---
id: adr-2605263400-musubi-covenant-ceremony-tier-b-actor-r0
title: "ADR-2605263400: musubi (結) — non-profit religious-corp covenant ceremony substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: musubi-covenant-ceremony-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: ceremony
weight: 0.55
priority_note: "Sixth-priority gap-closure actor (gap audit row 6 = 冠婚葬祭 covenant ceremonies). Performs the ceremonies that chigiri (ADR-2605262700) attests on-chain. The chigiri.covenant_ceremony cell explicitly path-reserved musubi as its cross-actor pair at R2 activation; this ADR realizes that pair. 任意団体 internal ceremony performance substrate at did:web:musubi.etzhayyim.com (20-actors/musubi/). Etymology: 結 (musubi) = tie / knot / bind / connect; Shinto 産霊 (musubi) = generative-creative force tying threads of life — apt for ceremonies that tie families (marriage) / name new lives (naming) / honor passages (funeral) / commit vocations (vow). Scope = marriage ceremony (covenant rite; NOT state-recognized; Charter §1.12 routing-around) / naming ceremony (Adherent SBT issuance ritual; cross-actor with chigiri.member_onboarding) / funeral ceremony 葬送 (cross-actor with chigiri.inheritance + future shidemori memorial) / vocation vow (L5 vocation-flow steward commitment) / rededication ceremony (post-voluntary-withdrawal return or post-excommunication cure per chigiri G12) / seasonal communal ceremony (新年 / 祈年 / 収穫 + Wellbecoming festival cycles). **Constitutional octet**: (1) NO clergy class G3 (Reformed 万人祭司 priesthood-of-all-believers invariant per Charter §1.7; officiants are L5 vocation-flow community-witnessed-competent, NOT ordained clergy) / (2) NO mandatory ritual attendance G4 (free conscience invariant; member opt-in) / (3) Per-ceremony consent G5 (default-deny for non-applicant participation) / (4) NO commercial wedding/funeral industry software G6 (Aisle Planner / Honeybook / The Knot / WeddingWire / Zola / SRS Computing / Aldor / Wilbert / Frazer Consultants PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor concern — vendor closed query-tracking on member life-events exposes deeply personal posture) / (5) NO bride price / dowry coercive economic structure G7 (anti-coercive ceremony economy; gifts permitted but coercive transfer prohibited) / (6) NO video recording without per-party consent G8 (ceremony privacy; mirrors hagukumi G2 / iyashi G3) / (7) NO sacrament-as-transubstantiation theology G9 (Sola Scriptura + Reformed memorial view; communal practice without doctrinal monopoly) / (8) Cross-actor chigiri.covenantAttestation emit MANDATORY G11 (chigiri attests on-chain; musubi performs ceremony; non-emit = procedure invisible per chigiri G2). 6 cells / 5 Lexicons under com.etzhayyim.musubi.* / 13 immutable gates / 12 non-goals / 4-phase R0..R3. Cross-actor: chigiri (covenant_ceremony pair; attestation emit) / iyashi (post-clinical healing-rite ceremonial closure for chronic conditions) / hagukumi (children/elder ceremony participation; multi-gen) / shidemori (future; funeral → memorial NFT cross-link) / kokoro (future; grief / mental-health surge post-funeral) / chigiri.stewardLaborAttestation (officiant L5 classification) / toritate (ceremony venue cost via Public Fund grant if applicable)."
authoritative_for:
  - musubi actor R0 charter
  - religious-corp covenant ceremony performance substrate single SoT
  - `com.etzhayyim.musubi.*` Lexicon namespace boundary
  - Reformed 万人祭司 invariant (no clergy class; officiants are L5 vocation-flow community-witnessed)
  - prohibition on commercial wedding/funeral industry software
  - anti-coercive ceremony economy (no bride price / dowry)
  - per-ceremony consent + multi-generational invariant
  - chigiri cross-actor pair for covenantAttestation emit
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605250200-l5-religious-marriage-cell
  - adr-2605261000
  - adr-2605261030
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
related: []
supersedes: []
superseded_by: []
---

# ADR-2605263400: musubi (結) — non-profit religious-corp covenant ceremony substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The gap audit (session 2026-05-26) identified covenant ceremonies as
priority row 6. chigiri (ADR-2605262700) already path-reserved
`musubi` as the cross-actor pair of its `covenant_ceremony` cell at
R2 activation. This ADR realizes that pair.

The asymmetry between chigiri and musubi is structural:

- **chigiri** is procedural / attestation substrate. It does NOT
  perform ceremonies. It attests that ceremonies happened (per the
  `covenantAttestation` Lexicon, ADR-2605262700 L1).
- **musubi** is the ceremony-performance substrate. It coordinates
  the actual covenant rites — marriage / naming / funeral / vocation
  vow / rededication / seasonal communal — and emits the records
  that chigiri's attestation flow consumes.

The two are designed as a tight pair (same SRP discipline as iyashi
performs clinical encounters while mitate routes diagnoses).

Etymology: 結 (musubi) = "tie / knot / bind / connect". Shinto 産霊
(musubi) is the generative-creative force tying threads of life;
classical Japanese poetry uses 結 for binding souls, oaths, marriages,
ancestral lineage. The actor name carries the dual meaning of (a)
ceremonies that tie families and lives, and (b) the ongoing
connection that the ceremony seals.

Constitutional constraints (inherited; not adjustable):

- **NO clergy class** (G3 + N2) — Reformed 万人祭司 (priesthood-of-
  all-believers) invariant per Charter §1.7. Officiants are L5
  vocation-flow community-witnessed-competent stewards, NOT ordained
  clergy. Anyone can perform a covenant ceremony with Council-attested
  community-witness + ≥1 prior officiant attestation. There is no
  apostolic-succession / no sacramental-monopoly.
- **NO mandatory ritual attendance** (G4 + N3) — free conscience
  invariant. Members opt in to ceremonies; non-participation is
  never grounds for membership-status consequences.
- **NO sacrament-as-transubstantiation** (G9 + N4) — Sola Scriptura
  + Reformed memorial view per Charter §1.7. Communal practice
  honors biblical reference without imposing a single doctrinal
  monopoly; cross-doctrinal Wellbecoming priority over theological
  monoculture (N12).
- **NO commercial wedding/funeral industry software** (G6 + N6) —
  Aisle Planner / Honeybook / The Knot / WeddingWire / Zola / SRS
  Computing / Aldor / Wilbert / Frazer Consultants PROHIBITED per
  Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor
  concern (vendor closed query-tracking on member life-events
  exposes the deepest personal posture).
- **NO bride price / dowry coercion** (G7 + N7) — anti-coercive
  ceremony economy. Gifts to support newly-married couples are
  permitted; coercive economic transfer (bride price, dowry,
  bride-purchase) is constitutionally rejected. Multi-generational
  invariant + 反個人主義 honor mutual aid; coercive economic
  structures attached to ceremony are prohibited.
- **NO video recording without per-party consent** (G8) — ceremony
  privacy; mirrors hagukumi G2 + iyashi G3. Audio attestation may be
  permitted with consent (e.g., recorded vows); video is opt-in
  per-party.
- **NO payroll for officiants** (G12) — vocation-flow L5 stewards
  per Liberation Ladder L0..L6; cross-actor enforcement with
  chigiri.stewardLaborAttestation + toritate.ledgerEntry.category
  enum exclusion (this is now the pattern across chigiri / toritate
  / iyashi / mizuho / kazaori / musubi).
- **Multi-generational invariant** (G10) — Charter §1.7 prioritizes
  多世代 inclusion in ceremonies (children + adults + elders);
  silenMusubiReview audits cohort ratio per ceremony category.
- **Charter §1.13 Eros / Gore moderation** (G9) — marriage ceremony
  content + funeral content + seasonal-festival content pass the
  Eros/Gore moderation board (existing Charter §1.13 framework).
- **Cross-actor chigiri.covenantAttestation emit MANDATORY** (G11) —
  every ceremony performance MUST emit a corresponding chigiri.covenantAttestation
  record; non-emit = procedure invisible per chigiri G2 (kotoba-datomic
  attestation lineage MANDATORY).
- **Murakumo-only inference** (G13) — ceremony content review
  (Charter §1.13 + officiant-attestation language analysis) via
  judah LiteLLM → gemma4:e4b; commercial ceremony-content AI
  PROHIBITED.

# Decision

Create `musubi` (結) as a Tier-B religious-corp covenant ceremony
substrate actor at `20-actors/musubi/`, with DID
`did:web:musubi.etzhayyim.com`, Lexicon namespace
`com.etzhayyim.musubi.*`. R0 = scaffold only; all cells import-time
`RuntimeError`.

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `musubi` (結 — tie / knot / bind / connect; Shinto 産霊 generative force) |
| DID | `did:web:musubi.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.musubi.*` |
| Form | 任意団体 internal covenant ceremony performance substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格 — Preamble §0.4 Lv7+ unanimity lock) |
| Tier | Tier-B per-domain leader actor |
| Cross-actor pair | **chigiri** (chigiri attests, musubi performs; chigiri.covenant_ceremony cell explicit path-reserve at R2) |
| Other cross-actor | iyashi (healing-rite ceremonial closure post-chronic-care) / hagukumi (multi-gen ceremony participation) / shidemori (future; funeral → memorial NFT) / kokoro (future; post-funeral grief / mental health) / toritate (Public Fund ceremony venue grant if applicable) |

## §2. Scope (6 ceremony categories)

### A. Marriage ceremony (covenant rite)

- Covenant rite per Charter §1.12 state-function routing-around;
- NOT state-recognized marriage (jurisdictional path is external);
- Member-pair or multi-party covenant (jurisdictional rules outside
  scope); religious-corp recognition is internal-only;
- chigiri.covenantAttestation `ceremonyType=marriage` emit MANDATORY;
- NO bride price / dowry (G7 + N7);
- Multi-gen invariant: family ceremony participation honored;
- ADR-2605250200 L5 religious_marriage cell is the Pregel-cell
  implementation reference (already exists in 20-actors/magatama/cells/).

### B. Naming ceremony (baptism-equivalent + Adherent SBT issuance)

- For new Adherent member onboarding (chigiri.member_onboarding
  cross-actor pair);
- For newborn naming within religious-corp community (parental
  consent + community-witness);
- chigiri.covenantAttestation `ceremonyType=naming` OR
  `ceremonyType=sbt-issuance` emit MANDATORY.

### C. Funeral ceremony 葬送

- Communal honoring of deceased; Reformed memorial view (not
  transubstantiation; no purgatorial intercession);
- Cross-actor with future shidemori for memorial NFT mint;
- Cross-actor with chigiri.inheritance for succession attestation;
- chigiri.covenantAttestation `ceremonyType=funeral` emit MANDATORY;
- Adherent SBT burn coordinated post-ceremony.

### D. Vocation vow ceremony

- L5 vocation-flow steward formal commitment to specific religious-
  corp vocation (caregiver / clinician / educator / etc.);
- Cross-actor with chigiri.stewardLaborAttestation;
- chigiri.covenantAttestation `ceremonyType=vocation-vow` emit
  MANDATORY.

### E. Rededication ceremony

- Member returning after voluntary withdrawal + cooling period
  (chigiri.withdrawalAttestation L3 expired without finalization);
- Member returning after excommunication cure period + fresh
  Adherent ceremony (chigiri G12);
- chigiri.covenantAttestation `ceremonyType=rededication` OR
  `ceremonyType=covenant-restoration` emit MANDATORY.

### F. Seasonal communal ceremony

- Annual rhythm: 新年 (New Year) / 祈年 (Spring blessing) / 収穫
  (Harvest thanksgiving) / 感謝 (Gratitude festival) / 鎮魂
  (memorial day for deceased members) / 安息 (Sabbath observance
  pattern) / etc.;
- Communal Wellbecoming priority; multi-gen inclusion;
- Does NOT emit chigiri.covenantAttestation (no per-individual
  covenant); emits musubi.seasonalCeremonyCalendar entries instead.

## §3. Cells (6 Pregel cells under `20-actors/magatama/cells/musubi_*/`)

All R0 path-reserved; import-time `RuntimeError("musubi R0 scaffold: activate via Council ADR + R1 ratification + ≥3 officiant baseline attestations + community-witness registry initialized")` at W1 creation.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `marriage_ceremony` | gad (chigiri-paired) | event | ceremony plan + party consent + officiant + witnesses → ceremonyPerformanceAttestation + chigiri.covenantAttestation cross-emit |
| 2 | `naming_ceremony` | gad (chigiri.member_onboarding-paired) | event | new member candidate OR newborn + consent → ceremonyPerformanceAttestation + chigiri.covenantAttestation cross-emit |
| 3 | `funeral_ceremony` | gad (chigiri.inheritance + shidemori-paired) | event | deceased member DID + ceremony plan + witnesses → ceremonyPerformanceAttestation + chigiri.covenantAttestation + chigiri.inheritanceChain cross-emit |
| 4 | `vocation_vow_ceremony` | gad (chigiri.stewardLaborAttestation-paired) | event | L5 vocation candidate + commitment scope + witnesses → ceremonyPerformanceAttestation + chigiri.covenantAttestation cross-emit |
| 5 | `rededication_ceremony` | gad | event | returning member + cure-period attestation + Council ≥3 attestation → ceremonyPerformanceAttestation + chigiri.covenantAttestation cross-emit |
| 6 | `seasonal_communal_ceremony` | gad | calendar-driven (8-12/year) | seasonal cycle + community-attendance opt-in → seasonalCeremonyCalendar + (NO chigiri.covenantAttestation; communal not per-individual) |

R1 activation gates each cell separately + ≥3 officiant baseline
attestations on file (different from clergy ordination per G3 — these
are community-witnessed-competence attestations) + community-witness
registry initialized.

## §4. Lexicons (5, all under `com.etzhayyim.musubi.*`)

| # | Lexicon | Consumer cell | Description |
|---|---|---|---|
| L1 | `ceremonyPerformanceAttestation` | all 6 cells | Per-ceremony performance record; cross-link to chigiri.covenantAttestation CID; multi-gen ratio enforced |
| L2 | `officiantAttestation` | (all cells; officiant verification) | Officiant L5 vocation-flow community-witnessed-competence; G3 STRUCTURAL: officiantClass enum DELIBERATELY excludes "clergy" / "ordained" / "priest" / "bishop"; replaced by "community-witnessed-competent" |
| L3 | `communityWitnessAttestation` | all 6 cells | Per-ceremony witnesses (multi-gen required per G10) |
| L4 | `seasonalCeremonyCalendar` | seasonal_communal_ceremony | Annual calendar of communal ceremonies; community-attendance opt-in registry |
| L5 | `silenMusubiReview` | (Council attestation scope) | Quarterly Council Wellbecoming + multi-gen ratio + Charter §1.13 compliance + anti-coercive-economy audit |

## §5. Gates (13, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Every ceremony document MUST pass `pymagatama.organism.sensors.charter_rider.scan()` §2(a)-(h). |
| **G2** | Every record MUST emit `com.etzhayyim.musubi.*` Lexicon with kotoba-datomic attestation lineage. |
| **G3** | **NO clergy class** — Reformed 万人祭司 per Charter §1.7; officiants are L5 vocation-flow community-witnessed-competent; `officiantAttestation.officiantClass` enum DELIBERATELY excludes "clergy" / "ordained" / "priest" / "bishop" / "minister-with-ecclesiastical-authority". |
| **G4** | **NO mandatory ritual attendance** — free conscience invariant; member opt-in only; non-participation NEVER grounds for membership consequences. |
| **G5** | **Per-ceremony consent** (default-deny) — `ceremonyPerformanceAttestation.partyConsentCids` REQUIRED for all primary participants. |
| **G6** | **NO commercial wedding/funeral industry software** — Aisle Planner / Honeybook / The Knot / WeddingWire / Zola / SRS Computing / Aldor / Wilbert / Frazer Consultants PROHIBITED per Charter Rider §2(e) + §2(c). |
| **G7** | **NO bride price / dowry coercion** — anti-coercive ceremony economy; gifts permitted but coercive transfer prohibited; silenMusubiReview audits anti-coercive compliance. |
| **G8** | **NO video recording without per-party consent** — `ceremonyPerformanceAttestation.videoRecordingPerPartyConsent` REQUIRED if video produced; audio attestation may be recorded with consent. |
| **G9** | **Charter §1.13 Eros/Gore moderation** on ceremony content; no transubstantiation theology imposed (Sola Scriptura + Reformed memorial view); cross-doctrinal Wellbecoming priority. |
| **G10** | **Multi-generational invariant** per Charter §1.7 — ceremonies prioritize 多世代 inclusion; silenMusubiReview cohortRatio audits children + adults + elders per ceremony category. |
| **G11** | **Cross-actor chigiri.covenantAttestation emit MANDATORY** for marriage / naming / funeral / vocation-vow / rededication cells (NOT seasonal_communal — that is communal, not per-individual). |
| **G12** | NO payroll for officiants — vocation-flow L5 stewards (cross-actor enforcement chigiri.stewardLaborAttestation + toritate.ledgerEntry.category enum exclusion). |
| **G13** | Murakumo-only inference for ceremony content review (Charter §1.13 + officiant language analysis); commercial ceremony-content AI PROHIBITED. |

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT state-recognized marriage (Charter §1.12 routing-around; jurisdictional state recognition is external). |
| N2 | NOT clergy ordination (Reformed 万人祭司 invariant). |
| N3 | NOT mandatory ritual attendance (free conscience). |
| N4 | NOT sacrament-as-transubstantiation theology (Sola Scriptura + Reformed memorial view). |
| N5 | NOT confession requirement (no doctrinal confession in Protestant tradition). |
| N6 | NOT commercial wedding/funeral industry integration. |
| N7 | NOT bride price / dowry economic structure. |
| N8 | NOT closed-source. |
| N9 | NOT a state-licensed entity. |
| N10 | NOT payroll-based officiant model. |
| N11 | NOT surveillance-based ceremony recording (G8 per-party consent invariant). |
| N12 | NOT single-doctrinal-stance — cross-doctrinal Wellbecoming priority over theological monoculture; Protestant / Reformed / Anglican / Baptist / Methodist / nondenominational / cross-tradition all accommodated within Charter §1.7 + §1.13 boundaries. |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 6 cells path-reserved. 5 Lexicons schema skeleton. | No deployment |
| **R1** | post-Council + ≥3 officiant baseline attestations + community-witness registry initialized + chigiri R1 active (covenantAttestation cross-emit dependency) | Activate 2 core cells: `marriage_ceremony` + `naming_ceremony`. ≤10 marriages + ≤20 naming ceremonies in pilot year. | gad (single node) |
| **R2** | post-R1 + 30-day public objection + 5 community-site Council attestations | Activate +3 cells: `funeral_ceremony` (shidemori-pair future) + `vocation_vow_ceremony` (chigiri.stewardLaborAttestation-pair) + `rededication_ceremony`. ≤50 ceremonies/year per category. | gad + simeon (2 nodes) |
| **R3** | post-R2 + Council Lv7+ unanimity + ≥1 full annual cycle of seasonal_communal_ceremony completed + silenMusubiReview cycle established | Activate +1 cell: `seasonal_communal_ceremony` (8-12 annual). Multi-site community-scale. | gad + simeon + naphtali (3 nodes) |

## §8. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `chigiri.covenant_ceremony` | ↔ (TIGHT PAIR) | chigiri attests on-chain, musubi performs ceremony; covenantAttestation cross-emit MANDATORY (G11) |
| `chigiri.member_onboarding` | ↔ (naming pair) | New Adherent SBT issuance ceremony pairs with member onboarding cell |
| `chigiri.inheritance` | ↔ (funeral pair) | Funeral ceremony triggers inheritanceChain succession attestation |
| `chigiri.stewardLaborAttestation` | → (read) | Officiant L5 vocation-flow classification (G12); vocation_vow_ceremony also writes back |
| `iyashi` | ↔ | Healing-rite ceremonial closure for chronic care recipients (post-clinical ceremonial transition) |
| `hagukumi` | ↔ | Multi-gen ceremony participation (children + elders cross-link) |
| `shidemori` (future) | ↔ | Funeral → memorial NFT mint cross-actor |
| `kokoro` (future) | ↔ | Post-funeral grief + mental-health surge cross-actor |
| `toritate` | → (read; ceremony venue cost via Public Fund grant) | Optional Public Fund grant for venue / supplies if applicable |
| ADR-2605250200 L5 religious_marriage cell | ← (implementation reference) | Existing Pregel-cell pattern for marriage ceremony performance |

## §9. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605263400-musubi-covenant-ceremony-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/musubi/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 5 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/musubi/` + README;
4. `deps.toml` [[adrs]] + [[modules]] entries;
5. `90-docs/adr/README.md` index update;
6. `CLAUDE.md` Status table row 73 + Repo Layout entry.

No code activation in R0.

# Consequences

**Positive**:

- Closes gap-audit #6 priority (covenant ceremonies) — religious-corp
  finally has a first-party ceremony substrate matching the chigiri
  attestation cell;
- G3 + N2 Reformed 万人祭司 invariant operationalized via
  officiantAttestation.officiantClass enum exclusion of clergy /
  ordained / priest / bishop terms — structural enforcement of
  Charter §1.7;
- G6 + N6 commercial wedding/funeral industry software prohibition
  documents and structurally enforces Charter Rider §2(e) + §2(c);
- G7 + N7 anti-coercive ceremony economy operationalizes Charter
  §1.7 multi-gen + 反個人主義 + non-coercive economy doctrines into
  ceremony domain (where coercive bride price / dowry historically
  embedded);
- G10 multi-generational invariant in ceremonies counter-balances
  modern individualist ceremony trends;
- Cross-actor chigiri pair completes a long-pending tight integration
  (path-reserved at chigiri ADR-2605262700);
- Seasonal communal ceremony (R3) adds annual community rhythm that
  reinforces multi-gen + Wellbecoming priority.

**Negative / cost**:

- ≥3 officiant baseline attestations is R1 gating dependency; Bootstrap
  Council Seat 2-5 RFP must surface willing officiant-candidates with
  ceremony experience;
- G3 no-clergy invariant is theologically opinionated (Reformed
  Protestant); members from Catholic / Orthodox / sacramental
  traditions must reconcile (Charter §1.13 cross-doctrinal Wellbecoming
  priority handles this at the moderation board);
- G6 commercial-wedding-industry-software prohibition means
  religious-corp wedding ceremonies cannot integrate with mainstream
  vendor calendars (Aisle Planner / Zola / etc.); members must accept
  the friction;
- G7 anti-coercive ceremony economy may conflict with cultural
  expectations of bride price / dowry in some communities; cultural
  vs constitutional tension resolved in favor of constitutional
  invariant.

**Forward-compatibility**:

- shidemori (future; gap audit row 10 = 冥府 / cemetery + memorial)
  cross-actor for funeral → memorial NFT mint;
- kokoro (future; gap audit row 9 = 精神 / mental health) cross-actor
  for post-funeral grief surge;
- Seasonal ceremony calendar (R3) extends naturally to additional
  cycles as community grows;
- Cross-religious-corp ceremony recognition (future Sphere-style
  federation) integrates via chigiri.covenantAttestation cross-emit
  pattern.

# Alternatives Considered

1. **Subsume into chigiri (legal procedure)**. Rejected — chigiri is
   attestation; musubi is performance; SRP violation if merged
   (same pattern as iyashi separate from mitate).

2. **Allow clergy ordination (carve out from Reformed 万人祭司)**.
   Rejected per G3 + N2 + Charter §1.7 constitutional invariant.
   Officiants are community-witnessed-competent stewards; this is
   structural, not policy.

3. **Use Aisle Planner / Zola / Honeybook / SRS Computing as
   ceremony management software**. Rejected per Charter Rider
   §2(e) + §2(c). Vendor closed query-tracking on member life-
   events is structurally unacceptable.

4. **Allow bride price / dowry as cultural accommodation**. Rejected
   per G7 + Charter §1.7 anti-coercive economy invariant.
   Constitutional invariant overrides cultural accommodation.

5. **Make ceremony attendance mandatory for membership preservation**.
   Rejected per G4 + free conscience invariant. Non-participation
   NEVER grounds for membership consequences.

6. **Skip seasonal_communal_ceremony (focus on individual rites
   only)**. Rejected — multi-gen invariant (G10) requires communal
   rhythm; individual-rite-only would individualize ceremony life
   inconsistent with Charter §1.7 反個人主義.

7. **Defer until shidemori (cemetery / memorial) future actor lands
   first**. Rejected — funeral ceremony is currently the gap; shidemori
   is a downstream memorial-NFT actor that consumes the funeral
   ceremony output. musubi can ship without shidemori; funeral_ceremony
   cell at R2 awaits shidemori for full memorial flow but the
   ceremony itself can perform.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605181100 — MST encrypted records + Signal key wrap
- ADR-2605192100 — Mission Charter (§1.7 multi-gen + 万人祭司 + 反個人主義; §1.12 routing-around; §1.13 Eros/Gore)
- ADR-2605192145 — Public Fund architecture (ceremony venue grant)
- ADR-2605192200 — Charter Compliance Rider v2.0 (§2(e) + §2(c) G6 sources)
- ADR-2605192245 — Global Land Sovereignty (ceremony location Land Registry cross-link)
- ADR-2605192300 — Council 5-of-7 Safe
- ADR-2605215000 — Inference Murakumo-only (G13)
- ADR-2605250200 — L5 religious_marriage cell (existing Pregel-cell implementation reference)
- ADR-2605261000 — Labor Liberation Transition Mechanism (G12 vocation-flow)
- ADR-2605261030 — hagukumi (cross-actor multi-gen ceremony participation)
- ADR-2605262130 — Kotoba storage substrate
- ADR-2605262700 — chigiri (TIGHT PAIR — covenant_ceremony cell explicit cross-actor)
- ADR-2605262900 — toritate (cross-actor ceremony venue accounting)
- ADR-2605263000 — iyashi (cross-actor healing-rite ceremonial closure)
- `/CHARTER-RIDER.md` §2 — 8 prohibited categories
