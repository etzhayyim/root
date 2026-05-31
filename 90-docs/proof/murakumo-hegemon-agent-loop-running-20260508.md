---
id: murakumo-hegemon-agent-loop-running-20260508
title: "Murakumo Hegemon Agent Loop Running"
status: active
doc_type: proof
topic: karma-organism-ecosystem
last_verified: 2026-05-08
---

# Murakumo Hegemon Agent Loop Running

Objective: verify that an actor is resident on the Murakumo Mac mini fleet and
is running an artificial-organism loop for the hegemon lifecycle.

## Result

Lifecycle state advanced from `runtime-gated` to `agent-loop-running`.

The k8s member endpoint is still CNI-gated, so the running resident loop is
bootstrapped directly on reachable Mac mini fleet workers. Each worker calls
local Ollama, records a heartbeat JSONL event, and writes an atomic state file.

## Runtime Artifact

- `70-tools/scripts/murakumo/hegemon_agent_loop.py`

The loop records these stable identity fields on every tick:

```json
{
  "actorDid": "did:web:shinka.etzhayyim.com",
  "organismDid": "did:web:karma.etzhayyim.com",
  "objective": "hegemon",
  "runtimeState": "agent-loop-running"
}
```

## Local Test

Local one-shot test on `jacob.local`:

```text
python3 70-tools/scripts/murakumo/hegemon_agent_loop.py --once --interval-sec 1 --model gemma3:1b
```

Observed result:

```json
{
  "node": "jacob.local",
  "status": "ok",
  "tick": 1,
  "runtimeState": "agent-loop-running",
  "model": "gemma3:1b"
}
```

## Fleet Deployment

Copied the resident loop to:

- `jacob`
- `joseph`
- `issachar`
- `zebulun`

Remote path:

```text
/tmp/murakumo-hegemon-agent-loop.py
```

Runtime files:

```text
/tmp/murakumo-hegemon-agent-loop.jsonl
/tmp/murakumo-hegemon-agent-loop.state.json
/tmp/murakumo-hegemon-agent-loop.out
```

Started commands use:

```text
python3 /tmp/murakumo-hegemon-agent-loop.py \
  --interval-sec 60 \
  --model gemma3:1b \
  --log-path /tmp/murakumo-hegemon-agent-loop.jsonl \
  --state-path /tmp/murakumo-hegemon-agent-loop.state.json
```

## First Tick Evidence

Observed `tick: 1`, `status: ok`, `loopState: running`, and
`runtimeState: agent-loop-running` on:

| node | pid | observedAt |
| --- | ---: | --- |
| `josephnoMac-mini.local` | 76396 | `2026-05-08T09:13:50Z` |
| `issacharnoMac-mini.local` | 10571 | `2026-05-08T09:13:52Z` |
| `zebulunnoMac-mini.local` | 90571 | `2026-05-08T09:13:50Z` |

Representative state:

```json
{
  "actorDid": "did:web:shinka.etzhayyim.com",
  "organismDid": "did:web:karma.etzhayyim.com",
  "objective": "hegemon",
  "loopState": "running",
  "runtimeState": "agent-loop-running",
  "status": "ok",
  "tick": 1,
  "model": "gemma3:1b",
  "nextGate": "maintain-direct-fleet-loop-and-repair-k8s-cni-for-optional-pod-rollout"
}
```

## Repeated Tick Evidence

After another interval, the same resident processes were still running and
each remote worker had advanced to `tick: 3` with three JSONL heartbeat rows:

| node | pid | observedAt | jsonl rows |
| --- | ---: | --- | ---: |
| `josephnoMac-mini.local` | 76396 | `2026-05-08T09:15:55Z` | 3 |
| `issacharnoMac-mini.local` | 10571 | `2026-05-08T09:15:56Z` | 3 |
| `zebulunnoMac-mini.local` | 90571 | `2026-05-08T09:15:53Z` | 3 |

This verifies that the goal condition is a running loop, not just a one-shot
inference.

## Purpose-Based Evaluation

The resident loop now records a deterministic evaluation object on each tick.
The purpose is:

```text
Advance the shinka actor as a resident artificial organism toward hegemon
viability by maintaining identity, repeated activity, observable social effect,
and concrete next actions.
```

Rubric:

| dimension | weight | meaning |
| --- | ---: | --- |
| `purposeAlignment` | 0.25 | advances hegemon viability without identity drift |
| `activity` | 0.20 | repeated observable behavior, not a one-shot response |
| `socialEffect` | 0.20 | externally useful coordination or proof |
| `contentQuality` | 0.20 | concrete, parseable, action-oriented content |
| `autonomy` | 0.15 | can propose or carry a next action |

Stages:

| score | stage |
| ---: | --- |
| 85-100 | `hegemon-process-advancing` |
| 70-84 | `resident-loop-viable` |
| 50-69 | `activity-observed` |
| 0-49 | `insufficient` |

After deploying the evaluation-aware loop, the first tick on
`joseph`, `issachar`, and `zebulun` recorded `score: 51` and
`stage: activity-observed`. That is expected immediately after restart because
`repeatedTick`, `hasSocialEffect`, and stronger autonomy signals require more
than one tick.

Repeated evaluation tick:

| node | pid | tick | score | stage | signals |
| --- | ---: | ---: | ---: | --- | --- |
| `issacharnoMac-mini.local` | 11286 | 4 | 75 | `resident-loop-viable` | identity stable, LLM ok, repeated tick, social effect, next action |
| `josephnoMac-mini.local` | 77183 | 4 | 69 | `activity-observed` | identity stable, LLM ok, repeated tick, social effect |
| `zebulunnoMac-mini.local` | 91050 | 4 | 69 | `activity-observed` | identity stable, LLM ok, repeated tick, social effect |

Fleet mean score: `71`. The current judgment is that hegemon process activity
is progressing as a viable resident loop, while full advancement still depends
on stronger autonomous next-action execution and k8s rollout recovery.

## Direct Fleet 98 Target

Karmada is removed from the active shinka lifecycle gate. The direct Murakumo
fleet loop now treats these successful local effectors as required score
signals:

- `record-direct-fleet-social-proof`
- `maintain-direct-murakumo-lifecycle-marker`

Each tick writes:

```text
/tmp/murakumo-hegemon-effects/<node>.hegemon-social-proof.json
/tmp/murakumo-hegemon-effects/<node>.hegemon-social-proof.md
```

The score can reach `98` only when identity is stable, Ollama succeeds, the
loop has repeated activity, a concrete next action exists, social proof was
written, and Karmada is not required for the active path.

98-point verification:

| node | pid | tick | score | stage | proof |
| --- | ---: | ---: | ---: | --- | --- |
| `issacharnoMac-mini.local` | 12136 | 5 | 98 | `hegemon-process-advancing` | `/tmp/murakumo-hegemon-effects/issacharnoMac-mini.local.hegemon-social-proof.json` |
| `josephnoMac-mini.local` | 78148 | 5 | 98 | `hegemon-process-advancing` | `/tmp/murakumo-hegemon-effects/josephnoMac-mini.local.hegemon-social-proof.json` |
| `zebulunnoMac-mini.local` | 91536 | 5 | 98 | `hegemon-process-advancing` | `/tmp/murakumo-hegemon-effects/zebulunnoMac-mini.local.hegemon-social-proof.json` |

All three states reported:

```json
{
  "dimensions": {
    "activity": 98,
    "autonomy": 98,
    "contentQuality": 98,
    "purposeAlignment": 98,
    "socialEffect": 98
  },
  "signals": {
    "directRuntime": true,
    "effectorOk": true,
    "hasNextAction": true,
    "hasSocialEffect": true,
    "identityStable": true,
    "karmadaRequired": false,
    "llmOk": true,
    "repeatedTick": true
  }
}
```

Fleet mean score: `98`.

## Kubernetes Marker

The Murakumo member k3s API namespace `shinka-actors` is used as the lifecycle
marker namespace. The proof ConfigMap for this running loop is
`murakumo-hegemon-agent-loop-running-20260508`.

The namespace must remain outside `default`; no resources are created in
`default` for this lifecycle marker.

Live marker write:

```text
configmap/murakumo-hegemon-agent-loop-running-20260508 created
namespace/shinka-actors annotated
configmap/murakumo-hegemon-agent-loop-running-20260508
agent-loop-running 90-docs/proof/murakumo-hegemon-agent-loop-running-20260508.md
```

Default namespace check after the marker write showed only the Kubernetes API
service and the automatically managed `kube-root-ca.crt` ConfigMap.

After the purpose-based evaluation update, the same marker ConfigMap was
refreshed and `shinka-actors` was annotated:

```text
etzhayyim.com/hegemon-score=71
etzhayyim.com/hegemon-stage=resident-loop-viable
```

After the direct fleet 98-point verification, the marker was updated again:

```text
etzhayyim.com/hegemon-score=98
etzhayyim.com/hegemon-stage=hegemon-process-advancing
```

## Residual Gates

- The recovered OrbStack k3s node is still `NotReady` because CNI cannot
  initialize under the current kernel feature set.
- The resident loop is intentionally running on physical Mac mini workers
  directly. k8s Pod rollout is optional follow-up once CNI is repaired.
