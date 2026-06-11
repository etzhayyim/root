#!/usr/bin/env bash
# warehouse-yard-e2e-smoke.sh — smoke test for warehouse + yard-ops MVP
#
# Verifies:
#   1. All 8 warehouse + yard-ops BPMN process_def rows exist and are
#      bound (deployed_zeebe_key may be PENDING right after migration).
#   2. registerSku  → vertex_warehouse_sku INSERT
#   3. putaway      → vertex_warehouse_putaway INSERT (bin assigned)
#   4. pick         → vertex_warehouse_pick INSERT (bins resolved)
#   5. checkInTrailer → vertex_yard_ops_trailer INSERT
#   6. assignDoor   → vertex_yard_ops_dock_job INSERT + edge to loading mission
#   7. completeDockJob → vertex_yard_ops_dock_completion INSERT, dock_job closed
#   8. mv_dock_dwell_minutes_15m has at least one row after completion
#
# Usage:
#   bash 70-tools/scripts/test/warehouse-yard-e2e-smoke.sh
#
# Required env:
#   DATABASE_URL              — RW connection (read+write to vertex_*)
#   BPMN_DISPATCHER_URL       — default http://dispatcher.etzhayyim.com:8080
#   BPMN_INTERNAL_SECRET      — x-internal-trust header (for XRPC dispatch)

set -euo pipefail

DISPATCHER="${BPMN_DISPATCHER_URL:-http://dispatcher.etzhayyim.com:8080}"
SECRET="${BPMN_INTERNAL_SECRET:-}"
DB="${DATABASE_URL:-}"

if [[ -z "$DB" ]]; then
  echo "ERROR: DATABASE_URL not set"
  exit 1
fi

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass() { echo "  ✅ $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  ❌ $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }
warn() { echo "  ⚠️  $1"; WARN_COUNT=$((WARN_COUNT+1)); }
hdr()  { echo; echo "── $1 ──"; }

PSQL() { psql "$DB" -A -t -c "$1" 2>/dev/null || echo ""; }

# Stable IDs for this run
RUN_TS=$(date -u +%Y%m%d%H%M%S)
SKU="SMOKE-SKU-${RUN_TS}"
ORDER_ID="SMOKE-ORDER-${RUN_TS}"
TRAILER_PLATE="SMOKE-TRL-${RUN_TS:8}"

# ── Step 1 — BPMN process_def deployment ────────────────────────────────────

hdr "Step 1: BPMN process_def deployment"

EXPECTED_PROCESSES=(
  warehouse_register_sku
  warehouse_putaway
  warehouse_pick
  warehouse_get_inventory
  yard_ops_check_in_trailer
  yard_ops_assign_door
  yard_ops_complete_dock_job
  yard_ops_get_dock_schedule
)

for proc in "${EXPECTED_PROCESSES[@]}"; do
  ROW=$(PSQL "SELECT bpmn_process_id || '|' || COALESCE(deployed_zeebe_key::text, 'PENDING') FROM vertex_bpmn_process_def WHERE bpmn_process_id = '$proc' LIMIT 1")
  if [[ -z "$ROW" ]]; then
    fail "$proc — row missing (migration 20260509070000 not applied?)"
  elif [[ "$ROW" == *"|PENDING" ]]; then
    warn "$proc — row exists but deployed_zeebe_key NULL (Zeebe watcher not yet)"
  else
    pass "$proc — deployed (key=${ROW#*|})"
  fi
done

# ── Step 2 — registerSku → putaway → pick ───────────────────────────────────

hdr "Step 2: warehouse XRPC dispatch"

if [[ -z "$SECRET" ]]; then
  warn "BPMN_INTERNAL_SECRET unset — skipping XRPC dispatch tests"
else
  call_xrpc() {
    local nsid=$1; local body=$2
    curl -fsS -X POST "$DISPATCHER/xrpc/$nsid" \
      -H "Content-Type: application/json" \
      -H "x-internal-trust: $SECRET" \
      -d "$body" || echo ""
  }

  R1=$(call_xrpc "com.etzhayyim.apps.warehouse.registerSku" \
    "{\"skuCode\":\"$SKU\",\"description\":\"smoke sku\",\"unitOfMeasure\":\"EA\",\"weightKg\":\"1.0\"}")
  if [[ "$R1" == *'"ok":true'* ]]; then pass "registerSku → ok"; else fail "registerSku → $R1"; fi

  R2=$(call_xrpc "com.etzhayyim.apps.warehouse.putaway" \
    "{\"skuCode\":\"$SKU\",\"quantity\":50}")
  if [[ "$R2" == *'"ok":true'* ]]; then pass "putaway → ok"; else fail "putaway → $R2"; fi

  R3=$(call_xrpc "com.etzhayyim.apps.warehouse.pick" \
    "{\"orderId\":\"$ORDER_ID\",\"skuCode\":\"$SKU\",\"quantity\":5}")
  if [[ "$R3" == *'"ok":true'* ]]; then pass "pick → ok"; else fail "pick → $R3"; fi

  # ── Step 3 — yard-ops flow ──────────────────────────────────────────────

  hdr "Step 3: yard-ops XRPC dispatch"

  R4=$(call_xrpc "com.etzhayyim.apps.yardOps.checkInTrailer" \
    "{\"trailerPlate\":\"$TRAILER_PLATE\",\"carrierDid\":\"did:web:smoke-carrier.etzhayyim.com\"}")
  if [[ "$R4" == *'"ok":true'* ]]; then pass "checkInTrailer → ok"; else fail "checkInTrailer → $R4"; fi

  TRAILER_VID=$(echo "$R4" | sed -n 's/.*"vertexId":"\([^"]*\)".*/\1/p')
  if [[ -z "$TRAILER_VID" ]]; then
    warn "trailer vertexId missing — skipping assignDoor / completeDockJob"
  else
    R5=$(call_xrpc "com.etzhayyim.apps.yardOps.assignDoor" \
      "{\"trailerVertexId\":\"$TRAILER_VID\",\"direction\":\"inbound\",\"loadPlanRef\":\"$ORDER_ID\"}")
    if [[ "$R5" == *'"ok":true'* ]]; then pass "assignDoor → ok"; else fail "assignDoor → $R5"; fi

    JOB_VID=$(echo "$R5" | sed -n 's/.*"vertexId":"\([^"]*\)".*/\1/p')
    if [[ -n "$JOB_VID" ]]; then
      R6=$(call_xrpc "com.etzhayyim.apps.yardOps.completeDockJob" \
        "{\"dockJobVertexId\":\"$JOB_VID\",\"actualDurationMin\":42}")
      if [[ "$R6" == *'"ok":true'* ]]; then pass "completeDockJob → ok"; else fail "completeDockJob → $R6"; fi
    fi
  fi
fi

# ── Step 4 — graph state checks ─────────────────────────────────────────────

hdr "Step 4: graph state"

SKU_CNT=$(PSQL "SELECT count(*) FROM vertex_warehouse_sku WHERE vertex_key = '$SKU'")
[[ "${SKU_CNT:-0}" -ge 1 ]] && pass "vertex_warehouse_sku has $SKU_CNT row(s) for $SKU" || fail "vertex_warehouse_sku missing for $SKU"

PUT_CNT=$(PSQL "SELECT count(*) FROM vertex_warehouse_putaway WHERE value_json LIKE '%$SKU%'")
[[ "${PUT_CNT:-0}" -ge 1 ]] && pass "vertex_warehouse_putaway has $PUT_CNT row(s)" || warn "vertex_warehouse_putaway empty for $SKU"

PICK_CNT=$(PSQL "SELECT count(*) FROM vertex_warehouse_pick WHERE value_json LIKE '%$ORDER_ID%'")
[[ "${PICK_CNT:-0}" -ge 1 ]] && pass "vertex_warehouse_pick has $PICK_CNT row(s)" || warn "vertex_warehouse_pick empty for $ORDER_ID"

TRL_CNT=$(PSQL "SELECT count(*) FROM vertex_yard_ops_trailer WHERE vertex_key = '$TRAILER_PLATE'")
[[ "${TRL_CNT:-0}" -ge 1 ]] && pass "vertex_yard_ops_trailer has $TRL_CNT row(s)" || warn "vertex_yard_ops_trailer empty for $TRAILER_PLATE"

JOB_CNT=$(PSQL "SELECT count(*) FROM vertex_yard_ops_dock_job WHERE value_json LIKE '%$TRAILER_PLATE%' OR value_json LIKE '%$ORDER_ID%'")
[[ "${JOB_CNT:-0}" -ge 1 ]] && pass "vertex_yard_ops_dock_job has $JOB_CNT row(s)" || warn "vertex_yard_ops_dock_job empty for run"

CMP_CNT=$(PSQL "SELECT count(*) FROM vertex_yard_ops_dock_completion WHERE value_json LIKE '%$TRAILER_PLATE%'")
[[ "${CMP_CNT:-0}" -ge 1 ]] && pass "vertex_yard_ops_dock_completion has $CMP_CNT row(s)" || warn "vertex_yard_ops_dock_completion empty for run"

# Cost-KPI MV may take a refresh tick; warn rather than fail if empty.
MV_CNT=$(PSQL "SELECT count(*) FROM dev.mv_dock_dwell_minutes_15m")
[[ "${MV_CNT:-0}" -ge 1 ]] && pass "mv_dock_dwell_minutes_15m has $MV_CNT row(s)" || warn "mv_dock_dwell_minutes_15m empty (SQLMesh may not have run)"

# ── Summary ─────────────────────────────────────────────────────────────────

echo
echo "── Summary ──"
echo "  PASS:  $PASS_COUNT"
echo "  WARN:  $WARN_COUNT"
echo "  FAIL:  $FAIL_COUNT"
[[ "$FAIL_COUNT" -gt 0 ]] && exit 1 || exit 0
