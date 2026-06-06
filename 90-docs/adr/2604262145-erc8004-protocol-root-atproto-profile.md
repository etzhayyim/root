---
id: adr-2604262145-erc8004-protocol-root-atproto-profile
title: "ADR: ERC725/ERC-8004 is the protocol root; atproto/XRPC is a protocol profile"
status: active
doc_type: adr
topic: erc8004-protocol-root
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - etzhayyim public protocol root after the Ethereum identity migration
  - Relationship between ERC725, ERC-8004, atproto, XRPC, MCP, A2A, k8s, and IPFS
  - How AT Protocol repo commits are represented inside ERC-8004 agent discovery
  - Naming rule that prevents every public interface from being classified as atproto
related:
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
  - adr-2604261830-ethereum-anchored-wasm-bpmn-runtime
  - adr-2604261936-ipfs-self-hosted-vultr-b2
  - adr-2604251220-record-log-not-mst
  - adr-2604241121-repo-commit-stays-on-pds
  - adr-2604231811-atproto-extension-service-layers
supersedes:
  - adr-2604231811-atproto-extension-service-layers
superseded_by: []
---

# Context

The previous platform language treated nearly every public surface as
"atproto": XRPC, repo records, actor Workers, MCP facades, DID directories,
runtime workers, inference fleets, and public app views. That was acceptable
while the PDS was the only public trust anchor.

ADR-0074 and ADR-2604262100 changed the root. etzhayyim public authority is now
anchored in Ethereum identity:

- ERC725 root identity contracts hold durable controller, policy, facade DID,
  and revocation pointers.
- ERC-8004-style agent registries publish agent identity, validation, and
  reputation records.
- `agentURI` documents are pinned to IPFS and served through `ipfs.etzhayyim.com`.
- Runtime execution remains offchain in Zeebe, Python/k8s workers, MCP
  adapters, Cloudflare Workers, Kotoba/Datomic, B2, and AT Protocol PDS surfaces.

Therefore "atproto" can no longer be the umbrella protocol name. It is one
profile inside the public agent protocol stack.

This ADR defines the new vocabulary and boundary. It intentionally does not
move repo commit execution off the PDS; ADR-2604241121 and ADR-2604251220 still
govern that write path.

# Decision

etzhayyim's public protocol root is **ERC725/ERC-8004**.

All other public interfaces are **protocol profiles** advertised by an
ERC-8004 agent registration document and controlled by an ERC725 root identity.

```text
ERC725 root identity
  -> controller / smart account / policy CID / facade DID hashes
  -> ERC-8004 AgentIdentityRegistry token
      agentRegistry = eip155:260425:<identityRegistry>
      agentId       = <tokenId>
      agentURI      = ipfs://<cid>/agent.json
          -> protocol profiles:
               atproto-xrpc
               mcp
               a2a
               http-api
               k8s-runtime
               ipfs-artifact
               evm-receipt
```

## Protocol Layer Names

Use these names in ADRs, manifests, registry rows, and public documents:

| Layer | Name | Canonical role |
|---|---|---|
| P0 | `erc725-root` | Durable root identity, controllers, policy pointers, facade DID hashes. |
| P1 | `erc8004-agent` | Public agent identity, discovery, validation, reputation. |
| P2 | `ipfs-publication` | Public content-addressed documents, manifests, artifacts, evidence. |
| P3 | `evm-runtime-receipt` | Artifact registration, execution receipt, checkpoint, validation, reputation hashes. |
| P4 | `atproto-xrpc` | AT Protocol repo/profile/social record surface over XRPC. |
| P5 | `mcp` | Tool discovery and invocation surface. |
| P6 | `a2a` | Agent-to-agent interaction endpoint. |
| P7 | `http-api` | Non-XRPC HTTP API surface. |
| P8 | `k8s-runtime` | Operational runtime placement for Zeebe, Python workers, jobs, cronjobs, and adapters. |

`atproto-xrpc` is a first-class profile, not the root protocol. New public
surfaces must not be described as "atproto" unless they actually implement AT
Protocol repo, sync, identity, OAuth/DPoP, or XRPC semantics.

## ERC-8004 Agent Registration Envelope

Every public actor/agent MUST have one registration envelope:

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
  "protocols": []
}
```

The `protocols` array is the only place where atproto, XRPC, MCP, A2A, HTTP,
k8s, IPFS, and EVM receipt details are published. This keeps ERC725/ERC-8004
as the public authority root while letting each protocol retain its native
semantics.

## atproto/XRPC Profile

AT Protocol is represented as a profile inside `protocols`:

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
      "com.atproto.repo.putRecord",
      "com.atproto.repo.deleteRecord",
      "com.atproto.repo.applyWrites",
      "com.atproto.repo.uploadBlob"
    ],
    "syncMethods": [
      "com.atproto.sync.getLatestCommit",
      "com.atproto.sync.subscribeRepos",
      "com.atproto.sync.getRecord",
      "com.atproto.sync.getBlob"
    ]
  },
  "repo": {
    "writeAuthority": "pds-singleton",
    "storageShape": "append-only-record-log",
    "commitLog": "vertex_repo_commit",
    "recordLog": "vertex_repo_record",
    "mstCar": "not-authoritative",
    "federation": "etzhayyim-internal"
  },
  "collections": [
    "app.bsky.feed.post",
    "app.bsky.actor.profile",
    "com.etzhayyim.yoro.*"
  ],
  "blob": {
    "uploadBlobStore": "b2",
    "ipfsMirror": "planned",
    "gateway": "https://ipfs.etzhayyim.com"
  }
}
```

Rules:

- XRPC remains the wire protocol for `com.atproto.*` and compatible app
  lexicons.
- Repo commits remain owned by the PDS singleton. ERC-8004 does not become a
  repo writer.
- The atproto DID is a facade DID linked from ERC725. It is not the root
  identity.
- `vertex_repo_commit` and `vertex_repo_record` remain the operational commit
  and record logs for etzhayyim's PDS.
- CAR/IPLD/CID values may be published through IPFS, but IPFS is not the
  authoritative AT Protocol repo host. The PDS is.

## MCP Profile

MCP is represented independently from atproto:

```json
{
  "kind": "mcp",
  "endpoint": "https://yoro.etzhayyim.com/mcp",
  "transport": "streamable-http",
  "auth": {
    "method": "oauth2-dpop",
    "issuer": "https://authn.etzhayyim.com",
    "resource": "https://yoro.etzhayyim.com/mcp",
    "scopes": ["com.etzhayyim.agent.invoke"]
  },
  "toolsCid": "ipfs://bafy..."
}
```

MCP tool publication does not imply AT Protocol repo access. If a tool writes
an AT record, it must call the PDS `atproto-xrpc` profile or a governed BPMN
task that calls that profile.

## k8s Runtime Profile

k8s is an execution placement profile:

```json
{
  "kind": "k8s-runtime",
  "cluster": "murakumo-k3s",
  "namespace": "yoro-actors",
  "workload": {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "name": "yoro-actor-zeebe-worker"
  },
  "image": "ghcr.io/etzhayyim/pymagatama@sha256:...",
  "entrypoint": ["python", "-m", "pymagatama.zeebe_worker_main"],
  "runtimeKind": "bpmn-zeebe-worker",
  "publicManifestCid": "ipfs://bafy..."
}
```

No k8s resource may be created in the `default` namespace. Public manifests are
redacted projections only; they must not include secrets, service-account
tokens, private RPC credentials, or unprotected internal endpoints.

## EVM Receipt Profile

Runtime receipts, validation results, and reputation updates are represented as
EVM profiles linked to the agent:

```json
{
  "kind": "evm-runtime-receipt",
  "chainId": 260425,
  "actorRuntimeRegistry": "0x...",
  "artifactId": "0x...",
  "latestCheckpoint": "0x...",
  "validationRegistry": "0x...",
  "reputationRegistry": "0x..."
}
```

The EVM profile stores hashes and CIDs, not payloads. Sensitive traces remain
in Kotoba/Datomic/B2/IPFS according to policy, with only commitments onchain.

## Naming And Migration Rule

Replace ambiguous phrases as follows:

| Old phrase | New phrase |
|---|---|
| "atproto is the platform protocol" | "ERC725/ERC-8004 is the public protocol root." |
| "actor is an atproto service" | "actor is an ERC-8004 agent with protocol profiles." |
| "XRPC protocol" | "`atproto-xrpc` profile." |
| "PDS owns actor state" | "PDS owns AT repo commits; ERC725/ERC-8004 owns public agent identity." |
| "IPFS is atproto public surface" | "`ipfs-publication` profile for artifacts and mirrors; PDS remains AT repo host." |
| "k8s pod is an actor" | "k8s pod is a runtime placement for an ERC-8004 agent." |

ADR-2604231811's 15-layer atproto taxonomy is superseded by this profile model.
The old layer names may remain in historical docs, but new decisions must use
the ERC725/ERC-8004 protocol root vocabulary.

# Consequences

## Positive

- Public identity, discovery, validation, and reputation no longer depend on
  AT Protocol terminology.
- AT Protocol keeps its correct scope: repo, sync, identity, social/profile,
  blob upload, OAuth/DPoP, and XRPC wire semantics.
- MCP, A2A, k8s, IPFS, and EVM receipts can evolve without being forced into
  AT Protocol service categories.
- The agent registration document becomes the single public map of all
  protocol surfaces for one actor/agent.
- `ipfs.etzhayyim.com` has a clear role: publication and evidence, not replacement
  PDS authority.

## Negative

- Docs and code comments that use "atproto" as the umbrella term need gradual
  cleanup.
- Public registration consistency now spans ERC725, ERC-8004, IPFS, Kotoba/Datomic,
  and live runtime deployments.
- Verification tools must resolve multiple profiles instead of only querying
  the PDS.

# Operational Invariants

- ERC725 root identity is the highest public authority for an actor/agent.
- ERC-8004 agent registration is the highest public discovery document.
- atproto/XRPC is only the profile for AT Protocol repo and social surfaces.
- PDS remains the only writer for AT repo commits.
- Runtime pods are placement, not identity.
- IPFS CIDs are publication/evidence pointers, not controller authority.
- Secrets never appear in ERC725Y values, ERC-8004 JSON, IPFS manifests, or
  redacted k8s public manifests.
- Kubernetes `default` namespace remains prohibited for etzhayyim resources.

# Implementation Plan

1. Done for public templates: add `erc8004-agent-registration/v1` as the
   protocol-root envelope used by live `public-agent-registration*.json`
   templates. The older `agent-runtime-registration/v1` schema remains a
   flat runtime-oriented shape and is not the canonical public actor envelope.
2. Done for explicit runtime publisher: extend the deploy publisher to render
   `protocols[]` with at least
   `atproto-xrpc`, `mcp`, `k8s-runtime`, `ipfs-publication`, and
   `evm-runtime-receipt` profiles.
3. Done for `yoro`: pin agent registration JSON and redacted runtime manifests
   through `ipfs.etzhayyim.com`.
4. Pending chain submit: store the registration CID in ERC-8004 `agentURI`.
5. Store facade DID hashes, policy CID, and ERC-8004 agent token id in ERC725Y.
6. Add `etzhayyim agent verify` to resolve:
   ERC725 root -> ERC-8004 agentURI -> IPFS JSON -> profile endpoints ->
   latest EVM receipt/checkpoint.
7. Update docs and manifests when touched to replace umbrella "atproto" wording
   with the correct profile name.

# Alternatives Considered

## Keep atproto as the umbrella protocol

Rejected. ERC725 and ERC-8004 now carry root identity and public discovery.
Calling MCP, k8s runtimes, IPFS artifacts, EVM receipts, and A2A endpoints
"atproto" hides the real authority boundary and causes future design drift.

## Make ERC-8004 replace AT Protocol

Rejected. ERC-8004 discovers and helps trust agents; it does not define AT repo
records, XRPC methods, blob upload semantics, social profile records, or repo
sync. AT Protocol remains the correct profile for those surfaces.

## Use IPFS as the umbrella protocol

Rejected. IPFS provides content addressing and publication. It does not provide
controller rotation, agent ownership, validation registry, reputation registry,
or PDS repo write semantics.

# References

- ERC-725: https://eips.ethereum.org/EIPS/eip-725
- ERC-8004: https://eips.ethereum.org/EIPS/eip-8004
- AT Protocol repository specification: https://atproto.com/specs/repository
- ADR-0074: Ethereum identity bridge via WebAuthn, SIWE/CACAO, and smart wallet
- ADR-2604262100: ERC725/ERC-8004 public agent runtime registry
- ADR-2604251220: etzhayyim PDS uses append-only record log, not AT Protocol MST CAR
- ADR-2604241121: Repo commit stays on PDS
- ADR-2604261936: ipfs.etzhayyim.com self-hosted Kubo on Vultr VKE with B2
