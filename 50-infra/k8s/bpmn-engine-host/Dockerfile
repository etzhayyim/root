FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY engine.py main.py ./

EXPOSE 8080

# Granian ASGI server (matches existing pyzeebe-worker FastAPI sidecar pattern,
# 50-infra/deps.toml [knowledge.zeebe-worker-fastapi-granian-sidecar-20260507]).
CMD ["granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8080", \
     "--workers", "1", "main:app"]
