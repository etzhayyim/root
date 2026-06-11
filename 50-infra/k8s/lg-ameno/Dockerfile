# lg-ameno — Container image for the Path-B ameno headless daemon.
#
# Wraps kotodama.projects.ameno (Python LangGraph + FastAPI) so the
# same StateGraph the svelte browser appview and TS daemon run can also
# deploy as a K3s pod on the Murakumo Mac-mini fleet.
#
# Build context: repo root (so the COPY can reach 40-engine/kotoba/crates/kotoba-kotodama/py).
#
#   docker build -f 50-infra/k8s/lg-ameno/Dockerfile \
#     -t ghcr.io/etzhayyim/lg-ameno:$(git rev-parse --short HEAD) .
#
# Authoritative:
#   ADR-2605191257 — Path B Python port
#   ADR-2605191346 — etzhayyim is Vultr-free (K3s on Mac-mini)
#   ADR-2605191229 — Path A daemon (TS reference)

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Minimal runtime deps. uvicorn is what server.py drives; the rest are
# transitive but worth pinning at the layer boundary so cache stays
# stable across kotodama edits.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir \
      "uvicorn[standard]>=0.30,<1" \
      "fastapi>=0.115,<1" \
      "httpx>=0.27,<1" \
      "langgraph>=0.6,<0.8" \
      "langgraph-checkpoint>=2.0,<3" \
      "langchain-core>=0.3,<1" \
      "pydantic>=2.7,<3"

# Copy the kotodama package (project source layout).
COPY 40-engine/kotoba/crates/kotoba-kotodama/py /opt/kotodama
RUN pip install --no-cache-dir --no-deps -e /opt/kotodama

# Default home — overridable via env at pod boundary so the volume mount
# can route this to a PVC.
ENV AMENO_HOME=/var/etzhayyim/ameno \
    AMENO_HOST=0.0.0.0 \
    AMENO_PORT=8080 \
    LOCAL_LLM_PROVIDER=ollama \
    LOCAL_LLM_ENDPOINT=http://ollama.etzhayyim-langserver.svc.cluster.local:11434/api/chat \
    LOCAL_LLM_MODEL=gemma3:4b

EXPOSE 8080

# Run as the same non-root uid the lg-uhl-right-neural pod uses so the
# pod-spec securityContext (runAsUser=65532, fsGroup=65532) stays uniform.
USER 65532:65532

# Equivalent to `python -m kotodama.projects.ameno` but without the
# `-m` indirection so signal handling routes cleanly to uvicorn.
ENTRYPOINT ["uvicorn", "kotodama.projects.ameno.server:app", \
            "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
