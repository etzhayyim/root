---
id: adr-2605212000-yatabase-phase2-autonomous-growth-actors
title: "yatabase — Phase 2 Autonomous Growth Engine + LangGraph Actor Design"
status: active
doc_type: adr
topic: yatabase-product-bmc
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - yatabase SaaS phase roadmap (Phase 2 / 3 / 4)
  - yatabase LangGraph autonomous growth actor set
  - yatabase cron schedule SSoT (all graphs on lg-yatabase pod)
related:
  - adr-2605210001-yatabase-minimax-pricing-bmc
  - adr-2605210000-yatabase-deploy-first-query
  - adr-2605080600-langgraph-server-granian-l3-runtime
supersedes: []
superseded_by: []
---

# yatabase — Phase 2 Autonomous Growth Engine + LangGraph Actor Design

## 0. Context

ADR-2605210001 confirmed the minimax-optimal pricing grid (Pro ¥4,980/mo) and declared
3 structural moats (MCP-first, multi-language, BWA $0 egress). Sprint 1 completed:
- ✅ H2: LP pivot to "graph DB BaaS" (2026-05-21)
- ✅ H1 partial: mcpservers.org submitted, awesome-mcp-servers PR pending
- ✅ bmc_agent daily cron live on Vultr GPU pod (09:03 JST)

This ADR defines:
1. Next 3 phases of the yatabase SaaS business
2. LangGraph actor set for autonomous growth (lead discovery → activation → conversion → retention)
3. Sprint 2 hypotheses and KPIs

---

## 1. Phase Roadmap

### Phase 2 — Autonomous Growth Engine (2026-05-22 → 2026-06-15)

**Goal**: ≥1 paying customer (MRR ≥ ¥4,980)

| Hypothesis | Metric | Gate |
|---|---|---|
| H1: MCP listing → 5× signups | signups/week | listing live |
| H4: LP A/B 3-way test | conversion rate of hero copy | CF A/B 2026-06-04 |
| H5: HN + GitHub lead gen → 5 qualified leads/week | `vertex_lead` ingested/week | lead_discovery cron live |
| H6: Day-7 activation sequence → >5% Free→Paid | conversion within 30d | activation cron live |

**Key deliverables**:
- 4 new LangGraph actors (lead_discovery, activation, conversion, retention) deployed via ConfigMap
- MCP listing live on Cursor + Claude Desktop MCP marketplace
- LP A/B test (H4) via Cloudflare A/B

### Phase 3 — Monetization (2026-06-15 → 2026-07-31)

**Goal**: Break-even — 9 Pro tenants (MRR ≥ ¥44,820)

| Hypothesis | Metric | Gate |
|---|---|---|
| H7: Conversion trigger → >5% free→paid | conversion rate | conversion actor |
| H8: Retention loop → churn <5%/mo | monthly churn rate | retention actor |
| H9: sakamoto CS → 80% ticket deflection | % issues auto-resolved | sakamoto LangGraph |
| H10: Business tier → 1 Business customer | MRR ≥ ¥98,000 | Stripe Business tier |

**Key deliverables**:
- Stripe upgrade flow A/B (prompt at 80% quota vs. soft-wall at 100%)
- sakamoto CS agent (LangGraph): tier = Free/Starter, escalates to human for Pro+
- Business tier introduction with SLA enforcement
- metrics_daily actor feeding dashboard

### Phase 4 — Scale (2026-08-01 → 2026-10-31)

**Goal**: 50 Pro + 2 Business = MRR ≥ ¥445,000 (≈ $3K), ARR ≥ ¥5.3M

| Hypothesis | Metric | Gate |
|---|---|---|
| H11: OWL DL tier drives Business → Enterprise upgrade | upgrade count | OWL DL GA |
| H12: Multi-region (SJC + TYO-1) → JP-local latency | P95 query latency <50ms | Vultr TYO-1 |
| H13: GraphQL + Realtime WS → 3× session depth | queries/session | WebSocket endpoint |
| H14: Enterprise pipeline → 1 ¥1M/mo deal | enterprise MRR | enterprise_prospector |

---

## 2. LangGraph Actor Architecture

All actors run as LangGraph `StateGraph` graphs registered on the `lg-yatabase` pod
(`60-apps/etzhayyim-project-yatabase/lg/`). Each is imported in `server.py`, exposed via
`/runs` and `/xrpc/com.etzhayyim.apps.yata.lg.*`, and scheduled via APScheduler.

```
lg-yatabase pod (mitama-udf namespace, Vultr GPU node)
├── bmc_agent         daily 09:03 JST  ← existing
├── lead_discovery    every 6h (0 */6) ← Phase 2
├── activation        daily 08:30 JST  ← Phase 2
├── conversion        daily 10:15 JST  ← Phase 2
├── retention         daily 11:00 JST  ← Phase 2
├── metrics_daily     daily 09:00 JST  ← Phase 2 (feeds bmc_agent)
├── marketing         every 6h         ← existing
└── sales             hourly           ← existing
```

### 2.1 lead_discovery

**Purpose**: Autonomous HN + GitHub stargazer lead generation.

**State**:
```python
class LeadDiscoveryState(TypedDict, total=False):
    run_date: str
    hn_stories: list[dict]      # raw HN hits
    gh_users: list[dict]        # GitHub stargazers with public emails
    new_leads: list[dict]       # filtered, not already in vertex_lead
    ingested: int               # count inserted
    summary: str
```

**Pipeline**: `search_hn → search_github → filter_new → ingest → report`

- `search_hn`: Algolia HN search for past-week stories mentioning
  "graph database", "neo4j alternative", "knowledge graph", "cypher query",
  "dgraph", "memgraph". Extract: url, author, score, created_at.
- `search_github`: GitHub Search API for users who recently starred
  `neo4j/neo4j`, `dgraph-io/dgraph`, `memgraph/memgraph`, `supabase/supabase`.
  Extract: login, email (if public), company, location.
- `filter_new`: Cross-check against `vertex_lead` (deduplicate by domain/email).
- `ingest`: `INSERT INTO vertex_lead` for each new lead with `source='discovery'`,
  `outreach_status='new'`.
- `report`: Write summary to `vertex_email_outbox` (kind='lead-discovery-report').

**Schedule**: `0 */6 * * *` (4× daily, UTC).

### 2.2 activation

**Purpose**: Day-3 and day-7 onboarding sequence for inactive free tenants.

**State**:
```python
class ActivationState(TypedDict, total=False):
    run_date: str
    d3_candidates: list[dict]   # signed up 3d ago, 0 queries
    d7_candidates: list[dict]   # signed up 7d ago, <10 queries
    sent_d3: int
    sent_d7: int
    summary: str
```

**Pipeline**: `find_inactive → enqueue_d3 → enqueue_d7 → report`

- `find_inactive`: Query `vertex_api_key` for tenants where
  `signup_at BETWEEN NOW()-4d AND NOW()-3d AND query_count = 0` (d3)
  and `signup_at BETWEEN NOW()-8d AND NOW()-7d AND query_count < 10` (d7).
- `enqueue_d3`: Insert `vertex_email_outbox` with kind=`'activation-d3'` —
  "Here's your first Cypher query" with a ready-to-run snippet.
- `enqueue_d7`: Insert with kind=`'activation-d7'` — "Still stuck?" with
  MCP quickstart link + Calendly link for a 15-min setup call.
- `report`: summary to bmc_agent state (env `BMC_ACTIVATION_D3`, `BMC_ACTIVATION_D7`).

**Schedule**: `30 8 * * *` (08:30 JST daily, before bmc_agent at 09:03).

### 2.3 conversion

**Purpose**: Usage-based upgrade trigger when free tenants approach quota.

**State**:
```python
class ConversionState(TypedDict, total=False):
    run_date: str
    approaching_quota: list[dict]   # >80% node or MCP quota used
    high_activity: list[dict]       # >100 queries/week on free
    triggered: int                  # emails sent
    summary: str
```

**Pipeline**: `find_candidates → score → enqueue_offer → report`

- `find_candidates`: Free tenants with `node_count > 400K` (80% of 500K) OR
  `mcp_calls_month > 8K` (80% of 10K). Also: free tenants with `query_count_7d > 100`.
- `score`: Deterministic urgency score (0-100). LLM augmentation via `_llm.call_llm_json`
  for personalized benefit framing.
- `enqueue_offer`: Insert kind=`'upgrade-trigger'` into `vertex_email_outbox`.
  Body highlights the specific limit they're approaching + concrete Pro benefit.
  Idempotent: skip if kind=`'upgrade-trigger'` sent within last 14d.
- `report`: Summary with `triggered` count.

**Schedule**: `15 10 * * *` (10:15 JST daily).

### 2.4 retention

**Purpose**: Churn signal detection and win-back for paid tenants.

**State**:
```python
class RetentionState(TypedDict, total=False):
    run_date: str
    low_risk: list[dict]       # paid, 7-13d no queries
    medium_risk: list[dict]    # paid, 14-20d no queries
    high_risk: list[dict]      # paid, 21d+ no queries (escalate human)
    reengaged: int
    escalated: int
    summary: str
```

**Pipeline**: `detect_signals → classify_risk → engage_low_medium → escalate_high → report`

- `detect_signals`: Paid tenants (`plan IN ('starter','pro','business')`) with
  `last_query_at < NOW() - 7d` OR 7d query volume < 20% of prior-7d average.
- `classify_risk`: Bucket by inactive duration: low (7-13d), medium (14-20d), high (21d+).
- `engage_low_medium`: kind=`'reengagement-low'` / `'reengagement-medium'`.
  Low: "What are you building?" direct question. Medium: "Can we help?" + link to
  new features (e.g. OWL reasoning, SPARQL).
  Rate-limit: skip if kind=`'reengagement-*'` sent within last 30d.
- `escalate_high`: Insert kind=`'churn-escalate'` with `status='queued-no-recipient'`
  — human operator reviews and decides whether to offer discount or cancel.
- `report`: Summary with risk counts.

**Schedule**: `0 11 * * *` (11:00 JST daily).

### 2.5 metrics_daily

**Purpose**: Daily KPI snapshot for bmc_agent and Studio dashboard.

**State**:
```python
class MetricsDailyState(TypedDict, total=False):
    run_date: str
    mrr_jpy: dict[str, int]     # by tier: {free: 0, starter: N, pro: N, ...}
    mrr_total_jpy: int
    activated_count: int        # tenants with >10 queries in last 7d
    total_tenants: int
    query_lang_split: dict      # {cypher: %, sparql: %, sql: %}
    mcp_calls_total: int        # last 30d
    conversion_rate_30d: float  # free→paid in last 30d
    churn_rate_30d: float       # paid→cancelled in last 30d
    summary: str
```

**Pipeline**: `collect_mrr → collect_usage → collect_cohort → snapshot → report`

- `collect_mrr`: Count tenants per plan, multiply by tier price.
  `vertex_api_key.plan` → {starter: ¥1,980, pro: ¥4,980, business: ¥98,000}.
- `collect_usage`: Aggregate query volume, query language split, MCP call count
  from `vertex_billing_event` (last 30d).
- `collect_cohort`: Cohort analysis — signups in last 30d → how many activated
  (>10 queries) → how many paid. Derive conversion_rate.
- `snapshot`: Insert row into `vertex_bmc_metrics_daily` (new table, see §3).
- `report`: Emit summary string consumed by bmc_agent `check_outbox` context.

**Schedule**: `0 9 * * *` (09:00 JST daily, 3 min before bmc_agent).

---

## 3. New Database Table

```sql
-- Migration: 20260521100000_vertex_yatabase_metrics_daily.sql
CREATE TABLE IF NOT EXISTS vertex_yatabase_metrics_daily (
    run_date         DATE         NOT NULL,
    mrr_total_jpy    INTEGER      NOT NULL DEFAULT 0,
    mrr_by_tier      JSONB        NOT NULL DEFAULT '{}',
    total_tenants    INTEGER      NOT NULL DEFAULT 0,
    activated_count  INTEGER      NOT NULL DEFAULT 0,
    mcp_calls_30d    INTEGER      NOT NULL DEFAULT 0,
    query_lang_split JSONB        NOT NULL DEFAULT '{}',
    conversion_rate  NUMERIC(5,4) NOT NULL DEFAULT 0,
    churn_rate       NUMERIC(5,4) NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (run_date)
);
```

---

## 4. NSID Map (new actors)

| NSID | Graph | Description |
|---|---|---|
| `com.etzhayyim.apps.yata.lg.leadDiscovery.run` | `lead_discovery` | HN + GitHub lead gen |
| `com.etzhayyim.apps.yata.lg.activation.run` | `activation` | Day-3/7 onboarding |
| `com.etzhayyim.apps.yata.lg.conversion.run` | `conversion` | Quota-based upgrade trigger |
| `com.etzhayyim.apps.yata.lg.retention.run` | `retention` | Churn detection + win-back |
| `com.etzhayyim.apps.yata.lg.metricsDaily.run` | `metrics_daily` | KPI snapshot |

---

## 5. Cron Schedule (full, post-Phase-2)

| Time (JST) | Actor | Trigger |
|---|---|---|
| 00:00 / 06:00 / 12:00 / 18:00 | lead_discovery | Every 6h |
| 08:30 | activation | Daily |
| 09:00 | metrics_daily | Daily (feeds bmc_agent) |
| 09:03 | bmc_agent | Daily (existing) |
| 09:15 | marketing | Every 6h, overlaps |
| 10:15 | conversion | Daily |
| 11:00 | retention | Daily |
| Every hour :15 | sales | Hourly (existing) |

---

## 6. Break-even Path

```
Phase 2 end (2026-06-15): target 3 Pro = ¥14,940 MRR  (75% of fixed cost)
Phase 3 end (2026-07-31): target 9 Pro = ¥44,820 MRR  (break-even)
Phase 4 end (2026-10-31): target 50 Pro + 2 Business = ¥445,000 MRR
ARR at Phase 4: ¥5.3M (~$35K)
```

LTV:CAC stays >16× because all lead acquisition is autonomous (LLM inference
on self-hosted Vultr A16 = ¥0 variable cost, human time = 0).

---

## 7. Decision

This ADR formalises:
1. Phase 2 = Autonomous Growth Engine, 4 new LangGraph actors, Sprint 2 KPIs
2. Phase 3 = Monetization, break-even at 9 Pro by 2026-07-31
3. Phase 4 = Scale to ¥5.3M ARR by 2026-10-31
4. All actors live on the existing Vultr GPU pod via ConfigMap overlay (no Docker rebuild needed for Phase 2)
5. metrics_daily feeds bmc_agent via the same `vertex_email_outbox` / env-var pattern

Next review: 2026-06-15 (Phase 2 end) or on first paying customer (whichever first).
