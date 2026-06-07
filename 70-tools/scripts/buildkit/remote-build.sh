#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  remote-build.sh --image IMAGE --context DIR [--dockerfile PATH] [--tag TAG] [--push|--load] [--extra-arg ARG]

Examples:
  70-tools/scripts/buildkit/remote-build.sh \
    --image ghcr.io/etzhayyim/kotodama \
    --context 40-engine/kotoba/crates/kotoba-kotodama/py \
    --dockerfile 40-engine/kotoba/crates/kotoba-kotodama/py/Dockerfile

Environment:
  BUILDKIT_BUILDER       buildx builder name, default etzhayyim-vke
  BUILDKIT_PLATFORM      target platform, default linux/amd64
  BUILDKIT_CACHE_REF     registry cache ref, default ghcr.io/etzhayyim/build-cache:main
  IMAGE_TAG              explicit tag if --tag is not passed
USAGE
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BUILDER="${BUILDKIT_BUILDER:-etzhayyim-vke}"
PLATFORM="${BUILDKIT_PLATFORM:-linux/amd64}"
CACHE_REF="${BUILDKIT_CACHE_REF:-ghcr.io/etzhayyim/build-cache:main}"
PUSH_MODE="--push"
IMAGE=""
CONTEXT=""
DOCKERFILE=""
TAG="${IMAGE_TAG:-}"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      IMAGE="$2"
      shift 2
      ;;
    --context)
      CONTEXT="$2"
      shift 2
      ;;
    --dockerfile)
      DOCKERFILE="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --push)
      PUSH_MODE="--push"
      shift
      ;;
    --load)
      PUSH_MODE="--load"
      shift
      ;;
    --extra-arg)
      EXTRA_ARGS+=("$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${IMAGE}" || -z "${CONTEXT}" ]]; then
  usage >&2
  exit 1
fi

if ! docker buildx inspect "${BUILDER}" >/dev/null 2>&1; then
  echo "buildx builder '${BUILDER}' does not exist. Run setup-buildx-k8s.sh first." >&2
  exit 1
fi

if [[ -z "${TAG}" ]]; then
  SHA="$(git -C "${ROOT_DIR}" rev-parse --short HEAD)"
  ARCH="${PLATFORM##*/}"
  TAG="${SHA}-${ARCH}"
fi

if [[ "${CONTEXT}" != /* ]]; then
  CONTEXT="${ROOT_DIR}/${CONTEXT}"
fi

if [[ -n "${DOCKERFILE}" && "${DOCKERFILE}" != /* ]]; then
  DOCKERFILE="${ROOT_DIR}/${DOCKERFILE}"
fi

BUILD_ARGS=(
  docker buildx build
  --builder "${BUILDER}"
  --platform "${PLATFORM}"
  --cache-from "type=registry,ref=${CACHE_REF}"
  --cache-to "type=registry,ref=${CACHE_REF},mode=max"
  -t "${IMAGE}:${TAG}"
  "${PUSH_MODE}"
)

if [[ -n "${DOCKERFILE}" ]]; then
  BUILD_ARGS+=(-f "${DOCKERFILE}")
fi

BUILD_ARGS+=("${EXTRA_ARGS[@]}" "${CONTEXT}")

echo "Remote BuildKit builder: ${BUILDER}"
echo "Image: ${IMAGE}:${TAG}"
echo "Platform: ${PLATFORM}"
"${BUILD_ARGS[@]}"
