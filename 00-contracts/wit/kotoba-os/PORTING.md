# kotoba-os — reference → production porting handoff

**ADR**: [ADR-2606031600](../../../90-docs/adr/2606031600-kotoba-os-content-addressed-wasm-unikernel.md)
**Audience**: an upstream contributor implementing the **production** `kotoba-os`
in the `40-engine/kotoba` subrepo (per N6 — no fork; upstream PR only).

This monorepo tree (`00-contracts/wit/kotoba-os/`) is a **tested reference**, not the
shipping kernel. It pins the contracts and the behaviour with 70 tests; the production
crate must reproduce that behaviour against the real kotoba crates and a real lower
edge. This doc is the map.

## What is real here vs. what production must build

| Concern | Reference (this tree) | Production target (`40-engine/kotoba`) | Delta to implement |
|---|---|---|---|
| Device + control contract | `kotoba-os.wit` (validated) | shared WIT, e.g. `crates/kotoba-os/wit/` or `kotoba-guest` | none — copy the WIT verbatim; keep the package `kotoba:os@0.1.0` |
| Boot types | `kotoba-os-types` (`GenesisManifest`, `LowerEdge`, `Violation`) | new crate `kotoba-os` | port the types as-is; replace stubs below |
| Content addressing | `cid.rs` from-scratch CIDv1(blake3) + base32 | **`kotoba-core`** (CIDv1 blake3, KAIS frame) | replace `cid::cidv1_raw_blake3` / `verify_blake3` with `kotoba-core`'s CID; the reference base32 was validated against an independent oracle, so outputs must match |
| Canonical state (the Datom log) | `HostState` in-memory `Vec<(T,E,A,V)>` | **`kotoba-kqe`** arrangements + **`kotoba-graph`** Quad/Commit-DAG over content-addressed blocks (`kotoba-store`) | replace the in-memory log with the real Datom log; `commit()` becomes a Datom transaction; `as_of` becomes a kqe arrangement read |
| Agent mesh | `mesh.rs` (source chain / witness-index / membrane, FNV-1a) | **`kotoba-dht`** (SourceChain / Warrant / Neighborhood / Availability Proof) + **`kotoba-net`** (libp2p) | replace the FNV-1a chain + in-proc witness with kotoba-dht; keep the ADR-2605231902 witness-index rule |
| WASM host | `plc-host-runner` (standalone wasmtime + `bindgen!`) | **`kotoba-runtime`** (WasmExecutor + WIT host bindings) | host the device-WIT imports from kotoba-runtime; keep fuel metering (soft-RT N2) |
| Device buses | simulated host impls (return canned values) | real drivers: modbus/opcua/ethercat/canopen libs + GPIO via the unikernel HAL | the **only** place real hardware enters; gated by N3 (no live actuation until R5) |
| L1 lower edges | `HostedEdge` stub only | `UnikernelEdge` (Hermit-derived `no_std` boot) · `HostedEdge` (e7m process) · `BrowserEdge` (`kotoba-store-web`) | the unikernel edge is **net-new** (Hermit vendor + boot); reference has no real boot |
| Genesis manifest | JSON Schema + Rust types + `boot_actor` | same schema (it is the contract); deserialize in `kotoba-os` | keep the schema in `00-contracts/`; production reads it |
| OCI-CID artifact | schema + decode invariant | **`kotoba-store`** IPFS gateway + Murakumo kubelet pod class | implement the `ipfs://<cid>` pull + CID re-verify at the k8s edge |

## Field mapping: `kotoba:os/datom` → `kotoba:kais/kqe`

`kotoba:os/datom.fact` is **structurally isomorphic** to the canonical
`kotoba:kais/kqe.quad` already used by other guests — only the EAVT field names
differ. When porting the Datom surface to `kotoba-kqe`, map field-for-field:

| `kotoba:os/datom.fact` | `kotoba:kais/kqe.quad` |
|---|---|
| `entity`     | `subject`     |
| `attribute`  | `predicate`   |
| `value-cbor` | `object-cbor` |
| `graph`      | `graph`       |

`assert-facts(list<fact>)` is the batched form of `kqe.assert-quad(quad)`. No
incompatible divergence — the production crate should treat `datom.fact` as the
Datomic-named projection of the kqe quad, not a separate type.

## Acceptance spec — the 70 reference tests are the contract

The production crate is correct when it reproduces these behaviours (run
`reference/run-all.sh` for the reference's own pass):

- **scan cycle = Datom transaction** — each committed cycle appends Datoms at `T = cycle`; `as_of(t)` reconstructs state (`test_scan_cycle_model`, `plc-host-runner` e2e).
- **N3 fault-atomicity** — a faulted cycle commits zero Datoms (e2e: faulted sensor read → guest `Err` → log unchanged).
- **N2 soft-RT** — per-scan fuel is measurable; a starved budget traps the guest (e2e fuel demo).
- **capability scoping** — components import only granted interfaces; `boot_actor` refuses an actor whose imports the manifest does not grant (`UnauthorizedImport`).
- **content addressing** — `verify_artifact` recompute rejects tampered bytes (`cid` tests).
- **source chain** — append-only, monotone growth; tamper-detecting `verify` (`mesh` tests + e2e).
- **multi-actor one log** — two components over one Datom log.
- **drift / authorization guards** — WIT == schema == Rust; manifest ⊇ component imports (hikari authorizes modbus, not the discrete-I/O guest).
- **browser edge** — the substrate crate compiles to `wasm32-unknown-unknown` (baien target).

## Invariants the production crate MUST preserve (from the ADR)

- **N1** civilian-only (no weapons / fire-control); **N2** not a certified safety system at R0..R4 (hard-RT/SIL = R5 Lv7+); **N3** no live actuation without operator + Council gate; **N4** Murakumo-only inference (`kotoba-llm` facade, no local inference); **N5** no server-held key (delegated capability via `kotoba-auth`); **N6** no fork; **N7** Datomic unchanged (no bypass-the-log mutable store); **N8** single-address-space single-workload unikernel.
- **C1–C7** (ADR §"Constitutional carve-outs"): Datom canonical, Murakumo-only, no-server-key, on-chain-stays-on-chain, Apache-2.0 + Charter Rider, substrate boundary, `com.etzhayyim.encrypted.*` wire format.

## Sequencing suggestion

1. `kotoba-os` crate with the ported types + `kotoba-core` CID + the genesis schema; reuse `reference/` tests as a conformance suite.
2. `kotoba-runtime`-hosted device-WIT bindings + the 4 example components; reproduce the e2e behaviours.
3. `kotoba-kqe`/`kotoba-graph` Datom-log backing for `commit`/`as_of`.
4. `kotoba-dht`/`kotoba-net` for the real mesh.
5. `HostedEdge` first (e7m), then the Hermit `UnikernelEdge` boot (net-new), then `BrowserEdge`.
6. OCI-CID pull + Murakumo kubelet pod class.
7. Real device drivers — **last**, behind the N3 operator + Council gate.

> Until these land upstream, this tree is the source of truth for the contracts and
> the expected behaviour. Keep the WIT package id (`kotoba:os@0.1.0`) and the genesis /
> OCI schemas stable so the reference and production agree.
