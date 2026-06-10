#!/usr/bin/env bash
# Deploy etzhayyim-organism to the local OrbStack cluster.
# Substitutes __REPO_ROOT__ with the actual git root path at deploy time
# so the manifests stay portable across machines.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
CONTEXT="${KUBECTL_CONTEXT:-orbstack}"

echo "REPO_ROOT: ${REPO_ROOT}"
echo "context:   ${CONTEXT}"

kubectl --context "${CONTEXT}" kustomize "$(dirname "$0")" \
  | sed "s|__REPO_ROOT__|${REPO_ROOT}|g" \
  | kubectl --context "${CONTEXT}" apply -f -
