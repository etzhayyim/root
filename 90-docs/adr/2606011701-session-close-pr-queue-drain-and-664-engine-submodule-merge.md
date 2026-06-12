---
id: adr-2606011701-session-close-pr-queue-drain-and-664-engine-submodule-merge
renumbered_from: "2606011700"
title: "ADR-2606011701: Session close — full PR-queue drain (366 merged) + #664 in-tree↔submodule engine merge"
status: active
doc_type: adr
topic: ci-pr-hygiene
authoritative: false
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Documentation-only session-close record for the 2026-06-01 session that reviewed and merged every open PR (339 Dependabot + the #664 spirit-in-physics feature PR), fixed the pre-existing test-workflow break on main, and resolved the kami-engine in-tree↔submodule structural conflict losslessly across two repos."
authoritative_for:
  - session-close record for the 2026-06-01 PR-queue-drain + #664 merge session
depends_on:
  - adr-2606011500-kami-engine-reusable-vs-repo-specific-separation-plan
  - adr-2606011500-spirit-in-physics-kotoba-datafication
related:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312355-session-close-kotoba-datom-first-class-and-charter-rider-d1
supersedes: []
superseded_by: []
---

# ADR-2606011701: Session close — full PR-queue drain (366 merged) + #664 engine submodule merge

**Status**: active (documentation-only session-close record)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

Originating request: *「https://github.com/etzhayyim/root/pulls の PR review, merge」* then
*「すべて review, merge を進めて」* / *「conflict を解消しつつ merge」*. At session start the
repo had **339 open PRs** (all Dependabot) plus, surfacing mid-session, the founder's large
feature PR **#664** (`feat(spirit): datafy 霊性 … into datomic kotoba`, ~70k additions / 565 files,
bundling 7 ADRs + 2 new submodules).

Two structural facts shaped the work:

1. **`main` was already red.** The `test` workflow's `tsc (20-actors/etzhayyim-sdk-auth)` job had
   failed since 2026-05-29 (`TS2304: Cannot find name 'Request'/'fetch'`), and `audit-health`
   (`monorepo-health`) + `openot-gate-c` were independently red on pre-existing debt. Most
   "Dependabot-broke-it" reds were **inherited**, not bump-caused.
2. **#664 straddled the kami-engine extraction.** Per ADR-2606011500, `40-engine/kami-engine` was
   extracted to its own repo (`etzhayyim/kami-engine`) as a **submodule** on `main`, but #664 was
   based on pre-extraction `main` and still carried the engine **in-tree** — with ~1,200 lines of
   kami-genesis physics + 7 new modules + 4 app crates **not yet present in the extracted repo**.
   A naive "adopt the submodule" merge would have destroyed that research.

# Decision (what shipped this session)

**366 PRs merged; open PR count driven to 0.**

## Dependabot drain (361 + 4 follow-ups)
- Merged every green PR via an iterative rebase→CI-gate→merge orchestration (siblings share
  lockfiles, so winners merge and the rest auto-rebase in waves).
- Root-caused the dominant red: **PR #671** added `"DOM"` to `etzhayyim-sdk-auth/tsconfig.json`
  `lib`, fixing the pre-existing `fetch`/`Request` break and greening the whole `test` matrix —
  which unblocked a large batch of bumps that only *inherited* that failure.
- Real major-version migrations landed with their fixes (not bump-only):
  - **#674** `typescript ^6.0.3` + `tsconfig "types":["node"]` (TS6 dropped implicit `@types`
    inclusion) — superseded bump-only #408.
  - **#673** `vitest ^4.1.7` (regenerated lockfile to clear a stale conflict) — superseded #452.
  - **#625** `heapless 0.9`, **#667** `wasmtime → 36.0.8` (all open-ot build rigs green; the 2
    residual reds = pre-existing `openot-gate-c` debt). **#631** (`wasmtime 45`, breaks gate-a/b)
    closed in favor of #667.
  - `#670` reapplied a conflict-stuck `@types/node` bump (#335) conflict-free.

## #664 — lossless in-tree↔submodule reconciliation (across two repos)
- **`kami-engine#1`**: ported #664's kami-genesis maturation (modules `obb`/`mpm`/`ccd`/`convex`/
  `thermal`/`batched`/`wgpu_planar` + expanded `contact`/`articulation3d`/`planar_chain` + `lib.rs`
  wiring) into the canonical engine repo. Validated: `cargo test -p kami-genesis` = **143 passed /
  0 failed**.
- **`kami-engine#2`**: carried the 4 engine app crates (`kami-app-{giemon,giemon-factory,shibuya,
  tatekata}`) into the engine repo as preserved source (not yet `[workspace].members` — they need
  standalone asset-path adaptation). `kami-engine-sdk` was already a submodule there, untouched.
- **root#676**: bumped the `40-engine/kami-engine` submodule to the commit holding all the above,
  delivering the physics maturation to monorepo `main`.
- **#664 merge**: adopted the submodule (`40-engine/kami-engine` gitlink), `.gitmodules` union
  (kami-engine + spirit-in-physics submodules), `deps.toml` union (260 ADRs, TOML-valid),
  `90-docs/_registry/{docs.json,graph.jsonld}` regenerated from source (735 entries, freshness
  `--check` green). `lint-and-test` green → merged. Nothing lost.

# Consequences

- **`etzhayyim/root` open PRs = 0.** `main` HEAD advanced through #678.
- `etzhayyim/kami-engine` gained 2 PRs (#1 physics, #2 app crates); its submodule pin on `main`
  now reflects the merged engine work.
- **Known pre-existing debt (NOT introduced here, red on `main` independently):**
  - `monorepo-health` / `test_rollup_matches_baseline`: now **"expected 25, got 7"** — audit
    findings *dropped* (debt paid down by the Dependabot drain); the hardcoded baseline (25) is
    stale and should be lowered to ≤7 in a follow-up.
  - `openot-gate-c`: `builder-sign-rs` + `kani (vv-curve)` still red (pre-existing since 05-21).
  - `build-and-push` (container deploy) is non-blocking, not a correctness gate.
- The 4 carried app crates still reference monorepo asset paths (`70-tools/e7m-sim`, Shibuya OSM)
  and need standalone-fixture adaptation before they build inside the engine repo; preserved as
  source so that adaptation can proceed in-repo.

# Alternatives Considered

- **Force-merge #664 by adopting the submodule directly** — rejected: would have destroyed the
  in-tree kami-genesis physics + app crates not yet in the extracted repo.
- **Drop #664's engine edits as "stale"** — rejected after evidence showed the canonical repo was
  0 files ahead and #664 was strictly additive (a superset), so the work was unported, not
  superseded.
- **Force the red bumps in regardless** — rejected; CI-gated every merge instead and fixed the
  underlying `main` break (#671) so reds resolved at the source rather than being bypassed.

# References

- ADR-2606011500 (kami-engine reusable-vs-repo-specific separation plan — the extraction this merge reconciles against)
- ADR-2606011500 (spirit-in-physics kotoba datafication — #664's design)
- ADR-2605312355 (prior session-close; documented the audit-health pre-existing debt)
- ADR-2605262130 (kotoba storage substrate — registry/Datom context)
- `etzhayyim/kami-engine` PRs #1 (kami-genesis physics sync), #2 (4 app crates)
- `etzhayyim/root` PRs #671 (sdk-auth DOM lib fix), #673 (vitest 4), #674 (typescript 6), #676 (submodule bump), #664 (spirit merge)
