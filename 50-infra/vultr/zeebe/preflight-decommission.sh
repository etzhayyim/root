#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ENGINE_NAMESPACE="${ENGINE_NAMESPACE:-mitama-udf}"
ENGINE_SERVICE="${ENGINE_SERVICE:-bpmn-engine-host}"
ENGINE_LOCAL_PORT="${ENGINE_LOCAL_PORT:-18080}"
SPIFF_WORKER_DEPLOY="${SPIFF_WORKER_DEPLOY:-lawfirm-spiff-worker}"

cleanup() {
  if [[ -n "${PF_PID:-}" ]]; then
    kill "${PF_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "== Spiff rollouts =="
kubectl -n "${ENGINE_NAMESPACE}" rollout status "deploy/${ENGINE_SERVICE}" --timeout=120s
kubectl -n "${ENGINE_NAMESPACE}" rollout status "deploy/${SPIFF_WORKER_DEPLOY}" --timeout=120s

echo "== Engine health =="
kubectl -n "${ENGINE_NAMESPACE}" port-forward "svc/${ENGINE_SERVICE}" "${ENGINE_LOCAL_PORT}:80" >/tmp/zeebe-decommission-pf.log 2>&1 &
PF_PID=$!
sleep 2
curl -fsS "http://localhost:${ENGINE_LOCAL_PORT}/healthz"
echo
curl -fsS "http://localhost:${ENGINE_LOCAL_PORT}/readyz"
echo
cleanup
unset PF_PID

echo "== RW health gate =="
"${ROOT_DIR}/70-tools/scripts/ingest/rw-health-gate.sh"

echo "== Legacy Zeebe workloads =="
kubectl get deploy,sts,cronjob -A -o wide | grep -Ei 'zeebe|pyzeebe|ZEEBE' || true

echo "== Legacy Zeebe services =="
kubectl get svc -A -o wide | grep -Ei 'zeebe|26500' || true

echo "== Next =="
echo "Review any listed Zeebe workloads/services before running DECOMMISSION-RUNBOOK.md delete steps."
