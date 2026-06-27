# lg-chat OSS Dockerfile — general-purpose chat.gftd.ai LangGraph server.
#
# Build (from repo root, linux/amd64 via BuildKit k8s remote — ADR-2605142000):
#   docker buildx build --platform linux/amd64 \
#     -f 60-apps/ai-gftd-chat-shell/lg/Dockerfile \
#     -t ghcr.io/gftdcojp/lg-chat:0.1.0-amd64 \
#     --push \
#     60-apps/ai-gftd-chat-shell/lg

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

COPY pyproject.toml /app/pyproject.toml
COPY langgraph.json /app/langgraph.json
COPY lg_chat /app/lg_chat

RUN uv pip install --system --no-cache -e /app

RUN uv pip uninstall --system uv 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "lg_chat.server:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", \
     "--access-log", "--log-level", "info"]
