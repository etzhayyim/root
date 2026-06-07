---
id: adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
title: "ADR: ERC725/ERC-8004 public agent runtime registry for Zeebe and Python k8s workers"
status: accepted
doc_type: adr
topic: erc725-erc8004-agent-runtime
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - ERC725 root identity mapping for public agent/runtime authority
  - ERC-8004-compatible agent discovery for MCP and runtime endpoints
  - k8s pod and IPFS publication model for Zeebe/Python worker runtime
  - persistence boundary for runtime artifacts, receipts, and checkpoints
related:
  - adr-2604262145-erc8004-protocol-root-atproto-profile
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-2604261830-ethereum-anchored-wasm-bpmn-runtime
  - adr-2604261936-ipfs-self-hosted-vultr-b2
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-0056-bpmn-as-actor
  - adr-0049-python-udf-shared-pool-runtime
  - adr-2604261000-mcp-registry-via-kysely-schema
supersedes: []
superseded_by: []
---

# Context

ADR-0074 changed the platform root from `did:etzhayyim` to an ERC725 contract
identity:

```text
did:erc725:etzhayyim:260425:<erc725IdentityContract>
```

ADR-2604261830 already anchors WASM/BPMN/browser/LangGraph artifacts and
execution receipts in `ActorRuntimeRegistry`. ADR-2604251830 defines the live
runtime topology:

- L4 Kotoba/Datomic registry: `actor_registry`, `mcp_registry`, `tool_registry`,
  `process_def`, and BPMN bindings.
- L7 Zeebe BPMN worker: orchestration and durable workflow scheduling.
- L8 Vultr k8s Python pod worker: heavy tool execution, browser, ETL, ML, and
  external IO.
- Private EVM chain `260425`: trust anchor for identity, deploy receipts,
  runtime receipts, credits, staking, and escrow.
- IPFS/B2: content-addressed artifact and evidence storage.

The missing piece is the public agent-runtime surface: other systems should be
able to discover an agent, its MCP endpoint, its runtime artifact, the k8s
execution class backing it, and the onchain trust/reputation/receipt roots
without treating Cloudflare Workers or per-app manifests as the source of truth.

# Decision

Adopt an **ERC725 + ERC-8004-compatible agent runtime registry** on the private
EVM chain, backed by IPFS and k8s runtime manifests.

The contracts remain compact trust anchors. They do not run agents, BPMN,
Python, MCP servers, OAuth, browser sessions, or LLM calls.

```text
Identity:
  ERC725 root identity contract
    -> smart wallet / did:pkh alias
    -> AT facade did:plc / did:web
    -> policy CID / auth method hash / CACAO revocation root

Discovery:
  ERC-8004-compatible AgentIdentityRegistry
    -> agentURI = ipfs://<cid>/agent.json
    -> MCP endpoint, OAuth issuer/resource metadata, A2A endpoint
    -> runtime refs for Zeebe/Python/k8s

Runtime:
  k8s pods in explicit namespaces
    -> Zeebe worker Deployment for BPMN/service tasks
    -> Python worker Deployment/Job/CronJob for tool execution
    -> MCP adapter Service when an agent exposes MCP

Persistence:
  Kotoba/Datomic = operational registry/state
  IPFS/B2 = artifacts, manifests, receipts, traces, evidence
  EVM = hashes, CIDs, identity links, registration, receipts, checkpoints
  Zeebe = workflow instance state
```

## Contract Set

| Contract                   | Standard shape                     | Role                                                                                              |
| -------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------- |
| `etzhayyimRootIdentity`         | ERC725X/ERC725Y-compatible         | Root identity for actor/org/agent/account authority. Stores compact claim keys and pointers only. |
| `etzhayyimRootIdentityRegistry` | platform registry                  | Maps `rootDidHash` and facade DID hashes to ERC725 identity address.                              |
| `AgentIdentityRegistry`    | ERC-8004 identity registry shape   | ERC-721-style agent identity. `agentURI` points to IPFS registration JSON.                        |
| `AgentValidationRegistry`  | ERC-8004 validation registry shape | Records validator, validation request hash, result hash, and validation CID.                      |
| `AgentReputationRegistry`  | ERC-8004 reputation registry shape | Records reputation claims and aggregate roots. Detailed scoring lives offchain.                   |
| `ActorRuntimeRegistry`     | existing ADR-2604261830            | Runtime artifact versions, execution receipts, and actor checkpoints.                             |
| `DeployRegistry`           | existing ADR-0074 Phase 2-A        | `etzhayyim deploy` content hash, commit hash, and optional CID.                                        |

`ActorRuntimeRegistry` remains the runtime provenance anchor. ERC-8004 registry
adds discovery and trust semantics; it does not replace the runtime registry.

## ERC725 Data Keys

ERC725Y keys are deterministic `keccak256` keys. Store only hashes, CIDs, and
addresses.

| Key namespace                       | Value                                                 |
| ----------------------------------- | ----------------------------------------------------- |
| `etzhayyim.root.version`                 | semantic root identity schema version                 |
| `etzhayyim.root.facade.atproto`          | `did:plc` or `did:web` facade DID hash + optional CID |
| `etzhayyim.root.smartAccount.260425`     | ERC-4337 smart account address                        |
| `etzhayyim.root.didPkh.260425`           | linked wallet/smart-account `did:pkh` hash            |
| `etzhayyim.root.policy.cid`              | Rego/RBAC policy bundle CID                           |
| `etzhayyim.root.cacao.revocationRoot`    | revocation Merkle root or CID                         |
| `etzhayyim.root.oauth.subjectHash`       | salted OAuth subject hash pointer                     |
| `etzhayyim.root.webauthn.credentialRoot` | Merkle root of credential claim hashes                |
| `etzhayyim.agent.erc8004.tokenId`        | linked ERC-8004 agent token id                        |

Raw OAuth tokens, passkey public-key material, PII, secrets, and policy bodies
must not be written to chain.

## ERC-8004 Agent Registration JSON

`AgentIdentityRegistry.agentURI(tokenId)` points to an IPFS CID served through
`https://ipfs.etzhayyim.com/ipfs/<cid>`. The registration file is canonical for public
discovery; Kotoba/Datomic remains canonical for internal dispatch. The protocol-root
envelope is defined by ADR-2604262145 as
`https://etzhayyim.com/schemas/erc8004-agent-registration/v1.json`; the older
flat `agent-runtime-registration/v1` shape remains a narrow runtime-oriented
schema and must not be used for new public actor registrations.

```json
{
  "schema": "https://etzhayyim.com/schemas/erc8004-agent-registration/v1.json",
  "agent": {
    "agentRegistry": "eip155:260425:0x...",
    "agentId": "123",
    "agentURI": "ipfs://bafy.../agent.json"
  },
  "rootIdentity": {
    "kind": "erc725-root",
    "chainId": 260425,
    "address": "0x...",
    "rootDid": "did:erc725:etzhayyim:260425:0x...",
    "facadeDids": ["did:web:yoro.etzhayyim.com"],
    "policyCid": "ipfs://bafy..."
  },
  "protocols": [
    {
      "kind": "atproto-xrpc",
      "service": "https://atproto.etzhayyim.com",
      "pdsDid": "did:web:atproto.etzhayyim.com",
      "actorDid": "did:web:yoro.etzhayyim.com",
      "facadeFor": "did:erc725:etzhayyim:260425:0x..."
    },
    {
      "kind": "mcp",
      "endpoint": "https://agent.example.etzhayyim.com/mcp",
      "transport": "streamable-http",
      "auth": {
        "method": "oauth2-dpop",
        "issuer": "https://authn.etzhayyim.com",
        "resource": "https://agent.example.etzhayyim.com/mcp",
        "scopes": ["com.etzhayyim.agent.invoke"]
      }
    },
    {
      "kind": "k8s-runtime",
      "cluster": "murakumo-vke",
      "namespace": "mitama-udf",
      "runtimeKind": "bpmn-zeebe-worker",
      "publicManifestCid": "ipfs://bafy..."
    }
  ],
  "registries": {
    "actorRegistryRow": "actor_registry:<did>",
    "mcpRegistryRow": "mcp_registry:<mcp_id>",
    "toolRegistryRows": ["tool_registry:<tool_nsid>"]
  }
}
```

The registration JSON is public. It must not contain bearer tokens, Kubernetes
secrets, private service URLs that bypass auth, or raw internal credentials.

## Protocol Profile Convention

In public registration documents, `atproto` and `xrpc` are one protocol profile:
`atproto-xrpc`.

The `atproto-xrpc` profile carries both AT Protocol/XRPC wire details and repo
facade metadata as one unit (repo methods, sync methods, DIDs, and collection
bindings). Do not model it as two separate profiles.

```json
{
  "kind": "atproto-xrpc",
  "service": "https://atproto.etzhayyim.com",
  "pdsDid": "did:web:atproto.etzhayyim.com",
  "actorDid": "did:web:yoro.etzhayyim.com",
  "facadeFor": "did:erc725:etzhayyim:260425:0x...",
  "xrpc": {
    "repoMethods": [
      "com.atproto.repo.createRecord",
      "com.atproto.repo.putRecord"
    ],
    "syncMethods": [
      "com.atproto.sync.getLatestCommit",
      "com.atproto.sync.subscribeRepos"
    ]
  }
}
```

## Runtime Classes

| Runtime class   | Existing layer | k8s shape                                                     | Public registration                                                          |
| --------------- | -------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `bpmn-zeebe`    | L7             | Zeebe broker + `zeebe-worker` Deployment + dispatcher Service | `runtimeKind=BpmnZeebe`, BPMN XML CID, Zeebe process id, worker image digest |
| `python-worker` | L8             | Python Deployment, Job, or CronJob                            | image digest, entrypoint, tool NSID list, resource profile                   |
| `mcp-adapter`   | L3/L8 bridge   | HTTP Service exposing MCP over a runtime backend              | MCP endpoint and OAuth resource metadata                                     |
| `wasm-wasi`     | L7 primitive   | WASM module staged in worker image or IPFS-pulled cache       | WASM CID, module sha256, `generic.wasm.run` binding                          |
| `browser-pod`   | L8             | Playwright/CDP Deployment or Job                              | image digest, policy hash, output trace CID                                  |
| `langgraph`     | L7/L8 hybrid   | Python Deployment with durable state in RW/B2                 | graph definition CID and checkpoint root                                     |

The spelling is **Zeebe**, not `zebee`, in file names and registry values.

## k8s Publication Model

Each published runtime has two manifests:

1. **Operational k8s manifest** applied to the cluster.
2. **Public runtime manifest** pinned to IPFS and referenced from ERC-8004.

The public runtime manifest is a redacted projection of the k8s workload:

```json
{
  "schema": "https://etzhayyim.com/schemas/k8s-runtime-public/v1.json",
  "cluster": "vultr-vke-lax",
  "namespace": "mitama-udf",
  "workload": {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "name": "zeebe-worker"
  },
  "image": "ghcr.io/etzhayyim/pymagatama@sha256:...",
  "ports": [
    { "name": "http", "public": false },
    {
      "name": "mcp",
      "public": true,
      "url": "https://agent.example.etzhayyim.com/mcp"
    }
  ],
  "runtime": {
    "kind": "bpmn-zeebe",
    "taskTypes": [
      "generic.db.insert",
      "generic.audit.emit",
      "generic.wasm.run"
    ],
    "resourceProfile": { "cpu": "500m", "memory": "512Mi" }
  },
  "redactions": ["env", "secretRef", "serviceAccountToken", "privateUrl"]
}
```

Rules:

- No resource may be created in the Kubernetes `default` namespace.
- Runtime namespaces are explicit: `mitama-udf`, `yoro-actors`, `ipfs`,
  `geth-private`, or a new `agent-runtime-<domain>` namespace.
- Public manifests must remove `env`, `secretKeyRef`, service-account tokens,
  private RPC URLs, and internal bearer values.
- The public manifest CID is pinned through `ipfs.etzhayyim.com` and stored in both
  Kotoba/Datomic and the ERC-8004 `agentURI` document.

## Build And Deploy Flow

```text
1. Build runtime image
   -> ghcr.io/etzhayyim/<image>@sha256:<digest>

2. Render operational manifest
   -> namespace-specific k8s Deployment/Job/CronJob/Service

3. Render public runtime manifest
   -> redact secrets and private service refs
   -> pin to IPFS

4. Pin artifacts
   -> BPMN XML / WASM module / tool schema / MCP schema / SBOM / provenance
   -> ipfs://<cid>

5. Register or update ActorRuntimeRegistry artifact
   -> artifactId, RuntimeKind, contentHash, policyHash, publisherDid, uri

6. Register or update ERC725 root identity
   -> smartAccount, facade DID, policy CID, agent token id

7. Mint/update ERC-8004 AgentIdentityRegistry token
   -> owner/controller = ERC725 root or linked smart account
   -> agentURI = ipfs://<registration-json-cid>

8. Write L4 Kotoba/Datomic registry rows
   -> actor_registry / mcp_registry / tool_registry / process_def bindings

9. Apply k8s manifest
   -> explicit namespace only

10. Runtime executes jobs
    -> write operational state to Kotoba/Datomic/B2
    -> write traces/evidence to IPFS
    -> record EVM execution receipt/checkpoint when policy requires
```

`DeployRegistry` continues to record `etzhayyim deploy` app-level provenance.
`ActorRuntimeRegistry` records runtime artifact and execution provenance.
`AgentIdentityRegistry` records public discovery identity.

## Implementation Status

As of 2026-04-27, the foundation is implemented in the private-chain contracts,
schemas, k8s annotations, Cloudflare discovery documents, and `etzhayyim` CLI.

Implemented:

- `etzhayyimRootIdentity` and `etzhayyimRootIdentityRegistry` deployed on chain `260425`.
- `etzhayyimAgentRegistry` deployed on chain `260425` at
  `0xcA3480edDAfa39c9377B83eEB18291286C8Cb865`.
- Public schemas:
  - `00-contracts/schemas/agent-runtime-registration.schema.json`
  - `00-contracts/schemas/k8s-runtime-public.schema.json`
- Protocol-root registration envelope:
  `https://etzhayyim.com/schemas/erc8004-agent-registration/v1.json` per
  ADR-2604262145 and the live `public-agent-registration*.json` templates.
- Public runtime renderer:
  `70-tools/scripts/contract/render-agent-runtime-public.py`.
- `etzhayyim agent-runtime render`: renders redacted k8s public runtime JSON.
- `etzhayyim agent-runtime publish`: dry-run hash summary by default; with
  `--dry-run=false`, pins rendered public runtime JSON to `ipfs.etzhayyim.com`
  through the HMAC-protected Kubo API.
- `etzhayyim agent-runtime register`: derives `rootDidHash`, owner, and
  `metadataHash`, then dry-runs or submits
  `etzhayyimAgentRegistry.registerAgent(bytes32,address,string,bytes32)` through
  `cast send`.
- `etzhayyim agent-runtime publish-agent`: one-shot pipeline that renders the public
  k8s runtime manifest, publishes it to IPFS, renders the ERC-8004 agent
  registration JSON with the runtime CID, publishes that registration JSON to
  IPFS, and optionally registers its `agentURI` on `etzhayyimAgentRegistry`. It
  defaults to dry-run, writes to IPFS with `--dry-run=false`, and only submits
  the chain transaction when `--submit-chain` is also set.
- `.well-known` discovery from Cloudflare Workers advertises the
  ERC-8004-compatible runtime discovery surface.

Updated 2026-04-27:

- `did:web:yoro.etzhayyim.com` is linked as an AT facade for the canonical ERC725
  root DID
  `did:erc725:etzhayyim:260425:0xe506d815690ab0b81bf2f34b5057d7b8b96fe643`.
- `etzhayyimRootIdentityRegistry` has the canonical `keccak256(utf8(rootDid))`
  registered for that root identity address, and the facade link points to
  that canonical root hash.
- Kotoba/Datomic projection sync is performed by
  `30-graph/graph-schema/scripts/migrate-rw-erc725-root.mjs`. The projection
  must write `root_did_hash = keccak256(utf8(rootDid))` derived from the
  resolved identity address. A registry-returned root hash may be logged as
  diagnostic state, but must not override the canonical projection hash.
- Actor vector embeddings and AppView semantic actor search use the ERC725
  root DID as the canonical actor key. AT facade DIDs remain profile/display
  and federation keys only.

2026-04-27 onchain transactions:

- `registerRootIdentity`:
  `0x8ec4f45113bd93226fc8caccfd416892ee6da28ec65c186e06f072d6b9f45892`
- `linkFacade`:
  `0x3c1a39efc3e86efd9e1ecdb1b70c91a14ce749748a570012ca26ad655546768a`

Verified locally on 2026-04-27:

```bash
go test . -run TestAgentRuntime -count=1

etzhayyim agent-runtime render \
  --cluster murakumo-vke \
  50-infra/multicluster/murakumo-vke/yoro-actors/actor-workers.yaml

etzhayyim agent-runtime publish --dry-run \
  --cluster murakumo-vke \
  50-infra/multicluster/murakumo-vke/yoro-actors/actor-workers.yaml

etzhayyim agent-runtime register --dry-run \
  --registration 50-infra/multicluster/murakumo-vke/yoro-actors/public-agent-registration.template.json \
  --agent-uri ipfs://<agent-registration-cid> \
  --root-did did:erc725:etzhayyim:260425:<erc725IdentityContract> \
  --owner <evmOwnerAddress>

etzhayyim agent-runtime publish-agent --dry-run \
  --cluster murakumo-vke \
  --registration 50-infra/multicluster/murakumo-vke/yoro-actors/public-agent-registration.template.json \
  --root-did did:erc725:etzhayyim:260425:<erc725IdentityContract> \
  --owner <evmOwnerAddress> \
  50-infra/multicluster/murakumo-vke/yoro-actors/actor-workers.yaml

etzhayyim agent-runtime publish-agent --dry-run=false \
  --ipfs http://144.202.126.131 \
  --cluster murakumo-vke \
  --registration 50-infra/multicluster/murakumo-vke/yoro-actors/public-agent-registration.template.json \
  --registration-out /tmp/yoro-agent-registration.json \
  50-infra/multicluster/murakumo-vke/yoro-actors/actor-workers.yaml
```

`publish-agent --dry-run=false` has been successfully run for `yoro`; ERC-8004
`agentURI` on-chain registration is still pending until `--submit-chain` is
explicitly enabled.

`render` rejects workloads in the Kubernetes `default` namespace. Error output
must preserve the redaction/render failure reason so CI and operators can see
`forbidden default namespace`.

## Persistence Boundary

| Data                     | Primary persistence            |                               Public? | Onchain value                            |
| ------------------------ | ------------------------------ | ------------------------------------: | ---------------------------------------- |
| ERC725 root identity     | EVM                            |                             partially | identity contract state                  |
| Agent discovery document | IPFS/B2                        |                                   yes | CID in ERC-8004 `agentURI`               |
| k8s public manifest      | IPFS/B2                        |                                   yes | CID in agent registration JSON           |
| k8s operational manifest | git + cluster API              |                                    no | hash/CID only if published               |
| Container image          | GHCR                           | digest public/internal by repo policy | digest in IPFS JSON and EVM content hash |
| BPMN XML                 | Kotoba/Datomic + IPFS/B2           |                   yes if public actor | artifact hash/CID                        |
| Zeebe instance state     | Zeebe volume/state             |                                    no | checkpoint or receipt hash only          |
| Python worker output     | Kotoba/Datomic + B2/IPFS           |                depends on sensitivity | outputHash / traceHash                   |
| MCP tool list            | Kotoba/Datomic + public agent JSON |                                   yes | registration hash/CID                    |
| OAuth/session data       | AuthN/AuthZ + D1/RW            |                                    no | salted hash/revocation root only         |
| Execution receipts       | EVM + optional IPFS detail     |                  receipt tuple public | receipt hashes                           |
| Actor checkpoints        | EVM + RW/IPFS evidence         |                           root public | checkpoint root/evidence hash            |

## MCP And OAuth

MCP servers are exposed as public HTTP resources only through an authenticated
edge or runtime adapter. The ERC-8004 document advertises the endpoint and auth
metadata; it does not grant access by itself.

Runtime MCP calls use one of:

| Auth method          | Use                                                           |
| -------------------- | ------------------------------------------------------------- |
| `oauth2-dpop`        | external MCP clients and user-facing tools                    |
| `service-auth-es256` | internal etzhayyim service-to-service calls                        |
| `cacao`              | portable delegated capability crossing etzhayyim boundary          |
| `none`               | read-only public tools only, must be explicitly marked public |

OAuth tokens remain offchain. ERC725 stores only subject hashes, linked method
hashes, policy CIDs, and revocation roots.

## Runtime Receipt Flow

```text
Zeebe ServiceTask / Python worker job
  -> load artifact and policy by artifactId
  -> execute in k8s pod
  -> persist output/evidence to RW + IPFS/B2
  -> compute:
       inputHash
       outputHash
       traceHash
       operatorDid
       artifactId
  -> ActorRuntimeRegistry.recordExecutionReceipt(...)
  -> optional AgentValidationRegistry validation result
  -> optional AgentReputationRegistry reputation claim
```

Receipt submission is policy-driven:

- mandatory for paid/staked/operator-visible jobs
- mandatory for public MCP tools that claim verifiable execution
- optional for internal low-risk jobs
- forbidden for sensitive payload details; only hashes may be onchain

## Operator And Trust Model

Operators are identities, not pods. A k8s pod is one execution placement for an
operator identity.

```text
operatorDid
  -> ERC725 root
  -> smart account / stake / settlement account
  -> k8s service account binding
  -> runtime image signing key
```

Public trust is built from four layers:

1. ERC725 root identity and controller history.
2. ERC-8004 identity/validation/reputation records.
3. IPFS-pinned artifact and public runtime manifest CIDs.
4. Runtime receipts and checkpoints in `ActorRuntimeRegistry`.

## Relationship To Current etzhayyim Architecture

This ADR does not replace the Shannon 8-layer architecture. It publishes it.

| Current layer          | New public surface                                              |
| ---------------------- | --------------------------------------------------------------- |
| L2 PDS/AppView routing | OAuth/DPoP protected entry; no actor state                      |
| L3 dispatcher          | optional MCP/runtime adapter; no authoritative actor definition |
| L4 Kotoba/Datomic registry | internal SSoT mirrored into ERC-8004/IPFS public docs           |
| L5 B2/IPFS             | public artifact and evidence store                              |
| L7 Zeebe               | runtime backend advertised as `bpmn-zeebe`                      |
| L8 Python pod          | runtime backend advertised as `python-worker`                   |
| Private EVM            | ERC725 root + ERC-8004 discovery + runtime receipts             |

Kotoba/Datomic remains the operational SSoT. ERC-8004 is the public/distributed
discovery and trust projection.

# Consequences

## Positive

- etzhayyim gets a standards-aligned public agent discovery surface without moving
  runtime execution into EVM.
- ERC725 becomes the durable authority root for actor/org/agent identities.
- MCP endpoint publication has a single public document, backed by onchain
  identity and IPFS content addressing.
- k8s runtime details are inspectable at the right abstraction level without
  leaking secrets.
- Zeebe and Python workers remain the actual runtime, preserving current
  operational investment.
- Execution receipts and checkpoints become portable audit anchors.

## Negative

- Public registration is now a two-phase consistency problem:
  Kotoba/Datomic internal rows and ERC-8004/IPFS projection must be reconciled.
- ERC725 and ERC-8004 add contract surface area and migration work.
- Public k8s manifests need a redaction pipeline; accidental secret publication
  becomes a real release risk.
- Chain RPC availability matters for public verification, so readers need
  cached snapshots or fallback indexers.

## Security

- No secret material in ERC725, ERC-8004 registration JSON, IPFS manifests, or
  public k8s projections.
- k8s workloads must use explicit namespaces; `default` namespace is prohibited.
- MCP endpoint publication does not imply open access. OAuth/DPoP, ServiceAuth,
  or CACAO must be enforced by the runtime adapter.
- Receipt hashes must be computed over canonical JSON/CAR payloads to avoid
  ambiguous verification.
- ERC725 controller changes, smart-account changes, agent token transfers,
  policy CID changes, and CACAO revocation-root updates require fresh WebAuthn
  or org multisig policy.

# Alternatives Considered

## Olas-style service registry as primary runtime

Rejected for now. Olas is close in spirit, but its Open Autonomy/Tendermint
service model overlaps with the existing Zeebe orchestration layer. etzhayyim should
publish Zeebe/Python workers through ERC-8004 rather than adopting a second
service lifecycle runtime.

## AO/Arweave as primary runtime

Rejected for primary scheduling. AO process execution and WASM checkpointing are
useful as a future backend, but the current platform already has Zeebe and k8s
Python workers. AO can be added later as `runtimeKind=ao-process`.

## IPFS-only discovery

Rejected. IPFS CIDs provide content addressing, not identity, controller
rotation, revocation, reputation, or validation. ERC725/ERC-8004 are needed for
authority and trust state.

## EVM-only storage

Rejected. Full manifests, traces, BPMN XML, WASM modules, and MCP schemas are
too large and too sensitive for direct chain storage. EVM stores hashes and
pointers only.

# Implementation Plan

1. Done: define `etzhayyimRootIdentity` ERC725 key schema and root identity registry.
2. Done: add ERC-8004-compatible identity/validation/reputation registry contracts
   through `etzhayyimAgentRegistry`.
3. Done: add an `agent-runtime-registration` JSON schema and redacted k8s public
   manifest schema.
4. Done for explicit CLI: add `etzhayyim agent-runtime render|publish|publish-agent`
   to render and pin public runtime manifests to `ipfs.etzhayyim.com`. Still pending
   integration into the default `etzhayyim deploy` flow. As part of this, `atproto`
   and `xrpc` are now normalized into the single `atproto-xrpc` profile in
   public protocol registration design.
5. In progress: extend deploy pipeline to register/update `ActorRuntimeRegistry`,
   ERC725 root keys, and ERC-8004 agent URI.
6. Add Kotoba/Datomic reconciliation tables:
   `agent_publication`, `agent_runtime_artifact`, `agent_runtime_receipt`.
7. Add a reconciler that compares Kotoba/Datomic rows, IPFS CIDs, and EVM events.
8. In progress: publish the first runtime:
   `yoro.etzhayyim.com` Zeebe worker + MCP adapter in namespace `yoro-actors`.
9. Publish the shared Python worker runtime in namespace `mitama-udf`.
10. Add verification script:
    `etzhayyim agent verify --did <rootDid>` that resolves ERC725, ERC-8004,
    IPFS, k8s public manifest, and latest runtime receipt.

# References

- ADR-0074: ERC725 Root Identity + Coinbase Smart Wallet Execution Topology
- ADR-2604261830: Ethereum-anchored WASM/BPMN actor runtime
- ADR-2604261936: ipfs.etzhayyim.com self-hosted Kubo on Vultr VKE with B2
- ADR-2604251830: Shannon-optimal layered architecture
- ADR-0056: BPMN-as-actor
- ERC-725: contract-based identity and generic key/value claims
- ERC-8004: trustless agent identity, validation, and reputation registry
