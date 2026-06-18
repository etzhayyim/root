---
id: note-260618-py-cljc-twin-migration-status
title: "py↔cljc twin-migration status — prune-safety triage (ADR-2606160842 port wave)"
status: active
doc_type: reference
topic: py-cljc-migration
authoritative: false
last_verified: 2026-06-18
related:
  - 90-docs/adr/2606160842  # py→clj port wave
---

# py↔cljc twin-migration status — prune-safety triage

The ADR-2606160842 py→clj port wave left several actors with **both** a `methods/X.cljc`
(substrate-native, run by `run_tests.sh`) **and** a `methods/X.py` twin. Two parallel
implementations of the same logic is a **drift risk** — it is exactly how the R2-autonomous
gate regressions slipped into twin files (FINDING 260617). The standing directive is
"py から clj, edn にしていたら py は prune" — but a `.py` twin may only be pruned when it is
**genuinely dead** (no live consumer beyond its own py test). This note records the per-actor
verdict so a future iteration does not naively prune a `.py` twin that still backs a live py
cell / analyze / ingest path (which would be a regression).

## Verdict (verified 2026-06-18)

| Actor | twins | `.py` consumer (beyond its py test) | prune-safe? |
|---|---|---|---|
| **kamado** | analyze, carbon_balance, ingest, feedstock_guard | analyze/carbon_balance/ingest = py-test-only → **PRUNED 2026-06-18**. feedstock_guard still imported by `cells/test_state_machines.py` → kept. | ✅ done (3 of 4) |
| **hikari** | microgrid, panel_install | `cells/grid_edge/state_machine.py` imports `microgrid`; `cells/solar_pv_install/state_machine.py` imports `panel_install` | ❌ NOT yet — py cells still live |
| **hydrogen_electrolysis** | electrolysis | `methods/analyze.py` + `kotoba/ingest_efficiency.py` import `electrolysis` | ❌ NOT yet — py analyze/ingest still live |
| **rasen** | analyze, cid, coverage_report, datom_emit, ingest | `wasm/app.py` imports analyze/datom_emit/coverage_report (live pywasm entrypoint); `publish.py` imports `cid` (py-only, no cljc twin) | ❌ NOT — py twins back the wasm app + publish.py (verified 2026-06-18) |
| **ibuki** | ~23 (autorun, datoms, kotoba_bridge, member_submit, …) | py is the **canonical R3 live impl** (root CLAUDE.md: autorun.py / kotoba_bridge.py verified live); cljc is the port-in-progress | ❌ NOT — py is canonical here |
| **tsumugi** | ~16 (analyze, ingest, publish, narrate, …) | no wasm/cells consumer, and the py-only influence layer (analyze_influence/ingest_influence) does NOT import the twins — BUT the **CLAUDE.md operator runbook invokes the py directly**: `python3 methods/autorun.py --cycles 1` (heartbeat) + `publish_ipfs.py --verify` (CLI). cljc is the tested port, not the operator default. | ❌ NOT — live operator runbook runs the py twins (verified 2026-06-18) |

## Net (verified 2026-06-18)

**kamado was the only clean prune.** All 5 other twin-actors have a LIVE py path the cljc has
not yet replaced — py cells (hikari), py analyze/ingest (hydrogen_electrolysis), the canonical R3
impl (ibuki), the wasm-app entrypoint (rasen), or the operator runbook/CLI (tsumugi). None is a
safe single-step prune today. Each is unblocked only by first migrating its specific live py
consumer to cljc (or repointing it at the cljc twin) — a focused per-actor task, not a /loop
one-liner. Until then, **do not prune** these twins (it would regress a live path).

## Safe prune procedure (per twin)

1. Confirm `run_tests.sh` runs the **cljc** suite (cljc is canonical) and it is green.
2. `grep` every `import X` / `from X import` across the actor's `*.py` (excluding `X`'s own
   py test + `__pycache__`). If the ONLY importer is `test_X.py`, the twin is dead.
3. Confirm a green `test_X.cljc` exists (cljc test parity).
4. Prune `X.py` **and** its now-orphaned `test_X.py`. Keep any py the cells/analyze/ingest still import.
5. Re-run `run_tests.sh` → must stay green.

## Worklist to unblock the ❌ actors

The `.py` twins there are live because the **cells / analyze / ingest** layer is still py.
To prune safely, first migrate those py consumers to cljc (or repoint them at the cljc twin),
then re-run the procedure above. Until then, leave the twins — pruning would break the py layer.
ibuki is a special case: its py IS the canonical live impl (R3 verified), so its cljc twins are
the migration target, not the prune target — do not prune ibuki's py.
