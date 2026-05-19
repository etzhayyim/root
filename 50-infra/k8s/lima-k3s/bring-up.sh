#!/usr/bin/env bash
# bring-up.sh — Stand up a 3-node K3s embedded-etcd HA cluster on Lima.
#
# Idempotent: re-running after a partial bring-up resumes from where it
# stopped. To wipe and start over use teardown.sh.
#
# Prereqs (host):
#   - macOS with brew install lima socket_vmnet
#   - brew install kubectl  (or any other client)
#   - About 12 GB RAM free  (3 VMs × 4 GiB)
#   - About 90 GB disk free (3 × 30 GiB qcow2, sparse)
#
# Authoritative ADR: 90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/lima-k3s-server.yaml"
KUBECONFIG_OUT="$SCRIPT_DIR/kubeconfig"
VMS=(k3s-server-01 k3s-server-02 k3s-server-03)

# Use the same secret on every node — k3s requires it for cluster membership.
# Override via env if you want something deterministic.
CLUSTER_TOKEN="${CLUSTER_TOKEN:-etzhayyim-k3s-dryrun-2026}"

# Channel pin: keep the K3s upstream version stable across the fleet.
# Bump after smoke-testing in a follow-up.
INSTALL_K3S_CHANNEL="${INSTALL_K3S_CHANNEL:-v1.31}"

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "❌ missing prereq: $1" >&2; exit 1; }
}

require limactl
require kubectl

# socket_vmnet is the recommended Lima network backend on macOS.
# Without it `networks: lima: shared` falls back to slirp NAT which
# breaks pod-to-pod traffic between Lima VMs.
if [[ "$(uname -s)" == "Darwin" ]]; then
  if [[ ! -x /opt/socket_vmnet/bin/socket_vmnet ]]; then
    echo "⚠️  socket_vmnet not found at /opt/socket_vmnet — Lima VMs cannot reach each other." >&2
    echo "    Install with:  brew install socket_vmnet" >&2
    echo "    Then run:      sudo brew services start socket_vmnet" >&2
    exit 1
  fi
fi

create_vm() {
  local name="$1"
  if limactl list --format json 2>/dev/null | jq -e --arg n "$name" 'select(.name==$n)' >/dev/null; then
    echo "  ✓ $name already exists (skipping create)"
  else
    echo "  → creating $name"
    limactl create --name="$name" --tty=false "$TEMPLATE"
  fi
}

start_vm() {
  local name="$1"
  local status
  status=$(limactl list --format '{{.Status}}' "$name" 2>/dev/null || echo "")
  if [[ "$status" == "Running" ]]; then
    echo "  ✓ $name already running"
  else
    echo "  → starting $name"
    limactl start "$name"
  fi
}

vm_ip() {
  local name="$1"
  limactl shell "$name" -- ip -4 -o addr show scope global \
    | awk '{print $4}' | head -n1 | cut -d/ -f1
}

install_k3s_first() {
  local name="$1"
  local ip
  ip=$(vm_ip "$name")
  if limactl shell "$name" -- systemctl is-active --quiet k3s 2>/dev/null; then
    echo "  ✓ k3s already running on $name ($ip)"
    return
  fi
  echo "  → installing k3s on $name (cluster-init) at $ip"
  limactl shell "$name" -- sudo env \
    INSTALL_K3S_CHANNEL="$INSTALL_K3S_CHANNEL" \
    K3S_TOKEN="$CLUSTER_TOKEN" \
    INSTALL_K3S_EXEC="server --cluster-init --node-name=$name --tls-san=$ip --tls-san=$name.lima --write-kubeconfig-mode=644" \
    /usr/local/bin/k3s-install.sh
  # Wait for the API server to respond.
  for _ in $(seq 1 60); do
    if limactl shell "$name" -- sudo kubectl --kubeconfig=/etc/rancher/k3s/k3s.yaml get nodes >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done
  echo "❌ $name api-server did not become ready" >&2
  exit 1
}

install_k3s_join() {
  local name="$1"
  local first_ip="$2"
  local ip
  ip=$(vm_ip "$name")
  if limactl shell "$name" -- systemctl is-active --quiet k3s 2>/dev/null; then
    echo "  ✓ k3s already running on $name ($ip)"
    return
  fi
  echo "  → installing k3s on $name (join server@$first_ip) at $ip"
  limactl shell "$name" -- sudo env \
    INSTALL_K3S_CHANNEL="$INSTALL_K3S_CHANNEL" \
    K3S_TOKEN="$CLUSTER_TOKEN" \
    INSTALL_K3S_EXEC="server --server=https://$first_ip:6443 --node-name=$name --tls-san=$ip --tls-san=$name.lima --write-kubeconfig-mode=644" \
    /usr/local/bin/k3s-install.sh
}

export_kubeconfig() {
  local name="$1"
  local first_ip="$2"
  echo "  → exporting kubeconfig from $name → $KUBECONFIG_OUT"
  limactl shell "$name" -- sudo cat /etc/rancher/k3s/k3s.yaml > "$KUBECONFIG_OUT"
  # Rewrite server URL to point at the VM IP (kubeconfig defaults to 127.0.0.1).
  sed -i.bak "s#https://127.0.0.1:6443#https://$first_ip:6443#g" "$KUBECONFIG_OUT"
  rm -f "$KUBECONFIG_OUT.bak"
  chmod 600 "$KUBECONFIG_OUT"
}

main() {
  echo "==> 1/4 ensure Lima template + VMs exist"
  for vm in "${VMS[@]}"; do create_vm "$vm"; done

  echo "==> 2/4 start VMs"
  for vm in "${VMS[@]}"; do start_vm "$vm"; done

  echo "==> 3/4 install K3s (etcd HA)"
  install_k3s_first "${VMS[0]}"
  local first_ip
  first_ip=$(vm_ip "${VMS[0]}")
  for vm in "${VMS[@]:1}"; do
    install_k3s_join "$vm" "$first_ip"
  done

  echo "==> 4/4 export kubeconfig"
  export_kubeconfig "${VMS[0]}" "$first_ip"

  cat <<EOF

✅ K3s HA dry-run cluster is up.

   kubeconfig:   $KUBECONFIG_OUT
   API server:   https://$first_ip:6443
   token:        $CLUSTER_TOKEN

Verify:

   KUBECONFIG=$KUBECONFIG_OUT kubectl get nodes -o wide
   bash $SCRIPT_DIR/verify.sh

Teardown:

   bash $SCRIPT_DIR/teardown.sh
EOF
}

main "$@"
