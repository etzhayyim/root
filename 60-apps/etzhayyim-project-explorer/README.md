# etzhayyim-project-explorer

The **etzhayyim.com apex** SPA — a serverless, browser-side view of the living
organism, replacing the yoro bsky AppView at the apex (yoro lives on at
`yoro.etzhayyim.com`). Design: **ADR-2606201610**.

Three route-first views:

| route       | view      | what it shows |
|-------------|-----------|---------------|
| `/` (default) | **Organism** | Tree-of-Life (10 axes) + aliveness 5-tuple `⟨M,D,C,P,G⟩` (recomputed in-browser) + pulse commit stream + joucho mood |
| `/explorer` | **kotoba blockchain** | runs the **real `kotoba.datom` codec in the browser**: fetches a kotoba Datom log, **verifies the content-addressed chain** (recomputes every `:tx/cid`, tamper-evident), materializes the **EAVT entity browser**, and runs a Datalog-shaped query — all client-side |
| `/nodes`    | **distribution (分散状況)** | the actor/cell mesh (browser-laid-out force graph) + alive/dormant/stub summary + physical fleet + libp2p/SSE live Datom tail |

## Serverless / browser-side by design

There is **no backend in this app**. Every read is a content-addressed or static
snapshot served by the apex `etzhayyim-did-web` Worker:

- `/organism/*.json` `*.kotoba.edn` — heartbeat snapshots from
  `60-apps/etzhayyim-project-organism` (pulse ~6 s, joucho ~60 s, vitals ~1 h)
- `/kotoba/<genesis>.root.json` — CommitDag head pointer
- `/kotoba/blocks/<cid>` — content-addressed block (KV/IPFS), CID-verified

The browser does all decode / compute / layout (EDN parsing via `cljs.reader`,
the aliveness recompute, the force layout, and — via `kotoba-wasm` — CID-verified
Prolly traversal + Datalog). The edge is an **untrusted cache**; the browser is
the only authority (ADR-2606013600). Because all reads are content-addressed, the
same build is IPFS-portable.

## Stack

Reagent 1.2 + re-frame 1.4 + shadow-cljs `:browser` (mirrors the yoro cljs
harness). EDN is native — no JS parser shim. The explorer **actually requires**
the canonical portable codec `kotoba.datom`
(`orgs/kotoba-lang/kotodama/src/kotoba/datom.cljc`) and binds its `*sha256-hex*` seam to
a synchronous SHA-256 (`js-sha256`), so chain verification is **byte-compatible**
with the clj/Python writers — proven by `datom_test.cljs`, which verifies a real
committed log (mimamori's golden fixture) and confirms tamper-detection fires.

## Develop

```sh
npm install
# point the data plane at the live apex (snapshots are not local):
#   in public/index.html, set window.__DATA_BASE__ = "https://etzhayyim.com"
npm run dev        # shadow-cljs watch app → http://localhost:8710 (push-state)
npm test           # shadow-cljs :node-test
```

## Build & deploy

```sh
npm run build      # shadow-cljs release app → public/js
npm run deploy:prod  # wrangler deploy  (Worker: kotodama-explorer)
```

**Cut-over (decided 2026-06-20):** publish at `explorer.etzhayyim.com` first and
verify, then flip the apex `etzhayyim-did-web` catch-all Service Binding
`YORO → EXPLORER` (one line in its `wrangler.toml` + `src/worker.ts`). The apex
also needs to surface `/organism/*` (already serves `/kotoba/*`) and the heartbeat
should emit `/organism/fleet.json` from `50-infra/murakumo/fleet.edn`.

## Layout

```
src/etzhayyim/explorer/
├── core.cljs             # bootstrap (React 18 root, router)
├── shell.cljs            # top nav + route-first view switch
├── router.cljs           # push-state router
├── data.cljs             # content-addressed fetch (JSON/EDN/blocks)
├── state.cljs            # re-frame db + resource loading + promise fx
├── ui.cljs               # loading gate + heartbeat staleness badges
├── live.cljs             # libp2p/SSE Datom tail (progressive, degrades silently)
├── organism/{aliveness,bonsai,view}.cljs
├── nodes/{graph,view}.cljs
└── chain/view.cljs
```

## Status

R0 (this commit): all three views render from the existing snapshots; aliveness
M/D computed in-browser; node mesh laid out in-browser; live SSE tail wired
(opt-in). The explorer runs the **real `kotoba.datom` codec in-browser** —
byte-compatible content-addressed chain verification + EAVT entity browser +
Datalog-shaped query over a real committed Datom log (no stub). **R1:**
kotoba-wasm Prolly/CAR block decode for the raw `/kotoba/blocks/<cid>` path +
full kqe Datalog grammar (EAVT/AEVT/AVET/VAET arrangements); IPFS pin; fleet
healthz live probe.
