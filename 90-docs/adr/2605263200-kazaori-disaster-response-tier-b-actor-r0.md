---
id: adr-2605263200-kazaori-disaster-response-tier-b-actor-r0
title: "ADR-2605263200: kazaori (風折) — non-profit religious-corp civilian disaster response substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: kazaori-disaster-response-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: emergency-response
weight: 0.55
priority_note: "Fifth-priority gap-closure actor (gap audit row 5 = 災害対応 / disaster response). Civilian disaster response substrate — earthquake / typhoon / flood / wildfire / pandemic-class biological emergency / power outage / water shortage / food shortage / building damage / mass evacuation / medical surge coordination. NOT military, NOT war-zone humanitarian, NOT long-term refugee resettlement, NOT state emergency-management replacement, NOT armed enforcement (force authorization is separate per ADR-2605192315 Transparent Force; kazaori is civilian-only). 任意団体 internal coordination substrate at did:web:kazaori.etzhayyim.com (20-actors/kazaori/). Etymology: 風折 = wind-broken (storm-damaged tree branches; classical 古事記 / 万葉集 imagery); evokes disaster-induced rupture requiring response. Standards reference (NOT membership): Sphere Standards (G9) + ICRC Code of Conduct + IFRC + UN OCHA cluster system (all open-source / open-publication frameworks). NO commercial disaster management software (G4 — Veoci / NC4 / Crisis Track / Everbridge / OnSolve / SAP Disaster Recovery / Microsoft Disaster Response Hub / IBM Crisis Response PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor concern — vendor closed query-tracking exposes member-evacuation + member-status posture). NO surveillance-based monitoring (G6 — aerial drone surveillance / facial-recognition crowd-monitoring / Bluetooth-beacon-tracking PROHIBITED per Charter §2(c); evacuation check-in is OPT-IN self-attestation, member-signed). Time-bounded carve-outs (G8 — normally-prohibited operations such as mizuho G5 single-use water container distribution may be activated during declared emergency, default 60-day initial / Council Lv7+ unanimity extension / auto-revoke on emergency-lifting). 6 cells / 6 Lexicons under com.etzhayyim.kazaori.* / 12 immutable gates / 12 non-goals / 4-phase R0..R3. Cross-actor: mizuho (G5 single-use carve-out coordination + emergency water supply) / mitsuho (emergency food supply from reserve stocks + mutual aid) / hagukumi (vulnerable population coordination — children + elderly) / iyashi + mitate (medical surge) / tatekata (building damage assessment) / hikari (power outage coordination) / chigiri (declaration procedural attestation + post-emergency mediation if cure-required) / toritate (Public Fund emergency disbursement + post-emergency accounting) / wakai (future; mutual aid pooling) / kokoro (future; post-emergency mental health surge)."
authoritative_for:
  - kazaori actor R0 charter
  - religious-corp civilian disaster response substrate single SoT
  - `com.etzhayyim.kazaori.*` Lexicon namespace boundary
  - civilian-only invariant (NOT military; force authorization separate per ADR-2605192315)
  - time-bounded carve-out invariant (G8 — normally-prohibited operations auto-revoke on emergency-lifting)
  - prohibition on commercial disaster management software (Veoci / NC4 / Crisis Track / Everbridge / OnSolve / SAP / Microsoft / IBM Crisis Response)
  - prohibition on surveillance-based emergency monitoring (opt-in self-check-in only)
  - Sphere Standards reference (NOT membership)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605181200-mst-encrypted-metadata-leak-reduction
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605261000
  - adr-2605261015
  - adr-2605261030
  - adr-2605261100
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
  - adr-2605263100-mizuho-water-sanitation-tier-b-actor-r0
related: []
supersedes: []
superseded_by: []
---

# ADR-2605263200: kazaori (風折) — non-profit religious-corp civilian disaster response substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The gap audit (session 2026-05-26) identified disaster response as
priority row 5. Religious-corp lacks an actor for emergency response
coordination, despite having most of the upstream and downstream
actors that disaster scenarios touch:

- **mizuho** (ADR-2605263100) — water supply; G5 single-use container
  prohibition needs a time-bounded carve-out path for emergencies;
- **mitsuho** (ADR-2605261015) — food supply; emergency reserve stock
  coordination missing;
- **hagukumi** (ADR-2605261030) — daily-living care; vulnerable
  population (children + elderly) coordination during evacuation
  missing;
- **iyashi** (ADR-2605263000) + **mitate** — clinical capacity surge
  during mass casualty event missing;
- **tatekata** — building damage assessment missing;
- **hikari** — power outage coordination missing;
- **chigiri** — declaration procedural attestation + post-emergency
  mediation (when carve-out cure-period applies);
- **toritate** — Public Fund emergency disbursement + post-emergency
  accounting transparency;
- **kokoro** (future) — post-emergency mental health surge;
- **wakai** (future) — mutual aid pooling across community sites.

Without **kazaori**, religious-corp depends on state emergency
management (which brings vendor data-sovereignty exposure, mandatory
ID-disclosure during evacuation, and centralized command structures
incompatible with religious-corp 1 SBT = 1 vote discipline).

Etymology: 風折 (kazaori / kazaore) = "wind-broken" (storm-damaged
tree branches in classical Japanese imagery; 万葉集 evokes the
ephemeral fragility that disasters expose). The actor name carries
the dual meaning of (a) disasters that come, and (b) the response that
follows.

Constitutional constraints (inherited; not adjustable):

- **NOT military / NOT armed enforcement** (G5 + N1) — kazaori is
  civilian disaster response only. Transparent Force authorization
  (ADR-2605192315) is the separate procedural substrate for any
  defensive force scenarios; kazaori MUST NOT invoke or coordinate
  with armed force actions during disaster response.
- **NOT war-zone humanitarian aid** (N2) — community-scale civilian
  only. ICRC + IFRC + UN OCHA frameworks are referenced as
  standards (not membership; not deployment authorization).
- **NOT a state emergency-management replacement** (N5) — parallel
  substrate per Charter §1.12 state-function routing-around;
  cooperates with state emergency management where appropriate but
  does not depend on it.
- **NO commercial disaster management software** (G4) — Veoci / NC4
  / Crisis Track / Everbridge / OnSolve / SAP Disaster Recovery /
  Microsoft Disaster Response Hub / IBM Crisis Response PROHIBITED
  per Charter Rider §2(e) + §2(c). Vendor closed query-tracking on
  evacuation status + member location is structurally unacceptable.
- **NO surveillance-based monitoring** (G6) — aerial drone
  surveillance / facial-recognition crowd-monitoring / Bluetooth-
  beacon-tracking PROHIBITED per Charter §2(c) covert-ops avoidance.
  Evacuation check-in is OPT-IN self-attestation only; member-signed;
  encrypted envelope per ADR-2605181100.
- **Time-bounded carve-outs** (G8) — normally-prohibited operations
  (mizuho G5 single-use water container; iyashi G13 expedited
  consent abridgment for unconscious patients; etc.) MAY be activated
  during a Council-Lv6+-declared emergency, default 60-day initial /
  Council Lv7+ unanimity extension / auto-revoke on emergency-lifting.
  Carve-outs are logged via `emergencyCarveOutLog` Lexicon and post-
  emergency Council attestation review (G via silenKazaoriReview).
- **Sphere Standards minimum compliance** (G9) — reference framework
  for shelter / water / food / health / protection in any kazaori
  response; Sphere is open-publication; no membership / no certification
  required for reference.
- **Council Lv6+ ≥4/7 declaration** (G10) — emergency state requires
  Council supermajority declaration; Council Lv7+ unanimity for
  extension beyond 60 days; auto-lifting at expiration unless
  re-extended.
- **NO payroll for responders** (G12) — responders are vocation-flow
  L5 stewards per Liberation Ladder L0..L6 + cross-actor enforcement
  with chigiri.stewardLaborAttestation + toritate.ledgerEntry.category
  enum exclusion.
- **Murakumo-only inference** (ADR-2605215000) — damage assessment
  prediction + supply-demand routing via judah LiteLLM → gemma4:e4b;
  commercial disaster-AI (One Concern / FloodFlash / etc.)
  PROHIBITED.

# Decision

Create `kazaori` (風折) as a Tier-B religious-corp civilian disaster
response substrate actor at `20-actors/kazaori/`, with DID
`did:web:kazaori.etzhayyim.com`, Lexicon namespace
`com.etzhayyim.kazaori.*`. R0 = scaffold only; all cells import-time
`RuntimeError`.

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `kazaori` (風折 — wind-broken; storm-damaged) |
| DID | `did:web:kazaori.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.kazaori.*` |
| Form | 任意団体 internal civilian disaster response substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格 — Preamble §0.4 Lv7+ unanimity lock) |
| Tier | Tier-B per-domain leader actor |
| Cross-actor (response) | mizuho (G5 carve-out + water) / mitsuho (food) / hagukumi (vulnerable populations) / iyashi + mitate (medical surge) / tatekata (damage assessment) / hikari (power outage) / chigiri (declaration attestation) / toritate (Public Fund emergency disbursement) |
| Cross-actor (future) | wakai (mutual aid pooling) / kokoro (post-emergency mental health surge) / shidemori (mass-fatality memorial when applicable) |
| Standards reference (NOT membership) | Sphere Standards / ICRC Code of Conduct / IFRC / UN OCHA cluster system / WHO Health Cluster |

## §2. Scope (5 sections)

### A. Emergency state lifecycle

- Council Lv6+ ≥4/7 declares state of emergency (`emergencyDeclarationAttestation`);
- 60-day initial duration; Council Lv7+ unanimity required for extension;
- Auto-lifting at expiration; carve-outs auto-revoke;
- Post-emergency Council review (silenKazaoriReview) mandatory within 90 days of lifting.

### B. Damage assessment + needs prediction

- Continuous data fusion across cross-actors during active emergency
  (mizuho water-quality / hikari grid status / tatekata building
  damage / iyashi clinical capacity / mitsuho food reserve);
- Murakumo-only inference for needs prediction (G7);
- NO surveillance-based monitoring (G6); damage assessment is
  attestation-based (community-reporting + cross-actor data),
  not surveillance-based.

### C. Cross-actor emergency supply dispatch

- **Water** → mizuho G5 single-use container time-bounded carve-out
  activated; emergency potable water dispatch via closed-loop
  refillable containers preferred, single-use ONLY where logistics
  require (logged via `emergencyCarveOutLog`);
- **Food** → mitsuho reserve stock release coordination + mutual aid
  pooling (future wakai integration);
- **Medical** → iyashi + mitate clinical surge protocol (clinic-
  overflow + temporary triage site authorization);
- **Power** → hikari grid-edge battery emergency redirection;
- **Shelter** → tatekata damage assessment + safe-site designation
  (community-scale).

### D. Mass evacuation coordination (OPT-IN)

- Member opt-in self-check-in via `evacuationCheckIn` (member-signed;
  encrypted payload per ADR-2605181100);
- Safe-site registry (community-scale safe sites; cross-actor with
  tatekata for facility damage assessment);
- Vulnerable population priority routing (hagukumi cross-link for
  children + elderly + chronic-care patients);
- NO surveillance / NO mandatory tracking (G6); families that do not
  check in are NOT pursued by kazaori (state emergency management
  may; that's their domain).

### E. Time-bounded carve-out lifecycle

- During active declared emergency, normally-prohibited operations
  may be activated via `emergencyCarveOutLog`;
- Examples: mizuho G5 single-use container distribution, iyashi G4
  expedited consent abridgment for unconscious patients, mitsuho
  reserve-stock-distribution-without-individual-consent protocols;
- Each carve-out MUST cite the specific gate being carved-out + the
  Council Lv6+ ≥4/7 attestation authorizing it;
- Carve-outs auto-revoke on emergency-lifting (no carve-over to
  normal operations);
- Post-emergency Council review (silenKazaoriReview) audits every
  carve-out used during the emergency.

## §3. Cells (6 Pregel cells under `20-actors/magatama/cells/kazaori_*/`)

All R0 path-reserved; import-time `RuntimeError("kazaori R0 scaffold: activate via Council ADR + R1 ratification + Sphere Standards baseline + ≥1 community-pilot tabletop drill")` at W1 creation.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `emergency_declaration` | naphtali | event | Council Lv6+ ≥4/7 declaration → emergencyDeclarationAttestation; handles lifting state-transition |
| 2 | `damage_assessment` | naphtali | continuous (during active emergency) | cross-actor data fusion → damageAssessmentReport |
| 3 | `emergency_water_supply` | naphtali (mizuho-paired) | continuous (during active emergency) | needs prediction → mizuho G5 carve-out + emergencySupplyDispatch |
| 4 | `emergency_food_supply` | naphtali (mitsuho-paired) | continuous (during active emergency) | needs prediction → mitsuho reserve release + emergencySupplyDispatch |
| 5 | `mass_evacuation` | naphtali | continuous (during active emergency) | opt-in self-check-in → evacuationCheckIn + safe-site registry routing |
| 6 | `medical_surge` | naphtali (iyashi + mitate paired) | continuous (during active emergency) | clinical capacity overflow → iyashi clinic-overflow protocols + temporary triage site authorization |

R1 activation gates each cell separately + Sphere Standards baseline
attestation on file + ≥1 community-pilot tabletop drill.

## §4. Lexicons (6, all under `com.etzhayyim.kazaori.*`)

| # | Lexicon | Consumer cell | Description |
|---|---|---|---|
| L1 | `emergencyDeclarationAttestation` | emergency_declaration | Council Lv6+ ≥4/7 declaration of state of emergency; G10 structural; duration enum; declaredScope (which jurisdictions + community sites covered) |
| L2 | `damageAssessmentReport` | damage_assessment | Per-area / per-asset damage report; cross-actor data fusion sources via $ref |
| L3 | `emergencySupplyDispatch` | emergency_water_supply + emergency_food_supply | Per-dispatch event; cross-actor mizuho / mitsuho; carve-out cite via $ref |
| L4 | `evacuationCheckIn` | mass_evacuation | OPT-IN self-attestation; encryptedPayloadCid REQUIRED (G2-equivalent privacy invariant); G6 structural: no third-party tracking |
| L5 | `emergencyCarveOutLog` | any cell | Per-carve-out activation log; gate being carved + Council attestation chain + auto-revoke timestamp; G8 structural |
| L6 | `silenKazaoriReview` | (Council attestation scope) | Post-emergency review; Sphere Standards compliance assessment + carve-out audit + Wellbecoming preservation review; G9 + G8 structural |

## §5. Gates (12, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Every emergency document MUST pass `pymagatama.organism.sensors.charter_rider.scan()` §2(a)-(h). |
| **G2** | Every record MUST emit `com.etzhayyim.kazaori.*` Lexicon with kotoba-datomic attestation lineage. |
| **G3** | **Community-scale only** — disaster response coordinated for religious-corp community sites + adjacent partner sites; NOT large municipal / regional / national disaster response replacement. |
| **G4** | **NO commercial disaster management software** — Veoci / NC4 / Crisis Track / Everbridge / OnSolve / SAP Disaster Recovery / Microsoft Disaster Response Hub / IBM Crisis Response PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty. |
| **G5** | **NO armed enforcement** — kazaori is civilian disaster response only; force authorization is separate per ADR-2605192315 Transparent Force; kazaori MUST NOT invoke or coordinate with armed force actions. |
| **G6** | **NO surveillance-based monitoring** — aerial drone surveillance / facial-recognition crowd-monitoring / Bluetooth-beacon-tracking PROHIBITED per Charter §2(c); evacuation check-in is OPT-IN self-attestation only. |
| **G7** | Murakumo-only inference per ADR-2605215000 — commercial disaster-AI (One Concern / FloodFlash / etc.) PROHIBITED. |
| **G8** | **Time-bounded carve-outs** — normally-prohibited operations MAY be activated only during Council-Lv6+-declared emergency; default 60-day initial; Council Lv7+ unanimity for extension; auto-revoke on emergency-lifting; logged via `emergencyCarveOutLog`; post-emergency Council review mandatory. |
| **G9** | **Sphere Standards minimum compliance** — reference framework for shelter / water / food / health / protection; Sphere is open-publication; silenKazaoriReview audits compliance. |
| **G10** | **Council Lv6+ ≥4/7 declaration** — emergency state requires Council supermajority; `emergencyDeclarationAttestation.councilAttestations` minLength 4. |
| **G11** | NOT a state-licensed emergency services entity — 任意団体 internal substrate; cooperates with state emergency management but is NOT a substitute. |
| **G12** | NO payroll for responders — vocation-flow L5 stewards (cross-actor enforcement with chigiri.stewardLaborAttestation + toritate.ledgerEntry.category enum exclusion). |

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT military operations / NOT armed enforcement (force authorization separate per ADR-2605192315). |
| N2 | NOT war-zone humanitarian aid (community-scale civilian only). |
| N3 | NOT long-term refugee resettlement (immediate emergency only; ≤180 days post-event). |
| N4 | NOT insurance claim processing (no insurance billing per chigiri / toritate / iyashi pattern). |
| N5 | NOT state emergency-management replacement (parallel substrate per Charter §1.12). |
| N6 | NOT surveillance-based monitoring (G6; opt-in self-check-in only). |
| N7 | NOT commercial disaster management software integrator (G4). |
| N8 | NOT armed enforcement (G5). |
| N9 | NOT closed-source (Apache 2.0 + Charter Rider). |
| N10 | NOT a state-licensed entity (G11). |
| N11 | NOT single-jurisdiction-dependent (community-scale across jurisdictions; Sphere reference is jurisdiction-agnostic). |
| N12 | NOT permanent emergency state (G8 time-bounded; auto-revoke; Council Lv7+ unanimity for any extension). |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 6 cells path-reserved. 6 Lexicons schema skeleton. | No deployment |
| **R1** | post-Council + Sphere Standards baseline attestation on file + ≥1 community-pilot tabletop drill | Activate 2 core cells: `emergency_declaration` + `damage_assessment`. ≥1 community pilot drill (tabletop exercise + 1 simulated emergency declaration). | naphtali (single node) |
| **R2** | post-R1 + ≥30-day public objection + 3 community-site Council attestations | Activate +3 cells: `emergency_water_supply` (mizuho-pair G5 carve-out automation), `emergency_food_supply` (mitsuho-pair), `mass_evacuation` (opt-in registry). | naphtali + dan (2 nodes) |
| **R3** | post-R2 + Council Lv7+ unanimity + ≥1 real (or large-scale simulated) emergency cycle completed + silenKazaoriReview cycle established | +1 cell: `medical_surge` (iyashi + mitate triad pair). Post-emergency Council review cycle established. Sphere compliance attestation per emergency. | naphtali + dan + levi (3 nodes) |

## §8. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `mizuho` | ↔ | G5 single-use container time-bounded carve-out coordination during emergency; emergency water supply dispatch |
| `mitsuho` | ↔ | Emergency food supply from reserve stocks + mutual aid distribution |
| `hagukumi` | ↔ | Vulnerable population coordination (children + elderly + chronic care recipients) during evacuation |
| `iyashi` | ↔ | Clinical capacity surge protocols; clinic-overflow + temporary triage site authorization |
| `mitate` | ↔ | Diagnostic surge + emergency keyword cross-actor pattern (existing G10 mitate emergency-keyword Lexicon) |
| `tatekata` | ↔ | Building damage assessment + safe-site designation |
| `hikari` | ↔ | Power outage coordination + grid-edge battery emergency redirection |
| `chigiri` | ↔ | Declaration procedural attestation + post-emergency mediation if carve-out cure-period applies |
| `toritate` | ↔ | Public Fund emergency disbursement + post-emergency accounting transparency report |
| `wakai` (future) | ↔ | Mutual aid pooling across community sites |
| `kokoro` (future) | ↔ | Post-emergency mental health surge |
| `shidemori` (future) | ↔ | Mass-fatality memorial when applicable |

## §9. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605263200-kazaori-disaster-response-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/kazaori/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 6 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/kazaori/` + README;
4. `deps.toml` [[adrs]] + [[modules]] entries;
5. `90-docs/adr/README.md` index update;
6. `CLAUDE.md` Status table row 72 + Repo Layout entry.

No code activation in R0.

# Consequences

**Positive**:

- Closes gap-audit #5 priority (disaster response) — religious-corp
  no longer depends entirely on state emergency management with all
  its vendor data-sovereignty + ID-disclosure implications;
- G4 commercial-disaster-management-software prohibition documents
  and structurally enforces a Charter Rider §2(e) + §2(c) constraint;
- G5 + N1 civilian-only invariant separates emergency response from
  Transparent Force authorization (ADR-2605192315) cleanly;
- G6 + N6 surveillance prohibition extends Charter §2(c) covert-ops
  avoidance into the emergency domain (where surveillance temptation
  is highest);
- G8 time-bounded carve-out lifecycle gives religious-corp a
  structurally-safe path to suspend gates that would otherwise
  block emergency response (mizuho G5 single-use container is the
  paradigm example);
- The cross-actor coordination at R3 (water + food + clinical surge +
  power + damage assessment + evacuation) makes religious-corp
  community sites resilient against the most common disaster classes.

**Negative / cost**:

- G8 time-bounded carve-out is constitutionally novel; there is no
  prior religious-corp precedent for time-bounded gate suspension;
  Council attestation discipline at silenKazaoriReview is critical
  to prevent carve-out drift toward normalization;
- ≥1 community-pilot tabletop drill is R1 gating dependency;
  Bootstrap Council Seat 2-5 RFP must surface a willing emergency-
  management-experienced advisory candidate;
- Sphere Standards compliance is an ongoing attestation burden
  (Sphere is large; ~5,000 indicators across shelter / water / food
  / health / protection); R3 silenKazaoriReview pattern must scale;
- G6 opt-in-only evacuation means kazaori CANNOT pursue families that
  do not check in; this is by design (privacy invariant) but is a
  real cost during fast-moving events (state emergency management
  has the alternate authority for non-religious-corp residents).

**Forward-compatibility**:

- wakai (future; gap audit row 7 = 共済) cross-actor for mutual aid
  pooling integrates cleanly via `emergencySupplyDispatch`
  cross-actor pattern;
- kokoro (future; gap audit row 9 = 精神 / mental health) post-
  emergency mental health surge integrates via medical_surge cell
  extension at R3+;
- shidemori (future; gap audit row 10 = 冥府 / cemetery + memorial)
  cross-actor for mass-fatality memorial when applicable;
- Cross-religious-corp federation potential: Sphere Standards
  reference is jurisdiction-agnostic and supports inter-religious-
  corp mutual aid where future Sphere-attested partners exist.

# Alternatives Considered

1. **Subsume into chigiri (legal procedure)**. Rejected — emergency
   response is operational, not procedural; SRP violation.

2. **Use Veoci / NC4 / Crisis Track / Everbridge as the response
   platform**. Rejected per Charter Rider §2(e) + §2(c). Vendor
   tracking on member evacuation status is structurally unacceptable.

3. **Allow surveillance during declared emergency (carve-out)**.
   Rejected per G6 + N6. Surveillance during emergency is the
   highest-temptation case; the constitutional invariant must hold
   precisely there. Opt-in self-check-in is the discipline.

4. **Allow armed enforcement carve-out for evacuation crowd control**.
   Rejected per G5 + N1 + N8. Civilian disaster response remains
   civilian; armed force scenarios go through ADR-2605192315
   Transparent Force, which has its own discipline and its own gating.

5. **Make declaration unilateral (Founder Lv7+ emergency power)**.
   Considered. Rejected per the pattern established in ADR-2605262200
   ("Founder Lv7+ emergency authorization explicitly NOT taken;
   institutional integrity over R&D urgency"); same discipline applies
   here — Council Lv6+ ≥4/7 is the minimum for declaration even in
   urgent situations.

6. **Skip Sphere Standards reference (too large to attest)**. Rejected
   per N11 multi-jurisdictional principle. Sphere is the open-
   publication jurisdiction-agnostic reference framework; the
   compliance attestation burden is real but the standard itself is
   the right anchor.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605181100 — MST encrypted records + Signal key wrap
- ADR-2605192100 — Mission Charter (Wellbecoming + §1.12 + §2(c))
- ADR-2605192145 — Public Fund architecture (emergency disbursement)
- ADR-2605192200 — Charter Compliance Rider v2.0
- ADR-2605192245 — Global Land Sovereignty (safe-site Land Registry cross-link)
- ADR-2605192300 — Council 5-of-7 Safe (G10 declaration)
- ADR-2605192315 — Transparent Force authorization (G5 + N1 separation)
- ADR-2605215000 — Inference Murakumo-only (G7)
- ADR-2605261000 — Labor Liberation Transition Mechanism (G12)
- ADR-2605261015 — mitsuho (cross-actor food supply)
- ADR-2605261030 — hagukumi (cross-actor vulnerable population)
- ADR-2605261100 — hikari (cross-actor power outage)
- ADR-2605262130 — Kotoba storage substrate
- ADR-2605262700 — chigiri (cross-actor procedural attestation)
- ADR-2605262900 — toritate (cross-actor emergency disbursement)
- ADR-2605263000 — iyashi (cross-actor medical surge)
- ADR-2605263100 — mizuho (cross-actor G5 single-use carve-out + water)
- `/CHARTER-RIDER.md` §2 — 8 prohibited categories (esp. §2(e) + §2(c))
- Sphere Handbook (Sphere Standards) — open-publication reference framework
- ICRC Code of Conduct for International Red Cross / Red Crescent Movement
- IFRC + UN OCHA cluster system — emergency coordination reference
