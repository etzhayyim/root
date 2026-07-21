# ---------------------------------------------------------
# ETZ HAYYIM: ROOT ROUTER & 1000 CLEAN ROOM ACTORS
# Production Dockerfile
# ---------------------------------------------------------

# Stage 1: Base Environment
FROM python:3.11-slim-bullseye AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Stage 2: Dependencies
FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 3: Production Image
FROM base AS production
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy the entire architectural ecosystem
COPY 40-engine/ /app/40-engine/
COPY 60-apps/ /app/60-apps/
COPY 70-tools/ /app/70-tools/

# Create volume mount points for the Datomic immutable journal
RUN mkdir -p /app/80-data/datomic_mock && chown -R 1000:1000 /app/80-data

# Set non-root user for security
USER 1000

# Expose the Root Router Gateway Port
EXPOSE 8000

# Boot the Root Router via Uvicorn
WORKDIR /app
CMD ["uvicorn", "40-engine.root-router.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
