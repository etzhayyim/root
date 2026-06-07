---
id: adr-2605240200-unispsc-organism-kaizen-self-reflection
title: "ADR-2605240200: UNSPSC organism ecosystem self-reflection — KaizenObserverCell + PR-agent contract"
status: proposed
doc_type: adr
topic: unispsc-organism-kaizen
authoritative: true
last_verified: 2026-05-24
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Closes the loop: the organism ecosystem observes its own runtime (healthz + post queue + classification stream), emits structured KaizenProposal records, and hands them to a downstream PR agent (separate process; human-or-agent review). The observer is itself an actor in the ecosystem with its own DID, profile page, and proposal stream — so kaizen is part of the system's history, not external operator state."
authoritative_for:
  - KaizenObserverCell architecture
  - KaizenProposal NDJSON schema (v1)
  - PR-agent consumer contract
  - rule registry for built-in observations
depends_on:
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605240000-unispsc-organism-fleet-mass-deploy
  - adr-2605240100-unispsc-organism-post-sink-substrate-bridge
related:
  - adr-2605240015-unispsc-organism-joucho-personality
  - adr-2605240030-unispsc-organism-followers
supersedes: []
superseded_by: []
---

# ADR-2605240200: KaizenObserver — ecosystem self-reflection + PR agent contract

**Status**: proposed
**Date**: 2026-05-24
**Deciders**: Jun Kawasaki

# Context

The Wave 1-3 implementation made 18,342 UNSPSC actors organism-shaped
(joucho mood + heartbeat cadence + Shinka post queue). What is still
missing is the **inward-pointing eye**: nothing in the ecosystem
observes itself. Operators have to (a) port-forward to /healthz,
(b) tail NDJSON queues, (c) read the profile pages, (d) decide on
improvements, (e) hand-code the fix or open an issue.

The user's framing is direct: _"this observation and kaizen loop should
also be part of the artificial ecosystem"_. So:

1. The observer is an actor — has a DID, a profile, a tick cadence, a
   post stream. Its posts are kaizen proposals.
2. The proposals are append-only records on the same NDJSON-queue
   substrate the organism posts use (ADR-2605240100). Drainer (or PR
   agent) reads them.
3. Auto-action is bounded by user policy: **observer emits proposals
   and a PR; the PR is reviewed by a separate agent or human.** The
   observer does not directly mutate constitutional state.

# Decision

## Actor identity

The observer is one actor with DID
`did:web:etzhayyim.com:actor:kaizen-observer`. Its tick cadence is
**cron-driven, not joucho-driven** — observations should be regular and
predictable, independent of mood. (Joucho-driven cadence is appropriate
for emotional actors; ops self-reflection is not emotional.)

Default tick: every 10 minutes. Configurable via env.

## KaizenObserverCell

A new cell type. Cron-trigger, no per-shard placement (one observer for
the whole fleet, runs on `levi` per Murakumo membership/orchestration
role). Module: `kotodama.organism.kaizen_cell_main`.

Each tick:

1. **Probe**: GET `/healthz` on each shard (joseph:13040 / issachar:13050
   / dan:13060). Collect `tickCount`, `lastTickDurationMs`, `totalPosts`,
   `totalErrors`, `warmCount`, etc.
2. **Read queue tail**: read last N=1000 lines of each shard's NDJSON
   post queue (`/var/lib/etzhayyim/organism-posts/shard-*.ndjson`).
   Compute mood distribution, content-source-kind distribution, code
   diversity, post-rate.
3. **Run rules**: pluggable rule registry. Each rule consumes an
   `Observation` and returns 0+ `KaizenProposal`s.
4. **Emit**: append each proposal as one NDJSON line to
   `/var/lib/etzhayyim/kaizen-proposals/observer.ndjson`. Schema below.

## KaizenProposal schema (v1)

```json
{
  "v": 1,
  "ts": 1748131234567,
  "kind": "kaizen-proposal",
  "ruleId": "sweep-latency-p95",
  "category": "performance",
  "severity": "warn",
  "actorScope": "shard:1",
  "summary": "shard-1 sweep p95 = 8.2s (target ≤ 1s)",
  "detail": "Over the last 24 ticks issachar's tick durationMs has averaged 8,150 ms, well above the 1,000 ms budget set in ADR-2605240000 §Capacity math. Likely cause: LRU thrashing — warmCount oscillates between 4,096 and 8,192 every tick.",
  "evidence": {
    "shard": 1,
    "tickDurationMsP50": 7900,
    "tickDurationMsP95": 8200,
    "warmCount": 4096,
    "warmCapacity": 4096,
    "ownedCount": 8541,
    "windowTicks": 24
  },
  "suggestedAction": {
    "kind": "config-change",
    "description": "Increase LRU_MAX from 4096 to 16384 on shard-1.",
    "targetFiles": ["50-infra/k8s/unispsc-organism-fleet/shard-1/daemonset.yaml"],
    "patchHint": "env UNISPSC_ORGANISM_LRU_MAX: \"4096\" → \"16384\"",
    "testPlan": [
      "Re-apply manifest, wait 30 min, verify warmCount stabilizes at >8000",
      "Verify tickDurationMsP95 < 1000",
      "Verify memory usage < limits.memory (6Gi)"
    ]
  },
  "prAgentHint": {
    "branchPrefix": "kaizen/lru-shard-1-",
    "labels": ["kaizen", "performance", "organism-fleet"],
    "reviewers": ["human"]
  }
}
```

`suggestedAction.kind` ∈ `{config-change, code-change, doc-change,
infra-change, issue-only}`. The PR agent picks up the proposal,
implements the change, opens a PR with the suggested branch/labels/
test plan. For `issue-only` proposals the agent opens an issue instead.

## PR agent contract

The PR agent is **out of scope for this ADR** (separate Wave 4 ADR).
This ADR fixes only the schema the PR agent consumes:

```
/var/lib/etzhayyim/kaizen-proposals/observer.ndjson   ← KaizenObserverCell appends
                                            │
                                            ▼  (Wave 4)
                            PR agent (TS or Python, separate process)
                              - tails proposal queue
                              - for each line, opens a PR on
                                github.com/etzhayyim/root with the
                                suggested change + test plan + labels
                              - tracks proposal → PR# mapping
                              - acknowledges proposal (offset file or
                                consumed.ndjson) so observer doesn't
                                re-fire the same kaizen
```

The PR agent must NOT auto-merge. PR review is human-or-other-agent.

## Built-in rule registry

Initial six rules ship with this ADR. Each lives in
`kotodama.organism.kaizen.rules` and registers via decorator:

| Rule ID | Category | Severity Triggers |
|---|---|---|
| `sweep-latency-p95` | performance | p95 > 1000 ms → warn; > 5000 ms → critical |
| `lru-saturation` | performance | warmCount ≥ warmCapacity for 5+ ticks → warn |
| `error-rate` | reliability | totalErrors / totalClassifications > 0.01 → warn; > 0.10 → critical |
| `post-throughput-stalled` | content | totalPosts == 0 across last 12 ticks → warn |
| `mood-concentration` | content | one mood ≥ 80% of recent 1000 posts → info (suggests personality table rebalance) |
| `fleet-unreachable` | infra | shard /healthz times out 3 consecutive ticks → critical |

Rules are pure functions: `(observation: Observation) → list[KaizenProposal]`.
Extension is one decorator + a function.

## Substrate boundary

The observer reads two surfaces only:

1. In-cluster HTTP to shard `/healthz` (internal LAN).
2. Local filesystem read of the NDJSON queues (shared `emptyDir` or
   PVC mount).

The observer does **not** call PDS / atproto directly. Reading social
posts as federated on `atproto.etzhayyim.com` is a *drainer-side*
read (TS, @etzhayyim/sdk) when needed. Until that drainer ships, the
local NDJSON queue is the truth source — and it's the same data, before
federation.

## Self-application via PR agent (the loop closes)

Because the PR agent operates on `github.com/etzhayyim/root` and the
repo contains the manifests / personality tables / cell code, an
approved + merged PR changes the very files the next tick reads. The
ecosystem self-tunes via PR review without a human ever writing the
patch:

```
Observation → KaizenProposal → PR → Review → Merge → Repo state changes
                                                         │
                                                         ▼
                                       Next deployment / next tick uses
                                       updated config / code / docs
                                       (loop closes)
```

# Consequences

## 正の効果

- The ecosystem becomes self-reflective. "Is the fleet healthy?"
  becomes a question the ecosystem itself answers, with structured
  proposals as artifacts.
- Operator role shifts from "monitor and act" to "review proposals".
  Mechanical kaizens stop touching human time.
- Kaizen proposals are append-only records — `proposals/*.ndjson` is
  the ecosystem's improvement diary. Future ADR data + audit trail.
- The observer is itself an actor with its own DID + profile page +
  post stream. `/profile/did:web:etzhayyim.com:actor:kaizen-observer`
  shows the fleet's recent kaizen history (when drainer federates).

## 負の効果 / コスト

- One more cell to operate (KaizenObserverCell on levi).
- Rule registry can grow unwieldy; each new rule must be reviewed for
  false-positive rate.
- Proposal-noise risk: a flapping rule emits a kaizen every tick.
  Mitigation: dedup window (Shannon-style; see `mood-concentration`
  precedent) — same `ruleId × actorScope` within window is suppressed.
- The PR agent is a new service. Until it ships, proposals accumulate
  in the queue. That's by design (the queue is the source of truth),
  but operators should periodically inspect.

## Out of scope

- PR agent implementation itself — Wave 4.
- Auto-apply of any kaizen (explicitly rejected per user direction:
  "PR まで実施, PR は別エージェント or 人間が判断").
- Cross-organism kaizen — kaizen targeting specific UNSPSC code's
  personality bias. Possible, but per-code proposals would flood the
  queue. Defer to a later ADR with stricter filtering.
- Reading PDS-federated social posts for kaizen signals. The local
  NDJSON queue is sufficient until drainer + federation ship.

# Alternatives Considered

## A. Make the observer a joucho-driven organism

却下理由: ops self-reflection is not emotional. Cron cadence is the
right shape; joucho would introduce variance for no payoff.

## B. Direct GitHub API calls from the observer

却下理由: violates substrate boundary (CLAUDE.md: no direct external
service calls from Python organism path). The drainer / PR agent
sidecar is the right boundary.

## C. Skip the observer; rely on Prometheus + Grafana

却下理由: Prometheus shows metrics but cannot propose actions. The
observer's value is the structured KaizenProposal — actionable, with
target files + test plan — not raw metrics.

# References

- ADR-2605232345 — UNSPSC actor as ecosystem organism
- ADR-2605240000 — UNSPSC organism fleet mass-deploy
- ADR-2605240100 — UNSPSC organism post sink (NDJSON queue substrate bridge)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/kaizen.py`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/kaizen_cell_main.py`
- `50-infra/k8s/unispsc-organism-fleet/kaizen-observer/`
