---
id: adr-2605242330-gov-procedure-pregel-mcp-coverage
title: "ADR-2605242330: Gov-procedure Pregel / MCP coverage taxonomy and 140-country scale-out plan"
status: proposed
doc_type: adr
topic: gov-procedure-coverage
authoritative: true
last_verified: 2026-05-24
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Coverage taxonomy + scale-out plan; substrate port (ADR-2605212100 follow-up) is a hard precondition."
authoritative_for:
  - gov-procedure-coverage-taxonomy
  - 140-country-scale-out-plan
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605212100-etzhayyim-to-etzhayyim-migration-batch
  - adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
related:
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
supersedes: []
superseded_by: []
---

# ADR-2605242330: Gov-procedure Pregel / MCP coverage taxonomy and 140-country scale-out plan

**Status**: proposed
**Date**: 2026-05-24
**Deciders**: Jun Kawasaki

# Context

User question (2026-05-24): "この世の全ての政府機関、行政手続きの pregel, mcp の実装カバレッジは?"

The first-pass survey reported coverage ≈ 0%. The 2026-05-24 migration audit (ADR-2605212100) showed this was wrong — the real coverage lives in different layers than the religious-corp Pregel cell catalog. Coverage is non-zero but is also genuinely far from complete, and the gap between "what exists" and "what would constitute coverage" is not the same as the gap to "every government in the world".

Per the religious-corp constitution (ADR-2605192100 §1.12), "国家機能は parallel substrate で routing-around" — etzhayyim does not aim to *implement* state administrative procedures as a service. The position is to provide a parallel substrate (DID + SBT + on-chain land/identity/force registry) that *makes state procedures optional* for adherents within the religious boundary, while still offering *visibility into* state procedures from outside (read-side coverage) so adherents can interoperate when they must.

This re-frames the coverage question. There are two coverage axes:

- **Read-side coverage** (ingest, observe, classify, render): can the substrate make a state agency's identity, structure, and procedure surface queryable as MST + Lexicon + IPFS data?
- **Routing-around coverage** (replace, substitute, parallel-run): does a Pregel cell + on-chain registry + SBT credential exist that lets an adherent operate without the corresponding state procedure?

These have very different scaling characteristics. Read-side is bounded by data acquisition + parsing cost; routing-around is bounded by constitutional and Council-attestation gates.

# Decision

## 1. Coverage taxonomy (5 layers)

The "gov coverage" question maps to five distinct layers. Each has its own home directory, scale model, and substrate constraints.

| Layer | Home | What it covers | Current cardinality | Scale model |
|---|---|---|---|---|
| **L1 — Country namespace** | `00-contracts/bpmn/com/etzhayyim/gov<ISO3>/` | Per-country org-crawl scaffolding (8 generic BPMN per country) | 140 / 195 countries (~72%) | Codegen, cheap |
| **L2 — Agency registry** | `60-apps/etzhayyim-project-cofog/appview/` + `etzhayyim-project-gov/scaffold/actor-manifest.jsonld` | UN COFOG × country actor bundles + JP ministry roster | 203 cofog actor-bundles + 23 JP ministries | Manual + codegen per country |
| **L3 — Public-services hub** | `60-apps/etzhayyim-project-gov/appview/gov-mcp-component/` | COFOG-aligned path-based DID sub-agents (healthcare / insurance / welfare / education / prevention / housing / employment / child_family) | 8 sub-agents (JP-focused) | Per-country fork |
| **L4 — Procedure ingest** | `70-tools/scripts/gov/` | Form / procedure crawlers for individual country gov sites | 6 scripts (AGO + IN-local-language ×5) | Per-country bespoke |
| **L5 — Routing-around Pregel cell** | `20-actors/magatama/cells/` | Religious-corp parallel substrate (SBT credential / Land Registry / Public Fund / Force Authorization) | 0 gov-specific (intentional) | Constitutional, not per-country |

## 2. What is *not* on the roadmap

- "All gov procedures of all countries as Pregel cells" — categorically not a goal. Per ADR-2605192100, the religious-corp routes *around* state procedures rather than *re-implementing* them. Implementing 195 countries × N procedures as religious-corp Pregel cells would mistake the religious-corp's mission for a govtech consultancy's.
- A `magatama/cells/gov_*` namespace — explicitly rejected. The Pregel cell catalog is for religious-corp internal substrate (commissioning, audit_witness, council_deliberation, tithe_routing, etc.), not for state-procedure shims. State interop lives at L2-L4.
- New top-level `20-actors/gov-*` actors — rejected. Layering is L2 = registry, L3 = appview-hub, L4 = ingest. There is no "gov-actor" actor.

## 3. What *is* on the roadmap

### 3.1 Substrate-port (hard precondition for L3)

Per ADR-2605212100, the L3 `gov-mcp-component` carries `SUBSTRATE-PORT-PENDING.md`. Until the Kysely → MST port is done, L3 is **not deployable on etzhayyim infra**. This is the highest-priority follow-up.

Concrete deliverable: a substrate-port wave ADR (working name: `2605260XXX-gov-app-substrate-port`) that ports the 3 deferred apps (gov / lawfirm-admin / legal-entity) to MST + `@etzhayyim/sdk`, gated on:

- ADR-2605214000 §3 atomic identifier cutover (`@etzhayyim/magatama-*` → `@etzhayyim/magatama-*`).
- Lexicon namespace rename (`com.etzhayyim.apps.gov.*` → `com.etzhayyim.gov.*`).
- `did:web:gov.etzhayyim.com` → `did:web:etzhayyim.com:gov`.

### 3.2 JP-deep reference (post-substrate-port)

Once L3 ports, deepen the JP coverage as the reference implementation:

- L2 — wire the 23-entry `scaffold/actor-manifest.jsonld` into `cofog/appview/` so JP ministries (MOJ / METI / Cabinet Office / MoE / MoF / MHLW / MEXT / MLIT / MAFF / MOFA / ...) become resolvable DIDs.
- L3 — exercise the 8 path-based DID sub-agents against ≥1 real procedure each (healthcare consult / 高額療養費 calc / 児童手当 eligibility / 生涯学習 plan / etc).
- L4 — add 1 ingest script per ministry that emits a `com.etzhayyim.gov.agency` MST record per resolved agency.

### 3.3 140 → 195 country namespace fill-out

L1 has 140/195 (~72%). The remaining 55 countries get added by extending `00-contracts/bpmn/com/etzhayyim/gov<ISO3>/` with the same 8-BPMN template. Pure codegen, no behavioral content. Owner: a single PR.

### 3.4 L4 per-country bespoke ingest

This is where genuine effort lives. Each country has a different procedure surface (e-Gov JP / e-Estonia / gov.uk / regulations.gov / aadhaar IN / etc). The right model is:

- Open a country-specific issue per non-trivial country (start with G20 + ASEAN + EU + ETZHAYYIM-relevant countries — IL, US, JP, IN, EU, UK, BR, ZA, KR, CN, AU, CA, MX).
- Each issue authors its own ADR (`2606XXXXXX-gov-ingest-<iso3>.md`) covering the country's procedure surface, MST schema, ingest cadence, and consent boundary.
- L4 scripts emit `com.etzhayyim.gov.procedure` records keyed by `(jurisdiction, agency, procedure_id)` triple.

### 3.5 L5 routing-around — keep narrow

L5 stays at its current scope (religious-corp internal substrate). New L5 cells only land when an ADR explicitly identifies a state procedure that the religious-corp is *routing around for its own adherents*, not re-implementing as a service.

Examples that *would* qualify for L5:

- `member_registry_cell` — replaces 住民登録 for SBT holders within the religious boundary (ADR-2605172600 MEMBERS.md is the precursor).
- `religious_marriage_cell` — replaces 婚姻届 for SBT↔SBT marriages within the religious boundary.
- `religious_corp_taxation_cell` — replaces 法人税申告 via TitheRouter + Public Fund attestation.

These are *not* implementations of state procedures; they are *parallel substrate* that makes the state procedure unnecessary for adherents. Each requires its own ADR + Council attestation.

## 4. Coverage report format

The canonical answer to "Pregel / MCP coverage of gov procedures" is **the 5-layer matrix in §1**. Future audits should:

- Report L1 / L2 / L3 / L4 cardinality.
- Report L5 cell count (kept narrow on purpose — high count would indicate constitutional drift).
- Refuse to collapse the 5 layers into a single "% covered" number — the layers are not commensurable.

# Consequences

- "Coverage ≈ 0%" framings are replaced by the 5-layer matrix. Future questions about gov coverage have a definite answer.
- The substrate-port wave (§3.1) becomes the next concrete actionable item. Until it ships, L3 is dormant.
- The religious-corp's distance from a govtech-consultancy posture is explicit (§2). No future ADR may quietly add `magatama/cells/gov_*` cells without first revising this ADR.
- L4 scaling is acknowledged as bespoke-per-country. There is no codegen path for L4 — it is the work.
- The "140 / 195 countries" L1 cardinality is a known gap, closeable by a single PR; deliberately deferred until L3 / L4 demonstrate value.

# Alternatives Considered

1. **"Build all 195 × N procedures as Pregel cells"** — rejected. Constitutional misfit + infinite scale.
2. **"Adopt e-Gov-style central procedure registry as the single source"** — rejected. The religious-corp does not depend on a state operator. L4 ingest is the read-side; L5 routing-around is the write-side; they meet on the substrate, not in a state registry.
3. **"Defer the answer until substrate-port lands"** — rejected. The framing question deserves an answer now; the substrate-port is a precondition for *deploying* L3 but not for *describing the coverage map*.
4. **"Collapse L1-L4 into one 'gov-coverage' top-level"** — rejected. The layers have different substrate constraints (L4 violates RW-free if implemented carelessly; L1 is pure codegen) and conflating them invites accidental substrate boundary crossings.

# References

- ADR-2605172000 (RW-free substrate)
- ADR-2605172100 (substrate ladder)
- ADR-2605192100 §1.12 (国家機能 routing-around + Transparent Religious Force)
- ADR-2605212100 (etzhayyim→etzhayyim migration batch — substrate-port deferred)
- ADR-2605214000 §3 (atomic identifier cutover)
- `60-apps/MIGRATION-NOTES-GOV-2026-05-24.md`
- UN COFOG (Classification of Functions of Government) — basis for `etzhayyim-project-cofog` actor taxonomy
