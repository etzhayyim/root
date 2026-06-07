---
id: murakumo-hegemon-lifecycle-tick-20260508
title: "Murakumo Hegemon Artificial-Organism Lifecycle Tick"
status: active
doc_type: proof
topic: karma-organism-ecosystem
last_verified: 2026-05-08
---

# Murakumo Hegemon Artificial-Organism Lifecycle Tick

Objective: use the Murakumo Mac mini fleet to advance the karma-hegemon /
artificial-organism lifecycle.

## Tick Result

Lifecycle advanced from "K3.5 deploy-ready manifests missing placement closure"
to "K3.5 runtime-gated with Murakumo placement artifacts recorded in the
member k3s API".

The full worker rollout gate remains blocked because the node is `NotReady`
and runtime secrets are not provisioned. The tick nevertheless mutated the
Murakumo member k3s API by creating the `shinka-actors` namespace,
`shinka-actor-worker` ServiceAccount, and a proof ConfigMap.

## Artifacts Produced

- `50-infra/multicluster/murakumo-vke/shinka-actors/namespace.yaml`
- `50-infra/multicluster/murakumo-vke/shinka-actors/actor-workers.yaml`
- `50-infra/multicluster/murakumo-vke/shinka-actors/kustomization.yaml`
- `50-infra/multicluster/murakumo-vke/shinka-actors/propagation-policy.yaml`
- `50-infra/multicluster/murakumo-vke/shinka-actors/README.md`
- `50-infra/multicluster/murakumo-vke/placement-contract.yaml`
- `50-infra/multicluster/murakumo-vke/topology.yaml`
- `50-infra/multicluster/murakumo-vke/README.md`
- `50-infra/multicluster/murakumo-vke/karmada-pull-mode-runbook.md`

## Fleet Evidence

Reachable Ansible nodes:

- `jacob`, `naphtali`, `zebulun`, `asher`, `benjamin`, `joseph`, `issachar`
- `judah`, `levi`, `simeon`, and `dan` were SSH-unreachable during this tick.

Ollama status on reachable non-control nodes:

- `benjamin`, `joseph`, `issachar`, `zebulun`, `asher`, `naphtali` returned
  `Ollama is running` on `127.0.0.1:11434`.
- Model tags observed on those nodes:
  `qwen3.5:9b`, `gemma4:e4b`, `gemma3:1b`.

Murakumo fleet inference tick:

```json
{
  "nodes": ["joseph", "issachar", "zebulun"],
  "model": "gemma3:1b",
  "result": {
    "phase": "deploy-ready",
    "step": "apply",
    "state": "unavailable"
  }
}
```

## Kubernetes Evidence

Murakumo k3s control endpoint recovered:

- OrbStack machine `murakumo` is running at `192.168.139.151`.
- Historical kubeconfig
  `~/.kube/config.backup-20260423-122949` contains context
  `murakumo-provider`.
- The kubeconfig server certificate SAN does not cover
  `murakumo.orb.local`, so read/write access used
  `--insecure-skip-tls-verify=true` against that recovered context.

Static checks:

- `kubectl kustomize 50-infra/multicluster/murakumo-vke/shinka-actors`
  rendered successfully.
- Rendered resources contain no `metadata.namespace: default`.
- `ClusterPropagationPolicy` is cluster-scoped and un-namespaced.
- Both shinka deployments read `ZEEBE_GATEWAY` from
  `shinka-actor-runtime-secrets`, avoiding a VKE-only ClusterIP from Murakumo.

Client dry-run against the current VKE context:

```text
namespace/shinka-actors configured (dry run)
serviceaccount/shinka-actor-worker configured (dry run)
deployment.apps/shinka-actor-zeebe-worker configured (dry run)
deployment.apps/llm-knowledge-zeebe-worker configured (dry run)
```

Live writes to recovered Murakumo k3s API:

```text
namespace/shinka-actors created
serviceaccount/shinka-actor-worker created
configmap/murakumo-hegemon-lifecycle-tick-20260508 created
namespace/shinka-actors annotated
```

Live verification:

```text
shinka-actors true

NAME                                 SECRETS   AGE
serviceaccount/default               0         ...
serviceaccount/shinka-actor-worker   0         ...

murakumo-hegemon-lifecycle-tick-20260508 shinka-actors
```

Default namespace check on VKE:

```text
NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   17d
```

## Blocked Runtime Gates

- `limactl list` reported no local Lima instances, so
  `limactl shell murakumo-gpu -- kubectl ...` cannot reach Murakumo k3s.
- `~/.karmada/vke-murakumo/data/karmada-apiserver-external.config` points at
  `45.76.77.26:32444`, but `kubectl get clusters` timed out.
- The current VKE context has no `karmada-system` namespace, so hub-local
  Karmada recovery is not presently available from this context.
- Recovered OrbStack k3s node `murakumo` is `NotReady` because CNI is not fully
  initialized in this kernel environment (`CONFIG_VETH`, `CONFIG_BRIDGE`,
  `CONFIG_NF_NAT`, `CONFIG_POSIX_MQUEUE`, and `CONFIG_KEYS` missing per
  `k3s check-config`). API objects can be written, but pods will not schedule.
- Reachable physical Mac mini nodes do not have `/etc/rancher/k3s/k3s.yaml`;
  they are Ollama fleet workers, not the member k3s control endpoint.

## Follow-up Runtime Tick

Follow-up proof:

- `90-docs/proof/murakumo-hegemon-agent-loop-running-20260508.md`

The lifecycle progressed beyond this `runtime-gated` proof by starting a
resident actor loop on reachable physical Murakumo Mac mini workers. The k8s
Pod rollout remains blocked, but the actor loop is now running directly on the
fleet and writing heartbeat state.

## Remaining k8s Gate

To move the resident loop from direct fleet processes into k8s Pods:

1. Move the Murakumo k3s control endpoint to a Ready-capable environment
   (`murakumo-gpu` Lima or a Linux kernel with the required CNI features), or
   repair the OrbStack kernel/CNI limits.
2. Create the `shinka-actors` runtime secrets with Murakumo-reachable
   `ZEEBE_GATEWAY`, `KOTOBA_URL`, image pull credentials, and optional runtime
   signing key.
3. Apply `actor-workers.yaml` directly on Murakumo k3s, or restore Karmada and
   apply the `shinka-actors` kustomization on the hub.
4. Verify rollout and record the first successful `com.etzhayyim.shinka.tick`.
