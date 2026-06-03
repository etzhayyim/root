#!/usr/bin/env bash
# deploy.sh — Build, push, and deploy the RisingWave Python UDF server.
#
# Usage:
#   ./deploy.sh              # build + push + apply
#   ./deploy.sh build        # build only
#   ./deploy.sh push         # push only (assumes image exists)
#   ./deploy.sh apply        # kubectl apply only (assumes image pushed)
#
# Requires:
#   - docker (buildx for multi-arch)
#   - gh auth token (for ghcr.io push)
#   - KUBECONFIG pointing to LKE cluster
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="ghcr.io/etzhayyim/risingwave-python-udf"
TAG="${TAG:-latest}"
PLATFORM="${PLATFORM:-linux/amd64}"  # LKE node arch
BUILDER="${BUILDKIT_BUILDER:-etzhayyim-vke}"
CACHE_REF="${BUILDKIT_CACHE_REF:-ghcr.io/etzhayyim/build-cache:risingwave-python-udf}"
NAMESPACE="risingwave"
KUBECONFIG="${KUBECONFIG:-${SCRIPT_DIR}/../../50-infra/linode/risingwave-iceberg/kubeconfig.yaml}"
KUSTOMIZE_DIR="${SCRIPT_DIR}/../../50-infra/linode/risingwave-iceberg/kustomize/base"

do_login() {
  local user
  user="$(gh api user -q .login)"
  gh auth token | docker login ghcr.io -u "${user}" --password-stdin
}

do_build() {
  echo "==> Building ${IMAGE}:${TAG} for ${PLATFORM}..."
  docker buildx build --builder "${BUILDER}" --platform "${PLATFORM}" \
    --cache-from "type=registry,ref=${CACHE_REF}" \
    --cache-to "type=registry,ref=${CACHE_REF},mode=max" \
    --output=type=cacheonly \
    -t "${IMAGE}:${TAG}" "${SCRIPT_DIR}"
}

do_push() {
  echo "==> Authenticating with ghcr.io..."
  do_login
  echo "==> Building + pushing ${IMAGE}:${TAG} for ${PLATFORM}..."
  docker buildx build --builder "${BUILDER}" --platform "${PLATFORM}" \
    --cache-from "type=registry,ref=${CACHE_REF}" \
    --cache-to "type=registry,ref=${CACHE_REF},mode=max" \
    --push -t "${IMAGE}:${TAG}" "${SCRIPT_DIR}"
}

do_apply() {
  echo "==> Applying kustomize (namespace=${NAMESPACE})..."
  export KUBECONFIG
  kubectl apply -k "${KUSTOMIZE_DIR}"
  echo "==> Waiting for rollout..."
  kubectl rollout status deployment/risingwave-python-udf -n "${NAMESPACE}" --timeout=180s
  echo "==> UDF server deployed. Service: risingwave-python-udf.${NAMESPACE}.svc:8815"
}

case "${1:-all}" in
  build) do_build ;;
  push)  do_push ;;
  apply) do_apply ;;
  all)
    do_build
    do_push
    do_apply
    ;;
  *)
    echo "Usage: $0 [build|push|apply|all]" >&2
    exit 1
    ;;
esac
