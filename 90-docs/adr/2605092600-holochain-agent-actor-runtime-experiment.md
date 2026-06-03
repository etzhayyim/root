---
id: adr-2605092600-holochain-agent-actor-runtime-experiment
title: "ADR-2605092600: Holochain Agent/Actor Runtime Experiment"
status: deprecated
doc_type: adr
topic: holochain-agent-actor-runtime
authoritative: true
last_verified: 2026-05-09
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Experiment completed; retained as reference only. Production path stays LangGraph/LangServe + SpiffWorkflow + RisingWave."
authoritative_for:
  - runtimeKind=holochain experimental contract
  - Holochain placement as L3 virtual actor runtime experiment
  - Holochain source-chain/DHT boundary vs RisingWave projection SSoT
depends_on:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605082200-langgraph-single-task-and-row-driven-runtime
  - adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
related:
  - adr-0087-magatama-mcp-tool-facade
  - adr-0002-persistence-risingwave-only
supersedes: []
superseded_by: []
---

# ADR-2605092600: Holochain Agent/Actor Runtime Experiment

**Status**: rejected after experiment
**Date**: 2026-05-09
**Deciders**: Jun Kawasaki

## Context

ADR-2605080000 fixes the production cognitive actor stack around L1 Edge,
L2 LangGraph coordination, L3 virtual actor runtime, L4 MCP capability,
L5 RisingWave memory, and L6 compute. That stack is correct for centralized
operations, but it leaves one open question: whether per-agent local source
chains and peer validation are useful for agent/actor runtime events before
they are projected into RisingWave.

Holochain is a plausible experiment because a hApp is composed from one or
more DNAs, a DNA defines an isolated peer network and shared graph database,
and zomes expose the hApp API as WebAssembly functions. This maps naturally
to a cell-level actor event log, but only if we keep the existing etzhayyim
boundaries intact.

## Decision

Introduce `runtimeKind=holochain` as an **experimental runtime lane**, but do
not adopt it for the production agent/actor runtime.

After implementation and smoke verification, the production decision is:

- Use LangGraph/LangServe for agent graph serving.
- Use SpiffWorkflow for BPMN/human workflow orchestration.
- Use RisingWave for durable/queryable actor memory and projections.
- Keep Holochain only as a reference experiment for future local-first,
  peer-validated agent event logs.

Placement:

| Layer | Role |
|---|---|
| L3 | Holochain conductor lifecycle and hApp cell activation |
| L4 | MCP/XRPC facade only; conductor admin API is not public |
| L5 | RisingWave remains the query/projection SSoT |
| L6 | Holochain zome WASM executes actor event validation and command commit |

Holochain stores only the agent-local source chain and replicated DHT evidence
needed for actor event validation. Accepted events are projected to
`vertex_actor_event_holochain`, then existing actor/runtime projections derive
queryable state. Holochain must not become the long-term analytical query
store.

The initial hApp contract is:

| Binding | Value |
|---|---|
| hApp | `etzhayyim-agent-actor-runtime` |
| DNA | `agent_actor_runtime` |
| role | `agent_actor_runtime` |
| coordinator zome | `actor_runtime` |
| LangGraph registration | `register_langgraph_actor` |
| LangChain registration | `register_langchain_actor` |
| run start | `start_graph_run` |
| command/event commit | `commit_actor_event` |
| signal/query | `latest_actor_head`, `list_actor_events` |
| entry shape | `ActorEvent { actor_did, command_id, lexicon_nsid, input_cid, output_cid, occurred_at }` |

LangChain/LangGraph code is not run inside Holochain WASM. The cell stores
agent-owned definitions and receipts:

- `LangActor`: `actor_did`, `assistant_id`, `runtime_family`, `graph_kind`,
  `factory_path` or `graph_spec_cid`, `policy_cid`
- `GraphRun`: run identity and input CID
- `ActorEvent`: command/result receipt projected to RisingWave

## Implementation

Implemented contract and scaffolding:

- `00-contracts/schemas/agent-runtime-registration.schema.json` admits
  `runtimeKind=holochain`.
- `00-contracts/schemas/k8s-runtime-public.schema.json` admits public
  `runtime.kind=holochain`.
- `00-contracts/schemas/holochain-agent-runtime-plan.schema.json` defines the
  experiment plan output.
- `70-tools/etzhayyim/etzhayyim/agent_runtime_holochain.go` adds:
  `etzhayyim agent-runtime holochain-plan`.
- `50-infra/holochain/agent-runtime-experiment/holochain-agent-runtime.yaml`
  provides the experimental conductor StatefulSet projection source.
- `20-actors/magatama/holochain/agent-actor-runtime/` provides hApp/DNA
  manifest scaffolding and working HDK/HDI zomes.

The zome artifact image is built on Vultr VKE remote BuildKit, not on local
macOS Docker:

```text
builder: etzhayyim-vke
image: ghcr.io/etzhayyim/holochain-agent-actor-runtime:experimental-amd64
digest: sha256:29a1f2f037a31a8ae0518272706368714610b3eba845667e9690834b31a031b0
platform: linux/amd64
```

## Verification

Local contract smoke:

```sh
cd 70-tools/etzhayyim/etzhayyim
go test . -run Holochain
go run . agent-runtime holochain-plan \
  --agent-did did:web:kami-agent.etzhayyim.com \
  --happ-uri ipfs://bafy-happ \
  --dna-hash uhC0kagentactorruntime \
  --out ../../../90-docs/proof/holochain-agent-runtime-plan.local.json
```

The smoke verifies:

- schema/runtime enum accepts `holochain`
- cell binding is modeled as DNA hash + agent DID
- zome command surface is explicit
- Holochain event transport remains separated from RisingWave projection SSoT
- Vultr remote buildx compiles `actor_runtime_integrity.wasm` and
  `actor_runtime.wasm` for `wasm32-unknown-unknown`

VKE runtime smoke, 2026-05-09:

- `mitama-udf/langgraph-server` returned `/healthz` OK and exposed the `echo`
  assistant.
- A LangGraph actor run was created with
  `actor_did=did:web:holochain-agent-runtime.etzhayyim.com` and
  `thread_id=holochain-actor-thread-20260509`.
- Run `be761cd8-0a01-46e4-836f-4709ceabd925` reached `success` with output
  `echo: holochain langgraph actor smoke 2026-05-09`.
- The result was shaped as a Holochain `GraphRunCompleted` receipt for the
  `actor_runtime` zome.
- The pushed artifact image started in namespace `agent-runtime-holochain` and
  listed the zome WASM, DNA/hApp manifests, and LangGraph/LangChain examples.
- A LangChain actor smoke also ran in namespace `agent-runtime-holochain` using
  `langchain-core.RunnableLambda`, producing a successful tool-call receipt for
  `langchain-tool-agent`.

Proof: `90-docs/proof/holochain-langgraph-agent-runtime-smoke-20260509.json`.

Follow-up `call_zome` implementation was started by adding a SweetConductor
smoke binary under `20-actors/magatama/holochain/agent-actor-runtime/smoke/`.
That step pulled the full Holochain conductor/test harness dependency graph
and materially increased compile/deploy weight. The attempt confirmed that
`call_zome` is feasible, but its cost is not justified for the current
platform default.

## Consequences

Gained:

- A concrete runtime lane for local-first agent event validation.
- A reproducible JSON plan that can be registered/published like other
  runtime artifacts.
- A bounded place to test Holochain without weakening the production L3/L5
  architecture.

Constraints:

- This is not the default runtime.
- Holochain hApps expose zome functions through a conductor app websocket; a
  hApp is not itself an HTTP, MCP, or LangGraph server.
- HTTP/MCP/LangGraph integration would require a bridge/sidecar that calls
  zomes and maps the results into those protocols.
- Production use requires reproducible `.happ` build in CI and conductor
  image provenance.
- No public conductor admin API.
- RisingWave remains the source for platform queries, reports, and materialized
  actor state.

Rejected for current production:

- Build graph is heavy: conductor/test harness pulled hundreds of crates beyond
  the zome-only HDK/HDI path.
- Deploy topology is heavier: conductor state, app websocket, admin interface,
  hApp install/enable lifecycle, bridge sidecar, and image provenance are all
  additional moving parts.
- Operational debugging is less direct than the existing HTTP/LangGraph/Spiff
  path.
- The current platform needs centralized orchestration and queryable actor
  memory more than local-first peer validation.

## References

- Holochain developer docs: Application Structure, DNAs, Zomes, Packaging
- ADR-2605080000: Distributed Cognitive Actor System
- ADR-2605082200: LangGraph Row-Driven Runtime
