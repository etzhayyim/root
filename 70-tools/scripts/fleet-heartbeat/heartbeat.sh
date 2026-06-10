#!/usr/bin/env bash
# fleet-heartbeat — beat every locally-runnable actor's autonomous loop once.
#
# Runs each actor's `autorun.py` (the charter-permitted autonomous form: offline observe →
# analyze → persist a content-addressed transaction to the LOCAL append-only kotoba Datom
# log; ADR-2605312345). FAIL-OPEN per actor: one actor's failure never stops the fleet.
#
# DISCIPLINE (unchanged from each actor's gates):
#   - No live external I/O here — live ingest/posting stays per-actor operator/Council-gated
#     (e.g. KANJO_OPERATOR_GATE for EDGAR fetch). This script only beats the OFFLINE loops.
#   - Narration cells route Murakumo-only (ADR-2605215000) and degrade gracefully when the
#     fleet endpoint is down; this script never substitutes another LLM.
#
# Usage:
#   70-tools/scripts/fleet-heartbeat/heartbeat.sh             # 1 cycle per actor
#   CYCLES=3 70-tools/scripts/fleet-heartbeat/heartbeat.sh    # N cycles per actor
#   ACTORS="shionome kanjo" 70-tools/scripts/fleet-heartbeat/heartbeat.sh   # subset
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CYCLES="${CYCLES:-1}"
# actor → autorun dir (relative to repo root). tadori is case-anchored (needs TADORI_CASE_ID)
# so it is opt-in via ACTORS rather than part of the default beat.
DEFAULT_ACTORS="shionome kanjo kabuto kosatsu keizu danjo watari watatsuna sukashi ipaddress yabai"
ACTORS="${ACTORS:-$DEFAULT_ACTORS}"

# plain counters/strings (macOS ships bash 3.2 — empty arrays trip `set -u`)
ok_n=0; fail_n=0; failed=""
start_ts=$(date +%s)

for actor in $ACTORS; do
  dir="$ROOT/20-actors/$actor/methods"
  [ -f "$dir/autorun.py" ] || dir="$ROOT/20-actors/$actor/kotoba"
  if [ ! -f "$dir/autorun.py" ]; then
    echo "· $actor: no autorun.py — skipped"
    continue
  fi
  line=$(cd "$dir" && timeout 300 python3 autorun.py --cycles "$CYCLES" 2>&1 | grep -E "♥|log:" | tail -2)
  if [ -n "$line" ]; then
    echo "♥ $actor:"
    echo "$line" | sed 's/^/    /'
    ok_n=$((ok_n + 1))
  else
    echo "✗ $actor: heartbeat FAILED (no cycle output)"
    fail_n=$((fail_n + 1)); failed="$failed $actor"
  fi
done

echo
echo "── fleet-heartbeat: $ok_n beating · $fail_n failed · $(( $(date +%s) - start_ts ))s ──"
[ "$fail_n" -gt 0 ] && { echo "failed:$failed"; exit 1; }
exit 0
