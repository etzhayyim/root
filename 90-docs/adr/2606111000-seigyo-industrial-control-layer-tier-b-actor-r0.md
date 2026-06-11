---
id: adr-2606111000-seigyo-industrial-control-layer-tier-b-actor-r0
title: "ADR-2606111000: seigyo (制御) — open industrial control layer (PLC / SCADA / DCS-equivalent, ISA-95 L0–L2) Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: seigyo-industrial-control-layer-r0
authoritative: true
last_verified: 2026-06-11
priority: 6.8
axis: industrial-substrate
weight: 0.6
priority_note: "Closes the control-layer gap UNDER the existing manufacturing cell catalog. Every industrial Tier-B actor (igata megacasting, tsukuru silicon fab, yakushi pharma, futawa motorcycle, suki tractor, tsutae device, hikari/denki grid ops, mizuho water ops, district heat networks) is modelled at ISA-95 L3+ (recipe / orchestration / QC / attestation) — the L0–L2 control layer (sensors/actuators, PLC logic, SCADA supervision) that those recipes ultimately execute on is unmodelled, and its constitutional constraints are scattered across ADR-2605265000 §1.9 (no commercial DCS/SCADA vendor; open-source SCADA acceptable), ADR-2604252100 (OPC UA / AutomationML for industrial integration), and ADR-2605215000 (Murakumo-only inference). seigyo promotes the control layer to a first-class substrate actor: OpenPLC (IEC 61131-3) as the canonical L1 runtime, open-source SCADA (FUXA / Rapid SCADA / OpenSCADA) at L2, OPC UA (open62541) northbound, content-addressed PLC-program lifecycle with Council attestation, aggregate-only telemetry past the site boundary (N7 inheritance), and an ABSOLUTE safety invariant: safety interlocks are hardwired / safety-relay only — no LLM, no Murakumo inference, no kotoba cell in the safety path, ever. Etymology: 制御 = control; the hand on the valve beneath every recipe."
authoritative_for:
  - seigyo actor R0 charter
  - "industrial control layer (ISA-95 L0–L2) single SoT: PLC runtime, SCADA, fieldbus, historian"
  - "`com.etzhayyim.seigyo.*` Lexicon namespace boundary"
  - commercial DCS/PLC/SCADA vendor prohibition (generalizes ADR-2605265000 §1.9 from district-heat to ALL actors)
  - safety-path invariant (hardwired interlocks; software/inference advisory-only above L2)
  - PLC-program-as-attested-record lifecycle (IEC 61131-3 ST canonical, CID-addressed, runtime hash attestation)
  - aggregate-only northbound telemetry invariant (N7 inheritance; full-rate data never leaves site historian)
  - bounded-setpoint-envelope invariant for Murakumo optimization proposals
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605265000-district-heating-cooling-d-gate-evaluation-r0
  - adr-2604252100-robotics-product-manufacturing-package
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605261200-igata-megacasting-tier-b-actor-r0
  - adr-2605261215-igata-r1-benchtop-commissioning
  - adr-2605250545-yakushi-pharma-supply-chain-and-robotics
related:
  - adr-2605261500-suki-farm-tractor-tier-b-actor-r0
  - adr-2605261330-futawa-motorcycle-tier-b-actor-r0
  - adr-2605263100-mizuho-water-sanitation-tier-b-actor-r0
  - adr-2605261100-hikari-energy-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2606111000: seigyo (制御) — open industrial control layer (PLC / SCADA / DCS-equivalent, ISA-95 L0–L2) Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council ratification

# Context

The manufacturing cell catalog in `kotoba-kotodama/cells/` models every
industrial actor at the **orchestration layer** (ISA-95 Level 3 and
above): `silicon_etch` dispatches a recipe (gas mix + RF power +
endpoint-detector setpoint), `pharma_purification` encodes a
purification scheme with ICH M7 limits, `igata_shot_injection` /
`igata_solidification_eject` encode casting recipes,
`power_denki_grid_ops` dispatches load-shed priorities,
`water_purification_ops` dispatches treatment trains. Each of these
recipes ultimately executes on a **control layer** — sensors and
actuators (L0), programmable logic (L1), and supervisory control (L2)
— that no ADR or cell currently models.

The constitutional constraints that DO exist for that layer are
scattered:

- **ADR-2605265000 §1.9** (district heating): "Murakumo-only inference
  for network optimization; NO commercial DCS / SCADA vendor (Siemens /
  Honeywell / Yokogawa / Emerson proprietary) — open-source replacements
  (OpenSCADA / FUXA / Rapid SCADA) acceptable if Charter Rider §2 audit
  passes." Stated for ONE network type; clearly intended generally.
- **ADR-2604252100** (robotics manufacturing package): OPC UA
  information model + AutomationML / CAEX as the industrial-integration
  exchange standard. Stated as a file-format table row; no runtime
  architecture.
- **ADR-2605215000**: all inference Murakumo-fleet-only.

Without a first-class control-layer charter, each manufacturing actor
will improvise its own L0–L2 stack at commissioning time (igata R1
benchtop commissioning is the nearest forcing event), reproducing the
exact scattered-policy problem this repo's ADR discipline exists to
prevent — and, worse, improvising **safety-path** decisions per site.

`seigyo` (制御 — control) is therefore chartered as the Tier-B actor
that owns the control layer for ALL religious-corp industrial actors.

# Decision

## §1 Layer model (ISA-95 / Purdue mapping)

| Level | Scope | Canonical stack | Owner |
|---|---|---|---|
| **L0** | Sensors + actuators | Open-hardware transducers where available; commodity industrial I/O otherwise; all I/O points registered per `seigyo.ioPointRegistry` | seigyo |
| **L1** | Logic control (PLC) | **OpenPLC runtime** (IEC 61131-3) on commodity attested hardware; Structured Text (ST) canonical source dialect | seigyo |
| **L1S** | **Safety interlocks** | Hardwired relay / dedicated safety-relay logic ONLY — see §3 | seigyo (attestation only — see §3) |
| **L2** | Supervisory (SCADA/HMI) | **FUXA** or **Rapid SCADA** or **OpenSCADA** (per-site choice; Charter Rider §2 audit each) | seigyo |
| **L2.5** | Northbound gateway | **OPC UA** server (open62541); Modbus TCP/RTU southbound for legacy I/O; MQTT Sparkplug B optional intra-site | seigyo |
| **L3** | Orchestration (MES-equivalent) | Existing kotoba-kotodama manufacturing cells (igata_*, silicon_*, pharma_*, moto_*, suki_*, pillow_*, tsutae_*, power_denki_*, water_*) | per-domain actors |
| **L4** | Governance | ADRs + Council attestation + Charter Rider | Council |

There is deliberately **no monolithic DCS product** in this model: the
DCS-equivalent IS the composition L1 + L2 + L2.5 under one attestation
regime. This is the same architectural judgment commercial DCS vendors
sell as an integrated product, rebuilt from open components so Charter
Rider §2 audit is possible at every layer.

## §2 Commercial vendor prohibition (generalizes ADR-2605265000 §1.9)

Proprietary DCS / PLC / SCADA runtimes are **PROHIBITED** across all
religious-corp industrial actors: Siemens (SIMATIC PCS 7 / S7 / TIA
Portal runtime), Honeywell (Experion), Yokogawa (CENTUM), Emerson
(DeltaV / Ovation), Rockwell (PlantPAx / Logix), ABB (800xA),
Schneider (EcoStruxure Foxboro / Modicon Unity runtime), Mitsubishi
(MELSEC / iQ), GE (iFIX / Cimplicity), AVEVA (Wonderware / System
Platform), Inductive Automation (Ignition — source-available but
commercially licensed: prohibited).

Open-source replacements are acceptable subject to Charter Rider §2
audit: OpenPLC (L1), FUXA / Rapid SCADA / OpenSCADA (L2), open62541 /
Eclipse Milo (OPC UA), pymodbus / libmodbus (Modbus). Protocol
**interoperability** with third-party equipment that embeds a
proprietary PLC (e.g., a purchased machine tool with a built-in
controller) is permitted at the boundary via OPC UA / Modbus, but that
embedded controller is then an L0-equivalent black box: no
religious-corp recipe logic may be programmed INTO it, and its points
are registered as untrusted-external in `seigyo.ioPointRegistry`.

## §3 Safety-path invariant — ABSOLUTE

1. Safety interlocks (emergency stop, over-pressure, over-temperature,
   gas detection, light curtains, lockout-tagout) are **hardwired or
   dedicated safety-relay logic at L1S**. IEC 61508 / IEC 61511 design
   discipline is followed as engineering reference (no certification
   claim at R0/R1 scale).
2. **No LLM, no Murakumo inference, no kotoba cell, no network round
   trip is EVER in the safety path.** A safety function MUST complete
   with the site network cable cut.
3. Software above L1S is **advisory-only with respect to safety**: a
   kotoba cell or Murakumo optimization may REQUEST a setpoint change;
   it may never bypass, mask, or reset an interlock. Interlock reset is
   physical, on-site, human.
4. Murakumo optimization proposals apply only through a
   **bounded-setpoint envelope** compiled into the attested PLC program
   itself (min/max per setpoint, max rate-of-change). A proposal
   outside the envelope is clamped and logged at L1, regardless of what
   any upstream layer requested. Widening an envelope = new PLC program
   version = new attestation per §4.
5. `seigyo_interlock_attestation` (cell) records that a qualified
   engineer physically verified each interlock at commissioning and at
   each annual re-verification. The cell ATTESTS the safety layer; it
   is not IN it.

## §4 PLC-program-as-attested-record lifecycle

IEC 61131-3 Structured Text is the canonical source form (graphical LD
/ FBD may be authored but the committed artifact is ST). Lifecycle:

```
author (ST) → static checks + OpenPLC simulation → engineer review
  → Council/engineer attestation (program CID + setpoint-envelope table)
  → deploy to OpenPLC runtime
  → runtime hash attestation: hash(loaded program) == attested CID,
    re-verified on every controller restart and daily heartbeat
```

Programs, envelope tables, and I/O point maps are stored as kotoba
records (content-addressed, MST-anchored). A controller running a
program whose hash does not match its attested CID raises
`seigyo.runtimeAttestation` mismatch → L3 cells refuse to dispatch
recipes to that controller until resolved.

## §5 Telemetry + historian (N7 inheritance)

- Full-rate process data (ms–s sampling) stays in the **on-site
  historian** (TimescaleDB or InfluxDB OSS; site-local, religious-corp
  hardware).
- Northbound past the site boundary: **aggregate-only, ≥1-minute
  buckets for process variables, ≥1-hour buckets for anything
  attributable to an individual person's activity** (per hikari N7
  inheritance, same rule as ADR-2605265000 §1.3).
- Alarm/event records (not waveforms) flow north in full per
  `seigyo.alarmEventRecord` — alarms are operational facts, not
  personal telemetry.
- No camera/audio streams transit seigyo; vision QC stays in the
  per-domain robotics cells under their own charters.

## §6 New kotoba-kotodama cells (scaffold-only at R0)

| Cell | Role | ISA-95 seam | Murakumo node (proposed) | §2(a)(c) risk |
|---|---|---|---|---|
| `seigyo_plc_program_lifecycle` | §4 lifecycle: validate → simulate → attest → deploy → runtime-hash watch | L4 → L1 | judah | HIGH |
| `seigyo_interlock_attestation` | §3.5 commissioning + annual interlock verification records | L4 → L1S (attest only) | benjamin | HIGH |
| `seigyo_scada_gateway` | L2 config-as-record (FUXA/Rapid SCADA project files CID-attested) + alarm ingestion → `alarmEventRecord` | L2 ↔ L3 | judah | MEDIUM |
| `seigyo_opcua_bridge` | OPC UA information-model ↔ kotoba graph mapping; recipe dispatch L3→L2.5; point registry sync | L2.5 ↔ L3 | judah | MEDIUM |
| `seigyo_historian_aggregate` | §5 aggregation: site historian → bucketed northbound records | L2 → L3 | simeon | LOW |

All five ship as Council-attestation-gated scaffolds (`cell.py` raises
`RuntimeError` at import) per the L5-wave convention.

## §7 New Lexicons (R1+)

```
com.etzhayyim.seigyo.{
  ioPointRegistry,            # per-site I/O point map (tag, unit, range, trust class incl. untrusted-external)
  plcProgramAttestation,      # program CID + ST source CID + setpoint-envelope table + engineer/Council sigs
  setpointEnvelope,           # per-setpoint min/max + max rate-of-change (compiled into program; mirrored as record)
  runtimeAttestation,         # controller heartbeat: loaded-program hash vs attested CID; mismatch = dispatch freeze
  interlockVerificationRecord,# §3.5 physical verification (commissioning + annual), engineer DID + photo/measurement CIDs
  scadaProjectAttestation,    # L2 project-file CID (FUXA/Rapid SCADA config) + audit result
  alarmEventRecord,           # full-fidelity alarm/event northbound
  telemetryAggregateRecord,   # §5 bucketed process aggregates
  silenSeigyoReview           # annual Council review: envelope-clamp log + interlock records + vendor-prohibition audit
}
```

## §8 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; 5 scaffold cells import-time RuntimeError; no hardware | None |
| **R1** | post-Council + pairing with **igata R1 benchtop commissioning** (ADR-2605261215): ONE benchtop loop (e.g., furnace temperature PID) on OpenPLC + FUXA + open62541; full §4 lifecycle exercised end-to-end; §3 interlock = physical E-stop verified + recorded | 1 site, 1 controller, ≤10 I/O points |
| **R2** | post-R1 + 90-day clean runtime-attestation history: one full production cell (igata die-prep OR pillow foam line) under seigyo control; historian + N7 aggregation live | 1 site, ≤5 controllers |
| **R3** | post-R2 + annual `silenSeigyoReview` pass + ≥1 controls-engineer on Council attestation path: multi-site rollout to silicon / pharma / vehicle actors per their own R-gates | per-actor caps govern |

# Consequences

**Positive**:
- Every manufacturing actor's commissioning inherits one audited
  control stack instead of improvising; ADR-2605265000 §1.9 stops being
  a one-off footnote and becomes substrate law.
- Recipe→execution chain becomes attestable end-to-end: L3 recipe CID →
  L2.5 dispatch → L1 program CID → runtime hash.
- Safety architecture is decided once, constitutionally, before the
  first machine moves — not per-site under schedule pressure.

**Negative**:
- Open-source SCADA/PLC maturity gap vs commercial DCS is real
  (acknowledged in ADR-2605265000 consequences); seigyo absorbs that
  gap as integration + audit labor.
- OpenPLC is soft-real-time on commodity hardware; loops needing
  <1 ms determinism need dedicated motion controllers at the L0
  boundary (treated as embedded black boxes per §2).
- IEC 61508/61511 discipline without certification is an honest but
  limited claim; scale past R3 will force a formal functional-safety
  conversation.

# References

- ADR-2605265000 §1.9 — vendor prohibition + open-source SCADA precedent
- ADR-2604252100 — OPC UA / AutomationML industrial-integration table
- ADR-2605215000 — Murakumo-only inference
- ADR-2605261215 — igata R1 benchtop commissioning (R1 pairing target)
- IEC 61131-3 (PLC languages), IEC 61508 / 61511 (functional safety, reference discipline)
- ISA-95 / Purdue reference model (layer mapping)
- OpenPLC: https://autonomylogic.com/ — FUXA: https://github.com/frangoteam/FUXA — Rapid SCADA: https://rapidscada.org/ — open62541: https://open62541.org/
