#!/usr/bin/env bash
# teardown.sh — Remove the Lima K3s dry-run cluster.
#
# Stops and deletes all three VMs and the exported kubeconfig.
# Safe to run multiple times.
#
# Authoritative ADR: 90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VMS=(k3s-server-01 k3s-server-02 k3s-server-03)

for vm in "${VMS[@]}"; do
  if limactl list --format '{{.Name}}' 2>/dev/null | grep -qx "$vm"; then
    echo "→ stopping + deleting $vm"
    limactl stop "$vm" --force 2>/dev/null || true
    limactl delete "$vm" --force
  else
    echo "  ✓ $vm not present"
  fi
done

rm -f "$SCRIPT_DIR/kubeconfig"
echo "✅ teardown complete"
