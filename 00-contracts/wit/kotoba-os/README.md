# kotoba:os — kotoba-os device + control WIT surface

**ADR**: [ADR-2606031600](../../../90-docs/adr/2606031600-kotoba-os-content-addressed-wasm-unikernel.md) — kotoba-os content-addressed WASM-first unikernel OS
**Status**: R0 DRAFT (charter-level contract; no boot, no live device I/O)
**Validated**: `wasm-tools component wit kotoba-os.wit` → EXIT 0 (wasm-tools 1.225.0)

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
  liveActuation, N1 civilianOnly), capability scoping (`grants()`), and the
  **`LowerEdge` trait** abstracting L1 with an edge-independent `boot()` (validate
  → CID-verify kernel + each actor + its membrane rule). `HostedEdge` reference impl.
- **6 `cargo test` green**: valid manifest deserializes + validates, deny-unknown-fields
  matches the schema, validate() catches all three constitutional violations,
  capability scoping, HostedEdge boots a valid manifest (3 artifacts verified),
  boot refuses a server-key manifest.

## Next maturity steps (tracked toward R1)

- ✅ Host stub over a simulated bus + Datom surface, with replay-from-Datom test
  (`reference/`, 6 tests green).
- ✅ Genesis-manifest boot contract authored + tested (3 tests green).
- ✅ `kotoba-os-types` crate scaffold (genesis-manifest type + `LowerEdge` trait,
  6 cargo tests green).
- A reference `plc-control` guest (Rust → wasm32, componentize) that runs the
  same soft-RT loop as a real WASM Component Model component.
- A `mesh-agent` / source-chain reference (witness-quorum determinism, membrane
  validation) for ADR §D5.
