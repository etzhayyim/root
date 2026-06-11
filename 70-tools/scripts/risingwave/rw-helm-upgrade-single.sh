#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: rw-helm-upgrade-single.sh --dry-run
       rw-helm-upgrade-single.sh --apply

Runs the RisingWave Helm upgrade through the Kubernetes operation lock. Dry-run
is explicit and safe; --apply performs the real release upgrade.

Environment:
  RW_NAMESPACE       default: risingwave
  RW_RELEASE_NAME    default: risingwave
  RW_HELM_CHART      default: risingwavelabs/risingwave
  RW_HELM_VERSION    default: 0.2.49
USAGE
}

mode="${1:-}"
if [[ "$mode" != "--dry-run" && "$mode" != "--apply" ]]; then
  usage
  exit 2
fi

command -v helm >/dev/null 2>&1 || { echo "helm missing" >&2; exit 2; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../../.." && pwd)"
lock_script="${script_dir}/rw-op-lock.sh"
ledger_writer="${script_dir}/rw-ledger-write.mjs"
health_gate="${repo_root}/70-tools/scripts/ingest/rw-health-gate.sh"
values_file="${repo_root}/50-infra/vultr/risingwave/helm/values.yaml"

namespace="${RW_NAMESPACE:-risingwave}"
release_name="${RW_RELEASE_NAME:-risingwave}"
chart="${RW_HELM_CHART:-risingwavelabs/risingwave}"
chart_version="${RW_HELM_VERSION:-0.2.49}"

if [[ "$chart_version" != "0.2.49" && "${RW_ALLOW_RISINGWAVE_CHART_BUMP:-0}" != "1" ]]; then
  echo "[rw-helm-upgrade] refusing chart version ${chart_version}; set RW_ALLOW_RISINGWAVE_CHART_BUMP=1 for an intentional chart bump" >&2
  exit 2
fi

helm_args=(
  upgrade
  --install "$release_name" "$chart"
  --namespace "$namespace"
  --version "$chart_version"
  -f "$values_file"
  --reset-values
  --force-conflicts
  --take-ownership
)

if [[ "$mode" == "--dry-run" ]]; then
  helm_args+=(--dry-run=client)
fi

operation_kind="helm_apply"
if [[ "$mode" == "--dry-run" ]]; then
  operation_kind="helm_dry_run"
fi

RW_OP_ID="${RW_OP_ID:-helm-${release_name}-$$}" \
"${lock_script}" -- bash -c '
  set -euo pipefail
  ledger_writer="$1"
  health_gate="$2"
  operation_kind="$3"
  mode="$4"
  release_name="$5"
  chart="$6"
  chart_version="$7"
  values_file="$8"
  shift 8

  ledger_enabled=0
  database_url="${RW_DSN:-${DATABASE_URL:-}}"
  payload_json="{\"mode\":\"${mode}\",\"chart\":\"${chart}\",\"chart_version\":\"${chart_version}\",\"values_file\":\"${values_file}\"}"

  write_ledger() {
    local status="$1"
    local error_text="${2:-}"
    if [[ "$ledger_enabled" = 1 ]]; then
      DATABASE_URL="$database_url" node "$ledger_writer" \
        --operation-id "${RW_OP_ID}" \
        --operation-kind "$operation_kind" \
        --status "$status" \
        --purpose scaling \
        --lease-holder "${RW_OP_ID}" \
        --helm-release "$release_name" \
        --payload-json "$payload_json" \
        --error-text "$error_text" || {
          echo "[rw-helm-upgrade] ledger write failed for status=${status}; continuing" >&2
          return 0
        }
    fi
  }

  on_exit() {
    local rc=$?
    if [[ "$rc" -ne 0 ]]; then
      write_ledger failed "helm wrapper exited with status ${rc}" || true
    fi
    exit "$rc"
  }
  trap on_exit EXIT

  if [[ -n "$database_url" ]]; then
    ledger_enabled=1
    write_ledger running
  fi

  if [[ -n "${RW_DSN:-}" || -n "${DATABASE_URL:-}" ]]; then
    RW_DSN="${RW_DSN:-$DATABASE_URL}" RW_GATE_PURPOSE=scaling VERBOSE="${VERBOSE:-1}" "$health_gate"
  else
    echo "[rw-helm-upgrade] RW_DSN/DATABASE_URL not set; skipping DB health gate and relying on Kubernetes lock" >&2
  fi
  helm "$@"
  write_ledger succeeded
' bash "$ledger_writer" "$health_gate" "$operation_kind" "$mode" "$release_name" "$chart" "$chart_version" "$values_file" "${helm_args[@]}"
