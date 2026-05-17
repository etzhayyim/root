# Baien bitnet.cpp linux/amd64 reproduction (ADR 2605092350).
#
# Goal: verify whether the "fast but wrong" output from bitnet.cpp i2_s on
# Apple Silicon arm64 also reproduces on linux/amd64. If linux/amd64 i2_s
# yields coherent output, the bug is in the arm64 i2_s decode path. If
# linux/amd64 is also incoherent, the bug is upstream regardless of arch.
#
# The 1.2 GiB GGUF and 4.5 GiB bf16 master are bind-mounted from
# ~/.cache/baien/models so we don't redownload inside the container.
#
# Build:
#   docker build --platform linux/amd64 \
#       -f 70-tools/scripts/training/baien-bitnet-cpp-linux-amd64.dockerfile \
#       -t baien-bitnetcpp:linux-amd64 .
# Run (default = i2_s quant smoke):
#   docker run --rm --platform linux/amd64 \
#       -v $HOME/.cache/baien/models:/models \
#       baien-bitnetcpp:linux-amd64 \
#       i2_s "The capital of France is" 32

FROM --platform=linux/amd64 ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        clang \
        git \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone --depth 1 https://github.com/microsoft/BitNet.git /opt/BitNet \
    && git -C /opt/BitNet submodule update --init --depth 1 --recursive

WORKDIR /opt/BitNet
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt
ENV PATH="/opt/venv/bin:${PATH}"

# Build with the default x86_64 path (i2_s + tl2 codegen). This pulls
# the GGUF inside the image so the runtime container does not need
# network. The bind-mounted /models directory still wins at runtime
# (run.sh resolves /models/BitNet-b1.58-2B-4T/ggml-model-${QUANT}.gguf).
ARG QUANT=i2_s
RUN python setup_env.py \
        --hf-repo microsoft/BitNet-b1.58-2B-4T \
        -md /opt/BitNet/models/BitNet-b1.58-2B-4T \
        -q ${QUANT}

# Entry: $1=quant (i2_s), $2=prompt, $3=n_predict
COPY <<'SH' /opt/run.sh
#!/usr/bin/env bash
set -e
QUANT=${1:-i2_s}
PROMPT=${2:-"The capital of France is"}
N=${3:-32}
GGUF=/models/BitNet-b1.58-2B-4T/ggml-model-${QUANT}.gguf
if [ ! -f "$GGUF" ]; then
  echo "GGUF not found at $GGUF — bind-mount ~/.cache/baien/models to /models" >&2
  exit 2
fi
echo "[linux-amd64] /proc/cpuinfo: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs)"
echo "[linux-amd64] uname: $(uname -m)"
exec /opt/venv/bin/python /opt/BitNet/run_inference.py \
    -m "$GGUF" -p "$PROMPT" -n "$N" -t 4 -temp 0.0 -ngl 0
SH
RUN chmod +x /opt/run.sh
ENTRYPOINT ["/opt/run.sh"]
