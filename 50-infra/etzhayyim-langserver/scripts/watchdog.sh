#!/usr/bin/env bash
# watchdog.sh — one-shot cross-fleet langserver health poll.
#
# Reads lsp-fleet.json (produced by generate-fleet-registry.sh) and probes
# each healthz endpoint. Exits non-zero if any LSP is unhealthy. Intended
# usage:
#   - manual ad-hoc: ./watchdog.sh
#   - L9 cell:       a future LangserverHealthMonitoringCell calls this
#                    on cron and writes results to MST listener
#                    com.etzhayyim.apps.etzhayyim.langserver.health
#
# Output (TSV per row):
#   <lang>  <host>  <mesh_ip>:<healthz_port>  <http_status>  <body_summary>
#
# Usage:
#   ./watchdog.sh                  # poll all
#   ./watchdog.sh --json           # emit JSON aggregate
#   ./watchdog.sh rust python      # poll specific langs only

set -euo pipefail
cd "$(dirname "$0")/.."

REGISTRY="scripts/lsp-fleet.json"
if [ ! -f "$REGISTRY" ]; then
  echo "FATAL: $REGISTRY not found — run scripts/generate-fleet-registry.sh first" >&2
  exit 1
fi

JSON_OUT=false
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --json) JSON_OUT=true ;;
    *) TARGETS+=("$arg") ;;
  esac
done

# Probe one healthz endpoint
probe_one() {
  local lang="$1"
  local host="$2"
  local mesh_ip="$3"
  local lsp_port="$4"

  # healthz port = lsp_port + 100 per transports.toml convention
  local healthz_port=$((lsp_port + 100))
  local url="http://${mesh_ip}:${healthz_port}/healthz"

  # 2 second connect + 3 second total timeout
  local status_and_body
  status_and_body=$(curl -s -o /tmp/healthz-body-$$ -w "%{http_code}" \
    --connect-timeout 2 --max-time 3 "$url" 2>&1) || status_and_body="000"

  local body
  body=$(cat /tmp/healthz-body-$$ 2>/dev/null || echo "")
  rm -f /tmp/healthz-body-$$

  printf "%s\t%s\t%s:%s\t%s\t%s\n" \
    "$lang" "$host" "$mesh_ip" "$healthz_port" "$status_and_body" \
    "$(echo "$body" | head -c 120 | tr '\n' ' ')"
}

# Emit JSON or TSV
if [ "$JSON_OUT" = true ]; then
  python3 - "$REGISTRY" "${TARGETS[@]:-}" <<'PY'
import json, sys, urllib.request, socket, datetime
reg = json.load(open(sys.argv[1]))
targets = set(sys.argv[2:]) if len(sys.argv) > 2 else None
results = []
for e in reg["entries"]:
    if targets and e["lang"] not in targets:
        continue
    healthz_port = e["port"] + 100
    url = f"http://{e['mesh_ip']}:{healthz_port}/healthz"
    row = {"lang": e["lang"], "host": e["host"], "url": url}
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            row["http_status"] = resp.status
            row["body"] = json.loads(resp.read())
    except (urllib.error.URLError, socket.timeout, ConnectionRefusedError, OSError) as exc:
        row["http_status"] = 0
        row["error"] = repr(exc)
    results.append(row)
print(json.dumps({
    "polled_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    "results": results,
    "ok_count": sum(1 for r in results if r.get("http_status") == 200),
    "fail_count": sum(1 for r in results if r.get("http_status") != 200),
}, indent=2))
PY
  exit 0
fi

# TSV mode
printf "%s\t%s\t%s\t%s\t%s\n" "LANG" "HOST" "ENDPOINT" "STATUS" "BODY"
FAILS=0
python3 -c "
import json, sys
reg = json.load(open('$REGISTRY'))
targets = set('${TARGETS[*]:-}'.split()) if '${TARGETS[*]:-}' else None
for e in reg['entries']:
    if targets and e['lang'] not in targets: continue
    print(f\"{e['lang']}\t{e['host']}\t{e['mesh_ip']}\t{e['port']}\")
" | while IFS=$'\t' read -r lang host mesh_ip lsp_port; do
  result=$(probe_one "$lang" "$host" "$mesh_ip" "$lsp_port")
  echo "$result"
  status=$(echo "$result" | awk -F'\t' '{print $4}')
  if [ "$status" != "200" ]; then
    FAILS=$((FAILS + 1))
  fi
done

exit "$FAILS"
