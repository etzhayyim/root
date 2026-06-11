---
id: adr-2605061200-agi-active-inference-artificial-organism-architecture
title: "AGI / artificial organism architecture: LLM-only agents are insufficient; use active inference, persistent world models, embodiment, and self-maintenance"
status: active
doc_type: adr
topic: agi-artificial-organism-architecture
authoritative: true
last_verified: 2026-05-07
authoritative_for:
  - agi architecture direction
  - embodied agent architecture
  - artificial organism design constraints
  - active inference controller role
priority: 8.5
axis: architecture
weight: 0.80
priority_note: "STRONG — defines the upper architectural direction for agents that must persist, act, maintain state, and interface with robotics or artificial-life systems"
depends_on:
  - adr-2604291800-well-becoming-spirit-objective-function
  - adr-2604291800-well-becoming-formal-model
  - adr-2604251830-shannon-optimal-layered-architecture
related:
  - adr-0056-bpmn-as-actor
  - active-inference-agent-organism-design
  - adr-2605061300-real-world-effect-channel-boundary
  - adr-2605011200-graph-expand-bpmn-llm-edge-inference
  - adr-2605011300-capital-flow-information-physics
  - adr-2604301200-web4-contract-did-autonomous-agent-economy
  - adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
supersedes: []
superseded_by: []
---

# Context

Current foundation-model systems grow primarily from:

- Transformer / LLM next-token prediction
- diffusion models
- RLHF / preference optimization

These systems are strong at compressing cultural, linguistic, and visual
regularities. They are not, by themselves, sufficient for the target class of
systems this repo must support:

- AGI-like autonomous agents
- robotics
- artificial organisms
- self-maintaining systems
- self-evolving systems

The gap is architectural. An LLM objective is approximately:

```text
argmin -log p(x_t | x_<t)
```

That objective learns statistical prediction over observed symbols. It does not
directly supply:

- persistent hidden state
- sensorimotor closure
- causal intervention
- long-horizon self-maintenance
- energy / resource budgeting
- damage repair
- thermodynamic survival constraints
- open-ended adaptation

Therefore an LLM should be treated as a powerful compression and abstraction
layer, not as the whole agent.

# Decision

## 1. Do not define AGI or artificial-organism systems as LLM-only agents

Any repo architecture that claims to support AGI-like, robotics, or
artificial-organism behavior MUST NOT stop at:

```text
input -> LLM -> output
```

The minimum architecture is:

```text
Foundation Model
  -> Persistent World Model
  -> Planning / Policy Selection
  -> Active Inference Controller
  -> Embodiment / Tool or Robot Interface
  -> Homeostasis / Self-Maintenance
  -> Evolutionary Adaptation
```

The foundation model may provide language, vision, priors, abstraction, code,
and cultural knowledge. It is not the sole source of agency.

## 2. Separate prediction, world modeling, action, and self-maintenance

The system boundary is split into explicit layers:

| Layer | Role | Required capability |
|---|---|---|
| Foundation model | Knowledge compression | language, vision, concepts, tool descriptions |
| Persistent world model | Temporal state | hidden state, object permanence, causal simulation |
| Planning / policy | Candidate action selection | long-horizon plans, counterfactuals, constraints |
| Active inference controller | Perception-action loop | prediction-error minimization, uncertainty-aware action |
| Embodiment | Environment coupling | robot body, simulator, browser, shell, API, sensor stream |
| Homeostasis | Viability management | energy, resources, health, repair, service budget |
| Evolutionary adaptation | Open-ended improvement | policy updates, architecture search, objective refinement |

## 3. Use Active Inference as the controller pattern where action and uncertainty matter

For robotics, autonomous agents, and artificial organisms, the controller SHOULD
model action as controlled prediction-error minimization:

```text
perception = infer hidden causes of sensory states
action     = make future sensory states match prior preferences
explore    = reduce uncertainty / expected free energy
survive    = remain within viable state bounds
```

This is preferred over a fixed reward-only framing when the system must handle:

- partial observability
- noisy continuous environments
- sparse external rewards
- sim2real transfer
- irreversible physical actions
- curiosity / information gain
- self-maintenance constraints

RL remains valid as an implementation tool, but not as the only organizing
principle for embodied autonomous systems.

## 4. Treat prior preferences as survival and viability constraints

For artificial-organism work, "intelligence" must be connected to metabolism-like
constraints. The system must track viability variables such as:

- compute and energy budget
- storage and memory pressure
- sensor / actuator availability
- damage, degraded capability, and repair paths
- resource seeking
- reproduction or replication policy, if explicitly allowed
- adaptation under changing environment conditions

Landauer-style information cost and thermodynamic constraints are architectural
concerns, not after-the-fact metrics. An intelligence without any cost,
resource, or self-maintenance model is incomplete for organism-like behavior.

## 5. Keep objective evolution gated by Mokuteki

Self-evolving systems may adapt policies, priors, prompts, tools, memory, and
world-model parameters. They MUST NOT freely rewrite their highest-level
objective function.

Objective or prior-preference changes are allowed only under the higher gates
defined by the Well-Becoming / Mokuteki ADRs:

- child / future floor constraints
- Spirit separation-healing gate
- bottleneck dominance
- multiplicative total utility
- reversibility buffer

This prevents "self-evolution" from becoming unconstrained reward drift.

## 6. Reference architecture

The target architecture for future AGI / robotics / artificial-organism work is:

```text
LLM / VLM / diffusion model
  knowledge, perception, generation

Bayesian latent world model
  persistent state, objects, causality, counterfactual simulation

Active inference controller
  expected free energy, epistemic value, uncertainty-aware action

Embodied interface
  robot, browser, shell, API, simulator, sensorimotor stream

Homeostatic supervisor
  energy, compute, damage, budget, repair, viability bounds

Evolutionary adaptation layer
  bounded self-modification, policy search, architecture refinement
```

## 7. Model artificial life as an ecosystem, not one omnipotent agent

The preferred design unit is not a single universal agent. It is an artificial
ecosystem: multiple narrow organisms sharing a substrate, resource flows,
memory, selection pressure, and explicit boundaries.

```text
Substrate / soil
  Kotoba/Datomic, Git, IPFS, Ethereum, logs, object storage

Energy / nutrients
  electricity, compute, storage, bandwidth, API quota, money

Producers
  sensors, crawlers, ingestion agents, embedding agents

Consumers
  planners, document agents, code agents, media agents, transaction agents

Decomposers
  cleanup agents, validators, deduplicators, incident responders

Immune layer
  tests, policy engines, anomaly detection, secret scanning, sandboxing

Germline
  species repos, genome manifests, BPMN definitions, prompt and policy templates

Selection
  tests, simulations, user feedback, market signals, ERC-8004 reputation
```

This follows biological responsibility separation:

```text
Soma can act.
Germline can evolve.
Environment can select.
Metabolism limits growth.
Immune systems reject damage.
Development controls expression.
```

For software organisms this becomes:

```text
Runtime repos can act.
Evolution labs can mutate.
Tests / simulations / validators can select.
Budgets and leases limit growth.
Policy / sandbox layers reject damage.
BPMN controls expression and timing.
```

## 8. Separate runtime, evolution, species, and cultural-code repos

Self-evolution MUST NOT mean the resident runtime directly rewrites its own
production codebase with the same authority it uses for external actions.
Runtime, germline, and evolution responsibilities SHOULD be separated.

Recommended repo split:

```text
etzhayyim-root
  substrate: ADRs, graph schema, contracts, shared policies, protocol anchors

etzhayyim-organism-runtime
  soma: resident loop, sensors, effect dispatch, homeostasis, self-repair

etzhayyim-organism-evolution-lab
  reproduction: mutation, simulation, tests, fitness scoring, PR generation

etzhayyim-species-*
  germline: prompts, priors, BPMN variants, tool policy, genome manifests

Git / GitHub code repos
  cultural layer: tools, documents, workflows, libraries, PR-mediated changes

IPFS / Ethereum / ERC-8004
  lineage: immutable releases, identity, runtime receipts, reputation
```

The resident runtime may update bounded belief state, policy priors, routing
weights, and runtime memory. It MUST NOT directly mutate its top-level
objective, production source, signing authority, or action gateway policy.

## 9. Use LangGraph for cognition and Zeebe for durable responsibility

Kotoba/Datomic + LangGraph + LLM + Ethereum is sufficient for a minimal cognitive
PoC, but it is not the preferred full organism architecture once long-running
processes, real-world effects, auditability, retries, and self-evolution are in
scope.

Three accepted implementation patterns are:

| Pattern | Components | Use | Limitation |
|---|---|---|---|
| Minimal cognitive loop | Kotoba/Datomic + LangGraph + LLM + Ethereum | Single-organism PoC, proposal generation, local belief updates, chain commitments | Weak durable workflow, retry, compensation, and action audit |
| Durable organism runtime | Kotoba/Datomic + LangGraph + LLM + Zeebe + Ethereum | Resident agents, homeostasis, real-world effect gates, self-repair, phase control | More operational complexity |
| Ecosystem substrate | Kotoba/Datomic + Zeebe + LangGraph + LLM + Ethereum + IPFS + Git + separated repos | Multi-organism symbiosis, lineage, reputation, self-evolution, cultural-code evolution | Highest complexity; should be phased in |

Responsibility split:

```text
Kotoba/Datomic
  world model, event memory, belief state, viability telemetry

LangGraph
  local cognition, branching reasoning, reflection, tool-planning proposals

LLM / VLM / diffusion
  imagination, abstraction, summarization, generation

Zeebe / BPMN
  durable metabolism: timers, retries, gates, compensation, audit, task ownership

Ethereum / ERC-8004
  identity, commitments, lineage, reputation, economic accountability

IPFS / Git
  immutable artifacts and cultural-code history
```

Therefore Zeebe is not required for "thinking", but it is strongly recommended
for "responsible acting". Any effectful channel that can affect external people,
accounts, public surfaces, legal/commercial state, robots, or money SHOULD be
mediated by BPMN/Zeebe or an equivalent durable workflow engine.

## 10. Treat the repo as an event organism substrate

Under a philosophy-of-organism interpretation, the repo and graph are not only a
codebase. They are a durable event-memory substrate where actions, observations,
commits, messages, transactions, and proofs become linked occasions.

Design mapping:

| Organism philosophy term | Software substrate |
|---|---|
| actual occasion | event, observation, action, commit, message, transaction |
| prehension | graph edge: cites, causes, depends_on, learns_from, repairs, contradicts |
| concrescence | BPMN / LangGraph process that integrates inputs into a new event |
| nexus | organism, ecosystem, project, repo, community |
| subjective aim | prior preference plus Mokuteki / Well-Becoming gate |
| creativity | evolution lab, mutation, simulation, selection |
| durable memory | Kotoba/Datomic, IPFS, Git, Ethereum |

This does not license unconstrained expansion. It requires stronger membranes:
event provenance, policy gates, resource budgets, sandboxing, identity, and
lineage records.

# Consequences

- LLM-only agent implementations are acceptable for language, tool orchestration,
  and narrow automation, but not as the complete architecture for AGI,
  robotics, or artificial organisms.
- Future robotics actors must expose persistent state, uncertainty estimates,
  controller loops, and viability variables rather than only prompt templates.
- "Agent memory" must not be confused with a world model. A world model must
  support temporal state, causal simulation, and action-conditioned prediction.
- "Autonomous" claims must be backed by closed-loop perception-action behavior,
  not just repeated LLM calls.
- Artificial-life work must include resource accounting and self-maintenance
  invariants from the beginning.
- Self-modification is subordinate to Mokuteki gates and cannot override
  safety, child/future, or Spirit constraints.
- Self-evolution SHOULD be implemented through separated evolution-lab and
  species/germline repositories, not by giving the resident runtime direct
  authority to rewrite its own production code.
- Zeebe / BPMN SHOULD be used for durable action, real-world effect channels,
  self-repair, retries, compensation, audit, and phase control. LangGraph
  remains the local cognition layer.
- Artificial organisms SHOULD be decomposed into ecosystem roles such as
  sensors, digesters, planners, effectors, validators, decomposers, and
  evolution workers with least-privilege boundaries.
- When another agent, person, organization, or institution is affected, action
  selection SHOULD include a von Neumann minimax layer: infer what the
  counterparty is trying to protect, model those protected assets as prior
  preferences, simulate worst-case responses, and add minimax regret plus
  protected-asset violation terms to expected free energy. The counterparty is
  not just an obstacle; it is modeled as another preference-bearing agent.

# Prohibited Patterns

- Treating a next-token predictor as the full AGI architecture.
- Calling a stateless prompt loop an embodied agent.
- Using fixed external reward as the only survival or curiosity mechanism.
- Ignoring energy, compute, storage, damage, or repair in artificial-organism
  designs.
- Allowing self-modifying systems to rewrite top-level objectives without
  Mokuteki gate evaluation.
- Adding robotics controllers that hide uncertainty and viability state from
  audit logs.
- Letting a resident organism runtime mutate its own production source,
  authority keys, action gateway, or objective contract without a separate
  evolution-lab, test, review, and lineage process.
- Collapsing cognition, durable execution, external action, validation,
  reproduction, and lineage into one agent process with one authority boundary.

# Alternatives Considered

- **LLM-only AGI**: rejected. Strong for symbolic and cultural compression, but
  lacks action closure, persistent state, homeostasis, and embodiment.
- **RL-only robotics**: rejected as the sole pattern. It remains useful, but
  sparse rewards, sample inefficiency, partial observability, and sim2real gaps
  require world models and uncertainty-aware controllers.
- **Automata-only artificial life**: rejected as sufficient. Cellular automata
  and finite-state systems are useful substrates, but modern artificial
  organisms require hierarchical self-models, adaptive priors, embodied
  dynamics, thermodynamic survival, repair, and open-ended adaptation.
- **Unconstrained self-evolution**: rejected. Objective drift without higher
  gates conflicts with the repo's Well-Becoming / Mokuteki objective contract.
- **Same-repo direct self-modification**: rejected for production. It is
  acceptable only as a contained PoC branch/worktree pattern because the soma,
  germline, immune layer, and effector authority are not sufficiently separated.
- **Kotoba/Datomic + LangGraph + LLM + Ethereum only**: accepted for minimal
  cognitive PoC. Rejected as the full architecture for real-world effectful
  organisms because durable retries, timers, compensation, and audit workflows
  would otherwise be reimplemented ad hoc.
- **Zeebe for all cognition**: rejected. Durable workflow is not a replacement
  for uncertain local reasoning. LangGraph or an equivalent agent graph remains
  the better layer for cognition, while Zeebe owns durable responsibility.

# References

- ADR-2604291800 — Well-Becoming Spirit Objective Function
- ADR-2604291800 — Well-Becoming Formal Model
- ADR-2604251830 — Shannon Optimal Layered Architecture
- ADR-0056 — BPMN as Actor
- ADR-2605061300 — Real-World Effect Channel Boundary
- ADR-2604262100 — ERC-725 / ERC-8004 Agent Runtime
- Active Inference / Free Energy Principle: controller framing for
  perception-action loops
- Landauer principle: information processing has physical cost
- Embodied cognition: intelligence is coupled to body, environment, and action
