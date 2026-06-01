---
id: adr-2606015200-wasm-actor-runtime-round-2-dagpb-mesh-kanae-erc725
title: "ADR-2606015200: WASM-actor runtime round 2 — dag-pb CAR verify, mesh runner, kanae T1, ameno panel, ERC725 mirror, operator enablement"
status: accepted
doc_type: adr
topic: wasm-actor-runtime-round-2
authoritative: true
last_verified: 2026-06-01
priority: 6.1
axis: architecture
weight: 0.62
priority_note: "Completes the six next-steps from ADR-2606014800: dag-pb verification, mesh runner, 2nd T1 actor, ameno UI, on-chain vm mirror, operator runbook."
authoritative_for:
  - dagpb-car-verification
  - t2-mesh-runner
  - ameno-actor-panel
  - erc725-vm-mirror
depends_on:
  - 2606014600
  - 2606014500
  - 2606013800
  - 2605212030
  - 2605231525
related:
  - 2605302300
  - 2606011800
  - 2606012600
supersedes: []
superseded_by: []
---

# ADR-2606015200: WASM-actor runtime round 2

**Status**: accepted
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

ADR-2606014800 listed six next steps for the one-Worker WASM-actor runtime. This
ADR lands all six in one PR.

# Decision

**(2) dag-pb CAR verification — closes the T2 trustless gap.** `src/car.ts` parses
a CARv1, **verifies every block's `sha2-256`**, and reassembles the UnixFS file by
walking dag-pb links from the requested root — so multi-block `bafybei…` content is
now trustless too. The gateway (`/ipfs/<cid>`) fetches `?format=car` for dag-pb CIDs
and serves the reconstructed bytes (raw CIDs unchanged). Verified against a real
`ipfs dag export` CAR (620 KB / 3 leaves, exact reassembly) + 4 in-memory unit
tests (raw, dag-pb-over-2-leaves, tamper-rejection, missing-root).

**(6) T2 mesh runner.** `50-infra/e7m-wasm-runner` resolves an actor (DID/CID/file)
→ CID/CAR-verifies → runs it: core modules via `WebAssembly.instantiate` + the
`compute()` ABI, WASI components via `jco transpile`. The donated-mesh executor for
large (dag-pb) actors. 3 tests (kanae core end-to-end + core/component detector).

**(1) Second T1 actor — kanae.** `20-actors/kanae/wasm/kanae-core` (Rust→wasm,
23.9 KB, raw CID `bafkreielhr…jnie`) aggregates public fiscal-flow edges → top
recipients (NON-adjudicating; top = Prefectures). Registered as a new actor
(`did:web:etzhayyim.com:actor:kanae`, glyph 鼎) in the registry + seed; did.json
carries the `EtzhayyimWasmComponent` service tagged `x-exec: browser-local`. Proves
the T1 path generalizes beyond tsumugi.

**(3) ameno UI surface.** `@etzhayyim/ameno/inference/wasm-actor-panel` —
`mountActorPanel(el, {did})` (framework-free; resolve → fetch → CID-verify → run →
render; declines T2 dag-pb client-side) + pure `formatActorResult` (2 tests). A
runnable self-contained demo at `20-actors/ameno/demo/wasm-actor.html`.

**(5) On-chain ERC725 verificationMethod mirror.** `src/erc725.ts` —
`keccak256` (own impl, known-vector tested), `dwebHandleNode`,
`fetchOnChainVm(env, handle, did)` reads
`resolveDwebHandle(keccak256("<handle>.etzhayyim.com"))` via `eth_call` and maps the
active key to a secp256k1 verificationMethod. Wired into `resolveActorRecord`,
**gated** on `AUTHZ_CONTRACT_ADDRESS`+`BASE_RPC_URL`, best-effort (→ [] on any
failure). Never server-minted (ADR-2605231525). 3 tests (keccak vectors, node
derivation, key→vm mapping).

**(4) Operator enablement.** `scripts/enable-kv.sh` (`npm run enable-kv`: create
`ACTOR_KV` → publish records → deploy) + `RUNBOOK.md` consolidating the KV / kotoba
/ `IPFS_GATEWAYS` / ERC725 / mesh steps. These need Cloudflare/chain credentials →
operator-run.

# Consequences

- Trustless gateway now covers **both** T1 (raw) and T2 (dag-pb) content — no
  trusted party anywhere in the fetch path.
- A donated node can execute any actor (core or component) with CID-verified bytes.
- Two T1 browser-local actors (tsumugi, kanae) + the ameno panel give a real
  in-browser "run this actor" surface.
- The ERC725 vm mirror is wired and tested; it activates the moment the contract
  is deployed — no code change, no server key.
- Operator has a one-command path to promote did.json/profile to the kotoba source.
- Verification: worker `tsc` clean + 7 tests; runner 3 tests; ameno `tsc` clean +
  7 tests; kanae runs (Prefectures top); real ipfs CAR reassembles exactly.

# Honest scope (R0)

- CAR verification: sha2-256, CIDv1, raw + dag-pb UnixFS files (raw or dag-pb
  leaves) — the `ipfs add --cid-version=1` shape; exotic UnixFS (HAMT dirs, other
  hashes) out of scope.
- Mesh runner's libp2p `/x/etzhayyim/xrpc/1.0` transport is not yet wired (it runs
  + prints; serving over the mesh is the remaining step). watatsuna component
  binary stays gitignored (rebuild via its build.sh).
- ERC725: no live contract → returns [] in practice; `eth_call` itself untested
  (pure pieces are).
- kanae: bounded `:representative` fiscal seed (aggregate-only, non-adjudicating).
- #4 KV/chain enablement needs operator credentials (CF login / contract deploy).

# References

- `50-infra/etzhayyim-did-web/src/{car,erc725,cid}.ts` + `worker.ts` + `scripts/{car,erc725}.test.mjs` + `enable-kv.sh` + `RUNBOOK.md`
- `50-infra/e7m-wasm-runner/` · `20-actors/kanae/wasm/` · `20-actors/ameno/src/inference/wasm-actor-panel.ts` + `demo/wasm-actor.html`
- ADR-2606014800 (the six next steps), ADR-2606014600/14500/13800, ADR-2605212030 (ERC725), ADR-2605231525 (no-server-key), ADR-2605302300 (kanae)
