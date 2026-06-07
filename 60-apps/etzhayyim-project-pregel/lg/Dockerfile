# lg-pregel OSS Dockerfile (mirrors lg-yatabase pattern; ADR-2605080600).
#
# Build (remote BuildKit, linux/amd64):
#   cd 60-apps/etzhayyim-project-pregel/lg
#   docker buildx build \
#     --builder etzhayyim-vke \
#     --platform linux/amd64 \
#     --build-context py=../../../40-engine/kotoba/crates/kotoba-kotodama/py \
#     --cache-from type=registry,ref=ghcr.io/etzhayyim/build-cache:lg-pregel \
#     --cache-to   type=registry,ref=ghcr.io/etzhayyim/build-cache:lg-pregel,mode=max \
#     -t ghcr.io/etzhayyim/lg-pregel:0.0.1-amd64 \
#     --push .

FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir 'uv>=0.4'

WORKDIR /app

# kotodama (editable, mounted via --build-context py=...)
COPY --from=py . /opt/kotodama
RUN uv pip install --system --no-cache -e /opt/kotodama

# lg-pregel own deps
COPY pyproject.toml /app/pyproject.toml
COPY langgraph.json /app/langgraph.json
COPY lg_pregel /app/lg_pregel

RUN uv pip install --system --no-cache -e /app

RUN uv pip uninstall --system uv 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "lg_pregel.server:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", \
     "--access-log", "--log-level", "info"]
