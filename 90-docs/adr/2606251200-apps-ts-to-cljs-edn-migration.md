---
id: adr-2606251200-apps-ts-to-cljs-edn-migration
title: "ADR-2606251200: 60-apps TypeScript → ClojureScript + EDN migration"
status: proposed
doc_type: adr
topic: apps-ts-to-cljs-edn-migration
authoritative: true
last_verified: 2026-06-25
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "実装/engineering convention (changeable at the impl layer; not a charter invariant)"
authoritative_for:
  - 60-apps language/data-format direction (app/frontend layer)
depends_on:
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2606222000-etzhayyim-py-cli-bb-migration
  - adr-2606072802-tsubasa-r3-no-new-shell
supersedes: []
superseded_by: []
---

# ADR-2606251200: 60-apps TypeScript → ClojureScript + EDN migration

**Status**: proposed
**Date**: 2026-06-25
**Deciders**: Jun Kawasaki

# Context

The repo's lower layers have converged on **one language + one data format**:

- **State** is the **kotoba Datom log = EDN**, first-class canonical state (ADR-2605312345),
  over the kotoba substrate engine (ADR-2605262130) — not RisingWave/JSON DBs.
- **Operational/daemon/tooling code = Clojure on babashka** over that Datom log
  (repo-wide rule, CLAUDE.md §"Operational code = clj/bb"). The py→cljc and
  py-CLI→bb port waves (e.g. ADR-2606222000) carried the actors + tools to clj.
- **Actors** are increasingly clj-native (`*.cljc` methods + `kotoba.datom` ledger).

The **app / frontend layer (`60-apps/`) is the remaining TypeScript island.** Measured
on `main` 2026-06-25 (excluding `node_modules`/build output):

| layer | language surface |
|---|---|
| `60-apps/` (573 app dirs) | **ts 2,701 · tsx 177 · svelte 486 · js 376 ≈ 3,740 files** · cljs 33 · cljc 5 · clj 10 (≈1%) |
| `40-engine/` | **rust 34** (kami-engine / kotoba — generic engines) · ts 108 · svelte 110 |

This island carries a **second type system, a second runtime, and JSON/TS config that
re-declares shapes already defined in the EDN substrate** (lexicons, manifests,
ontologies). New app code defaults to TS, so the gap widens, not closes.

There are already **cljs footholds** to build the pattern on: `etzhayyim-project-explorer`
(clj `src/` **and** `test/`), `etzhayyim-organism-viz`, and the `lg/` (langgraph-cljs)
graphs under `animeka` / `kyber` / `mangaka`.

**Scope boundary.** `40-engine/` Rust (kami-engine physics/sim, kotoba storage substrate)
is a *different concern* — generic engines living in separate submodule repos. It stays
Rust and is **out of scope**. This ADR governs the **app/frontend layer (`60-apps`) only.**

# Decision

1. **Adopt ClojureScript + EDN as the default for NEW `60-apps` code**, and migrate
   existing apps **incrementally**. There is **no big-bang rewrite** of 573 apps — at
   3,740 files that is unmanageable and would strand apps half-migrated.

2. **EDN-first ordering.** Migrate **data before logic**: an app's config / manifest /
   schema / lexicon moves TS/JSON → **EDN** first. The substrate state is already EDN, so
   this removes the JSON↔EDN double-definition and makes app config queryable as Datoms.

3. **Tooling = squint/cherry preferred, shadow-cljs reserved.** The cljs→JS path should
   default to **squint / cherry** (ClojureScript *syntax* → lightweight JS, minimal/no
   runtime) to fit the **WASM-32 + edge-target** constraints already binding the platform
   (baien edge-target invariant; ameno browser-local; one-Worker/many-WASM-actors).
   **shadow-cljs** is reserved for apps that genuinely need the full cljs runtime/REPL.
   The final pick is **PoC-gated** (a small TS module ported under squint/cherry, built
   and run on the edge/WASM target, before mass adoption).

4. **Reference pilot + shared SDK.** `etzhayyim-project-explorer` (already clj `src`+`test`)
   is completed as the **canonical TS→cljs+edn reference pattern**, from which a shared
   **cljs app-SDK** (`@etzhayyim/sdk` cljs face: lexicon shapes, validation, kotoba reads,
   AT-Proto/XRPC client) is extracted so subsequent apps inherit it.

5. **UI strategy is per-app, not mandated here.** SvelteKit-heavy apps (e.g. yoro) may keep
   a Svelte shell while moving *logic* to cljs first; greenfield UIs may use a cljs view lib
   (reagent / replicant / uix). The view layer choice is deferred to the pilot.

6. **Enforced-forward, shrinks-only** (mirrors `lint:no-new-shell`, ADR-2606072802).
   Once an app is piloted/migrated, a lint flags **NEW first-party TS** in it; existing TS
   is **grandfathered** in a baseline that only shrinks (port a file → delete it →
   `--update`). Un-migrated apps are untouched until their wave.

7. **Classification.** This is an **実装/engineering convention**, not a charter invariant —
   changeable at the implementation/governance layer without a charter amendment (the
   substrate-boundary table in root CLAUDE.md). It does not alter any Tier-0/Tier-1 rule.

# Consequences

- **+** One language (clj/cljs/cljc) and one data format (EDN) across substrate → actor →
  app; the JSON/TS shape-duplication disappears; app config becomes queryable Datoms.
- **+** cljc code (validation, lexicon shapes, pure logic) is **shared** between the
  bb/clj actor side and the cljs app side — write once, run both.
- **+** Aligns the app layer with the kotoba canonical-state direction and the existing
  py→cljc / py→bb waves; new app code stops widening the gap.
- **−** Large surface (~3,740 files / 573 apps): the migration is **multi-wave and
  long-horizon**; risk of half-migrated apps (mitigated by EDN-first + per-app waves +
  shrinks-only lint, never a forced global cutover).
- **−** Build/tooling complexity: a cljs build is added to the TS/Svelte pipelines; team
  ClojureScript ramp-up.
- **−** UI-framework story is unresolved for SvelteKit-heavy apps (handled per-app, gated
  on the pilot).

# Alternatives Considered

- **Big-bang rewrite of all 573 apps** — rejected: unmanageable surface, would strand apps.
- **Stay TypeScript, bridge only via an SDK** — rejected: perpetuates the second
  type-system + second runtime; the JSON↔EDN double-definition remains.
- **Keep TS but adopt a TS EDN library** — rejected: unifies the *data format* only, not
  the *language*; cljc code can't be shared with the clj actor side.
- **shadow-cljs everywhere** — deferred, not rejected: its runtime weight is at odds with
  the edge/WASM target; squint/cherry is preferred for the default path, shadow-cljs kept
  for runtime/REPL-heavy apps. Settled by the tooling PoC.

# References

- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605262130 — kotoba storage-substrate unification (no RisingWave)
- ADR-2606222000 — etzhayyim py-CLI → bb migration (prior language-cutover wave)
- ADR-2606072802 — tsubasa R3 `lint:no-new-shell` (shrinks-only enforced-forward pattern)
- root `CLAUDE.md` §"Operational code = clj/bb over the kotoba Datom log" + Substrate-boundary table
- Surface measurement: `main` 2026-06-25 (this ADR's Context table)
