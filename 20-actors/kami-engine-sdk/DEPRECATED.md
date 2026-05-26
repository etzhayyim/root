# 20-actors/kami-engine-sdk — DEPRECATED (retire by Phase 3 of ADR-2605265200)

This directory is a **legacy duplicate** of the canonical `@etzhayyim/kami-engine-sdk`.
The canonical source is `40-engine/kami-engine/kami-engine-sdk/` (a git subrepo of
`github.com/gftdcojp/kami-engine-sdk`).

## Status

| Phase | What | Status |
|---|---|---|
| 1 | This file + canonical SDK added to `pnpm-workspace.yaml` | 🟢 active (2026-05-26) |
| 2 | Verify all consumers (`workspace:*` + `link:`) resolve to canonical | ⏳ pending (~7 days) |
| 3 | `git rm -r 20-actors/kami-engine-sdk/` | ⏳ pending Phase 2 close |

See **ADR-2605265200** (`90-docs/adr/2605265200-kami-engine-sdk-20-actors-legacy-duplicate-retirement.md`) for the full retirement plan, alternatives considered, and consequences.

## Why this exists at all

`20-actors/kami-engine-sdk/` predates the migration of the SDK to its own publishable npm package (`github.com/gftdcojp/kami-engine-sdk`, vendored back into this monorepo as a git subrepo at `40-engine/kami-engine/kami-engine-sdk/`). When the subrepo migration happened, the `20-actors/` copy was left in place to avoid breaking in-flight references; it was never cleaned up.

## Why retire now (2026-05-26)

The 2026-05-26 SDK three-free cutover (ADR-2605264300, commits `b04c54eb5` + `ea0fd3ab8` + `5d2ba4b2d`) only landed in the 40-engine canonical. The 20-actors copy diverged:

- missing `src/lib/gsplat/` (3DGS preview bridge)
- missing `src/lib/webvr/` (headless incident-response engine)
- missing `src/lib/genko/canvas-pregel.ts` (LangGraph genko pipeline)
- `src/lib/builders/createBoneController.svelte.ts`, `createConversationController.svelte.ts`, `createMorphController.svelte.ts`, `createVrmEngine.svelte.ts` all carry the **pre-three-free** `ThreeVrmHandle` / `state.three` API
- `src/lib/types/engine.ts` still declares the retired `ThreeVrmHandle` interface
- `src/ambient.d.ts` still declares `declare module 'three'` (a stub block ADR-2605264300 removed)
- `package.json` partially reflects 2026-05-26 cleanup (no `three` peerDeps) but lacks the canonical's `gsplat` + `wgpu` keywords + langgraph mandatory-peer-dep change

This divergence is a **dangerous structural condition**: both `package.json` files declare `name: "@etzhayyim/kami-engine-sdk"`. If anyone adds either path to a pnpm workspace, the workspace will see a duplicate-name situation and pick one arbitrarily. The selection might land on this outdated copy, silently rolling back the three-free cutover.

## Until Phase 3 deletes this directory

Do **not** edit files under `20-actors/kami-engine-sdk/`. Use the canonical at `40-engine/kami-engine/kami-engine-sdk/` for any SDK change. If you import from `@etzhayyim/kami-engine-sdk` in a consumer app, depend on the workspace-registered canonical path (Phase 1 update).

If you need a feature that is missing from this stale copy (e.g., `./webvr` or `./gsplat`), depend on the canonical — those features only exist there.
