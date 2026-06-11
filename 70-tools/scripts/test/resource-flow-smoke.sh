#!/usr/bin/env bash
# resource-flow.etzhayyim.com smoke test — exercises the 4 NSIDs against
# atproto.etzhayyim.com (PDS pipethrough → resource-flow Worker).
#
# Usage:
#   ./resource-flow-smoke.sh
#   YADOYA_HOST=http://localhost:8787 ./resource-flow-smoke.sh
#   RF_BEARER=<jwt> ./resource-flow-smoke.sh   # exercise projectFlow / registerEmitter
set -u
HOST="${RF_HOST:-https://atproto.etzhayyim.com}"
BEARER="${RF_BEARER:-}"

pass=0
fail=0
results=()

assert() {
  local label="$1"
  local code="$2"
  local body="$3"
  local want="$4"
  if [ "$code" = "$want" ]; then
    pass=$((pass + 1))
    results+=("ok    [$code] $label")
  else
    fail=$((fail + 1))
    results+=("FAIL  [$code, want $want] $label — body: ${body:0:200}")
  fi
}

call() {
  local method="$1"
  local nsid="$2"
  local query="${3:-}"
  local body="${4:-}"
  local url="$HOST/xrpc/$nsid"
  [ -n "$query" ] && url="$url?$query"
  local args=(-s -o /tmp/rf-smoke.body -w '%{http_code}' -X "$method" -H 'accept: application/json')
  [ -n "$BEARER" ] && args+=(-H "authorization: Bearer $BEARER")
  if [ "$method" = "POST" ]; then
    args+=(-H 'content-type: application/json' --data "$body")
  fi
  curl "${args[@]}" "$url" 2>/dev/null
}

echo "==> resource-flow smoke @ $HOST"

# 1. getSankey — currency, hospitality domain, no source filter
code=$(call GET com.etzhayyim.apps.resourceFlow.getSankey 'flowClass=currency&domain=hospitality&limit=20')
assert "getSankey currency hospitality" "$code" "$(cat /tmp/rf-smoke.body)" "200"

# 2. getSankey — service
code=$(call GET com.etzhayyim.apps.resourceFlow.getSankey 'flowClass=service&domain=hospitality&limit=20')
assert "getSankey service hospitality" "$code" "$(cat /tmp/rf-smoke.body)" "200"

# 3. listFlows — currency
code=$(call GET com.etzhayyim.apps.resourceFlow.listFlows 'flowClass=currency&limit=10')
assert "listFlows currency" "$code" "$(cat /tmp/rf-smoke.body)" "200"

# 3b. getActorLabels — bulk facade + ERC725 root resolution (ADR-0074, Phase 12)
code=$(call GET com.etzhayyim.apps.resourceFlow.getActorLabels 'dids=did:web:yadoya.etzhayyim.com&dids=did:web:hospitality.etzhayyim.com:actor:chain:hilton')
assert "getActorLabels yadoya+hilton" "$code" "$(cat /tmp/rf-smoke.body)" "200"

# 3c. listAnomalies — Phase 14'' read (open queue, Phase 16' reviewed filter)
code=$(call GET com.etzhayyim.apps.resourceFlow.listAnomalies 'limit=10&reviewed=open')
assert "listAnomalies reviewed=open" "$code" "$(cat /tmp/rf-smoke.body)" "200"

# 3c2. listAnomalies — closed queue (Phase 16')
code=$(call GET com.etzhayyim.apps.resourceFlow.listAnomalies 'limit=10&reviewed=closed')
assert "listAnomalies reviewed=closed" "$code" "$(cat /tmp/rf-smoke.body)" "200"

# 3c3. listAnomalies — severity filter
code=$(call GET com.etzhayyim.apps.resourceFlow.listAnomalies 'limit=10&reviewed=any&severity=high')
assert "listAnomalies severity=high" "$code" "$(cat /tmp/rf-smoke.body)" "200"

# 3d. reviewAnomaly — Phase 15 review action (bearer-gated; 200 with NotFound payload is the contract)
if [ -n "$BEARER" ]; then
  body='{"anomalyId":"at://did:web:resource-flow.etzhayyim.com/com.etzhayyim.apps.resourceFlow.anomaly/does-not-exist","action":"acknowledge","post":false}'
  code=$(call POST com.etzhayyim.apps.resourceFlow.reviewAnomaly '' "$body")
  assert "reviewAnomaly NotFound payload" "$code" "$(cat /tmp/rf-smoke.body)" "200"
fi

# 4. registerEmitter — write path
if [ -n "$BEARER" ]; then
  body='{"emitterDid":"did:web:yadoya.etzhayyim.com","emitterHandle":"yadoya.etzhayyim.com","emitterDisplayName":"Yadoya","emitterDescription":"Hotel search & reservation","industryCode":"I5510"}'
  code=$(call POST com.etzhayyim.apps.resourceFlow.registerEmitter '' "$body")
  assert "registerEmitter yadoya" "$code" "$(cat /tmp/rf-smoke.body)" "200"

  # 5. projectFlow — synthetic record
  body='{"flowClass":"currency","recordUri":"at://did:web:yadoya.etzhayyim.com/com.etzhayyim.apps.resourceFlow.legalEntityCurrencyFlow/smoke-001","observedAt":"2026-04-28T18:00:00Z","record":{"sourceDid":"did:web:yadoya.etzhayyim.com","counterpartyDid":"did:web:hospitality.etzhayyim.com:actor:chain:hilton","fiscalPeriod":"2026-04","flowType":"revenue","amount":0,"amountBucket":"lt-60k","currency":"JPY","industryCode":"I5510","sourceUrl":"https://yadoya.etzhayyim.com/about","sourceLicense":"etzhayyim-internal-aggregate-v1"}}'
  code=$(call POST com.etzhayyim.apps.resourceFlow.projectFlow '' "$body")
  assert "projectFlow currency" "$code" "$(cat /tmp/rf-smoke.body)" "200"

  # 6. detectAnomaly — manual invocation (Phase 13). post=false to avoid
  # spamming rf-anomaly during smoke.
  body='{"flowClass":"all","windowDays":30,"thresholdFactor":3.0,"minBaselineSamples":3,"post":false}'
  code=$(call POST com.etzhayyim.apps.resourceFlow.detectAnomaly '' "$body")
  assert "detectAnomaly dry-scan" "$code" "$(cat /tmp/rf-smoke.body)" "200"
else
  results+=("skip  registerEmitter / projectFlow — set RF_BEARER to exercise")
fi

echo
for r in "${results[@]}"; do echo "  $r"; done
echo
echo "==> $pass passed, $fail failed"
exit "$fail"
