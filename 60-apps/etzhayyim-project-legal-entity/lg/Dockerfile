# syntax=docker/dockerfile:1.7
# Build:
#   docker buildx build --platform linux/amd64 \
#     --build-context py=../../../40-engine/kotoba/crates/kotoba-kotodama/py \
#     -t ghcr.io/etzhayyim/lg-legal-entity:0.1.0-amd64 --push .

FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir 'uv>=0.4'

WORKDIR /app

# Install kotodama (editable) — provides kotodama.primitives.legal_entity
COPY --from=py . /opt/kotodama
RUN uv pip install --system --no-cache -e /opt/kotodama

# Install this package
COPY pyproject.toml /app/pyproject.toml
COPY lg_legal_entity /app/lg_legal_entity
RUN uv pip install --system --no-cache -e /app

RUN uv pip uninstall --system uv 2>/dev/null || true

EXPOSE 8000
CMD ["uvicorn", "lg_legal_entity.server:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--access-log", "--log-level", "info"]
