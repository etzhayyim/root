---
id: domain-expansion-agent-loop
title: "Domain Expansion Agent Loop — CC S3 → LLM → registerApp → Social Post"
status: active
doc_type: adr
topic: autonomous-growth
authoritative: true
authoritative_for:
  - domain-expansion
last_verified: "2026-04-11"
related:
  - 260409-unified-access-control-shannon-design
  - 260324-source-graph-hybrid-design
---

# Domain Expansion Agent Loop Design

**Date**: 2026-04-11
**Status**: Deployed, verified (Apps 45→77, 17 CC-discovered domains)

## Goal

Autonomous domain coverage growth without manual `etzhayyim seed`. PDS cron discovers new domains from Common Crawl bulk ingest, enriches via LLM, registers as apps, generates social posts and knowledge graphs — all visible on yoro.etzhayyim.com.

## Decision

Projector-pattern agent loop in PDS `scheduled()` handler. 1 domain per 5-min tick. 7 phases per tick.

## Architecture

```
PDS cron (*/5 min) → expandDomainCoverage()
  │
  ├─ Phase 1: Gap Detection
  │   vertex_page LEFT JOIN vertex_app → CC domain without app registration
  │   Fallback: static candidate list (14 authority-chain domains)
  │
  ├─ Phase 2: CC Public S3 Data Fetch
  │   CDX: index.commoncrawl.org/{crawl}-index?url={domain}/*&output=json
  │   WAT: data.commoncrawl.org/{filename} (Range: bytes=offset-end)
  │
  ├─ Phase 3: MCP Fallback (site.etzhayyim.com → gyotaku.etzhayyim.com)
  │   Layer 2: POST /xrpc/com.etzhayyim.apps.site.crawlPage → WET/WAT
  │   Layer 3: POST /xrpc/com.etzhayyim.apps.gyotaku.searchSnapshots → archive
  │
  ├─ Phase 4: Murakumo LLM Classification (on-prem, ¥0)
  │   Input: CC/site/gyotaku context
  │   Output: { domain_summary, sector, knowledge_edges[] }
  │
  ├─ Phase 5: registerApp (Profile + App vertex)
  │   comAtprotoRepoPutRecord → vertex_profile + vertex_app
  │
  ├─ Phase 6: Social Post (Design E Tier 1)
  │   Murakumo LLM → domain announcement post
  │   comAtprotoRepoCreateRecord → app.bsky.feed.post
  │
  └─ Phase 7: Governance + Knowledge Graph
      knowledge_edges → com.etzhayyim.actor.knowledgeEdge × 3-5
      capabilities → com.etzhayyim.actor.app.capabilitiesJson
```

## Data Sources (priority order)

| Layer | Source | API | Fallback |
|---|---|---|---|
| 1 | Common Crawl S3 | `data.commoncrawl.org` CDX + WAT range | Layer 2 |
| 2 | site.etzhayyim.com | `com.etzhayyim.apps.site.crawlPage` XRPC | Layer 3 |
| 3 | gyotaku.etzhayyim.com | `com.etzhayyim.apps.gyotaku.searchSnapshots` XRPC | static desc |

## Verified Results (2026-04-11)

| Metric | Start | End |
|---|---|---|
| Apps | 45 | 77 (+32) |
| CC-discovered domains | 0 | 17 (youtube, pubmed, europa.eu, apple, google, amazon, baidu, etc.) |
| getProfile (yoro) | 1 | 17+ domains displayable |
| Social posts | 0 | 1+ (lists.wikimedia.org confirmed postsCount=1) |
| CC page base | 563,592 | growing with bulk ingest |

## CC-Discovered Domains

| Domain | CC Pages | Registration |
|---|---|---|
| forsale.godaddy.com | 84 | auto |
| www.youtube.com | 70 | auto |
| webgate.ec.europa.eu | 67 | auto |
| www.afternic.com | 65 | auto |
| commons.wikimedia.org | 63 | auto |
| learn.microsoft.com | 57 | auto |
| news.qq.com | 56 | auto |
| data.europa.eu | 53 | auto |
| tv.apple.com | 51 | auto |
| ailegal.baidu.com | 51 | auto |
| play.google.com | 46 | auto |
| classical.music.apple.com | 46 | auto |
| docs.cloud.google.com | 45 | auto |
| pubmed.ncbi.nlm.nih.gov | 43 | auto |
| photos.google.com | 42 | auto |
| docs.aws.amazon.com | 41 | auto |
| lists.wikimedia.org | 41 | auto |

## Growth Rate

| Metric | Value |
|---|---|
| Tick interval | 5 min |
| Domains per tick | 1 |
| Domains per hour | 12 |
| Domains per day | 288 |
| Gap domains available | 50+ (grows with CC ingest) |
| Static candidates | 14/14 consumed |

## Supporting Infrastructure Changes

| Component | Change | Status |
|---|---|---|
| Graph Worker (`worker.ts`) | Structured error (code/suggestion/cypher) | deployed |
| PDS `pds-cache.ts` | `cyWithDiag()` error-preserving queries | deployed |
| PDS `pds-agent-infer.ts` | STARTS WITH → exact match (transpiler-safe) | deployed |
| PDS `pds-helpers.ts` | Authority column promotion (kind/authority_kind/tier/jurisdiction) | deployed |
| PDS `pds-handlers-etzhayyim.ts` | `com.etzhayyim.graph.query` legacy alias | deployed |
| PDS `pds-dispatch.ts` | Stale legacy NSID cleanup | deployed |
| etzhayyim `seed.go` | applyWrites → registerApp canonical path | committed |
| etzhayyim `domain_coverage.go` | vertex_authority_* + vertex_did batch UNION ALL | committed |
| etzhayyim `world_coverage.go` | `_alive` column removal (P10v2) | committed |
| etzhayyim `graph_client.go` | Canonical graph SQL NSID `com.etzhayyim.graph.cypher` | committed |
| etzhayyim `seed_domains.go` | Enriched columns (kind/authority_kind/tier) | committed |

## Key Design Decisions

1. **No seed dependency** — gap detection from CC bulk ingest, not static lists
2. **CC public S3** — `data.commoncrawl.org` CDX + WAT range (not Linode S3)
3. **Projector pattern** — READ → LLM → WRITE per tick (same as `com.etzhayyim.projector`)
4. **Murakumo only** — on-prem LLM, zero cost
5. **Social post per domain** — LLM generates announcement (Design E Tier 1)
6. **30s CPU budget** — 1 domain/tick fits CF Worker limits
7. **Structured errors** — Graph Worker returns code + suggestion for LLM agent recovery

## Files

| File | Role |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/pds-app.ts` | `expandDomainCoverage()` agent loop |
| `50-infra/cloudflare/workers/graph/worker.ts` | Structured error responses |
| `50-infra/cloudflare/workers/atproto/src/pds-cache.ts` | `cyWithDiag()` |
| `50-infra/cloudflare/workers/atproto/src/pds-agent-infer.ts` | Transpiler-safe queries |
| `70-tools/etzhayyim/etzhayyim/domain_coverage.go` | Coverage reconciliation |
| `70-tools/etzhayyim/etzhayyim/seed.go` | registerApp canonical path |
| `90-docs/260411-domain-expansion-agent-loop-design.md` | This document |
