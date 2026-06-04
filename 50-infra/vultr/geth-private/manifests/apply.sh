#!/usr/bin/env bash
# Idempotent applier for the etzhayyim private-chain Geth on Vultr VKE.
#
#   - creates the namespace
#   - creates ConfigMap geth-private-genesis from manifests/genesis.json
#   - creates Secret geth-private-sealer from .local-secrets/{address,keystore,password}
#   - applies StatefulSet + Service
#
# Re-running is safe: ConfigMap and Secret use --dry-run | apply -f -, so
# updates are honoured but the underlying chaindata PVC is untouched.
#
# Pre-req: kubectl context already pointing at vke-a61d513b-…
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
NS="geth-private"

if [ ! -f "$DIR/.local-secrets/sealer.address" ]; then
  echo "fatal: $DIR/.local-secrets/ missing — run scripts/gen-sealer.mjs first" >&2
  exit 1
fi

echo "==> kubectl context: $(kubectl config current-context)"

kubectl apply -f "$DIR/manifests/00-namespace.yaml"

echo "==> ConfigMap geth-private-genesis"
kubectl -n "$NS" create configmap geth-private-genesis \
  --from-file=genesis.json="$DIR/manifests/genesis.json" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Secret geth-private-sealer"
kubectl -n "$NS" create secret generic geth-private-sealer \
  --from-literal=sealer.address="$(tr -d '\n' < "$DIR/.local-secrets/sealer.address")" \
  --from-file=sealer-keystore.json="$DIR/.local-secrets/sealer-keystore.json" \
  --from-file=sealer.password="$DIR/.local-secrets/sealer.password" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f "$DIR/manifests/10-statefulset.yaml"
kubectl apply -f "$DIR/manifests/20-service.yaml"

echo "==> waiting for pod to be Ready..."
kubectl -n "$NS" rollout status statefulset/geth-private --timeout=300s

echo "==> done. RPC inside cluster: http://geth-private.${NS}.svc.cluster.local:8545"
echo "    Port-forward locally:    kubectl -n ${NS} port-forward svc/geth-private 8545:8545"
