# etzhayyim-organism-viz — realtime + interactive Svelte sumi-e topology
#
# Multi-stage: Node builds the Svelte app → wheel includes dist/ → Python serves.

# ── stage 1: Svelte build ────────────────────────────────────────────────
FROM node:22-slim AS web
WORKDIR /web
COPY web/ ./
RUN npm install -g pnpm@10
RUN pnpm install --ignore-workspace --frozen-lockfile || pnpm install --ignore-workspace
RUN pnpm run build

# ── stage 2: Python app ──────────────────────────────────────────────────
FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/etzhayyim/root"
LABEL org.opencontainers.image.description="etzhayyim-organism-viz — sumi-e topology + chat + SSE"
LABEL org.opencontainers.image.licenses="Apache-2.0 WITH etzhayyim-Charter-Rider-2.0"

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ETZ_REPO=/repo \
    ETZ_VIZ_HOST=0.0.0.0 \
    ETZ_VIZ_PORT=8081

COPY pyproject.toml /app/
COPY src /app/src
COPY organism-pkg /app/organism-pkg
# Force-include in pyproject.toml expects web/dist at the same relative path
# the host has, so the wheel build can locate it. Use BOTH locations.
COPY --from=web /web/dist /app/web/dist

RUN pip install --no-cache-dir \
      "fastapi>=0.115.0" \
      "uvicorn[standard]>=0.30.0" \
      "pydantic>=2.0" \
 && pip install --no-cache-dir /app/organism-pkg \
 && pip install --no-cache-dir .

RUN useradd --no-create-home --uid 10001 viz
USER 10001:10001

EXPOSE 8081
ENTRYPOINT ["python", "-m", "etzhayyim_organism_viz", "serve"]
