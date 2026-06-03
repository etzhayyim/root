# kotoba:os — kotoba-os device + control WIT surface

**ADR**: [ADR-2606031600](../../../90-docs/adr/2606031600-kotoba-os-content-addressed-wasm-unikernel.md) — kotoba-os content-addressed WASM-first unikernel OS
**Status**: **R1/R2 tested reference landed** (R0 charter ratification still pending Council Lv6+ >=3). Real: 2 validated WASM components (`plc-control` + `mesh-agent`), a wasmtime end-to-end run (scan-cycle Datom history + N3 fault-atomicity + fuel-bounded soft-RT + multi-actor one-log), real CIDv1(blake3) verification, genesis + OCI-CID schemas, cross-artifact drift/authorization guards -- **63 tests** via `run-all.sh`.  
**Honest boundaries** (still TRUE): NO actual unikernel boot on hardware, NO live device I/O (host-process / simulation only); the **production crate** (real wasmtime host + kotoba-core) lands in the `40-engine/kotoba` subrepo via upstream coordination -- this tree is the contracts + tested reference, not the shipping kernel.
**Validated**: `wasm-tools component wit kotoba-os.wit` → EXIT 0 (wasm-tools 1.225.0)

## Porting to production

`PORTING.md` is the reference→production handoff: it maps every artifact here to its
target kotoba crate in the `40-engine/kotoba` subrepo, lists the stub→real deltas, and
names the reference tests as the acceptance spec. `reference/test_porting_doc.py` keeps
it honest (every named reference artifact must exist; real port-target crates).

## Verify everything

```bash
bash reference/run-all.sh   # WIT + Rust suite + wasm32 browser-edge build + Python suite
```

One command runs every check; stages whose tooling is absent are SKIPPED (not
failed). Current: **WIT validates · 19 Rust tests · 35 Python tests** (the Python
suite itself builds the real WASM component and runs the wasmtime e2e when the
toolchain is present) = **54 tests + 1 validated component + 1 e2e run**.

### Coverage matrix (ADR pillar → artifact → tests)

| ADR | Pillar | Artifact | Tests |
|---|---|---|---|
| D1 | boot manifest | `schemas/…-genesis-manifest.json` + Rust `GenesisManifest`/`validate()` | 3 py + (in 19 rust) |
| D2 | userland | **4 real WASM components** plc-control + mesh-agent + modbus-control + device-coverage (all 8 device interfaces bind) | 3+3+3+2 py |
| D3 | scan-cycle = Datom txn | `scan_cycle_model.py` + **wasmtime e2e** (control+fuel+N3+**multi-actor**) | 6 + 5 py |
| D4 | k8s OCI-CID | `schemas/…-oci-artifact.json` (digest=CID decode invariant) | 8 py |
| D5 | agent-centric mesh | `kotoba-os-types::mesh` (source chain + witness quorum + membrane) | 7 rust |
| D6 | sizing budget | `sizing-budget.json` (estimates, honestly labeled) | 7 py |
| —  | content addressing | `kotoba-os-types::cid` (real CIDv1 blake3 verify) | 6 rust |
| —  | drift guard | `test_artifact_consistency.py` (WIT==schema==Rust) | 5 py |
| —  | browser edge (L1c) | `kotoba-os-types` compiles to wasm32 (baien target) | run-all gate |
| L1/L2 | unikernel boot + MMIO + scan model + **WASM in-kernel** | `boot-poc/` boots no_std aarch64 on QEMU virt (real PL011 UART), runs the scan/N3 model AND a **real core-wasm module under wasmi in-unikernel** (host calls → Datoms, **+ reads command strings from the guest's linear memory**) | 1 py |

## What this is

The OT/PLC device + control interfaces named in ADR-2606031600 §D3, expressed as
WIT Component-Model contracts. The L2 kotoba-os kernel device shim **implements**
these (host side); an L5 control program **imports** a capability-scoped subset
(guest side). The defining property: **a scan cycle is a Datom transaction** —
every cycle's input snapshot + staged outputs become immutable Datoms with
`T = cycle index`, yielding a replayable, on-chain-anchored control history
(Datomic preserved, ADR-2605312345).

## Package mapping

The ADR refers to `kotoba:io/*` and `kotoba:fieldbus/*` world families. WIT
resolves one package per directory, so they are realized as interfaces inside
the single `kotoba:os@0.1.0` package:

| ADR name              | WIT interface        |
|-----------------------|----------------------|
| `kotoba:io/digital`   | `io-digital`         |
| `kotoba:io/analog`    | `io-analog`          |
| `kotoba:io/gpio`      | `io-gpio`            |
| `kotoba:fieldbus/modbus`   | `fieldbus-modbus`   |
| `kotoba:fieldbus/opcua`    | `fieldbus-opcua`    |
| `kotoba:fieldbus/ethercat` | `fieldbus-ethercat` |
| `kotoba:fieldbus/canopen`  | `fieldbus-canopen`  |
| (Datom state surface) | `datom`             |

Worlds: `plc-control` (control program, exports `scan(cycle) -> scan-report`) and
`mesh-agent` (non-control Holochain-style agent, exports `step`).

## Invariants encoded in the contract

- **N1 no weapons/fire-control** — civilian producing actors only (tatekata /
  giemon / hikari / mizuho / mitsuho / factory lines); the contract is a control
  + audit substrate, never a kinetic/military loop (Charter §2(a), force-separation).
- **N2 soft-RT only** — `scan-report.duration-us` exists for jitter
  characterization; NO IEC 61508 SIL / IEC 61131-3 conformance / hard-RT claim at
  R0. Output ops are **staged** (deferred to an atomic per-cycle commit), never
  applied mid-cycle.
- **N3 no live actuation** — all `write-*` ops are stage-only at R0; live hardware
  actuation is R5 (Council Lv7+ + operator gate).
- **N7 Datomic unchanged** — the only durable state path is `datom.assert-facts`;
  no bypass-the-log mutable store.
- **Capability-scoped** — a guest reaches only the channels/nodes its genesis
  manifest granted; no ambient authority.

## Cross-artifact drift guard

The `kotoba:os` contract is expressed three times — the WIT package, the genesis
JSON Schema (`witInterface`/`world` enums), and the Rust `kotoba-os-types` enums.
`reference/test_artifact_consistency.py` (**5 tests**) parses all three and asserts
they list the same 8 interfaces + 2 worlds, so a future edit can't silently desync
them (e.g. add a WIT interface but forget the schema's capability enum). A baseline
test also pins the known R0 set against a wholesale rename in all three at once.

## Genesis manifest — the boot contract (ADR §D1)

The "DNA" a node boots from ("boot a CID, reconstruct its Datom state, join the
neighbourhood"):

- `../../schemas/kotoba-os-genesis-manifest.schema.json` — JSON Schema (draft
  2020-12) naming the kernel image CID, the userland WASM actor(s) + their
  content-addressed validation-rule CIDs (the membrane), the capability-scoped
  WIT imports, the **delegated** identity (`serverKey: const false` — C3/N5), the
  mesh neighbourhood + witness quorum, and the safety posture
  (`realtimeClass`, `liveActuation: const false` N3, `civilianOnly: const true` N1).
- `reference/examples/genesis-hikari-pv-controller.json` — valid example
  (a hikari grid-edge PV controller on the unikernel edge).
- `reference/examples/genesis-INVALID-server-key.json` — negative fixture that
  the schema MUST reject (holds a platform key + live actuation).
- `reference/test_genesis_manifest_schema.py` — **3 tests** (valid passes;
  invalid rejected at `identity/serverKey` + `safety/liveActuation`; unknown WIT
  interface rejected by capability scoping). Skips cleanly without `jsonschema`.
- `reference/test_manifest_authorizes_component.py` — **3 tests** wiring D1↔D2: a
  manifest must grant every interface its actor's real component imports.
  `genesis-plc-bangbang.json` authorizes the built plc-control component; the
  modbus `hikari` manifest correctly FAILS to grant `io-digital` (the check has teeth).

## k8s OCI-CID artifact convention (ADR §D4)

`../../schemas/kotoba-os-oci-artifact.schema.json` + example + 8 tests make the
"OCI image reference = CID, pulled from IPFS" convention a **checkable invariant**:
the OCI manifest sha2-256 `digest` and the `cid` are the same hash re-encoded
(`cid = base32(0x01 0x55 0x12 0x20 || digest)`). The test **decodes the cid back to
a digest** (stdlib b32decode) and asserts equality — "digest = CID" is verified,
not asserted. The schema forbids commercial registries by construction (`imageRef`
must be `ipfs://bafkre…`; a `ghcr.io` ref is rejected — negative test), `pull.type`
is `ipfs` only, and placement is the Murakumo kubelet (`donated`/`operator` node
class). Keeps the k8s edge inside the IPFS / donation-funded substrate.

## Unikernel-edge sizing budget (ADR §D6)

`sizing-budget.json` replaces the ADR's "sizing budget is honestly TBD" gap with a
**falsifiable, consistency-checked** budget. Every number is an explicit
ENGINEERING ESTIMATE (range, MiB) — NOT a measured footprint; real numbers are an
R2 deliverable (build the Hermit + WASM-runtime + minimal-substrate image and
measure). Three device tiers (T0 MCU honestly excluded · T1 constrained SoC =
minimal target · T2 edge gateway), per-component RAM/flash estimate ranges with
reference-class sources, and a minimal-resident profile whose **low-end sums to
~14 MiB RAM**, fitting the 64 MiB T1 floor.

- `reference/test_sizing_budget.py` — **7 tests**: valid low≤high ranges with
  sources, tiers ascending + T0-not-a-target, minimal profile uses wasmi (not the
  JIT), low-end RAM/flash fit the T1 floor, high-end spread is real (honesty), and
  the estimate disclaimer is present. The tests check *consistency*, not the truth
  of the estimates — R2 measurement re-runs them against corrected numbers.

## Executable reference semantics (`reference/`)

The WIT contract's central claim — **scan cycle = Datom transaction, replayable** —
is pinned by a stdlib-only reference model so it can't silently regress before the
real Rust host exists:

- `reference/scan_cycle_model.py` — `ScanHost` (L2) + scan-cycle driver
  (read → compute → stage → atomic commit) over an immutable `Datom` log, with
  `as_of(t)` / `replay_outputs(t)`.
- `reference/test_scan_cycle_model.py` — **6 tests, all green**
  (`python3 -m unittest`): staged-not-applied-mid-cycle (N3), faulted-cycle-commits-
  nothing (N3 atomicity), one-transaction-per-cycle-with-T=cycle (D3),
  as-of-reconstruction (Datomic), bus-state-is-a-pure-projection-of-the-log (N7),
  append-only-immutable-log (N7).

## Reference Rust crate (`reference/kotoba-os-types/`)

The R1 crate scaffold, monorepo-side (standalone — own `[workspace]`; the
production crate lands in the kotoba subrepo via upstream coordination, N6):

- `kotoba-os-types` — the genesis manifest as typed Rust (serde,
  `deny_unknown_fields` mirroring the schema's `additionalProperties:false`),
  `GenesisManifest::validate()` enforcing the carve-outs (C3/N5 serverKey, N3
  liveActuation, N1 civilianOnly), capability scoping (`grants()` + `authorizes()`/`ungranted()` = a manifest must grant every interface its actor imports), and the
  **`LowerEdge` trait** abstracting L1 with an edge-independent `boot()` (validate
  → CID-verify kernel + each actor + its membrane rule). `HostedEdge` reference impl.
- **`mesh` module** (ADR §D5 agent-centric mesh): `SourceChain` (append-only,
  hash-linked = the local Datom-log segment, with tamper-detecting `verify()`),
  deterministic `witness_index`/`select_witnesses` (the ADR-2605231902
  `hash(record_cid) + i mod n` rule), and a `Membrane` trait + `CapabilityMembrane`
  + `quorum_accepts()`.
- **`cid` module** (ADR §D1, R2): real CIDv1 content addressing matching
  kotoba-core's "CIDv1 blake3" — `cidv1_raw_blake3()`, `verify_blake3()`, and an
  OCI-bridge `cidv1_raw_sha256()`. From-scratch base32 encoder validated against an
  independent oracle (the sha256 CID python produced for §D4). `LowerEdge` gains
  `verify_artifact(bytes, cid)` = **real recompute** (rejects tampered bytes), not
  the R0 structural shape check.
- **19 `cargo test` green**: 6 manifest/edge (valid deserialize+validate,
  deny-unknown-fields matches schema, validate() catches all three violations,
  capability scoping, HostedEdge boots 3 artifacts, boot refuses server-key) + 7
  mesh (chain links+verifies, verify detects tampering, witness selection
  deterministic + reproducible + spreads + capped, membrane rejects ungranted
  interface, quorum accepts only with enough valid witnesses).

## Real WASM Component guest (`reference/plc-control-guest/`)

The first **real** L5 userland artifact (ADR §D2/§D3): a bang-bang controller
compiled to an actual WASM Component-Model component implementing the `kotoba:os`
`plc-control` world. Built with `wit-bindgen` + plain cargo (wasm32) +
`wasm-tools component new` — NOT cargo-component (blocked here by a malformed
global `~/.config/wasm-pkg/config.toml`). `build.sh` does the toolchain-pinned
build, validates the component, prints its world + digest.

- The produced component (22.8 KB) **validates** (`wasm-tools validate
  --features component-model`) and exports `scan(cycle) -> scan-report`.
- Its imports are **capability-minimized**: wit-bindgen tree-shakes the world down
  to exactly the interfaces the controller calls — `io-analog` (read), `io-digital`
  (write/stage), `datom` (assert) — `fieldbus-*` and `io-gpio` do NOT appear.
- `reference/test_plc_component.py` — **3 tests** (component produced + valid,
  exports scan/scan-report, imports capability-minimized). Skips cleanly when the
  wasm32 toolchain / wasm-tools are unavailable. The binary is reproducible from
  source (gitignored; `Cargo.lock` committed).

**Second L5 world** (`mesh-agent-guest/`): the same artifact kind built for the
non-control `mesh-agent` world (exports `step`). Proves an agent has **zero device
authority** — its component imports only `kotoba:os/datom` (no `io-*`/`fieldbus-*`);
3 toolchain-guarded tests. **Modbus controller** (`modbus-control-guest/`): the first component to exercise a
`fieldbus-*` interface — tree-shakes to {io-analog, fieldbus-modbus, datom}, which is
exactly what the hikari grid-edge manifest grants, so hikari authorizes a real built
component (3 tests). **Device-surface coverage** (`device-coverage-guest/`): a single component touching
every kotoba:os device interface — its tree-shaken imports are all 8 (io-{digital,analog,
gpio} + fieldbus-{modbus,opcua,ethercat,canopen} + datom), proving the whole WIT device
surface binds to real WASM imports (2 tests; a completeness smoke test, not a controller).

## End-to-end host run (`reference/plc-host-runner/`)

The capstone (ADR §D2/§D3): a native **wasmtime** host that instantiates the real
`plc-control` component, provides the host imports (io-analog read / io-digital
write / datom assert) over an immutable Datom log, and drives a sequence of scan
cycles — proving the design's two central claims through **actual WASM execution**:

```
CYCLE 0 pv=3  cmd=ON  out10=Some(true)
CYCLE 1 pv=20 cmd=OFF out10=Some(false)
CYCLE 2 pv=8  cmd=ON  out10=Some(true)
CYCLE 3 FAULTED -> Err(sensor fault), no commit    # N3 atomicity through real WASM
DATOMS=6
E2E OK
```

- `src/main.rs` uses `wasmtime::component::bindgen!` against a trimmed host world
  (`wit/host.wit`, only the 3 interfaces the component imports). It self-asserts:
  scan cycle = Datom transaction (T = cycle, `as-of` reconstructs the command), and
  N3 fault-atomicity (a faulted sensor read → guest returns `Err` → zero datoms
  committed; the log stays at 6).
- `reference/test_plc_host_e2e.py` — **3 tests** (e2e OK, control history through
  real WASM, N3 fault-atomicity through real WASM). Toolchain-guarded. `Cargo.lock`
  gitignored (1744-line wasmtime tree; the runner is a harness, not an artifact).
- **Fuel metering** (N2 soft-RT): the runner enables wasmtime `consume_fuel`,
  reports per-scan fuel (~1.4-1.8k units = a WCET-estimation input), and a
- **Multi-actor, one log** (ADR §D2 core claim): the runner instantiates BOTH the
  plc-control and mesh-agent components into ONE store (one HostState = one Datom
  log) and interleaves control scans + agent steps — the combined log holds 2
  control commands + 2 heartbeats. 5 e2e tests.

## Next maturity steps (tracked toward R1)

- ✅ Host stub over a simulated bus + Datom surface, with replay-from-Datom test
  (`reference/`, 6 tests green).
- ✅ Genesis-manifest boot contract authored + tested (3 tests green).
- ✅ `kotoba-os-types` crate scaffold (genesis-manifest type + `LowerEdge` trait,
  6 cargo tests green).
- ✅ `mesh` module — source chain + witness-quorum determinism + membrane (ADR §D5,
  7 cargo tests green).
- ✅ Real `plc-control` WASM Component guest (`plc-control-guest/`, wit-bindgen →
  wasm32 → component; validates; capability-minimized imports; 3 tests green).
- ✅ Honest unikernel-edge flash/RAM sizing budget (ADR §D6, 7 tests green).
- ✅ End-to-end wasmtime host run of the real component (`plc-host-runner/`):
  scan-cycle Datom history + N3 fault-atomicity through actual WASM (3 tests green).
- ✅ D4 k8s OCI-CID artifact convention (digest = CID, IPFS-pulled; 8 tests, incl.
  the decode-cid-equals-digest invariant + registry-ref rejection).
- ✅ Cross-artifact drift guard — WIT == schema == Rust types (5 tests).
- ✅ R2 real blake3 CID verification in `LowerEdge::verify_artifact` (`cid` module,
  6 tests; from-scratch base32 validated vs an independent oracle).
- ✅ Consolidated coverage runner (`reference/run-all.sh`) + coverage matrix.
- The real production crate in the kotoba subrepo (upstream coordination) +
  wasmtime fuel metering / WCET for the soft-RT story (§D3, R3).
