#!/usr/bin/env bash
# Loop trajectory stats: read _observations/*-cycle-NN.md and summarize.
#
# Output is markdown — pipe to a file or commit as `_observations/_trajectory.md`
# for the latest snapshot. The script is intended to run as part of each
# active-inference tick to make the loop's own behavior observable.
#
# Active-inference cycle 08 (2026-05-22). Closes Axis 4 Active Inference
# next-action per README.md § As Artificial Organism Ecosystem.
#
# Usage (from repo root):
#   70-tools/scripts/loop/trajectory-stats.sh
#   70-tools/scripts/loop/trajectory-stats.sh _observations > _observations/_trajectory.md

set -euo pipefail

ROOT="${1:-_observations}"
[[ -d "$ROOT" ]] || { echo "No $ROOT directory" >&2; exit 1; }

FILES=$(ls -1 "$ROOT"/*-cycle-*.md 2>/dev/null | sort || true)
[[ -z "$FILES" ]] && { echo "No cycle files found in $ROOT" >&2; exit 0; }

NUM_CYCLES=$(echo "$FILES" | wc -l | tr -d ' ')

echo "# Loop Trajectory Stats"
echo
echo "Generated: $(date '+%Y-%m-%d %H:%M %Z')"
echo "Cycles observed: $NUM_CYCLES"
echo

# --- Section 1: total trajectory ---
echo "## Total trajectory"
echo
echo "| Cycle | Timestamp | Total | Δ vs prev |"
echo "|-------|-----------|-------|-----------|"

prev=""
total_start=""
total_end=""
for f in $FILES; do
  base=$(basename "$f")
  ts=$(echo "$base" | sed -nE 's/^([0-9]+)-cycle-[0-9]+\.md$/\1/p')
  cycle=$(echo "$base" | sed -nE 's/^[0-9]+-cycle-([0-9]+)\.md$/\1/p')
  total=$(grep -oE '\*\*[0-9]+ */ *100\*\*' "$f" | head -1 | grep -oE '[0-9]+ */ *100' | tr -d ' ' || true)
  num=${total%/100}
  [[ -z "$num" ]] && continue

  [[ -z "$total_start" ]] && total_start="$num"
  total_end="$num"

  if [[ -n "$prev" ]]; then
    diff=$((num - prev))
    [[ $diff -ge 0 ]] && delta="+$diff" || delta="$diff"
  else
    delta="—"
  fi
  echo "| $cycle | $ts | $total | $delta |"
  prev=$num
done

if [[ -n "$total_start" && -n "$total_end" ]]; then
  net=$((total_end - total_start))
  [[ $net -ge 0 ]] && net_str="+$net" || net_str="$net"
  echo
  echo "**Net trajectory:** $total_start / 100 → $total_end / 100 ($net_str)"
fi
echo

# --- Section 2: latest per-axis ---
LAST_FILE=$(echo "$FILES" | tail -n1)
echo "## Latest per-axis scores"
echo
echo "Source: \`$(basename "$LAST_FILE")\`"
echo
awk '/^## 3\. Scores/,/^## 4\. Action/' "$LAST_FILE" \
  | grep -E '^\|' \
  | sed 's/Δ vs cycle [0-9]*/Δ/' || true

echo

# --- Section 3: stall detection ---
# A stall = 3 consecutive cycles with Δ = 0 (no axis movement).
# When detected, the loop should auto-emit an ADR proposing a strategy
# change rather than continuing to grind on diminishing returns.
echo "## Stall detection"
echo
STALL_COUNT=0
STALL_LAST_3=()
prev=""
for f in $FILES; do
  total=$(grep -oE '\*\*[0-9]+ */ *100\*\*' "$f" | head -1 | grep -oE '[0-9]+ */ *100' | tr -d ' ' || true)
  num=${total%/100}
  [[ -z "$num" ]] && continue
  if [[ -n "$prev" ]]; then
    diff=$((num - prev))
    STALL_LAST_3+=("$diff")
    # Keep only last 3
    if [[ ${#STALL_LAST_3[@]} -gt 3 ]]; then
      STALL_LAST_3=("${STALL_LAST_3[@]:1}")
    fi
  fi
  prev=$num
done

if [[ ${#STALL_LAST_3[@]} -eq 3 ]]; then
  ZEROS=0
  for d in "${STALL_LAST_3[@]}"; do
    [[ "$d" == "0" ]] && ZEROS=$((ZEROS + 1))
  done
  echo "Last 3 deltas: ${STALL_LAST_3[*]}"
  if [[ $ZEROS -eq 3 ]]; then
    echo
    echo "**STALL DETECTED** — 3 consecutive cycles at Δ=0. Copy \`90-docs/adr/_template-stall-rotation.md\` to \`90-docs/adr/\$(date +%y%m%d%H%M)-stall-rotation.md\`, fill in §1-4, obtain attestation per §5 (Founder during bootstrap; ≥3-of-5 Council post-bootstrap), and emit. The template surface was added cycle 10 (2026-05-22) per active-inference loop Option A."
  else
    echo
    echo "No stall (loop still making progress: $ZEROS / 3 recent ticks at Δ=0)."
  fi
else
  echo "Insufficient history for stall detection (need ≥4 cycles with totals; have ${#STALL_LAST_3[@]} deltas)."
fi

echo

# --- Section 4: artifact count ---
ARTIFACT_COUNT=$(find "$ROOT" -type f \( -name '*.md' -o -name '*.txt' \) | wc -l | tr -d ' ')
echo "## Artifact count"
echo
echo "\`$ROOT\` contains **$ARTIFACT_COUNT** files (cycle records + nested READMEs + anchors)."
