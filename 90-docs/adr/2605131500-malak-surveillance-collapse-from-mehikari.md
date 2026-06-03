---
id: adr-2605131500-malak-surveillance-collapse-from-mehikari
title: "malak.surveillance — JP police-only mehikari collapsed into international LEA platform"
status: active
doc_type: adr
topic: malak-surveillance-international-collapse
authoritative: true
last_verified: 2026-05-13
authoritative_for:
  - malak.etzhayyim.com surveillance capability cluster (15 NSID)
  - International LEA seed scope (INTERPOL 196 members)
  - cooperation_status filter (prohibited / restricted / standard / unverified)
  - etzhayyim ↔ etzhayyim Japan operating-entity / vendor boundary for surveillance
priority: 8.5
axis: surveillance-capability
weight: 0.85
priority_note: "Phase 0 — live deploy of vertex_malak_surveillance_* + outreach blocked on G1+G2+G3 of PHASE-1-LAUNCH-READINESS.md until 2026-08-01."
depends_on:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605010000
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0095-simplified-3layer-identity-rw-vault
related:
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
supersedes: []
superseded_by: []
notes: |
  Background: original project "mehikari" (眼光り) was scoped as a JP-police-only
  surveillance vendor. 2026-05-13 user directive collapsed it into
  malak.etzhayyim.com (existing cybercrime intelligence platform, m4l4k001) and
  expanded the scope to all INTERPOL member countries. This ADR records
  the resulting design.
---

# Context

Two days of design work (CXO-LEDGER #1-31) produced a JP-police-only
surveillance vendor under the project name "mehikari" with:

- 15 Lexicon NSIDs under `com.etzhayyim.apps.mehikari.*`
- Project directory `60-apps/etzhayyim-project-mehikari/`
- LangGraph chain `langgraph_sales_outreach.py`
- 47-prefecture seed in `60-apps/etzhayyim-project-states/data/gov/jpn/`
- Compliance memo addressed to Japanese law only

A user directive on 2026-05-13 redirected this scope: the platform must
also serve **international law-enforcement agencies (LEAs)** beyond Japan.
The existing `malak.etzhayyim.com` actor already implemented cybercrime
intelligence with `AgencyReferral` lexicon + INTERPOL Notice graph node
(`intel:notice-`) + `ThreatActor` + 19 BPMN-as-actor flows. Adding a new
"mehikari" actor next to malak created two redundant cybercrime-investigation
surfaces with overlapping addressee semantics.

# Decision

**Collapse mehikari into malak.surveillance capability cluster** of the
existing `malak.etzhayyim.com` actor (`m4l4k001`). malak's actor identity, DID,
sensitivity policy (invite-only, TLP:AMBER default), and existing 10
NSIDs are retained. Surveillance becomes a new capability cluster
(8 search + 7 outreach NSIDs) within malak rather than a separate actor.

## 1. NSID rename

15 NSIDs collapsed into `com.etzhayyim.apps.malak.*` namespace with rebrand
where the JP-only "mehikari" naming was generic:

| Old | New | Notes |
|---|---|---|
| `mehikari.registerCamera` | `malak.registerCamera` | camera 系 unchanged |
| `mehikari.ingestClip` | `malak.ingestSurveillanceClip` | clarify domain |
| `mehikari.queryScene` | `malak.queryScene` | unchanged |
| `mehikari.queryPerson` | `malak.queryPerson` | unchanged — warrant-gated |
| `mehikari.reviewMatches` | `malak.reviewSurveillanceMatches` | clarify domain |
| `mehikari.exportEvidence` | `malak.exportSurveillanceEvidence` | distinguish from `exportAgencyReferralPackage` |
| `mehikari.listQueries` | `malak.listSurveillanceQueries` | clarify domain |
| `mehikari.getAuditTrail` | `malak.getSurveillanceAuditTrail` | clarify domain |
| `mehikari.registerProspect` | `malak.registerAgencyProspect` | align with AgencyReferral |
| `mehikari.draftSalesEmail` | `malak.draftAgencyOutreach` | "outreach" matches AgencyReferral lexicon style |
| `mehikari.reviewSalesEmail` | `malak.reviewAgencyOutreach` | same |
| `mehikari.sendSalesEmail` | `malak.sendAgencyOutreach` | same |
| `mehikari.handleInboundReply` | `malak.handleAgencyOutreachReply` | same |
| `mehikari.unsubscribe` | `malak.unsubscribeAgencyOutreach` | same |
| `mehikari.listOutreach` | `malak.listAgencyOutreach` | same |

## 2. International LEA scope expansion

The JP-only `60-apps/etzhayyim-project-states/data/gov/jpn/` seed was
extended with **INTERPOL 196 member NCBs** in
`60-apps/etzhayyim-project-states/data/gov/{cc}/lea.ndjson`:

- Tier 1 (52 entries): INTERPOL HQ (IPSG Lyon + Cybercrime Directorate) +
  Europol + Eurojust + UNODC + FATF + G7 federal LEAs + Five Eyes
  intelligence agencies. Hand-curated.
- Tier 2 (51 entries): G20 + key Asia (KOR/SGP/HKG/IND/BRA/MEX/TUR/ZAF/SAU/
  ARE/IDN/POL/ESP/NLD/ARG/CHN/RUS). Hand-curated.
- Tier 3 (169 entries): remaining INTERPOL members as `status:"stub"`,
  `phase:3` (enriched during Phase 1 by external counsel).
  Generator: `60-apps/etzhayyim-project-states/tools/gen-lea-stubs.py`.

## 3. cooperation_status filter (CRITICAL)

Each LEA carries `cooperation_status ∈ {standard, restricted, prohibited,
unverified}`. The status is aggregated per country by **strictest wins**
(any prohibited → country prohibited; any restricted → country restricted).

| Status | Effect on outreach |
|---|---|
| `prohibited` | Hard-blocked at edge layer + pyzeebe + LangGraph |
| `restricted` | Requires `extra_approver_did` (external counsel sign-off) |
| `standard` | Normal SAFETY_GATES flow |
| `unverified` | Tier 3 stub default; manual review only |

Initial `prohibited`/`restricted` countries (per OFAC + EU sanctions + INTERPOL
suspension records at time of seed): CHN MSS (prohibited), RUS MVD/FSB
(prohibited), IRN, SYR, BLR, MMR, LBY, YEM, AFG, SSD, SDN, IRQ.

## 4. etzhayyim ↔ etzhayyim Japan boundary preserved

The CLAUDE.md root rule survives the rename:

- Operating entity = `etzhayyim`
- Vendor (contractor) = `etzhayyim Japan株式会社`
- Personal-data controller (APPI) = etzhayyim
- Face-template custodian = etzhayyim CLO
- Police agreement counterparty = etzhayyim (etzhayyim Japan disclosed
  as sub-contractor)

# Hard invariants (graph-layer enforcement)

| Invariant | Enforcement layer |
|---|---|
| Face templates stay inside JP on-prem GPU pod | murakumo on-prem placement + protocol-level egress blocks |
| `queryPerson` requires `legalBasis.warrantRef OR enquiryRef` | edge `src/app.ts:preflightGate` + pyzeebe `task_malak_query_person` + LangGraph Conditional edge |
| `exportSurveillanceEvidence` requires `supervisorDid + sectionChiefDid` (two-stage approval) | same three layers |
| `registerAgencyProspect` opt-in source ∈ {exhibition_list,lecture_host,referral,inbound} | same three layers |
| `sendAgencyOutreach` business-hour gate (09:00-17:00 JST weekdays OR scheduleHint=nextBusinessHour) | same three layers |
| Audio stream dropped at ingest | ffmpeg ingest filter |
| Audit log 7-year retention | `vertex_malak_surveillance_audit_event` |
| Soft-delete forbidden for face templates / outreach contacts | hard DELETE + key destruction |

# RW schema

Migration: `30-graph/graph-schema/migrations/20260513140000_vertex_malak_surveillance_lea_org.ts`

5 vertex + 1 edge + 14 idx + 2 MV:

```
vertex_malak_surveillance_lea_branch
vertex_malak_surveillance_prefectural_police
vertex_malak_surveillance_police_station
vertex_malak_surveillance_koban
vertex_malak_surveillance_org_contact      -- AES-256-GCM ciphertext + wrapped_key + kid
edge_malak_surveillance_lea_hierarchy
mv_malak_surveillance_jpn_police_coverage
mv_malak_surveillance_outreach_funnel
```

Briefing graph (CXO #37): `30-graph/graph-schema/migrations/20260513150000_vertex_malak_briefing.ts`

4 vertex + 6 edge + 21 idx + 2 MV. See ADR-2605131600 for the LangGraph
chain that populates them.

# Phase gate

Live RW apply is blocked on three gates (PHASE-1-LAUNCH-READINESS.md):

- **G1**: Kunal CLO triage of COMPLIANCE-MEMO §2 Q1-Q10 + SCRAPE §S1-S8 +
  sales templates K1-K8 / KE1-KE8 (deadline 2026-06-01)
- **G2**: External counsel onboarding for [BAR-JP] items (deadline 2026-07-15)
- **G3**: etzhayyim board approval for B2G surveillance launch (deadline 2026-08-01)

Phase 1 launch target: **2026-08-01**.

# Alternatives considered

## A. Keep mehikari as a separate actor next to malak

- Pros: clean separation, independent deploy
- Cons: two cybercrime-investigation surfaces, addressee semantics overlap,
  international scope would require duplicating malak's INTERPOL Notice
  graph + AgencyReferral lexicon. **Rejected** — redundant cost.

## B. Demote malak to subordinate role under mehikari

- Pros: surveillance was newer code with fewer entrenched deps
- Cons: malak had ~3 weeks of live operational evidence (Takahashi case,
  CXO #18-31) and existing 10 NSIDs in production. **Rejected** — would
  destabilise live evidence chain.

## C. Make a new "lea" / "police" top-level actor housing both

- Pros: cleanest naming
- Cons: requires new DID + new appview + new BPMN registry; the existing
  malak DID already published threat intel records that downstream
  consumers track. **Rejected** — DID stability cost too high.

# References

- CXO-LEDGER #32 — collapse decision + rename batch
- CXO-LEDGER #33 — wrangler deploy `Version 22ad3cd6-de51-4ed9-962c-2c8dd037a43e`
- CXO-LEDGER #34-35 — 15 stub handlers + pyzeebe wire
- CXO-LEDGER #37 — graph-native briefing chain
- CXO-LEDGER #40 — orchestration pivot (see ADR-2605131600)
- CXO-LEDGER #41 — INTERPOL IPSG EN briefing dry-run
- CXO-LEDGER #42 — EN agency outreach templates
- CXO-LEDGER #43 — JP/EN bilingual landing
- `_working/malak/surveillance/PHASE-1-LAUNCH-READINESS.md`
- `_working/malak/surveillance/MURAKUMO-DOMESTIC-CONSTRAINT.md`
- `_working/malak/surveillance/COMPLIANCE-MEMO.md` (Kunal CLO triage register)
