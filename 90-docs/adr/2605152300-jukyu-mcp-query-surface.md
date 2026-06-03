---
id: "2605152300"
title: "Jukyu MCP Query Surface — XRPC endpoints + bpmn-dispatcher proxy routing"
status: active
doc_type: adr
topic: jukyu-mcp-query-surface
authoritative: true
last_verified: 2026-05-15
date: "2026-05-15"
authors: ["jun@etzhayyim.com"]
tags: ["jukyu", "mcp", "xrpc", "langgraph", "bpmn-dispatcher"]
---

# Jukyu MCP Query Surface

## Context

`jukyu.etzhayyim.com` runs global supply-demand equilibrium analysis via a resident K8s LangGraph/Pregel pod (`lg-jukyu`, `mitama-udf` namespace). The Pregel loop runs every 15 minutes, writing results to four RisingWave MVs. Before this ADR, the pod exposed `/cron/equilibrium`, `/extract/shocks`, and `/export/brief` but had no queryable MCP surface — callers had no way to read balance data, supply-chain topology, or company exposure rankings without direct pod access.

This ADR documents the implementation of four new XRPC MCP query endpoints and the bpmn-dispatcher routing changes that wire them to the public `jukyu.etzhayyim.com` CF edge worker.

## Decision

### 1. Four new XRPC endpoints in `pymagatama.jukyu.server`

| NSID | Source MV | Key filters | Max rows |
|---|---|---|---|
| `com.etzhayyim.apps.jukyu.queryBalance` | `mv_jukyu_global_balance` | domain, countryCode, productFamily | 500 |
| `com.etzhayyim.apps.jukyu.querySupplyChain` | `mv_jukyu_supply_chain_trace` | domain, countryCode, productFamily, nodeCode | 1000 |
| `com.etzhayyim.apps.jukyu.rankCompanyExposure` | `mv_jukyu_company_exposure_rank` | domain, countryCode, minRiskScore | 250 |
| `com.etzhayyim.apps.jukyu.explainNode` | `vertex_jukyu_supply_node` + `mv_jukyu_supply_chain_trace` + `mv_jukyu_global_balance` | nodeCode (required), domain | node + chain (50) + balance (10) |

All endpoints:
- Accept `POST` with JSON body
- Authenticate via `x-api-key` header (same `LG_JUKYU_API_KEY` secret as cron endpoints, optional binding)
- Use `fetch_all(sql, tuple(params))` — synchronous psycopg2 pool, exact-match `=` filters only (no CONTAINS/LIKE)
- Return `{"ok": true, "count": N, "rows": [...]}` on success; `explainNode` returns `{"ok": true, "node": {...}, "chainCount": N, "chain": [...], "balance": [...]}` or `{"error": "not_found"}` 404

### 2. bpmn-dispatcher lg-jukyu proxy routing

The bpmn-dispatcher's `dispatch()` function uses a static prefix-match table (`LG_{NAME}_PROXY_PREFIXES`) to forward NSIDs to pod-internal URLs. Added:

```python
LG_JUKYU_INTERNAL_URL = os.environ.get(
    "LG_JUKYU_INTERNAL_URL",
    "http://lg-jukyu.mitama-udf.svc.cluster.local:8000",
)
LG_JUKYU_PROXY_PREFIXES = ("com.etzhayyim.apps.jukyu.",)
LG_JUKYU_UTIL_PATHS = frozenset({"/extract/shocks", "/export/brief"})
```

The `dispatch()` function checks `LG_JUKYU_PROXY_PREFIXES` before the `vertex_bpmn_lexicon_binding` RisingWave lookup, so no DB registration is needed. Util paths (`/extract/shocks`, `/export/brief`) are registered as dedicated `aiohttp` routes at `make_app()` startup — the same pattern used by `lg-animeka` and `lg-malak`.

### 3. CF worker UTIL_PATHS routing gap fix

`jukyu.etzhayyim.com` app.ts previously routed only NSID-prefixed and `CRON_PATHS` requests to the dispatcher. Added `UTIL_PATHS = new Set(["/extract/shocks", "/export/brief"])` and included it in the routing condition, enabling those two non-XRPC paths to reach the dispatcher correctly.

## Routing chain

```
POST jukyu.etzhayyim.com/xrpc/com.etzhayyim.apps.jukyu.queryBalance
  → CF Worker (app.ts): NSID_PREFIX match → proxyToDispatcher
    → dispatcher.etzhayyim.com/xrpc/com.etzhayyim.apps.jukyu.queryBalance
      → bpmn-dispatcher: LG_JUKYU_PROXY_PREFIXES match → _proxy_to_lg_pod
        → lg-jukyu.mitama-udf.svc.cluster.local:8000/xrpc/com.etzhayyim.apps.jukyu.queryBalance
          → FastAPI + psycopg2 → RisingWave mv_jukyu_global_balance
```

## RisingWave MV column contracts (verified 2026-05-15)

**`mv_jukyu_global_balance`**: domain, country_code, region_code, product_code, product_family, supply_quantity, demand_quantity, inventory_quantity, balance_quantity, latest_observed_at, avg_confidence, observation_count

**`mv_jukyu_supply_chain_trace`**: domain, src_node_code, src_node_type, src_country_code, src_region_code, dst_node_code, dst_node_type, dst_country_code, dst_region_code, dependency_type, dependency_weight, product_family, is_critical_path

**`mv_jukyu_company_exposure_rank`**: domain, company_id, company_name, country_code, risk_score, exposure_count, critical_exposure_count, avg_dependency_weight, last_propagated_at

**`vertex_jukyu_supply_node`**: node_code, node_type, country_code, region_code, product_family, domain, capacity, capacity_unit, operator_company_id, status, confidence

## Deployed image tags

- `lg-jukyu`: `ghcr.io/etzhayyim/pymagatama:jukyu-mcp-query-1127e93592e-20260515170344-amd64`
- `bpmn-dispatcher`: rebuilt same session with lg-jukyu routing additions

## Consequences

- All four query endpoints respond through `jukyu.etzhayyim.com` (HTTP 200, verified 2026-05-15)
- `explainNode` requires real node codes (format: `JURONG-NAPH`, `ARA-NAPH`, `CHIBA-C2`) from `vertex_jukyu_supply_node`
- The bpmn-dispatcher proxy pattern is now consistent across: lg-animeka, lg-malak, lg-jukyu (and others)
- No RisingWave `vertex_bpmn_lexicon_binding` row needed for jukyu — static prefix table is the SSoT

## Files changed

- `20-actors/magatama/py/src/pymagatama/jukyu/server.py` — 4 new XRPC endpoints
- `60-apps/etzhayyim-project-jukyu/appview/jukyu-ui-jukyu001/src/app.ts` — UTIL_PATHS routing
- `20-actors/magatama/py/src/pymagatama/dispatcher_main.py` — lg-jukyu proxy constants + routing
- `50-infra/k8s/lg-jukyu/deployment.yaml` — updated image tag
