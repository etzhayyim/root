---
id: adr-2605215300-etzhayyim-yoro-python-primitives-mst-rewrite-addendum
title: "ADR-2605215300: etzhayyim yoro Python primitives — MST rewrite addendum (per-function migration table + skeleton)"
status: proposed
doc_type: adr
topic: yoro-python-primitives-mst-rewrite-addendum
authoritative: true
last_verified: 2026-05-21
priority: 8.5
axis: architecture
weight: 0.85
priority_note: "Fills the gap left by ADR-2605191358: per-function migration table for yoro Python primitive layer. Without this, Step 8 cutover (ADR-2605171900) is mechanically impractical."
authoritative_for:
  - per-function migration table for yoro_social.py RisingWave call sites
  - per-function migration table for yoro_product_ingest.py RisingWave call sites
  - new lexicon NSIDs required under app.etzhayyim.* namespace
  - substrate write-path mapping from psycopg2/3 INSERT to @etzhayyim/sdk MST dispatch
  - M0–M5 successor roadmap for Python primitive layer cutover
extends:
  - adr-2605191358-yoro-murakumo-rw-free-rewrite-map
depends_on:
  - adr-2605191358-yoro-murakumo-rw-free-rewrite-map
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605214000-etzhayyim-murakumo-no-vke-mesh-verdict-taxonomy
  - adr-2605215000-etzhayyim-murakumo-fleet-only-inference-no-runpod
  - adr-2605202100-etzhayyim-magatama-cell-runner-launchd
related:
  - ADR-2605171900 (yoro migration to etzhayyim — Stages 1–5)
  - ADR-2605172100 (etzhayyim payments on-chain only)
  - ADR-2605181100 (MST encrypted records)
  - ADR-2605171800 (LangGraph MST IPFS L2 anchor pipeline)
  - 20-actors/magatama/py/YORO-PYTHON-MIGRATION-NOTES.md
supersedes: []
superseded_by: []
---

# ADR-2605215300: etzhayyim yoro Python primitives — MST rewrite addendum

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

## Context

ADR-2605191358 (`yoro-murakumo-rw-free-rewrite-map`) mapped yoro's RisingWave dependency at the **CF Worker / UI path level** — `kagami-store`, 12 RW Async MVs, and `searchActors` — but did NOT decompose the Python primitive layer (`primitives/yoro_social.py`, 1687 LoC, and `primitives/yoro_product_ingest.py`).

The 2026-05-21 substrate-fit audit (`20-actors/AUDIT-RUNPOD-RW-2026-05-21.md §3`) surfaces the gap with precision:

- **14 REIMPLEMENT** findings in the Python layer: structural RisingWave writes via `psycopg2`/`psycopg3` `sync_cursor()` that have no passthrough equivalent under the etzhayyim MST substrate.
- **12 PORT-adapted** findings: functions that build wire shapes compatible with AT MST but emit them to RisingWave rather than a PDS.
- **8 VENDOR-ONLY** findings: functions that are legitimately vendor SaaS–specific (remain in `yoro_social.py` for vendor use).
- 8 REJECT → RESOLVED 2026-05-21: Stripe Issuing fiat surface, all removed.

The audit conclusion states: "yoro's Python primitive layer has 14+ structural RisingWave writes ... ADR-2605191358 maps the replacement path at a high level but no per-function migration table exists yet, making Step 8 cutover impractical without further decomposition."

`deps.toml` carries the `yoro-python-primitives-rewrite` migration as `pending` with `blocked_on = "Per-function migration table required — extends ADR-2605191358 yoro-murakumo-rw-free-rewrite-map"`.

This ADR is a **tactical addendum** to ADR-2605191358. It fills the Python layer gap by supplying:

1. A per-function migration table for every RisingWave call site in `yoro_social.py`.
2. The new `app.etzhayyim.*` lexicons required where no `app.bsky.*` equivalent exists.
3. A concrete substrate write-path mapping (`psycopg2 INSERT` → `@etzhayyim/sdk` MST dispatch).
4. A successor roadmap M0–M5 gating Step 8 cutover.
5. Skeleton implementation files (`yoro_social_murakumo.py`, `yoro_product_ingest_murakumo.py`) as the landing target.

**This ADR does NOT supersede ADR-2605191358.** It extends and sharpens it with per-function decomposition of the Python layer that the parent ADR explicitly deferred.

## Decision

### §1 Per-function migration table

Every function in `primitives/yoro_social.py` that touches RisingWave via `sync_cursor()` is mapped to a religious-corp replacement. Functions touching only AT wire shapes (build-only, no DB call) are PORT-adapted and included for completeness.

| # | Function | Vendor RW operation | Table(s) | Religious-corp replacement | Verdict |
|---|---|---|---|---|---|
| 1 | `insert_social_post_record(row, ...)` | `INSERT INTO vertex_repo_record` + `INSERT INTO vertex_post` | `vertex_repo_record`, `vertex_post` | `@etzhayyim/sdk` Python binding → PDS `putRecord` → `app.bsky.feed.post` → MST commit → IPFS pin → L2 anchor (per ADR-2605171800) | REIMPLEMENT |
| 2 | `insert_repo_records(rows, ...)` — `app.bsky.feed.post` branch | `INSERT INTO vertex_repo_record` + `INSERT INTO vertex_post` | `vertex_repo_record`, `vertex_post` | Same as #1, batch write variant | REIMPLEMENT |
| 3 | `insert_repo_records(rows, ...)` — `app.bsky.graph.follow` branch | `INSERT INTO edge_follows` | `edge_follows` | `@etzhayyim/sdk` Python binding → PDS `putRecord` → `app.bsky.graph.follow` → MST commit | REIMPLEMENT |
| 4 | `insert_repo_records(rows, ...)` — `app.bsky.actor.profile` branch | `INSERT INTO vertex_profile` | `vertex_profile` | `@etzhayyim/sdk` Python binding → PDS `putRecord` → `app.bsky.actor.profile` → MST commit | REIMPLEMENT |
| 5 | `insert_translation_link_record(row)` | `DELETE FROM vertex_translation_link` + `INSERT INTO vertex_translation_link` | `vertex_translation_link` | `@etzhayyim/sdk` Python binding → PDS `putRecord` → `app.etzhayyim.translationLink` (new lexicon §2) → MST commit → IPFS pin | REIMPLEMENT |
| 6 | `_emit_actor_quality_activity_event(...)` | `INSERT INTO vertex_bpmn_activity_event` | `vertex_bpmn_activity_event` | `@etzhayyim/sdk` Python binding → PDS `putRecord` → `app.etzhayyim.bpmnActivityEvent` (new lexicon §2) → MST commit | REIMPLEMENT |
| 7 | `_enrich_actor_quality_profile(...)` — INSERT branch | `INSERT INTO vertex_profile` (full upsert) | `vertex_profile` | `@etzhayyim/sdk` Python binding → PDS `putRecord` → `app.bsky.actor.profile` → MST commit (profile already federable) | REIMPLEMENT |
| 8 | `_enrich_actor_quality_profile(...)` — UPDATE branch | `UPDATE vertex_profile SET ...` | `vertex_profile` | `@etzhayyim/sdk` Python binding → PDS `putRecord` (rkey=`self`, overwrite existing) → MST tree rewrite | REIMPLEMENT |
| 9 | `_insert_feed_post_row(cur, row)` — helper | `DELETE FROM vertex_repo_record WHERE uri=...` + `INSERT INTO vertex_repo_record` + `DELETE FROM vertex_post WHERE vertex_id=...` + `INSERT INTO vertex_post` | `vertex_repo_record`, `vertex_post` | Absorbed into #1/#2: idempotent MST `putRecord` replaces DELETE+INSERT semantics (rkey-keyed, PDS deduplicates) | REIMPLEMENT |
| 10 | `_fetch_source_post(post_uri)` | `SELECT FROM vertex_repo_record WHERE uri=...` | `vertex_repo_record` | MST graph read via `@etzhayyim/sdk` `getRecord({ repo, collection, rkey })` or PDS firehose subscription cache | PORT-adapted |
| 11 | `_fetch_actor_generation_context(actor_did, handle)` | `SELECT FROM vertex_profile WHERE did=...` + `SELECT FROM vertex_repo_record WHERE repo=...` | `vertex_profile`, `vertex_repo_record` | `@etzhayyim/sdk` `listRecords({ repo, collection })` for repo records; `getRecord` for profile | PORT-adapted |
| 12 | `_fetch_profile_quality(actor_did, handle)` | `SELECT FROM vertex_profile WHERE did=...` + `SELECT count(*) FROM vertex_repo_record WHERE repo=...` | `vertex_profile`, `vertex_repo_record` | `@etzhayyim/sdk` `getRecord({ repo, collection: 'app.bsky.actor.profile', rkey: 'self' })` + `listRecords` count | PORT-adapted |
| 13 | `_fetch_diet_speech_rows(speech_id, limit)` | `SELECT FROM vertex_fukkou_diet_speech WHERE ...` | `vertex_fukkou_diet_speech` | VENDOR-ONLY: `vertex_fukkou_diet_speech` is a vendor-specific ETL ingest table with no AT lexicon equivalent; stays in `yoro_social.py` for vendor SaaS | VENDOR-ONLY |
| 14 | `task_yoro_social_platform_pulse_graph_fallback(...)` — `_count_scalar` calls | `SELECT count(*) FROM vertex_repo_record ...` + `SELECT count(*) FROM vertex_actor WHERE status='active'` | `vertex_repo_record`, `vertex_actor` | `@etzhayyim/sdk` `listRecords` count (aggregate) or `mst-projector` CID-pinned snapshot for heavy counts (per ADR-2605191358 §murakumo-cluster) | PORT-adapted |
| 15 | `build_social_post_record(...)` | No direct DB call — builds wire shape | — | PORT-adapted: wire shape is `app.bsky.feed.post` compatible; function reusable as-is in murakumo variant after removing `sync_cursor` dependency | PORT-adapted |
| 16 | `build_repo_record(...)` | No direct DB call — builds wire shape | — | PORT-adapted: wire shape is AT MST–compatible; reusable after import path fix | PORT-adapted |
| 17 | `build_translation_link_record(...)` | No direct DB call — builds wire shape for `ai.gftd.apps.media_gamers.record.translationLink` | — | PORT-adapted with namespace migration: NSID changes to `app.etzhayyim.translationLink` (§2) in religious-corp variant | PORT-adapted |
| 18 | `task_yoro_social_translate_post(...)` | Calls `_fetch_source_post` (RW SELECT) + `insert_social_post_record` (RW INSERT) + `insert_translation_link_record` (RW INSERT) | via #5, #10 | REIMPLEMENT: all three sub-calls replaced with SDK equivalents in M2/M3 | REIMPLEMENT |
| 19 | `task_yoro_social_translate_post_batch(...)` | Calls `task_yoro_social_translate_post` in loop | via #18 | REIMPLEMENT: inherits from #18 | REIMPLEMENT |
| 20 | `task_yoro_actor_quality_enrich_profile(...)` | Calls `_enrich_actor_quality_profile` (RW INSERT/UPDATE) | via #7/#8 | REIMPLEMENT: inherits from #7/#8 | REIMPLEMENT |
| 21 | `task_yoro_actor_quality_ensure_seed_post(...)` | Calls `insert_social_post_record` (RW INSERT) | via #1 | REIMPLEMENT: inherits from #1 | REIMPLEMENT |
| 22 | `task_yoro_actor_quality_inspect(...)` | Calls `_fetch_profile_quality` (RW SELECT) + `_emit_actor_quality_activity_event` (RW INSERT) | via #6, #12 | REIMPLEMENT: event emission replaced; profile read replaced with SDK | REIMPLEMENT |
| 23 | `register(worker, timeout_ms)` | No direct DB call — task registration | — | PORT-adapted: registration pattern reused verbatim, task handler refs updated to murakumo variants | PORT-adapted |

**Additional call sites follow the same INSERT/SELECT pattern**; see `20-actors/magatama/py/YORO-PYTHON-MIGRATION-NOTES.md` for the full 40-row table covering `yoro_product_ingest.py`.

**REIMPLEMENT count**: 14 functions (rows 1–9, 18–22).
**PORT-adapted count**: 8 functions (rows 10–12, 14–17, 23) — adapted after removing `sync_cursor` dependency.
**VENDOR-ONLY count**: 1+ functions in scope above (row 13: `_fetch_diet_speech_rows`); additional vendor-only entries in `yoro_product_ingest.py`.

### §2 New lexicons required

The following `app.etzhayyim.*` lexicons are required because the vendor logic has no existing `app.bsky.*` or prior etzhayyim equivalent:

| NSID | Record type | Rationale | Status |
|---|---|---|---|
| `app.etzhayyim.translationLink` | record | Captures the semantic link between a source AT post and its translation: `sourceUri`, `sourceLang`, `translatedUri`, `targetLang`, `source` (model/origin), `qualityScore`. No `app.bsky.*` equivalent exists. Current vendor namespace `ai.gftd.apps.media_gamers.record.translationLink` is vendor-scoped and must be migrated. | Required — M1 |
| `app.etzhayyim.bpmnActivityEvent` | record | Captures BPMN process activity events for audit trail: `caseId`, `taskType`, `lifecycle`, `actorDid`, `eventType`, `payloadJson`, `occurredAt`. Vendor currently writes to `vertex_bpmn_activity_event` SQL table. No `app.bsky.*` or existing etzhayyim equivalent. | Required — M1 |
| `app.etzhayyim.actorQualityReport` | record | Optional: captures actor quality inspection results (`qualityScore`, `missingFields`, `postsCount`). Replaces in-memory return value with durable MST record for auditability across Pregel cells. | Recommended — M2 |
| `app.etzhayyim.platformPulseMetric` | record | Optional: replaces `_count_scalar` SQL aggregates in `task_yoro_social_platform_pulse_graph_fallback` with a CID-pinned MST record for verifiable platform-level metrics. | Recommended — M3 via mst-projector |

**Note**: `app.bsky.feed.post`, `app.bsky.actor.profile`, and `app.bsky.graph.follow` are already federable AT lexicons. These three collections do NOT require new lexicons — they map directly to existing AT Protocol standard NSIDs.

### §3 Substrate write-path mapping

| Vendor pattern | Religious-corp path |
|---|---|
| `psycopg2.connect(RW_URL).cursor().execute("INSERT INTO vertex_post ...")` | `@etzhayyim/sdk` Python binding → PDS `putRecord({ repo, collection: 'app.bsky.feed.post', rkey, record })` → MST commit → IPFS pin (if `ipfs_pin=True` flag) → Base L2 anchor batch (per ADR-2605171800 `anchor-cron`) |
| `cursor.execute("INSERT INTO vertex_repo_record ...")` | Same path as above — `vertex_repo_record` is the vendor's materialisation of the AT record log; in etzhayyim, the PDS MST commit IS the canonical record log |
| `cursor.execute("INSERT INTO vertex_profile ON CONFLICT UPDATE")` | `@etzhayyim/sdk` Python binding → PDS `putRecord({ repo, collection: 'app.bsky.actor.profile', rkey: 'self', record })` — idempotent overwrite, PDS handles conflict semantics |
| `cursor.execute("INSERT INTO vertex_translation_link ...")` | `@etzhayyim/sdk` Python binding → PDS `putRecord({ collection: 'app.etzhayyim.translationLink', rkey, record })` → MST commit → IPFS pin |
| `cursor.execute("INSERT INTO vertex_bpmn_activity_event ...")` | `@etzhayyim/sdk` Python binding → PDS `putRecord({ collection: 'app.etzhayyim.bpmnActivityEvent', rkey, record })` → MST commit |
| `cursor.execute("INSERT INTO edge_follows ...")` | `@etzhayyim/sdk` Python binding → PDS `putRecord({ collection: 'app.bsky.graph.follow', rkey, record })` → MST commit (federable via AT Relay) |
| `cursor.execute("SELECT FROM vertex_repo_record WHERE uri = ...")` | MST graph read via `@etzhayyim/sdk` `getRecord({ repo, collection, rkey })` (decoded from AT URI) |
| `cursor.execute("SELECT FROM vertex_profile WHERE did = ...")` | `@etzhayyim/sdk` `getRecord({ repo: did, collection: 'app.bsky.actor.profile', rkey: 'self' })` |
| `cursor.execute("SELECT FROM vertex_repo_record WHERE repo = ... LIMIT 5")` | `@etzhayyim/sdk` `listRecords({ repo, collection, limit })` — key-prefix MST traverse (per ADR-2605191358 §read-path) |
| `cursor.execute("SELECT count(*) FROM vertex_repo_record ...")` | `mst-projector` derives CID-pinned aggregate snapshot (per ADR-2605191358 §12-MVs) OR `@etzhayyim/sdk` `listRecords` with client-side count for low-volume use cases |
| `cursor.execute("SELECT FROM vertex_fukkou_diet_speech ...")` | VENDOR-ONLY: this table is a vendor ETL ingest surface; no religious-corp equivalent. Stays in `yoro_social.py` for vendor SaaS. |
| `cur.execute("FLUSH")` | Removed: MST commits are atomic at `putRecord` call; no streaming-MV FLUSH required |

### §4 Successor roadmap M0–M5

| Step | Task | Target |
|---|---|---|
| M0 | This ADR proposed → active; `YORO-PYTHON-MIGRATION-NOTES.md` published; skeleton files `yoro_social_murakumo.py` and `yoro_product_ingest_murakumo.py` committed | M0 + 0d (2026-05-21) |
| M1 | New lexicons authored in `00-contracts/lexicons/app/etzhayyim/`: `translationLink`, `bpmnActivityEvent` (+ optional `actorQualityReport`). PDS bundle regenerated per gftdcojp deploy runbook. | M0 + 30d |
| M2 | Skeleton stubs replaced with `@etzhayyim/sdk` calls for top-5 highest-traffic functions: `insert_social_post_record`, `insert_repo_records` (feed.post + profile branches), `_enrich_actor_quality_profile`, `task_yoro_social_translate_post`. CI substrate-fit lint passes. | M1 + 30d |
| M3 | Remaining 9 REIMPLEMENT functions ported: `insert_translation_link_record`, `_emit_actor_quality_activity_event`, `insert_repo_records` (follow branch), task orchestrators (#18–#22). PORT-adapted read paths migrated to `@etzhayyim/sdk` reads. | M2 + 30d |
| M4 | End-to-end smoke test: yoro feed post → PDS `putRecord` → MST commit → IPFS pin → L2 anchor on test adherent DID. Translation link round-trip: post → translation → `app.etzhayyim.translationLink` record visible on AT firehose. BPMN activity event record query. | M3 + 21d |
| M5 | Retire vendor `yoro_social.py` RW writes from etzhayyim/root paths (Step 8 cutover gate per ADR-2605171900). Vendor SaaS `yoro_social.py` RW writes **remain** in `ai-gftd-apps-gftdcojp` for paid SaaS tier. | Tied to legal registration (ADR-2605171900 §Step-8) |

### §5 Status amendments

This ADR amends the state of the following:

- **ADR-2605191358** — no longer blocked on Python layer decomposition. §Python-primitive-layer is now addressed by this addendum. The parent ADR's CF Worker + UI path rewrite plan is unchanged.
- **ADR-2605172000** §write-path — this ADR confirms the Python primitive write path maps to `@etzhayyim/sdk` exclusively; no RW dependency survives in religious-corp builds.
- **ADR-2605214000** §2 namespace rule — new lexicons go under `app.etzhayyim.*` (no `app.bsky.*` equivalent exists for `translationLink` and `bpmnActivityEvent`); this is consistent with the namespace rule.
- **deps.toml** migration `yoro-python-primitives-rewrite` — `blocked_on` condition satisfied by this ADR + skeleton files.

## Consequences

**Positive**:

- **Python-layer REIMPLEMENT closure**: the 14 REIMPLEMENT findings from the 2026-05-21 audit have a concrete, function-by-function replacement plan. Step 8 cutover is now mechanically actionable at M4 milestone completion.
- **New lexicons are open and federable**: `app.etzhayyim.translationLink` and `app.etzhayyim.bpmnActivityEvent` records are MST-committed, IPFS-pinned, and L2-anchored — verifiable by any client with internet access. Translation provenance becomes publicly auditable.
- **Vendor parity preserved**: `yoro_social.py` RW writes remain in `ai-gftd-apps-gftdcojp` for the vendor paid SaaS tier. No business continuity disruption. The religious-corp `*_murakumo.py` variants are parallel additions, not replacements of vendor code.
- **Substrate-fit import guard**: the skeleton modules `yoro_social_murakumo.py` and `yoro_product_ingest_murakumo.py` fail fast (raise `RuntimeError`) if `RW_URL` is present in the environment, preventing accidental RW coupling in etzhayyim builds.
- **CI enforcement**: the substrate-fit regression test (`test_yoro_murakumo.py`) prevents re-introduction of `psycopg2`, `psycopg`, `RW_URL`, `Stripe`, and `runpod` imports via CI.

**Negative / costs**:

- **MST commit latency vs. RW INSERT**: vendor RisingWave INSERT is ~1–5 ms (Hyperdrive path). PDS `putRecord` + MST commit + IPFS pin is expected to be ~100–400 ms per record in current `50-infra/mst-projector/` scaffold. **Throughput target for M4**: ≥ 5 records/sec sustained for translation batch tasks; bulk ingest paths (Diet speech projection) must be async / batched, not inline synchronous. If latency target is unmet, the `@etzhayyim/sdk` Python binding must implement request coalescing.
- **New lexicons require PDS bundle regeneration**: each new NSID must be registered in `00-contracts/lexicons/` and the PDS validator bundle must be regenerated and re-deployed before the murakumo variant can call `putRecord` without `Lexicon not found` error. M1 milestone is a hard dependency for M2.
- **Federation behaviour of new lexicons**: `app.etzhayyim.translationLink` and `app.etzhayyim.bpmnActivityEvent` records will appear on the AT firehose but AppViews (Bluesky relay) will not index them — they require a custom etzhayyim AppView (per ADR-2605171900 Stage 3). Translation records are therefore verifiable but not yet discoverable via Bluesky search until the etzhayyim AppView is deployed.
- **mst-projector dependency**: PORT-adapted count functions (`_count_scalar` → platform-pulse metrics) require `mst-projector` CID-pinned snapshot delivery for non-trivial aggregates. This is currently scaffold-only (`50-infra/mst-projector/`). Low-volume counts can use `listRecords` client-side until M3.
- **`vertex_fukkou_diet_speech` has no MST path**: Diet speech data originates from vendor-specific ETL ingest. The etzhayyim `yoro_social_murakumo.py` will not include a replacement for `_fetch_diet_speech_rows`; the `task_yoro_social_project_diet_speeches_graph_fallback` task is VENDOR-ONLY and will remain in `yoro_social.py` only.

## Alternatives Considered

**A. Lift via opt-in RisingWave gateway** — a thin proxy that accepts `@etzhayyim/sdk` calls and writes to RW internally.
Rejected. ADR-2605172000 hard rule: etzhayyim/root open apps MUST be RW-free. A gateway that hides RW behind an SDK call is substrate subterfuge — the result is still "open license, closed substrate." The failure mode ADR-2605172000 was created to prevent.

**B. Use Bluesky AppView as full replacement for all Python primitives** — route every record type through `app.bsky.*` collections.
Rejected. `translationLink` and `bpmnActivityEvent` have no `app.bsky.*` analog. The translation-link record requires `sourceUri`, `translatedUri`, `sourceLang`, `targetLang` fields that carry semantic meaning outside the Bluesky social graph. Forcing them into `app.bsky.feed.post` embeds (as `source` extra fields) is fragile — Bluesky AppView may strip unknown fields. Dedicated lexicons under `app.etzhayyim.*` are the correct namespace per ADR-2605214000 §2.

**C. Defer to a generic "yoro Python v2" rewrite** — treat the entire `yoro_social.py` as a single unit and rewrite it from scratch after legal registration.
Rejected. 1687 LoC rewritten as a single unit creates a large surface area for undetected regressions. Per-function granularity is the right level: each REIMPLEMENT function is independently testable; the NotImplementedError stub skeleton lets CI catch missing implementations before any cutover attempt. This is the same approach that proved effective for `maps_sentinel_murakumo.py`.

**D. Keep `psycopg2` but point `RW_URL` at a PostgreSQL-compatible MST proxy** — use an intermediary that accepts SQL INSERTs and translates them to MST writes.
Rejected. This would maintain a psycopg2 import in etzhayyim/root (substrate boundary violation) and require maintaining a SQL-to-MST translation layer of significant complexity. The `@etzhayyim/sdk` Python binding already provides the correct abstraction at the right level.

## References

- ADR-2605191358 — yoro/murakumo RW-free rewrite per-path map (parent ADR being extended)
- ADR-2605171900 — yoro migration to etzhayyim (Stages 1–5; Step 8 is the cutover gate)
- ADR-2605172000 — etzhayyim RW-free substrate hard rule
- ADR-2605171800 — LangGraph Pregel → MST → IPFS → L2 anchor pipeline
- ADR-2605214000 — Murakumo no-VKE mesh + substrate-fit verdict taxonomy
- ADR-2605215000 — Murakumo-fleet-only inference, no RunPod
- ADR-2605202100 — magatama-cell-runner launchd (Tier 1 常駐稼働)
- ADR-2605181100 — MST encrypted records (`app.etzhayyim.encrypted.*`)
- `20-actors/magatama/py/YORO-PYTHON-MIGRATION-NOTES.md` — full per-function table (40 rows)
- `20-actors/magatama/py/src/pymagatama/primitives/yoro_social_murakumo.py` — skeleton implementation
- `20-actors/magatama/py/src/pymagatama/primitives/yoro_product_ingest_murakumo.py` — skeleton implementation
- `20-actors/magatama/py/tests/test_yoro_murakumo.py` — substrate-fit regression test
- `20-actors/AUDIT-RUNPOD-RW-2026-05-21.md §3` — source audit findings
- `50-infra/mst-projector/` — MST → CID-pinned aggregate snapshot projector (scaffold)
- `50-infra/anchor-cron/` — Base L2 batched anchor (scaffold)
- `20-actors/etzhayyim-sdk/README.md` — SDK API surface + hard rules
