---
id: 2605232100-religious-corp-cells-on-k3s-daemonset
title: "ADR-2605232100: religious-corp Pregel cells runtime — launchd → k3s DaemonSet on Mac mini fleet"
status: proposed
doc_type: adr
topic: cell-runtime
authoritative: true
last_verified: 2026-05-23
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "religious-corp daemon runtime upgrade — stateful Pregel cells need DaemonSet semantics that launchd cannot express"
authoritative_for:
  - religious-corp Pregel cell runtime decision
  - fleet.toml `control_plane` field SoT
  - lg-open-unispsc substrate decontamination scope
depends_on:
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
related:
V05182312-local-bring-up-murakumo-gemma4
V05171300
supersedes: []
superseded_by: []
---

# ADR-2605232100: religious-corp Pregel cells runtime — launchd → k3s DaemonSet on Mac mini fleet

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

## Context

ADR-2605191346 §3 established a tiered runtime policy: native daemon (launchd/systemd) preferred for stateless loops, K3s HA on 3 Mac minis allowed for "HA stateful services". At the time of writing, religious-corp Pregel cells (`CharterAttestationRequestCell`, `TitheRoutingCell`, `LandStewardshipMonitoringCell`, etc.) were treated as the stateless loop case → `control_plane = "launchd (macOS) — no commercial K8s per ADR-2605191346"` in `50-infra/murakumo/fleet.toml:19`.

The 2026-05-20 → 2026-05-23 implementation wave proved this classification wrong. Each cell is in fact **stateful in three independent dimensions**:

1. **kotoba-datomic-chain state** (ADR-2605231400 §2). Each cell maintains an atproto PDS MST source chain. Crash mid-commit must be recoverable without losing the chain head.
2. **MstCheckpointSaver state** (ADR-2605171800, ADR-2605191559). LangGraph Pregel checkpoint frames are streamed over Unix socket to the `@etzhayyim/sdk` MstCheckpointSaver sidecar, then projected to CAR + IPFS pin + L2 anchor. Loss of the sidecar mid-frame produces a half-anchored MST root.
3. **kotoba-datomic-witness quorum state** (ADR-2605231400 §5). Each cell is a validator candidate for 1/N of all records (N=fleet size). Witness selection is deterministic on `record_cid`, so cell death = quorum unavailable for that record's witness shard until restart.

launchd's process-group model cannot express these requirements cleanly:

- No declarative `nodeSelector` — cell↔node pinning lives implicitly in `--node <name>` argv parsing inside `cell_runner_main.py`
- No rolling update — cell-key rotation (90-day cadence per `fleet.toml:24`) requires manual plist regeneration on each node
- No readiness gate — sidecar (`@etzhayyim/sdk` checkpointer Unix socket) may not be live when the cell's first MST commit fires
- No cross-node coordinated lease — swarm leader election (ADR-2605191603) re-implements primitives k8s already provides via Lease objects
- No structured liveness — heartbeat protocol (ADR-2605191645) is bespoke HTTP poll on `:13000/healthz`, no integration with control-plane health

Parallel evidence: `50-infra/k8s/etzhayyim-organism/` has been running the CNS daemon as a Pod on orbstack k8s for 24+ hours without incident, and `50-infra/k8s/lg-open-unispsc/deployment.yaml` already specifies a complete Deployment manifest for the 18,342 UNSPSC agent XRPC façade (currently unapplied because it carries an ADR-2605172000 violation — see §Decision item 3).

Additional constraint discovered 2026-05-23: the lg-open-unispsc manifest references `secretKeyRef: mitama-udf-pool-rw / KOTOBA_URL` for both `KOTOBA_URL` and `DATABASE_URL` env vars, plus `RW_SYNC_POOL=1`. This is a direct violation of ADR-2605172000 (kotoba substrate). Inspection of `kotodama/langgraph_server_app.py` shows the RW dependency is confined to the `/readyz` DB probe (line 670-687); the XRPC façade itself, the UNSPSC graph registry, and the invoke pipeline never touch Kotoba/Datomic. The contamination is therefore probe-only and removable without functional regression.

## Decision

**(1) religious-corp Pregel cells (per ADR-2605192415 §4) run as Kubernetes Pods on a k3s control plane spanning the Mac mini fleet.** Native launchd is retained only for Tier-2 host-resident user daemons (ameno-daemon, agent_daemon_main) per ADR-2605191346 §3 unchanged.

**(2) `50-infra/murakumo/fleet.toml` remains the placement source-of-truth.** A generator (`70-tools/fleet-to-kustomize/`, follow-up implementation) projects fleet.toml → `kustomize` overlay producing one `DaemonSet` per cell with `nodeSelector: kubernetes.io/hostname=<node>.local` and `tolerations` matching the 12-tribes node taints. fleet.toml schema additions:

```toml
[fleet]
control_plane = "k3s (Lima/OrbStack on Mac mini fleet) — religious-corp cells per ADR-2605232100"
# launchd retained for Tier-2 host-resident daemons (ameno-daemon, agent_daemon_main) per ADR-2605191346 §3
adr = ["2605192415", "2605191346", "2605182312", "2605211910", "2605171300", "2605232100"]
```

**(3) `50-infra/k8s/lg-open-unispsc/deployment.yaml` is decontaminated** in the same change set:

- Remove env vars `KOTOBA_URL`, `DATABASE_URL`, `RW_SYNC_POOL` and the `mitama-udf-pool-rw` secretRef
- Switch readinessProbe target from `/xrpc/com.etzhayyim.apps.unispsc.health` (which transitively touches RW via `/readyz`) to `/healthz` (graph registry counts only, no DB)
- Add env vars `ETZ_SUBSTRATE=kotoba-datomic`, `ETZ_CHECKPOINTER_SOCKET=/run/etzhayyim/checkpointer.sock` as forward-compatible markers for Stage 2 (Pod sidecar wiring of `@etzhayyim/sdk` MstCheckpointSaver — not in this ADR scope)
- Comment-link the new ADR ID in the manifest header

**(4) ADR-2605191346 §3 classification is updated by reference.** religious-corp Pregel cells are now classified as "HA stateful service" not "stateless agent loop". Native daemon path remains valid for ameno-daemon (Path A/B per ADR-2605191229/2605191257) and other user-host daemons.

**(5) No commercial K8s.** ADR-2605191346 §1 hard rule (Vultr / EKS / GKE / AKS / DOK forbidden for etzhayyim/*) is unchanged. The k3s control plane runs on Mac mini fleet via Lima or OrbStack (self-hosted), not on cloud K8s.

## Consequences

### Positive

- Cell↔node pinning becomes declarative (`fleet.toml` + generated kustomize) — readable from one file instead of inferring from 10 launchd plists
- Sidecar dependency expressible as Pod initContainer/readinessProbe → MstCheckpointSaver Unix socket guaranteed before first MST commit
- Rolling cell-key rotation (90-day cadence) becomes `kubectl rollout restart daemonset/<cell>` — no per-node SSH
- Swarm leader election (ADR-2605191603) collapses into Kubernetes Lease objects → ~200 LoC removable from cell_runner_main.py
- kotoba-datomic-witness availability tracked via DaemonSet `status.numberReady` — quorum can self-detect degraded fleet
- `50-infra/k8s/lg-open-unispsc/` becomes immediately applyable for the 18,342 UNSPSC agent XRPC façade

### Negative

- New runtime surface (k3s) on every Mac mini — requires Lima/OrbStack Linux VM per node, +~2 GB RAM per VM
- One-time migration cost: 10 Mac minis × Lima provision + k3s join + DaemonSet apply
- `cell_runner_main.py` is not removed but downgraded to a local-dev fallback path (single-cell `--cell-only` invocation for debug) — implementation cleanup is follow-up
- Loss of macOS native API access from inside cells (Metal, CoreML, AppleScript). Religious-corp cell catalog (ADR-2605192415) does not use these today, but capability boundary is now Linux-only inside Pods

### Neutral

- fleet.toml schema is additive (new `control_plane` text) — no consumer breakage
- ADR-2605191346 §3 native-daemon path stays valid for non-religious-corp ameno-daemon — no contradiction with parent ADR

## Alternatives Considered

| Option | Rejected because |
|---|---|
| Stay on launchd, add per-cell file-lock leader election + plist generator | Re-implements k8s primitives (Lease, DaemonSet, rolling update) in bash + Python. Maintenance debt without parity. |
| Use Holochain conductor (`50-infra/holochain/`) as cell runtime | ADR-2605231400 §README explicitly states kotoba-datomic is built *independently of* Holochain — adopting the actual conductor would contradict that decision and re-introduce a non-kotoba-datomic runtime |
| Cell as systemd unit on Linux VM (no k3s above it) | Same gap as launchd — no declarative placement, no rolling update primitive, no Lease object |
| Move cells to murakumo-kubelet GPU bursts | murakumo-kubelet is for bursty GPU compute (ADR-2605110100, vendor monorepo) — religious-corp cells are long-lived CPU daemons; mismatch |

## Migration plan (out of scope for this ADR — Stage 1+ work)

1. **Stage 1 (this ADR)**: ADR text + fleet.toml `control_plane` update + lg-open-unispsc RW decontamination patch ✅ 2026-05-23
2. **Stage 2**: `70-tools/fleet-to-kustomize/` generator + first DaemonSet apply for `CharterAttestationRequestCell` on orbstack (single-node validation) ✅ 2026-05-23
3. **Stage 3 (revised 2026-05-23)**: Fleet-wide k3s bring-up via the **existing Ansible playbook** at `60-apps/etzhayyim-project-murakumo/ansible/k8s-gpu-cluster.yml`. `50-infra/k8s/lima-k3s/bring-up.sh` is a local 3-VM smoke-test on the developer host only — NOT the production path. Operator commands (from jacob):

   ```bash
   cd 60-apps/etzhayyim-project-murakumo/ansible
   ansible-playbook k8s-gpu-cluster.yml --tags=tools       # host toolchain (Lima, k3s installer)
   ansible-playbook k8s-gpu-cluster.yml --tags=preflight   # prerequisite checks
   MURAKUMO_K3S_TOKEN="$(openssl rand -hex 32)" \
   ansible-playbook k8s-gpu-cluster.yml --tags=bootstrap   # one Lima VM per Mac mini → k3s join over WireGuard wg0
   ```

   `lima_k3s_gpu` role (`roles/lima_k3s_gpu/`) implements `tools / preflight / bootstrap / deploy_llama_vulkan` modes. Cross-VM pod networking goes over WireGuard (`wg0`) with k3s `node-ip` and flannel both bound to `wg0` — set up by the playbook, not the operator. Inventory at `60-apps/etzhayyim-project-murakumo/ansible/inventory/hosts.yml` covers `jacob` (control plane, 127.0.0.1) + 10 tribe nodes.
4. **Stage 4**: `kubectl apply -k 50-infra/k8s/murakumo/` rolls out all 15 religious-corp cells per fleet.toml placement (target = `production`, no `--target orbstack` override).
5. **Stage 5**: `lg-open-unispsc` apply + verify 18,342 UNSPSC agents resolvable via `/xrpc/com.etzhayyim.apps.unispsc.invokeAgent` ✅ 2026-05-23 (on orbstack; production fleet pending Stage 3).
6. **Stage 6**: `cell_runner_main.py` retired to debug-only path, swarm leader election code deleted in favor of Kubernetes Lease.

### Why two k3s paths exist in the repo (clarification, 2026-05-23)

| Path | Purpose | Production use? |
|---|---|---|
| `60-apps/etzhayyim-project-murakumo/ansible/` | **The real fleet bootstrapper.** One Lima VM per Mac mini, joined into one k3s cluster over WireGuard. Inventory-driven, idempotent, includes preflight + tools + bootstrap + GPU workload deploy. | ✅ Stage 3 production path |
| `50-infra/k8s/lima-k3s/bring-up.sh` | Local 3-VM smoke test on the developer host (`k3s-server-01..03`, embedded etcd HA on one machine). Validates k3s manifests before they hit the fleet. | ❌ Dev/test only — does NOT touch Mac minis |

The first ADR draft (2026-05-23 morning) cited `bring-up.sh` as the Stage 3 path, which was wrong. The Ansible playbook is the source-of-truth and has been in place since the Murakumo Mac mini fleet was provisioned. fleet.toml `[fleet] ansible_playbook` now records this explicitly.

## References

- ADR-2605191346 — Vultr-free / no commercial K8s (Tier-1 substrate parent rule)
- ADR-2605192415 — religious-corp daemon architecture (cell catalog source)
- ADR-2605172000 — kotoba substrate (justifies lg-open-unispsc decontamination)
- ADR-2605171800 — LangGraph → MST → IPFS → L2 pipeline (defines stateful invariant)
- ADR-2605231400 — kotoba-datomic Holochain-iso substrate (defines witness quorum requirement)
- `50-infra/murakumo/fleet.toml` — cell placement SoT
- `50-infra/k8s/lg-open-unispsc/deployment.yaml` — UNSPSC façade manifest (patched in this ADR scope)
- `50-infra/k8s/etzhayyim-organism/deployment.yaml` — existing Pod-based daemon precedent (CNS, 24h+ Running)
- `60-apps/etzhayyim-project-murakumo/ansible/k8s-gpu-cluster.yml` — **Stage 3 production playbook** (one Lima VM per Mac mini, WireGuard overlay, ansible-driven)
- `60-apps/etzhayyim-project-murakumo/ansible/inventory/hosts.yml` — fleet inventory SoT (jacob + 10 tribe nodes)
- `60-apps/etzhayyim-project-murakumo/ansible/roles/lima_k3s_gpu/` — k3s role (tools / preflight / bootstrap / deploy_llama_vulkan)
- `50-infra/k8s/lima-k3s/bring-up.sh` — **local 3-VM smoke test only**, not the fleet bootstrapper (clarified in Stage 3 above)
- `20-actors/etzhayyim-sdk/src/checkpointer.ts` — MstCheckpointSaver sidecar (Pod sidecar target)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runner_main.py` — legacy launchd entrypoint (downgraded to debug-only post-Stage 6)
