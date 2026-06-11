#!/usr/bin/env bash
# yadoya end-to-end smoke test — exercises all 5 NSIDs against
# atproto.etzhayyim.com (PDS pipethrough → yadoya Worker).
#
# Usage:
#   ./yadoya-smoke.sh                     # default endpoint
#   YADOYA_HOST=http://localhost:8787 ./yadoya-smoke.sh
#   YADOYA_BEARER=<jwt> ./yadoya-smoke.sh # exercise create/cancel paths
#
# Exit 0 = all gates passed, exit 1 = any gate failed.
set -u
HOST="${YADOYA_HOST:-https://atproto.etzhayyim.com}"
BEARER="${YADOYA_BEARER:-}"

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
  local args=(-s -o /tmp/yadoya-smoke.body -w '%{http_code}' -X "$method" -H 'accept: application/json')
  [ -n "$BEARER" ] && args+=(-H "authorization: Bearer $BEARER")
  if [ "$method" = "POST" ]; then
    args+=(-H 'content-type: application/json' --data "$body")
  fi
  curl "${args[@]}" "$url" 2>/dev/null
}

echo "==> yadoya smoke @ $HOST"

# 1. listHotels — public, no params required
code=$(call GET com.etzhayyim.apps.yadoya.listHotels 'limit=5')
assert "listHotels limit=5" "$code" "$(cat /tmp/yadoya-smoke.body)" "200"

# 2. searchHotels — public, region filter
code=$(call GET com.etzhayyim.apps.yadoya.searchHotels 'region=asia&limit=5')
assert "searchHotels region=asia" "$code" "$(cat /tmp/yadoya-smoke.body)" "200"

# 3. getReservation — should 200 with NotFound payload for synthetic id
code=$(call GET com.etzhayyim.apps.yadoya.getReservation 'reservationId=does-not-exist-xx')
# Worker returns the NotFound shape inside a 200; that's the contract.
assert "getReservation NotFound payload" "$code" "$(cat /tmp/yadoya-smoke.body)" "200"

# 4. createReservation — only attempted if a bearer is supplied (writes
# are owner-scoped and require Service Auth JWT per ADR-0023)
if [ -n "$BEARER" ]; then
  HOTEL_ID=$(grep -o '"vertex_id":"[^"]*"' /tmp/yadoya-smoke.body 2>/dev/null | head -1 | cut -d'"' -f4)
  if [ -z "$HOTEL_ID" ]; then
    # repeat listHotels to capture a hotel id for the create call
    call GET com.etzhayyim.apps.yadoya.listHotels 'limit=1' >/dev/null
    HOTEL_ID=$(grep -o '"vertex_id":"[^"]*"' /tmp/yadoya-smoke.body | head -1 | cut -d'"' -f4)
  fi
  if [ -n "$HOTEL_ID" ]; then
    body=$(printf '{"hotelId":"%s","checkin":"2026-12-01","checkout":"2026-12-03","guests":2,"channel":"ai-agent"}' "$HOTEL_ID")
    code=$(call POST com.etzhayyim.apps.yadoya.createReservation '' "$body")
    assert "createReservation pending" "$code" "$(cat /tmp/yadoya-smoke.body)" "200"
    RES_ID=$(grep -o '"reservationId":"[^"]*"' /tmp/yadoya-smoke.body | head -1 | cut -d'"' -f4)
    if [ -n "$RES_ID" ]; then
      confirm_body=$(printf '{"reservationId":"%s","amountJpy":45000,"currency":"JPY"}' "$RES_ID")
      code=$(call POST com.etzhayyim.apps.yadoya.confirmReservation '' "$confirm_body")
      assert "confirmReservation + flow emit" "$code" "$(cat /tmp/yadoya-smoke.body)" "200"

      cancel_body=$(printf '{"reservationId":"%s","reason":"smoke-test"}' "$RES_ID")
      code=$(call POST com.etzhayyim.apps.yadoya.cancelReservation '' "$cancel_body")
      assert "cancelReservation cancelled" "$code" "$(cat /tmp/yadoya-smoke.body)" "200"
    fi
  else
    results+=("skip  no hotel id available — backfill migration not applied?")
  fi
else
  results+=("skip  createReservation/cancelReservation — set YADOYA_BEARER to exercise")
fi

echo
for r in "${results[@]}"; do echo "  $r"; done
echo
echo "==> $pass passed, $fail failed"
exit "$fail"
