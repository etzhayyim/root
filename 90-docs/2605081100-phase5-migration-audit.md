# Phase 5 BPMN Migration Audit (2026-05-08)

ADR-2605080600 Phase 5 — `Zeebe timer-start BPMN → K8s CronJob + LangGraph StateGraph`.

## Scope: 345 active timer-start BPMNs remaining (after batches 1-3)

| Category | Distinct BPMNs | Migration kind | Priority |
|---|---|---|---|
| **gov_heartbeat** (`gov_*_heartbeat_tick`) | 140 | Possibly dead — CF Worker `xrpc.com.etzhayyim.gov{Country}.heartbeatTick` handlers may no longer exist after ADR-0095 (3-layer identity, 2026-04-26 ERC725 simplification). **Audit before migrating.** If alive, single generic graph + 1 looping CronJob. | LOW |
| **other** (heterogeneous: air_*, ads_*, agent_*, arms_*, copyright_*, etc.) | 87 | Per-actor case-by-case; requires reading each XML | MEDIUM |
| **open_*** (open_smartphone, open_cyber, open_oss, etc.) | 22 | Per-NSID; primitives in `kotodama.primitives.open_*` | MEDIUM |
| **maps_*** | 22 | maps live-tracking (R/PT10S aircraft, R/PT5M track) — sub-minute cadence cannot map cleanly to K8s CronJob (1m floor). Need single long-running poller, not CronJob. | DEFER |
| **tsukuru_isic_*** | 21 | Daily ISIC sector pulse, all `generic.db.select` + audit. Single generic graph + 21 CronJobs differing by `industryCodes` input. | MEDIUM |
| **science_*** | 9 | Compound/crystal/element/protein/taxon seed | LOW |
| **kaisya_*** | 8 | Daily/weekly briefings, `generic.llm.chat` based | MEDIUM |
| **coverage_*** | 8 | Coverage gap inference (lda_*, kdrift, fission, census). Several already wired through `kotodama.primitives.coverage_gap`. | HIGH |
| **rl_*** | 6 | Active inference / preference / trajectory | LOW |
| **pds_*** | 6 | PDS internal cron (rotateKeys, syncWriteOutbox, warmCache). **Critical infra — keep running on Zeebe until validated.** | DEFER |
| **netintel_*** | 5 | DNS/IP/whois/banner/fingerprint delta scans | MEDIUM |
| **kiyo_*** | 3 | citation/embedding/digest (academic) | LOW |
| **patent_*** | 3 | EPO/USPTO weekly | MEDIUM |
| **natural_person_*** | 3 | Cohort generation | LOW |
| **shosha_***, **agent_*** | 2 | Stragglers from earlier batches | HIGH |

## Already migrated (cumulative)

| Batch | BPMNs | Status |
|---|---|---|
| **Batch 1** (wellbecoming + shinka_cron_tick + animeka_autopilot + shosha_*) | ~14 | live |
| **Batch 2** (isbn_ingest_*) | 6 | live (smoke ✓) |
| **Batch 3** (aria_* + adsk_ingest_dataset) | 8 | live (smoke ✓) |
| **Total migrated** | ~28 | |

## Recommendation for next iterations

**Highest leverage**:

1. **gov_heartbeat audit + bulk action** (140 BPMNs)
   - Step 1: query `vertex_repo_record WHERE collection = 'app.bsky.feed.post' AND uri LIKE '%gov%' AND ts_ms > now()-7d` to confirm the BPMNs are emitting real social posts (i.e., heartbeats are still doing meaningful work).
   - Step 2a: if dead → mass-mark `status='superseded'` (no replacement needed). 140 BPMNs retired in one SQL query.
   - Step 2b: if alive → single generic graph `gov_heartbeat_generic` + 1 CronJob iterating the country list internally. 140 → 1.

2. **shosha + agent stragglers** (2 BPMNs)
   - Quick win, complete shosha/agent migration

3. **coverage_*** (8 BPMNs)
   - Most primitives exist (`coverage_gap.py`). Modest batch size.

**Lowest priority / defer**:
- maps_* (sub-minute polling unsuitable for CronJob)
- pds_* (infra-critical, validate carefully)
- science_* / rl_* / kiyo_* / natural_person_* (low-traffic, can wait)

## Phase 6 (Zeebe shutdown) gating

Cannot proceed until:
- All timer-start BPMNs migrated OR superseded
- maps_* sub-minute polling redesigned (long-running poller pod, not CronJob)
- pds_* validated against alternative cron pathway

Estimated 3-5 more batches + 1 gov_heartbeat audit before Zeebe shutdown is safe.
