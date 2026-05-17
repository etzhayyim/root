# Shared image for the lightweight maps3d workers (mapillary-fetcher,
# langgraph-curator, langgraph-actor-link). The colmap-worker uses
# Dockerfile.colmap which adds the COLMAP CPU binary on top.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install minimal build deps for psycopg / numpy wheels, then drop them.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
# colmap-worker is the only consumer of open3d — exclude it here so the
# light pods stay slim. The colmap Dockerfile reinstalls the full set.
RUN grep -vE "^(open3d|b2sdk)" /app/requirements.txt > /app/req.light.txt \
 && pip install --no-cache-dir -r /app/req.light.txt

COPY . /app/workers
ENV PYTHONPATH=/app

# Default command is overridden by each Deployment's `command:`.
CMD ["python", "-m", "workers.mapillary_fetcher"]
