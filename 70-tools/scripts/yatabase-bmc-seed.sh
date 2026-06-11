#!/usr/bin/env bash
# yatabase-bmc-seed.sh — seed initial BMC v1 + 5 lean hypotheses.
#
# Run this after `POST /_bmc/bootstrap` succeeds (i.e. once RW is no
# longer in "cluster is recovering" state). It's idempotent up to the
# vertex_id collisions on bmc:state:v1 / bmc:hyp:H{1..5}-* — re-running
# will fail (correctly) until you POST a new v2.
#
# Required env:
#   YATA_AGENT_ADMIN_KEY   the wrangler secret on kotodama-y4t4b4se
#   YATA_BASE              default https://yatabase.etzhayyim.com
#
# Usage:  YATA_AGENT_ADMIN_KEY=$(security find-generic-password -s etzhayyim.yatabase -a YATA_AGENT_ADMIN_KEY -w) \
#         ./70-tools/scripts/yatabase-bmc-seed.sh

set -euo pipefail
ADMIN="${YATA_AGENT_ADMIN_KEY:?env YATA_AGENT_ADMIN_KEY required}"
HOST="${YATA_BASE:-https://yatabase.etzhayyim.com}"
DEADLINE="${YATA_BMC_DEADLINE_ISO:-2026-06-30T00:00:00Z}"

POST() {
  local path="$1"; local body="$2"
  curl -sS --max-time 30 -X POST "${HOST}${path}" \
    -H "x-yata-admin-key: ${ADMIN}" \
    -H 'content-type: application/json' \
    -d "$body"
}

echo "▸ bootstrap (idempotent if already done)"
POST /_bmc/bootstrap '{}' | python3 -m json.tool

echo
echo "▸ v1 canvas — what yatabase is today (2026-05-11 snapshot)"
POST /_bmc/state "$(cat <<'JSON'
{
  "rationale": "Initial canvas, derived from shipped state at v0.1.0 (P1-P46). Source of truth for measuring divergence as we iterate.",
  "source": "seed",
  "created_by": "operator",
  "canvas": {
    "customerSegments": {
      "bullets": [
        "AI-native devs building MCP-enabled products (primary)",
        "Indie hackers / side projects evaluating graph DB (price-sensitive)",
        "Japan SaaS startups needing 適格請求書",
        "Mid-market data teams (50-500) consolidating graph + storage + auth"
      ]
    },
    "valuePropositions": {
      "bullets": [
        "One bill across graph + object storage + MCP, single sk_live_yata_* key",
        "Starter $13/mo undercuts Supabase Pro $25/mo by ~50%",
        "MCP-native (only competitor with first-party /mcp surface)",
        "Anonymous signup, no email + no credit card required",
        "AT Protocol DID auth (did:web / did:plc) as alternative to email/password"
      ]
    },
    "channels": {
      "bullets": [
        "HN Algolia scrape → cold outreach (autonomous, cron 0 */6)",
        "GitHub stargazers of neo4j/supabase/hasura/dgraph/arangodb (cron 45 */6)",
        "Organic SEO (sitemap.xml, robots, JSON-LD SoftwareApplication + FAQPage)",
        "/comparison page vs Supabase / Neo4j AuraDB / Hasura",
        "/integrations: Cursor / Claude Desktop / Continue.dev MCP listings (manual)"
      ]
    },
    "customerRelationships": {
      "bullets": [
        "Self-service via /docs + /quickstart + /studio + /dashboard",
        "sakamoto (CS AI agent) drafts replies to support@etzhayyim.com",
        "nishino (sales AI agent) drafts cold outreach (operator approves in Studio Leads pane)",
        "tanaka (QA AI agent) hourly probes; chikada (dev AI agent) audit-log triage"
      ]
    },
    "revenueStreams": {
      "bullets": [
        "Subscription: Free $0 / Starter $13 / Developer $33 / Business $650 / Enterprise $6700+ (USD-primary)",
        "JP 適格請求書 invoicing (T9007028460042, etz hayim) for paid JP customers",
        "Future: usage-based overage (api_request, storage_gb_hour, yata_query_cu_ms, mcp_call) above plan cap",
        "Future: marketplace fees on third-party MCP tools that wrap yatabase",
        "Future: professional services / migration consulting (enterprise)"
      ]
    },
    "keyResources": {
      "bullets": [
        "Cloudflare Workers (edge compute, Hyperdrive, R2 cache)",
        "RisingWave Postgres on Vultr VKE LAX (per-tenant schema yata_<sha256(orgDid)[:16]>)",
        "Backblaze B2 (content-addressed object storage)",
        "Stripe Live billing (3 products: Starter / Developer / Business)",
        "4 in-Worker AI agents + 3 autonomous lead-discovery crons + LangGraph bmc_iteration"
      ]
    },
    "keyActivities": {
      "bullets": [
        "Lead generation (HN Algolia + GitHub stargazers, autonomous)",
        "Lead enrichment (homepage scrape, fills contact_email + tech_stack)",
        "Outreach drafting (nishino → operator approves in Studio Leads pane → batch-send)",
        "Customer support (sakamoto drafts replies; operator reviews)",
        "Daily BMC iteration (LangGraph bmc_iteration cron 0 7 * * *)"
      ]
    },
    "keyPartnerships": {
      "bullets": [
        "Cloudflare (Workers + Hyperdrive + R2 + DNS)",
        "Vultr (VKE LAX k8s for yata-zeebe-worker + bpmn-dispatcher)",
        "Backblaze (B2 storage, content-addressed)",
        "Stripe (US payments + Tax for nexus states)",
        "Resend (transactional email — operator must wire RESEND_API_KEY)",
        "RunPod + Murakumo (LLM inference for marketing + sales graphs)"
      ]
    },
    "costStructure": {
      "bullets": [
        "Cloudflare Workers requests (egress-free, ~$5/M req)",
        "Vultr VKE LAX: ~$241/mo (8c/32GB, post-Linode cutover savings $123/mo)",
        "Backblaze B2: ~$0.006/GB-month, content-addressed dedup",
        "Stripe: 2.9% + $0.30 per transaction (US)",
        "Resend: $0 trial, $20/mo for 50k emails (when wired)",
        "RunPod 6000 Ada GPU: per ADR-2605010000 (LLM inference for nishino/sakamoto drafting)"
      ]
    }
  }
}
JSON
)" | python3 -m json.tool

echo
echo "▸ Hypothesis H1 — Cursor/Claude MCP listing drives signups"
POST /_bmc/hypotheses "$(cat <<JSON
{
  "slug": "H1-cursor-mcp-listing",
  "block": "channels",
  "statement": "Listing yatabase as an MCP server in Cursor's / Claude Desktop's marketplace drives ≥5x more weekly signups than HN scrape outreach alone.",
  "metric": "signups_per_week_mcp_referer",
  "metric_query": "sql:vertex_signup_count_window",
  "threshold": 25,
  "baseline": 5,
  "deadline_iso": "$DEADLINE",
  "min_sample": 7
}
JSON
)" | python3 -m json.tool

echo
echo "▸ Hypothesis H2 — /comparison page boosts /quickstart click-through"
POST /_bmc/hypotheses "$(cat <<JSON
{
  "slug": "H2-comparison-quickstart-ctr",
  "block": "valuePropositions",
  "statement": "Visitors landing on /comparison are ≥2x more likely to reach /quickstart than visitors landing on /docs.",
  "metric": "comparison_quickstart_ctr_ratio",
  "metric_query": "sql:vertex_audit_log_referrer_funnel",
  "threshold": 2.0,
  "baseline": 1.0,
  "deadline_iso": "$DEADLINE",
  "min_sample": 100
}
JSON
)" | python3 -m json.tool

echo
echo "▸ Hypothesis H3 — HTML welcome email lifts day-7 activation"
POST /_bmc/hypotheses "$(cat <<JSON
{
  "slug": "H3-html-welcome-day7-activation",
  "block": "customerRelationships",
  "statement": "Tenants receiving the new HTML welcomeEmail (P45) make ≥1.5x more api_request calls in days 1-7 than the plain-text baseline.",
  "metric": "day7_api_request_avg",
  "metric_query": "sql:vertex_billing_event_metric_sum",
  "threshold": 150,
  "baseline": 100,
  "deadline_iso": "$DEADLINE",
  "min_sample": 20
}
JSON
)" | python3 -m json.tool

echo
echo "▸ Hypothesis H4 — \$13 Starter undercuts beats free→paid conversion"
POST /_bmc/hypotheses "$(cat <<JSON
{
  "slug": "H4-starter-13-conversion",
  "block": "revenueStreams",
  "statement": "≥5% of free-tier tenants convert to a paid Stripe subscription within 30 days of signup.",
  "metric": "free_to_paid_30d_rate",
  "metric_query": "external:stripe_subscriptions",
  "threshold": 0.05,
  "baseline": 0.0,
  "deadline_iso": "$DEADLINE",
  "min_sample": 50
}
JSON
)" | python3 -m json.tool

echo
echo "▸ Hypothesis H5 — Anonymous signup outperforms email-required"
POST /_bmc/hypotheses "$(cat <<JSON
{
  "slug": "H5-anonymous-signup-velocity",
  "block": "customerSegments",
  "statement": "Tenants who omit email at signup reach their first paid plan ≥2x faster than tenants who provide email at signup.",
  "metric": "median_signup_to_paid_days",
  "metric_query": "sql:vertex_signup_cohort_funnel",
  "threshold": 0.5,
  "baseline": 1.0,
  "deadline_iso": "$DEADLINE",
  "min_sample": 30
}
JSON
)" | python3 -m json.tool

echo
echo "✓ Seed complete. Verify in Studio → BMC (admin) pane."
echo "  Next: operator clicks 'activate' on H1 to enter active state, then"
echo "  the LangGraph bmc_iteration cron (0 7 * * *) starts measuring."
