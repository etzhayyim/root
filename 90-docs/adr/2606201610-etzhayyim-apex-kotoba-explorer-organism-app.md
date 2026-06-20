---
id: adr-2606201610-etzhayyim-apex-kotoba-explorer-organism-app
title: "ADR-2606201610: etzhayyim.com apex — kotoba blockchain explorer + node-distribution + organism app (serverless, browser-side)"
status: proposed
doc_type: adr
topic: etzhayyim-apex-kotoba-explorer-organism-app
authoritative: true
last_verified: 2026-06-20
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - etzhayyim.com apex landing app (replaces the yoro bsky AppView at the apex)
  - browser-side (serverless) kotoba blockchain/CommitDag explorer
  - node-distribution (分散状況) view over the actor/cell mesh
  - organism aliveness view (Tree-of-Life + 5-tuple)
depends_on:
  - adr-2606013600-browser-kotoba-node-sovereign-apex-tier2
  - adr-2605202359-etzhayyim-apex-yoro-proxy
related:
  - adr-2605171900-yoro-migration-to-etzhayyim
  - adr-2605311310-yoro-black-screen-spa-recursion-fix-and-ipfs-deploy-feasibility
  - adr-2606121350-yoro-ui-svelte-to-cljs-migration-harness
supersedes: []
superseded_by: []
---

# ADR-2606201610: etzhayyim.com apex — kotoba explorer + node-distribution + organism app

**Status**: proposed (R0 design)
**Date**: 2026-06-20
**Deciders**: Jun Kawasaki

# Context

Today `https://etzhayyim.com/` (apex) reverse-proxies, via a Cloudflare Service
Binding, to the **yoro** Bluesky/AT-Protocol AppView SPA
(`60-apps/etzhayyim-project-yoro`, Worker `kotodama-yoro`). The apex is a generic
social feed — it says nothing about what etzhayyim *is*.

We want the apex to instead present the **substance of the organism itself**, in
three views:

1. **kotoba blockchain explorer** — browse the kotoba CommitDag (the append-only,
   content-addressed Datom ledger), its commits, blocks, and Datoms.
2. **node distribution (分散状況)** — the live mesh of actors/cells: who is alive,
   dormant, or a stub; the dependency graph; per-node reflex/heartbeat/cells.
3. **organism** — the aliveness of the whole: the Tree-of-Life 10 axes, the
   aliveness 5-tuple ⟨M,D,C,P,G⟩, pulse (commit stream), and joucho (mood).

Hard constraint from the operator: **serverless, computed in the browser** ("kotoba
browser で serverless, browser 側で処理、計算する"). No new backend service, no
server in the trust path; the browser fetches content-addressed data and does the
decoding/querying/layout/metric computation itself.

## What already exists (we are assembling, not inventing)

The pieces are already in the tree and running — this app is a **UI shell** over a
proven substrate:

- **Browser-only kotoba node** — `50-infra/etzhayyim-did-web/poc-browser-node`
  (ADR-2606013600) proves `kotoba-wasm` (`40-engine/kotoba/crates/kotoba-wasm`)
  runs **entirely in the browser**: `kotoba-kqe` EAVT/AEVT/AVET/VAET indexes +
  **CID-verified Prolly-tree traversal** compiled to `wasm32`, client-side ed25519
  commit signing (**no server key**), and an **IndexedDB block store**. Verified in
  real Chrome via a Service Worker (`x-kotoba-sw: local-wasm`). This is exactly the
  "kotoba browser, browser-side compute" the apex needs.
- **Block/ledger data plane already served from the apex Worker** —
  `50-infra/etzhayyim-did-web/src/kotoba-publish.ts` already answers
  `GET /kotoba/<genesis>.root.json` (CommitDag head) and
  `GET /kotoba/blocks/<cid>` (a content-addressed block, served from Cloudflare KV
  with IPFS as the durable tier). These are **static, cacheable, content-addressed**
  reads — the browser verifies each block by CID, so the edge is *not* trusted.
- **Organism + node data already generated as static JSON/EDN** —
  `60-apps/etzhayyim-project-organism/public/` is regenerated on a heartbeat
  (pulse ~6s, joucho ~60s, vitals ~1h; see `health.json`/`watchdog.json`):
  - `organism.json` — `summary {cells, alive, dormant, stub}` + `nodes[]` each
    `{id, class, score, reflex, heartbeatDays, inDeg, outDeg, cells, clj, actor,
    atproto, bsky, port, status}` → **this is the node-distribution graph**.
  - `trajectory.json` — `runs[] {at, cells, alive, dormant, stub, sum}` time series.
  - `pulse.json` — `stream[] {at, actor, subj}` recent commits + per-actor activity.
  - `vitals.kotoba.edn` — aliveness 5-tuple + 10-axis scores.
  - `joucho.json` / `narration.kotoba.edn` — mood + LLM narration (fail-open).
- **Bonsai Tree-of-Life renderer (reference)** —
  `60-apps/etzhayyim-organism-viz` already computes A(t)=⟨M,D,C,P,G⟩ and renders the
  10-axis bonsai as pure SVG (Python). We port its *geometry* to the browser; we do
  **not** keep the Python server in the apex path.

So the data already exists, is already content-addressed/static, and is already on a
heartbeat. The work is a **client-side viewer**, not a backend.

# Decision

Build a single static SPA — **`etzhayyim-project-explorer`** (working name
`kotoba-explorer`) — and put it at the apex in place of yoro. yoro keeps its own
home at `yoro.etzhayyim.com` (it already routes there).

## 1. Topology / deploy (serverless, one binding flip)

```
https://etzhayyim.com/                      (apex)
  └─ Worker: etzhayyim-did-web  (UNCHANGED responsibilities)
       ├─ /.well-known/did.json              → did.json                 (keep)
       ├─ /kotoba/<genesis>.root.json        → CommitDag head           (keep)
       ├─ /kotoba/blocks/<cid>               → KV/IPFS block, CID-checked(keep)
       ├─ /organism/*.json|*.edn             → static heartbeat assets  (NEW asset route)
       └─ /* (catch-all)  ── Service Binding ─┐
                                              ▼
                              Worker: kotodama-explorer  (NEW — Assets only)
                                 static SPA (index.html + hashed chunks)

https://yoro.etzhayyim.com/   → kotodama-yoro            (UNCHANGED — yoro lives on)
```

- **Only change to the apex Worker**: the catch-all Service Binding target flips
  `YORO → EXPLORER` in `50-infra/etzhayyim-did-web/wrangler.toml` + the proxy line in
  `src/worker.ts`. did:web, kotoba block serving, and actor profiles are untouched.
- The new Worker is **pure Cloudflare Workers Assets** (same serverless pattern as
  yoro: `ssr:false, csr:true`, SPA fallback) — no origin, no compute on the edge.
- **No server in the trust path**: every kotoba block is CID-verified in the browser;
  the edge (KV/Worker/IPFS gateway) is an untrusted cache. Matches ADR-2606013600.
- **IPFS-portable**: because all reads are content-addressed, the same build pins to
  IPFS and runs from a gateway with no behavior change (ADR-2605311310 feasibility).

## 2. App shell — three views, one SPA

Route-first SPA (per ADR-2605311310's anti-recursion lesson: each route renders its
panel directly, no nested SPA frame):

```
/            → Organism   (default landing — the "what is this" view)
/explorer    → kotoba blockchain explorer (CommitDag)
/nodes       → node distribution (分散状況)
/organism    → organism aliveness (alias of /)
```

```
┌──────────────────────────────────────────────────────────┐
│ etzhayyim            [ Organism ] [ Explorer ] [ Nodes ]   │
├──────────────────────────────────────────────────────────┤
│  ░░ default: ORGANISM ░░                                   │
│   ┌── Tree of Life (10 axes, bonsai) ──┐  ┌ A(t) dials ──┐ │
│   │        ✿ autopoiesis 10/10         │  │ M ▓▓▓░  Motion│ │
│   │      ✿ metabolism 6/10  …          │  │ D ▓▓░░  Divers│ │
│   │   trunk = charter, roots = LANDS   │  │ C ▓▓▓░  Couple│ │
│   └────────────────────────────────────┘  │ P ▓▓░░  Prune │ │
│   pulse ▸ busshi: refresh USGS metals…     │ G ▓▓▓▓  Gener │ │
│   joucho ▸ "steady, weaving"               └───────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### View A — Organism (`/`)
- **Source**: `/organism/vitals.kotoba.edn`, `/organism/trajectory.json`,
  `/organism/pulse.json`, `/organism/joucho.json`, `/organism/narration.kotoba.edn`.
- **Browser compute**: parse EDN client-side (`@edn-data/edn` or a small reader);
  **recompute** A(t)=⟨M,D,C,P,G⟩ from trajectory in-browser (don't just display the
  baked number — the constraint is *browser-side computation*); homeostatic-range
  banding per `ideal_state` ranges.
- **Render**: bonsai Tree-of-Life (port `etzhayyim-organism-viz/bonsai.py` geometry to
  Canvas2D/SVG), five A(t) dials, trajectory sparkline, pulse commit ticker, joucho
  mood line. Non-eschatological framing (health = stable open trajectory, not a goal).

### View B — kotoba blockchain explorer (`/explorer`)
- **Source**: a kotoba Datom log in the canonical `tx->edn-line` format (append-only
  commit-DAG; ADR-2605312345), plus the static `/kotoba/<genesis>.root.json` head
  pointer and raw `/kotoba/blocks/<cid>` blocks.
- **Browser compute — REAL, not a stub (the "kotoba browser")**: the view **requires
  the canonical `kotoba.datom` codec** (`20-actors/kotodama/src/kotoba/datom.cljc`)
  and binds its `*sha256-hex*` host seam to a synchronous SHA-256 (`js-sha256`). It
  then **verifies the content-addressed chain in-browser** by recomputing every
  `:tx/cid` from `(datoms, prev)` — **byte-compatible** with the clj/Python writers,
  so a tamper of any earlier tx breaks every later CID and is detected with no server
  in the loop. It **materializes the EAVT** (folds `[:db/add e a v]`) into an entity
  browser and runs a **Datalog-shaped query** (by attribute/value) client-side.
  *Proven*: `datom_test.cljs` verifies a real committed log (mimamori golden fixture,
  `:tx/cid b3dc4fac…`) → `:ok`, and confirms tamper-detection fires.
- **R1 (kotoba-wasm)**: the raw-block CAR path — CID-verified Prolly traversal +
  the full kqe Datalog grammar (EAVT/AEVT/AVET/VAET arrangements) — loads the
  `poc-browser-node` `kotoba-wasm` bundle lazily; IndexedDB caches blocks.
- **Trust**: ed25519 signer shown from the commit (no-server-key model); the edge is
  an untrusted cache (CID re-verified locally).

### View C — node distribution / 分散状況 (`/nodes`)
- **Source**: `/organism/organism.json` (`nodes[]` + `summary`) +
  `/organism/health.json` (layer staleness) + the murakumo roster
  `50-infra/murakumo/fleet.edn` (the 12-tribe physical nodes:
  naphtali/simeon/judah/zebulun/levi/joseph/issachar/dan/benjamin/asher — cell
  placement + healthz ports) baked as a static `/organism/fleet.json`.
- **Browser compute**: force-directed graph layout (`d3-force` or a tiny in-house
  sim) over `inDeg`/`outDeg` edges, computed in the browser; aggregate alive/dormant/
  stub counts; HHI-style concentration of cells per physical node.
- **Render**: (1) **mesh graph** — node = actor/cell, color = `reflex`
  (green/red/absent), size = `score`/`cells`, edges = dependency degree; (2) physical
  **fleet map** — 10 tribe nodes with their cell counts + healthz; (3) summary cards
  (`104 cells · 1 alive · 96 dormant · 7 stub`) + staleness badges from `health.json`.
- **Live tier (decided: in R0, still serverless)**: dial a kotoba node via libp2p
  **from the browser** for an SSE Datom tail
  (`/xrpc/com.etzhayyim.apps.kotoba.sync.subscribe`) so the mesh updates in
  real time. The static snapshot remains the **baseline render** (the page is fully
  functional with zero connections); the live tail is a progressive enhancement
  layered on top, and a connection failure degrades silently to the snapshot.

## 3. Tech stack

- **ClojureScript + shadow-cljs** (`:browser` target), aligning with the in-flight
  yoro Svelte→CLJS migration (ADR-2606121350) and the did-web cljs Worker core. EDN is
  native — no JS EDN-parser shim — which matters because organism vitals/joucho/
  narration are EDN. Reuse `@etzhayyim/design-system` for chrome.
  - *Fallback*: SvelteKit static adapter (yoro's proven build) if cljs viz velocity
    is a problem; the data plane and deploy are stack-agnostic.
- **Rendering**: Canvas2D/SVG for bonsai + graph; no heavy 3D dependency in R0.
- **kotoba-wasm**: consumed as the `poc-browser-node` web bundle (`wasm-pack --target
  web`); loaded lazily only when `/explorer` opens.
- **Build/deploy**: `pnpm build` → Workers Assets; apex binding flip. Mirrors the
  yoro pipeline exactly (drop-in at the apex).

## 4. Directory layout (new)

```
60-apps/etzhayyim-project-explorer/
├── README.md
├── shadow-cljs.edn                 # :app → :browser, :dev-http
├── wrangler.jsonc                  # Worker: kotodama-explorer (Assets only)
├── src/etzhayyim/explorer/
│   ├── app.cljs                    # route-first shell (/, /explorer, /nodes)
│   ├── organism/{view,bonsai,aliveness}.cljs   # A(t) recompute + Tree of Life
│   ├── chain/{view,commitdag,datom,query}.cljs # kotoba-wasm CommitDag explorer
│   ├── nodes/{view,graph,fleet}.cljs           # force graph + fleet map
│   └── data/fetch.cljs             # CID-verified block fetch + EDN/JSON readers
├── resources/kotoba-wasm/          # web bundle from poc-browser-node serve/
└── static/                         # build output (Workers Assets)
```

The heartbeat generator that already writes
`60-apps/etzhayyim-project-organism/public/*` gains an emit of `fleet.json` (from
`fleet.edn`) and those assets are surfaced under the apex `/organism/*` route.

# Consequences

**Positive**
- The apex finally *is* the organism: ledger + mesh + aliveness, not a generic feed.
- Genuinely serverless and trust-minimized: every read is content-addressed and
  CID-verified in the browser; the edge is a cache, not an authority (ADR-2606013600).
- Reuses proven parts (browser kotoba node, apex block serving, heartbeat data,
  bonsai geometry) — R0 is assembly + a viewer, low new-surface risk.
- IPFS-portable by construction; a future "no Cloudflare" pin works unchanged.
- yoro is preserved at `yoro.etzhayyim.com`; this is additive, reversible by one
  binding flip.

**Negative / risks**
- `kotoba-wasm` web bundle adds payload + a wasm32 build step (rustup, not Homebrew
  rust — per poc README). Lazy-load it on `/explorer` only.
- Organism/node data is a periodic snapshot (vitals ~1h); "live" needs the optional
  libp2p tail. Mitigate with visible `health.json` staleness badges.
- CLJS viz authoring is slower than Svelte for some; Svelte fallback noted.
- The explorer reveals the *real* mesh state (96/104 dormant today) — by design, but
  it makes organism health publicly legible; acceptable per the transparency posture.

# Rollout (R0 → R1)

- **R0 (this ADR — implemented)**: ClojureScript static SPA, **default landing =
  Organism**; three views from the existing snapshots; bonsai + browser-laid-out node
  graph; **libp2p live Datom tail** layered over the node snapshot; the explorer runs
  the **real `kotoba.datom` codec in-browser** — byte-compatible content-addressed
  chain verification + EAVT entity browser + Datalog-shaped query over a real committed
  log (proven by `datom_test.cljs`). Builds clean (shadow-cljs `release`, 0 warnings);
  8 tests / 25 assertions green. Ship behind `explorer.etzhayyim.com` first; flip the
  apex binding only after preview verification.
- **R1**: the raw-block CAR path via kotoba-wasm (Prolly traversal) + full kqe Datalog
  grammar; IPFS pin of the build; joucho/narration surfacing; physical fleet healthz
  live probe; broaden the live tail to the explorer (live commit stream).

# Decisions locked (2026-06-20)

1. **Stack** = ClojureScript + shadow-cljs (`:browser`) — native EDN, aligns with the
   yoro svelte→cljs migration and the did-web cljs Worker core.
2. **Default landing** = Organism (`/`) — lead with "what etzhayyim is".
3. **Cut-over** = preview at `explorer.etzhayyim.com` first, then flip the apex binding
   `YORO → EXPLORER` — safe and reversible.
4. **Live tier** = ship the libp2p SSE Datom tail in R0 as a progressive enhancement
   over the static snapshot baseline (degrades silently on failure).
