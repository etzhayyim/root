#!/usr/bin/env bash
# Baien local bitnet.cpp bootstrap (ADR 2605092350).
#
# Clones microsoft/BitNet, builds the CPU kernel, pulls the
# bitnet.cpp-compatible i2_s GGUF for `microsoft/BitNet-b1.58-2B-4T`,
# and runs a tiny inference smoke. All artifacts live under
# ${BAIEN_LOCAL_CACHE} (default ~/.cache/baien) so the repo stays clean.
#
# Usage:
#   ./baien-bitnet-cpp-bootstrap.sh                  # full bootstrap + smoke
#   ./baien-bitnet-cpp-bootstrap.sh --smoke-only     # skip clone/build, run smoke
#   BAIEN_LOCAL_CACHE=/tmp/foo ./baien-bitnet-cpp-bootstrap.sh
#
# Requires: cmake, clang (Xcode CLT), python3, git, huggingface-cli (auto-installed via uv).

set -euo pipefail

CACHE="${BAIEN_LOCAL_CACHE:-$HOME/.cache/baien}"
REPO_DIR="${CACHE}/BitNet"
MODEL_DIR="${CACHE}/models/BitNet-b1.58-2B-4T"
QUANT="${BAIEN_QUANT:-i2_s}"
HF_REPO="${BAIEN_GGUF_REPO:-microsoft/BitNet-b1.58-2B-4T-gguf}"
SMOKE_PROMPT="${BAIEN_SMOKE_PROMPT:-Baien is a 1.58-bit on-device model. In one sentence, what is its primary advantage?}"
SMOKE_TOKENS="${BAIEN_SMOKE_TOKENS:-64}"

mode_smoke_only=0
for a in "$@"; do
  case "$a" in
    --smoke-only) mode_smoke_only=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown arg: $a" >&2; exit 2 ;;
  esac
done

echo "[baien-bootstrap] cache=$CACHE quant=$QUANT hf_repo=$HF_REPO"
mkdir -p "$CACHE"

ensure_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "[baien-bootstrap] uv not found; please install (brew install uv) and retry" >&2
    exit 1
  fi
}

clone_repo() {
  if [ -d "$REPO_DIR/.git" ]; then
    echo "[baien-bootstrap] BitNet repo present, fetching"
    git -C "$REPO_DIR" fetch --depth 1 origin main
    git -C "$REPO_DIR" reset --hard origin/main
  else
    echo "[baien-bootstrap] cloning microsoft/BitNet"
    git clone --depth 1 https://github.com/microsoft/BitNet.git "$REPO_DIR"
  fi
  git -C "$REPO_DIR" submodule update --init --depth 1 --recursive
}

build_kernel() {
  ensure_uv
  cd "$REPO_DIR"
  if [ ! -d .venv ]; then
    echo "[baien-bootstrap] creating venv with uv"
    uv venv --python 3.11 .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  uv pip install -r requirements.txt huggingface_hub
  echo "[baien-bootstrap] running setup_env.py (quant=$QUANT)"
  python setup_env.py -md "$MODEL_DIR" -q "$QUANT" --skip-download || {
    echo "[baien-bootstrap] setup_env.py without --skip-download (fresh clone)"
    python setup_env.py -md "$MODEL_DIR" -q "$QUANT"
  }
}

download_gguf() {
  cd "$REPO_DIR"
  # shellcheck disable=SC1091
  source .venv/bin/activate
  if [ ! -f "$MODEL_DIR/ggml-model-${QUANT}.gguf" ]; then
    echo "[baien-bootstrap] downloading $HF_REPO -> $MODEL_DIR"
    mkdir -p "$MODEL_DIR"
    huggingface-cli download "$HF_REPO" \
      --include "ggml-model-${QUANT}.gguf" "tokenizer.model" "tokenizer.json" "tokenizer_config.json" \
      --local-dir "$MODEL_DIR"
  else
    echo "[baien-bootstrap] gguf already present"
  fi
  ls -lh "$MODEL_DIR" | head -10
}

run_smoke() {
  cd "$REPO_DIR"
  # shellcheck disable=SC1091
  source .venv/bin/activate
  local gguf="$MODEL_DIR/ggml-model-${QUANT}.gguf"
  if [ ! -f "$gguf" ]; then
    echo "[baien-bootstrap] no GGUF at $gguf — run without --smoke-only first" >&2
    exit 1
  fi
  echo "[baien-bootstrap] running inference smoke"
  echo "  prompt: $SMOKE_PROMPT"
  echo "  tokens: $SMOKE_TOKENS"
  python run_inference.py \
    -m "$gguf" \
    -p "$SMOKE_PROMPT" \
    -n "$SMOKE_TOKENS" \
    -t 4 \
    -temp 0.7
}

if [ "$mode_smoke_only" -eq 0 ]; then
  clone_repo
  build_kernel
  download_gguf
fi
run_smoke
