---
id: adr-2607011300-nv-compat-relocation-to-kotoba-lang
title: "ADR-2607011300: nv-compat relocation from etzhayyim-sdk to kotoba-lang/kami-nv-compat"
status: accepted
doc_type: adr
topic: nv-compat-relocation
authoritative: true
last_verified: 2026-07-01
priority: 3.0
axis: architecture
weight: 0.30
priority_note: "Housekeeping/placement ADR, not a design change to the facade itself."
authoritative_for:
  - kami-nv-compat repo location
  - kami-isaac-sim-wasm (kotoba-lang/kami-engine)
depends_on:
  - adr-2605261800-nvidia-omniverse-stack-api-compat
related:
  - adr-2606011500-kami-engine-reusable-vs-repo-specific-separation-plan
supersedes: []
superseded_by: []
---

# ADR-2607011300: nv-compat relocation from etzhayyim-sdk to kotoba-lang/kami-nv-compat

**Status**: accepted
**Date**: 2026-07-01
**Deciders**: Jun Kawasaki

# Context

`20-actors/etzhayyim-sdk/src/nv-compat/` (ADR-2605261800) is the TypeScript +
WGSL API-compat facade for NVIDIA Omniverse / Isaac Sim / Isaac Lab / OptiX /
RTX Renderer / Replicator / DriveSim / Omniverse Cloud / Nucleus / Alpamayo,
backed by KAMI-native canonical engines. It carries no etzhayyim-specific
business logic — no religious-corp identity, no CACAO auth, no charter
governance flow. It is generic robotics/rendering/simulation tech: WGSL
compute kernels, Featherstone articulated dynamics, a USD reader, a
Replicator-style domain-randomization sampler, drive-sim sensor models, an
extension-loader app shell, and a content-addressed store client.

The superproject's org taxonomy (ADR-2606302300, `manifest/repos.edn`)
partitions repos along "what kind of thing": `kotoba-lang` is the
language/substrate home consumed by all orgs (already hosting the sibling
`kami-engine` Rust workspace this facade's own README points to as the
longer-term backend — `kami-genesis`, `kami-articulated`, `kami-rt`,
`kami-usd`, etc.); `etzhayyim` is for agent-centric, public-interest actors.
The taxonomy's stated placement rule is explicit: "any library/substrate ...
→ kotoba-lang". `kami-engine` and `kami-engine-sdk` already made this move
(ADR-2606011500); nv-compat had not.

A grep across the whole `etzhayyim/root` monorepo found zero code-level
consumers of `20-actors/etzhayyim-sdk/src/nv-compat/` outside the facade's
own `test/` and `examples/` — it was never wired into `@etzhayyim/sdk`'s
public `package.json` exports map, nor imported by any actor
(wadachi/suki/sarutahiko/etc. still reference it only in ADR prose as a
future consumer). Relocating it now, before real consumers exist, is the
cheapest time to do it.

# Decision

Physically relocate `20-actors/etzhayyim-sdk/src/nv-compat/` (39 test files /
486 tests, 15 example HTML demos + README, ~15K lines of source) to a new
standalone repo **`kotoba-lang/kami-nv-compat`**, as-is (TypeScript + WGSL,
git history not preserved — see Alternatives Considered).

- New repo layout flattens the old `src/nv-compat/*` up to its own `src/*`
  root (so `omni-usd.ts`, `isaac-sim.ts`, `kami-rt/`, `dynamics/`, `warp/`,
  etc. become top-level); `test/` and `examples/` follow the same flattening,
  with internal relative imports (`../src/nv-compat/X` → `../src/X`)
  rewritten accordingly.
- npm package name kept in the `@etzhayyim/` scope
  (`@etzhayyim/kami-nv-compat`) per the `@etzhayyim/kami-engine-sdk`
  precedent — npm publish scope is a separate concern from which GitHub org
  hosts the source.
- License carried over unchanged: Apache 2.0 + Charter Compliance Rider v3.6
  (`LICENSE` / `CHARTER-RIDER.md` / `NOTICE` copied verbatim from
  etzhayyim/root's canonical copies), matching the `kami-engine` /
  `kami-engine-sdk` / `kotoba` precedent of kotoba-lang repos still carrying
  the Rider despite living outside the `etzhayyim` GitHub org — the Rider is
  a licensing condition Jun Kawasaki attaches to the code, independent of
  which org hosts it.
- `CHARTER-RIDER.md` §7.1's trademark-facade-namespace pointer updated (both
  in this repo and in the new repo's copy) from
  `20-actors/etzhayyim-sdk/src/nv-compat/` to `kotoba-lang/kami-nv-compat`.
- Registered in `manifest/repos.edn` (`:extra-projects`, `kotoba-lang`
  remote) + `manifest/west.yml` regenerated or the superproject.
- `etzhayyim-sdk` gets no new dependency: since nothing in the monorepo
  imported nv-compat via `@etzhayyim/sdk`'s own exports, there was nothing to
  rewire to point at the new package. `git rm -r src/nv-compat test/
  examples` is the entire etzhayyim-sdk-side diff (plus the CHARTER-RIDER.md
  pointer). `npm run typecheck` / `npm test` both stay green (143 tests,
  down from including nv-compat's now-relocated 486).
- ADR-2605261800 is **not** rewritten: its D1-D12 decisions (canonical KAMI
  names, trademark boundary, phase plan, Genesis backend choice, etc.) still
  govern the facade's design wherever it lives. Only this ADR's own
  `authoritative_for` path list and the two CHARTER-RIDER.md path references
  needed updating; ADR-2605261800's own body is left as the historical record
  of what was decided and where it was first built.

## Amendment (2026-07-01): `kami-isaac-sim-wasm` attempted, then superseded same day

Per Consequences' forward pointer below, a first concrete slice of the
eventual Rust `kami-engine` backend swap (A2) was attempted the same day as
the relocation — and then overtaken by a bigger, independent decision before
it could land. Recorded here for the honest trail, not as a completed step.

- Built **`kami-isaac-sim-wasm`**: a wasm-bindgen bridge generalizing the
  existing `kami-cartpole-wasm` precedent (fixed Cartpole topology only) to
  load **any** URDF, exposing `kami-genesis::IsaacWorld` /
  `ArticulationView(Mut)` / `ArticulationController` (RNEA/CRBA Featherstone
  dynamics + PD control — 208 tests in `kami-genesis` alone, cross-validated
  against cartpole / double-pendulum / arm fixtures) directly to JS.
  Verified end-to-end at the time: 4 native `cargo test` cases, a
  `wasm-pack build --target nodejs` success, and a vendored copy of that
  build driving 4 passing Node/vitest tests in `kami-nv-compat`
  (`test/isaac-sim-wasm-bridge.smoke.test.ts` — kept as a record of the
  approach; `vendor/kami-isaac-sim-wasm/README.md` documents it as
  proof-of-bridge only, never wired into the public API).
- **Never pushed to `kotoba-lang/kami-engine`.** Before pushing, a fresh
  fetch surfaced commit `34f43af` ("Remove Rust workspace from kami-engine
  (#82)", Jun Kawasaki, 2026-07-01 11:33 JST) — predating this crate's local
  build but not yet picked up by the local `west`-pinned checkout (pinned
  behind, so `cargo test` still ran against the old, now-removed Rust tree).
  `kami-engine`'s `main` now carries **zero `.rs`/`Cargo.toml` files**; its
  README states the Rust workspace is gone and native runtimes should live
  in adapter repositories consuming the CLJ/EDN/WIT/fixture assets kept
  there instead. Per owner direction: kami-engine (and the broader
  `kotoba-lang` org) is moving off Rust entirely toward Kotoba/Clojure —
  `kami-webgpu` ("no Rust/wasm", pure EDN render-IR) and `kototama`
  (Clojure/EDN → WebAssembly compiler) are the emerging replacement pattern
  for what `kami-genesis` used to do in Rust. No CLJ port of the
  Featherstone articulated-dynamics solver exists yet as of this writing.
- **This invalidates the A2/Consequences framing below** ("same-org Rust
  refactor" is no longer the direction) and the earlier survey this ADR's
  Decision section leaned on (`kami-genesis`'s 208 Rust tests no longer
  exist in the repo). The `kami-isaac-sim-wasm` source is kept locally
  (uncommitted to any shared branch beyond a personal `kami-engine` clone)
  as a reference for whatever eventually reimplements this surface in CLJ —
  it is not on a path to being merged as Rust.

## Amendment (2026-07-01, later same day): the named replacement pattern has no execution layer either

A follow-up survey of `kotoba-lang`'s WASM/UI/HTML/CSS/browser repos (12
repos checked directly, org-wide sweep of 157) found that the first
amendment's own proposed replacement path — "`kototama` (Clojure/EDN →
WebAssembly compiler) are the emerging replacement pattern for what
`kami-genesis` used to do in Rust" — is itself hollowed out, same day:

- `kotoba-lang/kototama`'s most recent commit (2026-07-01) is **"Remove
  Rust wrapper (#14)"** — the Cargo/wasm-bindgen compiler that actually did
  Clojure→WASM compilation is gone. What remains is a pure CLJC
  "authority/contract" layer (`kototama.contract` host-capability grants +
  an organism/cell runtime), not an executor. Real WASM execution is
  explicitly deferred in its own README to unspecified future "host adapter
  repos."
- `kotoba-lang/aiueos` ("Capability-secure Wasm component OS —
  Kotoba-defined, Kototama-executed") had the identical pivot the same day:
  **"Remove Rust runtime from aiueos authority (#14)"** — its Cargo/QEMU
  smoke scripts are gone too, leaving EDN-only component-manifest/policy
  contracts and an explicit README statement that "runtime implementations,
  Wasm engines, VM boot flows, browser adapters ... live in host adapter
  repositories" that do not yet exist in the org.
- So as of this writing, **no repo in `kotoba-lang` executes Clojure (or
  anything else) as WASM.** `kototama`'s and `aiueos`'s own contract layers
  are real and tested, but the "Kototama-executed" half of that sentence is
  currently aspirational, not a name for a working thing this ADR (or any
  future `kami-nv-compat` backend swap) could depend on today.
- Adjacent, non-substituting data points from the same survey, for whoever
  picks this up next: `kotoba-lang/wasm-ui` ("kotoba DOM-compatible WASM UI
  substrate") is real, tested CLJC code with its own WIT-shaped ABI
  contract — but its shipped renderers are plain ClojureScript (shadow-cljs
  → JS), not `.wasm` binaries; "WASM" there names a *future guest ABI*, not
  the current execution model. `kotoba-lang/kami-webgpu` (declarative
  WebGPU from EDN, "no Rust/wasm") is the most mature/active repo in that
  survey and the closest thing to a working CLJS-drives-GPU precedent, but
  it targets 3D scenes/games, not a general compute/dynamics backend, and
  has no cross-reference to `wasm-ui`, `kototama`, or this ADR's concerns.
- **Net effect on this ADR's own forward pointer**: the amendment above
  said "whatever eventually backs `kami-nv-compat`'s facade beyond its own
  TypeScript will most likely be CLJ/CLJC (via `kototama`'s Clojure→WASM
  path)." That target now has no executor to route through. This ADR
  records that gap rather than picking a new target — there is no CLJ/CLJC
  Featherstone-dynamics or WASM-execution substrate anywhere in `kotoba-lang`
  today for a future amendment to point `kami-nv-compat`'s backend at.

# Consequences

- `kami-nv-compat` becomes independently versioned and installable by any
  future consumer (a robotics actor, a different org's app) without pulling
  in the rest of `@etzhayyim/sdk` (AT Protocol / IPFS / Base L2 / payments —
  none of which nv-compat needs).
- Git history for the facade was not preserved: the local `etzhayyim/root`
  checkout is a shallow clone (`clone-depth: 1`) that only exposed a single
  commit of history for this path, so `git subtree split` / `git
  filter-repo` would have needed a full unshallow fetch of the whole
  170+-actor monorepo for a facade whose real development history (the D12
  amendment's "iter 71–109" trail) already sits past the shallow boundary.
  The ADR trail (2605261800 + this ADR) is the durable record of *why* and
  *when*; per-line blame is not preserved.
- **Superseded same day, see amendment below**: ADR-2605261800 §D6/§D7's
  planned Rust `kami-engine` backend (`kami-genesis`/`kami-articulated`/
  `kami-rt`/`kami-usd`) no longer exists — `kami-engine` dropped its entire
  Rust workspace on 2026-07-01 in favor of a Kotoba/Clojure direction. The
  Isaac Sim slice got a working Rust proof-of-bridge the same day
  (`kami-isaac-sim-wasm`) that was never merged as a result. Whatever
  eventually backs `kami-nv-compat`'s facade beyond its own TypeScript will
  most likely be CLJ/CLJC (via `kototama`'s Clojure→WASM path), not Rust.

# Alternatives Considered

## A1. Preserve git history via `git subtree split` / `git filter-repo`

Rejected for now: the local `etzhayyim/root` clone is shallow
(`clone-depth: 1`), and `git log -- 20-actors/etzhayyim-sdk/src/nv-compat`
showed only 1 commit locally. Unshallowing the whole monorepo just to recover
blame for one facade was judged disproportionate. Running `git filter-repo`
inside a linked worktree was also rejected as unsafe — it rewrites all
refs/objects in the shared `.git`, which would have clobbered other
concurrent agents' worktrees sharing the same object store.

## A2. Port to Rust (`kami-engine`) instead of relocating TypeScript as-is

This is ADR-2605261800's own eventual plan (§D6/§D7) and remains the
longer-term direction. Rejected as the *first* move here: a TS→Rust port of
~15K lines with 486 passing tests is 5-10× the effort of a same-language
relocation (cf. ADR-2605261800 §D10.5's "from-scratch fallback" honesty
framing) and was not what was asked for. Physically relocating first (this
ADR), then porting backend-by-backend into the already-registered
`kotoba-lang/kami-engine` crates later, de-risks the bigger move.

## A3. Leave nv-compat in etzhayyim-sdk, just document the taxonomy exception

Rejected: ADR-2606302300's placement rule is unconditional ("any
library/substrate → kotoba-lang"), nv-compat has zero etzhayyim-specific
coupling (confirmed by the zero-remaining-references grep), and `kami-engine`
/ `kami-engine-sdk` already set the precedent of making this exact move for
adjacent code.

# References

- ADR-2605261800 (NVIDIA Omniverse stack API-compat layer — design authority,
  unchanged by this move)
- ADR-2606011500 (kami-engine reusable-vs-repo-specific separation plan —
  precedent for TS-SDK/Rust-engine relocation to kotoba-lang)
- ADR-2606302300 (org-taxonomy 4-orgs — the library-placement rule this ADR
  executes)
- `kotoba-lang/kami-nv-compat` (new repo, `README.md` for provenance)
- `kotoba-lang/kami-engine/kami-isaac-sim-wasm` (new crate, first backend slice)
- `kotoba-lang/kami-nv-compat/vendor/kami-isaac-sim-wasm/README.md` (proof-of-bridge smoke test provenance)
- `kotoba-lang/kototama` (Clojure/EDN→WASM compiler — Rust wrapper removed 2026-07-01, contract-only as of this writing)
- `kotoba-lang/aiueos` (capability-secure Wasm component OS — Rust runtime removed 2026-07-01, contract-only as of this writing)
- `kotoba-lang/wasm-ui`, `kotoba-lang/kami-webgpu` (adjacent CLJS/EDN-driven browser-rendering precedents surveyed the same day; neither substitutes for a WASM-execution or Rust-dynamics backend)
