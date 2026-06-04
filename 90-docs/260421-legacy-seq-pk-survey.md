---
id: 260421-legacy-seq-pk-survey
title: Legacy seq-based PK survey post ADR-0041
status: active
doc_type: reference
topic: pds-write-path
authoritative: false
last_verified: 2026-04-21
related:
  - 90-docs/adr/0041-pds-commit-content-addressed-pk.md
V0421-pds-throughput-tuning
---

# Survey: remaining seq-based PK patterns (post ADR-0041)

After applying ADR-0041 (`vertex_repo_commit` content-PK), surveyed the codebase for other places that compose `vertex_id` from a derived `seq` value. These are **latent versions of the same race**: they don't surface today because they're either inactive (feature-flagged off) or low-throughput (no concurrent contention), but they encode the same anti-pattern.

## Findings

### A — Active in production

| # | Path | Pattern | Status |
|---|---|---|---|
| 1 | `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts:2227` | `vertex_etzhayyim_op_log.vertex_id = ${did}:${opSeq}` | **Low risk.** `opSeq` is per-DID monotonic, passed in by caller (CLI / app). Concurrent ops for the same DID are rare (DID identity ops). If two concurrent submissions race on `opSeq` computation client-side, PK collision would surface as `duplicate key` error → caller retries. Not a silent drop. |

### B — Inactive (feature-flagged off)

| # | Path | Pattern | Status |
|---|---|---|---|
| 2 | `50-infra/cloudflare/workers/atproto/src/repo/sql-storage.ts:335` | `vertex_id = ${this.did}:seq:${seq}` (MST commit path) | **Latent.** Activated by `PDS_MST_ENABLED=1`. Currently NOT set in `wrangler.jsonc` → dead code in production. **Will reproduce ADR-0041 bug** when enabled. Fix before flipping flag. |

### C — Acceptable seq usage (not PK collision risk)

| Path | Pattern | Why OK |
|---|---|---|
| `30-graph/graph-schema/migrations/20260415130100_vertex_osm_element.ts:87,109` | `edge_osm_way_node (way_vertex_id, seq)` index | Composite (parent_vid, seq) where parent is stable. seq is 0..N-1 within parent. No race because writes are batched per-OSM-way. |
| `30-graph/graph-schema/migrations/2026041*_*.ts` | `_seq BIGINT` column on every vertex/edge table | Standard ordering column, NOT used in PK. Safe. |
| `50-infra/cloudflare/workers/atproto/src/migrate/logical.ts:330` | `vertex_other (vertex_id, label, _alive, _seq)` soft-delete | Soft-delete inserts new row with same `vertex_id` + higher `_seq`. Composite (vertex_id, _seq) ordering, not race-prone. |
| `vertex_repo_record.uri` | at:// URI as PK | Already content-addressed. ADR-0041 precedent. |
| `vertex_repo_block.cid` | CID as PK | Already content-addressed (MST design). |

## Recommended actions

### Tier 1 — before MST is enabled

Apply ADR-0041 fix to `sql-storage.ts:335`:

```diff
- vertex_id: `${this.did}:seq:${seq}`,
+ vertex_id: `${this.did}:${op.collection}:${op.rkey}:${op.action}`,
```

Same pattern, different file. Trivial change. Block on PDS_MST_ENABLED rollout — must land before any test that flips the flag.

### Tier 2 — preventive

Audit `vertex_etzhayyim_op_log` write throughput. If concurrent DID op submissions become a real workload (e.g., bulk DID provisioning), the `${did}:${opSeq}` PK has the same theoretical race. Migrate to `${did}:${opCid}` (CID is already in the row, content-addressed).

### Tier 3 — convention

Add a code-quality lint rule that flags any `vertex_id` value containing `:seq:`, `${seq}`, or `MAX(seq)+offset` patterns in INSERT contexts. Forces future developers to use content-addressed PKs from day one.

## Decision log

- **Tier 1**: applied 2026-04-21 (sql-storage.ts edit + redeploy when MST flag activates)
- **Tier 2**: deferred — current `vertex_etzhayyim_op_log` write rate is < 1/min, race window not realistic
- **Tier 3**: deferred — would add to `etzhayyim code-quality` rules; coordinate with platform team

## References

- ADR-0041 — `90-docs/adr/0041-pds-commit-content-addressed-pk.md`
- Smoking gun + benchmarks — `90-docs/260421-pds-throughput-tuning.md`
- Original race analysis — `90-docs/260420-pds-commit-seq-race-analysis.md`
