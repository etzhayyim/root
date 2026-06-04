---
id: adr-2606032330-session-close-magatama-risingwave-to-kotoba-datomic-edn
title: "ADR-2606032330: Session close — magatama RisingWave → kotoba Datomic API/EDN refactor (substrate clients + LangGraph savers + sqlmesh view registry)"
status: active
doc_type: adr
topic: session-close-magatama-rw-to-kotoba
authoritative: false
last_verified: 2026-06-03
related:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605231525-server-side-signing-capability
  - adr-2606022150-kotoba-unified-ipld-dagcbor-prolly-datomic
  - adr-2606031030-session-close-kotoba-canonical-substrate-and-browser-node
supersedes: []
superseded_by: []
---

# ADR-2606032330: Session close — magatama RisingWave → kotoba Datomic API/EDN

**Status**: active — documentation-only closure
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

Closure for the request *「repo ないの risingwave を kotoba datomic api, edn に refactor」*.
This is the **magatama application-layer** counterpart to the kotoba-engine-internal
work in ADR-2606031030. The canonical substrate rule is **ADR-2605262130** (kotoba
Datom log = the only state home; no RisingWave/Postgres/Kysely) + **ADR-2605312345**
(Datom log = first-class canonical state). This session ported the magatama Python
worker layer + the TS app SDK off RisingWave onto the kotoba Datomic XRPC surface.

## Scope finding (recorded for the next session)

A full repo scan found **~1,380 files** mentioning `risingwave`. The decisive
result: the **30 Tier-B actors are already RW-free** — every remaining mention there
is a gate rule *forbidding* RW, a docstring documenting a prior migration, or a
manifest-cleanup TODO; **zero real RW usage remains in actor code**. The only live
RW code is two framework surfaces the migration plan had deferred to "P11":
(1) the `magatama/py` worker framework (LangGraph persistence + `rw_async_pool`/
`rw_sql` + 610 sqlmesh materialized views), and (2) the inherited
`60-apps/*-project-*` SaaS apps (Hyperdrive/Kysely). Both were taken on this session.

## What landed (all new files; standalone, tested, untracked in the working tree)

- **kotoba Datomic substrate client — Python** `20-actors/magatama/py/src/pymagatama/kotoba_datomic.py`.
  The RW-free replacement for `rw_async_pool` + `rw_sql`. stdlib-only (urllib), speaks
  `com.etzhayyim.apps.kotoba.datomic.{transact,q,pull}`. Maps `vertex_*`/`edge_*` SQL
  rows → namespaced EAVT entity maps with `:db.unique/identity` upsert (preserving the
  RW "PK implicit overwrite" semantics). Kysely-shim surface for low-friction caller
  migration: `insert_row` / `insert_rows` / `select_rows` / `select_where` /
  `select_first_where` / `aggregate_where` / `ensure_schema`. Writes are
  operator-credential-gated (ADR-2605231525 — no platform-held key; dry-run otherwise).
- **kotoba Datomic substrate client — TypeScript** `20-actors/magatama/sdk/magatama-host-sdk/src/kotoba-datomic.ts`.
  Byte-for-byte semantic mirror of the Python client (same NSIDs, same namespace
  mapping, same shim API) so a Python worker and a TS app project the same Datoms the
  same way. `createKotobaDb()` + `setKotobaConfig(env)` mirror `createKyselyDb()` +
  `setKyselyHyperdrive()`. Dependency-free (global `fetch`); `tsc --strict` clean.
- **kotoba-native LangGraph savers** `langgraph_checkpoint_kotoba.py` (`KotobaCheckpointSaver`)
  + `langgraph_store_kotoba.py` (`KotobaStore`). The RW 3-table checkpoint model maps
  onto `:lg.checkpoint/*` (pointer) + `:lg.checkpoint-blob/*` (content-addressed, CID
  = `:db.unique/identity` → kotoba dedups identical checkpoints for free) +
  `:lg.checkpoint-write/*`; identical zlib-b64 content-addressing to the RW saver
  (blobs interchangeable). Sync client wrapped in `asyncio.to_thread` to keep the async
  interface; `adelete_thread` uses `:db/retractEntity` (append-only history, 非終末論).
- **sqlmesh materialized-view → kotoba view registry** `20-actors/magatama/py/sqlmesh/sqlmesh_to_kotoba.py`
  + generated `sqlmesh/kotoba/views.edn` + `sqlmesh/kotoba/README.md`. An MV is a
  *derived read*, not state; under kotoba the read path is `kotoba-kqe` over the Datom
  log (no projection layer, ADR-2605262130). The converter parses every `MODEL(...)`
  header (name/kind/grain/tags/description/sources preserved) + the SELECT body and
  emits Datalog for the mechanically-translatable shapes. **Coverage: 295 / 610 auto**
  (single-source projection + scalar/grouped/filtered-equality aggregate, with cast-
  stripping); the remaining **315 `:manual`** (JOINs, UNION, DISTINCT-ON, subqueries,
  computed/`COALESCE` projections, non-equality filters) keep their original SQL under
  `:view/sql-source` + `:view/manual-reason` — never a pretended translation. A latent
  correctness bug was fixed in passing: filtered aggregates had been silently dropping
  their WHERE clause (wrong counts); the WHERE is now reflected in the `:where` clauses
  or the view stays `:manual`. Registry round-trips through the repo EDN reader.

## Migration recipe (proven, for the resumed app sweep)

| RisingWave / Kysely | kotoba Datomic |
|---|---|
| `selectFrom(t).where(c,"=",v).executeTakeFirst()` | `selectFirstWhere(t,c,v)` |
| `selectFrom(t).select(cols).execute()` | `selectRows(t,cols)` |
| `selectFrom(t).select(fn.sum(c)).where(...)` | `aggregateWhere(t,"sum",c,wc,wv)` |
| `insertInto(t).values(row).execute()` | `insertRow(t,row)` |
| `createKyselyDb(env.HYPERDRIVE)` | `setKotobaConfig(env)` + `createKotobaDb()` |

## Honest status / what did NOT land

- **Substrate clients + LangGraph savers + view registry: LANDED** (standalone, tested;
  Python `py_compile` clean, TS `tsc --strict` clean, EDN parse-verified). They are
  **untracked** in the working tree and were authored against the legacy `magatama/py`
  layout, which survived the cutover intact.
- **Wiring + app migrations: LOST.** The factory selectors in `langgraph_checkpoint_rw.py`
  / `langgraph_store_rw.py`, the `__init__.py` / host-sdk `index.ts` kotoba exports, and
  four reference app migrations (seibutsu / toshi-kozan / briefing / cpc) were authored
  during the session but **wiped by a concurrent history-rewrite (force-push/rebase): the
  loop-start HEAD `1f411a48` is no longer an ancestor of HEAD `346382b9`, +228 commits**.
  Those commits are the in-progress **`etzhayyim-` → `etzhayyim-` project-rename cutover**
  (371 `etzhayyim-project-*` still present, 22 `etzhayyim-project-*` created so far). The
  RW framework files are intentionally pristine and must not be re-reverted.
- **App sweep PAUSED.** Re-targeting the renamed `etzhayyim-project-*` paths should wait
  until the rename cutover completes, to avoid editing apps that are being moved.
- **No live kqe wiring.** The `:auto` view queries are emitted but not yet served by a
  live `kotoba-kqe` endpoint (Phase-2.5 read-path migration per ADR-2605262130).

## Decision

1. The kotoba Datomic API/EDN clients (Py + TS) are the **canonical RW-free substrate
   access** for the magatama layer, superseding `rw_async_pool`/`rw_sql`/`createKyselyDb`
   at the call sites as they migrate. The legacy RW modules stay pristine until the P11
   framework cutover removes them.
2. The `sqlmesh/kotoba/views.edn` registry is the canonical kotoba-native form of the
   610 RW materialized views; `:manual` entries are tracked R1 kqe-rule work.
3. The inherited-app sweep resumes **after** the `etzhayyim→etzhayyim` rename cutover, using
   the recipe table above against the final `etzhayyim-project-*` paths.

## Follow-ups (tracked)

- **P11a** — wire `createKotobaDb`/`get_checkpoint_saver`/`get_store` selectors back in
  once the rename cutover settles (the prior attempts were rebased away).
- **P11b** — re-apply the four reference app migrations against renamed paths, then batch
  the ~66 remaining real-usage TS files.
- **R1 views** — hand-author the 315 `:manual` views as multi-clause kqe rules
  (95 JOIN, 27 UNION, DISTINCT-ON, subqueries, computed projections); wire `:auto`
  queries into a live kqe endpoint (Phase 2.5).
- **Commit hygiene** — the surviving untracked kotoba files must be committed/stashed
  before the next rebase so they are not lost to `git clean`.
