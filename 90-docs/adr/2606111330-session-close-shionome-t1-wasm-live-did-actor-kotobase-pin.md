---
id: adr-2606111330-session-close-shionome-t1-wasm-live-did-actor-kotobase-pin
title: "ADR-2606111330: Session close — 潮目 T1 browser-wasm DID actor LIVE on etzhayyim.com + kotobase.net pin saga (root-caused)"
status: active
doc_type: adr
topic: shionome-cross-asset-capital-flow-observatory
authoritative: false
last_verified: 2026-06-11
priority: 5.0
axis: actor
weight: 0.5
depends_on:
  - adr-2606101540-session-close-shionome-stock-pyramid-grounding-live-edgar-fleet-heartbeat
  - adr-2606072200-shionome-cross-asset-capital-flow-observatory-r0
  - adr-2606015200-wasm-actor-runtime-round-2
  - adr-2606013800-actor-profile-ssot-dynamic-did-json
  - adr-2605231525-server-side-signing-capability-boundary
related:
  - 90-docs/adr/2606101540-session-close-shionome-stock-pyramid-grounding-live-edgar-fleet-heartbeat.md
supersedes: []
superseded_by: []
---

# Context

Question that opened the session: *「https://etzhayyim.com/ で browser wasm, did actor として動いている?」*

Honest answer at the time: **NO, on three levels.** (1) `did:web:etzhayyim.com:actor:shionome`
resolved only at the apex Worker's fallback-scaffold tier (keyless, `registry: null`, no WASM
service); (2) **zero** actors' wasm bytes were fetchable — apex `/ipfs/<cid>` returned 502 for
kanae's registered CID and timed out for the rest (no reachable IPFS provider anywhere); (3)
shionome's only wasm artifact was the 18.5MB componentize-py component — dag-pb codec = T2
mesh-tier, structurally not browser-local. The site SUBSTRATE did run browser-local kotoba WASM
(service-worker browser-node), but no ACTOR did.

# Decision (what landed — PR #1588, squash-merged 2026-06-10)

User instruction: a, b, c (register + pin + T1 build). All three landed; production e2e verified:

```
1. DID resolved:  did:web:etzhayyim.com:actor:shionome  (_meta.source: kotoba)
2. wasm service:  ipfs://bafkreihvidpg…  (x-exec: browser-local|donated-mesh)
3. apex /ipfs fetch: HTTP 200 · 18,762B  (x-etzhayyim-cid-verified: sha256)
4. local CID re-verify: MATCH ✓ (trustless)
5. EXECUTED: {"actor":"shionome","regime":"risk-on","grand_total":1383,
              "top_layer":"derivatives","no_trade":true}
```

1. **(c) T1 wasm** — `20-actors/shionome/wasm/shionome-core/`: compact Rust core
   (tsumugi/kanae ABI `compute() -> i32` + `result_ptr()`), embeds the `:representative`
   seed, computes the cross-asset regime + the `:outstanding-usd` stock pyramid;
   **18,762 bytes** (1/1000 of the T2 component) → raw single-block CID
   `bafkreihvidpgf5lgrgdwxskhjasbysigqcunrlshi2sx4zdngkapi5tlly`. `build-t1.sh`
   instantiates the built wasm and ASSERTS `no_trade:true` on its actual output —
   トレードはしない carried into the artifact itself (G2).
2. **(a) DID-actor registration in all three homes** — `actor-profile-seed.kotoba.edn`
   entry (kanae format, `:actor/wasm-cid`) + `INFRA_ACTORS` compiled mirror + static
   `public/actor/shionome/{did.json,profile.json}` (the edge-served canonical docs;
   discovered: named actors are served as STATIC files BEFORE the worker runs — the KV
   put path in publish-actor-records is a no-op for did.json). Worker tsc clean,
   **101/101 tests**, deployed to production (version `b50b69fb`).
3. **(b) pinning, local leg** — discovered the host runs TWO ipfs repos (offline CLI repo
   vs the live daemon — the first `ipfs add` went into the decoy); pinned via the daemon
   HTTP API. **kanae's Rust rebuild reproduced its registered CID bit-identically** →
   pinned → its 502 FIXED; tsumugi's committed loader artifact matched its CID → pinned.
   **All three T1 actors (shionome/kanae/tsumugi) now serve HTTP 200 via the apex
   trustless gateway** (re-verified against public gateways: ipfs.io 206).

# kotobase.net durability leg (operator instruction 「pin は kotobase.net を使って」) — root-caused, NOT yet pinned

Operational (no repo change). Findings worth permanent record:

- **Architecture**: kotobase.net = Hono CF Worker (repo `gftdcojp/net-kotobase`) exposing the
  standard IPFS Pinning Service API (`/pins`) as a thin shim that proxies to
  `https://kotoba-backend.gftd.ai` (kotoba-server pod on Vultr VKE; XRPC
  `com.etzhayyim.apps.kotobase.pin{Create,List,Delete}`). The repo-side `KOTOBA_PIN_TOKEN`
  exists in code only — no token on this machine; the working auth is (1) self-sovereign
  CACAO with the `kotobase:pin` capability (no internal-trust needed) or (2) edge JWT.
- **Tenant identity duality (pitfall)**: the same Ed25519 key is `did:key:ze2e…` (hex form,
  `kotoba whoami`) on the JWT path but `did:key:z6MktEjt…` (multibase form) to the CACAO
  verifier — two DIFFERENT tenants. **z6Mk is canonical**; pins were re-registered under it
  via direct backend CACAO calls: `pin_19eb4356b9f00007` (shionome) /
  `pin_19eb435d9ee00009` (kanae) / `pin_19eb43626b20000b` (tsumugi).
- **Stall root cause (code-read + live evidence)**: `kotobase_xrpc.rs` pin completion spawns
  `IpfsPinClient.pin()` → kubo `/api/v0/pin/add` with **no reqwest timeout**; kubo's pin/add
  **blocks until content is fetched**; the pod's node shows **`peer_count: 0`** (isolated) so
  the fetch never completes and status stays `pinning` forever. An earlier backend state
  reset also wiped the first day's requestids (and the free-tier 3/3 quota counter).
- **Operator follow-ups**: fix pod IPFS connectivity (VKE egress/bootstrap), and/or patch
  `IpfsPinClient` (timeout + gateway-fallback fetch + honest `failed` status). A session
  pin-watch cron re-announced providers + polled status (~4h, no transition); stopped at close.

# Honest boundary

- **Durability today** = the jacob local kubo daemon (sole first-party provider; NAT'd,
  relay/webtransport addrs only) + public gateway caches. kotobase.net pins are REGISTERED
  but not COMPLETE — if jacob goes offline before the pod is fixed, the wasm bytes
  eventually become unfetchable again.
- The 18.5MB T2 componentize-py component remains unpinned (bytes not rebuilt this session;
  componentize-py toolchain not installed).
- Murakumo narration remains down (`~/.ollama/models` → `/Volumes/251220` external disk,
  still unattached); a disk-full incident on jacob (228GiB, 118MiB free) interrupted one
  turn mid-session — user freed 21GiB; only other-session `/tmp` debris was implicated.

# Consequences

The original question is now answered YES with a five-step production proof: shionome (and
kanae/tsumugi) resolve as registered DID actors whose declared wasm is fetchable through the
apex trustless gateway, CID-re-verified, and executable browser-locally. The no-trade
invariant is enforced down to the wasm output. ZERO invariant amendments — keyless mirror DID
(G7 no-server-key), trustless CID re-verification, Murakumo-only narration all preserved.

# Alternatives Considered

- Shipping the 18.5MB componentize-py component as the browser-local artifact — rejected:
  dag-pb multi-block ≠ T1 raw single-block; bundling CPython is hostile to first-paint.
- kotobase pinning via the repo's `/api/v0/pin/add` client shape — rejected by reality (the
  deployed surface 404s it unauthed and the Worker only shims `/pins`); direct backend CACAO
  XRPC is the working path.
- Patching kotoba's pin worker this session — deferred: the fix is real (no-timeout await)
  but deployment of the pod is operator-gated, so a patch alone changes nothing today.

# References

- PR #1588 (squash-merged 2026-06-10) · prior wave PR #1533 / ADR-2606101540
- `20-actors/shionome/wasm/{shionome-core/,build-t1.sh}` · `50-infra/etzhayyim-did-web/public/actor/shionome/`
- `gftdcojp/net-kotobase` `worker/src/app.ts` (/pins shim) · kotoba `crates/kotoba-server/src/kotobase_xrpc.rs` (pin worker) · `crates/kotoba-store/src/ipfs_pin.rs` (no-timeout client)
