---
id: buildx-remote-build-only
title: Container builds use remote buildx BuildKit
status: active
doc_type: adr
topic: k8s-image-build
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - k8s-image-build
  - buildx-remote-build
  - local-build-policy
related:
  - buildkit-k8s-remote-build
  - 50-infra-k8s-buildkit-readme
supersedes: []
superseded_by: []
---

# Context

VKE workloads run on `linux/amd64`. Local Mac builds and OrbStack/Rosetta
fallbacks can produce host-specific behavior, consume local CPU/disk, and hide
the actual BuildKit/Kubernetes path that production deploys depend on.

The repository already has a Kubernetes-driver `docker buildx` builder:

- builder: `etzhayyim-vke`
- driver: `kubernetes`
- namespace: `buildkit`
- platform: `linux/amd64`
- cache: GHCR registry cache via `BUILDKIT_CACHE_REF`
- wrapper: `70-tools/scripts/buildkit/remote-build.sh`

# Decision

All future container image builds for VKE-targeted or production deploy
workloads MUST use remote buildx BuildKit through `etzhayyim-vke`.

Canonical command:

```sh
70-tools/scripts/buildkit/remote-build.sh \
  --image ghcr.io/etzhayyim/<name> \
  --context <dir> \
  --dockerfile <dir>/Dockerfile
```

Workload scripts may call `docker buildx build` directly only when they set the
same remote builder contract explicitly:

```sh
docker buildx build \
  --builder etzhayyim-vke \
  --platform linux/amd64 \
  --cache-from type=registry,ref="${BUILDKIT_CACHE_REF}" \
  --cache-to type=registry,ref="${BUILDKIT_CACHE_REF}",mode=max \
  --push
```

OrbStack, local Docker Desktop, and Mac-host local `docker build` / local
`docker buildx` builders are not accepted fallback paths for deploy builds. If
`etzhayyim-vke` is unavailable, fix the remote builder or stop the deploy; do not
switch to OrbStack/Rosetta as a workaround.

# Consequences

- Build failures surface in the same remote BuildKit path used by deploys.
- amd64 image behavior is tested at build time instead of inferred from a Mac
  host.
- Local machines no longer need to keep OrbStack running for repository build
  work.
- Cache behavior is centralized in GHCR registry cache refs.

# Alternatives Considered

- Keep OrbStack/Rosetta as an emergency fallback: rejected because it creates a
  second build path and makes failures harder to reproduce.
- Allow local `docker buildx` for one-off deploys: rejected for production
  deploys. Local builds may still be used outside this policy for unrelated
  personal experiments that do not produce deploy images.

# References

- `50-infra/k8s/buildkit/README.md`
- `70-tools/scripts/buildkit/remote-build.sh`
- `deps.toml` convention `buildkit-k8s-remote-build`
