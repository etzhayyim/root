# lg-lawfirm-intake Dockerfile.
#
# Build:
#   cd 60-apps/etzhayyim-project-lawfirm/lg
#   docker buildx build \
#     --builder etzhayyim-vke \
#     --platform linux/amd64 \
#     --cache-from type=registry,ref=ghcr.io/etzhayyimcojp/build-cache:lg-lawfirm-intake \
#     --cache-to   type=registry,ref=ghcr.io/etzhayyimcojp/build-cache:lg-lawfirm-intake,mode=max \
#     -t ghcr.io/etzhayyimcojp/lg-lawfirm-intake:0.1.0-amd64 \
#     --push .

FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir 'uv>=0.4'

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY lg_lawfirm_intake /app/lg_lawfirm_intake

RUN uv pip install --system --no-cache -e /app

RUN uv pip uninstall --system uv 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "lg_lawfirm_intake.server:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", \
     "--access-log", "--log-level", "info"]
