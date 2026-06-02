#!/usr/bin/env bash
# ameno live smoke test — verify the Phase 1-5f end-to-end XRPC chain.
#
# What it checks (in order):
#   1. POST /xrpc/com.etzhayyim.apps.ameno.saveResult         — Worker → bpmn-dispatcher
#                                                          → ameno-langserver pod
#                                                          → INSERT vertex_ameno_inferenceresult
#   2. GET  /xrpc/com.etzhayyim.apps.ameno.listHistory        — same path, SELECT
#                                                          (asserts row from #1 is back)
#   3. GET  /xrpc/com.etzhayyim.apps.ameno.subscribeBriefs    — SSE stream, must
#                                                          emit `event: ready`
#                                                          (proves NATS path)
#
# Configuration (env vars):
#   AMENO_BASE_URL       — XRPC base (default https://atproto.etzhayyim.com). The PDS
#                          routes via NSID_EXACT_MATCH_TABLE; you may also point
#                          this at the worker (https://ameno.etzhayyim.com) which
#                          forwards via sdk.pds.xrpc().
#   ACTOR_DID            — actorDid persisted on the smoke row + listHistory
#                          filter. Defaults to a deterministic test DID so
#                          re-runs collide on a stable filter.
#   SSE_TIMEOUT_SEC      — seconds to wait for the `ready` SSE event (default 6).
#
# Flags:
#   -v                   — verbose (print raw bodies / headers).
#
# Exit code: 0 on full pass, 1 on any failure.

set -uo pipefail

BASE="${AMENO_BASE_URL:-https://atproto.etzhayyim.com}"
ACTOR_DID="${ACTOR_DID:-did:web:ameno-smoke.etzhayyim.com}"
SSE_TIMEOUT_SEC="${SSE_TIMEOUT_SEC:-6}"
VERBOSE=0
if [[ "${1:-}" == "-v" ]]; then
  VERBOSE=1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Stable but unique probe: timestamp + 6 random hex chars so re-runs are
# distinguishable in listHistory but won't collide.
PROBE_PROMPT="ameno-smoke probe $(date -u +%Y%m%dT%H%M%SZ)"
PROBE_OUTPUT="ack $(od -An -N3 -tx1 /dev/urandom 2>/dev/null | tr -d ' \n')"

pass=0
fail=0
report=()

record() {
  local name="$1" ok="$2" detail="$3"
  if [[ "$ok" == "1" ]]; then
    pass=$((pass+1))
    report+=("PASS  $name")
  else
    fail=$((fail+1))
    report+=("FAIL  $name — $detail")
  fi
}

header() { printf '\n── %s ──\n' "$1"; }
v_dump() { [[ "$VERBOSE" == "1" ]] && cat "$1" || true; }

header "Config"
printf 'base:      %s\n' "$BASE"
printf 'actorDid:  %s\n' "$ACTOR_DID"
printf 'probe:     %s\n' "$PROBE_PROMPT"
printf 'sseWait:   %ss\n' "$SSE_TIMEOUT_SEC"

# ── 1. saveResult ─────────────────────────────────────────────────────────────
header "1. saveResult — POST /xrpc/com.etzhayyim.apps.ameno.saveResult"
cat > "${TMP}/save.json" <<EOF
{
  "modelId": "gemma-4-e2b-it",
  "actorDid": "${ACTOR_DID}",
  "prompt": "${PROBE_PROMPT}",
  "output": "${PROBE_OUTPUT}",
  "promptTokens": 8,
  "outputTokens": 4,
  "elapsedMs": 250,
  "tokensPerSec": 16000,
  "ragContextUsed": false
}
EOF
status=$(curl -sS --max-time 30 -L \
  -X POST "${BASE}/xrpc/com.etzhayyim.apps.ameno.saveResult" \
  -H 'content-type: application/json' \
  --data-binary @"${TMP}/save.json" \
  -o "${TMP}/save.resp" -w '%{http_code}')
body=$(cat "${TMP}/save.resp" 2>/dev/null || echo "")
echo "status=${status} body=${body:0:200}"
v_dump "${TMP}/save.resp"
if [[ "$status" == "200" ]] && echo "$body" | grep -qE '"status"\s*:\s*"(persisted|queued)"'; then
  record "saveResult persisted/queued" 1 ""
else
  record "saveResult persisted/queued" 0 "status=${status} body=${body:0:120}"
fi

# Best-effort capture of the resultId for the listHistory cross-check.
RESULT_ID=$(echo "$body" | sed -n 's/.*"resultId"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)

# ── 2. listHistory ────────────────────────────────────────────────────────────
header "2. listHistory — GET /xrpc/com.etzhayyim.apps.ameno.listHistory"
status=$(curl -sS --max-time 15 -L -G \
  "${BASE}/xrpc/com.etzhayyim.apps.ameno.listHistory" \
  --data-urlencode "actorDid=${ACTOR_DID}" \
  --data-urlencode "limit=20" \
  -H 'accept: application/json' \
  -o "${TMP}/list.json" -w '%{http_code}')
body=$(cat "${TMP}/list.json" 2>/dev/null || echo "")
echo "status=${status} body=${body:0:200}"
v_dump "${TMP}/list.json"
if [[ "$status" != "200" ]]; then
  record "listHistory 200" 0 "status=${status}"
elif ! echo "$body" | grep -q '"items"'; then
  record "listHistory shape" 0 "no items field: ${body:0:120}"
else
  record "listHistory shape" 1 ""
  if echo "$body" | grep -q "${PROBE_PROMPT}"; then
    record "listHistory contains probe" 1 ""
  elif [[ -n "$RESULT_ID" ]] && echo "$body" | grep -q "$RESULT_ID"; then
    record "listHistory contains probe (by resultId)" 1 ""
  else
    record "listHistory contains probe" 0 "row not yet visible (RW MV lag?)"
  fi
fi

# ── 3. subscribeBriefs ────────────────────────────────────────────────────────
header "3. subscribeBriefs — GET /xrpc/com.etzhayyim.apps.ameno.subscribeBriefs (SSE)"
# -N disables curl buffering so we see SSE frames as they arrive.
# --max-time bounds the test even if the server keeps the stream alive.
curl -sS -N --max-time "${SSE_TIMEOUT_SEC}" -L \
  "${BASE}/xrpc/com.etzhayyim.apps.ameno.subscribeBriefs?collection=app.bsky.feed.post&maxEvents=2&idleTimeoutSec=${SSE_TIMEOUT_SEC}" \
  -H 'accept: text/event-stream' \
  > "${TMP}/sse.txt" 2>/dev/null || true
sse_body="$(cat "${TMP}/sse.txt" 2>/dev/null || echo "")"
v_dump "${TMP}/sse.txt"
if echo "$sse_body" | grep -qE '^event:[[:space:]]*ready'; then
  record "subscribeBriefs ready" 1 ""
elif echo "$sse_body" | grep -qE '^event:[[:space:]]*brief'; then
  # Pre-existing brief beat the ready frame somehow — still a healthy stream.
  record "subscribeBriefs ready" 1 "(saw brief before ready)"
elif echo "$sse_body" | grep -qE '^event:[[:space:]]*error'; then
  record "subscribeBriefs ready" 0 "server-reported error: $(echo "$sse_body" | head -2 | tr '\n' ' ')"
elif [[ -z "$sse_body" ]]; then
  record "subscribeBriefs ready" 0 "no SSE body in ${SSE_TIMEOUT_SEC}s — pod / NATS unreachable"
else
  record "subscribeBriefs ready" 0 "no ready event: $(echo "$sse_body" | head -2 | tr '\n' ' ')"
fi

# ── Report ────────────────────────────────────────────────────────────────────
header "Report"
for line in "${report[@]}"; do
  echo "$line"
done
printf '\n%d passed, %d failed\n' "$pass" "$fail"
if [[ "$fail" -gt 0 ]]; then
  exit 1
fi
