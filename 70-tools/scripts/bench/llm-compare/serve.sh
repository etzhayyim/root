#!/bin/bash
# Start one model on port 8000 (OpenAI-compatible).
# Models are read from the Network Volume; only one runs at a time.
#
# Usage:
#   ./serve.sh qwen3-32b
#   ./serve.sh gemma4-31b
#   ./serve.sh deepseek-r1-32b
#   ./serve.sh llama4-scout
#
# The server blocks; use tmux or screen to background it.

set -euo pipefail

MODEL=${1:-gemma4-31b}
PORT=8000
BASE=/workspace/models

echo "Starting model: $MODEL"

VLLM_COMMON=(
  --host 0.0.0.0
  --port "$PORT"
  --max-model-len 8192
  --gpu-memory-utilization 0.92
  --served-model-name "$MODEL"
)

case "$MODEL" in
  qwen3-32b)
    exec vllm serve "$BASE/qwen3-32b-awq" "${VLLM_COMMON[@]}" \
      --quantization awq_marlin
    ;;

  gemma4-31b)
    # uses compressed-tensors; quantization is auto-detected from config
    exec vllm serve "$BASE/gemma4-31b-awq" "${VLLM_COMMON[@]}" \
      --trust-remote-code
    ;;

  deepseek-r1-32b)
    exec vllm serve "$BASE/deepseek-r1-32b-awq" "${VLLM_COMMON[@]}" \
      --quantization awq_marlin
    ;;

  llama4-scout)
    GGUF=$(ls "$BASE/llama4-scout-gguf"/*.gguf 2>/dev/null | head -1)
    if [ -z "$GGUF" ]; then
      echo "ERROR: no GGUF file found in $BASE/llama4-scout-gguf/"
      exit 1
    fi
    LLAMA_SERVER=/workspace/llama.cpp/build/bin/llama-server
    if [ ! -f "$LLAMA_SERVER" ]; then
      echo "llama.cpp not built — running setup_llamacpp.sh first"
      bash "$(dirname "$0")/setup_llamacpp.sh"
    fi
    # IQ3_XS = 47.5GB; keep ctx short to leave room for KV cache
    exec "$LLAMA_SERVER" \
      -m "$GGUF" \
      --host 0.0.0.0 --port "$PORT" \
      -ngl 99 \
      --ctx-size 4096 \
      --parallel 2 \
      --alias "$MODEL"
    ;;

  *)
    echo "Unknown model: $MODEL"
    exit 1
    ;;
esac
