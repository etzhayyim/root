# Kotoba RSI build/deploy closing — 2026-06-08

## Scope

Close-out for the Kotoba bounded RSI implementation and deployment loop:

- Murakumo/modal-compatible training path inside Kotoba.
- Kotoba artifact persistence for weights and checkpoints.
- benchmark and data-quality gates for promotion.
- token/cost-bounded RSI policy with human pruning authority.
- GHCR image build and Kubernetes deploy verification.

## Build

Verified build target:

- image: `ghcr.io/etzhayyim/kotoba:1409dc2dbd`
- local pushed manifest: `linux/arm64`
- digest: `sha256:e4fd3216d509beea0536e9475f3593484f0f7db33626a3c111a67a59dd00fd1f`

The multi-arch build path is the default contract. During the local verification pass, BuildKit stalled on multi-arch and was restarted; the final deploy used an arm64-only push for the OrbStack cluster.

## Deploy

Verified deploy target:

- context: `orbstack`
- namespace: `kotoba`
- deployment: `deployment/kotoba`
- image: `ghcr.io/etzhayyim/kotoba:1409dc2dbd`
- readiness: `1/1`
- pod state: `2/2 Running`
- local health URL: `http://127.0.0.1:18080/health`

Default namespace audit: no application resource was created in `default`; only the Kubernetes API service was present.

## Script Closure

The operational drift found during deploy was codified:

- `scripts/build-push.sh` supports `KOTOBA_IMAGE_REPO` and `KOTOBA_IMAGE_PLATFORMS`.
- `scripts/deploy.sh` supports `KOTOBA_NAMESPACE`, `KOTOBA_IMAGE_REPO`, `KOTOBA_IMAGE_PULL_SECRET`, and `KOTOBA_STORAGE_CLASS`.
- `deploy/kotoba-deploy.toml` records the VKE and OrbStack profile contract.

## Open Follow-Up

The pod can emit a transient startup panic while Kubo is still unavailable:

`there is no reactor running`

Health recovers to `status=ok`, so this is not a blocker for this deploy, but the retry path should be moved under a Tokio runtime or made fully synchronous in a follow-up patch.
