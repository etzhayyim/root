# lg-ses OSS Dockerfile — SES 案件 ingest LangGraph server (Phase 3).
# Server entrypoint: pymagatama.ses.server (granian ASGI)
# CronJob entrypoint: python -m pymagatama.ses.cron_main
#
# Build (Phase 3):
#   cd 60-apps/ai-gftd-project-ses/lg
#   docker buildx build --builder gftd-vke --platform linux/amd64 \
#     --build-context py=../../../20-actors/magatama/py \
#     --cache-from type=registry,ref=ghcr.io/gftdcojp/build-cache:lg-ses \
#     --cache-to   type=registry,ref=ghcr.io/gftdcojp/build-cache:lg-ses,mode=max \
#     -t ghcr.io/gftdcojp/pymagatama:ses-phase3-202605141100-amd64 --push .

FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir 'uv>=0.4'

WORKDIR /app

# pymagatama — contains pymagatama.ses.{server,graph,state,outlook_pull,...}
COPY --from=py . /opt/pymagatama
RUN uv pip install --system --no-cache -e /opt/pymagatama

RUN uv pip uninstall --system uv 2>/dev/null || true

EXPOSE 8000

CMD ["granian", "--interface", "asgi", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--access-log", \
     "pymagatama.ses.server:app"]
