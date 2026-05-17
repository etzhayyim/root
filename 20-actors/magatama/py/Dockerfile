FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/gftdcojp/etzhayyim/root"
LABEL org.opencontainers.image.description="mitama reactive agent shared UDF pool (ADR-0049)"

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ARG WASMTIME_VERSION=44.0.0
ARG FOUNDRY_VERSION=1.5.0
ARG TARGETARCH
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
 && apt-get install -y --no-install-recommends bash postgresql-client ca-certificates poppler-utils tesseract-ocr tesseract-ocr-jpn \
 && rm -rf /var/lib/apt/lists/*

ARG CACHE_BUST=1
COPY pyproject.toml /app/
COPY src /app/src

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl xz-utils \
 && case "${TARGETARCH}" in \
      amd64) wasmtime_arch="x86_64-linux"; foundry_arch="amd64" ;; \
      arm64) wasmtime_arch="aarch64-linux"; foundry_arch="arm64" ;; \
      *) echo "unsupported TARGETARCH=${TARGETARCH}" >&2; exit 1 ;; \
    esac \
 && curl -fsSL "https://github.com/bytecodealliance/wasmtime/releases/download/v${WASMTIME_VERSION}/wasmtime-v${WASMTIME_VERSION}-${wasmtime_arch}.tar.xz" \
    | tar -xJ --strip-components=1 -C /usr/local/bin "wasmtime-v${WASMTIME_VERSION}-${wasmtime_arch}/wasmtime" \
 && curl -fsSL "https://github.com/foundry-rs/foundry/releases/download/v${FOUNDRY_VERSION}/foundry_v${FOUNDRY_VERSION}_linux_${foundry_arch}.tar.gz" \
    | tar -xz -C /usr/local/bin cast \
 && apt-get purge -y --auto-remove curl xz-utils \
 && rm -rf /var/lib/apt/lists/*

# Install PyTorch from the CPU-only wheel index so sentence-transformers
# (required by handlers/actor_embed.py per ADR-0092 L2) does not pull the
# ~2 GB CUDA build. Everything else stays on PyPI. Image layer ≈ 900 MB.
RUN pip install --no-cache-dir \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      "torch>=2.2,<3" \
 && pip install --no-cache-dir .

EXPOSE 8815 9090

CMD ["python", "-m", "pymagatama.server"]
