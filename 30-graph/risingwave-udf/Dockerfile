FROM python:3.12-slim

WORKDIR /app

# pyarrow needs build tools only if no wheel; 3.12 has wheels so pip-only
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY udf_server.py .

# Arrow Flight gRPC
EXPOSE 8815

# Env knobs (overridable by K8s manifest / helm values):
#   UDF_PORT         — default 8815
#   LLM_URL          — Murakumo gemma4:e2b OpenAI-compat endpoint
#   LLM_MODEL        — default gemma4:e2b
#   LLM_TIMEOUT_SEC  — default 8
#   T3_IO_THREADS    — default 50 (ADR-0044 D3 recommended)
ENV UDF_PORT=8815 \
    LLM_URL=http://ollama.gftd.ai/v1/chat/completions \
    LLM_MODEL=gemma4:e2b \
    LLM_TIMEOUT_SEC=8 \
    T3_IO_THREADS=50

# Liveness: gRPC port must be reachable. (no HTTP healthcheck — Arrow Flight is gRPC-only)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import socket,os; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',int(os.environ.get('UDF_PORT','8815')))); s.close()" || exit 1

CMD ["python", "udf_server.py"]
