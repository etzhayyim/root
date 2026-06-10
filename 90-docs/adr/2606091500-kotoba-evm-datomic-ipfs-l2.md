---
id: adr-2606091500-kotoba-evm-datomic-ipfs-l2
title: "ADR-2606091500: kotoba-EVM — a Datomic+IPFS EVM-compatible L2 (geth-less); kotoba IS the chain"
status: proposed
doc_type: adr
topic: kotoba-evm-l2
authoritative: true
last_verified: 2026-06-09
priority: 8.0
axis: substrate-boundary
weight: 0.85
priority_note: "Removes the last external single-point-of-failure from the religious-corp substrate: geth-private (a single-sealer Clique PoA chain on Vultr VKE) is the host for GCC + every escrow (ClaimStakeEscrow, MishmarBondEscrow, MurakumoRegistry, …) — and on 2026-06-09 its public RPC returned HTTP 502 (in-cluster geth / tunnel down), which alone froze the entire on-chain economy + blocked the Mishmar persistence loop (ADR-2606082100). Depending on an operator-run external chain contradicts both the unstoppability goal and the standing 'blockchain-self-contained' rule (root CLAUDE.md: Datom log = FIRST-CLASS canonical state, IPFS = block backend, Base L2 = trust anchor). This ADR collapses the EVM execution layer INTO kotoba: kotoba becomes its own EVM-compatible L2 — state = Datom log, DA = IPFS, blocks = CommitDag, settlement anchored to Base L1, execution = revm over a Datom-backed Database, and kotoba serves the eth_* JSON-RPC so Solidity/forge/viem + the existing contracts run unchanged. No geth."
authoritative_for:
  - kotoba-EVM L2 architecture — Datom state model, CommitDag-as-block, revm execution, IPFS DA, Base L1 anchor
  - geth-less migration — retire geth-private as the contract host; redeploy GCC + escrows onto kotoba-EVM
  - eth_* JSON-RPC compatibility surface kotoba serves (geth/viem/forge parity)
  - EVM-on-Datomic gas/fee model under the Charter (gas-as-write-cost, no speculative gas market)
depends_on:
  - "2605262130"  # kotoba canonical storage substrate — Datom log is the engine this extends
  - "2605312345"  # Datom log = first-class canonical state; IPFS block backend; Base L2 trust anchor
  - "2606082100"  # Mishmar Storage Covenant — its escrows move from geth-private onto kotoba-EVM
  - "2605172300"  # AnchorBridge — reused to anchor the kotoba-EVM state root to Base L1
  - "2605240001"  # kotoba cleanroom — gas + CitationLedger primitives (gas model alignment)
  - "2605192100"  # mission charter — blockchain-self-contained, multi-generational stewardship
  - "2605192200"  # Charter Rider — §2(b) no speculative finance (gas/fee constraint)
related:
  - "2604261717"  # ClaimStakeEscrow — a contract that redeploys onto kotoba-EVM
  - "2605215000"  # Murakumo-only — kotoba-EVM sequencer/validator runs on the fleet
  - "50-infra/vultr/geth-private/"             # the chain this supersedes as the contract host
  - "50-infra/etzhayyim-chain-contracts/"      # AnchorBridge.sol + TitheRouter.sol
supersedes: []
superseded_by: []
---

# ADR-2606091500: kotoba-EVM — a Datomic+IPFS EVM-compatible L2 (geth-less)

**Status**: proposed
**Date**: 2026-06-09
**Deciders**: Jun Kawasaki

> kotoba does not *talk to* a chain. kotoba **is** the chain — an EVM-compatible L2
> whose state is the Datom log, whose data availability is IPFS, whose blocks are
> the CommitDag, and whose finality is a Base L1 anchor. No geth.

## Context

The religious-corp's on-chain layer is **geth-private** — a single-sealer Clique
PoA Ethereum chain on Vultr VKE (chainId 260425), hosting GCC and every contract
(`ClaimStakeEscrow`, `MishmarBondEscrow`, `MurakumoRegistry`, `AnchorBridge`,
`TitheRouter`, …). It is reached over `https://geth.etzhayyim.com` (CF Worker →
Cloudflare Tunnel → in-cluster geth).

Two facts make this the substrate's weakest link:

1. **It is an external single-point-of-failure.** On 2026-06-09 `eth_chainId`
   against `geth.etzhayyim.com` returned **HTTP 502** (in-cluster geth / tunnel
   down). A single pod outage froze the entire on-chain economy and blocked the
   Mishmar persistence loop (ADR-2606082100) — exactly the kind of operator
   dependency the unstoppability analysis set out to remove.
2. **It contradicts the standing substrate rule.** Root `CLAUDE.md` already
   declares the **kotoba Datom log the FIRST-CLASS canonical state**, with IPFS as
   the block backend and Base L2 as a *trust anchor* (ADR-2605262130 / 2605312345).
   geth-private is a *second*, non-content-addressed, non-anchored source of truth
   bolted on the side. The substrate is supposed to be **blockchain-self-contained**.

kotoba already carries the cryptographic half of EVM compatibility — `keccak256`,
EIP-55 addresses, secp256k1 recovery, ABI encode/decode, EIP-191/1271
(`kotoba-auth/eth/*`) — but only as a **read+verify** surface onto *external*
chains. The missing half is **execution + state + the JSON-RPC server**.

## Decision

Build **kotoba-EVM**: an EVM-compatible L2 collapsed *into* kotoba. There is no
separate chain process — a kotoba node IS the sequencer/state machine.

```
            ┌──────────────────────────────────────────────────────────┐
            │ kotoba node = kotoba-EVM L2                                │
            │                                                            │
            │  eth_* JSON-RPC  ◀── forge / viem / contracts (unchanged)  │
            │      │                                                     │
            │  revm execution ──▶ DatomDatabase (state as Datoms)        │
            │      │                    │                                │
            │  block = CommitDag commit (txList CID, stateRoot, parent)  │
            │      │                    │                                │
            │  DA = IPFS CARv1 per block        state Datoms in ProllyTree│
            └──────────────────────────────────────────────────────────┘
                          │ AnchorBridge.commitRoot(stateRoot, blockCid)
                          ▼
                    Base L1 (trust anchor / tamper-evidence / fork-choice root)
```

### 1. State model — EVM accounts/storage AS Datoms

The EVM world-state is projected into the canonical Datom log (entity = the
20-byte address as a CID via `from_bytes`):

| Datom predicate | value | EVM meaning |
|---|---|---|
| `evm/acct/<addr>/nonce` | Integer | account nonce |
| `evm/acct/<addr>/balance` | Bytes(u256-be) | account balance (wei) |
| `evm/acct/<addr>/codehash` | Cid | keccak256(code) → code blob CID |
| `evm/code/<codehash>` | Bytes | contract bytecode (content-addressed) |
| `evm/storage/<addr>/<slot>` | Bytes(32) | storage slot value |

The **state root** is the ProllyTree root over the `evm/*` Datoms (content-addressed,
deterministic) — kotoba's existing index machinery gives a verifiable state
commitment for free. `as-of` time-travel (TEA) yields historical state.

### 2. Block model — a CommitDag commit IS an EVM block

The CommitDag (kotoba's WAL/chain, ADR-2605262130) is the block chain. Each EVM
block is one commit carrying: `parent` (prev block CID), `number`, `timestamp`,
`txList` CID (the ordered txs, RLP), `stateRoot` (post-exec ProllyTree root),
`receiptsRoot`, `logsBloom`. Block hash = the commit CID. No new chain structure —
blocks are commits with EVM headers.

### 3. Execution — revm over a Datom-backed `Database`

Adopt **revm** (the standard Rust EVM) as the execution engine; implement its
`Database` trait (`basic`/`code_by_hash`/`storage`/`block_hash`) as
**`DatomDatabase`** reading the `evm/*` projection (hot Arrangement → ProllyTree
cold). Apply a tx → revm returns the state diff → commit as `evm/*` Datom
asserts/retracts in one CommitDag commit. Typed-tx (legacy / EIP-2930 / EIP-1559)
RLP decode + secp256k1 sender recovery reuse `kotoba-auth` `keccak256` + `k256`.

### 4. Data availability — IPFS CARv1 per block

Each block's tx blob + the state-diff blocks pack into a CARv1 bundle pinned to
IPFS (kotoba's existing cold tier + B2 mirror). DA is content-addressed and
permissionlessly re-fetchable — anyone can replay the chain from `genesis` block
CID + the CAR bundles, recomputing every state root. **This is the unstoppability
win over geth-private**: the chain is verifiable + forkable from public data, not
trapped in one PoA node's leveldb.

### 5. Finality / settlement — Base L1 anchor of the state root

Reuse `AnchorBridge.commitRoot(stateRoot, blockCid, number)` (ADR-2605172300) to
anchor the kotoba-EVM state root to Base L1 on a cadence — the same trust-anchor
role Base already plays for the Datom commit-DAG. R0 trust model = single
sequencer (the operator node) + public DA + L1 anchor (≈ "validium/optimistic
without proofs yet"); validity/fraud proofs are future work (§Roadmap).

### 6. eth_* JSON-RPC compatibility — kotoba serves it

kotoba serves the geth/viem subset so Solidity tooling + the existing contracts
run **unchanged** against kotoba-EVM:

- reads: `eth_chainId`, `eth_blockNumber`, `eth_getBalance`, `eth_getTransactionCount`,
  `eth_getCode`, `eth_getStorageAt`, `eth_call`, `eth_estimateGas`, `eth_getLogs`,
  `eth_getBlockByNumber/Hash`, `eth_getTransactionReceipt`.
- writes: `eth_sendRawTransaction` (decode → revm → commit block).

`forge create … --rpc-url <kotoba-node>` deploys onto kotoba-EVM. A distinct
`chainId` (e.g. `0x6b6f74` "kot") identifies the chain; genesis seeds GCC + the
Council Safe.

### 7. Gas / fee model under the Charter

Gas is metered (revm) but **not a speculative market** (§2(b)). Fees are paid in
the existing internal unit: gas → mKOTO at a Council-set tariff (ADR-2605282100),
mirroring the `econ.rs` write-cost economy — the operator/genesis account is the
fee sink, no MEV, no base-fee burn auction. EOAs of covenant members are
gas-exempt up to a quota (donation-funded), like the existing write-cost exemption.

## Migration (geth-less)

1. Deploy GCC + `AnchorBridge`/`TitheRouter` + `MishmarBondEscrow` +
   `ClaimStakeEscrow` + `MurakumoRegistry` onto kotoba-EVM (genesis + `forge`).
2. Repoint `KOTOBA_EVM_RPC_URL` (the Mishmar tick, ADR-2606082100 deploy) from
   `geth.etzhayyim.com` to the local kotoba-EVM RPC — the social-economy loop now
   observes its *own* chain.
3. Retire the Vultr VKE single-sealer geth-private (keep its history exported to
   IPFS for audit). `geth.etzhayyim.com` becomes a thin proxy to a kotoba-EVM node.

## Consequences

### Positive
- **No external chain SPOF** — the 502 class of outage cannot freeze the economy;
  the chain lives wherever a kotoba node + the IPFS CARs live (the donated mesh).
- **Verifiable + forkable** — content-addressed state + public DA + L1 anchor; the
  chain is reconstructible from genesis CID by anyone (Bitcoin-grade auditability,
  Holochain-grade portability — the unstoppability axes the analysis targeted).
- **One substrate** — Datom log is *the* state for both the knowledge graph and the
  EVM; one ProllyTree, one IPFS tier, one anchor.
- **Ecosystem kept** — Solidity, forge, viem, and every existing contract work
  unchanged; the EVM read+verify surface (`kotoba-auth/eth`) is reused for tx/sig.

### Negative / honest
- **revm is a heavy dependency** + a real execution-correctness surface (must track
  EVM semantics + hardforks). Mitigated by using the audited revm, not a hand-rolled VM.
- **R0 is a single sequencer** (the operator node) — censorship-resistant only via
  public DA + the right-to-fork, not yet via decentralized sequencing or proofs.
  Same trust as geth-private PoA today, but now content-addressed + anchored.
- **JSON-RPC completeness** is a long tail (filters, tracing, fee history) — ship
  the forge/viem-critical subset first.
- **Gas-as-write-cost** must be designed to not become a speculative market (§2(b));
  the tariff is Council-set, not auction-priced.

### Neutral
- Base L2 keeps exactly its current role (trust anchor) — unchanged by this ADR.
- kotoba-EVM is an *L2/sovereign rollup*, explicitly **not** a new L1 token chain;
  GCC remains the unit, no new gas token is minted.

## Roadmap (increments)

| R | Scope |
|---|---|
| **R0** ✅ | EVM state model as Datoms (`evm/*`) + read-side eth_* projection (`eth_chainId`/`getBalance`/`getTransactionCount`/`getCode`/`getStorageAt`) over a Datom view — **LANDED** in `kotoba-kqe::evm_state` (kotoba#91): `EvmStateView` reducer + `account_datoms`/`storage_datom` + geth/viem `quantity_hex`/`data_hex` encodings, 6 tests, `KOTOBA_EVM_CHAIN_ID` `0x6b6f74` |
| **R1** ✅ | revm + `DatomDatabase` execution over the Datom state — **LANDED** in the `kotoba-evm` crate (kotoba#92): `revm 14` `DatabaseRef` over `EvmStateView`, `apply_call` (message-call → `ExecOutcome` + `evm/*` state-diff Datoms), `state_to_datoms`; verified value-transfer executes + balances/nonce round-trip through the produced Datoms; gas priced 0 (§2(b)). |
| **R1b** ✅ | signed-tx decode + secp256k1 sender recovery → `eth_sendRawTransaction` — **LANDED** `kotoba-evm::tx` (kotoba#93): hand-rolled RLP + `kotoba-auth` keccak/recover (no alloy — avoided a revm-14 `alloy-eip7702` conflict), validated vs the canonical EIP-155 vector. (typed 2930/1559 envelopes + `eth_call`/`estimateGas` RPC surface = follow-up.) |
| **R2** ✅ (core) | block production — **LANDED** `kotoba-evm::block` (kotoba#93): `EvmBlock` + `produce_block` (ordered multi-tx exec over an evolving view → `evm/*` state-diff Datoms + content-addressed `state_root` (`EvmStateView::state_root`) + block CID; bad-tx reject). **R2.5 ✅ LANDED** `kotoba-evm::chain` (kotoba#95): `EvmChain` over a `BlockStore` — `commit_block` content-addresses each diff Datom + bundles a **CARv1** (root = block CID; IPFS-pinnable DA) + stores the header (parent + state_root + datom CIDs) + advances head; `read_block` replays the block from the store (verified: recipient credited). (CommitDag head-ref wiring folds in at R3.) |
| **R3** ✅ (payload+logs) | Base anchor + logs — **LANDED** `kotoba-evm::{anchor,logs}` (kotoba#96): `anchor_block_calldata` ABI-encodes `AnchorBridge.commitRoot(bytes32,bytes,uint64)` for a block (read+verify — relayer submits); revm logs → `Receipt` + 2048-bit `logs_bloom` (M3:2048) + `filter_logs` (eth_getLogs-style); `ExecOutcome`/blocks carry logs. **Remaining**: live Base submit + `eth_getLogs` over the chain via the RPC server. |
| R4 (mechanical) | genesis + redeploy GCC + escrows via forge; repoint the Mishmar tick; retire geth-private — **UNBLOCKED**: CREATE + the geth/viem `eth_*` surface land (kotoba#97-99); **`forge create` deploys a real solc contract to the running node end-to-end** (`evm_node` example: Deployed→0x5FbDB2…0aa3, `cast call x()`→42, no geth). Remaining = ops: `forge create` the actual GCC/escrows + genesis-seed + repoint tick + retire geth-private. |
| R5 | gas→mKOTO tariff; member gas-exemption quota; (later) fraud/validity proofs + decentralized sequencing |

## Alternatives considered

- **Keep geth-private** — rejected: external SPOF (502 today), non-content-addressed,
  not anchored, contradicts blockchain-self-contained.
- **Adopt an OP-stack / full rollup framework** — rejected: heavy, Go/TS-centric, not
  Datom-native; would re-introduce a separate state DB instead of the Datom log.
- **Drop EVM, go pure-Datalog contracts** — rejected: throws away Solidity, forge,
  viem, and the already-written + audited escrows; EVM compatibility is the point.

## References

- ADR-2606082100 (Mishmar Storage Covenant — escrows move here)
- ADR-2605262130 (kotoba canonical substrate) / ADR-2605312345 (Datom first-class state)
- ADR-2605172300 (AnchorBridge) / `50-infra/vultr/geth-private/` (superseded host)
- revm (Rust EVM) — proposed execution engine
