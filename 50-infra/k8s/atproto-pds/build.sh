#!/usr/bin/env bash
# atproto PDS — Bun container build (ADR-2605111300, Phase P1).
# Uses remote BuildKit on VKE (etzhayyim-vke builder).
#
# Usage:
#   50-infra/k8s/atproto-pds/build.sh                   # build + push :bun-canary
#   50-infra/k8s/atproto-pds/build.sh v1                # build + push :bun-v1
#   50-infra/k8s/atproto-pds/build.sh canary --load     # build + load into local Docker (no push)

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
TAG_SUFFIX="${1:-canary}"
TAG="bun-${TAG_SUFFIX}"
PUSH_MODE="--push"
if [[ "${2:-}" == "--load" || "${2:-}" == "--no-push" ]]; then
  PUSH_MODE="--load"
fi

export BUILDKIT_CACHE_REF="ghcr.io/etzhayyim/build-cache:atproto-pds-bun"

cd "$REPO_ROOT"

echo "[atproto-pds build] image=ghcr.io/etzhayyim/atproto-pds tag=${TAG} mode=${PUSH_MODE}"

exec "$REPO_ROOT/70-tools/scripts/buildkit/remote-build.sh" \
  --image ghcr.io/etzhayyim/atproto-pds \
  --tag "$TAG" \
  --context "$REPO_ROOT" \
  --dockerfile 50-infra/k8s/atproto-pds/Dockerfile \
  "$PUSH_MODE"
