# BuildKit Remote Build

This directory owns the Kubernetes namespace used by the Docker buildx
Kubernetes driver. BuildKit builder pods are created by `docker buildx`, not by
this kustomization.

## Setup

```sh
kubectl apply -k 50-infra/k8s/buildkit
70-tools/scripts/buildkit/setup-buildx-k8s.sh
```

The setup script creates a local buildx builder named `etzhayyim-vke` that runs
BuildKit pods in the `buildkit` namespace.

## Build

```sh
70-tools/scripts/buildkit/remote-build.sh \
  --image ghcr.io/etzhayyim/kotodama \
  --context 40-engine/kotoba/crates/kotoba-kotodama/py \
  --dockerfile 40-engine/kotoba/crates/kotoba-kotodama/py/Dockerfile
```

The wrapper uses the remote `etzhayyim-vke` builder, targets `linux/amd64`, and
imports/exports registry cache by default:

```sh
--cache-from type=registry,ref=${BUILDKIT_CACHE_REF:-ghcr.io/etzhayyim/build-cache:main}
--cache-to   type=registry,ref=${BUILDKIT_CACHE_REF:-ghcr.io/etzhayyim/build-cache:main},mode=max
```

Prefer workload-specific cache refs for repeated deploy paths:

```sh
BUILDKIT_CACHE_REF=ghcr.io/etzhayyim/build-cache:kotodama \
  IMAGE_TAG="$(git rev-parse --short HEAD)-amd64" \
  70-tools/scripts/buildkit/remote-build.sh \
    --image ghcr.io/etzhayyim/kotodama \
    --context 40-engine/kotoba/crates/kotoba-kotodama/py \
    --dockerfile 40-engine/kotoba/crates/kotoba-kotodama/py/Dockerfile
```

Only bypass cache when diagnosing a confirmed stale-layer issue:

```sh
IMAGE_TAG="$(git rev-parse --short HEAD)-amd64" \
  70-tools/scripts/buildkit/remote-build.sh \
    --image ghcr.io/etzhayyim/kotodama \
    --context 40-engine/kotoba/crates/kotoba-kotodama/py \
    --dockerfile 40-engine/kotoba/crates/kotoba-kotodama/py/Dockerfile \
    --extra-arg --no-cache
```

Useful environment overrides:

- `BUILDKIT_BUILDER`: buildx builder name, default `etzhayyim-vke`
- `BUILDKIT_NAMESPACE`: Kubernetes namespace, default `buildkit`
- `BUILDKIT_PLATFORM`: target platform, default `linux/amd64`
- `BUILDKIT_CACHE_REF`: registry cache ref, default
  `ghcr.io/etzhayyim/build-cache:main`. Workload scripts should use stable
  per-image tags such as `ghcr.io/etzhayyim/build-cache:maps-bulk-ingest`.
- `IMAGE_TAG`: explicit image tag. Defaults to
  `<git-sha>-<platform-arch>`.

Do not create BuildKit resources in the Kubernetes `default` namespace.
Do not use local `docker build` for VKE-targeted images from Mac hosts.
Do not use OrbStack/Rosetta as a fallback for deploy builds. If `etzhayyim-vke` is
unavailable, repair the remote builder or stop the deploy instead of switching
to a local builder.

## Verify

```sh
docker buildx ls
kubectl get pods -n buildkit -o wide
```

Expected: `etzhayyim-vke` uses the `kubernetes` driver and BuildKit pods are
`Running` in the `buildkit` namespace.
