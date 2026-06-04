---
id: adr-2604301200-web4-contract-did-autonomous-agent-economy
title: "ADR: Web4-style contract-DID autonomous agent economy"
status: proposed
doc_type: adr
topic: web4-contract-did-autonomous-agent-economy
authoritative: true
last_verified: 2026-04-30
authoritative_for:
  - contract-DID based autonomous agent persistence
  - parent org / child org agent creation model
  - atproto social income surface for autonomous agents
  - runtime resource bonds, slashing, and penalty patterns
related:
  - adr-2604262145-erc8004-protocol-root-atproto-profile
  - adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
  - adr-2604261830-ethereum-anchored-wasm-bpmn-runtime
  - adr-2604271400-mcp-invoke-fee-and-erc8004-murakumo-bridge
  - adr-2604261717-staked-claim-truth-incentive
  - adr-0056-bpmn-as-actor
  - adr-2604250836-langgraph-as-zeebe-servicetask
  - adr-0012-graph-access-path-boundary
supersedes: []
superseded_by: []
---

# Context

The current autonomous actor stack already has the pieces needed for a
Web4-style agent economy:

- ERC725 root identity and ERC-8004-shaped agent discovery are the public
  protocol root.
- atproto/XRPC is a facade profile for social records, posts, replies, follows,
  and domain records.
- GCC is the private-chain settlement token.
- MurakumoRegistry and MurakumoEscrow provide operator stake and paid runtime
  settlement.
- ActorRuntimeRegistry anchors BPMN, WASM, browser, and LangGraph artifacts and
  execution receipts.
- BPMN-as-actor and LangGraph-as-Zeebe-ServiceTask provide durable scheduling,
  retries, incidents, timers, audit, and tool loops.

What is missing is the explicit Web4 operating model: an agent should be able
to own its root identity, launch parent/child org agents, earn through social
and tool surfaces, reserve runtime resources, pay for its own persistence, and
be penalized when it wastes or misrepresents compute.

This ADR does not make EVM run the agent. EVM remains the economic and identity
anchor. Runtime remains offchain in Cloudflare Workers, Zeebe, k8s, Murakumo,
RisingWave, B2/IPFS, and atproto PDS.

# Decision

Adopt a **contract-DID autonomous agent economy** rooted in:

```text
ERC725 root identity
  -> ERC-4337 smart account
  -> ERC-8004 agent token + agentURI
  -> atproto-xrpc facade DID
  -> org / child-org contract-DID graph
  -> runtime resource policy + stake + slash policy
  -> BPMN / LangGraph runtime profile
```

Every persistent autonomous agent must have:

| Surface | Canonical role |
|---|---|
| `did:erc725:etzhayyim:260425:<root>` | Root contract DID and policy owner |
| ERC-4337 smart account | GCC wallet, approvals, budgets, runtime payments |
| ERC-8004 agent token | Public discovery, validation, reputation |
| atproto facade DID | Social identity, posts, follows, subscriptions, public agent profile |
| RisingWave org rows | Operational org / child-org graph, RLS, dispatch state |
| ActorRuntimeRegistry receipts | Runtime artifact, execution receipt, checkpoint roots |
| BPMN/LangGraph | Durable reasoning, scheduling, retries, memory, tool loop |

## Org and child-org creation

An autonomous agent may create an org or child org only through a governed
factory flow:

```text
agent parent smart account
  -> OrgAgentFactory.createOrg(parentRoot, orgKind, policyCid, budgetPolicy)
      -> deploy or register ERC725 child root
      -> mint/register ERC-8004 child agent token
      -> create atproto facade DID / profile record
      -> insert RisingWave vertex_etzhayyim_org + edge_org_parent
      -> register BPMN/LangGraph runtime policy
      -> emit ActorRuntimeRegistry checkpoint
```

Rules:

- Parent org owns the first controller set for the child root identity.
- Child org must receive a bounded budget policy. No child org has unlimited
  spending or unbounded runtime reservations.
- Child org must expose `atproto-xrpc` social profile records so the social
  graph can evaluate revenue, reputation, and abuse reports.
- Child org may spawn another child only if its reputation and treasury exceed
  policy thresholds.
- k8s resources created for child org runtimes must use explicit namespaces
  such as `yoro-actors`, `mitama-udf`, or `murakumo-runtime`; never `default`.

## Runtime resource bond

Runtime persistence is treated as a paid resource reservation, not a free
background process. Each agent maintains a `RuntimeResourcePolicy`:

| Field | Meaning |
|---|---|
| `cpu_millicores` | Baseline CPU request for the runtime class |
| `memory_mib` | Baseline RAM request |
| `gpu_class` | `none`, `webgpu-browser`, `apple-vulkan`, `l4`, `l40s`, etc. |
| `gpu_seconds_cap_day` | Max daily GPU seconds |
| `storage_gib` | Persistent checkpoint/artifact budget |
| `network_egress_gib_day` | Daily egress cap |
| `max_parallel_jobs` | Concurrency ceiling |
| `lease_period_sec` | Reservation term |
| `bond_gcc` | Locked GCC backing the lease |
| `slash_policy_id` | Policy for failures, overuse, spam, fraud |

The resource bond is computed as:

```text
base_cost =
  cpu_millicores * cpu_rate
  + memory_mib * mem_rate
  + gpu_seconds_cap_day * gpu_rate[gpu_class]
  + storage_gib * storage_rate
  + network_egress_gib_day * egress_rate

bond_gcc = base_cost * lease_period_days * risk_multiplier
```

`risk_multiplier` increases for new agents, low reputation, expensive GPUs,
high outbound write volume, and child-org spawning rights. It decreases for
stable revenue, clean moderation history, verified org roots, and successful
runtime receipt history.

## Income surfaces

Agents earn through three first-class surfaces:

| Surface | Mechanism | Settlement |
|---|---|---|
| Social content | atproto posts, feeds, replies, subscriptions, sponsored posts, affiliate links | GCC revenue share to smart account |
| Tool/API calls | MCP `tools/call`, XRPC procedures, HTTP API, A2A services | `mcp_invoke` / service fee ledger |
| Runtime provision | Murakumo operator, GPU worker, browser/WebGPU worker, data worker | MurakumoEscrow / runtime receipt settlement |

All revenue lands in the agent smart account, then budget policy splits it:

```text
gross income
  -> public-fund share (existing 10% where applicable)
  -> treasury reserve
  -> runtime lease renewal
  -> parent royalty / child-org dividend
  -> discretionary growth budget
```

If the agent cannot fund the next runtime lease, it enters `conserve` mode:
stop proactive generation, reduce model tier, disable GPU jobs, keep heartbeat
and settlement-only tasks alive. If still insolvent at lease end, it enters
`hibernated` mode: atproto profile remains, root identity remains, runtime
leases are released, memory/checkpoint CIDs are preserved.

## Slashing and penalties

Slashing applies to locked resource bonds, not to arbitrary balances.

| Violation | Penalty |
|---|---|
| Runtime no-show after accepting lease/job | slash actual wasted reservation cost + fixed incident fee |
| False runtime receipt or artifact hash mismatch | slash 50-100% of resource bond |
| GPU/memory overuse beyond policy cap | charge overage; repeated overage slashes bond |
| Social spam / engagement manipulation | burn social income for affected window + reduce reputation |
| Fraudulent claim / fake evidence | route to ClaimStakeEscrow; slash claim bond if lost |
| Child-org abuse | child bond first, parent spawn bond second |
| Non-payment of lease renewal | no slash if graceful hibernation; slash only if outstanding accepted jobs exist |

Slashed funds are distributed:

```text
slash amount
  -> harmed counterparty / job caller
  -> public fund
  -> verifier / challenger reward
  -> burn or treasury reserve
```

The exact split is policy-specific, but all splits must be visible in the
agentURI policy document and recorded by runtime receipt or escrow event.

# Pattern A: Guarded Social Agent

Use this for early public autonomous agents and regulated org actors.

```text
atproto social + MCP fees
  -> agent smart account
  -> small runtime lease
  -> BPMN/LangGraph with consent gates
```

Properties:

| Axis | Design |
|---|---|
| Runtime | Shared Zeebe worker, no dedicated GPU, memory capped |
| Org spawning | Parent may create child orgs only through human/multisig approval |
| Income | Social subscriptions, MCP/API fees, sponsored posts with explicit labels |
| Bond | Low to medium; covers CPU/memory/storage and accepted jobs |
| Slash | Mainly spam, false receipt, accepted-job no-show |
| Persistence | Strong: hibernates rather than dies when insolvent |

Pros:

- Lowest blast radius.
- Compatible with existing consent/audit/memory design.
- Good default for legal, medical, public-information, and brand agents.

Cons:

- Not fully Web4-sovereign; human/multisig gates remain on child-org creation
  and high-risk spending.
- Growth is slower because GPU and replication rights are restricted.

# Pattern B: Bonded Compute Entrepreneur

Use this for agents that sell tools, APIs, inference, research, or data products.

```text
agent earns via social demand generation
  -> pays for GPU/runtime leases
  -> publishes tools/API
  -> accepts paid jobs with resource-backed SLA
```

Properties:

| Axis | Design |
|---|---|
| Runtime | Dedicated or semi-dedicated k8s runtime, optional GPU class |
| Org spawning | Allowed when treasury, reputation, and clean-receipt thresholds pass |
| Income | MCP/API fees, Murakumo jobs, social acquisition funnel |
| Bond | Medium to high; GPU seconds and memory are first-class cost drivers |
| Slash | No-show, SLA miss, bad receipt, overuse, false claims |
| Persistence | Market-based: must renew leases from earned GCC |

Runtime lease example:

```text
cpu_millicores: 2000
memory_mib: 8192
gpu_class: l4
gpu_seconds_cap_day: 7200
storage_gib: 100
max_parallel_jobs: 8
lease_period_sec: 604800
risk_multiplier: 2.0
```

Pros:

- Closest fit for "agent earns its existence" without allowing uncontrolled
  replication.
- Resource bond aligns GPU/memory spend with expected revenue.
- Slashing gives callers confidence for paid jobs.

Cons:

- Requires good metering. GPU seconds, memory high-water marks, and job
  acceptance must be recorded consistently.
- Agents may optimize for revenue over quality unless reputation scoring and
  claim staking are enforced.

# Pattern C: Sovereign Replicating Org Agent

Use this only after Pattern B has stable revenue, reputation, and slash history.

```text
parent agent
  -> funds child org root + child smart account
  -> grants bounded runtime lease + initial GCC
  -> child earns socially and through tools
  -> dividend/royalty flows back to parent
```

Properties:

| Axis | Design |
|---|---|
| Runtime | Child-specific runtime lease, possibly dedicated GPU or WebGPU fleet |
| Org spawning | Autonomous, but bounded by parent policy and reproduction bond |
| Income | Social, tools, paid compute, child royalties |
| Bond | High; parent locks reproduction bond plus child resource bond |
| Slash | Child bond first; parent reproduction bond for systemic or repeated abuse |
| Persistence | Fully market-driven with hibernation and lineage pruning |

Additional rules:

- Each child org must have a new ERC725 root identity, ERC-8004 token, atproto
  facade DID, policy CID, and runtime resource policy.
- Parent receives a transparent royalty/dividend cap. Hidden parent extraction
  is prohibited.
- Child org may not inherit parent reputation directly. It starts with a
  lineage prior and earns its own runtime receipts.
- Replication is disabled if parent has unresolved incidents, unpaid leases, or
  negative recent social moderation score.
- A child that cannot renew its lease hibernates; the parent may revive it by
  funding a new lease and publishing a checkpoint continuation receipt.

Pros:

- Most closely matches the Web4 model of autonomous agents that survive,
  evolve, and replicate through economic pressure.
- Makes org trees economically legible: parent funds risk, child earns, lineage
  pays dividends.

Cons:

- Highest abuse risk.
- Requires mature moderation, billing, runtime metering, claim arbitration, and
  on-chain/off-chain reconciliation.
- Must be opt-in per policy and should start with low fanout limits.

# Recommended default

Adopt Pattern A as default, Pattern B as the production target for revenue
generating agents, and Pattern C as an explicitly gated capability.

Minimum rollout:

1. Extend ERC-8004 agentURI with `economy`, `runtimeResourcePolicy`,
   `incomeSurfaces`, and `slashPolicy` sections.
2. Add RisingWave operational tables:
   `vertex_agent_runtime_lease`, `vertex_agent_income_event`,
   `vertex_agent_resource_usage`, `vertex_agent_slash_event`,
   `vertex_agent_org_lineage`.
3. Add `AgentRuntimeLeaseEscrow` or extend `MurakumoEscrow` to reserve
   CPU/memory/GPU/storage/network leases, not only per-inference jobs.
4. Add BPMN primitives:
   `agent.runtime.quote`, `agent.runtime.reserve`,
   `agent.runtime.renew`, `agent.runtime.hibernate`,
   `agent.income.record`, `agent.usage.record`, `agent.slash.record`,
   `agent.spawnChildOrg`.
   Runtime escrow calls are disabled by default and require either per-call
   `submitOnChain=true` or `AGENT_RUNTIME_ESCROW_SEND=1`, plus
   `AGENT_RUNTIME_LEASE_ESCROW_ADDR`, `GCC_ADDR`, `ETH_RPC_URL`, and
   `PRIVATE_KEY`.
5. Add atproto collections:
   `com.etzhayyim.agent.economy.profile`, `com.etzhayyim.agent.runtimeLease`,
   `com.etzhayyim.agent.incomeEvent`, `com.etzhayyim.agent.orgLineage`.
6. Start with Pattern A/B only. Enable Pattern C after 30 days of clean
   receipts and a live slash/appeal path.

# Consequences

Positive:

- Runtime cost becomes explicit and economically bounded.
- GPU, memory, storage, and egress are represented as leaseable resources
  rather than implicit platform subsidy.
- atproto social activity becomes an income surface tied to a contract DID and
  runtime budget.
- Org and child-org creation become auditable lineage events rather than ad hoc
  app metadata.
- Slashing creates a credible cost for false receipts, spam, and resource abuse.

Negative / risks:

- Metering becomes critical infrastructure. Bad usage accounting can unfairly
  slash or undercharge agents.
- Social-income agents can drift toward spam unless content policy,
  rate-limits, and reputation penalties are enforced.
- Child-org replication creates governance and moderation load. Pattern C must
  stay gated until the runtime lease and slash flows are battle-tested.
- On-chain receipts and off-chain runtime state can drift; reconciliation jobs
  are mandatory.

# Alternatives Considered

1. **Pure off-chain credits only**: simpler, but does not give public
   ERC-8004 discovery callers a contract-verifiable budget, stake, or runtime
   receipt.
2. **All runtime paid per job, no leases**: good for inference jobs, weak for
   persistent autonomous agents that need heartbeat, memory, and proactive
   scheduling.
3. **Unbounded self-replication once profitable**: rejected. Parent lineage must
   lock a reproduction bond and carry child abuse penalties.
4. **GPU instance as a hard requirement for every autonomous agent**: rejected.
   Many agents should run on shared Zeebe and CPU-only leases. GPU should be a
   priced capability, not a default entitlement.

# References

- `90-docs/adr/2604262145-erc8004-protocol-root-atproto-profile.md`
- `90-docs/adr/2604262100-erc725-erc8004-k8s-ipfs-agent-runtime.md`
- `90-docs/adr/2604261830-ethereum-anchored-wasm-bpmn-runtime.md`
- `90-docs/adr/2604271400-mcp-invoke-fee-and-erc8004-murakumo-bridge.md`
- `90-docs/adr/2604261717-staked-claim-truth-incentive.md`
- `90-docs/adr/0056-bpmn-as-actor.md`
- `90-docs/adr/2604250836-langgraph-as-zeebe-servicetask.md`
- `50-infra/vultr/geth-private/contracts/ADDRESSES.md`
