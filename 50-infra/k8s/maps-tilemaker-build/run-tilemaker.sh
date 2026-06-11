#!/usr/bin/env bash
#
# run-tilemaker.sh
# ----------------
# One-shot build: download OSM PBF → tilemaker → PMTiles → R2 upload → update
# manifest.json. Designed to run as a Kubernetes Job entrypoint.
#
# Required env:
#   PBF_URL                Source OSM PBF (https://... or s3://...)
#   R2_BUCKET              R2 bucket name, e.g. etzhayyim-maps-tiles
#   R2_ACCOUNT_ID          Cloudflare account id (for rclone S3 endpoint)
#   R2_ACCESS_KEY_ID       R2 S3 access key id (secret)
#   R2_SECRET_ACCESS_KEY   R2 S3 secret access key (secret)
#
# Optional env:
#   VERSION                Defaults to UTC date-hour (YYYYMMDDHH).
#   TILEMAKER_CONFIG       Defaults to /config/openmaptiles.json.
#   TILEMAKER_PROCESS      Defaults to /config/openmaptiles.lua.
#   TILEMAKER_EXTRA        Extra tilemaker CLI args (e.g. "--bbox 128,30,146,46").
#   TILEMAKER_THREADS      Defaults to nproc.
#   CONFIG_FETCH_AT_RUNTIME=1 to curl upstream config instead of using vendored.
#
set -Eeuo pipefail

log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*"; }
die() { log "FATAL: $*"; exit 1; }

: "${PBF_URL:?PBF_URL is required}"
: "${R2_BUCKET:?R2_BUCKET is required}"
: "${R2_ACCOUNT_ID:?R2_ACCOUNT_ID is required}"
: "${R2_ACCESS_KEY_ID:?R2_ACCESS_KEY_ID is required}"
: "${R2_SECRET_ACCESS_KEY:?R2_SECRET_ACCESS_KEY is required}"

VERSION="${VERSION:-$(date -u +%Y%m%d%H)}"
TILEMAKER_CONFIG="${TILEMAKER_CONFIG:-/config/openmaptiles.json}"
TILEMAKER_PROCESS="${TILEMAKER_PROCESS:-/config/openmaptiles.lua}"
TILEMAKER_THREADS="${TILEMAKER_THREADS:-$(nproc)}"

SCRATCH=/scratch
PBF=${SCRATCH}/planet.osm.pbf
PMTILES=${SCRATCH}/planet-${VERSION}.pmtiles
MANIFEST=${SCRATCH}/manifest.json

mkdir -p "${SCRATCH}"

# --- 0. optional: fetch fresh OpenMapTiles config at runtime -----------------
if [[ "${CONFIG_FETCH_AT_RUNTIME:-0}" == "1" ]]; then
  log "Fetching fresh openmaptiles config from upstream tilemaker resources"
  curl -fsSL -o /config/openmaptiles.json \
    https://raw.githubusercontent.com/systemed/tilemaker/master/resources/config-openmaptiles.json
  curl -fsSL -o /config/openmaptiles.lua \
    https://raw.githubusercontent.com/systemed/tilemaker/master/resources/process-openmaptiles.lua
fi

# --- 1. download PBF ----------------------------------------------------------
log "Downloading PBF: ${PBF_URL}"
if [[ "${PBF_URL}" == s3://* || "${PBF_URL}" == r2://* ]]; then
  # rclone supports s3:// and r2:// style sources if a remote is configured.
  rclone copyto "${PBF_URL}" "${PBF}" --s3-no-check-bucket
else
  curl -fL --retry 5 --retry-delay 10 -o "${PBF}" "${PBF_URL}"
fi
PBF_BYTES=$(stat -c %s "${PBF}")
log "Downloaded ${PBF_BYTES} bytes to ${PBF}"

# --- 2. tilemaker -------------------------------------------------------------
log "Running tilemaker: threads=${TILEMAKER_THREADS} config=${TILEMAKER_CONFIG} process=${TILEMAKER_PROCESS}"
# tilemaker emits PMTiles directly when --output has a .pmtiles extension.
# shellcheck disable=SC2086
tilemaker \
  --input "${PBF}" \
  --output "${PMTILES}" \
  --config "${TILEMAKER_CONFIG}" \
  --process "${TILEMAKER_PROCESS}" \
  --threads "${TILEMAKER_THREADS}" \
  ${TILEMAKER_EXTRA:-}

PMTILES_BYTES=$(stat -c %s "${PMTILES}")
log "tilemaker produced ${PMTILES_BYTES} bytes at ${PMTILES}"

# --- 3. configure rclone for R2 ----------------------------------------------
# R2 S3 endpoint: https://<ACCOUNT_ID>.r2.cloudflarestorage.com
export RCLONE_CONFIG_R2_TYPE=s3
export RCLONE_CONFIG_R2_PROVIDER=Cloudflare
export RCLONE_CONFIG_R2_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}"
export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}"
export RCLONE_CONFIG_R2_ENDPOINT="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
export RCLONE_CONFIG_R2_ACL=private
export RCLONE_CONFIG_R2_NO_CHECK_BUCKET=true

R2_KEY="v1/planet-${VERSION}.pmtiles"
log "Uploading ${PMTILES} → r2://${R2_BUCKET}/${R2_KEY}"
rclone copyto --s3-chunk-size=64M --s3-upload-concurrency=8 \
  "${PMTILES}" "r2:${R2_BUCKET}/${R2_KEY}"

# --- 4. manifest.json ---------------------------------------------------------
# Worker reads manifest.json from KV (with R2 fallback) to resolve the "current"
# PMTiles. Atomically swap by uploading manifest.json last.
BUILT_AT="$(date -u +%FT%TZ)"
jq -n \
  --arg version    "${VERSION}" \
  --arg pmtilesKey "${R2_KEY}" \
  --arg builtAt    "${BUILT_AT}" \
  --argjson bytes  "${PMTILES_BYTES}" \
  --arg source     "${PBF_URL}" \
  '{
    schema: "openmaptiles",
    version: $version,
    pmtilesKey: $pmtilesKey,
    builtAt: $builtAt,
    bytes: $bytes,
    source: $source,
    tileFormat: "pbf",
    minZoom: 0,
    maxZoom: 14
  }' > "${MANIFEST}"

log "Uploading manifest.json:"
cat "${MANIFEST}"
rclone copyto "${MANIFEST}" "r2:${R2_BUCKET}/v1/manifest.json"

log "DONE version=${VERSION} key=${R2_KEY} bytes=${PMTILES_BYTES}"
