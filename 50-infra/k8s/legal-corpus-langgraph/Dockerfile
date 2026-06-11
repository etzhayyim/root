FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/etzhayyim/root"
LABEL org.opencontainers.image.description="legal-corpus LangGraph worker (ADR-0049, ADR-2605080600)"

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
# Install torch CPU-only first to avoid pulling the ~2 GB CUDA build.
RUN pip install --no-cache-dir \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      "torch>=2.2,<3"

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY legal_corpus_langgraph.py legal_corpus_worker.py mcp_server.py /app/

EXPOSE 8080

CMD ["python", "/app/legal_corpus_worker.py"]
