# murakumo-mesh — distributed cluster placement contract (no VKE, no Karmada)

This directory replaces the vendor `murakumo-vke/` design (Karmada pull-mode against Vultr VKE hub). Per **ADR-2605191346**, etzhayyim runs no commercial K8s control plane. The mesh below is the canonical placement contract.

## Why this exists

The vendor murakumo at `etzhayyim.com` used Karmada v1.17 with a Vultr VKE hub cluster and a member k3s cluster on the Mac mini fleet. That topology required:

- VKE control plane (kube-apiserver, etcd, scheduler) on Vultr
- Karmada hub + member registration (PropagationPolicy CRDs)
- k3s on each Mac mini + Lima/krunkit VM shim
- WireGuard overlay (`murakumo-netd`) for pod CIDR routing
- ghcr.io image registry + per-actor Helm chart

etzhayyim murakumo drops all of that:

| Dropped | Replaced by |
|---|---|
| Vultr VKE hub | (nothing — no hub needed) |
| Karmada PropagationPolicy | `placement-contract.yaml` (this dir) + `50-infra/murakumo/fleet.toml` |
| k3s + Lima/krunkit | `launchd` + kotodama-cell-runner (`50-infra/cluster/murakumo/cell-runner/`) |
| WireGuard overlay | self-hosted **tailmesh** (X25519 + XChaCha20-Poly1305, `50-infra/cluster/murakumo/src/murakumo_mesh.rs`) |
| ghcr.io image registry | Apple Silicon native binaries (cell-runner) + ollama-pulled models |
| Helm chart per actor | Pregel cell catalog (`40-engine/kotoba/crates/kotoba-kotodama/cells/`) |

## Topology

Single fleet, no hub/member split. Every node is peer.

```
                      tailmesh control plane (peer-to-peer)
                      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬──────────┬──────┬───────────┬───────┐
   │naphtali │ simeon  │ judah   │ zebulun │ levi    │ joseph  │ issachar │ dan  │ benjamin  │ asher │
   │(charter │(steward │(land)   │(econ)   │(council │(pheno-0+│(pheno-1) │(pheno│ (force +  │ (any  │
   │ +survey)│ +ipfs)  │         │         │ +audit) │ construct│         │ -2 + │  ethics)  │  cell)│
   │         │         │         │         │         │ )        │         │decom)│           │       │
   └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴──────────┴──────┴───────────┴───────┘
                                                                                                  ▲
                                                                                                  │ replica
                                                                                                  │ of *
                       ┌───────────────────────────┐
                       │  evo-x2 (Windows LAN-only)│  Ryzen AI Max+ 395 + Radeon 8060S
                       │  Ollama + LiteLLM + ComfyUI│  (LAN-only inference, no AT membership)
                       └───────────────────────────┘
```

- **No hub cluster.** Leader election (per cell role) is swarm-based (ADR-2605191603); any node can be promoted to leader on failover, with `asher` reserved as the standing replica.
- **No member cluster.** Each Mac mini is a peer in the tailmesh. Inference pod `evo-x2` is a non-member resource consumed via LAN HTTP.
- **No PropagationPolicy.** The placement contract is `fleet.toml` + `placement-contract.yaml` (this dir). Cells declared in `fleet.toml` are launched by the per-node cell-runner; multi-LAN extension uses additional fleet entries, not a new control plane.

## Files

| File | Purpose |
|---|---|
| `topology.yaml` | Machine-readable node inventory + role labels (single-fleet schema, no hub/member). |
| `placement-contract.yaml` | Cell group → node group binding. References cells from `40-engine/kotoba/crates/kotoba-kotodama/cells/` and the fleet defined in `50-infra/murakumo/fleet.toml`. |
| `README.md` | this file. |

## Invariants

- No workload may bypass the fleet.toml/cell-runner pipeline. K8s manifests (Deployment, CronJob, DaemonSet, StatefulSet) are not authoritative in this dir — drop them on sight.
- `naphtali` / `simeon` / `judah` / `zebulun` / `levi` are role-leader nodes per ADR-2605192415 §4; do not strip their cells without an amendment ADR.
- `asher` is the standing replica (`replicas_of = ["*"]`) — never assign it primary cells.
- Inference traffic to `evo-x2` is LAN-only (192.168.1.70). The pod is **not** an AT Protocol member, has no DID, and is not addressable from public internet.
- `witness_min = 2` on `SiteSurveyCell`, `ConstructionOrchestrationCell`, `AuditWitnessCell` — constitutional invariant (ADR-2605201400 §9). Never reduce.

## Multi-LAN extension (future)

If a second LAN is added (e.g. west-coast Mac mini cell extending the religious-corp body):

1. Add a second `[[fleet]]` block in a sibling `fleet.toml` (e.g. `50-infra/murakumo/fleet-westcoast.toml`).
2. Establish tailmesh peering between the LAN gateway nodes — peers list in `~/.murakumo/peers.json`, X25519 keys per node.
3. Update `placement-contract.yaml` here with the new node group + which cells are eligible for placement on it (default: only `replica` role, then promote individually with ADR review).
4. **Do not** install Karmada / k8s federation / external etcd. The mesh stays peer-to-peer.

## Verification

```bash
# Fleet readiness (WoL + ssh)
70-tools/scripts/murakumo/wol-fleet.sh
70-tools/scripts/murakumo/ssh-fleet.sh exec uname -a

# Cell runner health on each node
50-infra/cluster/murakumo/cell-runner/deploy-fleet.sh --check

# LiteLLM gateway health
curl -fs http://127.0.0.1:4000/health/liveliness

# EVO-X2 inference reachability
curl -fs http://192.168.1.70:11434/v1/models
curl -fs http://192.168.1.70:4000/v1/models  # litellm proxy
curl -fs http://192.168.1.70:8188/system_stats  # comfyui
```

## ADR Authority

- **2605191346** — no commercial K8s
- **2605182312** — 12-tribes naming
- **2605192415** — religious-corp daemon architecture
- **2605191603** — swarm leader election
- **2605191524** — swarm broadcast
- **2605191645** — heartbeat
- **2605202345** — EVO-X2 inference backend
- **2605201400** — kuni-umi cells (witness_min invariant)

## Vendor parity (NOT in scope here)

The vendor `etzhayyim.com/etzhayyim-apps-etzhayyimcojp` keeps its `50-infra/multicluster/murakumo-vke/` (Karmada + Vultr VKE) for its own paid SaaS workloads. That topology is **not** mirrored here and **must not** be re-introduced. If religious-corp activity needs commercial cloud compute (it should not), open an ADR amending 2605191346 first.
