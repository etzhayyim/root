#!/usr/bin/env bash
# domain-coverage-strict-health.sh — strict live MV health check for `gftd coverage domain`.
#
# Required env:
#   GFTD_DATABASE_URL or DATABASE_URL
# Optional env:
#   GFTD_BIN   path to gftd binary (default: ./gftd)
#   PDS_URL    override reconciliation endpoint
#   OUT_JSON   output path for JSON report (default: /tmp/domain-coverage-strict-health.json)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

GFTD_BIN="${GFTD_BIN:-./gftd}"
OUT_JSON="${OUT_JSON:-/tmp/domain-coverage-strict-health.json}"

if [[ -z "${GFTD_DATABASE_URL:-}" && -z "${DATABASE_URL:-}" ]]; then
  echo "::error::GFTD_DATABASE_URL or DATABASE_URL is required" >&2
  exit 1
fi

if [[ ! -x "$GFTD_BIN" ]]; then
  echo "::error::gftd binary not found or not executable: $GFTD_BIN" >&2
  exit 1
fi

ARGS=(coverage domain --format json --strict)
if [[ -n "${PDS_URL:-}" ]]; then
  ARGS+=(--pds "$PDS_URL")
fi

echo "==> strict health check: $GFTD_BIN ${ARGS[*]}"
"$GFTD_BIN" "${ARGS[@]}" > "$OUT_JSON"

echo "==> summary"
jq -r '
  "evaluatedAt: \(.authorityChain.evaluatedAt // .authorityChain.EvaluatedAt // "n/a")",
  "authorityModel: \(.authorityModel.name) [\(.authorityModel.mode)]",
  "liveReadModel: \(.liveReadModel.name) [\(.liveReadModel.mode)]",
  "platformRatePct: \(((.authorityChain.platformRate // 0) * 100) | tostring)",
  "reconciliationRows: \((.reconciliation // []) | length)",
  "reconcileError: \(.reconcileError // "")"
' "$OUT_JSON"

ROWS="$(jq '(.reconciliation // []) | length' "$OUT_JSON")"
if [[ "$ROWS" -le 0 ]]; then
  echo "::error::strict health check produced no reconciliation rows" >&2
  exit 1
fi

echo "==> strict health check passed: $ROWS reconciliation rows"
