#!/usr/bin/env bash
# RisingWave IP-restrict — defense against leaked credentials.
#
# Per the 2026-05-17 GitGuardian incident (RisingWave PostgreSQL DSN
# leaked in git history). Even after `git filter-repo` removed the
# password from etzhayyim/root history, vendor history retains it and
# any forks/clones made before the rewrite still have it. The only
# durable defense is **network-level access restriction**.
#
# This script installs a Vultr firewall group on the VKE LB / instance
# fronting RisingWave (host tracked in deps.toml / 1Password — never
# hardcode the public IP in this repo), allowing only:
#   - K8s pod CIDRs (intra-cluster traffic)
#   - explicitly-allowlisted developer / operator IPs
#   - (optional) Cloudflare Hyperdrive egress ranges
#
# After applying: a leaked password is useless from any other IP.
#
# Prerequisites:
#   - VULTR_API_KEY in macOS Keychain (security find-generic-password -s etzhayyim.vultr -a VULTR_API_KEY -w)
#   - jq, curl
#
# Usage:
#   1. Edit ALLOW_CIDRS below (or pass via env var) to your operator IPs
#   2. Confirm the RisingWave instance ID + port
#   3. Run: ./50-infra/vultr/risingwave-firewall-restrict.sh
#
# Reversal: re-apply this script with an empty ALLOW_CIDRS plus open access.

set -euo pipefail

# ─── Config ────────────────────────────────────────────────────────────────

VULTR_API_KEY="${VULTR_API_KEY:-$(security find-generic-password -s etzhayyim.vultr -a VULTR_API_KEY -w 2>/dev/null || true)}"
if [[ -z "${VULTR_API_KEY}" ]]; then
  echo "ERROR: VULTR_API_KEY not in Keychain (etzhayyim.vultr) and not in env" >&2
  exit 1
fi

# RisingWave network exposure points (from 50-infra/vultr/risingwave/risingwave.yaml)
RW_PORT="${RW_PORT:-4566}"
RW_PORT_FRONTEND="${RW_PORT_FRONTEND:-4566}"
RW_PORT_METADATA="${RW_PORT_METADATA:-5690}"

# Firewall group name — created/updated by this script
FW_GROUP_NAME="${FW_GROUP_NAME:-risingwave-restrict}"
FW_DESCRIPTION="RisingWave VKE access — locked to operator IPs + intra-cluster (post-GitGuardian 2026-05-17)"

# Allow-list of CIDRs that can reach RisingWave port 4566.
# Customize for your environment.
#   - K8s pod CIDR (intra-cluster — needed for any pod that talks to RW)
#   - Vultr VKE LB internal IPs (if RW is fronted by a Vultr LB)
#   - Cloudflare Hyperdrive egress IPs (if using CF Hyperdrive)
#   - Operator developer IPs (you / each developer)
#
# DO NOT include 0.0.0.0/0 — that defeats the purpose.
ALLOW_CIDRS=(
  # K8s VKE pod network (lax cluster) — TODO: confirm from `kubectl cluster-info dump | grep podCIDR`
  # "10.244.0.0/16"

  # Vultr VKE node pool egress NAT (TODO: get from Vultr console: VKE → cluster → Nodes)
  # "<vke-node-egress-ip>/32"

  # Cloudflare Hyperdrive egress (per https://developers.cloudflare.com/hyperdrive/reference/configuration/#network-access)
  # Update from CF docs when configuring Hyperdrive.
  # "172.64.0.0/13"
  # "131.0.72.0/22"
  # "104.16.0.0/13"

  # Developer / operator workstation IPs
  # "<your-public-ip>/32"
)

if [[ "${#ALLOW_CIDRS[@]}" -eq 0 ]]; then
  echo "ERROR: ALLOW_CIDRS is empty. Edit the script (or pass via env) to add allowed CIDRs." >&2
  echo "Hint: \`curl -s https://ifconfig.io\` to get your current public IP" >&2
  exit 2
fi

# ─── Helpers ───────────────────────────────────────────────────────────────

api() {
  local method="$1" path="$2"
  shift 2
  curl -sS -X "${method}" \
    -H "Authorization: Bearer ${VULTR_API_KEY}" \
    -H "Content-Type: application/json" \
    "https://api.vultr.com/v2${path}" \
    "$@"
}

# ─── 1. Find or create firewall group ──────────────────────────────────────

echo "[fw] Looking for existing firewall group '${FW_GROUP_NAME}'..."
existing_id=$(api GET "/firewalls" | jq -r --arg name "${FW_GROUP_NAME}" \
  '.firewall_groups[] | select(.description | contains($name)) | .id' | head -1)

if [[ -n "${existing_id}" && "${existing_id}" != "null" ]]; then
  GROUP_ID="${existing_id}"
  echo "[fw] Found existing group: ${GROUP_ID}"
else
  echo "[fw] Creating new firewall group..."
  GROUP_ID=$(api POST "/firewalls" -d "$(jq -nc --arg desc "${FW_DESCRIPTION}" '{description: $desc}')" | jq -r '.firewall_group.id')
  if [[ -z "${GROUP_ID}" || "${GROUP_ID}" == "null" ]]; then
    echo "ERROR: failed to create firewall group" >&2
    exit 3
  fi
  echo "[fw] Created group: ${GROUP_ID}"
fi

# ─── 2. Replace rules atomically (delete existing, then add fresh) ─────────

echo "[fw] Fetching existing rules..."
existing_rule_ids=$(api GET "/firewalls/${GROUP_ID}/rules" | jq -r '.firewall_rules[].id // empty')

for rid in ${existing_rule_ids}; do
  echo "[fw]   - deleting rule ${rid}"
  api DELETE "/firewalls/${GROUP_ID}/rules/${rid}" >/dev/null
done

echo "[fw] Adding fresh ALLOW rules..."
for cidr in "${ALLOW_CIDRS[@]}"; do
  for port in "${RW_PORT_FRONTEND}" "${RW_PORT_METADATA}"; do
    subnet="${cidr%/*}"
    mask="${cidr#*/}"
    [[ "${cidr}" != */* ]] && mask="32"

    echo "[fw]   + ALLOW ${cidr} → tcp/${port}"
    api POST "/firewalls/${GROUP_ID}/rules" -d "$(jq -nc \
      --arg subnet "${subnet}" \
      --arg mask "${mask}" \
      --arg port "${port}" \
      '{ip_type:"v4", protocol:"tcp", subnet:$subnet, subnet_size:($mask|tonumber), port:$port, source:"", notes:"risingwave allow"}')" >/dev/null
  done
done

# Default deny is implicit on Vultr firewall groups (no rule → drop).

# ─── 3. Attach the group to the RisingWave instance ─────────────────────────

echo ""
echo "[fw] Firewall group ${GROUP_ID} ready with ${#ALLOW_CIDRS[@]} allow rules × 2 ports."
echo ""
echo "Next: attach this group to the RisingWave instance (or VKE LB)."
echo ""
echo "If RisingWave is on a Vultr Compute instance:"
echo "  curl -sS -X PATCH \\"
echo "    -H \"Authorization: Bearer \\\$VULTR_API_KEY\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    \"https://api.vultr.com/v2/instances/<INSTANCE_ID>\" \\"
echo "    -d '{\"firewall_group_id\": \"${GROUP_ID}\"}'"
echo ""
echo "If RisingWave is on Vultr VKE behind a LoadBalancer service:"
echo "  - Edit the Service manifest: spec.loadBalancerSourceRanges: [<CIDR>, ...]"
echo "  - OR attach the firewall group via the Vultr console → Load Balancer → Firewall"
echo ""
echo "Verify post-attach:"
echo "  # From an allowed IP:    psql \"postgresql://root@\${RW_HOST}:4566/dev\" -c 'SELECT 1'  → OK"
echo "  # From a non-allowed IP: same command → connection refused / timeout"
echo "  # (RW_HOST: see 1Password item 'RisingWave root' or deps.toml [infra.risingwave])"
echo ""
echo "[fw] Done."
