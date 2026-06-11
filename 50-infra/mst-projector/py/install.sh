#!/usr/bin/env bash
# mst-projector LaunchDaemon installer for Murakumo simeon node.
#
# Per ADR-2605215500 §4 M4 deployment milestone.
#
# Requirements:
#   - macOS (launchctl / plutil)
#   - uv (Astral package manager) installed at /opt/homebrew/bin/uv or /usr/local/bin/uv
#   - LanceDB data dir writable
#   - sudo access (for /Library/LaunchDaemons/ + /var/lib/ + /var/log/)
#
# Usage:
#   sudo ./install.sh [--data-dir /custom/path] [--port 8765] [--install-dir /custom/path]

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
INSTALL_DIR="${INSTALL_DIR:-/opt/etzhayyim/mst-projector}"
DATA_DIR="${ETZHAYYIM_MST_PROJECTOR_DATA_DIR:-/var/lib/etzhayyim/mst-projector}"
LOG_DIR="/var/log/etzhayyim"
PORT="${ETZHAYYIM_MST_PROJECTOR_PORT:-8765}"
LABEL="com.etzhayyim.mst-projector"
PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/launchd/${LABEL}.plist"
PLIST_DEST="/Library/LaunchDaemons/${LABEL}.plist"

# ── Discover uv ───────────────────────────────────────────────────────────────
UV_PATH=""
for candidate in /opt/homebrew/bin/uv /usr/local/bin/uv "$(command -v uv 2>/dev/null || true)"; do
    if [ -x "$candidate" ]; then
        UV_PATH="$candidate"
        break
    fi
done

if [ -z "$UV_PATH" ]; then
    echo "ERROR: uv not found. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# ── Parse args ────────────────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
    case "$1" in
        --data-dir)    DATA_DIR="$2";    shift 2 ;;
        --port)        PORT="$2";        shift 2 ;;
        --install-dir) INSTALL_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: sudo ./install.sh [--data-dir /path] [--port 8765] [--install-dir /path]"
            exit 0
            ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

# ── Sudo check ────────────────────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: must run as root (sudo)" >&2
    exit 1
fi

echo "=== mst-projector install ==="
echo "  install dir: ${INSTALL_DIR}"
echo "  data dir:    ${DATA_DIR}"
echo "  log dir:     ${LOG_DIR}"
echo "  port:        ${PORT}"
echo "  uv:          ${UV_PATH}"

# ── Stop existing service if loaded ──────────────────────────────────────────
if launchctl list | grep -q "${LABEL}"; then
    echo "stopping existing service..."
    launchctl unload "${PLIST_DEST}" 2>/dev/null || true
fi

# ── Copy source ───────────────────────────────────────────────────────────────
echo "installing source to ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"
SRC_ROOT="$(cd "$(dirname "$0")" && pwd)"
rsync -av --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
    "${SRC_ROOT}/" "${INSTALL_DIR}/"
chown -R root:wheel "${INSTALL_DIR}"

# ── Create data + log dirs ────────────────────────────────────────────────────
mkdir -p "${DATA_DIR}" "${LOG_DIR}"
chown -R root:wheel "${DATA_DIR}" "${LOG_DIR}"
chmod 755 "${DATA_DIR}" "${LOG_DIR}"

# ── Install Python deps via uv ────────────────────────────────────────────────
echo "installing Python deps via uv..."
cd "${INSTALL_DIR}"
"${UV_PATH}" sync --frozen 2>/dev/null || "${UV_PATH}" sync

# ── Render plist with placeholder substitutions ───────────────────────────────
echo "installing LaunchDaemon plist..."
sed -e "s|@@UV_PATH@@|${UV_PATH}|g" \
    -e "s|@@INSTALL_DIR@@|${INSTALL_DIR}|g" \
    "${PLIST_SRC}" > "${PLIST_DEST}"

# Override data dir + port if non-default values were supplied
plutil -replace 'EnvironmentVariables.ETZHAYYIM_MST_PROJECTOR_DATA_DIR' \
    -string "${DATA_DIR}" "${PLIST_DEST}"
plutil -replace 'EnvironmentVariables.ETZHAYYIM_MST_PROJECTOR_PORT' \
    -string "${PORT}" "${PLIST_DEST}"

chown root:wheel "${PLIST_DEST}"
chmod 644 "${PLIST_DEST}"

# ── Load service ──────────────────────────────────────────────────────────────
echo "loading LaunchDaemon..."
launchctl load -w "${PLIST_DEST}"

# ── Smoke test ────────────────────────────────────────────────────────────────
sleep 3
if launchctl list | grep -q "${LABEL}"; then
    echo ""
    echo "mst-projector installed and loaded"
    echo ""
    echo "Status:"
    launchctl print "system/${LABEL}" 2>/dev/null | grep -E "(state|pid|last exit code)" | head -5 || true
    echo ""
    echo "Logs:"
    echo "  ${LOG_DIR}/mst-projector.out.log"
    echo "  ${LOG_DIR}/mst-projector.err.log"
    echo ""
    echo "Test:"
    echo "  curl -s -X POST http://localhost:${PORT}/xrpc/com.etzhayyim.mstProjector.countByCollection \\"
    echo "    -H 'Content-Type: application/json' -d '{\"collection\":\"app.bsky.feed.post\"}'"
else
    echo "ERROR: service failed to load. Check logs:" >&2
    echo "  ${LOG_DIR}/mst-projector.err.log" >&2
    exit 1
fi
