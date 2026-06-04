---
id: adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
title: "ADR-2605262700: chigiri (契) — non-profit religious-corp legal procedure substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: chigiri-legal-procedure-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: governance
weight: 0.60
priority_note: "First-class religious-corp legal procedure actor. 任意団体 internal procedure substrate + state-system interface routing + Charter §1.12 state-function routing-around — packaged as procedural template + on-chain attestation + routing substrate, NOT as a commercial law firm and NOT as an unauthorized practice of law (UPL strictly prohibited per G14). chigiri does not provide legal advice; human counsel is contracted out of Public Fund (Council Lv6+) when needed. 12 cells / 9 Lexicons under `com.etzhayyim.chigiri.*` / 14 immutable constitutional gates / 12 non-goals / 4-phase R0..R3. Consumes legal corpus from ADR-2605262800 (public-data legal corpus ingestion via IPFS-pinned DataLad subdatasets) as the data substrate, and cross-actor invokes `did:web:hanrei.etzhayyim.com` for case-law / 判例 lookups. Replaces the legacy `lawfirm.etzhayyim.com` reference visible in 20-actors/hanrei/CLAUDE.md with a religious-corp native, Murakumo-only, SBT-gated, Charter Rider §2-compliant substrate. Constitutional invariants honored: NOT 宗教法人法 登記 (Preamble §0.4 Lv7+ unanimity lock); NOT a state-granted legal personality (N2); Murakumo-only inference (G11); 1 SBT = 1 vote for community governance decisions (G6); Defensive Just War only (G7); Open-source legal templates (G8); Multi-jurisdictional fallback (G9); Cooperative mediation precedes adversarial arbitration (G10); Excommunication Council Lv6+ + 30-day cure (G12); Volunteer ≠ employee per Liberation Ladder L0..L6 classification (G13). All 12 cells import-time `RuntimeError` at R0 (same scaffold discipline as hagukumi ADR-2605261030)."
authoritative_for:
  - chigiri actor R0 charter
  - religious-corp legal procedure substrate single SoT
  - `com.etzhayyim.chigiri.*` Lexicon namespace boundary
  - non-profit (任意団体) legal procedure architecture
  - Charter §1.12 state-function routing-around procedural primitives
  - covenant ceremony attestation contract (musubi / shidemori cross-actor)
  - internal mediation precedes adversarial arbitration rule (G10)
  - UPL prohibition surface (G14) — chigiri is NOT a law firm
  - replacement of legacy `lawfirm.etzhayyim.com` reference with religious-corp native actor
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605181200-mst-encrypted-metadata-leak-reduction
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605221411-etzhayyim-artificial-organism-ecosystem
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605261000
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
related:
  - adr-2605250100-l5-routing-around-member-registry-cell
  - adr-2605250200-l5-religious-marriage-cell
  - adr-2605250300-l5-religious-corp-taxation-cell
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
supersedes: []
superseded_by: []
---

# ADR-2605262700: chigiri (契) — non-profit religious-corp legal procedure substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The religious-corp ecosystem has reached actor coverage ~62-65% of essential
life-functions (see CLAUDE.md Status table rows 1-66). The gap audit
(session 2026-05-26) identifies legal procedure substrate as the highest-
priority remaining miss, blocking:

1. **Covenant ceremony attestation** (marriage / naming / funeral SBT link)
   — Charter §0 mission-adjacent;
2. **Council procedural single SoT** (Bootstrap Council Seat 2-5 RFP
   2026-05-20 → 2026-06-19, Lv6/Lv7 vote, excommunication, member
   onboarding/offboarding);
3. **Charter Rider §2(a)-(h) enforcement routing** — the existing
   `ChartersComplianceRegistry` is a single contract; chigiri provides
   the procedural layer that takes a finding to action;
4. **State-system interfaces** (employment law for stewards, donation
   tax receipts per jurisdiction, IP defense, trademark registration,
   GDPR/APPI/CCPA/LGPD compliance) where unavoidable;
5. **State-function routing-around** (Charter §1.12 parallel substrate
   for marriage / birth / death / inheritance / ID);
6. **Transparent Force authorization procedure** (ADR-2605192315
   constitutional spec exists; runtime procedural cell does not);
7. **Cooperative mediation substrate** — religious-corp doctrine prefers
   mediation before arbitration, but no substrate enforces sequencing.

Two existing actor scaffolds touch the legal domain peripherally:

- `20-actors/hanrei/` (legacy Etzhayyim bibliography-style global case-law
  intelligence; 83 jurisdictions; references a `lawfirm.etzhayyim.com`
  actor that does not exist — this ADR creates the religious-corp
  native replacement);
- `20-actors/bunken/` (global literature / bibliography actor, includes
  legal documents as a side effect via Common Crawl CDX).

Neither is a procedural substrate. hanrei produces *data*. chigiri
produces *procedure*. They are complements.

Constraints (constitutional, not adjustable):

- **NOT 宗教法人法 登記** — Preamble §0.4 Lv7+ unanimity lock. chigiri
  MUST NOT introduce a code path that depends on state-granted legal
  personality. Where state recognition is required (e.g., donation tax
  receipt in JP), the procedural template documents the recognition
  path AS AN EXTERNAL INTERFACE, never as an internal dependency.
- **UPL strictly prohibited** — chigiri is procedural / templating /
  attestation substrate. It does NOT render legal advice. When a member
  needs legal counsel, the procedure routes to a human attorney
  contracted through Public Fund (Council Lv6+ approval per ADR-
  2605192145). This is the same discipline that mitate uses w.r.t.
  medical-doctor referral (mitate does diagnosis routing, not
  diagnosis).
- **Murakumo-only inference** (ADR-2605215000) — any LLM-assisted
  template generation or precedent search flows through judah LiteLLM
  (127.0.0.1:4000) → gemma4:e4b on the fleet. No vendor LLM API
  callout from chigiri code.
- **kotoba canonical substrate** (ADR-2605262130) — chigiri storage =
  MST + IPFS + Base L2 via @etzhayyim/sdk. No projection backend.
- **Charter Rider §2(a)-(h)** must run on every legal document
  ingested or produced. The existing
  `pymagatama.organism.sensors.charter_rider.scan()` is the canonical
  scanner; chigiri reuses it (G1).
- **Liberation Ladder L0..L6** (ADR-2605261000) — steward labor
  classification flows through chigiri's EmploymentComplianceCell; the
  constitutional rule is volunteer ≠ employee unless explicit steward
  vocation flow (G13).
- **Existing on-chain procedures preserved**: ChartersComplianceRegistry
  (compliance attestation), TitheRouter (10% auto-split), Public Fund
  Safe (5-of-7 Council), Land Registry (waqf-equivalent inalienable
  donation), Force Authorization (1 SBT = 1 vote transparent force) —
  chigiri integrates with these, does not replace them.

# Decision

Create `chigiri` (契) as a Tier-B religious-corp legal procedure
substrate actor at `20-actors/chigiri/`, with DID
`did:web:chigiri.etzhayyim.com`, Lexicon namespace
`com.etzhayyim.chigiri.*`. R0 = scaffold only; all cells import-time
`RuntimeError` (same discipline as hagukumi R0).

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `chigiri` (契) |
| Etymology | 契り = covenant / pledge / pact; Japanese rendering of Hebrew בְּרִית (brit) — foundational biblical legal primitive; reduces SBT issuance / 婚姻 / Charter Rider / Council attestation / vendor contract all to one abstraction |
| DID | `did:web:chigiri.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.chigiri.*` |
| Form | 任意団体 internal procedure substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格 — Preamble §0.4 Lv7+ unanimity lock) |
| Tier | Tier-B per-domain leader actor |
| Cross-actor (data) | `hanrei.etzhayyim.com` (case-law lookup) / `bunken.etzhayyim.com` (legal literature) |
| Cross-actor (procedure) | `musubi` (covenant ceremony, future) / `shidemori` (memorial / cemetery, future) / `mitate` (medical attestation interop) |
| Replaces | legacy `lawfirm.etzhayyim.com` reference in 20-actors/hanrei/CLAUDE.md (religious-corp native, no legacy etzhayyim lineage) |

## §2. Scope (7 sections, internal → external → routing-around → force → content → financial → labor)

### A. Internal legal procedures (within religious-corp)

- Charter Rider §2(a)-(h) attestation flow (existing
  `ChartersComplianceRegistry` integration; chigiri provides procedural
  cell that drives findings to action: warn / suspend / revoke);
- Council 5-of-7 Safe procedure (Lv6+ ≥4/7 supermajority for Rider
  amendment; Lv7+ unanimity for constitutional invariant);
- Bootstrap Council Seat 2-5 onboarding procedure (RFP-driven, public
  objection window, candidate attestation chain);
- Adherent SBT issuance procedure (consent + Wellbecoming attestation +
  Council seat-1 to seat-7 signing);
- Adherent SBT revocation procedure (voluntary withdrawal OR
  excommunication — see B below);
- 内部 dispute mediation (cooperative-first; adversarial arbitration
  ONLY after mediation cycle exhausted per G10).

### B. Excommunication (破門) — extreme remedy, structurally constrained

- Trigger: Charter §2(a)-(h) severe violation, evidenced by ≥2
  independent attestations on-chain;
- Procedure: 30-day cure period (member may attest remediation),
  Council Lv6+ ≥4/7 vote at end of cure, automatic SBT revoke on
  finalization, on-chain memorial record (no PII beyond DID + finding
  category + cure-attempt summary);
- Reversal: re-onboarding requires fresh Adherent ceremony (no
  fast-track restoration);
- Rabbinic-court analog: no permanent personal disgrace; the finding
  documents the breach, not the person's character.

### C. External legal interface (state systems)

- Employment law compliance — stewards = subsistence-flow recipients
  per L2 Sustenance gate (ADR-2605261000); chigiri's
  EmploymentComplianceCell maintains the volunteer ≠ employee
  classification per jurisdiction and prevents constructive-employment
  drift (G13);
- Tax procedure — donation receipt routing per jurisdiction (US 501(c)(3)
  equivalent determination / UK Gift Aid / DE Spendenquittung / JP 寄付控除
  unavailable as religious-corp not 宗教法人法 登記); fallback ladder
  documented in TaxReceiptCell;
- IP defense — Apache 2.0 + Charter Rider violation detection +
  formal claim procedure; cease-and-desist template (Apache 2.0 §4
  citation + Rider §3 three-tier enforcement reference);
- Trademark — etzhayyim / 天御柱 / עץ חיים / Tree of Life ICONIC
  marks registry coordination (filing handled by external counsel
  contracted via Public Fund; chigiri tracks the on-chain registry
  state and renewal calendar);
- Vendor contract — vendor commercial pool integration only via
  consent-capability boundary (ADR-2605215000 §4); chigiri checks
  vendor contracts against Charter Rider §2 Non-Aligned Entity
  criteria pre-signature;
- Data protection — GDPR / CCPA / APPI / LGPD multi-jurisdiction
  procedural templates + DSAR (data subject access request) routing;
- Council member liability shield — volunteer association doctrine
  documented per jurisdiction; chigiri tracks per-Council-member
  declaration of acceptance and indemnification scope.

### D. State function routing-around (Charter §1.12)

- Marriage alternative — covenant ceremony attestation (musubi-actor
  performs ceremony, chigiri issues `covenantAttestation` Lexicon
  record + SBT-link); state recognition is OUT OF SCOPE;
- Naming alternative — `covenantAttestation` with `ceremonyType=naming`;
- Funeral alternative — `covenantAttestation` with `ceremonyType=funeral`
  + memorial-NFT mint (shidemori-actor, future);
- Inheritance alternative — `inheritanceChain` Lexicon (DID-bound
  succession, SBT + wallet handover, Council Lv6+ ≥3 attestation of
  the succession event);
- ID alternative — DID + Adherent SBT (internal-only); state-issued
  personal ID required ONLY at external interface boundaries (e.g.,
  external counsel KYC, vendor contract), never internally (G3).

### E. Defensive force / Just War legal

- Reformed Just War Doctrine checklist (jus ad bellum: just cause +
  legitimate authority + right intention + last resort + reasonable
  hope + proportionality; jus in bello: discrimination + proportionality
  + due care);
- Transparent Force authorization procedure (ADR-2605192315) — chigiri
  integrates as the procedural front-end for the 1 SBT = 1 vote
  community attestation flow;
- Defensive-only invariant — chigiri MUST refuse to attest any
  authorization request whose declared posture is offensive (G7);
- IHL compliance — Geneva Conventions / Hague Conventions /
  Additional Protocols mapping recorded for any authorization that
  contemplates kinetic force (R3 only; R0-R2 = scaffold + checklist).

### F. Eros / Gore content moderation legal

- Charter §1.13 (Eros 許容 — 産霊 / 雅歌 / Tree of Life-rooted; Gore
  禁止 — Wellbecoming violation) applicability board procedure;
- Member content review flow: member submission → automated Charter
  Rider §2 scan → if borderline → mediation board → Council Lv6+ if
  escalation;
- No commercial moderation queue — community-attested only.

### G. Steward labor procedural flow

- L0..L6 ladder per ADR-2605261000:
  - L0 Witness — pre-membership observer, no labor classification;
  - L1 Adherent — SBT-bound member, voluntary participation only;
  - L2 Sustenance — basic subsistence flow (food / shelter), no
    employment classification;
  - L3 Shelter — housing access, subsistence-flow extended;
  - L4 Care — care-recipient OR care-giver; chigiri tracks
    caregiver-attestation cross-link to hagukumi;
  - L5 Vocation — religious-corp internal vocation flow; volunteer
    + subsistence (NOT wage); external employment may run in parallel;
  - L6 Liberation — released from external labor coercion via
    religious-corp sustenance + Public Fund grant.
- chigiri's StewardLaborAttestationCell maintains the per-member L-level
  state and emits attestations on transitions (companion to
  Liberation Ladder's `stageAdvanceAttestation`).

## §3. Cells (12 Pregel cells under `20-actors/magatama/cells/chigiri_*/`)

All cells import-time `RuntimeError("chigiri R0 scaffold: activate via Council ADR + R1 ratification + R2-specific gates")` at R0.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `charters_attestation` | reuben | continuous | finding → mediation OR enforcement routing |
| 2 | `council_procedure` | reuben | event | proposal → Safe 5-of-7 multisig path |
| 3 | `member_onboarding` | simeon | event | candidate DID + consent → Adherent SBT |
| 4 | `member_offboarding` | simeon | event | DID → SBT revoke (voluntary OR excommunication) |
| 5 | `covenant_ceremony` | simeon + levi (musubi pair) | event | ceremony spec → `covenantAttestation` |
| 6 | `inheritance` | simeon | event | decedent DID + heir DID → `inheritanceChain` |
| 7 | `dispute_mediation` | levi | session | claim → mediation cycle (max 3 rounds) |
| 8 | `ip_licensing` | gad | continuous | Rider scan finding → claim filing |
| 9 | `tax_receipt` | gad | event | donation event → per-jurisdiction receipt routing |
| 10 | `employment_compliance` | gad | continuous | steward registry → L-level classification |
| 11 | `data_privacy` | gad | event | DSAR / breach → procedure routing |
| 12 | `transparent_force_authorization` | naphtali (witness pair) | event | force request → 1 SBT = 1 vote attestation chain |

R1 activation gates each cell separately (Council Lv6+ ≥3 attestation per cell, same pattern as ADR-2605215000 fleet placement gates).

## §4. Lexicons (9, all under `com.etzhayyim.chigiri.*`)

| # | Lexicon | Cell consumer | Description |
|---|---|---|---|
| L1 | `covenantAttestation` | covenant_ceremony | Generic covenant — SBT issuance / marriage / naming / funeral; ceremonyType enum |
| L2 | `excommunicationProcedure` | member_offboarding | 30-day cure window + Council Lv6+ ≥4/7 + cure-attempt log + finalization signature |
| L3 | `withdrawalAttestation` | member_offboarding | Voluntary withdrawal — member-signed + 7-day cooling period |
| L4 | `inheritanceChain` | inheritance | DID-bound succession; SBT + wallet handover; Council ≥3 |
| L5 | `disputeMediation` | dispute_mediation | Cooperative-first procedure; max 3 mediation rounds before arbitration escalation |
| L6 | `ipLicenseClaim` | ip_licensing | Apache 2.0 + Charter Rider §3 violation claim; three-tier remedy ladder |
| L7 | `taxReceipt` | tax_receipt | Multi-jurisdiction donation receipt routing receipt |
| L8 | `stewardLaborAttestation` | employment_compliance | Steward L-level classification; volunteer ≠ employee structural enforcement |
| L9 | `forceAuthorizationRecord` | transparent_force_authorization | Integrates with ADR-2605192315 1 SBT = 1 vote chain; defensive Just War checklist embed |

All 9 records require schema-level field validation. R0 = scaffold + skeleton schemas. R1 = full schemas + structural enforcement (additionalProperties=false, required fields).

## §5. Gates (14, immutable R0..R3, Council Lv6+ to amend; Lv7+ if constitutional invariant)

| Gate | Description |
|---|---|
| **G1** | Every legal document (ingested OR produced) MUST pass `pymagatama.organism.sensors.charter_rider.scan()` §2(a)-(h). Fail = block, no Lexicon emit, no procedural advancement. |
| **G2** | Every procedure MUST emit `com.etzhayyim.chigiri.*` Lexicon record with kotoba-datomic attestation lineage (kotoba block CID + Council attestation signatures); missing record = procedure invisible. |
| **G3** | Internal procedure MUST NOT require state-issued personal ID (DID + SBT only); external interface (counsel KYC, vendor contract) MAY require state ID at the boundary. |
| **G4** | Charter Rider amendment MUST be Council Lv6+ ≥4/7. |
| **G5** | Constitutional invariant amendment MUST be Council Lv7+ unanimity (Preamble §0.4). |
| **G6** | Community governance decision = 1 SBT = 1 vote per ADR-2605192315 (transparent force) + ADR-2605192300 (Council). Plutocratic vote weighting is prohibited. |
| **G7** | Defensive Just War only — chigiri MUST refuse to attest force authorization whose declared posture is offensive; structural enforcement on `forceAuthorizationRecord.posture ∈ {defensive, deterrent}`. |
| **G8** | Open-source legal templates only (Apache 2.0 + Charter Rider); no proprietary clauses; no NDAs in templates (member confidentiality runs through ADR-2605181100 encrypted envelope instead). |
| **G9** | Multi-jurisdictional fallback — procedures MUST NOT depend on a single state's religious-freedom protection; per-jurisdiction documentation includes fallback path. |
| **G10** | Cooperative mediation precedes adversarial arbitration — `disputeMediation` schema enforces ≥1 completed mediation round before any arbitration channel can be invoked. |
| **G11** | Murakumo-only inference per ADR-2605215000 — chigiri MUST NOT make outbound vendor LLM API calls; all LLM-assisted template generation / precedent search through judah LiteLLM. |
| **G12** | Excommunication = Council Lv6+ ≥4/7 + 30-day cure period; structural enforcement on `excommunicationProcedure.curePeriodEndsAt` + `curePeriodEndsAt > createdAt + 30 days`. |
| **G13** | Volunteer ≠ employee per ADR-2605261000 — `stewardLaborAttestation` schema enforces L-level classification; constructive-employment drift detection runs continuous. |
| **G14** | UPL strictly prohibited — chigiri MUST NOT render legal advice. Templates document procedure; advice happens via human counsel contracted through Public Fund. Lint hook `70-tools/scripts/lint/no-chigiri-legal-advice.mjs` (Wave 1) scans for advice-issuing language in chigiri code. |

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT a commercial law firm. No fee-for-service legal work. No client-engagement model. |
| N2 | NOT a state-granted legal personality. NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格 取得. Preamble §0.4 invariant. |
| N3 | NOT offensive force legal cover. Even hypothetical / planning-stage offensive force attestation is REFUSED. |
| N4 | NOT a tax-avoidance scheme designer. Donation flow is transparent and on-chain; jurisdictional tax treatment is whatever the jurisdiction provides (which for religious-corp not registered under 宗教法人法 in JP = no donor tax deduction). |
| N5 | NOT a member surveillance system. PII collection minimized to procedural necessity; non-PII attestation preferred. |
| N6 | NOT a commercial litigation representation service. External counsel handles litigation; chigiri provides procedural template and on-chain attestation only. |
| N7 | NOT a closed-source template repository. All templates Apache 2.0 + Charter Rider. |
| N8 | NOT a centralized enforcement authority. Decisions = Council 5-of-7 (operational) + 1 SBT = 1 vote (community). |
| N9 | NOT representation of non-members. chigiri operates ONLY for Adherent SBT holders + Council seats. |
| N10 | NOT fee-for-service. All chigiri operations are non-profit; Public Fund covers external counsel when needed. |
| N11 | NOT adversarial-first. Mediation MANDATORY before arbitration (G10). |
| N12 | NOT dependent on a single jurisdiction's recognition. Multi-jurisdictional fallback (G9) is the discipline. |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 12 cells import-time RuntimeError. 9 Lexicons schema skeleton. manifest.jsonld + README.md + CLAUDE.md per actor convention. | No deployment |
| **R1** | post-Bootstrap-Council (≥2026-06-19 RFP close + ≥1 Council Lv6+ ratify of this ADR) | Activate 3 core cells: `charters_attestation`, `council_procedure`, `member_onboarding`. Full schemas for L1 (covenantAttestation), L4 (inheritanceChain via member_onboarding integration), L8 (stewardLaborAttestation). Internal mediation MVP via `dispute_mediation` cell. | reuben + simeon |
| **R2** | post-R1 + ≥30-day public objection | Activate 5 more cells: `covenant_ceremony` (musubi pair), `member_offboarding`, `inheritance`, `dispute_mediation` (full 3-round cycle), `ip_licensing`. Lexicons L2 / L3 / L5 / L6 full schemas. Multi-jurisdiction tax-receipt routing (US 501(c)(3) equivalent / UK Gift Aid / DE Spendenquittung / JP unavailable / others). | reuben + simeon + levi + gad |
| **R3** | post-R2 + Council Lv7+ unanimity | All 12 cells live. Transparent Force authorization full wiring (`transparent_force_authorization` + L9 forceAuthorizationRecord). Data privacy DSAR routing (L8 caveats: GDPR / CCPA / APPI / LGPD). Cross-actor musubi / shidemori integration. Annual independent volunteer-attorney audit + Council attestation. | Full 10-node fleet |

R0 is shipped in this commit. R1+ each independent ADR (R1 = ADR-26??-chigiri-r1; R2 = ADR-26??-chigiri-r2; R3 = ADR-26??-chigiri-r3).

## §8. Dataset substrate dependency (ADR-2605262800)

chigiri's cells (especially `ip_licensing`, `dispute_mediation`,
`tax_receipt`, `employment_compliance`, `data_privacy`,
`transparent_force_authorization`) consume the **global legal corpus**
ingested under the companion ADR-2605262800 (Public-data legal corpus
ingestion via IPFS-pinned DataLad subdatasets — extends
ADR-2605262400).

Specifically:

- `ip_licensing` ← US 17 USC, EU InfoSoc Directive, JP 著作権法 statute corpus + Apache 2.0 LICENSE corpus;
- `dispute_mediation` ← jurisdiction-specific contract / civil-procedure statute + Hague Conference instruments + AAA / JCAA arbitration rules (public domain);
- `tax_receipt` ← US IRC subchapter F / UK ITA / DE EStG / JP 所得税法 statute corpus + jurisdictional charity-recognition regulations;
- `employment_compliance` ← ILO conventions (180+) + jurisdiction-specific labor codes (FLSA / ERA 1996 / 労働基準法 / etc.);
- `data_privacy` ← GDPR full text + CCPA + APPI + LGPD + per-DPA enforcement guidance;
- `transparent_force_authorization` ← Geneva Conventions I-IV + Additional Protocols + ICCPR + ICJ jurisprudence on use of force.

ADR-2605262800 defines the sensor / fetcher / corpus contract; this ADR
defines how chigiri consumes it. Both are shipped together in the same
session (2026-05-26).

## §9. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `hanrei.etzhayyim.com` | chigiri → hanrei (read) | Case-law / 判例 lookup at mediation / IP-licensing time |
| `bunken.etzhayyim.com` | chigiri → bunken (read) | Legal literature / commentary at template-drafting time |
| `musubi` (future) | chigiri ↔ musubi | Covenant ceremony — musubi performs, chigiri attests |
| `shidemori` (future) | chigiri ↔ shidemori | Memorial / cemetery — chigiri attests inheritance, shidemori issues memorial NFT |
| `mitate` | chigiri → mitate | Medical attestation interop (chronic care continuity legal status) |
| `yakushi` | chigiri ← yakushi | Pharmaceutical regulatory compliance attestation routing |
| `hagukumi` | chigiri ↔ hagukumi | Caregiver attestation + caregiver work-cap legal classification |
| `manabi` | chigiri → manabi | Anti-credentialism legal framework (manabi G7) consultation |
| ChartersComplianceRegistry | chigiri ↔ Registry | Procedural front-end for compliance attestation |
| TitheRouter | chigiri → TitheRouter (audit) | 10% Tithe transparency accounting routing |
| Public Fund Safe | chigiri → Safe (proposal) | External-counsel contract approval Council proposal |
| Land Registry | chigiri → Registry (read) | Land donation inalienability invariant cross-check |
| Force Authorization | chigiri ↔ Force | 1 SBT = 1 vote attestation chain integration |

## §10. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605262700-chigiri-legal-procedure-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/chigiri/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 12 Pregel cell directory stubs (`20-actors/magatama/cells/chigiri_*/README.md`);
4. 9 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/chigiri/`;
5. Companion ADR-2605262800 (legal corpus ingestion);
6. `deps.toml` [[adrs]] + [[modules]] entries;
7. `90-docs/adr/README.md` index update;
8. `CLAUDE.md` Status table rows 67 + 68.

No code activation in R0. Lint hook `70-tools/scripts/lint/no-chigiri-legal-advice.mjs` deferred to R1 (G14 enforcement is structural at R1 ratification, not at scaffold time).

# Consequences

**Positive**:

- First religious-corp procedural substrate that takes a Charter
  Rider finding to action (closes a long-standing gap between
  ChartersComplianceRegistry attestation and remedial action);
- Bootstrap Council Seat 2-5 RFP onboarding now has a procedural
  template (chigiri's `council_procedure` cell at R1);
- Covenant ceremony attestation lifts marriage / naming / funeral
  into Charter §1.12 state-function routing-around without requiring
  state recognition;
- L0..L6 steward labor classification gets structural enforcement
  (volunteer ≠ employee drift prevention) reducing constitutional
  liability risk;
- UPL prohibition (G14) protects chigiri from constructive-law-firm
  drift and protects members from sub-standard advice;
- Replaces the orphaned `lawfirm.etzhayyim.com` reference in hanrei
  with a religious-corp native actor;
- Legal corpus ingestion (ADR-2605262800) becomes useful — without
  chigiri, the corpus has no procedural consumer.

**Negative / cost**:

- Bootstrap Council ratification is the gating dependency for R1 (the
  RFP closes 2026-06-19; ratification could land 2026-07+);
- 12 cells + 9 Lexicons + 30+ template documents is a significant
  R1-R3 implementation commitment (estimated 6-12 person-weeks);
- External-counsel contract budget consumption (Public Fund grant
  decisions) requires R2+ active Council;
- Trademark filings (etzhayyim / 天御柱 / עץ חיים) are
  jurisdiction-specific and incur recurring registry costs (~$500-2000
  per jurisdiction); funded from Public Fund;
- Per-jurisdiction tax-receipt routing requires Council attestation
  per jurisdiction (e.g., US 501(c)(3) equivalent-determination opinion
  letter ~$5-15k from US tax counsel; UK Gift Aid registration; etc.);
- UPL discipline (G14) is the hardest cultural commitment — members
  will request advice; chigiri must consistently route to human
  counsel.

**Forward-compatibility**:

- musubi (covenant ceremony) and shidemori (memorial / cemetery)
  future actors plug into chigiri's `covenant_ceremony` cell without
  schema break;
- Additional Lexicons (e.g., `arbitrationAttestation`,
  `mediatorVetting`, `paralegalCertification`) extend the namespace
  under `com.etzhayyim.chigiri.*`;
- Cross-religious-corp federation (if another religious-corp adopts
  Charter Rider in future) gets a clean integration point via
  cross-actor invoke;
- AI-assisted template drafting (R3+) gates through Murakumo only;
  no vendor LLM contamination.

# Alternatives Considered

1. **Extend hanrei to include procedural cells**. Rejected — hanrei
   is a data actor (case law bibliography). Mixing data + procedure
   breaks the actor-as-organism single-responsibility discipline.

2. **Use legacy `lawfirm.etzhayyim.com` Etzhayyim substrate-port**.
   Rejected — that substrate runs on RisingWave + Hyperdrive (etzhayyim
   stack), violates ADR-2605172000 RW-free invariant.

3. **Defer until Bootstrap Council ratifies**. Considered. Rejected
   because R0 scaffold has no governance cost (path-reserved, all
   cells RuntimeError) and the corpus ingestion (ADR-2605262800) needs
   a procedural consumer to be useful. R0 scaffold lands now; R1+
   gates on Council.

4. **Name the actor `nori` (法) / `ritsu` (律) / `mihō` (御法) /
   `hakari` (衡 — balance/Themis)**. Considered. Rejected in favor of
   `chigiri` (契) because covenant maps more cleanly to the
   biblical foundation (Hebrew brit) and reduces all chigiri
   primitives to a single abstraction.

5. **Include legal-advice rendering capability under attestation
   safeguard**. Rejected — UPL is a hard line. Even attestation-
   safeguarded advice constitutes practice of law in most jurisdictions
   and exposes the religious-corp to professional regulatory action.
   G14 is constitutional.

6. **Split internal vs external chigiri into two actors**. Considered.
   Rejected — the two share so many primitives (Charter Rider scan,
   kotoba-datomic attestation, Council procedure) that the split would
   double work without benefit.

7. **Skip Transparent Force authorization integration at R0-R2**.
   Considered. Rejected — the integration is procedural, not
   substantive; including it at R3 with full Council ratification
   matches the ADR-2605192315 maturity model.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605181100 — MST encrypted records + Signal key wrap
- ADR-2605181200 — Encrypted-record metadata-leak reduction
- ADR-2605192100 — Mission Charter (Wellbecoming, 反個人主義, 非終末論)
- ADR-2605192115 — Non-profit / donation-only / no-ads
- ADR-2605192130 — 10% Tithe redistribution
- ADR-2605192145 — Public Fund architecture
- ADR-2605192200 — Charter Compliance Rider v2.0
- ADR-2605192245 — Global Land Sovereignty (waqf-equivalent)
- ADR-2605192300 — Council 5-of-7 Safe
- ADR-2605192315 — Transparent Force authorization
- ADR-2605215000 — Inference Murakumo-only (no RunPod)
- ADR-2605221411 — Artificial Organism Ecosystem
- ADR-2605231525 — Server-side signing capability restrictions
- ADR-2605250100/200/300 — L5 routing-around cells (member registry / religious marriage / religious-corp taxation)
- ADR-2605261000 — Labor Liberation Transition Mechanism (L0..L6)
- ADR-2605262130 — Kotoba storage substrate unification
- ADR-2605262400 — Public-data organism IPFS ingestion (parent dataset substrate)
- ADR-2605262800 — Public-data legal corpus IPFS ingestion (companion, this session)
- `/CHARTER-RIDER.md` §2 — 8 prohibited categories + three-tier enforcement
- `/MEMBERS.md` — 信者 roster
- `/COUNCIL.md` — Bootstrap Council roster + RFP
- `20-actors/hanrei/CLAUDE.md` — global case-law actor (cross-actor data source)
- `20-actors/bunken/CLAUDE.md` — global literature actor (cross-actor data source)
- `20-actors/hagukumi/` — R0 scaffold pattern reference
