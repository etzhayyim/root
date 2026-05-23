# Crawler Seed Auto Expansion Design (2026-02-25)

## Goal
- Expand crawl coverage from current seed set automatically.
- Evaluate discovered links/domains and promote high-quality domains to seeds safely.
- Keep scheduler stable (no uncontrolled seed explosion).

## Current State (Measured)
- Endpoint: `https://422c6fae.etzhayyim.com`
- Health: `200` (healthy)
- Stats snapshot:
  - `hosts=262`, `total_urls=1464`, `completed=914`, `errors=115`, `pending=23`
- Metrics snapshot:
  - `jobs_total=262`, `jobs_completed=145`, `jobs_failed=115`, `jobs_running=2`, `results_total=1423`
- Scheduler snapshot:
  - `seed_total=1000`, `due_now=1000`, `last_tick_at=2026-02-24T09:56:33Z`, `total_runs=5`, `total_queued=66`
- Seed coverage (seed list vs at-least-once completed seed jobs):
  - `40 / 1000 = 4.0%`

## Problems
- Scheduler backlog is saturated (`due_now=1000`), so expansion must be throttled.
- Current crawler stores link count only; outbound link/domain telemetry is not persisted.
- No first-class API to promote candidate domains into seeds automatically.
- Many failures exist; auto-add must avoid low-quality hosts (cdn/static/internal).

## Design Overview

### 1) Persist Link Candidate Telemetry During Crawl
Add per-result domain candidate extraction in `runCrawl`:
- From discovered links (`normalizeAndResolveLink` output), derive host candidates.
- For each candidate host, accumulate stats in KV:
  - `seen_count`, `success_ref_count`, `source_seed_count`, `first_seen_at`, `last_seen_at`
  - `sample_url`, `source_categories` (gov/news/intl/adult/unknown)
  - `rejected_reason` (optional)

KV keys:
- `crawler:seed:candidate:<host>`
- `crawler:seed:candidate:index:v1`

### 2) Link/Host Scoring
Host score formula (v1):
- `+8 * success_ref_count`
- `+0.2 * total_outbound_links_from_source_pages`
- `-3 * fail_ref_count`
- `+category_bonus` where:
  - `gov +20`, `intl +16`, `news +12`, `adult +8`, `unknown +0`
- `-hard_penalty` for risk patterns:
  - `svc.cluster.local`, private TLD/internal host, static/cdn/assets host, pure media hosts

Minimum promotion gate (default):
- `score >= 30`
- `success_ref_count >= 2`
- `host not already in seed catalog`
- `not blocked by denylist`

### 3) Auto Promotion Workflow
Introduce two MCP tools + REST endpoints:
- `crawler.seed_candidates`
  - list candidates with score and reason fields
- `crawler.seed_promote`
  - promote top-N candidates (`dry_run` default true)

Promotion behavior:
- infer category from source category majority.
- default seed policy:
  - `enabled=true`
  - `frequency_minutes` by category (`gov=720`, `intl=360`, `news=90`, `adult=240`, `unknown=180`)
  - `priority` from normalized score (e.g. 40-95)
- deduplicate by normalized host.
- cap additions per run (`max_add_per_run`, default 10).

### 4) Seed Catalog Capacity and Queue Control
- Keep active seeds bounded:
  - `active_seed_limit` (default 1200)
- If exceeding limit:
  - demote lowest-score stale seeds (`enabled=false`) instead of hard delete.
- Scheduler fairness:
  - weighted round-robin by category + priority.
  - maintain separate per-category due budgets.

### 5) Safety and Governance
- Add denylist regex and explicit allowlist override.
- Exclude obvious non-content hosts:
  - `cdn.*`, `static.*`, `assets.*`, internal cluster hosts.
- Add provenance fields to seed:
  - `source = manual|bootstrap|auto`
  - `score`, `promoted_at`, `promoted_by_version`

## Data Model Changes

### seedSite extension (backward compatible)
- `Source string \`json:"source,omitempty"\``
- `Score float64 \`json:"score,omitempty"\``
- `PromotedAt string \`json:"promoted_at,omitempty"\``

### new seedCandidate model
- `Host string`
- `SampleURL string`
- `Category string`
- `Score float64`
- `SeenCount int`
- `SuccessRefCount int`
- `FailRefCount int`
- `FirstSeenAt string`
- `LastSeenAt string`
- `Blocked bool`
- `BlockedReason string`

## Runtime Verification Plan

### A. Functional Checks
1. Run one crawl with `follow_external_links=true`.
2. Confirm candidate KV keys are created.
3. `crawler.seed_candidates` returns ranked candidates.
4. `crawler.seed_promote dry_run=true` shows deterministic plan.
5. `crawler.seed_promote dry_run=false` actually adds seeds.
6. `scheduler` returns increased `seed_total` and new seeds with `source=auto`.

### B. Throughput and Stability
- Compare before/after over 60 minutes:
  - `results_per_min`
  - `jobs_failed_ratio`
  - `seed_coverage_ratio`
- Guardrail targets:
  - failure ratio does not worsen > 10%
  - results/min improves or stays neutral with broader host diversity

### C. Search Integration Validation
- Verify newly promoted seed domains appear in crawl results and then searchable via `search` (same Quickwit index `crawler-pages-v1`).

## Immediate Candidate Snapshot (from current results)
Top filtered hosts not in current seed list:
- `nhentai.net` (score 1793.4)
- `hentai2read.com` (269.2)
- `br.youporn.com` (155.4)
- `etzhayyim.com` (152.4)
- `fr.xvideos.com` (105.2)
- `it.xvideos.com` (105.2)
- `example.com` (41.0)
- `httpbin.org` (33.4)
- `xnxx-ru.com` (32.4)
- `xnxx.es` (32.4)

Note:
- `example.com` and `httpbin.org` should be blocked in production by quality policy.

## Rollout Strategy
- Phase 1: telemetry + candidate listing only (no auto-write).
- Phase 2: dry-run promotion in scheduler windows.
- Phase 3: bounded auto-promotion (`max_add_per_run=5..10`) + rollback switches.

Feature flags:
- `SEED_AUTO_EXPAND_ENABLED=0/1`
- `SEED_PROMOTION_DRY_RUN=1` (default)
- `SEED_MAX_ADD_PER_RUN=10`
- `SEED_ACTIVE_LIMIT=1200`

## Open Decisions
- Keep catalog global-only or split per category namespace?
- Allow adult expansion in same pipeline or isolate policy path?
- Hard upper bound for active seeds (1200 vs 1500 vs 2000)?
