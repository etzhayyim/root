# ADR-2606010200 — haraedo 祓戸 — global bulky-waste (粗大ゴミ) disposal actor

- **Status**: Proposed
- **Date**: 2026-06-01
- **Deciders**: Council (Bootstrap Seat 1) — ratification of outward operation pending Seats 2–5
- **Layer**: 20-actors (Tier-B actor) + 40-engine/kotoba (EAVT substrate) + 00-contracts (lexicons)
- **Supersedes / Superseded-by**: —

## Context

Bulky-waste (粗大ゴミ / sperrmüll / bulky-trash / oversized-waste) disposal is a
near-universal municipal service whose **citizen-facing intake** (どの品目が出せる
か・いくらか・いつ出すか・どこに出すか) and **operator-facing logistics** (受付 →
手数料収納 → 収集日割当 → 配車 → 担当者割当 → 収集ルート最適化 → 搬入先処理場
決定) are everywhere fragmented across thousands of incompatible municipal forms,
phone lines, and back-office spreadsheets. The same structural-labor toil the
Charter (ADR-2605192100) targets — opaque, repetitive, jurisdiction-locked
administrative + dispatch labor — recurs in **every one of the world's ~tens of
thousands of local governments**.

etzhayyim already runs the citizen-procedure concierge **toritsugi** (ADR-2605312030)
for general 自治体手続き. Bulky-waste disposal is distinct enough to warrant its own
actor because it is not merely an information/guidance procedure: it is a
**two-sided logistics problem** — a citizen application that must be matched to a
physical collection slot, a vehicle, a crew, an optimized route, and a destination
processing facility with finite daily capacity. It also requires a **global
registry of waste-processing facilities** (位置 / 種別 / 処理能力 / 受入品目) that
no actor currently owns.

Forces:

- **Universality** — bulky-waste service exists in essentially every municipality;
  the model must be jurisdiction-parametric, not JP-only.
- **Two-sidedness** — citizen intake AND municipal operations (受付・配車・ルート・
  担当者) are both in scope, per the request.
- **Physical constraint** — facility daily capacity, accepted categories, vehicle
  capacity, crew shifts and certifications, and route distance are hard constraints,
  not advisory text. They belong in the kotoba EAVT graph as queryable facts.
- **Substrate invariants** — state MUST live in the kotoba Datom log (ADR-2605312345);
  inference MUST be Murakumo-only (ADR-2605215000); fees MUST NOT use fiat
  processors (substrate boundary); PII MUST be encrypted + DID-bound (ADR-2605181100).
- **Labor liberation, not gig exploitation** — 担当者 (crew) modeling MUST align with
  the Labor Liberation ladder (ADR-2605261000); haraedo coordinates dignified labor,
  it does not create an extractive gig-dispatch market.

## Decision

Introduce a Tier-B actor **`haraedo` 祓戸** (after the Haraedo-no-Ōkami, the Shinto
purification deities who carry impurities away to be dissolved — the mythic image of
collecting refuse and routing it to be processed/purified).

`haraedo` SHALL provide, kotoba-EAVT-native and Murakumo-only:

1. **Citizen intake** (`intake` cell, langgraph/WASM): classify item(s) → quote fee →
   match an accepting facility with capacity → offer a collection slot → issue a
   collection sticker/ticket id → emit a `:application/*` record. Member self-applies
   under explicit DID-signed consent (G1); address/PII is encrypted (G6).

2. **Operator-side logistics** (`dispatch` cell, langgraph/WASM): for a given
   jurisdiction + date, gather scheduled applications → cluster by service area →
   assign a vehicle (capacity-checked) → assign a crew (shift + certification checked)
   → optimize the collection route (nearest-neighbour + 2-opt heuristic over collection
   points) → select the destination facility (capacity + accepted-category checked) →
   emit a `:route/*` plan with ordered stops and personnel. This is the 受付・配車・
   ルート・担当者 design surface.

3. **Global facility registry** (`facility_registry` cell, datalog/kotoba): a coded,
   jurisdiction-parametric registry of waste-processing facilities worldwide —
   `:facility/{kind lat lon capacityTonnesDay acceptedCategories gateFee operatingHours}`
   — stored as kotoba EDN. R0 seed is representative across multiple countries,
   flagged `:sourcing :representative`; later waves ingest authoritative open data.

4. **Fleet & crew registry** (`fleet_registry` cell, datalog/kotoba): vehicles
   (`:vehicle/*`) and crew (`:crew/*`) per jurisdiction, modeled as Labor-Liberation
   participants, not gig contractors.

The langgraph Python actor SHALL be built to a WASM Component-Model cell
(`componentize-py -w kotoba-actor`) and deployed to a running kotoba server (`:8077`)
via `kotoba/deploy.sh`, exactly as toritsugi (ADR-2605312030) and the verified
kotoba-langgraph path (ADR-2605302355). LLM access is via `KotobaLLM` →
Murakumo LiteLLM loopback `127.0.0.1:4000` only.

### Gates (constitutional + actor-specific)

| Gate | Name | Rule |
|---|---|---|
| G1 | consent-bound | member explicit consent (DID-signed) before any application/collection action |
| G2 | no-illegal-dumping | only verified facilities + licensed routes; never propose unlicensed/illegal disposal |
| G3 | hazardous-boundary | 家電リサイクル法対象 / PCB / asbestos / 医療廃棄物 / batteries → routed to licensed handler, NOT collected as bulky waste |
| G5 | labor-dignity | 担当者 modeled per Labor Liberation ladder (ADR-2605261000); no extractive gig dispatch |
| G6 | pii-encrypted | member address/PII → `com.etzhayyim.encrypted.*` envelope, DID-bound (ADR-2605181100) |
| G7 | fee-non-fiat | 手数料 via USDC/warifu SBT↔SBT internal carve-out or external-backend XRPC consent-capability (領収書用途のみ); never Stripe/PayPal/Square |
| G11 | outward-gated | real-world receipt/dispatch/collection requires Council ratification + community operator; R0 is design-only (mirrors ADR-2605302358 G11) |
| G14 | verified-facility | route destinations + fee tables drawn only from the verified facility/fleet registry |
| G15 | capacity-honest | facility daily capacity + vehicle capacity + crew shift are hard constraints; a plan that violates them is rejected, never silently truncated |

### Boundary

- **toritsugi boundary**: toritsugi is the general-procedure concierge; haraedo owns
  the bulky-waste two-sided logistics. haraedo MAY be surfaced *through* toritsugi/LINE.
- **danjo/kanae boundary**: haraedo operates a service; it does not adjudicate or audit
  government fiscal flows.
- **hodoki / kanayama boundary**: post-collection ELV/metals dismantling + circular
  recovery remain hodoki 解き (ADR-2605261215) and kanayama 金山 (ADR-2605252400);
  haraedo hands material *to* facilities, it does not itself reprocess.
- **chigiri boundary**: any licensing/permit legal procedure is chigiri's UPL-bounded
  domain.

## R1 — capacity-honest scheduling · global fee models · capacitated routing

R1 (still design-only under G11; verified by `py/test_agent.py`) extends R0 along
the three axes where the R0 honest non-goals bit hardest:

1. **Per-jurisdiction fee models** — `quote` now honours `:jurisdiction/bulky-fee-model`
   (`:free` / `:per-item` / `:per-sticker` / `:per-weight` / `:flat`) with
   per-jurisdiction parameters (`:jurisdiction/{currency fee-per-sticker fee-per-kg
   fee-flat}`). Seed: JP per-sticker (¥400/¥300), US-NYC free, US-SF per-item,
   DE-Berlin flat (€50), GB-Camden per-weight (£1/kg). Fixes the R0 "sum base fees
   everywhere" shortcut.

2. **Capacity-honest slot calendar** — new `:slot/*` entity (jurisdiction · date ·
   service-area · window · capacity · booked). `schedule` resolves the earliest open
   slot for the collection point's area on/after the desired date and **books it**
   (`booked += 1`); no open slot → empty date (caller re-offers). Extends G15 from
   facility/vehicle/crew capacity to the booking calendar itself.

3. **Capacitated multi-vehicle VRP** — `dispatch` replaces the R0 single-vehicle
   NN+2-opt tour with **Clarke-Wright savings** over per-stop demand: routes are
   built so each route's load ≤ vehicle capacity, every stop is covered exactly
   once, each route is 2-opt-polished, and each route is assigned the smallest
   feasible available vehicle + early-shift crew + destination facility. Routes with
   no feasible vehicle are surfaced in `unassigned` (G15 — never silently dropped).
   Resolves the R0 non-goal "route opt is single-vehicle NN+2-opt, not VRP".

Still deferred (R2+): exact/optimal VRP (OR-Tools-class), time-window VRP (slot ×
route coupling), real authoritative facility/fee/slot data ingestion, live operator
ingest (auth-gated, see below).

### Deployment note (live kotoba)

The running kotoba node enforces **operator auth** on writes (`quad put` → 401;
MCP `tools/call` → "requires Authorization: Bearer <AT-session-JWT>"). This is the
intended no-server-key posture: writing to the canonical Datom journal needs an
authorized operator session token. `kotoba/ingest_mcp.py` flattens `seed.edn`
(39 entities → 347 datoms, verified) and asserts via MCP `kotoba_datom_create`
(or `kotoba quad put`) once `KOTOBA_TOKEN` is supplied, then `kotoba commit` seals.

## R2 — VRPTW (slot×route) · Or-opt local search · authoritative facility data

R2 (design-only under G11; verified by `py/test_agent.py`) closes the three R2-deferred
items named in §R1:

1. **Solver upgrade (Or-opt + local search)** — `_or_opt` (relocate chains of length
   1–3) composed with 2-opt into `_local_search` (alternate until neither improves).
   `_clarke_wright` now polishes each route with `_local_search` instead of 2-opt
   only, so quality is provably ≥ R1. True exact/`OR-Tools`-class VRP stays a deferred
   server-side carve-out (heavy native dep, not WASM-edge-friendly per the lean-edge
   ethos); R2 ships a stronger pure-Python metaheuristic, honestly labelled.

2. **VRPTW — time-window × route coupling** — the R1-deferred coupling. `schedule`
   already books a `:slot/*`; R2 persists `:application/slot-id` so `dispatch` can join
   application → slot → window. `cluster` loads each stop's `{window,start,end}`;
   `build_routes` partitions stops by window and routes each window separately;
   `_route_eta` computes an arrival clock (depot at `window-start`, `speed_kmh`,
   `service_min/stop`); stops whose ETA exceeds `window-end` are surfaced as
   `tw_violations` (G15 — never silently served late). Routes carry `:route/window`.

3. **Authoritative facility ingestion** — `kotoba/fetch_facilities.py` replaces the
   R0/R1 `:sourcing :representative` seed with a coded **open-license SOURCES registry**
   (JP 環境省 一般廃棄物処理実態調査 / US EPA FRS / EU E-PRTR / GB EA — all
   open/public-domain, no proprietary aggregators per Charter Rider §2(e)) + a
   CSV→kotoba-EDN transform that stamps every record `:facility/sourcing :authoritative`
   with `:facility/source-url` + `:facility/source-dataset` provenance (G8
   non-fabrication). Network crawl of each portal is the deferred R2.1 step; the
   transform is the stable seam (`--from <csv> --dataset <id>`).

New schema: `:application/slot-id`, `:slot/window-start|end`, `:route/window`,
`:facility/source-url|source-dataset`. Still deferred (R3+): exact VRP solver,
inter-window vehicle reuse, live authoritative crawl, real operator dispatch (auth +
Council, G11).

## R3 (started) — inter-window vehicle reuse

First R3 increment (design-only under G11; verified by `py/test_agent.py`). R2
routed each time window with a fresh disposable vehicle list. R3 replaces that with
a **persistent vehicle pool carrying a `free_at` clock** (the minute each vehicle is
next back at the depot): a later window may **reuse** a vehicle iff `free_at ≤
window_start`. After each route, `free_at = last-stop ETA + service + return-to-depot
travel`. Routes carry `vehicle_reused`; a vehicle that cannot return in time is not
forced (the route goes to `unassigned`, G15). This raises fleet utilisation
(one AM+PM-capable truck now serves both windows) without overstating capacity.

Still deferred (R3.x / R4): exact/optimal VRPTW solver (server carve-out), crew
inter-window reuse + shift rules, live authoritative-data crawl, and real operator
dispatch (auth + Council ratification, G11).

## Consequences

### Positive

- A single jurisdiction-parametric model for a service that exists in ~every
  municipality; structural-labor relief on both citizen and operator sides.
- Facility/fleet/crew/route/application as **first-class kotoba EAVT facts** → routing
  and capacity decisions are queryable, auditable, and on-chain-anchorable.
- Reuses the verified kotoba-langgraph-WASM + Murakumo path end-to-end (no new
  substrate primitives invented).

### Negative / Risks

- Route optimization is NP-hard; the R0 heuristic (NN + 2-opt) is a stand-in, not an
  exact VRP solver. Flagged; a real solver is a later wave (analogous to the giemon
  MoldField app-layer stand-in, ADR-2605312300).
- Global facility data is vast and heterogeneous; R0 seed is representative only
  (`:sourcing :representative`) — must not be mistaken for authoritative coverage.
- Real collection touches public-health, traffic, and labor regulation per
  jurisdiction; **G11 keeps all outward action design-only** until Council + operator.

### Neutral

- Adds one Tier-B actor row and one ADR; no change to existing actors.

## Alternatives Considered

- **Extend toritsugi instead of a new actor** — rejected: bulky-waste is a logistics
  optimization problem (vehicles/routes/capacity), not a guidance procedure; it would
  overload toritsugi's concierge scope.
- **Model only the citizen side** — rejected: the request explicitly requires the
  operator side (受付・配送・配車・ルート・担当者).
- **Store facility data in a GIS/Postgres** — rejected by substrate boundary; kotoba
  EAVT is the canonical state home (ADR-2605312345).

## References

- ADR-2605312030 — toritsugi citizen-procedure concierge (sibling pattern)
- ADR-2605262130 / 2605312345 — kotoba storage substrate + Datom-first-class state
- ADR-2605302355 — kotoba langgraph LLM verified + durable Murakumo routing
- ADR-2605215000 — Murakumo-only inference
- ADR-2605181100 — confidentiality envelope (encrypted PII)
- ADR-2605261000 — Labor Liberation ladder
- ADR-2605261215 / 2605252400 — hodoki / kanayama circular-recovery boundary
- ADR-2605302358 — social-security delivery pipeline (G11 outward-gating precedent)
- ADR-2605192100 — etzhayyim Mission Charter
