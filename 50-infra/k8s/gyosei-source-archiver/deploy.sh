#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
NAMESPACE="${NAMESPACE:-mitama-udf}"
CRONJOB_NAME="${CRONJOB_NAME:-gyosei-source-archiver}"
SCHEDULE="${SCHEDULE:-17 2 * * *}"

SCRIPT_PATH="${ROOT_DIR}/70-tools/evidence-crawler/capture_gyosei_sources_to_b2.py"
MANIFEST_PATH="${ROOT_DIR}/80-data/gyosei/source-manifest.json"
CRONJOB_TEMPLATE="${ROOT_DIR}/50-infra/k8s/gyosei-source-archiver/cronjob.yaml"

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "${NAMESPACE}" create configmap gyosei-source-archiver-script \
  --from-file=capture_gyosei_sources_to_b2.py="${SCRIPT_PATH}" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "${NAMESPACE}" create configmap gyosei-source-archiver-manifest \
  --from-file=source-manifest.json="${MANIFEST_PATH}" \
  --dry-run=client -o yaml | kubectl apply -f -

sed \
  -e "s|__NAMESPACE__|${NAMESPACE}|g" \
  -e "s|__CRONJOB_NAME__|${CRONJOB_NAME}|g" \
  -e "s|__SCHEDULE__|${SCHEDULE}|g" \
  "${CRONJOB_TEMPLATE}" | kubectl apply -f -

echo "[gyosei-source-archiver] deployed"
echo "  namespace: ${NAMESPACE}"
echo "  cronjob:   ${CRONJOB_NAME}"
echo "  schedule:  ${SCHEDULE} UTC"
