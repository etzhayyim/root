# fleet-to-kustomize

Project `50-infra/murakumo/fleet.toml` → kustomize overlay producing one
DaemonSet per religious-corp Pregel cell. Per [ADR-2605232100](../../90-docs/adr/2605232100-religious-corp-cells-on-k3s-daemonset.md) Stage 2.

`fleet.toml` is the placement source-of-truth. This tool is a deterministic
projection — the kustomize output is **regenerable**, not hand-edited.

## Install

```bash
cd 70-tools/fleet-to-kustomize
uv venv .venv && source .venv/bin/activate
uv pip install -e .
```

## Usage

```bash
# Dry-run (no files written) — preview which cells would be emitted.
fleet-to-kustomize --dry-run

# Single-cell emission for local orbstack validation.
fleet-to-kustomize --cell CharterAttestationRequestCell --target orbstack

# Full production emission (all non-sharded cells, leader Mac mini hostnames).
fleet-to-kustomize --target production
```

## Output layout

```
50-infra/k8s/murakumo/
├── kustomization.yaml          # root, includes all cell overlays
├── namespace.yaml              # ns/etzhayyim-cells
└── cells/
    └── {cell-name-kebab}/
        ├── kustomization.yaml
        ├── serviceaccount.yaml
        ├── service.yaml         # ClusterIP for /healthz scrape
        └── daemonset.yaml       # nodeSelector pinned to leader Mac mini
```

Apply with `kubectl apply -k 50-infra/k8s/murakumo/`.

## Stage 2 scope

Per [ADR-2605232100](../../90-docs/adr/2605232100-religious-corp-cells-on-k3s-daemonset.md)
§Migration plan, this Stage emits only **simple 1-leader-node cells**:

- Sharded cells (`PhenotypeAgent` / `UnispscAgentExecutorCell` across joseph/issachar/dan
  with `shard_index`) are **deferred** with a warning.
- Replica-of-all cells (`UnispscRegistryCell` on asher with `replicas_of: ["*"]`)
  are **deferred** with a warning.

These need follow-up work (shard-aware StatefulSet, replica leader-election
via Kubernetes Lease, etc.) tracked under Stage 6.

## How it maps fleet.toml → manifests

| fleet.toml | DaemonSet manifest |
|---|---|
| `[[nodes]] name` | `metadata.annotations[etzhayyim.com/leader-node]` |
| `[[nodes]] hostname` | `template.spec.nodeSelector[kubernetes.io/hostname]` (production target) |
| `[cells.<Name>] healthz_port` | `containerPort` + Service `port` |
| `[cells.<Name>] trigger` | annotation (informational) |
| `[cells.<Name>] listens_to` | annotation (MST NSIDs the cell subscribes to) |
| `[cells.<Name>] cron` | annotation (cron expression — actual scheduling is in-Pod) |
| `[cells.<Name>] adr` | annotation (governing ADR IDs) |

## Container

Each Pod runs:

```
python -m kotodama.cell_runner_main \
  --node <leader_node_name> \
  --cell-only <CellName>
```

The image (`ghcr.io/etzhayyim/kotodama:main` by default) carries the full
40-engine/kotoba/crates/kotoba-kotodama codebase. `cell_runner_main.py` is the per-cell entrypoint;
per ADR-2605232100 Stage 6 it will eventually be downgraded to a debug-only
path with Kubernetes Lease replacing in-process swarm leader election.

## Determinism

Two runs of `fleet-to-kustomize` on the same fleet.toml MUST produce byte-
identical output. If you see drift, file an issue — the generator is meant
to be `git diff` clean across re-runs.
