# lg-recap OSS Dockerfile (no langgraph-api paid image required).
#
# Build:
#   cd 60-apps/etzhayyim-project-recap/lg
#   docker buildx build --platform linux/amd64 \
#     --build-context py=../../../40-engine/kotoba/crates/kotoba-kotodama/py \
#     -t ghcr.io/etzhayyim/lg-recap:0.1.0-amd64 --push .

FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates \
        curl \
        ffmpeg \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# Install deno (yt-dlp JS runtime for YouTube extraction, avoids bot-detection fallback).
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh \
    && deno --version

RUN pip install --no-cache-dir 'uv>=0.4'

WORKDIR /app

COPY --from=py . /opt/kotodama
RUN uv pip install --system --no-cache -e /opt/kotodama

COPY pyproject.toml /app/pyproject.toml
COPY langgraph.json /app/langgraph.json
COPY lg_recap /app/lg_recap

RUN uv pip install --system --no-cache -e /app

RUN uv pip uninstall --system uv 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "lg_recap.server:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", \
     "--access-log", "--log-level", "info"]
