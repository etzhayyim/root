#!/bin/bash
# Build llama.cpp (CUDA) for Llama 4 Scout GGUF inference.
# Run once per pod instance (not needed for vLLM models).

set -euo pipefail

LLAMA_DIR=/workspace/llama.cpp

if [ -f "$LLAMA_DIR/build/bin/llama-server" ]; then
  echo "llama.cpp already built at $LLAMA_DIR"
  exit 0
fi

apt-get install -y cmake build-essential 2>/dev/null || true

git clone --depth 1 https://github.com/ggerganov/llama.cpp "$LLAMA_DIR"
cd "$LLAMA_DIR"
cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --target llama-server -j"$(nproc)"

echo "Built: $LLAMA_DIR/build/bin/llama-server"
