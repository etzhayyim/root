---
id: adr-2606020100-session-close-kotoba-browser-node
title: "ADR-2606020100: Session close — kotoba browser node (WASM read/write + jco Pregel) + browser-native actors + durable search"
status: active
doc_type: adr
topic: session-close-kotoba-browser-node
authoritative: false
last_verified: 2026-06-02
priority: 4.0
axis: process
weight: 0.40
priority_note: "Documentation-only session-close record; authoritative design = ADR-2606013600"
authoritative_for: []
depends_on:
  - adr-2606013600-kotoba-wasm-browser-node
related:
  - adr-2606013200-yoro-kotoba-feed-readpath-migration
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605241900-baien-edge-target-invariant
  - adr-2606012100-donation-funded-operation-and-compute-node-donation
supersedes: []
superseded_by: []
---

# ADR-2606020100: Session close — kotoba browser node + browser-native actors + durable search

**Status**: active (documentation-only)
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

Session opened on "https://etzhayyim.com/ への登録アクターは world coverage はどうなっている? kotoba server で設計実装されている?" and the actor search showing `検索に失敗しました`. It closes with the **whole actor read path running in the browser** and the recurring data-loss + 1-actor-search bugs fixed. Authoritative design = ADR-2606013600 (kotoba browser node).

# Decision (what shipped, with verification)

## Search 502 root cause + fix
`/search` called the decommissioned legacy AppView host `bsky.etzhayyim.com`
(`etzhayyim-appview` binding force-deleted → 502 `検索に失敗しました`). Repointed the
reader to the same-origin apex substrate path (`/xrpc` → etzhayyim-did-web →
yoro-xrpc-adapter), the ADR-2605172000 RW-free read path (yoro commit `b94484a5d`).

## kotoba browser node (ADR-2606013600, P0–P3 — kotoba PRs #14/#15/#16)
- **P0**: `kotoba-wasm` crate — the `kotoba-kqe` Datom read engine on
  `wasm32-unknown-unknown`. The ONLY wasm blocker is tokio's `net`→`mio`; fixed by
  a per-target tokio feature-gate on `kotoba-kqe` (native full / wasm32 `sync`).
  Bundle **87 KiB gzip**.
- **P1**: `loadDatoms()` hydration from `datomic.datoms` JSON; a **transparent
  Service-Worker `/xrpc` shim** (yoro-rw-free unchanged); **IndexedDB persistence**
  (reseed-free cold reload) + snapshot delta + a **registered-actor backfill** so
  `/search` never degrades to one actor again.
- **P2**: local `transact()` + `exportDatoms()` + **OPFS append-only tx journal**.
- **P3**: the **real `kotoba-guest`** (kotoba-node world) → `wasm32-wasip2` →
  **jco** → runs on the browser WebAssembly engine with `kotoba:kais/{kqe,kse,auth}`
  host imports wired to `KotobaNode` (`kqe.assert-quad` lands in the node; `llm`
  disabled = Murakumo-only). **JS BSP multi-superstep driver** (browser
  `WasmPregelRunner`).

All verified in a **real Chromium** (Playwright): in-browser `searchActors`,
cold-restart IndexedDB restore (seed blocked), `transact`+OPFS journal surviving
cold restart, real guest `run()` + `kqe.assert-quad` into KotobaNode, BSP driver
looping 4 supersteps.

## Browser-native actors on etzhayyim.com
`etzhayyim.com/actors` now serves a browser shell: the in-page kotoba wasm node
loads the registry (`/.well-known/actors.json`, INFRA_ACTORS SSoT) and renders +
searches **every actor client-side** (no server query for the data). CSP is
same-origin only — the CF analytics beacon is CSP-blocked (Charter Rider §2(c)
no-tracker). `?static=1` keeps the no-JS list. Verified live: 10 actors rendered
in-browser, CJK + description search work, no app console errors.

## Durability (the recurring data-loss, resolved)
`/search` had shown only the `did:web:etzhayyim.com` entity after the local kotoba
restarted. Re-ingested the 10 registered actors (`:yoro.profile/*`); the live path
now returns 11. **Verified durable**: `launchctl kickstart -k com.etzhayyim.kotoba`
(kill + replay) preserved all 11 profiles — head persisted in `ipns-heads.json` +
Kubo pins (780 recursive / 49,519 objects). The SW backfill is the second layer of
resilience.

# Consequences

- The browser is a **first-class kotoba replica + compute node** (read engine,
  persistence, local writes, guest execution) — the baien edge-invariant posture
  (ADR-2605241900) and ameno donated-node story (ADR-2606012100): "open a tab".
- The actor registry + search are resilient to the local kotoba node restarting,
  via durable replay AND the SW backfill.
- No new substrate; still the kotoba Datom log + content-addressed blocks. Inference
  stays Murakumo-only (the storage node exposes none).

# Commits / deploys (this session)

- root: `b94484a5d` (search→substrate), `b2dcc0103` (yoro ships browser node),
  `97793e4dc` (IDB persistence + delta), `df22e7b03` (transact + OPFS),
  `8bba6d867` (search backfill), `33cd95730` (browser-native /actors),
  `28cd81764` (ADR-2606013600), this session-close ADR.
- kotoba subrepo `main`: PR #14 (P0+P1), #15 (P2 transact), #16 (real guest jco);
  local `72f939a` (BSP driver) + `b509042` (real-browser BSP) pending a follow-on PR.
- deployed: `magatama-yoro` (browser-node SW + bundle), `etzhayyim-did-web`
  (browser-native /actors), `yoro-xrpc-adapter` (kotoba read path).

# Honest gaps

- Full browser Pregel still needs the OPFS-backed `kse`/`auth` host (currently
  stubs) + the full CBOR QuadObject codec + a real-browser run of the *kotoba*
  guest (the jco path + BSP driver are each browser-verified; their composition is
  node-verified). `GuestRuntime` trait extraction (native) + libp2p-in-browser P2P
  sync are follow-ons.
- kotoba `72f939a`/`b509042` are local commits at session close (PR pending).
- Server durability relies on the external IPFS volume (`/Volumes/260317`,
  KeepAlive PathState); the SW backfill covers the window when it is unmounted.

# Alternatives Considered

See ADR-2606013600 (port wasmtime to browser — infeasible; second guest ABI —
rejected; SQLite-WASM mirror — violates the substrate boundary).

# References

- ADR-2606013600 — kotoba browser node (authoritative design)
- ADR-2606013200 — yoro kotoba feed read-path migration
- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605241900 — baien edge-target invariant
- ADR-2606012100 — donation-funded operation + compute-node donation
