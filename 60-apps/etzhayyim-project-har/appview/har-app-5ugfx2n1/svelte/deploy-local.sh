#!/bin/bash
set -e

# Configuration
REGISTRY="ghcr.io"
IMAGE_NAME="etzhayyim-har"
PLATFORM="linux/amd64"
BUILDER="${BUILDKIT_BUILDER:-etzhayyim-vke}"
CACHE_REF="${BUILDKIT_CACHE_REF:-ghcr.io/etzhayyim/build-cache:etzhayyim-har}"

echo "🚀 Starting local build for ${IMAGE_NAME}..."

# 1. Build SvelteKit application
echo "📦 Building SvelteKit app..."
pnpm build

# 2. Build and Push Docker image
echo "🐳 Building and Pushing Docker image (@${PLATFORM})..."
# Generate a unique tag or use latest, but we need the digest
docker buildx build --builder "${BUILDER}" --platform "${PLATFORM}" \
  --cache-from "type=registry,ref=${CACHE_REF}" \
  --cache-to "type=registry,ref=${CACHE_REF},mode=max" \
  --push -t "${REGISTRY}/${IMAGE_NAME}:latest" -f Dockerfile.static .

# 3. Get the digest
DIGEST=$(docker buildx imagetools inspect "${REGISTRY}/${IMAGE_NAME}:latest" --format '{{.Manifest.Digest}}')

if [ -z "$DIGEST" ]; then
    echo "❌ Failed to get image digest."
    exit 1
fi

echo "✅ Image digest: ${DIGEST}"

# 4. Update manifests
echo "📝 Updating Kubernetes manifests..."

# Update kustomization.yaml
if [ -f "k8s/kustomization.yaml" ]; then
    sed -i '' "s/digest: sha256:.*/digest: ${DIGEST}/" k8s/kustomization.yaml || echo "kustomization.yaml digest update skipped"
fi

# Update deployment.yaml
if [ -f "k8s/deployment.yaml" ]; then
    sed -i '' "s|image: ${REGISTRY}/${IMAGE_NAME}@sha256:.*|image: ${REGISTRY}/${IMAGE_NAME}@${DIGEST}|" k8s/deployment.yaml
fi

echo "✨ Manifests updated. Ready to commit and push."
echo "Run: git add k8s/ && git commit -m \"deploy: update ${IMAGE_NAME} to ${DIGEST}\" && git push origin main"
