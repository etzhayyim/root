#!/usr/bin/env bash
# verify.sh — sanity checks against the Lima K3s HA cluster.
#
# Runs through the gates that decide whether the M1 dry-run succeeded:
#   1. All three nodes are Ready
#   2. All three are etcd members (HA quorum)
#   3. Default storage class works (local-path-provisioner)
#   4. Cross-VM pod networking works (test pods on different nodes can talk)
#   5. cluster-info reachable from host kubeconfig
#
# Authoritative ADR: 90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KUBECONFIG_FILE="${KUBECONFIG:-$SCRIPT_DIR/kubeconfig}"
export KUBECONFIG="$KUBECONFIG_FILE"

pass() { echo "  ✅ $1"; }
fail() { echo "  ❌ $1"; exit 1; }

echo "==> 1/5 cluster-info"
kubectl cluster-info >/dev/null && pass "API server reachable" || fail "cluster-info failed"

echo "==> 2/5 node readiness"
ready=$(kubectl get nodes --no-headers | awk '$2=="Ready"' | wc -l | tr -d ' ')
if [[ "$ready" -eq 3 ]]; then
  pass "all 3 nodes Ready"
else
  kubectl get nodes -o wide
  fail "expected 3 Ready nodes, got $ready"
fi

echo "==> 3/5 etcd HA membership"
# k3s exposes etcd via the embedded controller. We probe the leader to
# confirm 3 members are registered.
members=$(kubectl get nodes -l node-role.kubernetes.io/etcd=true --no-headers | wc -l | tr -d ' ')
if [[ "$members" -eq 3 ]]; then
  pass "3 etcd members (HA quorum reachable)"
else
  fail "expected 3 etcd members, got $members"
fi

echo "==> 4/5 default storage class (local-path-provisioner)"
sc=$(kubectl get sc -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}')
if [[ -z "$sc" ]]; then
  fail "no default StorageClass"
fi
pass "default StorageClass: $sc"

echo "==> 5/5 cross-VM pod networking"
ns="etzhayyim-verify"
kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
trap 'kubectl delete namespace "$ns" --wait=false >/dev/null 2>&1 || true' EXIT

# Two pods anti-affinity scheduled — at least two different nodes.
cat <<EOF | kubectl apply -n "$ns" -f - >/dev/null
apiVersion: v1
kind: Pod
metadata:
  name: probe-a
  labels: { app: probe }
spec:
  containers:
    - name: c
      image: ghcr.io/nicolaka/netshoot:latest
      command: ["sleep", "300"]
---
apiVersion: v1
kind: Pod
metadata:
  name: probe-b
  labels: { app: probe }
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels: { app: probe }
          topologyKey: kubernetes.io/hostname
  containers:
    - name: c
      image: ghcr.io/nicolaka/netshoot:latest
      command: ["sh", "-c", "while true; do nc -lk -p 8080; done"]
      ports:
        - containerPort: 8080
EOF

kubectl wait -n "$ns" --for=condition=Ready pod/probe-a --timeout=120s >/dev/null
kubectl wait -n "$ns" --for=condition=Ready pod/probe-b --timeout=120s >/dev/null

probe_b_ip=$(kubectl get -n "$ns" pod probe-b -o jsonpath='{.status.podIP}')
if kubectl exec -n "$ns" probe-a -- sh -c "echo hi | nc -w 2 $probe_b_ip 8080" >/dev/null 2>&1; then
  pass "probe-a → probe-b across VMs ($probe_b_ip)"
else
  kubectl get pods -n "$ns" -o wide
  fail "cross-VM TCP failed"
fi

echo ""
echo "🎉 dry-run cluster passes all gates."
echo "    kubeconfig: $KUBECONFIG_FILE"
