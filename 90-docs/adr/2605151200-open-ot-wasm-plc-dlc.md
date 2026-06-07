---
id: adr-2605151200-open-ot-wasm-plc-dlc
title: "ADR-2605151200: Open-OT — WASM-based PLC and Distributed Logic Controller"
status: active
doc_type: adr
topic: open-ot-wasm-plc-dlc
authoritative: true
last_verified: 2026-05-15
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Prototype in progress. Risk-1 cells and host harness exist; industrial deployment remains gated on Risk-1 acceptance."
authoritative_for:
  - etzhayyim-project-open-ot scope and boundary
  - WASM runtime selection for industrial PLC / DLC
  - logic-language tier policy for IEC 61131-3 migration
  - distribution substrate selection (Zenoh / OPC UA FX / XRPC)
  - safety classification (non-SIL only at MVP)
depends_on:
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605082100-langgraph-checkpointer-storage
  - adr-2605082200-langgraph-single-task-and-row-driven-runtime
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
related:
  - 2604251700-wproto-wit-dead-path
  - adr-2604261830-ethereum-anchored-wasm-bpmn-runtime
  - adr-2605142200-giemon-open-hardware-brand
supersedes: []
superseded_by: []
---

# ADR-2605151200: Open-OT — WASM-based PLC and Distributed Logic Controller

**Status**: active (prototype in progress; deployment gated by Risk-1)
**Date**: 2026-05-15
**Deciders**: Jun Kawasaki

## Context

The etzhayyim platform already covers IT-side cognitive actors (LangGraph + Kotoba/Datomic + atproto cohort). It does not yet have an Operational Technology (OT) story — the controllers, sensors, and actuators that physically run factories, grids, water plants, building HVAC, and process plants. The incumbent OT stacks are vertically integrated and proprietary: Yokogawa CENTUM VP, Honeywell Experion PKS, Siemens SIMATIC PCS 7, ABB Ability System 800xA, Emerson DeltaV. Open alternatives exist but are fragmented (OpenPLC, Beremiz, Eclipse 4diac), and none ship a production WASM runtime path.

Three industry shifts make a WASM-native OT stack worth designing now:

1. **WAMR AOT on RTOS** has reached 60–95 % of native C performance with 20–80 µs scan-cycle jitter on Cortex-M7-class hardware (Zephyr + WAMR, Bytecode Alliance / Intel / Renesas reports 2024–2025). Soft-RT (1–10 ms) is solved; hard-RT remains hosted on the RTOS layer.
2. **OPC UA FX + IEEE 802.1Qbv TSN** is the standards-aligned replacement for proprietary fieldbuses (Profinet IRT, EtherCAT, Sercos III). Switch silicon shipped 2023–2024; multi-vendor interop demonstrated SPS 2024.
3. **IEC 61499 distributed function blocks** (Eclipse 4diac / FORTE) provide a formal model for distributing control logic across cohorts of devices — the right abstraction for **DLC (Distributed Logic Controller)** rather than the centralized scan-loop semantics of IEC 61131-3. Crucially, **IEC 61499's event-driven FB network is semantically isomorphic to LangGraph's Pregel super-step model**: typed events ≡ Pregel messages, FB tick ≡ super-step, FB network barrier ≡ super-step barrier. This gives etzhayyim a one-shot architectural alignment that no other OT model offers.

A WASM cell + atproto record model decomposes the legacy DCS into (a) per-control-loop WASM modules running on commodity edge nodes, (b) configuration / lineage / audit as immutable atproto records, (c) a low-latency distribution substrate replacing the proprietary I/O bus, (d) **a LangGraph graph as the orchestrator of multi-cell loops**, with the same checkpointer / single-task / row-driven runtime that already runs etzhayyim's cognitive actors. This fits the existing etzhayyim `bonsai cultivar` and `cohort` model: each control loop is a cell with declared upstream / downstream / neighbor links.

## Decision

Establish `etzhayyim-project-open-ot` as the open-source reference implementation for WASM-native PLC and DLC, scoped to **non-safety-rated industrial control** (process monitoring, energy management, building automation, water/wastewater non-SIL, lab and agricultural automation). Apache-2.0.

### Runtime stack

Three tiers, each with a fixed OS and runtime pick:

| Tier | OS | Runtime | Purpose |
|---|---|---|---|
| Field device | **Zephyr LTS** | **WAMR AOT** | per-cell control loop, FB step() execution |
| Edge controller | **NixOS + linuxPackages_rt** (greenfield) or **Talos Linux + RT kernel patch** (K8s flow) | **CPython 3.11+ / Granian / LangGraph** + **Wasmtime** sidecar | Pregel orchestrator, multi-cell loop coordination, checkpointer |
| Cloud gateway | **VKE (existing)** | **LangServer pod** | XRPC ↔ AgentGateway MCP ↔ atproto records |

Detail:

- **Field device — WAMR AOT on Zephyr LTS**. ~85–150 KB code, AOT artefacts loaded by a small runtime, MISRA-C-aligned, vendor-supported by Intel / Sony / Renesas / Siemens. Scan-cycle target: 1 ms with ≤ 100 µs jitter, achieved by SCHED_FIFO Zephyr thread, pre-faulted linear memory, no GC, no `memory.grow` at runtime. Zenoh-Pico for substrate I/O.
- **Edge controller — NixOS or Talos with PREEMPT_RT**. Hosts the LangGraph Pregel orchestrator (CPython 3.11+ / Granian per ADR-2605080600), the Kotoba/Datomic-backed checkpointer (per ADR-2605082100), Wasmtime for tier-2 cells that fit on the gateway, and the OPC UA FX ↔ Zenoh bridge. Achieves ~30–150 µs cyclictest-class jitter at 1 kHz with isolcpus, irqaffinity, full_nohz, mlockall. **NixOS is preferred for greenfield** (declarative IaC, snapshot/rollback, etzhayyim Nix culture); **Talos is preferred where the edge already runs as a K8s node** (LangServer pod portability). QNX, VxWorks, FreeRTOS hosts are rejected — they cannot run CPython, so LangGraph cannot live there.
- **Hard-RT escape hatch** — for sub-10 µs servo / motion loops, control logic remains in qualified host C / RT-Linux; WASM is **not** placed in the hard-RT path. Xenomai / EVL co-kernel optional for vendors who need it. LangGraph never runs in the hard-RT path.

GC proposal modules and Component-Model dynamic linking are **disallowed in the control-data path** until WCET tooling matures (~2027 estimated). They are allowed in the configuration / engineering / HMI tier.

### Logic language

Dual-track at MVP, both **IEC 61499-compatible**:

- **Tier 1 (greenfield, etzhayyim-native)** — **Rust function-block API, IEC 61499 FBType-compatible**. Typed events, typed data inputs/outputs, ECC (Execution Control Chart) state machine, explicit cohort declaration in a `kotodama.jsonld`-equivalent manifest. Compiled to `wasm32-wasi` linear-memory only, no `gc` feature. Recommended path for new projects. The FB type signature is wire-compatible with 4diac's FBType XML so engineering can move between Rust source and 4diac IDE without re-modeling.
- **Tier 1b (graphical engineering)** — **Eclipse 4diac IDE → FBType XML → Rust FB API codegen**. 4diac IDE used as the graphical surface; etzhayyim-owned codegen emits Rust source against the Tier 1 API. Avoids depending on the immature fortiss FORTE→WASM prototype while preserving IEC 61499 semantics end to end.
- **Tier 2 (migration)** — **matiec fork → ST → WASM**. Allows existing IEC 61131-3 codebases (Structured Text, Ladder Diagram, Function Block Diagram) to migrate. Owned end-to-end by etzhayyim (no upstream open ST→WASM compiler exists as of early 2026 — Bosch and Siemens have published PoCs but no open code). Budget: 12–18 months to a usable port. ST procedures wrapped as a single 61499 BFB at the boundary so the Pregel binding is uniform.

Promotion rationale: IEC 61499's typed event + ECC tick model is **isomorphic to a Pregel super-step**, giving open-ot a single execution model from cell up to multi-loop LangGraph orchestration. Skipping 61499 would force etzhayyim to reinvent the binding, and would lose the formal distribution semantics that the standard already provides.

### Distribution substrate

Three layers, each with the right tool:

| Plane | Substrate | Latency target | Rationale |
|---|---|---|---|
| Data (cohort-internal control / I/O) | **Eclipse Zenoh** (default) — UDP / shared memory | 100 µs–1 ms | Lowest overhead, multi-transport, query model DDS lacks. |
| Industrial interop (cross-vendor) | **OPC UA FX over TSN** bridge | 1–10 ms | Standards-aligned; bridge from Zenoh via a sidecar so wire format is not baked into FB API. |
| Control plane (config / lineage / audit / SSoT) | **etzhayyim XRPC + MCP** → atproto records | seconds (eventual) | Deployment, version pinning, capability grants, audit. **Not** on the data plane — XRPC ms-floor is wrong for control. |

Southbound legacy protocol drivers (S7, EtherNet/IP, Modbus, BACnet, DNP3) via **Apache PLC4X**.

### Safety classification

Non-safety only at MVP. Any Safety Instrumented Function (SIF) requires a separate certified safety PLC (HIMA HIMatrix, Siemens S7-1500F, Rockwell GuardLogix) running in parallel. **IEC 62443 OT cybersecurity** is in scope from day one (signed `.wasm` / `.aot` modules, capability-based imports, no ambient authority, hardened WAMR build). Target posture: SL-2 at MVP, SL-3 with hardware root of trust as a roadmap item. **IEC 61508 / 61511 functional safety certification is explicitly out of scope** until Risk-1 is resolved.

### LangGraph + Pregel binding

Each multi-cell control loop is a LangGraph graph; each WASM cell is a Pregel node. The orchestrator runs on the edge-controller tier (NixOS / Talos), not on the field device.

| LangGraph / Pregel concept | Open-OT mapping |
|---|---|
| Pregel super-step | one IEC 61499 event tick = one cell `step()` for all participating cells |
| Pregel message | typed IEC 61499 event + data, transported via Zenoh (intra-site) or OPC UA FX (cross-vendor) |
| Super-step barrier | TSN `802.1Qbv` gate event when present; software barrier on the Pregel scheduler otherwise |
| LangGraph node | one cell DID (`did:web:open-ot.etzhayyim.com:cell:*`) bound to a pinned `.aot` artefact |
| LangGraph graph | one loop DID (`:loop:*`); graph-as-data per ADR-2605082000 |
| Checkpointer | Kotoba/Datomic checkpointer per ADR-2605082100 — each super-step persists `(loop_did, step_id, cell_state[], in_flight_msgs[])` |
| Single-task / row-driven | per ADR-2605082200 — one signal change → one row in `vertex_open_ot_signal_change` → one task → one super-step on the affected loop |
| Resume from checkpoint | plant restart loads the last persisted super-step; cells resume with the same inputs and ECC state they had pre-failure |
| Operator intervention | `setpointChange` / `modeChange` injected as a typed event into the next super-step; appears in checkpoint history as part of the audit trail |
| Audit trail | super-step checkpoint stream is the audit log — no separate audit pipeline |

Determinism contract: a loop's super-step is **deterministic given (cell_states, inbound messages, params)**. Wall-clock side effects (timers, RNG, external I/O) must enter as explicit inbound messages so that replay from checkpoint reproduces behaviour. This is the same contract LangGraph already requires of cognitive actors; OT inherits it for free.

Cycle-period vs super-step rate: tight inner loops (≥ 100 Hz) run **on the field device only**, with the LangGraph orchestrator observing at a slower rate (1–10 Hz checkpointer cadence). The orchestrator is for multi-loop coordination, mode transitions, fault handling, and operator/agent interaction — **not** for per-cycle PID math. This keeps Pregel's BSP overhead off the critical control path.

### Identity and persistence

Aligns with platform invariants:

- Each device, cell, and signal point gets a path-based DID (`did:web:open-ot.etzhayyim.com:{device|cell|signal|loop}:{id}`).
- Configuration, version pins, capability grants, and audit are atproto records under `com.etzhayyim.apps.openOt.*` NSIDs.
- Telemetry is **not** atproto records — it is Zenoh stream + Kotoba/Datomic continuous ingest (per ADR-2605111200, RW writes happen inside K8s pods via XRPC `recordTelemetryBatch`, not from the edge device directly; a tunnel pod aggregates).
- Control writes (setpoint changes, mode changes) go XRPC → bpmn-dispatcher → AgentGateway MCP → LangServer pod → Zenoh publish → device cell. The control-plane round trip is human / agent latency, not control-loop latency.

## Scope at MVP

Initial NSIDs to be defined in `60-apps/etzhayyim-project-open-ot/SPEC.md`:

- `defineDevice` — physical controller / RTU / gateway
- `defineCell` — control loop or function block instance
- `defineSignal` — analog / digital / string signal point
- `defineLoop` — PID / sequence / interlock loop
- `pinModule` — pin a `.aot` / `.wasm` artefact (CID) to a cell
- `grantCapability` — host capability grant (I/O, network, neighbor cell)
- `setpointChange` — operator / agent setpoint write (audited)
- `recordTelemetryBatch` — pod-side ingest from Zenoh aggregator
- `reportFault` — fault with severity DMN
- `getCell` / `listLoops` / `listFaults` — read methods

## Consequences

### Positive

- First open WASM-native OT reference implementation; aligned to the ecosystem-as-model and bonsai-cultivar metaphors without contorting either.
- Sandboxed control logic gives a real IEC 62443 cybersecurity story that legacy PLCs cannot match without retrofit.
- Cohort distribution semantics map cleanly onto `cell membrane` (MCP) / `cytoplasm` (XRPC) / `mycorrhiza` (Zenoh) layering.
- Reuses etzhayyim persistence, identity, audit, and agent loop without inventing parallel infra.

### Negative

- Toolchain qualification debt — LLVM + WAMR + the Rust FB framework is unqualified for any safety standard. Any move toward industrial buyers (even non-SIL) will surface this.
- No upstream open ST → WASM compiler — etzhayyim owns the matiec port end-to-end if IEC 61131-3 portability is demanded.
- OPC UA FX adoption is real but slow; if it stalls and the market re-entrenches on Profinet / EtherCAT, the Zenoh-first DLC story becomes a niche edge play.
- Hard-RT control still lives outside WASM; the project does not replace dedicated motion controllers.

### Top 3 risks

1. **Toolchain qualification cost.** Decision gate: prototype in Q3 2026 measuring (a) WAMR AOT WCET bound on a representative PID loop, (b) effort to produce IEC 61508 process documentation for the toolchain. Re-evaluate scope if cost > 6 person-months.
2. **ST → WASM ownership.** Mitigation: defer until a paying customer demands it; prefer Rust FB API as the primary surface.
3. **OPC UA FX adoption.** Mitigation: keep the substrate pluggable (PLC4X-style southbound), do not bake Zenoh wire format into the FB API.

## Alternatives considered

- **Container-based OT (ABB Ability Edgenuity, Schneider EcoStruxure direction).** Rejected as primary: containers do not give the WCET, footprint, or sandbox properties needed on Cortex-M-class controllers. Containers remain valid for the edge-gateway tier and may share the host with Wasmtime.
- **wasm3 interpreter as the canonical embedded runtime.** Rejected: 5–15× slower than WAMR AOT, project maintenance has slowed since 2023. Retained as a fallback for <100 KB flash MCUs.
- **IEC 61499 / 4diac FORTE as the primary FB framework, replacing Rust FB API.** Rejected: FORTE → WASM is prototype-stage and unmaintained outside fortiss. Compromise: adopt **IEC 61499 semantics** (FBType, ECC, event+data) via a etzhayyim-owned Rust FB API, with 4diac IDE as the graphical engineering surface. This captures the standard's distribution model without taking on FORTE's runtime debt.
- **Holochain-style per-device source chain for telemetry.** Rejected by ADR-2605092600 outcome; LangGraph + Kotoba/Datomic is the production memory plane.

## Resolved decisions (2026-05-15 follow-up)

### R1 — Hardware reference design: Giemon Mimi / Te / Atama

Adopt the Giemon brand (per ADR-2605142200) with body-part naming consistent with `etzhayyim-project-open-robo` (Giemon Otete). Three reference boards:

| Product | Role | SoC / form | Runtime | Distinguishing I/O |
|---|---|---|---|---|
| **Giemon Mimi (耳)** | sensor RTU | STM32H753 @ 480 MHz, 1 MB SRAM, Cortex-M7 | Zephyr LTS + WAMR AOT + Zenoh-Pico | 16ch 24V DI, 8ch 4–20 mA AI, 2× RS-485 (Modbus RTU), 1× 100BASE-T1 (TSN-capable) |
| **Giemon Te (手)** | actuator RTU | i.MX RT1170 dual-core (Cortex-M7+M4) | Zephyr LTS + WAMR AOT + Zenoh-Pico; M4 reserved for hard-RT motion if needed | 8ch 24V DO (sourcing), 4ch 0–10 V AO, 2× CAN-FD, 1× 100BASE-T1 |
| **Giemon Atama (頭)** | edge controller | Rockchip RK3588 8-core ARMv8.2 (4×A76+4×A55), 16 GB LPDDR5, 128 GB eMMC | NixOS + linuxPackages_rt + CPython/Granian/LangGraph + Wasmtime + RW checkpointer | 4-port TSN switch (802.1Qbv), 1× 2.5 GbE WAN, OPC UA FX bridge, 24 V UPS input |

Brand mapping: Mimi = listen (sensors), Te = act (actuators), Atama = think (Pregel orchestrator + LangGraph). Sourcing follows the open-robo precedent (JP-domestic structure / passives / power, imported SoC soldered on JP-fab). KiCad sources tracked under `60-apps/etzhayyim-project-open-ot/cad-spec/`.

### R2 — Loop-level Svelte editor: deferred to post-Risk-1, spec'd now

Per-cell FB editing is owned by Eclipse 4diac IDE (per logic-language section). Loop-level (multi-cell LangGraph graph) composition + operator HMI lives in a future `60-apps/etzhayyim-project-open-ot/svelte/` SvelteKit app. Initial scope when work begins: (a) read-only loop visualization (cells as nodes, Pregel messages as edges, super-step replay timeline reading `vertex_open_ot_loop_checkpoint`), (b) operator HMI (signal trends, setpoint write via `setpointChange` XRPC, mode change via `modeChange` XRPC). Engineering-write (graph composition, capability grants) deferred to MVP+1. **Implementation start gated on Risk-1 PASS** (see R4).

### R3 — First prototype vertical: Microgrid

Pick **microgrid (community-scale, 100 kW–10 MW class)** as the first prototype. Rationale:

- `etzhayyim-project-open-denki` (CIM-aligned smart-grid stack, MVP 2026-05-07) already provides the entity vocabulary: `defineGenerationNode`, `defineSubstation`, `defineFeeder`, `registerSmartMeter`, `recordRenewableOutput`, `recordDemandResponse`. open-ot consumes this as configuration SSoT and extends with control verbs.
- Multi-loop coordination (PV inverter setpoint, BESS charge/discharge, generator dispatch, islanding decision, frequency / voltage support) showcases the LangGraph + Pregel binding without contrived demos.
- Non-safety (no SIF) but economically meaningful (peak shaving, DR participation, islanding ride-through) — real customer pull without IEC 61508 blocker.
- Building HVAC (BACnet / PLC4X) and water utility remain on the roadmap as MVP+1 / MVP+2.

Prototype scope tracked in SPEC.md §13.

### R4 — Risk-1 gate: quantitative acceptance criteria

Risk-1 (toolchain qualification cost) prototype runs Q3 2026.

**Gate A — WAMR AOT WCET on representative PID loop (Giemon Mimi class)**
- Rig: STM32H753 @ 480 MHz, Zephyr LTS 4.x, WAMR AOT (LLVM 18, `-O3`, no GC), Zenoh-Pico
- Workload: typed BFB with 100 DataIn / 100 DataOut signals, 1 ms cycle, 10 hours continuous
- **PASS**: p99.9 tick latency ≤ 200 µs, zero deadline misses, observed heap delta = 0 bytes after `init`
- **FAIL**: any deadline miss, p99.9 > 500 µs, or any heap growth after `init`

**Gate B — Pregel super-step latency end-to-end**
- Rig: 3× Giemon Atama (NixOS+RT) + 12× Giemon Mimi/Te (Zephyr) on a TSN switch fabric
- Workload: 12-cell loop, 1 Hz super-step, 24 hours; inject 1 controller crash and 3 device crashes
- **PASS**: super-step duration p99 ≤ 50 ms; checkpoint write p99 ≤ 100 ms; zero in-flight message loss across crashes; resume-from-checkpoint within 5 s
- **FAIL**: any message loss, p99 super-step > 200 ms, or resume > 30 s

**Gate C — Toolchain qualification cost estimate**
- Deliverable: written estimate (WAMR AOT compiler / LLVM dependency mapping / Rust FB framework memory-safety claims / Zephyr LTS vendor safety package reuse) for producing **IEC 62443-3-3 SL-2** documentation
- **PASS**: estimated effort ≤ 6 person-months and no LLVM-side blocker identified
- **FAIL**: any structural blocker (e.g., LLVM versioning policy incompatible with cyber-cert requirements) or estimate > 12 person-months

**Decision matrix**

| A | B | C | Outcome |
|---|---|---|---|
| PASS | PASS | PASS | Promote to MVP build, commission Giemon Mimi/Te/Atama Rev-1, start microgrid pilot, begin Svelte editor |
| PASS | PASS | FAIL | Promote runtime, defer industrial-cyber-cert path, ship community-microgrid + research-only positioning |
| PASS | FAIL | * | Re-architect orchestrator (lower super-step rate, alternative checkpointer); rerun Gate B |
| FAIL | * | * | Re-evaluate WAMR AOT vs. Wasmtime-on-RT-Linux on a single Atama (no Mimi/Te separation); rerun Gate A |

## Closing state (2026-05-15 session)

The ADR moved from spec-only to prototype-in-progress:

- `60-apps/etzhayyim-project-open-ot/cells/openot-bfb-rs` defines the shared
  Rust BFB trait surface for IEC 61499-style typed events, typed data, ECC
  state, and bounded `TickResult` event emission.
- `cells/pid-limited` implements the representative PID loop used by Risk-1
  Gate A.
- `cells/droop-p-f` implements a microgrid active-power/frequency droop cell
  for the first prototype vertical.
- `cells/anti-islanding-rocof` implements the first protection/interlock BFB:
  ROCOF + voltage/frequency envelope detection, latched trip, RESET event,
  multi-event output (`CNF` + `TRIP`), and deterministic replay tests.
- `risk1/gate-a-rig` provides the Wasmtime host harness for loading cell WASM,
  exercising the ABI, and recording host-side latency reports. The harness now
  grows linear memory before placing scratch buffers at the 1 MiB offset.

Verification at close:

- `cargo test -p anti-islanding-rocof` passed 14/14 unit tests.
- `cargo check -p anti-islanding-rocof --target wasm32-unknown-unknown
  --no-default-features` passed.

This does not satisfy Risk-1 Gate A yet. Gate A still requires WAMR AOT on the
Giemon Mimi-class target with the 10-hour latency/deadline/heap criteria above.

## Open questions

- Vendor relationships for safety-rated co-controller integration (HIMA / Siemens / Rockwell) — out of scope for spec but needed before any plant deployment.
- Migration story for existing CENTUM / Experion plants — large engineering investment, defer until first design partner.
- TSN switch silicon for Giemon Atama — Marvell 88Q5050 vs Microchip LAN9692 vs NXP SJA1110, decision pending Q3 supply quotes.
- Whether Giemon Te M4 core hosts a **separate** WAMR instance for hard-RT cells (M7 = soft-RT cells, M4 = hard-RT motion) or stays bare-metal C only.

## References

- Bytecode Alliance, *WAMR Performance Benchmarks*, 2024.
- Bosch Research, *WebAssembly for Industrial Edge*, 2023 (PoC; no open code).
- Eclipse 4diac project — IEC 61499 reference implementation, fortiss / Profactor / JKU.
- OPC Foundation, *OPC UA Field eXchange (FX) Specification*, 2022 with 2024 updates.
- IEEE 802.1Qbv (TSN scheduled traffic), 802.1Qci (per-stream filtering and policing).
- IEC 61131-3 (Programmable controllers — programming languages); IEC 61499 (Function blocks for distributed industrial systems).
- IEC 61508 (Functional safety, generic); IEC 61511 (Process industry); IEC 62443 (Industrial automation security).
- ZettaScale, *Eclipse Zenoh* — protocol and Zenoh-Flow.
- Apache PLC4X — driver library for industrial protocols.
