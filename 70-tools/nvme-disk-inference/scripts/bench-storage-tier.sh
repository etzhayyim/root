#!/usr/bin/env bash
# bench-storage-tier.sh — A/B llama.cpp inference bench across two storage tiers.
#
# Usage:
#   ./bench-storage-tier.sh \
#     --model gemma-4-26B-A4B-it-UD-Q3_K_M.gguf \
#     --tier-a-dir /Volumes/SanDisk/models \
#     --tier-b-dir /Users/$USER/Models \
#     --tier-a-label sandisk-usb32-gen2 \
#     --tier-b-label internal-ap0256z \
#     --prompt "Mac mini M4 16GB で 26B MoE モデルを動かす最大の制約を 3 行で。" \
#     --output results/
#
# Protocol per tier:
#   1. flush page cache (14 GB junk write+read)
#   2. cold llama-cli run with `time -l`
#   3. capture full stdout/stderr to results/{label}-{date}.txt

set -euo pipefail

LLAMA_CLI="${LLAMA_CLI:-/opt/homebrew/bin/llama-cli}"
THREADS="${THREADS:-4}"
CTX="${CTX:-2048}"
N_PREDICT="${N_PREDICT:-120}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

usage() {
  grep '^#' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-1}"
}

MODEL_NAME=""
TIER_A_DIR=""
TIER_B_DIR=""
TIER_A_LABEL="tier-a"
TIER_B_LABEL="tier-b"
PROMPT="Mac mini M4 16GB で 26B MoE モデルを動かす最大の制約を 3 行で。"
OUT_DIR="results"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)         MODEL_NAME="$2"; shift 2 ;;
    --tier-a-dir)    TIER_A_DIR="$2"; shift 2 ;;
    --tier-b-dir)    TIER_B_DIR="$2"; shift 2 ;;
    --tier-a-label)  TIER_A_LABEL="$2"; shift 2 ;;
    --tier-b-label)  TIER_B_LABEL="$2"; shift 2 ;;
    --prompt)        PROMPT="$2"; shift 2 ;;
    --output)        OUT_DIR="$2"; shift 2 ;;
    -h|--help)       usage 0 ;;
    *) echo "unknown arg: $1" >&2; usage 1 ;;
  esac
done

[[ -z "$MODEL_NAME" || -z "$TIER_A_DIR" || -z "$TIER_B_DIR" ]] && usage 1
[[ ! -x "$LLAMA_CLI" ]] && { echo "missing $LLAMA_CLI" >&2; exit 2; }

mkdir -p "$OUT_DIR"
DATE_TAG="$(date +%Y%m%d-%H%M)"

run_tier() {
  local label="$1"
  local model_path="$2"
  local outfile="$OUT_DIR/${label}-${DATE_TAG}.txt"

  echo "=== $label : $model_path ==="
  echo "[$(date -Iseconds)] flushing page cache…"
  "$SCRIPT_DIR/cache-flush.sh" 14

  echo "[$(date -Iseconds)] running llama-cli (cold)…"
  {
    echo "tier_label=$label"
    echo "model_path=$model_path"
    echo "host=$(uname -mnrs)"
    echo "llama_cli=$LLAMA_CLI"
    echo "ts_start=$(date -Iseconds)"
    echo "----"
    /usr/bin/time -l "$LLAMA_CLI" -m "$model_path" \
      -ngl 0 -c "$CTX" -fa 1 -ctk q8_0 -ctv q8_0 -t "$THREADS" -n "$N_PREDICT" \
      -no-cnv -st --simple-io -p "$PROMPT" < /dev/null
    echo "----"
    echo "ts_end=$(date -Iseconds)"
  } > "$outfile" 2>&1

  echo "→ $outfile"
  echo ""
  grep -E "(Prompt:|Generation:|real|maximum resident|page faults|swaps|peak memory footprint)" "$outfile" || true
  echo ""
}

[[ -f "$TIER_A_DIR/$MODEL_NAME" ]] || { echo "missing tier-A: $TIER_A_DIR/$MODEL_NAME" >&2; exit 3; }
[[ -f "$TIER_B_DIR/$MODEL_NAME" ]] || { echo "missing tier-B: $TIER_B_DIR/$MODEL_NAME" >&2; exit 3; }

run_tier "$TIER_A_LABEL" "$TIER_A_DIR/$MODEL_NAME"
sleep 3
run_tier "$TIER_B_LABEL" "$TIER_B_DIR/$MODEL_NAME"

echo "=== A/B done. results in $OUT_DIR/ ==="
