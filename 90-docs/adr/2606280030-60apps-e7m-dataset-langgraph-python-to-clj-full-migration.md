---
id: adr-2606280030-60apps-e7m-dataset-langgraph-python-to-clj-full-migration
title: "ADR-2606280030: 60-apps + e7m-dataset langgraph-python → clj full migration"
status: proposed
doc_type: adr
topic: 60apps-e7m-dataset-langgraph-clj-migration
authoritative: true
last_verified: 2026-06-27
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 60-apps-langgraph-clj-migration
  - e7m-dataset-clj-migration
depends_on: []
related:
  - adr-2606222000-etzhayyim-cli-babashka-port
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2606280030: 60-apps + e7m-dataset langgraph-python → clj full migration

**Status**: proposed
**Date**: 2026-06-27
**Deciders**: Jun Kawasaki

# Context

The repo-wide convention (CLAUDE.md § "Operational code = clj/bb over the kotoba Datom
log") is that first-party operational code SHOULD be Clojure on babashka over the kotoba
Datom log, NOT Python/shell. The actor tree (`20-actors`) was driven to **zero external
python-library dependencies** in a prior wave:

| external py lib | resolution | PRs |
|---|---|---|
| web3 / eth_account | new org lib `com-junkawasaki/eth-crypto-clj` (Keccak-256 / secp256k1 sign+recover / EIP-712 / EIP-55 / RLP / EIP-155 — pure clojure, spec-vector-verified) | #2608 #2610 #2614 #2615 |
| httpx | `babashka.http-client` (bb built-in) | #2612 |
| numpy/scipy/pandas/torch | none in the actor tree | — |

The **last sanctioned in-flight migration** is the `etzhayyim.cli` babashka port
(ADR-2606222000) — finishing it retires `70-tools/etzhayyim-py` (its ~40 `httpx` modules
already have clj twins on `babashka.http-client`).

Beyond those, the remaining first-party Python is concentrated in **`60-apps/*`
(LangGraph product apps) and `70-tools/e7m-dataset` (dataset fetchers)**. Unlike the
actor tree these are **actively developed** (many committed 2026-06-27) Python LangGraph
apps with **no cljc twins yet**. They were previously left as "convert opportunistically."
This ADR records the founder decision (2026-06-27) to **fully migrate them to Clojure**,
making the whole first-party codebase clj/bb-native.

# Decision

**Migrate all `60-apps/*` LangGraph Python apps + `70-tools/e7m-dataset` from Python to
Clojure**, using the pattern established in the actor-tree wave:

- **LangGraph Python → `langgraph-clj` StateGraph.** Each app's `lg/` graphs/nodes/state
  port to `io.github.com-junkawasaki/langgraph-clj` (already a `bb.edn`/`deps.edn` dep).
  Reference shape: the 3 actor StateGraphs (robotaxi-actor / gftd-talent-actor /
  ai-gftd-itonami) + `kaname.graph`.
- **`httpx` → `babashka.http-client`** (no new dep; the actor-tree pattern).
- **State → kotoba Datom log** where the app holds state (per ADR-2605312345), Murakumo
  inference default (per ADR-2605215000 / 2606172359), `cheshire` for JSON.
- **Worktree-isolated, one app = one PR.** Each app migrates in its own git worktree off
  `origin/main` (CLAUDE.md worktree-isolation rule, critical here because the apps are
  under active development); each lands as its own reviewable PR with the app's tests green
  under bb. `.py` is removed only when its cljc twin is verified and nothing imports it
  (coexist + report otherwise — the actor-tree discipline).
- **Full fan-out orchestration, in waves.** The migration runs as multi-agent fan-out
  (founder-selected "全アプリ一括 fan-out", 2026-06-27); because 52 apps span hundreds of
  Python files and are actively developed, it executes in **waves by size/risk**, this ADR
  the tracking SSoT. No silent truncation: every app's status is recorded below.

## Scope — full inventory (52 apps + e7m-dataset)

`lg` = has a LangGraph `lg/` graph dir (primary targets). `httpx` = HTTP files to repoint.
Status: ⬜ pending · 🟡 in-flight · ✅ migrated (cljc twin verified, .py retired/coexist).

| app | py | httpx | lg | status |
|---|---|---|---|---|
| etzhayyim-project-mangaka | 96 | 6 | ✓ | 🟡 partial #2649 |
| etzhayyim-project-animeka | 44 | 14 | ✓ | 🟢 twin #2652 |
| etzhayyim-project-open-ot | 32 | 0 | | ⬜ |
| etzhayyim-project-yukkuri | 25 | 12 | ✓ | 🟢 twin #2648 |
| kotoba-erp | 23 | 0 | | ⬜ |
| etzhayyim-project-maps | 22 | 0 | | ⬜ |
| etzhayyim-project-jukyu | 21 | 1 | ✓ | 🟢 twin #2651 |
| etzhayyim-project-states | 20 | 0 | | ⬜ |
| etzhayyim-project-hakken | 19 | 10 | ✓ | 🟡 partial #2650 |
| ai-gftd-chat-shell | 17 | 2 | ✓ | 🟢 twin #2631 |
| etzhayyim-chat-shell | 17 | 2 | ✓ | 🟢 twin #2634 |
| etzhayyim-project-kyber | 17 | 3 | ✓ | 🟢 twin #2632 |
| etzhayyim-project-open-robo | 16 | 0 | | ⬜ |
| etzhayyim-project-common-crawl | 16 | 2 | | ⬜ |
| etzhayyim-project-docs | 14 | 2 | ✓ | 🟢 twin #2627 |
| etzhayyim-project-sheets | 14 | 2 | ✓ | 🟢 twin #2626 |
| etzhayyim-project-media-gamers | 13 | 4 | ✓ | 🟢 twin #2629 |
| etzhayyim-project-calendar | 12 | 2 | ✓ | 🟢 twin #2625 |
| etzhayyim-project-narou | 12 | 2 | ✓ | 🟢 twin #2623 |
| etzhayyim-project-webmk | 12 | 1 | ✓ | 🟢 twin #2620 |
| etzhayyim-organism-viz | 11 | 0 | | ⬜ |
| etzhayyim-project-drive | 11 | 2 | ✓ | 🟢 twin #2624 |
| etzhayyim-project-patent | 11 | 0 | ✓ | 🟢 twin #2640 |
| etzhayyim-project-x | 11 | 3 | ✓ | 🟢 twin #2628 |
| etzhayyim-project-open-isic | 10 | 0 | ✓ | 🟢 twin #2639 |
| etzhayyim-project-open-patent | 10 | 0 | ✓ | 🟢 twin #2642 |
| etzhayyim-project-recap | 10 | 1 | ✓ | 🟢 twin #2622 |
| etzhayyim-project-dougaka | 8 | 1 | ✓ | 🟢 twin #2621 |
| etzhayyim-project-lawfirm | 7 | 0 | ✓ | 🟢 twin #2636 |
| etzhayyim-project-open-jpn-mynumber | 7 | 0 | ✓ | 🟢 twin #2644 |
| etzhayyim-project-browser | 6 | 1 | | ⬜ |
| spirit-in-physics | 6 | 0 | | ⬜ |
| etzhayyim-project-vpn | 5 | 1 | | ⬜ |
| etzhayyim-project-comfyui | 4 | 2 | | ⬜ |
| etzhayyim-project-curpus2skill | 4 | 0 | ✓ | 🟢 twin #2637 |
| etzhayyim-project-karma | 4 | 0 | ✓ | 🟢 twin #2638 |
| etzhayyim-project-kenkyusha | 4 | 0 | ✓ | 🟢 twin #2641 |
| etzhayyim-project-ki | 4 | 0 | ✓ | 🟢 twin #2646 |
| etzhayyim-project-legal-entity | 4 | 0 | ✓ | 🟢 twin #2643 |
| etzhayyim-project-pregel | 4 | 0 | ✓ | 🟢 twin #2647 |
| etzhayyim-project-public-domain-colorization | 4 | 0 | ✓ | 🟢 twin #2645 |
| etzhayyim-project-web4 | 3 | 0 | | ⬜ |
| etzhayyim-project-murakumo | 2 | 0 | | ⬜ |
| etzhayyim-project-okaimono | 2 | 0 | | ⬜ |
| etzhayyim-project-onion | 2 | 0 | | ⬜ |
| etzhayyim-project-open-unispsc | 2 | 0 | | ⬜ |
| etzhayyim-project-ma | 1 | 0 | | ⬜ |
| etzhayyim-project-ohanashi | 1 | 0 | | ⬜ |
| etzhayyim-project-open-saas | 1 | 0 | | ⬜ |
| etzhayyim-project-real-estate | 1 | 0 | | ⬜ |
| etzhayyim-project-runpod | 1 | 1 | | ⬜ |
| etzhayyim-project-search | 1 | 0 | | ⬜ |
| etzhayyim-project-telecom | 1 | 0 | | ⬜ |
| **70-tools/e7m-dataset** | 57 | 45 | | ⬜ |

## Pattern (per-app recipe)

1. Worktree off `origin/main`; one app per agent.
2. Port `lg/<app>/graphs/*` → `langgraph-clj` StateGraph (`:nodes`/`:edges`/`interrupt-before`);
   nodes → clj fns; state → a map/kotoba Datom log.
3. `httpx` calls → `babashka.http-client`; JSON → `cheshire`; LLM → Murakumo loopback
   (`babashka.http-client`, no-server-key read-only where possible).
4. Port the app's tests to `clojure.test` (`run_tests.clj`, repo rule — not `.sh`).
5. Verify under bb: every cljc ns loads; `run_tests.clj` green.
6. Remove `.py` only when its cljc twin is verified + unreferenced (grep-confirmed);
   coexist + note otherwise. Update `pyproject.toml`/`requirements`/deploy refs.
7. One PR per app; this ADR's status table updated as each lands.

# Consequences

- **+** First-party codebase becomes clj/bb-native end-to-end; httpx/python-langgraph
  eliminated; apps inherit kotoba as-of state + content-addressed snapshots + crash-resume.
- **+** One reusable langgraph-python→langgraph-clj recipe across all apps.
- **−** Large program (52 apps, hundreds of files); runs in waves, not one pass.
- **−/risk** The apps are under active development (committed 2026-06-27); worktree
  isolation + per-app PRs bound the blast radius, but a migration PR may need rebasing on
  in-flight app work. Each app owner reviews its PR.
- **Reversible** per app (each is its own PR; coexist-until-verified means no app is left
  broken).

# Tracking

This ADR is the migration SSoT. Each wave appends its landed PRs here. The fan-out is
driven by multi-agent orchestration; per-app status lives in the inventory table above.

## Wave log

- **Wave 1 (2026-06-27)** — 13 small/medium lg apps migrated to langgraph-clj twins
  (additive, coexist; python still deployed). All bb-verified green; merged #2620–#2634:
  webmk #2620, dougaka #2621, recap #2622, narou #2623, drive #2624, calendar #2625,
  sheets #2626, docs #2627, x #2628, media-gamers #2629, ai-gftd-chat-shell #2631,
  kyber #2632, etzhayyim-chat-shell #2634. **httpx not yet eliminated** — each app's
  deployment cutover (langgraph.json/Dockerfile/Helm → clj runtime + retire .py) is a
  dedicated follow-up pass after all twins are built.
