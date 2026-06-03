#!/usr/bin/env bash
# deploy-mesh.sh — Deploy murakumo-mesh to Mac Mini nodes and establish mesh network
#
# Usage:
#   ./deploy-mesh.sh                    # Deploy + mesh setup (dan, simeon, joseph)
#   ./deploy-mesh.sh dan simeon         # Deploy to specific nodes
#   ./deploy-mesh.sh --status           # Show mesh status only

set -euo pipefail

cd "$(dirname "$0")"

# Resolve cargo target directory (may be overridden in .cargo/config.toml)
CARGO_TARGET=$(cargo metadata --format-version 1 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('target_directory','target'))" 2>/dev/null || echo "target")
BINARY="${CARGO_TARGET}/release/etzhayyim-murakumo"
MESH_IDENTITY_DIR="$HOME/.etzhayyim/mesh"
CONTROL_PLANE="https://murakumo.etzhayyim.com"

# Default mesh nodes
declare -A NODES=(
  [dan]="192.168.1.58"
  [simeon]="192.168.1.59"
  [joseph]="192.168.1.48"
)

declare -A USERS=(
  [dan]="dan"
  [simeon]="simeon"
  [joseph]="joseph"
)

# Parse args
STATUS_ONLY=false
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --status) STATUS_ONLY=true ;;
    *) TARGETS+=("$arg") ;;
  esac
done

if [ ${#TARGETS[@]} -eq 0 ]; then
  TARGETS=("dan" "simeon" "joseph")
fi

ssh_cmd() {
  local name="$1"
  shift
  local ip="${NODES[$name]}"
  local user="${USERS[$name]}"
  ssh -o ConnectTimeout=5 -o BatchMode=yes "${user}@${ip}" "$@"
}

scp_cmd() {
  local name="$1"
  local src="$2"
  local dst="$3"
  local ip="${NODES[$name]}"
  local user="${USERS[$name]}"
  scp -o ConnectTimeout=5 -q "$src" "${user}@${ip}:${dst}"
}

# ── Status only ──
if [ "$STATUS_ONLY" = true ]; then
  echo "=== Murakumo Mesh Status ==="
  for name in "${TARGETS[@]}"; do
    echo ""
    echo "[$name] (${NODES[$name]})"
    ssh_cmd "$name" "/usr/local/bin/etzhayyim-murakumo murakumo-mesh status 2>&1 || echo 'mesh not configured'" 2>/dev/null || echo "  unreachable"
  done
  exit 0
fi

# ── Verify binary ──
if [ ! -f "$BINARY" ]; then
  echo "ERROR: $BINARY not found. Run: cargo build --release"
  exit 1
fi

echo "=== Deploying murakumo-mesh to ${#TARGETS[@]} nodes ==="
echo ""

# ── Step 1: Generate mesh identities locally ──
mkdir -p "$MESH_IDENTITY_DIR"

for name in "${TARGETS[@]}"; do
  IDENTITY_FILE="$MESH_IDENTITY_DIR/${name}.json"
  if [ ! -f "$IDENTITY_FILE" ]; then
    echo "[$name] generating mesh identity..."
    "$BINARY" murakumo-mesh keygen --node-id "$name" > "$IDENTITY_FILE"
  else
    echo "[$name] identity exists: $IDENTITY_FILE"
  fi
done

echo ""

# ── Step 2: Deploy binary to each node ──
deploy_node() {
  local name="$1"
  echo "[$name] deploying binary to ${NODES[$name]}..."

  scp_cmd "$name" "$BINARY" "/tmp/etzhayyim-murakumo-new"
  ssh_cmd "$name" "sudo mv /tmp/etzhayyim-murakumo-new /usr/local/bin/etzhayyim-murakumo && sudo chmod +x /usr/local/bin/etzhayyim-murakumo"
  echo "[$name]   binary updated"

  # Deploy mesh identity
  local identity_file="$MESH_IDENTITY_DIR/${name}.json"
  ssh_cmd "$name" "mkdir -p ~/.etzhayyim/mesh"
  local remote_home
  remote_home=$(ssh_cmd "$name" "echo \$HOME")
  scp_cmd "$name" "$identity_file" "${remote_home}/.etzhayyim/mesh/identity.json"
  echo "[$name]   identity deployed"

  # Verify
  local version
  version=$(ssh_cmd "$name" "/usr/local/bin/etzhayyim-murakumo version 2>&1" 2>/dev/null || echo "unknown")
  echo "[$name]   version: $version"
}

for name in "${TARGETS[@]}"; do
  deploy_node "$name"
  echo ""
done

# ── Step 3: Install mesh launchd service on each node ──
install_mesh_service() {
  local name="$1"
  local identity_file="\$HOME/.etzhayyim/mesh/identity.json"

  echo "[$name] installing mesh daemon..."

  # Extract identity fields
  local node_id secret_key
  node_id=$(jq -r '.node_id' "$MESH_IDENTITY_DIR/${name}.json")
  secret_key=$(jq -r '.secret_key' "$MESH_IDENTITY_DIR/${name}.json")

  # Create mesh launcher script locally, then scp
  local tmp_script="/tmp/mesh-run-${name}.sh"
  cat > "$tmp_script" << EOF
#!/usr/bin/env bash
exec /usr/local/bin/etzhayyim-murakumo murakumo-mesh tunnel \\
  --node-id ${node_id} \\
  --secret-key ${secret_key} \\
  --control-plane ${CONTROL_PLANE} \\
  2>&1
EOF
  chmod +x "$tmp_script"

  local home_dir
  home_dir=$(ssh_cmd "$name" 'echo $HOME')
  scp_cmd "$name" "$tmp_script" "${home_dir}/.etzhayyim/mesh/run-mesh.sh"
  ssh_cmd "$name" "chmod +x ~/.etzhayyim/mesh/run-mesh.sh"
  rm -f "$tmp_script"

  # Create launchd plist locally, then scp
  local tmp_plist="/tmp/mesh-plist-${name}.plist"
  cat > "$tmp_plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.etzhayyim.murakumo-mesh</string>
    <key>ProgramArguments</key>
    <array>
        <string>${home_dir}/.etzhayyim/mesh/run-mesh.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>10</integer>
    <key>StandardOutPath</key>
    <string>${home_dir}/.etzhayyim/mesh.log</string>
    <key>StandardErrorPath</key>
    <string>${home_dir}/.etzhayyim/mesh.log</string>
</dict>
</plist>
EOF
  scp_cmd "$name" "$tmp_plist" "${home_dir}/Library/LaunchAgents/com.etzhayyim.murakumo-mesh.plist"
  rm -f "$tmp_plist"

  # Kill existing mesh process and restart via nohup (more reliable than launchd for this)
  ssh_cmd "$name" "pkill -f 'murakumo-mesh tunnel' 2>/dev/null; sleep 1; rm -f ~/.etzhayyim/mesh.log; nohup ~/.etzhayyim/mesh/run-mesh.sh > ~/.etzhayyim/mesh.log 2>&1 &"
  echo "[$name]   mesh daemon started"
}

for name in "${TARGETS[@]}"; do
  install_mesh_service "$name"
  echo ""
done

# ── Step 4: Wait and verify ──
echo "=== Waiting 5s for mesh daemons to start... ==="
sleep 5

echo ""
echo "=== Mesh Status ==="
for name in "${TARGETS[@]}"; do
  echo ""
  echo "[$name] (${NODES[$name]})"

  # Show mesh IP
  local_mesh_ip=$("$BINARY" murakumo-mesh dns "$name" 2>&1 | tail -1)
  echo "  mesh: $local_mesh_ip"

  # Show daemon log tail
  log_tail=$(ssh_cmd "$name" "tail -3 ~/.etzhayyim/mesh.log 2>/dev/null" 2>/dev/null || echo "  no log")
  echo "  log:"
  echo "$log_tail" | sed 's/^/    /'
done

echo ""
echo "=== Mesh Network Summary ==="
echo ""
echo "Nodes:"
for name in "${TARGETS[@]}"; do
  node_id=$(jq -r '.node_id' "$MESH_IDENTITY_DIR/${name}.json")
  mesh_ip=$(jq -r '.mesh_ip' "$MESH_IDENTITY_DIR/${name}.json")
  pubkey=$(jq -r '.public_key' "$MESH_IDENTITY_DIR/${name}.json" | cut -c1-16)
  printf "  %-10s  %-16s  node=%s  pk=%s...\n" "$name" "$mesh_ip" "$node_id" "$pubkey"
done

echo ""
echo "Commands:"
echo "  ./deploy-mesh.sh --status          # Check mesh status"
echo "  ssh dan 'tail -f ~/.etzhayyim/mesh.log' # Watch mesh logs"
echo "  etzhayyim-murakumo murakumo-mesh peers  # List mesh peers"
echo ""
echo "=== Mesh deployment complete ==="
