#!/usr/bin/env bash
# probe-hardware.sh — SSH probe each Murakumo Mac mini and emit hw.* TOML fragments
# for inclusion in 50-infra/etzhayyim-langserver/hosts.toml.
#
# Usage:
#   ./probe-hardware.sh                  # probe all 10 tribes; print TOML fragments
#   ./probe-hardware.sh --emit > hw.toml # write fragments to file
#   ./probe-hardware.sh naphtali simeon  # probe specific tribes
#   ./probe-hardware.sh --apply          # patch hosts.toml in-place (Layer 1 commit)
#
# Per CLAUDE.md: this script is **read-only** on the remote (sysctl + sw_vers only).
# Does NOT load any launchd plist. L2 plist generation is gated on this probe
# committing hw.* fields.

set -euo pipefail

cd "$(dirname "$0")/.."

# Tribes + their LAN IPs (mirror of hosts.toml; keep in sync)
declare -A NODES=(
  [naphtali]="192.168.1.18"
  [simeon]="192.168.1.19"
  [judah]="192.168.1.17"
  [zebulun]="192.168.1.11"
  [levi]="192.168.1.16"
  [joseph]="192.168.1.15"
  [issachar]="192.168.1.12"
  [dan]="192.168.1.13"
  [benjamin]="192.168.1.14"
  [asher]="192.168.1.21"
)

EMIT=false
APPLY=false
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --emit) EMIT=true ;;
    --apply) APPLY=true ;;
    *) TARGETS+=("$arg") ;;
  esac
done

if [ ${#TARGETS[@]} -eq 0 ]; then
  TARGETS=(naphtali simeon judah zebulun levi joseph issachar dan benjamin asher)
fi

probe_one() {
  local name="$1"
  local ip="${NODES[$name]}"
  local out
  # All commands are read-only and standard macOS sysctl/sw_vers.
  out=$(ssh -o ConnectTimeout=5 -o BatchMode=yes "${name}@${ip}" \
    'echo "soc=$(sysctl -n machdep.cpu.brand_string)"; \
     echo "ram_bytes=$(sysctl -n hw.memsize)"; \
     echo "arch=$(uname -m)"; \
     echo "macos=$(sw_vers -productVersion)"; \
     echo "build=$(sw_vers -buildVersion)"' \
    2>/dev/null) || {
    echo "# [$name] unreachable (${ip})" >&2
    return 1
  }

  local soc ram_bytes arch macos build ram_gb
  # shellcheck disable=SC2086
  eval "$out"
  ram_gb=$(awk "BEGIN { printf \"%.0f\", ${ram_bytes}/1073741824 }")

  cat <<EOF
# Probe result for ${name} (${ip}) — ${macos} (${build})
[[hw_probe]]
name = "${name}"
soc = "${soc}"
ram_gb = ${ram_gb}
arch = "${arch}"
macos_version = "${macos}"
macos_build = "${build}"
probed_at = "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EOF
}

if [ "$APPLY" = true ]; then
  echo "ERROR: --apply is reserved for a follow-up PR. This dry-run only emits TOML to stdout." >&2
  echo "Run without --apply, review output, then commit hosts.toml updates manually." >&2
  exit 2
fi

for name in "${TARGETS[@]}"; do
  probe_one "$name" || true
  echo ""
done
