---
id: active-inference-agent-organism-design
title: "Active Inference Agent / Artificial Organism Design"
status: active
doc_type: explanation
topic: agi-artificial-organism-architecture
authoritative: true
last_verified: 2026-05-06
authoritative_for:
  - active inference agent design
  - persistent world model schema plan
  - homeostasis and viability contract
  - embodied agent rollout plan
related:
  - adr-2605061200-agi-active-inference-artificial-organism-architecture
  - adr-2605061300-real-world-effect-channel-boundary
  - adr-2604240946-yoro-autonomous-actor-hybrid-loop
  - adr-2604252100-robotics-product-manufacturing-package
  - adr-2604301200-web4-contract-did-autonomous-agent-economy
  - adr-2605011200-graph-expand-bpmn-llm-edge-inference
---

# Active Inference Agent / Artificial Organism Design

## Goal

Turn ADR-2605061200 into an implementable repo architecture for agents that
need persistent state, action, uncertainty, and self-maintenance.

This design does not replace LLM / VLM / diffusion systems. It wraps them in a
closed-loop architecture:

```text
observe -> infer belief -> evaluate expected free energy -> propose action
        -> simulate / approve -> dispatch through safety boundary
        -> ingest telemetry -> update world state -> maintain viability
```

The first implementation target is a software-embodied agent. Robotics support
is added through the existing `robotics.*` contracts and safety gateway, not by
letting the planner write actuator commands directly.

## System Boundary

| Concern | Canonical layer | Existing repo anchor |
|---|---|---|
| Time-domain loop | Hybrid ms/s/min/hour split | ADR-2604240946 |
| Durable outer loop | BPMN-as-actor / Zeebe / pyzeebe | ADR-0056, yoro pattern |
| Short LLM inference | Murakumo / generic LLM primitive | ADR-2604240946 |
| Physical action boundary | robotics safety gateway | ADR-2604252100 |
| Agent identity and runtime budget | contract-DID runtime lease | ADR-2604301200 |
| Objective gate | Well-Becoming / Mokuteki | ADR-2604291800 |
| Market / resource flow | capital-flow information physics | ADR-2605011300 |

The new layer adds explicit world-state, belief-state, prior-preference,
homeostasis, and active-inference tick records.

## Design Principles

1. **LLM is a proposal engine, not the controller**
   LLMs may summarize state, propose hypotheses, or draft plans. The active
   inference loop owns uncertainty, preferences, and action selection.

2. **World model is persistent**
   Agent memory is not enough. The system needs state records with time,
   source, confidence, uncertainty, and action-conditioned update history.

3. **Action is always mediated**
   Every external action becomes an `action_proposal` first. Physical actions
   must pass simulation, approval, safety envelope, and audit sinks.

4. **Homeostasis is first-class**
   Compute, energy, storage, budget, lease health, error rate, and damage-like
   degradation are tracked as viability variables.

5. **Self-modification is bounded**
   Policy adaptation can adjust priors and tactics, but not bypass Mokuteki
   gates or rewrite top-level objective contracts.

## Phase 1 Scope

Phase 1 implements a safe closed-loop skeleton:

```text
Telemetry / environment event
  -> vertex_agent_observation
  -> vertex_agent_belief_state
  -> vertex_agent_active_inference_tick
  -> vertex_agent_action_proposal
  -> existing BPMN / robotics / PDS dispatch boundary
  -> vertex_agent_homeostasis_snapshot
```

Phase 1 does not dispatch robot motion directly. For robotics, the output is a
mission plan or simulation request routed through existing robotics lexicons:

- `com.etzhayyim.apps.robotics.mission.plan`
- `com.etzhayyim.apps.robotics.mission.simulate`
- `com.etzhayyim.apps.robotics.approvalRecord`
- `com.etzhayyim.apps.robotics.telemetry.ingest`
- `com.etzhayyim.apps.robotics.mission.status`

Real-world effect channels follow the same rule. Email, web form submission,
fax, phone calls, public posts, generated-media publication, and print-mail are
not direct planner outputs. They are `action_proposal` rows plus
`vertex_agent_realworld_effect` gate records governed by ADR-2605061300.

## Data Model

### `vertex_agent_observation`

Raw observed state from tools, sensors, commits, telemetry, social events,
runtime receipts, or human input.

| Column | Type | Notes |
|---|---|---|
| `vertex_id` | VARCHAR PRIMARY KEY | `at://did:web:agent.etzhayyim.com/com.etzhayyim.apps.agent.observation/{rkey}` |
| `agent_did` | VARCHAR | owning agent |
| `source_kind` | VARCHAR | `tool`, `sensor`, `telemetry`, `social`, `runtime`, `human` |
| `source_ref` | VARCHAR | URI / topic / task id |
| `observed_at` | VARCHAR | ISO timestamp |
| `payload_json` | JSONB or VARCHAR | Kotoba/Datomic compatibility decides exact type |
| `confidence` | DOUBLE PRECISION | source reliability |
| `uncertainty` | DOUBLE PRECISION | normalized [0,1] |
| `sensitivity_ord` | BIGINT | existing policy convention |
| `actor_id` | VARCHAR | audit actor |

### `vertex_agent_belief_state`

Current latent-state estimate derived from observations.

| Column | Type | Notes |
|---|---|---|
| `vertex_id` | VARCHAR PRIMARY KEY | belief row |
| `agent_did` | VARCHAR | owning agent |
| `belief_kind` | VARCHAR | `world`, `self`, `task`, `resource`, `robotics-asset` |
| `state_key` | VARCHAR | stable fact / variable key |
| `state_value_json` | JSONB or VARCHAR | current estimate |
| `posterior_confidence` | DOUBLE PRECISION | normalized [0,1] |
| `posterior_entropy` | DOUBLE PRECISION | uncertainty measure |
| `updated_from_observation` | VARCHAR | observation id |
| `updated_at` | VARCHAR | ISO timestamp |

### `vertex_agent_prior_preference`

Viability and goal constraints that action tries to satisfy.

| Column | Type | Notes |
|---|---|---|
| `vertex_id` | VARCHAR PRIMARY KEY | prior row |
| `agent_did` | VARCHAR | owning agent |
| `preference_key` | VARCHAR | e.g. `runtime.solvent`, `safety.no-estop`, `spirit.nonseparating` |
| `target_range_json` | JSONB or VARCHAR | allowed / preferred range |
| `hard_floor` | BOOLEAN | reject if violated |
| `weight` | DOUBLE PRECISION | only evaluated after hard gates |
| `depends_on_adr` | VARCHAR | e.g. `adr-2604291800-*` |
| `active` | BOOLEAN | preference lifecycle |

### `vertex_agent_policy_adaptation_proposal`

Bounded prior/policy adaptation evidence. Every adaptation attempt is recorded
here before any active prior is written.

| Column | Type | Notes |
|---|---|---|
| `vertex_id` | VARCHAR PRIMARY KEY | proposal row |
| `agent_did` | VARCHAR | owning agent |
| `preference_key` | VARCHAR | target preference |
| `proposal_hash` | VARCHAR | canonical proposal hash |
| `proposal_json` | JSONB or VARCHAR | normalized proposal payload |
| `mokuteki_gate_pass` | BOOLEAN | objective gate result |
| `triple_witness_pass` | BOOLEAN | integrity gate result |
| `blockers_json` | JSONB or VARCHAR | blockers when rejected |
| `proposal_state` | VARCHAR | `accepted` or `blocked` |

### `vertex_agent_active_inference_tick`

One evaluation of expected free energy and candidate action.

| Column | Type | Notes |
|---|---|---|
| `vertex_id` | VARCHAR PRIMARY KEY | tick id |
| `agent_did` | VARCHAR | owning agent |
| `tick_kind` | VARCHAR | `reactive`, `deliberative`, `homeostasis`, `robotics` |
| `belief_snapshot_hash` | VARCHAR | deterministic snapshot root |
| `candidate_actions_json` | JSONB or VARCHAR | action candidates |
| `expected_free_energy_json` | JSONB or VARCHAR | risk, ambiguity, epistemic value |
| `selected_action_id` | VARCHAR | chosen proposal |
| `mokuteki_gate_pass` | BOOLEAN | must pass before effectful action |
| `created_at` | VARCHAR | ISO timestamp |

### `vertex_agent_action_proposal`

Action proposal before effectful dispatch.

| Column | Type | Notes |
|---|---|---|
| `vertex_id` | VARCHAR PRIMARY KEY | action proposal |
| `agent_did` | VARCHAR | owning agent |
| `action_kind` | VARCHAR | `pds-dispatch`, `mcp-call`, `robotics-mission`, `runtime-lease`, `policy-update` |
| `target_surface` | VARCHAR | NSID / tool / robot asset / BPMN process |
| `proposal_json` | JSONB or VARCHAR | typed payload |
| `simulation_ref` | VARCHAR | simulation result if required |
| `authority_ref` | VARCHAR | signed delegated authority policy / capability ref |
| `approval_ref` | VARCHAR | legacy compatibility alias; new designs use `authority_ref` |
| `safety_state` | VARCHAR | `draft`, `simulated`, `authority_bound`, `rejected`, `dispatched` |
| `dispatch_ref` | VARCHAR | final effect id |
| `created_at` | VARCHAR | ISO timestamp |

### `vertex_agent_realworld_effect`

Cross-channel gate for actions that affect external people, organizations,
accounts, websites, public media surfaces, or the physical world.

| Column | Type | Notes |
|---|---|---|
| `vertex_id` | VARCHAR PRIMARY KEY | effect row |
| `action_proposal_id` | VARCHAR | link to `vertex_agent_action_proposal` |
| `agent_did` | VARCHAR | actor |
| `principal_did` | VARCHAR | authority holder / requester |
| `channel` | VARCHAR | `email`, `web`, `fax`, `phone`, `document`, `image`, `audio`, `video`, `print-mail`, `robotics` |
| `effect_class` | VARCHAR | `draft_only`, `private_send`, `public_publish`, `account_operation`, `legal_commercial`, `financial_commitment`, `physical_dispatch`, `emergency_or_safety` |
| `target_ref_hash` | VARCHAR | hashed recipient / endpoint where sensitive |
| `payload_hash` | VARCHAR | immutable payload digest |
| `summary` | VARCHAR | human-readable summary |
| `authority_ref` | VARCHAR | signed delegated authority policy / capability ref |
| `approval_ref` | VARCHAR | legacy compatibility alias; new designs use `authority_ref` |
| `budget_ref` | VARCHAR | quote / lease / budget |
| `dispatch_state` | VARCHAR | `draft`, `classified`, `policy_checked`, `authority_bound`, `dispatched`, `receipt_recorded`, `observed`, `authority_missing`, `blocked`, `failed` |
| `dispatch_receipt_ref` | VARCHAR | provider receipt |
| `observation_plan_json` | JSONB or VARCHAR | expected post-dispatch observation |
| `created_at` | VARCHAR | ISO timestamp |
| `updated_at` | VARCHAR | ISO timestamp |

### `vertex_agent_homeostasis_snapshot`

Viability state for organism-like persistence.

| Column | Type | Notes |
|---|---|---|
| `vertex_id` | VARCHAR PRIMARY KEY | snapshot |
| `agent_did` | VARCHAR | owning agent |
| `compute_budget_remaining` | DOUBLE PRECISION | runtime budget |
| `storage_pressure` | DOUBLE PRECISION | normalized [0,1] |
| `lease_seconds_remaining` | BIGINT | runtime lease health |
| `error_rate_1h` | DOUBLE PRECISION | degradation signal |
| `tool_success_rate_1h` | DOUBLE PRECISION | capability health |
| `energy_or_cost_proxy` | DOUBLE PRECISION | Landauer / cost proxy |
| `viability_state` | VARCHAR | `normal`, `conserve`, `repair`, `hibernate`, `halted` |
| `created_at` | VARCHAR | ISO timestamp |

## Lexicon Surface

Phase 1 should add only agent-level contracts. Robotics contracts remain in
`com.etzhayyim.apps.robotics.*`.

| NSID | Type | Role |
|---|---|---|
| `com.etzhayyim.apps.agent.observeState` | procedure | write observation |
| `com.etzhayyim.apps.agent.inferBelief` | procedure | derive / update belief rows |
| `com.etzhayyim.apps.agent.activeInferenceTick` | procedure | compute candidate actions and expected free energy |
| `com.etzhayyim.apps.agent.proposeAction` | procedure | record action proposal |
| `com.etzhayyim.apps.agent.classifyRealWorldEffect` | procedure | classify external effect channel and gates |
| `com.etzhayyim.apps.agent.planRealWorldDispatch` | procedure | convert autonomous authority into channel task plan |
| `com.etzhayyim.apps.agent.buildDispatchReceiptObservation` | procedure | convert channel receipt into observation |
| `com.etzhayyim.apps.agent.recordDispatchReceipt` | procedure | persist channel receipt state on effect vertex |
| `com.etzhayyim.apps.agent.inboundEmailToObservation` | procedure | convert inbound mail into observation |
| `com.etzhayyim.apps.agent.recordRealWorldEffect` | procedure | write effect gate / dispatch receipt |
| `com.etzhayyim.apps.agent.recordHomeostasis` | procedure | write viability snapshot |
| `com.etzhayyim.apps.agent.evaluateViability` | query | read current homeostasis and blockers |
| `com.etzhayyim.apps.agent.adaptPolicy` | procedure | bounded prior / policy update request |

Write allowlists:

| NSID | Allowed tables |
|---|---|
| `observeState` | `vertex_agent_observation` |
| `inferBelief` | `vertex_agent_belief_state` |
| `activeInferenceTick` | `vertex_agent_active_inference_tick`, `vertex_agent_action_proposal` |
| `proposeAction` | `vertex_agent_action_proposal` |
| `classifyRealWorldEffect` | `vertex_agent_realworld_effect` |
| `planRealWorldDispatch` | none; returns channel task plan only |
| `buildDispatchReceiptObservation` | none; returns observation row only |
| `recordDispatchReceipt` | `vertex_agent_realworld_effect` |
| `inboundEmailToObservation` | none; returns observation row only |
| `recordRealWorldEffect` | `vertex_agent_realworld_effect` |
| `recordHomeostasis` | `vertex_agent_homeostasis_snapshot` |
| `adaptPolicy` | `vertex_agent_policy_adaptation_proposal`, `vertex_agent_prior_preference` |

## BPMN Processes

### `agent/activeInferenceTick.bpmn`

Cadence: `R/PT5M` default, per agent policy may slow to conserve mode.

```text
Task_SelectObservations       generic.db.select
Task_UpdateBeliefs            generic.llm.json or generic.langgraph.run
Task_LoadPriorPreferences     generic.db.select
Task_EvaluateExpectedFreeEnergy
Task_WriteTick                generic.db.insert
Task_WriteActionProposal      generic.db.insert
Task_Audit                    generic.audit.emit
```

Phase 1 can implement `Task_EvaluateExpectedFreeEnergy` as deterministic Python
scoring, not LLM reasoning:

```text
G = risk + ambiguity - epistemic_value + viability_penalty
```

Lowest `G` wins only after hard floors pass.

### `agent/homeostasisWatch.bpmn`

Cadence: `R/PT1M` for active agents, `R/PT30M` in hibernation.

```text
Task_ReadRuntimeLease
Task_ReadRecentFailures
Task_ReadResourceUsage
Task_EvaluateViability
Task_WriteHomeostasis
Task_EmitConserveOrRepairAction
```

State transition:

```text
normal -> conserve  when budget or lease drops below floor
normal -> repair    when error rate / tool failure crosses threshold
conserve -> normal  when budget and health recover
conserve -> hibernate when lease cannot be renewed
repair -> halted    when safety or integrity gate fails
```

### `agent/policyAdaptation.bpmn`

Cadence: hourly or manually triggered. Must be gated by Mokuteki and
triple-witness integrity checks.

```text
Task_Adapt                 agent.adaptPolicy
Task_WriteProposal         generic.db.insert -> vertex_agent_policy_adaptation_proposal
Gateway_Accepted           policyAccepted only
Task_WritePreference       generic.db.insert -> vertex_agent_prior_preference
Task_AuditAccepted/Blocked generic.audit.emit
```

This process does not directly modify top-level objectives or hard floors.
It can activate bounded prior-preference updates only when Mokuteki and
triple-witness gates pass.

### `agent/realWorldEffectDispatch.bpmn`

Message-start process for effectful actions. It records the effect boundary and
audit event without calling channel-specific actors.

```text
Task_ClassifyEffect            agent.classifyRealWorldEffect
Task_RecordEffectGate          generic.db.insert
Task_Audit                     generic.audit.emit
```

### `agent/realWorldAutonomousDispatch.bpmn`

This is the first active-influence path. It does not wait for per-action human
approval. It dispatches only when the classified effect has a scoped autonomous
authority ref, policy ref, matching payload hash, and a supported channel task
plan.

```text
Task_Classify                  agent.classifyRealWorldEffect
Task_RecordEffect              generic.db.insert
Task_Plan                      agent.planRealWorldDispatch
Task_RecordDispatchLedger      generic.db.insert -> vertex_agent_dispatch_ledger
Gateway_Dispatch               dispatchAllowed + supported taskType
Task_SendEmail                 mailer.sendEmail
Task_BuildReceiptObservation   agent.buildDispatchReceiptObservation
Task_RecordEffectReceipt       agent.recordDispatchReceipt -> vertex_agent_realworld_effect
Task_RecordReceiptObservation  generic.db.insert -> vertex_agent_observation
Task_AuditSent/Blocked         generic.audit.emit
```

Phase A sends email only. Fax and print-mail remain task-plan targets until
their worker/BPMN bindings are present in this repo.

The local daemon suppresses duplicate dispatches within the running process.
The BPMN path also records `dispatchPlanId` in `vertex_agent_dispatch_ledger`
and only sends when that insert is new, so process restarts and multiple daemon
instances do not resend the same effect.

## Expected Free Energy Contract

Each candidate action gets a decomposed score:

| Term | Meaning |
|---|---|
| `risk` | expected preference violation or irreversible harm |
| `ambiguity` | uncertainty remaining after action |
| `epistemic_value` | expected information gain |
| `viability_penalty` | cost, budget, lease, repair, energy pressure |
| `mokuteki_floor` | hard rejection if false |
| `safety_floor` | hard rejection if false |

Selection rule:

```text
reject if mokuteki_floor = false
reject if safety_floor = false
reject if required approval / simulation is missing
choose min(risk + ambiguity - epistemic_value + viability_penalty)
```

For real-world effects, ADR-2605061300 adds:

```text
G = risk
  + ambiguity
  - epistemic_value
  + viability_penalty
  + external_effect_penalty
```

`external_effect_penalty` increases for new recipients, public visibility,
legal/commercial/financial consequence, physical dispatch, weak receipts, or
regulated / identity-sensitive payloads.

This is intentionally auditable. The first implementation should prefer a
simple transparent scorer over a black-box controller.

## Robotics Integration

Robotics remains two-stage:

```text
active inference tick
  -> action proposal: robotics-mission
  -> robotics.mission.plan
  -> robotics.mission.simulate
  -> robotics.approvalRecord
  -> robotics safety gateway
  -> adapter dispatch
  -> robotics.telemetry.ingest
  -> belief update
```

Hard rules:

- No active-inference task writes actuator commands.
- No simulation result means no robot dispatch.
- No approval record means no robot dispatch.
- No telemetry/audit sink means no robot dispatch.
- Estop and safety events update belief state and homeostasis immediately.

## Real-World Effect Channels

External channels are integrated through the same proposal-and-gate model:

```text
active inference tick
  -> action proposal
  -> real-world effect classification
  -> payload hash + scoped delegated authority + policy check
  -> channel-specific dispatch
  -> receipt
  -> observation plan
  -> belief / homeostasis update
```

| Channel | Existing or target surface | Effect begins when |
|---|---|---|
| Email | `com.etzhayyim.apps.mailer.sendEmail` | message is sent |
| Web operation | `com.etzhayyim.apps.browser.*` | form, purchase, booking, account change, or public write is submitted |
| Fax | `com.etzhayyim.apps.fax.*` | fax is sent |
| Phone | `com.etzhayyim.apps.phone.*` target namespace | call is placed |
| Document | `com.etzhayyim.apps.docs.*` | document is shared, signed, sent, filed, or printed |
| Image | ComfyUI / image gateway | image is published, sent, printed, or used in ads |
| Audio / voice | `com.etzhayyim.apps.voice.*` target namespace | audio is played to others, sent, published, or used in calls |
| Video | `com.etzhayyim.apps.video.*` target namespace | video is published, sent, or used in public/commercial context |
| Print-mail | `com.etzhayyim.apps.insatsu.printMailJob.*` | job is submitted to print/mail partner |
| Public post | AT Protocol / PDS dispatch | record is committed to external social surface |
| Robotics | `com.etzhayyim.apps.robotics.*` | adapter dispatches motion / physical operation |

Generated artifacts remain internal until one of the external-effect events
above happens.

Autonomous operation does not wait for per-action human approval. It requires a
pre-granted scoped capability, policy ref, optional budget/quote ref, payload
hash match, and channel receipt plan before dispatch.

## Artificial Organism Interpretation

An agent becomes organism-like only when these variables are closed in the loop:

| Biological analogy | Repo variable |
|---|---|
| metabolism | runtime lease, compute budget, energy/cost proxy |
| interoception | homeostasis snapshot |
| perception | observation rows |
| belief | latent world/self state |
| action | action proposal / dispatch receipt |
| repair | repair-mode action proposal |
| dormancy | hibernated runtime state |
| reproduction | child agent / org creation, governed by ADR-2604301200 |
| evolution | bounded policy adaptation under Mokuteki |

This design does not claim artificial life from a prompt loop. The claim only
applies when self-maintenance variables affect future action selection.

## Rollout Plan

| Phase | Deliverable | Notes |
|---|---|---|
| P0 | This design + ADR registry | architecture contract only |
| P1 | Lexicon JSON stubs for 9 `com.etzhayyim.apps.agent.*` NSIDs | no new runtime |
| P2 | Kotoba/Datomic migration for 7 tables | includes `vertex_agent_realworld_effect`; JSON type choice depends on local migration convention |
| P3 | Python primitive pure helpers for EFE scoring and viability transition | unit-testable, no network |
| P4 | BPMN seed for `activeInferenceTick` and `homeostasisWatch` | proposal-only action writes |
| P5 | Real-world effect dispatch bridge | email/web/fax/phone/media/print-mail/robotics require channel gates |
| P6 | Policy adaptation loop | Mokuteki + triple-witness gated |
| P7 | Counterparty minimax world model | opponent prior preferences, protected assets, worst-case response, minimax regret |
| P8 | Knowledge-graph fitness into active inference and evolution | development docs, graph edges, information height, and flow control become EFE reward terms and shinka evolution evidence |

## Acceptance Criteria

Phase 1 is complete when:

- An observation can be written for an agent.
- A belief-state row can be derived from observations.
- A tick can produce an auditable expected-free-energy decomposition.
- A selected action is written as proposal, not directly dispatched.
- Real-world effect proposals create `vertex_agent_realworld_effect` rows before dispatch.
- Homeostasis can force `conserve`, `repair`, or `hibernate`.
- Robotics proposals cannot bypass simulation and approval records.
- Email, web, fax, phone, public post, media publication, and print-mail cannot bypass payload hash, authority, approval, and receipt checks.
- Counterparty-aware actions can record protected assets and minimax regret before
  the final expected-free-energy score is selected.
- Knowledge-graph coverage can lower expected free energy through
  `kgDevelopmentGain`, and each tick can append a `vertex_shinka_evolution`
  evidence row with the KG fitness context.
- ADR validation and docs registry checks pass.

## Non-Goals

- Direct actuator control from the active inference controller.
- Full robotics sim2real control.
- Unbounded self-replication.
- On-chain execution of agent cognition.
- Replacing existing yoro / robotics BPMN contracts.
- A black-box learned controller as the first implementation.
