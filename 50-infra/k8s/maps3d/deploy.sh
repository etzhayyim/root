#!/usr/bin/env bash
# maps3d photogrammetry pipeline — single-command bring-up.
#
# Idempotent. Takes credentials from env / macOS Keychain, runs the
# six-step sequence: migrate → build → push → secrets → apply → smoke.
# Each phase has a corresponding --skip flag for partial re-runs.
#
# Required env (or macOS Keychain via `security find-generic-password`):
#   KOTOBA_URL              postgres URL for Kotoba/Datomic (etzhayyim.rw / ROOT_URL)
#   MAPILLARY_TOKEN     Mapillary v4 client access token
#   MURAKUMO_API_KEY    LLM gateway key
#   B2_KEY_ID           Backblaze B2 application key id
#   B2_APPLICATION_KEY  Backblaze B2 application key
#
# Optional env:
#   IMAGE_TAG           default `latest`
#   GHCR_USER           default `gh api user -q .login`
#   GHCR_TOKEN          default `gh auth token`
#   KUBECONTEXT         default current context
#   AGENTGATEWAY_MCP_URL default `http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080`
#   TEST_TILE_H3        default `8a2a1072b59ffff` (Tokyo Station)
#
# Usage:
#   50-infra/k8s/maps3d/deploy.sh                # full sequence
#   50-infra/k8s/maps3d/deploy.sh --dry-run      # validate only, no side effects
#   50-infra/k8s/maps3d/deploy.sh --skip-build   # re-apply without rebuilding images
#   50-infra/k8s/maps3d/deploy.sh --smoke-only   # re-run Layer 2 against existing pods

set -euo pipefail

# ─── Resolve repo root ──────────────────────────────────────────────
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"

# ─── Defaults + flags ───────────────────────────────────────────────
IMAGE_TAG="${IMAGE_TAG:-latest}"
GHCR_REGISTRY="ghcr.io/etzhayyim"
WORKER_IMAGE="$GHCR_REGISTRY/maps3d-worker:$IMAGE_TAG"
COLMAP_IMAGE="$GHCR_REGISTRY/maps3d-colmap-worker:$IMAGE_TAG"
TEST_TILE_H3="${TEST_TILE_H3:-8a2a1072b59ffff}"
AGENTGATEWAY_MCP_URL="${AGENTGATEWAY_MCP_URL:-http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080}"

DRY_RUN=0
SKIP_MIGRATE=0
SKIP_BUILD=0
SKIP_PUSH=0
SKIP_SECRETS=0
SKIP_APPLY=0
SKIP_SMOKE=0
SMOKE_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)        DRY_RUN=1 ;;
    --skip-migrate)   SKIP_MIGRATE=1 ;;
    --skip-build)     SKIP_BUILD=1; SKIP_PUSH=1 ;;
    --skip-push)      SKIP_PUSH=1 ;;
    --skip-secrets)   SKIP_SECRETS=1 ;;
    --skip-apply)     SKIP_APPLY=1 ;;
    --skip-smoke)     SKIP_SMOKE=1 ;;
    --migrate-only)   SKIP_BUILD=1; SKIP_PUSH=1; SKIP_SECRETS=1; SKIP_APPLY=1; SKIP_SMOKE=1 ;;
    --build-only)     SKIP_MIGRATE=1; SKIP_SECRETS=1; SKIP_APPLY=1; SKIP_SMOKE=1 ;;
    --apply-only)     SKIP_MIGRATE=1; SKIP_BUILD=1; SKIP_PUSH=1; SKIP_SMOKE=1 ;;
    --smoke-only)     SMOKE_ONLY=1; SKIP_MIGRATE=1; SKIP_BUILD=1; SKIP_PUSH=1; SKIP_SECRETS=1; SKIP_APPLY=1 ;;
    -h|--help)
      grep -E '^# (Usage|Required|Optional|maps3d|  )' "$0" | sed 's/^# //'
      exit 0
      ;;
    *)
      echo "unknown flag: $1" >&2; exit 2 ;;
  esac
  shift
done

log()   { printf "\033[1;36m[maps3d]\033[0m %s\n" "$*"; }
warn()  { printf "\033[1;33m[maps3d WARN]\033[0m %s\n" "$*" >&2; }
fatal() { printf "\033[1;31m[maps3d FAIL]\033[0m %s\n" "$*" >&2; exit 1; }

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf "  DRY  %s\n" "$*"
  else
    printf "  RUN  %s\n" "$*"
    eval "$@"
  fi
}

# ─── Credential resolution ──────────────────────────────────────────

keychain() {
  # $1 service, $2 account
  security find-generic-password -s "$1" -a "$2" -w 2>/dev/null || true
}

resolve_creds() {
  : "${KOTOBA_URL:=$(keychain etzhayyim.rw ROOT_URL)}"
  : "${MAPILLARY_TOKEN:=$(keychain etzhayyim.mapillary ACCESS_TOKEN)}"
  : "${MURAKUMO_API_KEY:=$(keychain etzhayyim.murakumo API_KEY)}"
  : "${B2_KEY_ID:=$(keychain etzhayyim.b2 KEY_ID)}"
  : "${B2_APPLICATION_KEY:=$(keychain etzhayyim.b2 APPLICATION_KEY)}"
  : "${GHCR_USER:=$(gh api user -q .login 2>/dev/null || echo "")}"
  : "${GHCR_TOKEN:=$(gh auth token 2>/dev/null || echo "")}"
  export KOTOBA_URL MAPILLARY_TOKEN MURAKUMO_API_KEY B2_KEY_ID B2_APPLICATION_KEY GHCR_USER GHCR_TOKEN
}

require_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    fatal "$name is required (set env var or add to macOS Keychain)"
  fi
}

# ─── 1. Migrate Kotoba/Datomic schema ───────────────────────────────────

phase_migrate() {
  log "1. apply Kotoba/Datomic migration"
  require_var KOTOBA_URL
  # rw-health-gate guards against DDL during recovery / SlowDown.
  if [[ -x "$REPO/70-tools/scripts/ingest/rw-health-gate.sh" ]]; then
    log "   pre-flight: rw-health-gate"
    run "RW_URL='$KOTOBA_URL' '$REPO/70-tools/scripts/ingest/rw-health-gate.sh'"
  else
    warn "   rw-health-gate.sh not found; skipping pre-flight"
  fi
  run "cd '$REPO/30-graph/graph-schema' && pnpm db:migrate latest"
}

# ─── 2 + 3. Build + push images ─────────────────────────────────────

phase_build_push() {
  log "2/3. build + push container images"
  if ! command -v docker >/dev/null 2>&1; then
    fatal "docker not on PATH"
  fi
  if [[ "$SKIP_PUSH" == "0" ]]; then
    require_var GHCR_USER
    require_var GHCR_TOKEN
    run "echo '$GHCR_TOKEN' | docker login ghcr.io -u '$GHCR_USER' --password-stdin"
  fi
  local push_flag="--load"
  [[ "$SKIP_PUSH" == "0" ]] && push_flag="--push"

  log "   build maps3d-worker (light shared image)"
  run "docker buildx build --platform=linux/amd64 \
    -t '$WORKER_IMAGE' \
    -f '$HERE/workers/Dockerfile' '$HERE/workers' $push_flag"

  log "   build maps3d-colmap-worker (COLMAP CPU + Open3D + b2sdk)"
  run "docker buildx build --platform=linux/amd64 \
    -t '$COLMAP_IMAGE' \
    -f '$HERE/workers/Dockerfile.colmap' '$HERE/workers' $push_flag"
}

# ─── 4. Provision k8s secrets ───────────────────────────────────────

phase_secrets() {
  log "4. provision maps3d-secrets"
  require_var KOTOBA_URL
  require_var MAPILLARY_TOKEN
  require_var MURAKUMO_API_KEY
  require_var B2_KEY_ID
  require_var B2_APPLICATION_KEY
  # Create namespace first; secret creation needs it to exist.
  run "kubectl create namespace maps3d --dry-run=client -o yaml | kubectl apply -f -"
  # Apply secret idempotently — `create --dry-run=client | apply` is the
  # canonical k8s pattern for upsert.
  run "kubectl -n maps3d create secret generic maps3d-secrets \
    --from-literal=KOTOBA_URL='$KOTOBA_URL' \
    --from-literal=MAPILLARY_TOKEN='$MAPILLARY_TOKEN' \
    --from-literal=MURAKUMO_API_KEY='$MURAKUMO_API_KEY' \
    --from-literal=B2_KEY_ID='$B2_KEY_ID' \
    --from-literal=B2_APPLICATION_KEY='$B2_APPLICATION_KEY' \
    --dry-run=client -o yaml | kubectl apply -f -"
  # Image pull secret. Re-uses the GHCR creds we already resolved.
  if [[ -n "${GHCR_USER:-}" && -n "${GHCR_TOKEN:-}" ]]; then
    run "kubectl -n maps3d create secret docker-registry ghcr-pull \
      --docker-server=ghcr.io \
      --docker-username='$GHCR_USER' \
      --docker-password='$GHCR_TOKEN' \
      --dry-run=client -o yaml | kubectl apply -f -"
  else
    warn "   GHCR_USER / GHCR_TOKEN not set; skipping ghcr-pull secret (assume pre-existing)"
  fi
}

# ─── 5. Apply manifests ─────────────────────────────────────────────

phase_apply() {
  log "5. apply Deployments"
  for f in mapillary-fetcher.yaml colmap-worker.yaml langgraph-curator.yaml langgraph-actor-link.yaml; do
    run "kubectl apply -f '$HERE/$f'"
  done
  log "   wait for pods to be Ready (timeout 5 min)"
  run "kubectl -n maps3d wait --for=condition=available --timeout=300s deployment --all"
}

# ─── 6. Smoke test (Layer 2) ────────────────────────────────────────

phase_smoke() {
  log "6. run Layer 2 BPMN integration test"
  local script="$REPO/70-tools/scripts/test/maps3d-bpmn-integration.py"
  if [[ ! -x "$script" ]]; then
    fatal "Layer 2 script not found: $script"
  fi
  run "RW_URL='$KOTOBA_URL' TILE_H3='$TEST_TILE_H3' '$script'"
}

# ─── Main ───────────────────────────────────────────────────────────

main() {
  log "maps3d bring-up · tag=$IMAGE_TAG · dry_run=$DRY_RUN"
  resolve_creds

  if [[ "$SMOKE_ONLY" == "1" ]]; then
    require_var KOTOBA_URL
    phase_smoke
    log "── smoke complete ──"
    return
  fi

  [[ "$SKIP_MIGRATE" == "0" ]] && phase_migrate
  [[ "$SKIP_BUILD"   == "0" ]] && phase_build_push
  [[ "$SKIP_SECRETS" == "0" ]] && phase_secrets
  [[ "$SKIP_APPLY"   == "0" ]] && phase_apply
  [[ "$SKIP_SMOKE"   == "0" ]] && phase_smoke

  log "── all phases complete ──"
}

main "$@"
