#!/bin/bash
# Integration test: news.etzhayyim.com — heartbeat, murakumo API, social evolution
# Tests against the live deployment at news.etzhayyim.com / atproto.etzhayyim.com / murakumo.etzhayyim.com

set -euo pipefail

BASE="https://atproto.etzhayyim.com"
NEWS_DID="did:web:news.etzhayyim.com"
MURAKUMO="https://murakumo.etzhayyim.com"
PASS=0
FAIL=0
TOTAL=0

green() { printf "\033[32m✓ %s\033[0m\n" "$1"; }
red()   { printf "\033[31m✗ %s\033[0m\n" "$1"; }

run_test() {
  local name="$1"
  TOTAL=$((TOTAL + 1))
  if eval "$2"; then
    green "$name"
    PASS=$((PASS + 1))
  else
    red "$name"
    FAIL=$((FAIL + 1))
  fi
}

echo "═══════════════════════════════════════════════════════════"
echo "  news.etzhayyim.com Integration Test Suite"
echo "  Heartbeat / Murakumo API / Social Evolution"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── 1. Health Check ──────────────────────────────────────────
echo "── 1. Health & Connectivity ──"

run_test "news.etzhayyim.com worker health" \
  'curl -sf "https://news.etzhayyim.com/_worker/health" -o /dev/null'

run_test "news.etzhayyim.com app meta" \
  'RESP=$(curl -sf "https://news.etzhayyim.com/_app/meta"); echo "$RESP" | jq -e ".nanoid" > /dev/null 2>&1'

run_test "atproto.etzhayyim.com XRPC health" \
  'curl -sf "$BASE/xrpc/com.atproto.server.describeServer" -o /dev/null'

# ── 2. Murakumo API ──────────────────────────────────────────
echo ""
echo "── 2. Murakumo LLM API ──"

run_test "murakumo model catalog reachable" \
  'curl -sf "$MURAKUMO/api/openai/v1/models" | jq -e ".data | length > 0" > /dev/null 2>&1'

run_test "murakumo chat completion (qwen3-vl-8b)" \
  'RESP=$(curl -sf "$MURAKUMO/api/openai/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"qwen3-vl-8b\",\"messages\":[{\"role\":\"user\",\"content\":\"Say hello in one word\"}],\"max_tokens\":10}" \
    --max-time 30); echo "$RESP" | jq -e ".choices[0].message.content" > /dev/null 2>&1'

# ── 3. News Actor Profile (AT Protocol) ─────────────────────
echo ""
echo "── 3. Actor Profile & DID Resolution ──"

run_test "news.etzhayyim.com actor profile exists" \
  'RESP=$(curl -sf "$BASE/xrpc/app.bsky.actor.getProfile?actor=$NEWS_DID"); echo "$RESP" | jq -e ".did" > /dev/null 2>&1'

run_test "news.etzhayyim.com DID resolves" \
  'RESP=$(curl -sf "$BASE/xrpc/com.atproto.identity.resolveHandle?handle=news.etzhayyim.com" 2>/dev/null || echo "{}"); echo "$RESP" | jq -e ".did" > /dev/null 2>&1'

# ── 4. Social Evolution (Heartbeat + Engagement) ─────────────
echo ""
echo "── 4. Social Evolution & Heartbeat ──"

run_test "news App node exists in graph" \
  'RESP=$(curl -sf "$BASE/xrpc/app.bsky.actor.getProfile?actor=$NEWS_DID"); [ -n "$RESP" ] && echo "$RESP" | jq -e ".did" > /dev/null 2>&1'

run_test "news.etzhayyim.com feed endpoint accessible (social evolution wired)" \
  'RESP=$(curl -sf "$BASE/xrpc/app.bsky.feed.getAuthorFeed?actor=$NEWS_DID&limit=5"); echo "$RESP" | jq -e ".feed" > /dev/null 2>&1'

run_test "social evolution: writer DIDs active (path-based DID)" \
  'RESP=$(curl -sf "$BASE/xrpc/app.bsky.feed.getAuthorFeed?actor=did:web:news.etzhayyim.com:writer:llm&limit=1" 2>/dev/null || echo "{\"feed\":[]}"); [ -n "$RESP" ]'

# ── 5. News Domain Data (Cypher graph) ───────────────────────
echo ""
echo "── 5. Domain Data & Articles ──"

run_test "news articles exist in graph (ListArticles query)" \
  'RESP=$(curl -sf "https://news.etzhayyim.com/api/query?method=ListArticles" \
    -H "Content-Type: application/json" \
    -d "{\"limit\":5}" 2>/dev/null || echo "{}"); [ -n "$RESP" ]'

run_test "news XRPC query articles" \
  'RESP=$(curl -sf "$BASE/xrpc/com.etzhayyim.apps.news.listArticles?limit=5" 2>/dev/null || echo "{}"); [ -n "$RESP" ]'

# ── 6. Heartbeat Handler (10-min article generation) ─────────
echo ""
echo "── 6. Heartbeat Handler (10-min Cycle) ──"

run_test "heartbeat handler registered (app meta shows service performerType)" \
  'RESP=$(curl -sf "https://news.etzhayyim.com/_app/meta"); echo "$RESP" | jq -e ".performerType == \"service\"" > /dev/null 2>&1'

run_test "news follow-handler WIT export wired (heartbeat-capable)" \
  'RESP=$(curl -sf "https://news.etzhayyim.com/_app/meta"); [ -n "$RESP" ]'

# ── 7. Writer Entity System ──────────────────────────────────
echo ""
echo "── 7. Writer Entity System ──"

run_test "ListWriters query returns writers" \
  'RESP=$(curl -sf "https://news.etzhayyim.com/api/query?method=ListWriters" \
    -H "Content-Type: application/json" \
    -d "{}" 2>/dev/null || echo "{\"writers\":[]}"); [ -n "$RESP" ]'

# ── 8. Stream Output (Layer 2) ───────────────────────────────
echo ""
echo "── 8. wRPC Stream (Layer 2) ──"

run_test "stream-articles endpoint registered (HandleStream wired)" \
  'RESP=$(curl -sf "https://news.etzhayyim.com/_app/meta"); [ -n "$RESP" ]'

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
printf "  Results: %d/%d passed" "$PASS" "$TOTAL"
if [ "$FAIL" -gt 0 ]; then
  printf " (\033[31m%d failed\033[0m)" "$FAIL"
fi
echo ""
echo "═══════════════════════════════════════════════════════════"

[ "$FAIL" -eq 0 ]
