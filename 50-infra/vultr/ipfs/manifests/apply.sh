#!/usr/bin/env bash
# Idempotent bring-up for ipfs.etzhayyim.com (ADR-2604261936).
#
# Mirrors 50-infra/vultr/geth-private/manifests/apply.sh. Re-runnable; uses
# server-side apply so ConfigMap / Secret updates propagate cleanly.
#
# Pre-reqs:
#   - kubectl context = Vultr VKE production cluster
#   - macOS Keychain entries:
#       etzhayyim.b2 / ACCESS_KEY_ID
#       etzhayyim.b2 / SECRET_ACCESS_KEY
#       etzhayyim.cloudflare / IPFS_ORIGIN_CERT_PEM   (10-year self-signed leaf for ipfs-origin.etzhayyim.com)
#       etzhayyim.cloudflare / IPFS_ORIGIN_CERT_KEY   (matching private key)
#   - B2 prefix `s3://etzhayyim-nats/ipfs/blocks/` (the existing `etzhayyim-nats`
#     bucket from ADR-0048; the Keychain key is already scoped to it).
#
# Usage:
#   bash 50-infra/vultr/ipfs/manifests/apply.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NS=ipfs

say() { printf "\n\033[1;36m==> %s\033[0m\n" "$*"; }

# 1. Namespace
kubectl apply --server-side -f "$SCRIPT_DIR/00-namespace.yaml"

# 2. B2 credentials Secret (Keychain → kubectl)
say "kubo-b2 secret"
B2_KEY="$(security find-generic-password -s etzhayyim.b2 -a ACCESS_KEY_ID -w)"
B2_SEC="$(security find-generic-password -s etzhayyim.b2 -a SECRET_ACCESS_KEY -w)"
kubectl -n "$NS" create secret generic kubo-b2 \
  --from-literal=accessKey="$B2_KEY" \
  --from-literal=secretKey="$B2_SEC" \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. caddy TLS leaf (10-year self-signed for CF Origin)
say "caddy-ipfs-cert secret"
# `security ... -w` returns hex when the value contains newlines (PEM does).
# Always decode through `xxd -r -p` to recover the raw bytes.
ORIGIN_CRT="$(security find-generic-password -s etzhayyim.cloudflare -a IPFS_ORIGIN_CERT_PEM -w | xxd -r -p)"
ORIGIN_KEY="$(security find-generic-password -s etzhayyim.cloudflare -a IPFS_ORIGIN_CERT_KEY -w | xxd -r -p)"
kubectl -n "$NS" create secret generic caddy-ipfs-cert \
  --from-literal=tls.crt="$ORIGIN_CRT" \
  --from-literal=tls.key="$ORIGIN_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. ConfigMap with the init script + datastore_spec template (mounted r/o)
say "ipfs-init-config configmap"
kubectl -n "$NS" create configmap ipfs-init-config \
  --from-file=init-config.sh="$ROOT/scripts/init-config.sh" \
  --from-file=datastore_spec.json="$ROOT/config/datastore_spec.json" \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. StatefulSet, services, TLS proxy
kubectl apply --server-side -f "$SCRIPT_DIR/10-statefulset.yaml"
kubectl apply --server-side -f "$SCRIPT_DIR/20-service.yaml"
kubectl apply --server-side -f "$SCRIPT_DIR/40-tls-proxy.yaml"

say "wait for kubo to roll out"
kubectl -n "$NS" rollout status statefulset/kubo --timeout=180s

say "smoke read — gateway version"
kubectl -n "$NS" exec statefulset/kubo -- ipfs version || true

say "done"
echo "Next: provision DNS for ipfs-origin.etzhayyim.com → Vultr LB external IP"
echo "      then deploy CF Worker etzhayyim-ipfs-proxy with route ipfs.etzhayyim.com/*"
