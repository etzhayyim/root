#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: rw-op-lock.sh -- <command> [args...]

Acquire a Kubernetes Lease before running a RisingWave topology or migration
operation. The lease is renewed while the command runs and is released only if
this process still owns it.

Environment:
  RW_NAMESPACE                 default: risingwave
  RW_OP_LEASE_NAME             default: risingwave-operation-lock
  RW_OP_ID                     default: <hostname>-<pid>
  RW_OP_TTL_SECONDS            default: 1800
  RW_OP_RENEW_INTERVAL_SECONDS default: 30
USAGE
}

if [[ "${1:-}" != "--" || "$#" -lt 2 ]]; then
  usage
  exit 2
fi
shift

command -v kubectl >/dev/null 2>&1 || { echo "kubectl missing" >&2; exit 2; }
command -v node >/dev/null 2>&1 || { echo "node missing" >&2; exit 2; }

namespace="${RW_NAMESPACE:-risingwave}"
lease_name="${RW_OP_LEASE_NAME:-risingwave-operation-lock}"
holder="${RW_OP_ID:-$(hostname 2>/dev/null || echo local)-$$}"
ttl="${RW_OP_TTL_SECONDS:-1800}"
renew_interval="${RW_OP_RENEW_INTERVAL_SECONDS:-30}"

now_rfc3339() {
  node -e 'process.stdout.write(new Date().toISOString().replace("Z", "000Z"))'
}

now_epoch() {
  date -u +%s
}

epoch_from_rfc3339() {
  node -e 'const t = Date.parse(process.argv[1]); if (!Number.isFinite(t)) process.exit(1); console.log(Math.floor(t / 1000));' "$1"
}

lease_field() {
  kubectl -n "$namespace" get lease "$lease_name" -o "jsonpath={$1}" 2>/dev/null || true
}

create_lease() {
  local now
  now="$(now_rfc3339)"
  kubectl -n "$namespace" create -f - >/dev/null <<EOF
apiVersion: coordination.k8s.io/v1
kind: Lease
metadata:
  name: ${lease_name}
spec:
  holderIdentity: ${holder}
  leaseDurationSeconds: ${ttl}
  acquireTime: ${now}
  renewTime: ${now}
EOF
}

patch_lease() {
  local now
  now="$(now_rfc3339)"
  kubectl -n "$namespace" patch lease "$lease_name" --type=merge -p \
    "{\"spec\":{\"holderIdentity\":\"${holder}\",\"leaseDurationSeconds\":${ttl},\"renewTime\":\"${now}\"}}" >/dev/null
}

lease_is_stale() {
  local renew_time duration renew_epoch expires_at
  renew_time="$(lease_field '.spec.renewTime')"
  duration="$(lease_field '.spec.leaseDurationSeconds')"
  duration="${duration:-$ttl}"
  if [[ -z "$renew_time" ]]; then
    return 0
  fi
  renew_epoch="$(epoch_from_rfc3339 "$renew_time" 2>/dev/null || echo 0)"
  expires_at=$((renew_epoch + duration))
  [[ "$(now_epoch)" -gt "$expires_at" ]]
}

acquire_lease() {
  local current_holder
  if ! kubectl -n "$namespace" get lease "$lease_name" >/dev/null 2>&1; then
    if create_lease 2>/dev/null; then
      echo "[rw-op-lock] acquired ${namespace}/${lease_name} holder=${holder}" >&2
      return 0
    fi
  fi

  current_holder="$(lease_field '.spec.holderIdentity')"
  if [[ "$current_holder" == "$holder" ]]; then
    patch_lease
    echo "[rw-op-lock] renewed existing ${namespace}/${lease_name} holder=${holder}" >&2
    return 0
  fi

  if lease_is_stale; then
    patch_lease
    echo "[rw-op-lock] took over stale ${namespace}/${lease_name} previous=${current_holder:-unknown} holder=${holder}" >&2
    return 0
  fi

  echo "[rw-op-lock] blocked: ${namespace}/${lease_name} is held by ${current_holder:-unknown}" >&2
  return 1
}

release_lease() {
  local current_holder
  current_holder="$(lease_field '.spec.holderIdentity')"
  if [[ "$current_holder" == "$holder" ]]; then
    kubectl -n "$namespace" delete lease "$lease_name" >/dev/null 2>&1 || true
    echo "[rw-op-lock] released ${namespace}/${lease_name} holder=${holder}" >&2
  fi
}

renew_loop() {
  while true; do
    sleep "$renew_interval"
    patch_lease || exit 1
  done
}

acquire_lease
renew_loop &
renew_pid=$!

cleanup() {
  local status=$?
  kill "$renew_pid" >/dev/null 2>&1 || true
  wait "$renew_pid" >/dev/null 2>&1 || true
  release_lease
  exit "$status"
}
trap cleanup EXIT INT TERM

"$@"
