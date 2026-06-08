---
id: adr-2606081748-kotoba-bounded-rsi-build-deploy-contract
title: "ADR-2606081748: Kotoba bounded RSI build/deploy contract"
status: accepted
doc_type: adr
topic: kotoba-bounded-rsi-build-deploy
authoritative: true
last_verified: 2026-06-08
priority: 5.0
axis: architecture
weight: 0.72
priority_note: "Session-close decision for Kotoba RSI train/build/deploy: autonomous self-modification is allowed only inside token/cost budgets, benchmark gates, data-quality gates, and human pruning authority."
authoritative_for:
  - kotoba-rsi-build-deploy-contract
  - murakumo-modal-training-artifact-loop
  - token-bounded-self-modification
depends_on:
  - adr-2606074000-kotoba-murakumo-reintegrated-into-kotoba-submodule
  - adr-2606074500-kotoba-py-siblings-engine-core-vs-actor-placement
related:
  - adr-2605232200
  - adr-2605191346
  - adr-2605182312
supersedes: []
superseded_by: []
---

# ADR-2606081748: Kotoba bounded RSI build/deploy contract

**Status**: accepted
**Date**: 2026-06-08
**Deciders**: Jun Kawasaki

# Context

Kotoba now carries the Murakumo training loop inside the Kotoba submodule:

- `modal`-compatible Python training entrypoints.
- Kotoba artifact persistence for weights and checkpoints.
- benchmark comparison before promotion.
- training-data quality scoring and selection.
- RSI policy that allows autonomous self-modification only when bounded by token/cost budgets and explicit prune controls.

The deployment verification on 2026-06-08 exposed operational drift:

- `scripts/build-push.sh` needed an explicit platform contract for arm64 local clusters and amd64 VKE.
- `scripts/deploy.sh` had to match the manifest pull secret (`ghcr-creds`) and support image repo/tag patching.
- OrbStack local validation requires `local-path`, while VKE remains on `vultr-block-storage-hdd-retain`.
- Kubernetes resources must remain in the `kotoba` namespace; `default` namespace resource creation is prohibited.

# Decision

Adopt `40-engine/kotoba/deploy/kotoba-deploy.toml` as the human-readable operational contract for Kotoba image, namespace, profile, and verification defaults.

The active script behavior is:

- build default image repo: `ghcr.io/etzhayyim/kotoba`.
- build default platforms: `linux/amd64,linux/arm64`.
- deploy namespace: `kotoba`.
- deploy pull secret: `ghcr-creds`.
- VKE StorageClass: `vultr-block-storage-hdd-retain`.
- OrbStack StorageClass override: `KOTOBA_STORAGE_CLASS=local-path`.
- local arm64-only build override: `KOTOBA_IMAGE_PLATFORMS=linux/arm64`.

RSI is accepted as a bounded recursive self-improvement loop, not an unlimited self-modification loop:

- model promotion requires benchmark improvement or an explicit operator override.
- data admission requires quality scoring and selection.
- weights and checkpoints are persisted as Kotoba artifacts.
- token/cost budgets constrain experiment count, patch scope, and promotion attempts.
- human administrators retain pruning authority over branches, candidates, schedules, and policy knobs.

# Consequences

Kotoba can train, checkpoint, evaluate, and redeploy autonomously inside a cost-governed loop.

The TOML contract gives operators a stable place to record cluster profile defaults without relying on stale comments in Kubernetes manifests.

Local OrbStack deploys no longer require hand-editing the PVC manifest, and image tag deployment no longer depends on the manifest currently using `latest`.

Remaining known issue: the service can log a transient Tokio reactor panic during Kubo startup retry while still recovering to healthy state. This is non-blocking for the 2026-06-08 deploy but should be fixed in a follow-up runtime patch.

# Alternatives Considered

1. Unlimited self-modification.

Rejected. It removes the economic governor and the administrator's pruning ability.

2. Human-only training promotion.

Rejected. It blocks the RSI loop and turns benchmark/data-quality gates into manual paperwork.

3. Separate local and VKE manifests.

Rejected for now. The current drift is small enough for env overrides plus a single TOML contract.

# References

- `40-engine/kotoba/deploy/kotoba-deploy.toml`
- `40-engine/kotoba/scripts/build-push.sh`
- `40-engine/kotoba/scripts/deploy.sh`
- `90-docs/deployments/kotoba-260608-rsi-build-deploy-closing.md`
