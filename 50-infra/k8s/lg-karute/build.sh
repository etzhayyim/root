#!/usr/bin/env bash
# Build + push lg-karute image.
# Per ADR-2605231900.
set -euo pipefail

cd "$(dirname "$0")/../../.."

GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "dev")
IMAGE="ghcr.io/etzhayyim/lg-karute"

echo "→ Building $IMAGE:$GIT_SHA"
docker build \
  -f 50-infra/k8s/lg-karute/Dockerfile \
  -t "$IMAGE:$GIT_SHA" \
  -t "$IMAGE:main" \
  .

if [ "${1:-}" = "--push" ]; then
  echo "→ Pushing $IMAGE:$GIT_SHA + :main"
  docker push "$IMAGE:$GIT_SHA"
  docker push "$IMAGE:main"
else
  echo "ℹ Pass --push to publish to ghcr.io"
fi

echo "✓ Done. Image: $IMAGE:$GIT_SHA"
