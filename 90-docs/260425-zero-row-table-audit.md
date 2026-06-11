# Zero-row vertex_*/edge_* table audit (Phase 4)

Date: 2026-04-25
Scope: prod Kotoba/Datomic (Vultr LAX, `45.32.79.245:4566`).
Followup to: `260424-nsid-traffic-audit.md`, `260424-bsky-compat-kotoba-split.md`.

## Method

1. From `pg_stat_user_tables`, list every `vertex_*` / `edge_*` table with `n_live_tup = 0` → **656 zero-row tables** (out of 934 total = 70%).
2. Bulk-grep `50-infra/cloudflare/workers/`, `60-apps/`, `20-actors/`, `30-graph/graph-schema/scripts/` for any `.insertInto("X")` / `.updateTable("X")` / `INSERT INTO X` / `UPDATE X` referencing each table → **178 distinct tables receive writes from live source**.
3. Set diff:
   - 0-row ∩ has write callsite = **10 tables** ("live but empty" — handler exists, but no traffic has triggered it yet)
   - 0-row ∖ write callsite = **646 tables** ("no source writes here" — pure candidate)

## What the 646 actually are (don't mass-drop)

Top 10 prefixes among the 646:

| prefix | count | provenance |
|---|---|---|
| `open` | 91 | ADR-0017 Wave 9/11 / Hormuz / chokepoints / cybersecurity — **active 2026-04-24/25 work** (cc3c5d2b55b, 2316cc3e3fc, ef55f5e8854, etc) |
| `anime` / `kuruma` / `vin` | 24+21+10 | media-gamers / car cluster — schema-ahead per `90-docs/260414-domain-coverage-depth-design.md`, app handlers TBD |
| `workspace` / `xlsx` / `pptx` / `gcal` / `gdrive` / `gmeet` | 20+14+10+7+7+7 | M365 / Google Workspace ingest — schema added 2026-04-17, ingest job not yet routed through atproto Worker (uses external loader) |
| `hc` | 12 | health care ADR cluster |
| `bpmn` | 11 | ADR-0056 BPMN-as-actor — dispatched dynamically via path-DID, not via static `insertInto("bpmn_*")` callsites in TS source. **False positive — DO NOT DROP** |
| `oshinobi` / `isekai` / `vin` / `yukkuri` / `nokyo` / `shiharai` / `pptx` / `atrecord` | 10 each | various waves |

Migration age distribution of the 646:

| bucket | count |
|---|---|
| `202604` (this month — schema added in past 25 days) | **420 / 646 (65%)** |
| `0001_` … `0xxx_` legacy numbered migrations | 153 / 646 (24%) |
| unresolved (no CREATE TABLE found in `migrations/`) | 73 / 646 (11%) |

**65% of the candidate set was added this month**. These are almost certainly schema-ahead for upcoming app deploys, not abandoned. Mass-DROP would delete in-flight work — exactly what the advisor warned against.

Even the 153 "legacy" candidates include `edge_blocks`, `edge_likes`, `edge_owns`, `edge_filed_at`, `edge_emits_risk`, `edge_enforces`, `edge_bpmn_*`, `edge_oil_*` — all of which have legitimate populating paths (Bluesky user actions, governance events, BPMN dispatch, oil supply chain ingestion) that the static `.insertInto()` check doesn't catch.

## Why static "no write callsite" is not enough

| populating path | static check sees? |
|---|---|
| direct Kysely `db.insertInto("X")` | ✅ caught |
| raw `INSERT INTO X` | ✅ caught |
| dynamic dispatch from a string variable: `db.insertInto(tableNameFromConfig)` | ❌ missed |
| BPMN-as-actor (ADR-0056): `processDef → vertex_<actor>_<kind>` resolved at runtime | ❌ missed |
| graph worker `handleCollection(nsid)` → `kagamiWriteVertex` (collection→table convention) | ❌ missed |
| migration scripts that seed via raw SQL files (e.g. ESCO/HS/SITC bulk loads) | partially — depends on file location |
| external psql / local CLI seeding (deps.toml-driven) | ❌ missed by source scan |

The 178 "writes seen" set is therefore a **lower bound** of live tables; the 646 candidate set has many false positives.

## Recommendation: per-domain owner cleanup, not bulk drop

1. **Do NOT mass-DROP the 646.** False-positive risk is too high.
2. Instead, when an app/cluster is decommissioned (`deps.toml [[migrations]] status="abandoned"`), the owner explicitly DROPs the tables for that cluster. Wave 0 already done by deletion of `vertex_repo_block` MST writers (260424).
3. The 10 "live but empty" set is genuinely worth attention — these tables HAVE handler code, just no traffic. Most likely sparse / weekly endpoints. Wait for ≥7-day tail data (`vertex_pds_tail_event` accumulation in progress) before judging.
4. Follow-on: build a maintenance script that runs the 0-row + no-write-callsite intersect monthly, and surface NEW arrivals (tables that *have been* zero for >30d AND have no write callsite). Those are higher-confidence candidates.

## Artifacts

- `/tmp/wave-b-drop-candidates.txt` — 646 raw candidates (ephemeral, regenerable)
- `/tmp/wave-b-live-but-empty.txt` — 10 tables with handlers but no traffic
- `/tmp/wave-b-table-mig.tsv` — 573/646 mapping to creating migration filename
- Source scanner: `/tmp/wave-b-fast.py` (~5s for the full sweep)

## Wave 0 (already done in 260424 session)

Wave 0 = MST commit path removal. Deleted code paths whose target tables are
also in the 646 candidate list (kept the tables — see `260424-bsky-compat-kotoba-split.md` for why
DROPing them was deferred):
- `vertex_repo_block` — 0 rows confirmed; handler removed but table preserved for future federation rebuild.
- (the `repoBackfillMst` handler now returns 410 Gone)

## What this audit does NOT do

- Does NOT propose any DROPs against prod RW. Producing the candidate list is the deliverable. Drop authority remains with each cluster's owner.
