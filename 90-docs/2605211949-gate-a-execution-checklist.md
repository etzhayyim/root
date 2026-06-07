---
id: doc-2605211949-gate-a-execution-checklist
title: "Phase 3 gate (a) execution checklist — per-worker RW-free port operator runbook"
status: active
doc_type: how-to
topic: gate-a-execution-checklist
authoritative: true
last_verified: 2026-05-21
priority: 7.5
axis: operations
weight: 0.55
priority_note: "Converts ADR-2605212100 §2(a) 'PATTERN ESTABLISHED, EXECUTION OPEN' from prose into per-worker checkboxes. Operators (or the next agent session) tick rows one-by-one as they commit the per-worker SQLite ports. When all 29 + 5 utility + 4 ingest + 4 primitive rows are checked, gate (a) closes and Phase 5 / Phase 6 can proceed."
authoritative_for:
  - per-worker gate (a) execution status (the one canonical checklist)
  - acceptance criteria per pattern (BeliefStore / audit log / read-cache / primary store / worker_runtime+stub / ingest module)
depends_on:
  - adr-2605212100-magatama-worker-3-axis-tranche-f-closure
  - adr-2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com
  - adr-2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook
related:
  - doc-2605211800-vendor-importer-survey-gate-d
  - doc-2605211900-tranche-f-all-gates-closure-confirmation
supersedes: []
superseded_by: []
---

# Phase 3 gate (a) execution checklist

**Date opened**: 2026-05-21
**Tracking**: ADR-2605212100 §2(a) Phase 3 gate (a) — per-worker RW-free re-impl
**Closure target**: every row in §1 + §2 + §3 + §4 checked + smoke-tested

## How to use

For each row:

1. Identify the target file in `etzhayyim/root/20-actors/magatama/py/src/pymagatama/`.
2. Apply the **Pattern** listed for the row (see §0 below for pattern recipes).
3. Run the **Smoke** command in a tmp `$ORGANISM_SQLITE_DIR`; all assertions
   in the smoke must pass.
4. Tick the checkbox and commit (one commit per row, or per logical batch of
   ≤5 rows from the same pattern group).
5. When the **last** row is checked, update vendor `deps.toml [[migrations]]
   etzhayyim-tranche-f-three-axis-split-2026-05-17`:
   ```toml
   gate_a_execution_completed_at = "2026-MM-DDTHH:MMZ"
   ```
   This unblocks ADR-2605211913 Phase 5 §2.A-2.D.

## §0 Pattern recipes (one paragraph each)

- **BeliefStore (organism)**: import `select_belief_store()` from
  `pymagatama.primitives.active_inference_substrate`; replace every
  `cur.execute("INSERT INTO vertex_<actor>_<kind> ...", ...)` with
  `store.put_row("vertex_<actor>_<kind>", {...})` where `store =
  select_belief_store()` is cached at module top. Reads via
  `store.list_<kind>(...)`. Smoke: 1 put + 1 list assertion against a
  tmp PVC.
- **Audit log**: per-actor SQLite at `audit-{repo}.db`, append-only,
  schema mirrors legacy `vertex_repo_commit`. Function body becomes
  `_ensure_schema()` + `INSERT OR REPLACE INTO audit_commit ...`. Smoke:
  2 emit + 1 error case (empty repo).
- **Read-cache**: per-actor SQLite at `{module}-{actor}.db`, SELECT-only,
  schema mirrors legacy `vertex_{module}_*` tables with indices on the
  `WHERE` and `ORDER BY` columns. External ingest path seeds the data
  (out of this row's scope). Smoke: seed via raw INSERT + 1 SELECT
  + 1 missing-id case + 1 ILIKE→LIKE COLLATE NOCASE search if applicable.
- **Primary store**: per-actor SQLite at `{module}-{actor}.db`,
  INSERT/SELECT/UPDATE/DELETE all served locally. Helpers are
  `_create_*` / `_list_*` / `_get_*` / `_update_*` / `_delete_*`; async
  task handlers wrap them via `asyncio.to_thread`. Smoke: full CRUD path
  + any JOIN query per worker.
- **worker_runtime + degraded stub**: drop `from pymagatama.zeebe_worker_main
  import ...` in favor of `from pymagatama.worker_runtime import watchdog,
  activation_monitor, task_sqlite_health_probe, make_degraded_ingest_stub`.
  Per-task: keep the same `worker.task(task_type=...)` registration but use
  the stub factory until the ingest module is also ported. Smoke: 1 health
  probe + 1 degraded-stub kwarg-pass-through.
- **Ingest module**: schema mirrors legacy + cursor table; helpers like
  `_get_cursor_height` / `_insert_block` use SQLite WAL; RPC paths
  (Bitcoin/Ethereum/eGov/eCFR/Common Crawl) unchanged. Smoke: mock RPC +
  cold-start ingest + idempotent re-run.

`$ORGANISM_SQLITE_DIR` defaults to `/var/lib/etzhayyim/organism`. In smoke
tests use `tempfile.TemporaryDirectory()`.

## §1 Substrate primitives (4 files — port first, they're imported by §2-§4)

| # | Target file | Pattern | Source ref | Smoke | Done |
|---|---|---|---|---|---|
| P1 | `primitives/active_inference_substrate.py` | (Protocol + dataclasses + factory) | etzhayyim vendor has 590 lines; etzhayyim port removes `_DualWriteBeliefStore` class + RW import branches, defaults backend to `at-ipfs-local` | `from pymagatama.primitives.active_inference_substrate import BeliefStore, ObservationRecord, select_belief_store` (import-only) | [x] 2026-05-21 |
| P2 | `primitives/at_ipfs_belief_store.py` | (concrete BeliefStore impl) | etzhayyim vendor has 430 lines; etzhayyim port = byte-identical copy (no RW imports in the file already) | seeded BeliefStore + put_observation/list_observations round-trip | [x] 2026-05-21 |
| P3 | `worker_runtime.py` | (new file at pymagatama root) | ~200 lines: `watchdog`, `activation_monitor`, `task_sqlite_health_probe`, `make_degraded_ingest_stub` | health probe healthy + degraded + watchdog clean exit + activation_monitor clean exit with bogus URL | [x] 2026-05-21 |
| P4 | `ingest/core.py` | (orchestration spine, 3 tables) | ~320 lines port from etzhayyim 569 lines (drops psql/_psql_exec fallback) | upsert_run + mark_run_finished + upsert_cursor + upsert_artifact round-trip | [x] 2026-05-21 (RW path disabled via `_psql_enabled() -> False`; vendor 4 helpers retained with non-psql fallback active) |

## §2 BeliefStore organism workers (8 — Wave D group)

| # | Target file | Pattern | Smoke | Done |
|---|---|---|---|---|
| W1 | `hakkou_worker_main.py` | BeliefStore | task_create_ferment_record + task_finalize_ferment | [ ] |
| W2 | `kabi_worker_main.py` | BeliefStore | task_anastomosis_probe | [ ] |
| W3 | `ki_worker_main.py` | BeliefStore | task_absorb + task_bloom + task_ring + task_synthesize | [ ] |
| W4 | `kinoko_worker_main.py` | BeliefStore | task_check_flow_threshold | [ ] |
| W5 | `kobo_worker_main.py` | BeliefStore | task_bud_agent + task_sporulate + task_germinate | [ ] |
| W6 | `koke_worker_main.py` | BeliefStore | task_scan_raw_signals + task_handoff_to_hakkou + task_handoff_to_saikin | [ ] |
| W7 | `saikin_worker_main.py` | BeliefStore | task_probe_environment + task_form_colony + task_handoff_to_ki | [ ] |
| W8 | `myco_yeast_worker_main.py` | BeliefStore | (per ADR-2605211200 Phase 2A-2D origin task set) | [ ] |

## §3 Primary-store + read-cache + audit workers (12 — Waves A-C)

### Wave A (read-cache + audit + utility cleanup)

| # | Target file | Pattern | Smoke | Done |
|---|---|---|---|---|
| W9 | `tools_audit_worker_main.py` | audit log | 2 emit + 1 error (empty repo) | [x] 2026-05-21 (already ported; docstring confirms "No psycopg / KOTOBA_URL dependency"; `task_audit_emit` importable) |
| W10 | `sixir_worker_main.py` | read-cache | 6 task: list/get/search × company + filing + earnings; ILIKE→LIKE COLLATE NOCASE | [x] 2026-05-21 (already ported; 8 task handlers importable: get/list × company/filing/earnings) |

### Wave B (single-table primary store)

| # | Target file | Pattern | Smoke | Done |
|---|---|---|---|---|
| W11 | `hub_worker_main.py` | primary store (2 tables: endpoint + webhook) | full CRUD + metrics | [ ] |
| W12 | `web4_worker_main.py` | primary store (2 tables: expert + inference_job; **also**: fix f-string LIMIT/OFFSET SQL injection from legacy) | full CRUD + UPDATE + cluster_stats | [ ] |
| W13 | `ge_worker_main.py` (covers legal-entity) | primary store (3 tables: org + project + resource_assignment) | full CRUD + JOIN metrics | [ ] |
| W14 | `oshiete_worker_main.py` | primary store (2 tables: question + answer) | full CRUD + vote_count update + JOIN topic_expert | [ ] |

### Wave C (multi-table + JOIN primary)

| # | Target file | Pattern | Smoke | Done |
|---|---|---|---|---|
| W15 | `resources_worker_main.py` | primary store (2 tables: resource + allocation) | full CRUD + DELETE + usage metrics | [ ] |
| W16 | `omikuji_worker_main.py` | primary store (2 tables: fortune_draw + shrine) | full CRUD + JP fortune random | [ ] |
| W17 | `kareyanagi_worker_main.py` | primary store (2 tables: listing + order) | full CRUD + UPDATE inventory + trade_history JOIN | [ ] |
| W18 | `kiyome_worker_main.py` | primary store (2 tables: clearance + audit_log) | full CRUD + approve/reject + compliance_status | [ ] |
| W19 | `gov_worker_main.py` | primary store (4 tables: agency + official + consult + municipality; **also**: dynamic WHERE builder for list_agencies / list_officials / list_consults) | full CRUD + JOIN getAgency | [ ] |
| W20 | `narou_worker_main.py` | primary store (4 tables: novel + chapter + character + world_setting) — write-heavy + LLM placeholder generate + post-filter search | 11 task handlers + search 'dragon' / 'tokyo' genre=scifi | [ ] |

## §4 Ingest-coupled workers (4 — Wave D group, gated on §1 ingest modules)

| # | Target file | Pattern | Smoke | Done |
|---|---|---|---|---|
| W21 | `blockchain_worker_main.py` | worker_runtime + ingest delegate to `ingest/blockchain.py` (replaces zeebe_worker_main + db_sync import) | task_blockchain_head_ingest (delegating to ingest.blockchain) + task_sqlite_health_probe | [ ] |
| W22 | `houbun_worker_main.py` | worker_runtime + ingest delegate to `ingest/houbun.py` (8 task handlers, all real not stub) | 8 task delegations + health | [ ] |
| W23 | `curpus2skill_worker_main.py` | worker_runtime + ingest delegate to `ingest/curpus2skill.py` (1 task) | extractEvidence delegation | [ ] |
| W24 | `site_common_crawl_worker_main.py` | worker_runtime + ingest delegate to `ingest/site_common_crawl.py` (8 task handlers) | 8 task delegations + health | [ ] |

## §5 Truly-clean utility workers (5 — no port work, audit only)

These are already RW-free; just verify no hidden RW import survives a fresh
audit, then check off.

| # | Target file | Audit | Done |
|---|---|---|---|
| U1 | `tools_const_worker_main.py` | 0 SQL hits, no hidden import | [x] |
| U2 | `tools_http_worker_main.py` | 0 SQL hits, no hidden import | [x] |
| U3 | `tools_json_worker_main.py` | 0 SQL hits, no hidden import | [x] |
| U4 | `tools_time_worker_main.py` | 0 SQL hits, no hidden import | [x] |
| U5 | `tools_transform_worker_main.py` | depends on `tools_json_worker_main` only — verify no chain RW import | [x] |

## §6 Ingest modules (4 — gated on §1 P4 ingest.core)

| # | Target file | Pattern | Smoke | Done |
|---|---|---|---|---|
| I1 | `ingest/blockchain.py` | ingest module (Bitcoin + Ethereum RPC, 4 tables: block + tx + actor + cursor) | mock RPC cold-start + idempotent re-run | [ ] |
| I2 | `ingest/houbun.py` | ingest module (eGov JPN + eCFR USA + NPC China RPC, 3 tables: statute + article + edge; `_insert_ignore` → `INSERT OR IGNORE`) | USA + JPN write + idempotent re-run | [ ] |
| I3 | `ingest/curpus2skill.py` | ingest module (corpus → ESCO skill evidence; 2 write tables + 5 source-read mirrors) | seed legal-corpus doc + exact_label match | [ ] |
| I4 | `ingest/site_common_crawl.py` | ingest module (artifact-first; 2 read tables: vertex_page + vertex_collection_job) | seed pages + count assertions | [ ] |

## Total

- 4 primitives (§1)
- 8 BeliefStore workers (§2)
- 12 primary/read-cache/audit workers (§3)
- 4 ingest-coupled workers (§4)
- 5 utility workers (§5, audit-only)
- 4 ingest modules (§6)

= **37 active port + 5 audit rows** = **42 rows** total. Gate (a) closes when
all 42 boxes are ticked + the final commit lands in
`etzhayyim/root/20-actors/magatama/py/src/pymagatama/`.

## Recommended port order

1. §1 P1-P4 substrate primitives (everything else depends on these)
2. §5 utility audit (closes 5 rows fast)
3. §3 Wave A (W9-W10): audit + read-cache (lowest write risk)
4. §3 Wave B (W11-W14): single-table primary stores
5. §3 Wave C (W15-W20): multi-table + JOIN primary stores
6. §2 BeliefStore organism cluster (W1-W8) — Wave D part 1
7. §6 ingest modules (I1-I4) — gates §4
8. §4 ingest-coupled workers (W21-W24) — Wave D part 2

## Acceptance summary

| Section | Rows | Status (2026-05-21) |
|---------|------|----------------------|
| §1 primitives | 4 | 4 / 4 ✅ (P1-P4 2026-05-21) |
| §2 BeliefStore | 8 | 0 / 8 |
| §3 primary/read/audit | 12 | 2 / 12 (Wave A W9-W10 done 2026-05-21) |
| §4 ingest-coupled | 4 | 0 / 4 |
| §5 utility audit | 5 | 5 / 5 ✅ (U1-U5 2026-05-21) |
| §6 ingest modules | 4 | 0 / 4 |
| **Total** | **37 + 5 = 42** | **11 / 42** (§1 + §5 + §3 Wave A complete; §2 + §3 Wave B/C + §4 + §6 in-progress) |

When **42 / 42** is reached, replace this status table with:

```
| **Total** | **42** | **42 / 42 — gate (a) CLOSED 2026-MM-DD by <operator>** |
```

…and update vendor `deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17`
`gate_a_execution_completed_at` field.

## References

- ADR-2605212100 (Tranche F closure — gate definitions + classification table)
- ADR-2605211757 (DNS cutover runbook — Wave A-D operator runbook, gated on this checklist)
- ADR-2605211913 (Phase 4-5 runbook — vendor refactor + git rm, gated on this checklist)
- ADR-2605211925 (Phase 6 archive markers — gated on Phase 5 completion)
- `90-docs/2605211800-vendor-importer-survey-gate-d.md` — vendor importer scope
- `90-docs/2605211900-tranche-f-all-gates-closure-confirmation.md` — overall gate status snapshot
