#!/usr/bin/env bash
# ship-logs-to-nats.sh — optional opt-in forwarder of langserver stdout/stderr
# to a NATS JetStream subject.
#
# Default mode is NOOP (dry-run). Pass --apply to actually start tailing
# and publishing. This script is intended to run on each Mac mini that
# is part of the langserver fleet, alongside the LSP daemon — NOT as a
# replacement for launchd's on-disk logging (which remains the primary
# observability sink per obs.toml).
#
# NATS deployment is itself scaffolded (50-infra/nats-jetstream-*) and not
# necessarily live on every mini; the forwarder is best-effort and exits
# cleanly if the NATS endpoint is unreachable.
#
# Subject:  etzhayyim.langserver.<host>.<lang>.<stream>   (stream = stdout|stderr)
#
# Usage:
#   ./ship-logs-to-nats.sh                        # dry-run (default)
#   ./ship-logs-to-nats.sh --apply                # start forwarders for all langs
#   ./ship-logs-to-nats.sh --apply rust python    # specific langs only
#   ./ship-logs-to-nats.sh --apply --nats-url nats://nats.etzhayyim.local:4222

set -euo pipefail
cd "$(dirname "$0")/.."

MODE="dry-run"
NATS_URL="${NATS_URL:-nats://nats.etzhayyim.local:4222}"
HOST="${ETZHAYYIM_NODE_NAME:-${HOSTNAME%%.*}}"
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --apply) MODE="apply" ;;
    --nats-url) shift; NATS_URL="$1" ;;
    --nats-url=*) NATS_URL="${arg#--nats-url=}" ;;
    --host) shift; HOST="$1" ;;
    --host=*) HOST="${arg#--host=}" ;;
    --help|-h) sed -n '2,25p' "$0"; exit 0 ;;
    *) TARGETS+=("$arg") ;;
  esac
done

if ! command -v nats >/dev/null 2>&1; then
  echo "WARN: 'nats' CLI not installed (brew install nats-io/nats-tools/nats)" >&2
  if [ "$MODE" = "apply" ]; then
    echo "ERROR: cannot --apply without nats CLI" >&2
    exit 1
  fi
fi

LOG_DIR="${ETZHAYYIM_LOG_DIR:-$HOME/.etzhayyim/log}"

# Resolve langs from langservers.toml
LANGS=$(python3 -c "
import tomllib
d = tomllib.loads(open('langservers.toml').read())
for ls in d.get('langserver', []):
    print(ls['lang'])
")

if [ ${#TARGETS[@]} -eq 0 ]; then
  mapfile -t TARGETS <<< "$LANGS"
fi

forward_one() {
  local lang="$1"
  local stream="$2"  # stdout | stderr
  local file="$LOG_DIR/langserver.${lang}.${stream}.log"
  local subject="etzhayyim.langserver.${HOST}.${lang}.${stream}"

  if [ ! -f "$file" ]; then
    echo "[$lang/$stream] log file not yet present at $file — skipping (LSP may not have started)" >&2
    return 0
  fi

  case "$MODE" in
    dry-run)
      echo "[dry-run] would tail $file → nats pub $subject (url=$NATS_URL)"
      ;;
    apply)
      echo "[apply] tail -F $file → nats pub $subject"
      # tail -F handles log rotation by newsyslog (re-opens file after rotation)
      tail -F -n 0 "$file" \
        | while IFS= read -r line; do
            # nats pub reads payload from stdin via -; one publish per line
            printf '%s' "$line" | nats --server "$NATS_URL" pub "$subject" -- 2>/dev/null || true
          done &
      echo "  forwarder pid=$! subject=$subject"
      ;;
  esac
}

echo "═══ langserver → NATS JetStream forwarder ═══"
echo "MODE=$MODE  HOST=$HOST  NATS_URL=$NATS_URL  LOG_DIR=$LOG_DIR"
echo ""

for lang in "${TARGETS[@]}"; do
  forward_one "$lang" "stdout"
  forward_one "$lang" "stderr"
done

if [ "$MODE" = "apply" ]; then
  echo ""
  echo "═══ forwarders launched. Stop with: pkill -f 'ship-logs-to-nats' ═══"
  # Stay alive so child tail -F processes don't get reaped
  wait
fi
