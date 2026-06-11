#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   BASE_URL="https://omise.etzhayyim.com" ORDER_ID="order-..." ./scripts/omise-did-flow.sh
# Optional:
#   AUTH_HEADER="Authorization: Bearer <token>"
#   WAREHOUSE_DID / LOGISTICS_DID / INVENTORY_DID / DISTRIBUTION_DID

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2
  exit 1
fi

BASE_URL="${BASE_URL:-https://omise.etzhayyim.com}"
ORDER_ID="${ORDER_ID:-}"
AUTH_HEADER="${AUTH_HEADER:-}"

if [[ -z "${ORDER_ID}" ]]; then
  echo "ORDER_ID is required" >&2
  exit 1
fi

WAREHOUSE_DID="${WAREHOUSE_DID:-did:web:warehouse.etzhayyim.com:tokyo}"
LOGISTICS_DID="${LOGISTICS_DID:-did:web:logistics.etzhayyim.com:primary}"
INVENTORY_DID="${INVENTORY_DID:-did:web:inventory.etzhayyim.com:central}"
DISTRIBUTION_DID="${DISTRIBUTION_DID:-did:web:distribution.etzhayyim.com:east}"

POST_CMD=(
  curl -sS -X POST
  -H "Content-Type: application/json"
)
if [[ -n "${AUTH_HEADER}" ]]; then
  POST_CMD+=(-H "${AUTH_HEADER}")
fi

post_json() {
  local endpoint="$1"
  local payload="$2"
  "${POST_CMD[@]}" "${BASE_URL}${endpoint}" -d "${payload}"
}

register_actor() {
  local role="$1"
  local did="$2"
  post_json "/xrpc/etzhayyim.omise.v1.OmiseCommandService/actor_register_did" "$(jq -nc \
    --arg role "${role}" \
    --arg did "${did}" \
    '{role:$role, actor_did:$did, display_name:($role + " actor"), capabilities_json:"[\"shipment.update\"]", vc_json:"{\"type\":\"VerifiableCredential\"}"}'
  )" | jq -c .
}

echo "[1/6] Register Actor DIDs"
register_actor warehouse "${WAREHOUSE_DID}"
register_actor logistics "${LOGISTICS_DID}"
register_actor inventory "${INVENTORY_DID}"
register_actor distribution "${DISTRIBUTION_DID}"

echo "[2/6] Create Shipment"
SHIPMENT_JSON="$(post_json "/xrpc/etzhayyim.omise.v1.OmiseCommandService/shipment_create" "$(jq -nc \
  --arg order_id "${ORDER_ID}" \
  --arg warehouse_did "${WAREHOUSE_DID}" \
  --arg logistics_did "${LOGISTICS_DID}" \
  --arg inventory_did "${INVENTORY_DID}" \
  --arg distribution_did "${DISTRIBUTION_DID}" \
  --arg signature "sig:bootstrap" \
  '{order_id:$order_id, carrier:"yamato", tracking_number:("TRK-" + ($order_id|gsub("[^A-Za-z0-9]";""))[0:16]), warehouse_did:$warehouse_did, logistics_did:$logistics_did, inventory_did:$inventory_did, distribution_did:$distribution_did, signature:$signature}'
)")"
echo "${SHIPMENT_JSON}" | jq -c .
SHIPMENT_ID="$(echo "${SHIPMENT_JSON}" | jq -r '.shipment_id')"

if [[ -z "${SHIPMENT_ID}" || "${SHIPMENT_ID}" == "null" ]]; then
  echo "shipment_create did not return shipment_id" >&2
  exit 1
fi

echo "[3/6] Update Shipment -> in_transit"
post_json "/xrpc/etzhayyim.omise.v1.OmiseCommandService/shipment_update_status" "$(jq -nc \
  --arg shipment_id "${SHIPMENT_ID}" \
  --arg actor_did "${LOGISTICS_DID}" \
  '{shipment_id:$shipment_id, status:"in_transit", location:"Tokyo DC", note:"departed", actor_role:"logistics", actor_did:$actor_did, signature:"sig:in-transit"}'
)" | jq -c .

echo "[4/6] Update Shipment -> delivered"
post_json "/xrpc/etzhayyim.omise.v1.OmiseCommandService/shipment_update_status" "$(jq -nc \
  --arg shipment_id "${SHIPMENT_ID}" \
  --arg actor_did "${LOGISTICS_DID}" \
  '{shipment_id:$shipment_id, status:"delivered", location:"Customer", note:"handover completed", actor_role:"logistics", actor_did:$actor_did, signature:"sig:delivered"}'
)" | jq -c .

echo "[5/6] Fetch Order Event Trace"
post_json "/xrpc/etzhayyim.omise.v1.OmiseQueryService/order_event_list" "$(jq -nc --arg order_id "${ORDER_ID}" '{order_id:$order_id, limit:50}')" | jq .

echo "[6/6] Done (shipment_id=${SHIPMENT_ID})"
