# UNSPSC Organism Fleet — k8s Manifests

Per ADR-2605240000 (mass-deploy) + ADR-2605240100 (post sink) +
ADR-2605232100 (religious-corp cells as DaemonSet).

## Layout

```
50-infra/k8s/unispsc-organism-fleet/
├── namespace.yaml          # etzhayyim-organism namespace
├── kustomization.yaml      # root — references shard-0/1/2
└── shard-{0,1,2}/
    ├── kustomization.yaml
    ├── serviceaccount.yaml
    ├── daemonset.yaml      # pinned to joseph / issachar / dan
    └── service.yaml        # ClusterIP for /healthz
```

## Apply

```bash
# From repo root, with current kubectl context pointing at the
# Murakumo k3s cluster (Lima/OrbStack on the Mac mini fleet).
kubectl apply -k 50-infra/k8s/unispsc-organism-fleet/
```

## Verify

```bash
# Pods up?
kubectl get pods -n etzhayyim-organism -o wide

# Healthz on each shard:
kubectl exec -n etzhayyim-organism ds/unispsc-organism-fleet-shard-0 -- \
  wget -qO- localhost:13040/healthz | jq

# Or via port-forward from a workstation:
kubectl port-forward -n etzhayyim-organism svc/unispsc-organism-fleet-shard-0 13040:13040
curl -s localhost:13040/healthz | jq
```

Expected healthz fields per ADR-2605240000:

| Field | Meaning |
|---|---|
| `ownedCount` | Codes this shard claims from registry |
| `warmCount` / `warmCapacity` | LRU usage |
| `tickCount` | Sweeps completed since startup |
| `lastTickDurationMs` | Most recent sweep wall time |
| `totalPosts` | Shinka posts emitted to NDJSON queue |
| `totalClassifications` | LangGraph invokes during ticks |

## Post-sink NDJSON queue

Each shard appends Shinka posts to
`/var/lib/etzhayyim/organism-posts/shard-{N}.ndjson`. The drainer
sidecar (Wave 3, ADR-2605240100 §Drainer) is commented out of the
DaemonSet until its image is published. Until then, posts queue but
do not federate.

To inspect a live queue:

```bash
kubectl exec -n etzhayyim-organism ds/unispsc-organism-fleet-shard-0 -- \
  tail -n 5 /var/lib/etzhayyim/organism-posts/shard-0.ndjson
```

## Fallback: logger sink

If the drainer is unavailable and queue disk usage is a concern, set
the cell to log-only:

```bash
kubectl set env -n etzhayyim-organism ds/unispsc-organism-fleet-shard-0 \
  UNISPSC_ORGANISM_POST_SINK=logger
```

## Kaizen observer (ADR-2605240200)

A single observer (`kaizen-observer/` subdir) probes the three shards every
10 min, runs a rule registry (sweep-latency-p95 / lru-saturation /
error-rate / post-throughput-stalled / mood-concentration /
fleet-unreachable), and appends structured `KaizenProposal` NDJSON lines to
`/var/lib/etzhayyim/kaizen-proposals/observer.ndjson`. The PR agent (Wave 4)
reads that queue and opens PRs on github.com/etzhayyim/root.

```bash
# View recent kaizen proposals:
kubectl exec -n etzhayyim-organism deploy/kaizen-observer -- \
  tail -n 5 /var/lib/etzhayyim/kaizen-proposals/observer.ndjson | jq

# Each proposal has:
#   suggestedAction.{kind,targetFiles,patchHint,testPlan}
#   prAgentHint.{branchPrefix,labels,reviewers}
# enough for a PR agent (or a human) to act mechanically.
```

The observer's own DID is `did:web:etzhayyim.com:actor:kaizen-observer` —
once the drainer + federation ship, its proposal posts will appear on
`/profile/did:web:etzhayyim.com:actor:kaizen-observer` like any other
organism's Shinka stream.

## Local development (no k8s)

```bash
cd 40-engine/kotoba/crates/kotoba-kotodama/py
UNISPSC_ORGANISM_SHARD_ALL=1 \
UNISPSC_ORGANISM_POST_SINK=ndjson \
UNISPSC_ORGANISM_POST_QUEUE_PATH=$HOME/.etzhayyim/log/organism-posts/dev.ndjson \
  uv run python -m kotodama.organism.fleet_cell_main &
curl -s localhost:13040/healthz | jq
tail -f ~/.etzhayyim/log/organism-posts/dev.ndjson
```
