# lg-uhl-right-neural — LangServer image for the uhl_right_neural Pregel.
#
# Build context: repo root (so the COPY can reach 20-actors/magatama/py).
#
#   docker build -f 50-infra/k8s/lg-uhl-right-neural/Dockerfile \
#     -t ghcr.io/etzhayyim/lg-uhl-right-neural:$(git rev-parse --short HEAD) .
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install langgraph CLI + minimal runtime deps. pymagatama is installed in
# editable mode in the next stage so seed YAMLs are picked up via importlib.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir \
      "langgraph-cli[inmem]>=0.4.0,<1" \
      "langgraph>=0.6,<0.8" \
      "pydantic>=2.5,<3" \
      "pyyaml>=6.0,<7"

# Copy the pymagatama package (project source layout).
COPY 20-actors/magatama/py /opt/pymagatama
RUN pip install --no-cache-dir -e /opt/pymagatama

# Langgraph CLI config (this directory only).
COPY 50-infra/k8s/lg-uhl-right-neural/langgraph.json /app/langgraph.json

EXPOSE 8080

USER 65532:65532

ENTRYPOINT ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8080", "--no-browser"]
