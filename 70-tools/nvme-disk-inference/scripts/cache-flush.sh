#!/usr/bin/env bash
# cache-flush.sh — evict file pages from macOS unified memory page cache.
#
# Usage:  ./cache-flush.sh [size_gb]
#
# Strategy: write+read N GB of throwaway data to /tmp so the kernel reclaims
# inactive file pages to make room. Default 14 GB targets Mac mini M4 16GB.
#
# Why not `purge`?  Requires sudo. This works in user-space.
# Why /dev/random not /dev/zero?  Some FS/SSD layers compress zeros and skip
# actual write; random forces real disk traffic.

set -euo pipefail

SIZE_GB="${1:-14}"
JUNK="/tmp/cache-flush-junk-$$"

echo "[cache-flush] writing ${SIZE_GB} GB to ${JUNK} (forces page reclaim)…"
dd if=/dev/random of="$JUNK" bs=1m count=$((SIZE_GB * 1024)) 2>/dev/null
echo "[cache-flush] reading back to ensure cache occupancy…"
dd if="$JUNK" of=/dev/null bs=1m 2>/dev/null
rm -f "$JUNK"
echo "[cache-flush] done"
