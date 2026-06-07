# lg-karute — LangServer image for the karute Pregel.
#
# Build context: repo root (so the COPY can reach 40-engine/kotoba/crates/kotoba-kotodama/py).
#
#   docker build -f 50-infra/k8s/lg-karute/Dockerfile \
#     -t ghcr.io/etzhayyim/lg-karute:$(git rev-parse --short HEAD) .
#
# Per ADR-2605231100 (karute EMR Phase 1) + ADR-2605231900 (deployment).
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir \
      "langgraph-cli[inmem]>=0.4.0,<1" \
      "langgraph>=0.6,<0.8" \
      "pydantic>=2.5,<3" \
      "pyyaml>=6.0,<7"

# Copy kotodama (editable install — picks up karute pregel module).
COPY 40-engine/kotoba/crates/kotoba-kotodama/py /opt/kotodama
RUN pip install --no-cache-dir -e /opt/kotodama

COPY 50-infra/k8s/lg-karute/langgraph.json /app/langgraph.json

EXPOSE 8080

USER 65532:65532

ENTRYPOINT ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8080", "--no-browser"]
