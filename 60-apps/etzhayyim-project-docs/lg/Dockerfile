# lg-docs Dockerfile (ADR-2606010500 — Google/Microsoft compatible drive API).
#
# Build (remote BuildKit, per 50-infra/CLAUDE.md — do NOT local docker build for deploy):
#   cd 60-apps/etzhayyim-project-calendar/lg
#   docker buildx build --builder etzhayyim-vke --platform linux/amd64 \
#     -t ghcr.io/etzhayyim/lg-docs:0.1.0-amd64 \
#     --cache-from type=registry,ref=ghcr.io/etzhayyim/build-cache:main \
#     --push .

FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir 'uv>=0.4'

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY langgraph.json /app/langgraph.json
COPY lg_docs /app/lg_docs

RUN uv pip install --system --no-cache -e /app

RUN uv pip uninstall --system uv 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "lg_docs.server:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", \
     "--access-log", "--log-level", "info"]
