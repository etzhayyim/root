---
id: adr-2606021600-ooyake-world-government-atlas
title: "ADR-2606021600: ooyake 公 — kotoba-Datomic world government atlas (country→省庁→局→課→窓口) with 住所/窓口/書式/手続き/BPMN, observational-mirror Tier-B actor R0"
status: proposed
doc_type: adr
topic: ooyake-world-government-atlas
authoritative: true
last_verified: 2026-06-02
priority: 7.0
axis: architecture
weight: 0.7
priority_note: "Canonical read-side government-unit SSoT consumed by danjo / kanae / tsumugi / toritsugi / himotoki; amends the ADR-2605242330 §2 per-unit-enumeration non-goal into a bounded read-side civic atlas"
authoritative_for:
  - ooyake actor (world government-unit atlas / civic wayfinding map)
  - gov-atlas kotoba ontology (:gov.unit/* :gov.address/* :gov.window/* :gov.form/* :gov.procedure/* :gov.bpmn/*)
  - per-unit civic-atlas DID scheme (did:web:etzhayyim.com:gov:<iso3>:...) — observational mirror
  - government 住所 / 窓口 / 書式 / 手続き / BPMN structural catalog
depends_on:
  - adr-2606011000-engi-organism-ontology-and-musubi-knowledge-graph
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605212100-gov-five-layer-taxonomy
  - adr-2606013800-actor-profile-and-dynamic-did-json
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605312030-toritsugi-government-procedure-concierge-tier-b-actor-r0
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605302300-kanae-fiscal-flow-visualization
  - adr-2606011800-tsumugi-spirit-intel-power-graph
  - adr-2605302130-himotoki-disclosure-request-tier-b-actor-r0
  - adr-2605242330-gov-procedure-pregel-mcp-coverage
  - adr-2605250680-etzhayyim-gov-coverage-maturity-score
supersedes: []
superseded_by: []
---

# ADR-2606021600: ooyake 公 — kotoba-Datomic world government atlas

**Status**: proposed (R0 design + schema + unverified-seed proof-of-model; live ingest Council + operator gated)
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

The founder asked (2026-06-02): *「今の actor で全世界の政府、自治体、省庁単位までの actor の設計と
…profile, xrpc はできている？住所、窓口、書式、手続き、bpmn などもすべて 設計, 公開されている?」* — is
there, across the existing actors, a design covering **every world government / municipality / ministry down
to the unit level** as an atproto actor (profile + XRPC), with **住所 (address) / 窓口 (service window) /
書式 (form) / 手続き (procedure) / BPMN** all designed and published?

The honest finding (investigation 2026-06-02):

- The six government-facing actors — **danjo** (watch the state), **kanae** (fiscal-flow viz), **toritsugi**
  (citizen procedure concierge), **moushibumi** (democratic-participation concierge), **himotoki** (DSAR/FOIA),
  **tsumugi** (power-graph) — are all **observers/agents about** governments. **None is a per-government-unit
  catalog.** All are R0.
- A **legacy F-Plan scaffold** exists: `00-contracts/bpmn/com/etzhayyim/gov<ISO3>/` (196 country dirs,
  ~1,574 BPMN **stubs** with generic `listOrgs`/`registerDIDs`/`resolveOrgPath`/`seedOrgs` tasks in the legacy
  `com.etzhayyim.gov*` namespace) + `90-docs/openapi/gov*.openapi.json` (141 skeleton specs). These are **bootstrap
  stubs** — no real units, addresses, windows, forms, procedures, or DIDs behind them.
- **toritsugi** holds a **6-entry** JP procedure seed (`registry/procedures.seed.json`, all
  `unverified-seed`). No address dataset, no window registry, no form catalog, no executable BPMN exist for any
  jurisdiction.
- ADR-2605242330 §2 explicitly set **per-unit global enumeration as a NON-GOAL**, framing gov coverage as
  read-side observability + narrow routing-around.

So the "all world governments down to unit level, each an actor with full address/window/form/procedure/BPMN"
vision was **aspirational, not built** — and partly **out of scope** by the prior ADR.

The founder has now directed building it, on the **EDN / kotoba / Datomic** premise. This ADR establishes the
substrate and **amends the scope**: a per-unit world government **atlas** is admitted as a **read-side civic
asset**, consistent with the religious-corp mission (it is the same read-side posture as danjo/tsumugi/kanae —
*observe and map*, never *operate the state*). It is **not** the routing-around concern that ADR-2605242330 §2
declined.

# Decision

Create **ooyake 公** — a Tier-B actor that is the canonical, content-addressed **structural atlas of every
government unit on Earth**, kotoba-Datomic-native, each unit carrying its 住所 / 窓口 / 書式 / 手続き / BPMN,
and each resolvable as a **civic-atlas mirror** atproto actor (profile + read XRPC).

- **Glyph / handle**: 公 / `ooyake`. DID: `did:web:ooyake.etzhayyim.com`.
- **名 (ooyake = the public / officialdom)**: the atlas of all public bodies — the read-side SSoT that danjo,
  kanae, tsumugi, toritsugi and himotoki all consume for "who / where / how" of public administration.

## §1 — Posture: observational mirror, civic wayfinding (constitutional)

ooyake is a **map of the state for citizens to find services**, in exactly the posture of tsumugi (*"an
accountability map, NEVER a target-list"*) and watatsuna (*"a resilience map, NEVER a target-list"*).

- It is **NOT** an official channel, **NOT** any government, and **never** impersonates one (§2(c)).
- Per-unit DIDs use a clearly-namespaced **civic-atlas mirror** scheme
  `did:web:etzhayyim.com:gov:<iso3>[:<level>:<code>]...` whose DID-document `alsoKnownAs`/`_meta` declares it an
  **etzhayyim observational mirror of a real public body**, linking to the body's `official-url` (and its
  `official-did` if the body publishes one). ooyake mirrors; it never mints a DID *as* the government and never
  accepts/issues anything on the government's behalf.
- ooyake is **read-only**: it catalogs. It **never files, submits, or mutates** a government record — that is
  toritsugi's gated concern. It **never audits/adjudicates** — that is danjo's.

## §2 — Scope amendment to ADR-2605242330 §2

ADR-2605242330 §2 declined *per-unit global enumeration* as conflating observability with routing-around. This
ADR **narrows that non-goal**: per-unit enumeration is admitted **only as a read-side civic atlas** (structure +
contact + wayfinding). Routing-around (L5) remains out of ooyake's scope and stays governed by the Transparent
Force discipline. The legacy `gov*` country BPMN/OpenAPI stubs and the L1–L4 COFOG taxonomy are **subsumed** by
ooyake's `:gov.*` graph as their kotoba-native canonical owner (the `com.etzhayyim.gov*` → `com.etzhayyim.ooyake.*`
rename is itemized for the gated Step-8 `etzhayyim-*` cutover, NOT executed here — root CLAUDE.md §Do-Not).

## §3 — Substrate (kotoba EDN / Datomic)

- **Ontology**: `00-contracts/schemas/gov-atlas-ontology.kotoba.edn` — six vocabularies:
  `:gov.unit/*` (recursive administrative tree), `:gov.address/*` (住所), `:gov.window/*` (窓口),
  `:gov.form/*` (書式), `:gov.procedure/*` (手続き), `:gov.bpmn/*` (process model).
- **First-class state**: the kotoba Datom log (ADR-2605312345). Hierarchy is `:gov.unit/parent` refs; queries
  run over EAVT/AVET/VAET arrangements (`getUnit`, `resolvePath`, `findService`, `searchUnits`). No Kotoba/Datomic,
  no projection layer (ADR-2605262130).
- **Reconciliation**: `:gov.unit/organism` links each unit to its engi-organism node (ADR-2606011000) so
  tsumugi's 縁/取 power-graph and ooyake's structural atlas share entities (atlas = structure; engi = karma).
  `:gov.unit/external-code` + `:gov.unit/wikidata` reconcile against JP 行政機関コード / 全国地方公共団体コード /
  ISO-3166-2 / GeoNames / Wikidata.
- **Procedure boundary**: `:gov.procedure/toritsugi-ref` points each procedure at toritsugi's existing
  `com.etzhayyim.toritsugi.procedure` registry — **ooyake catalogs (who/where/structure), toritsugi delivers
  (guide/draft/submit/track)**. No duplication.
- **Forms**: `:gov.form/chigiri-ref` points at chigiri's UPL-bounded fillable templates; ooyake only points.

## §4 — Constitutional gates (immutable; Council Lv6+ + new ADR to amend)

- **G1** Charter Rider §2(a)-(h) scan on every authored artifact + outbound fetch.
- **G2** kotoba attestation lineage on every datom (EAVT; no RW).
- **G3** **Observational mirror only** — civic-atlas DID never claims to BE the gov, never an official channel,
  never issues/accepts on a gov's behalf (§2(c) impersonation ban).
- **G4** **Public-data-only** — only public official sources; respect robots.txt / ToS / rate-limits; no
  behind-auth access; no scraping circumvention.
- **G5** **Non-fabrication** — every unit/address/window/form/procedure carries `provenance` + `last-verified` +
  `sourcing` (`:authoritative` | `:representative`); `:representative` rows are illustrative and **never counted
  as coverage**; procedures must cite `legal-basis`.
- **G6** **No personal data** — government org data only; public role-contact (switchboard, 窓口) only; **never**
  an individual official's private/home contact; data-minimized.
- **G7** Murakumo-only inference (ADR-2605215000).
- **G8** Non-commercial — non-profit; the atlas is a public good; no resale as a data product (Charter Rider
  §2(e)).
- **G9** **Read-side only** — ooyake never files/submits/mutates a government record (→ toritsugi, gated) and
  never audits/adjudicates (→ danjo).
- **G10** **Civic wayfinding, never a target-list** — helps a citizen find a service; never an attack-surface /
  SPOF map of the state (Transparent Force discipline, §1.12). No "weak-point" derivations.
- **G11** Jurisdiction-neutral + politically neutral (no ranking of governments; descriptive only).
- **G12** **Freshness-gated** — stale entries flagged `:stale`; downstream consumers (esp. toritsugi G14) MUST
  re-verify before any citizen-facing action.

## §5 — Cells (Pregel; path-reserved at R0, no deployment)

| Cell | Node | Phase | IO |
|---|---|---|---|
| `unit_registry` | reuben | continuous | maintain/resolve the `:gov.unit/*` tree; enforce sourcing + verification-status |
| `reconcile` | reuben | event | reconcile units vs Wikidata QID / 行政機関コード / 全国地方公共団体コード / ISO-3166-2 / GeoNames (read-only ingest, G4) |
| `address_ingest` | gad | event | ingest 住所 / hours / 窓口 from official sources → `:gov.address/*` + `:gov.window/*` |
| `procedure_link` | gad | event | link `:gov.procedure/*` ↔ toritsugi registry + chigiri templates + `:gov.bpmn/*` |
| `atlas_serve` | naphtali | continuous | serve per-unit civic-atlas profile + read XRPC (`getUnit`/`resolvePath`/`findService`/`searchUnits`) — READ ONLY |
| `freshness` | naphtali | continuous | re-verify within the freshness window; flag `:stale` (G12) |

## §6 — Lexicons (XRPC, read-only)

Records: `com.etzhayyim.ooyake.govUnit` / `.address` / `.window` / `.procedure`.
Queries: `com.etzhayyim.ooyake.getUnit` / `.resolvePath` / `.findService` / `.searchUnits`.
`searchUnits` is the backend for civic search at `etzhayyim.com` (the `/actors` kotoba-wasm search surfaces
ooyake gov units once the gov-atlas graph is published; Phase R1).

## §7 — BPMN

`00-contracts/bpmn/com/etzhayyim/ooyake/`: `resolveUnit.bpmn`, `findService.bpmn`, `reconcileUnit.bpmn` — real
read/ingest flows in the canonical `com.etzhayyim.ooyake.*` task namespace (`:model-only` at R0, no Zeebe engine
deployed). These supersede the legacy `gov*` country stubs as the canonical models.

## §8 — Roadmap

| Phase | Date | Scope | Gate |
|---|---|---|---|
| **R0** | 2026-06-02 | Ontology + manifest + CLAUDE/README/MATURITY + `gov-units.seed.edn` proof-of-model (full JP 財務省→国税庁→東京国税局→麹町税務署 chain + 東京都→新宿区→窓口 + USA/GBR/DEU/KOR/EU country+ministry rows, **all `unverified-seed`**) + 8 lexicons + 3 BPMN. **No cell runs, no live ingest, no served DIDs.** | this ADR (PROPOSED) |
| **R1** | post-Bootstrap-Council + Council Lv6+ ≥3 | `unit_registry` + `reconcile` live; ingest JP authoritative registries (行政機関コード, 全国地方公共団体コード) to `:authoritative`; `atlas_serve` serves `searchUnits`; `/actors` search surfaces gov units | Council Lv6+ ≥3 |
| **R2** | post-R1 | `address_ingest` + `procedure_link`; per-unit civic-atlas did.json served dynamically (kotoba → KV, ADR-2606013800 pattern); findService end-to-end for JP | Council Lv6+ ≥4 |
| **R3** | post-R2 | multi-jurisdiction ingest at scale; GeoJSON footprints; toritsugi/danjo/kanae/tsumugi consume the live atlas | Council Lv6+ ≥4 + 30-day public comment |

# R2 Technical Build — `:gov.procedure/bpmn` realized (2026-07-09, ratify-pending)

This section records the **technical** realization of the R2 `:gov.procedure/bpmn`
flow: the prior STUB `bpmn.ooyake.find-service` placeholder on the matching
`:gov.procedure/bpmn` field (in `registry/gov-units.seed.edn` ×3 +
`registry/gov-units.toritsugi-procedures.seed.edn` ×3) is replaced by **real
citizen-procedure BPMN process models** for the 6 R0 procedures. **ratify-pending**:
this is a technical/modeling completion, not a Council advancement; the sourcing
is still `unverified-seed` / `:representative` and NO live ingest / served DID is
enabled.

**What landed:**

- **`registry/gov-procedures.bpmn.edn`** — 6 BPMN-as-edn process models, one per
  R0 procedure: 住民票の写し交付請求 / 転入届 / 出生届 / マイナンバーカード交付申請 /
  児童手当認定請求 / 確定申告 e-Tax. Each process is DERIVED (G5 non-fabrication)
  from the corresponding `:gov.procedure`'s `{legal-basis, required-docs, fee,
  statutory-days, provenance}` in the seed — the identity-verification step comes
  from required-docs "本人確認書類", the fee-payment step from `:gov.procedure/fee`,
  the statutory waiting window from `:gov.procedure/statutory-days`.
  `:bpmn/legal-basis` and `:bpmn/provenance` are COPIED verbatim from the seed,
  never invented. FORMAT: BPMN-as-edn per **ADR-2607090900**
  (kotoba-lang/org-omg-bpmn / bpmn-clj R1 working `.cljc`).
- **`deploy/resolve_for_toritsugi.py`** — extended to resolve the coded procedure
  record (G14 verified + G8 根拠法令/provenance) AND surface its BPMN process id
  to toritsugi's `resolve` step. toritsugi consumes ooyake's BPMN; it never
  re-authors the government's process (cross-actor boundary, ADR-2605312030).
  Self-test PASS.
- **Seed wiring** — `registry/gov-units.seed.edn` + `registry/gov-units.toritsugi-procedures.seed.edn`
  carry the real `bpmn.ooyake.proc.jpn.*` ids on `:gov.procedure/bpmn` (the STUB
  `bpmn.ooyake.find-service` retired on all 6).

**Consumed by:** toritsugi `registry/toritsugi.procedure-flow.bpmn.edn` — the
`resolve` service-task REFERENCES these ooyake process ids by `:bpmn/gov-procedure-bpmn`
(ADR-2605312030 R1). toritsugi walks the MEMBER through the coded procedure; it
does not re-author it.

**What did NOT change:** the `:authoritative` vs `:representative` sourcing split
(G5) holds; coverage is not silently overstated; no live ingest, no served DID,
no cell runs. R2 Council ratification (Lv6+ ≥4) is still required to serve these
models dynamically.

# Consequences

**Positive**

- A single canonical read-side SSoT for government structure that danjo/kanae/tsumugi/toritsugi/himotoki stop
  re-deriving ad hoc. toritsugi's "where is the 窓口" and tsumugi's "which node" both resolve here.
- Honest, provenance-bearing coverage with an explicit `:authoritative` vs `:representative` split — coverage
  can never be silently overstated (G5).
- Subsumes the orphaned `gov*` BPMN/OpenAPI bootstrap stubs under a kotoba-native owner.

**Negative / risks**

- **Scale**: enumerating every unit on Earth is a multi-year ingest. R0 ships a **proof-of-model seed only**;
  the maturity score (ADR-2605250680, 49.18/100 baseline) governs honest reporting. Coverage claims are gated by
  `sourcing`.
- **Impersonation risk** is the central hazard; G3 + the explicit mirror DID-doc semantics are the mitigation
  and are constitutional invariants.
- **Target-list risk**: G10 forbids any weak-point/SPOF derivation over the state; reviewed like tsumugi/
  watatsuna.

# World-Model Reconcile Layer (`cells/world_model/`, added 2026-06-06)

§3 named `:gov.unit/organism` as the reconcile attr to tsumugi's karma graph, but it was populated by no
unit and joined by no code. The **world-model reconcile layer** closes that — the queryable join of
structure (ooyake `:gov.unit/*`) and karma (tsumugi `:organism/* + :en/*`), offline + deterministic +
read-side (G9). Charter shape unchanged: power-only (G1, local 窓口/ward/division **excluded by
construction** — never a target-list, G10), sourcing-honest (G5), no seed mutation; ZERO invariant amendments.

- **Reconcile** (`reconcile_world_model`): classifies every **power-bearing** unit (country / supranational /
  cabinet / ministry / agency / bureau / legislature / court) as **confirmed** (explicit `:gov.unit/organism`
  whose target organism exists) / **derived** (`gov.X → org.gov.X` already in the karma graph) / **dangling**
  (G5 flag) / **proposed** (`:latent`/`:representative` organism stub + link, written to
  `out/world-model.kotoba.edn`, NEVER to a committed seed). Flags orphan governmental organisms.
- **9 confirmed links** today, all publicly-documented regulator→entity ties: METI, FSA, BOJ, US SEC (a real
  atlas gap, added as `gov.usa.sec`), US Fed, EU, UK CMA, US DOJ Antitrust, JFTC. The rest of the atlas is
  honestly `:proposed`/`:representative` — the world model is mostly unreconciled, which is the honest state.
- **Government-stewardship join** (`government_stewardship`): reconciled gov-unit → its organism →
  `:tends`/`:custodies` 縁 → entity. **20 concrete paths** (e.g. `gov.eu --:tends--> Apple`,
  `gov.usa.sec --:tends--> NVIDIA`). `:depends-on` (the entity's reverse dependency) excluded.
- **Bidirectional query**: `regulators_of(entity)` (reverse: who governs X?) + `stewarded_entities_of(unit)`;
  consumed by tsumugi/danjo/kanae via `deploy/consumers_example.py::world_model_regulators`; CLI
  `scripts/world_model.py --entity <org>`.
- **kotoba persistence**: `deploy/ingest_world_model.py` projects the reconciled (NOT proposed) model into the
  named graph **`world-model-v1`** (`world.gov` entities with `world/organism` + `world/stewards` relations).
  Dry-run default; live ingest operator-gated (`KOTOBA_TOKEN`); never auto-seals.
- **Gates**: `scripts/world_model_coverage.py` (confirmed-floor + expected-set + zero-dangling +
  civic-surface-excluded + zero-orphan + stewardship-floor + well-formed-EDN) + `cells/world_model/
  test_consistency.py` SSoT drift-lock + 16-test cell suite (incl. EDN round-trip), all wired into
  `deploy/run_tests.sh`. Registered as ooyake's **7th cell** (manifest). `live` mode (planet-scale reconcile +
  seed write-back) is Council Lv6+ + operator gated.

# Alternatives Considered

1. **Extend toritsugi** instead of a new actor — rejected: toritsugi is citizen-side *delivery* (guide/submit);
   the atlas is a distinct *read-side structural SSoT* consumed by ≥5 actors. Conflating them violates the
   single-responsibility pattern used across the Tier-B roster.
2. **Extend tsumugi's engi power-graph** — rejected: engi is karma/縁 (`:en/*`, `:grasp/*`); the atlas is
   concrete structure (addresses, windows, forms). They reconcile via `:gov.unit/organism` but are different
   concerns; merging would overload the karma graph.
3. **Keep the legacy `gov*` BPMN stubs as the home** — rejected: they are legacy `com.etzhayyim` namespace, non-kotoba,
   stub-only, and pre-cutover; they become `:gov.bpmn` rows pointing at the new canonical models.
4. **Mint real per-government DIDs** — rejected as unconstitutional impersonation (§2(c)); mirror-only (G3).

# References

- `00-contracts/schemas/gov-atlas-ontology.kotoba.edn` — the ontology (this ADR §3)
- `20-actors/ooyake/manifest.jsonld` · `CLAUDE.md` · `registry/gov-units.seed.edn`
- `00-contracts/lexicons/com/etzhayyim/ooyake/*.json` · `00-contracts/bpmn/com/etzhayyim/ooyake/*.bpmn`
- ADR-2605242330 (scope amended here) · ADR-2605212100 (gov 5-layer taxonomy) · ADR-2605250680 (maturity score)
- ADR-2605312030 (toritsugi) · ADR-2605301600 (danjo) · ADR-2605302300 (kanae) · ADR-2606011800 (tsumugi)
- ADR-2606011000 (engi-organism) · ADR-2605262130 + 2605312345 (kotoba) · ADR-2606013800 (dynamic did.json)
- ADR-2605192100 (mission charter §1.12 Transparent Force) · ADR-2605192200 (Charter Rider) · ADR-2605215000 (Murakumo-only)
