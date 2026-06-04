#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
NAMESPACE="${BUILDKIT_NAMESPACE:-buildkit}"
BUILDER="${BUILDKIT_BUILDER:-etzhayyim-vke}"
REPLICAS="${BUILDKIT_REPLICAS:-2}"
PLATFORM="${BUILDKIT_PLATFORM:-linux/amd64}"

if [[ "${NAMESPACE}" == "default" ]]; then
  echo "Refusing to create a BuildKit builder in the default namespace." >&2
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required." >&2
  exit 1
fi

if ! docker buildx version >/dev/null 2>&1; then
  echo "docker buildx is required." >&2
  exit 1
fi

kubectl apply -k "${ROOT_DIR}/50-infra/k8s/buildkit"

if docker buildx inspect "${BUILDER}" >/dev/null 2>&1; then
  docker buildx use "${BUILDER}"
else
  docker buildx create \
    --name "${BUILDER}" \
    --driver kubernetes \
    --driver-opt "namespace=${NAMESPACE},replicas=${REPLICAS},nodeselector=kubernetes.io/arch=amd64" \
    --platform "${PLATFORM}" \
    --use
fi

docker buildx inspect "${BUILDER}" --bootstrap
docker buildx ls
