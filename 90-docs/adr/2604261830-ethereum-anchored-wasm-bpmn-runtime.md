---
id: adr-2604261830-ethereum-anchored-wasm-bpmn-runtime
title: "ADR: Ethereum-anchored WASM/BPMN actor runtime"
status: active
doc_type: adr
topic: ethereum-anchored-wasm-bpmn-runtime
authoritative: true
last_verified: 2026-04-26
authoritative_for:
  - Ethereum trust anchor for WASM/BPMN/browser/LangGraph runtime artifacts
  - generic.wasm.run BPMN primitive boundary
  - actor source-chain checkpoint anchoring
related:
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-0056-bpmn-as-actor
  - adr-2604240946-yoro-autonomous-actor-hybrid-loop
  - adr-2604251758-murakumo-yoro-actor-worker-fleet
  - adr-0081-worker-direct-hyperdrive-persistence
supersedes: []
superseded_by: []
---

# Context

The actor platform needs an actor-oriented runtime shape without replacing the
existing Kubernetes / Zeebe / Kotoba/Datomic / AT Protocol stack. The desired
properties are close to Holochain's agent-centric model: each actor has an
identity, an append-only action log, validation rules, and checkpoints that can
be audited later. At the same time, the repo already has a private EVM chain
(`260425`) with actor accounts, deploy receipts, GCC, Murakumo operator
registry, and escrow.

Running BPMN, LLMs, browser sessions, or WASM components directly inside EVM is
not practical. The EVM should instead anchor small facts that are expensive to
fake later:

- runtime artifact hash / URI / policy hash
- execution receipt hash tuple
- operator DID
- actor source-chain checkpoint root
- optional stake / escrow settlement through existing Murakumo contracts

# Decision

Adopt an **Ethereum-anchored actor runtime**:

```text
Actor runtime execution:
  Kubernetes / Zeebe / pyzeebe / LangGraph / WASI / browser pods

Operational state:
  Kotoba/Datomic + B2/Arweave/IPFS payloads

Trust anchor:
  private EVM ActorRuntimeRegistry
```

Add `ActorRuntimeRegistry` in `50-infra/vultr/geth-private/contracts/src/`.
It records four runtime kinds:

| Kind | Use |
|---|---|
| `WasmWasi` | deterministic or near-deterministic WASI modules run by `generic.wasm.run` |
| `BpmnZeebe` | BPMN XML process definitions and policy-bound process versions |
| `BrowserPod` | Playwright/CDP browser sessions as actor bodies |
| `LangGraph` | long-running planning graphs |

The registry stores only hashes, URIs, version counters, and receipts. It does
not store full BPMN XML, WASM binaries, browser traces, or memory payloads.

## Worker Primitive

Add `generic.wasm.run` to `pymagatama.zeebe_worker_main`.

Input:

| Field | Meaning |
|---|---|
| `modulePath` | pre-staged WASM module under `WASM_MODULE_DIR` |
| `moduleSha256` | optional `0x` sha256 expected hash |
| `artifactId` | artifact id registered on EVM, or derived from module hash |
| `actorDid` | actor identity, hashed to bytes32 if not already bytes32 |
| `operatorDid` | worker/operator identity, default local pyzeebe worker |
| `jobId` | job id, or derived from module/input/time |
| `input` | JSON payload sent to WASI stdin |
| `args` | CLI args after `--` |
| `timeoutSec` | bounded 1..300 seconds |
| `submitReceipt` | if true, best-effort `cast send` to `ActorRuntimeRegistry` |

Security boundary:

- module path must stay under `WASM_MODULE_DIR`
- module hash is verified before execution when supplied
- default runtime is `wasmtime`
- generic host functions are not exposed
- chain submission is skipped unless `ACTOR_RUNTIME_REGISTRY_ADDR`,
  `ACTOR_RUNTIME_RPC_URL` / `ETH_RPC_URL`, and `PRIVATE_KEY` are present

# Runtime Flow

```text
BPMN process
  -> generic.wasm.run
      -> resolve module under WASM_MODULE_DIR
      -> verify sha256
      -> run WASI module through wasmtime
      -> compute input/output/trace hashes
      -> optional ActorRuntimeRegistry.recordExecutionReceipt(...)
  -> generic.audit.emit / domain write
```

For richer execution:

```text
ActorRuntimeRegistry.registerArtifact(...)
MurakumoRegistry operator selection
MurakumoEscrow submit/settle when a paid external operator is used
ActorRuntimeRegistry.recordExecutionReceipt(...)
ActorRuntimeRegistry.recordActorCheckpoint(...)
```

# Holochain / AO Positioning

This ADR imports the Holochain-like idea of actor-owned source chains and
validation, but does not adopt Holochain's DHT/conductor runtime. Source-chain
records live in Kotoba/Datomic / AT Protocol records, and checkpoint roots are
anchored on EVM.

AO/Arweave remains a compatible mirror layer: payloads, traces, or checkpoint
evidence can be stored on Arweave/AO and referenced by URI/hash in the EVM
registry. AO is not the primary scheduler; Zeebe remains the scheduler.

# Consequences

Positive:

- Ethereum becomes the authority layer for runtime provenance without becoming
  the runtime itself.
- WASM modules can be introduced as sandboxed BPMN primitives.
- Actor source-chain roots can be periodically anchored.
- Existing DeployRegistry / MurakumoRegistry / MurakumoEscrow remain usable.

Trade-offs:

- WASI execution is only as deterministic as the module and exposed host
  environment. The generic primitive intentionally exposes no rich host
  functions.
- Receipt submission is best-effort from the worker and depends on `cast` plus
  chain credentials.
- Full fraud proofs are out of scope; use stake/slash, quorum, or TEE
  attestation in later ADRs if a workload needs stronger guarantees.

# Implementation

- `50-infra/vultr/geth-private/contracts/src/ActorRuntimeRegistry.sol`
- `50-infra/vultr/geth-private/contracts/script/DeployActorRuntime.s.sol`
- `20-actors/magatama/py/src/pymagatama/zeebe_worker_main.py`
  - task type: `generic.wasm.run`

# Deployment

`ActorRuntimeRegistry` is deployed on private chain `260425`:

| Field | Value |
|---|---|
| Address | `0x9C730960e9BF7A403E610Dca0C8a565CF655b6a1` |
| Owner | `0xaFed0Cb7633EDBd26aA52658e71528309F562501` |
| Block | `0x5916` (22806) |
| Tx | `0x7efa15dbaddb9110992f30a746e4eb18cb4cb6f0360ac3bf3c87f10eb382967c` |
| Broadcast log | `50-infra/vultr/geth-private/contracts/broadcast/DeployActorRuntime.s.sol/260425/run-latest.json` |

Sanity reads on 2026-04-26:

- `owner()` → sealer
- `openRegistration()` → `false`
- `openReceipt()` → `false`

## Yoro Runtime Rollout

`yoro.etzhayyim.com` is the first live actor-worker deployment wired to this ADR.
The VKE member cluster runs the runtime in namespace `yoro-actors`; no resources
are created in `default`.

| Component | Value |
|---|---|
| Zeebe worker | `deployment/yoro-actor-zeebe-worker` |
| MCP adapter | `deployment/yoro-mcp-adapter` |
| Image | `ghcr.io/etzhayyim/pymagatama:yoro-actor-runtime-20260426-receipts` |
| WASM runtime | `wasmtime 44.0.0` |
| Receipt CLI | `cast 1.5.0` |
| Registry RPC | `http://geth-private.geth-private.svc.cluster.local:8545` |
| Secret | `yoro-actor-runtime-secrets/PRIVATE_KEY` |

Live verification on 2026-04-26:

- both yoro runtime deployments rolled out `1/1`
- `cast --version` and `wasmtime --version` succeeded inside the Zeebe worker pod
- `generic.wasm.run` executed a pre-staged `noop.wat` module
- smoke artifact registered as `WasmWasi`
- `submitReceipt=true` recorded an `ExecutionReceipt` on `ActorRuntimeRegistry`
- `receipts(jobId)` returned the recorded tuple from chain

Smoke artifact:

| Field | Value |
|---|---|
| Artifact id / content hash | `0x6610f7ed558c7ee3ca3f4833a4c6f979b7845724f17aa26007b9823ffb77affd` |
| Artifact registration tx | `0xa3f78542985f02ba57b377ca115d48363a8ad8db88af1bc0ca04948e691f72b3` |
| Receipt job id | `0xa51f190402e5977b4bf4d1fc566b924270be0a453ae1bec982c22d5192e1e9b5` |
| Receipt tx | `0x3486a116867667109e6c4c8b00e2106a3e776c762a0e03ed6997aa47c473e42a` |
