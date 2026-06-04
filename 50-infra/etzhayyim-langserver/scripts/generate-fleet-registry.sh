#!/usr/bin/env bash
# generate-fleet-registry.sh — emit lsp-fleet.json from hosts.toml + transports.toml
# + mesh.toml.
#
# Output schema:
#   {
#     "generated_at": "<UTC ISO8601>",
#     "entries": [
#       {
#         "lang": "rust",
#         "host": "joseph",
#         "hostname": "josephnomac-mini.local",
#         "ip_lan": "192.168.1.15",
#         "mesh_ip": "10.99.<H>.<L>",         # blake3-derived (computed by helper)
#         "port": 15510,
#         "socket_path": "/tmp/etzhayyim-langserver-<user>/rust.sock",
#         "status": "pinned"  // pinned | deployed | unverified
#       },
#       ...
#     ]
#   }
#
# Consumers: L8 editor configs (nvim/VSCode/zed/helix attach blocks).
#
# Usage:
#   ./generate-fleet-registry.sh                  # writes scripts/lsp-fleet.json
#   ./generate-fleet-registry.sh --stdout         # prints to stdout
#   ./generate-fleet-registry.sh --check          # validate produced JSON

set -euo pipefail
cd "$(dirname "$0")/.."

OUT="scripts/lsp-fleet.json"
STDOUT=false
CHECK=false
for arg in "$@"; do
  case "$arg" in
    --stdout) STDOUT=true ;;
    --check) CHECK=true ;;
    --help|-h) sed -n '2,20p' "$0"; exit 0 ;;
  esac
done

# Generation runs entirely in python3 — no SSH calls. Mesh-IP is computed
# locally from the blake3 hash of node_id (same algorithm as
# murakumo_mesh.rs:allocate_mesh_ip).
JSON=$(python3 <<'PY'
import json, tomllib, hashlib, os, datetime, pathlib

base = pathlib.Path(".")

hosts = tomllib.loads((base / "hosts.toml").read_text())
ports = tomllib.loads((base / "transports.toml").read_text())
mesh  = tomllib.loads((base / "mesh.toml").read_text())

# Build lang → (port, socket_basename) lookup
transport = {t["lang"]: t for t in ports["transport"]}

# Build host → row lookup
nodes = {n["name"]: n for n in hosts["nodes"]}

# Mesh-IP derivation must match Rust impl:
#   blake3(node_id_bytes) → first 2 bytes mapped to 10.99.H.L
#   H = max(b[0], 1); L = clamp(b[1], 1, 254)
def mesh_ip(node_id: str) -> str:
    try:
        import blake3
        h = blake3.blake3(node_id.encode()).digest()
    except ImportError:
        # Fallback: stable-but-not-blake3 hash for pre-deployment preview.
        # Real mesh-IP is resolved at runtime by run-langserver.sh
        # reading ~/.etzhayyim/mesh/identity.json.
        h = hashlib.sha256(node_id.encode()).digest()
    H = max(h[0], 1)
    L = max(min(h[1], 254), 1)
    return f"10.99.{H}.{L}"

placement = hosts.get("lsp_placement", {}).get("proposed", {})
entries = []
for lang, host_name in placement.items():
    if lang == "replica":  # placement carries a 'replica' key that names a host, not a lang
        continue
    if lang not in transport:
        continue
    if host_name not in nodes:
        continue
    n = nodes[host_name]
    t = transport[lang]
    entries.append({
        "lang": lang,
        "host": host_name,
        "hostname": n["hostname"],
        "ip_lan": n["ip_lan"],
        "mesh_ip": mesh_ip(host_name),
        "port": t["port_tcp"],
        "socket_path": f"/tmp/etzhayyim-langserver-{n.get('ssh_user', host_name)}/{t['socket_basename']}",
        "status": "pinned",  # L3-pinned; deployment status flips after L6 health probe
    })

out = {
    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    "mesh_subnet": mesh["manifest"]["mesh_subnet"],
    "mesh_ip_note": "Computed locally; runtime mesh-IP comes from ~/.etzhayyim/mesh/identity.json (or legacy ~/.etzhayyim/mesh/identity.json).",
    "entries": entries,
}
print(json.dumps(out, indent=2))
PY
)

if [ "$CHECK" = true ]; then
  echo "$JSON" | python3 -m json.tool > /dev/null && echo "JSON valid ($(echo "$JSON" | python3 -c 'import json,sys;print(len(json.load(sys.stdin)["entries"]))') entries)"
  exit 0
fi

if [ "$STDOUT" = true ]; then
  echo "$JSON"
else
  echo "$JSON" > "$OUT"
  echo "wrote $OUT ($(echo "$JSON" | python3 -c 'import json,sys;print(len(json.load(sys.stdin)["entries"]))') entries)"
fi
