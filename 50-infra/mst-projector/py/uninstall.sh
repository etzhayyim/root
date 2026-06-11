#!/usr/bin/env bash
# mst-projector LaunchDaemon uninstaller.
#
# Per ADR-2605215500 §4 M4 deployment milestone.
#
# Usage:
#   sudo ./uninstall.sh            # preserve data + logs (default)
#   sudo KEEP_DATA=0 ./uninstall.sh  # also wipe /var/lib and log files

set -euo pipefail

LABEL="com.etzhayyim.mst-projector"
PLIST_DEST="/Library/LaunchDaemons/${LABEL}.plist"
INSTALL_DIR="${INSTALL_DIR:-/opt/etzhayyim/mst-projector}"
KEEP_DATA="${KEEP_DATA:-1}"  # by default, preserve data + logs

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: must run as root (sudo)" >&2
    exit 1
fi

# ── Stop service ──────────────────────────────────────────────────────────────
if launchctl list | grep -q "${LABEL}"; then
    echo "stopping service..."
    launchctl unload "${PLIST_DEST}" 2>/dev/null || true
fi

# ── Remove plist ──────────────────────────────────────────────────────────────
if [ -f "${PLIST_DEST}" ]; then
    rm -f "${PLIST_DEST}"
    echo "removed plist: ${PLIST_DEST}"
fi

# ── Remove install dir ────────────────────────────────────────────────────────
echo "removing install dir: ${INSTALL_DIR}"
rm -rf "${INSTALL_DIR}"

# ── Optionally remove data + logs ─────────────────────────────────────────────
if [ "${KEEP_DATA}" -eq 0 ]; then
    echo "removing data dir: /var/lib/etzhayyim/mst-projector"
    rm -rf "/var/lib/etzhayyim/mst-projector"
    echo "removing log files: /var/log/etzhayyim/mst-projector.*.log"
    rm -f "/var/log/etzhayyim/mst-projector.out.log" \
          "/var/log/etzhayyim/mst-projector.err.log"
fi

echo "mst-projector uninstalled (data preserved: ${KEEP_DATA})"
