#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: rw-run-migration-single.sh <migration_name>

Runs exactly one Kysely migration through the RisingWave operation lock.
The migration name must omit the .ts extension, for example:
  20260430220000_vertex_arms_conflict_falklands

Environment:
  DATABASE_URL or RW_DSN   RisingWave postgres URL
  RW_NAMESPACE             default: risingwave
USAGE
}

if [[ "$#" -ne 1 ]]; then
  usage
  exit 2
fi

migration_name="$1"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../../.." && pwd)"
graph_dir="${repo_root}/30-graph/graph-schema"
lock_script="${script_dir}/rw-op-lock.sh"
ledger_writer="${script_dir}/rw-ledger-write.mjs"
health_gate="${repo_root}/70-tools/scripts/ingest/rw-health-gate.sh"

database_url="${DATABASE_URL:-${RW_DSN:-}}"
if [[ -z "$database_url" ]]; then
  echo "DATABASE_URL or RW_DSN is required" >&2
  exit 2
fi

RW_OP_ID="${RW_OP_ID:-migration-${migration_name}-$$}" \
"${lock_script}" -- bash -c '
  set -euo pipefail
  ledger_writer="$1"
  graph_dir="$2"
  health_gate="$3"
  database_url="$4"
  migration_name="$5"

  payload_json="{\"migration_name\":\"${migration_name}\",\"graph_dir\":\"${graph_dir}\"}"

  write_ledger() {
    local status="$1"
    local error_text="${2:-}"
    DATABASE_URL="$database_url" node "$ledger_writer" \
      --operation-id "${RW_OP_ID}" \
      --operation-kind migration_apply \
      --status "$status" \
      --purpose ddl \
      --lease-holder "${RW_OP_ID}" \
      --migration-name "$migration_name" \
      --payload-json "$payload_json" \
      --error-text "$error_text" || {
        echo "[rw-migration] ledger write failed for status=${status}; continuing" >&2
        return 0
      }
  }

  on_exit() {
    local rc=$?
    if [[ "$rc" -ne 0 ]]; then
      write_ledger failed "migration wrapper exited with status ${rc}" || true
    fi
    exit "$rc"
  }
  trap on_exit EXIT

  write_ledger running

  RW_DSN="$database_url" RW_GATE_PURPOSE=ddl VERBOSE="${VERBOSE:-1}" "$health_gate"
  cd "$graph_dir"
  DATABASE_URL="$database_url" node scripts/apply-single.mjs "$migration_name"
  write_ledger succeeded
' bash "$ledger_writer" "$graph_dir" "$health_gate" "$database_url" "$migration_name"
