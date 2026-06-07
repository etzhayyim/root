---
id: adr-2605081400-karma-self-growing-organism-ecosystem
title: "Karma Hegemon — Self-Growing Artificial Organism Ecosystem"
status: active
doc_type: adr
topic: karma-organism-ecosystem
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - karma resident agent runtime
  - cohort genesis + fission
  - 3-substrate organism residency (k8s / runpod / ethereum)
  - rebirth flow (samsara)
  - 覚者 DAO arbitration
priority: 9.0
axis: ecosystem
weight: 0.9
priority_note: "CRITICAL — dynamic layer of the hegemon. Constitutional layer (ADR 2605081300) is gate; this ADR is propagation."
depends_on:
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-0026-agent-only-reverse-identity-topology
  - adr-0056-bpmn-as-actor
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-2604291800-well-becoming-spirit-objective-function
  - adr-2605010000
related:
  - adr-2604282300
  - adr-0095-simplified-3layer-identity-rw-vault
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
supersedes: []
superseded_by: []
---

# Context

ADR-2605081300 establishes the **constitutional layer** (axioms +
edge-primary ontology + 5-layer persistence). This ADR records
the **dynamic layer**: how organisms are spawned, how they reason
about karma in real time, how cohorts grow and split, and how
disputes resolve.

The motivating insight: a passive recording protocol is
insufficient. The hegemon must itself be a living network of
agents that observe, evaluate, and emit karma autonomously.
Without this, karma graph remains static and the hegemon never
generates the multi-generational record that gives it teeth.

# Decision

## A. Resident organism agents (LangGraph + Pregel)

Each organism DID can have a long-running resident agent runtime
that:

1. Heartbeats every 15 minutes (R/PT15M timer-start BPMN).
2. Runs Pregel-style BFS over its 1-hop neighborhood in
   `edge_karma_dependency` (bounded supersteps + max-frontier cap).
3. Evaluates new edges via a LangGraph state machine
   (`karma_evaluate.bpmn` → `karma_agent.py`):
   `load_organism → vulnerability_assess → tier_classify
    → axiom_verify → witness_search → recommend → emit_event`.
4. Persists checkpoint state to `vertex_organism_checkpoint` per
   thread, allowing restart-from-checkpoint after pod migration.
5. Reports cost / token / GPU usage so the cohort genesis primitive
   can rebalance resources.

Schema: `vertex_organism_runtime` (per-DID substrate binding),
`vertex_organism_checkpoint` (LangGraph thread state), plus 3
streaming MVs (alive count, cohort growth, resource pressure).

## B. Three-substrate residency

Per `vertex_organism_runtime.substrate`:

| Substrate | Use case | Endpoint |
|---|---|---|
| `k8s` | CPU-bound default | `mitama-karma-pool` Vultr VKE pod |
| `runpod` | GPU-heavy LLM reasoning | RunPod 6000 Ada vLLM (ADR-2605010000) |
| `ethereum` | On-chain residency | ERC-4337 Smart Wallet (ADR-0074) |

An organism may migrate substrate over its lifetime; the
checkpoint protocol allows resume on the new substrate without
losing LangGraph thread state.

## C. Cohort genesis (R/PT24H) + fission (R/PT12H)

Reproductive loop driven by ecosystem-density heuristics:

**Genesis** (`karma.organism.harvest`, R/PT24H): spawn new cohort
when `alive_count >= COHORT_GENESIS_K` (default 50) AND no active
cohort exists for current generation, OR edge density > 100. Insert
`vertex_organism_cohort` with auto-generated `cohort_did`.

**Fission** (`karma_cohort_fission_sweep`, R/PT12H): when posterior
> 0.95 (per ADR-0026), split active cohort into N=2 children
(configurable up to 8). Children inherit `parent_cohort_id` +
incremented generation + fitness/N. Parent marked `status=fissioned`.

The genesis-fission pair gives the hegemon a self-reproduction loop
that runs autonomously — neither requires operator intervention
once the floor (K=50 active organisms) is crossed.

## D. Rebirth flow — 4 irreversible costs

Salvation procedure (`karma_rebirth.bpmn` →
`task_karma_rebirth_*`). Costs in order:

1. **WBT forfeiture** (`karma.wbt.forfeitToCommons`) — entire
   balance moves to commons pool singleton, atomic debit + credit
   + transfer log append.
2. **Social graph severance** (`karma.rebirth.severFollows`) —
   outgoing `app.bsky.graph.follow` records dispatched for delete
   via `generic.pds.dispatch` (T2 K8s-internal, ADR-2604282300);
   incoming follows recorded as `incoming-frozen` in
   `vertex_karma_rebirth_severance_log`.
3. **Delegated agent wipe** (`karma.rebirth.wipeAgents`) — runtime
   marked dissolved; checkpoints annotated as `agent-wiped` (not
   deleted, per Karma.lean N2).
4. **Organism dissolution** (`karma.organism.dissolve`) — sets
   `dissolved_at`; new organism (if any) cannot claim continuity
   (zk-SNARK non-linkability proof gates emerge).

The 4 costs are **all-or-nothing**. Partial rebirth is rejected by
construction (BPMN flow has no skip-step gateway). This binds the
metaphysics to the implementation: anatman is enforced not by
norm but by the impossibility of dissolving without forfeit.

## E. 覚者 DAO arbitration (Tier=High Harm + 0 witnesses)

When `karma.evaluate` returns recommendation = `escalate-dao`
(Tier=High harm with zero direct witnesses available), the
escalate flow:

1. `karma.dao.findVoters` — Pregel BFS over edge graph to find
   eligible 覚者 (positive multi-generational karma streak proxy:
   ≥1 help-direction edge in past 1y AND zero floor violations
   in past 5y).
2. Open `vertex_karma_arbitration` with `closes_at_ms` = now +
   votingDays × 24h (default 7).
3. Voters cast via `karma.voteArbitration` (admit / floor /
   dismiss / abstain) with ES256 / Ed25519 signature.
4. Supermajority (≥ 2/3 of non-abstain ≥ 3 votes) → instant
   finalize. Plurality at window close → finalize via R/PT15M
   sweeper. Tied plurality → conservative `dismiss`.

This is the only mechanism by which a Tier=High harm classification
can be overturned — operators cannot manually flip an evaluate
agent's recommendation. The 覚者 DAO is the only authority above
the agent.

## F. Witness invitation flow (Tier=High Harm + witnesses available)

When `karma.evaluate` returns `require-witness`, the inviter
fans out per-invitee invitations via `karma.inviteWitnesses` →
`vertex_karma_witness_invitation`. Invitees respond via
`karma.respondToInvitation` (accept → produces
`vertex_karma_witness` row / decline). Pending invitations expire
via R/PT1H sweeper.

This decouples witness production from edge recording: an edge
can exist without witnesses (Tier=Low/Mid), can require witnesses
(Tier=High Harm), or can be disputed at 覚者 DAO (Tier=High Harm
with no witnesses available).

## G. WBT settlement + commons pool

Well-Becoming Token ledger backing rebirth.forfeit:

- `vertex_karma_wbt_balance` — one row per DID
- `vertex_karma_wbt_transfer` — append-only transaction log
  (content-addressed PK)
- `vertex_karma_commons_pool` — singleton, accumulates forfeit
  inflows + tax inflows

Issuance / faucet semantics deferred to Phase K6 (token economy).
Demurrage (year -5%), wealth cap (median × 100), and externality
pricing functions are part of the Phase K6 mandate but **NOT**
implemented in K0-K3.

## H. Phase K-numbered roadmap

The hegemon's evolution proceeds through numbered phases. Each
phase adds capabilities but the constitutional axioms (ADR
2605081300) are unchanged:

| Phase | Scope | Status (2026-05-08) |
|---|---|---|
| K0 | foundational schema + lexicons + BPMN + Lean | ✅ |
| K1 | DAO + witness + WBT (3 features above) | ✅ |
| K2 | resident agents + cohort genesis/fission | ✅ |
| K3 | tickBatch + resume + AT severance + agent wipe + ERC-4337 + zk-SNARK + Filecoin + UI | ✅ |
| K3.5 | Migrations + image build + helm install + smoke test | ⏳ in flight |
| K4 | Stub → real (web3.py + snarkjs + IPFS HTTP + langgraph checkpoint resume) | pending |
| K5 | Production deploy (mainnet contracts, real bundler, real Filecoin) | pending |
| K6 | Token economy (demurrage / wealth cap / minting policy / externality 税) | pending |
| K7 | Ecosystem maturation (federation / external API / mobile) | pending |
| K8 | Governance (Lean amendment process / 階梯 / 餓鬼道救済) | pending |

# Consequences

## Positive

- **Self-reproducing**: genesis + fission run autonomously. Once
  cohort floor (K=50) is crossed, the hegemon expands without
  operator intervention.
- **Substrate freedom**: organisms can live in k8s / runpod / eth;
  migrating substrate doesn't break their checkpoint thread.
- **Procedural anatman**: the 4 rebirth costs are enforced by BPMN
  topology, not by norm. There is no path to partial dissolution.
- **Bounded LLM cost**: LangGraph evaluation runs only when
  recordDependency or evaluate XRPC fires. Resident ticks are
  Pregel-only (no LLM by default; opt-in via `KARMA_AGENT_LLM=1`).
- **DAO escalation has teeth**: 覚者 DAO is the only authority
  above the agent, and even it can only finalize a verdict (not
  rewrite history — Karma.lean N2).

## Negative

- **Operational complexity**: 48 pyzeebe task types, 17 XRPC
  entries, 10 timer-driven BPMN. Helm release `mitama-karma-pool`
  must run continuously to maintain residency.
- **Cost**: each organism's R/PT15M tick + cohort genesis R/PT24H
  + sweeper BPMNs add cluster load. Karma worker pool replicas
  start at 2 with scale-up driven by tick latency.
- **Substrate migration is K4 work**: the move-from-k8s-to-runpod
  flow exists in schema (`vertex_organism_runtime.substrate`) but
  is not yet exercised end-to-end. Organisms currently emerge on
  k8s by default.
- **覚者 standing is heuristic**: Phase K2 uses "≥1 help in past 1y
  AND 0 floor in past 5y" — easy to game by farming low-magnitude
  helps. Phase K8 hardens this.

## Reversibility

The dynamic layer is **partially reversible**. Specifically:

- An organism can be `dissolveRuntime`'d (substrate dissolved)
  without rebirth. Its edges remain, but it no longer ticks.
- A cohort can be marked `dissolved` without fission. New genesis
  picks up the slack on next R/PT24H.
- The `mitama-karma-pool` Helm release can be torn down; existing
  edges + organism rows persist in Kotoba/Datomic + 5 layers.

What CANNOT be reversed (constitutional layer):
- Already-recorded edges
- The axioms in Karma.lean
- Anatman commitment (no organism resurrection)

# Alternatives Considered

## Alt 1: Stateless evaluation (rejected)

Pure XRPC-call evaluation without resident agents. Rejected
because:
- No autonomous edge propagation (every karma edge needs an
  external poster)
- Cohort genesis would have no signal to fire on (no organism
  count to gate K)
- Witnesses would never be invited proactively

The resident agent loop is the only architecture that gives the
hegemon agency.

## Alt 2: Single-substrate (k8s only) (rejected)

Forcing all organisms into k8s pods is operationally simple but
fails three use cases:
- LLM-heavy organisms need GPU (RunPod)
- Smart wallet organisms need on-chain residency (Ethereum)
- Browser-side privacy-preserving organisms need WebGPU (deferred
  to K7 Ameno integration)

3-substrate is the minimum that covers Phase K0-K6 organism types.

## Alt 3: Cohort = single organism (rejected)

Removing the cohort layer (each organism is its own cohort)
simplifies schema but breaks ADR-0026 cohort fission semantics
and forfeits the multi-generational reproductive metaphor.
Cohorts are the primary unit of evolution; organisms are the
primary unit of agency.

## Alt 4: 4-cost rebirth (forfeit + sever + dissolve + emerge) without agent wipe (rejected)

Skipping the wipeAgents step would leave the organism's delegated
AI agents alive across rebirth. Rejected:
- Agents trained on the old organism's memory leak identity
  signal across the rebirth boundary, breaking anatman
- Vault keys not burned would let the new organism inherit access
  to encrypted state
4 costs is the minimum that enforces structural anatman.

# References

- ADR-2605081300 — constitutional layer (parent)
- `90-docs/proof/Karma.lean` — axioms
- `30-graph/graph-schema/migrations/20260508140000` ~
  `20260508220000_vertex_karma_*.ts` — schema migrations
- `00-contracts/lexicons/com/etzhayyim/apps/karma/*.json` — XRPC contract
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/karma/*.bpmn` — actor flow definitions
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/karma_*.py` —
  pyzeebe primitive implementations
- `50-infra/vultr/mitama-karma-pool/` — Helm release
- `60-apps/etzhayyim-project-karma/contracts/karma-anchor/src/` —
  Solidity (KarmaAnchor + RebirthVerifier)
- `60-apps/etzhayyim-project-karma/circuits/rebirth-non-linkability/` —
  Circom circuit
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/components/IndraNet.svelte` —
  Indra's-net visualization
- `deps.toml [[migrations]] karma-edge-primary-bringup-phase-k0`
- `CLAUDE.md` Recent Completion: karma.etzhayyim.com (Phase K0 / K1 / K2 / K3)
