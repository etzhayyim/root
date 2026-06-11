---
id: adr-2606111100-seigyo-r1-benchtop-loop-commissioning
title: "seigyo R1 — Benchtop temperature-PID loop commissioning and Council baseline (paired with igata R1 benchtop)"
status: proposed
doc_type: adr
topic: seigyo/control-layer/benchtop-loop
authoritative: true
last_verified: 2026-06-11T00:00:00Z
depends_on:
  - ADR-2606111000
  - ADR-2605261215
  - ADR-2605192100
  - ADR-2605192200
  - ADR-2605215000
---

# seigyo R1 — Benchtop temperature-PID loop commissioning and Council baseline

**Date:** 2026-06-11
**Author:** Jun Kawasaki
**Status:** Proposed

## Context

R0 (ADR-2606111000) chartered seigyo (制御) as the industrial control layer
(ISA-95 L0–L2) for all religious-corp manufacturing actors, with 5 scaffold
cells, the §3 hardwired-safety invariant, the §4 PLC-program-as-attested-record
lifecycle, and a vendor prohibition generalizing ADR-2605265000 §1.9.

R1 transitions from paper to **one physical loop**, deliberately the smallest
loop that still exercises every layer and every invariant end-to-end. The
pairing target is **igata R1 benchtop commissioning** (ADR-2605261215): igata's
`die_preparation` cell requires a die preheat to 220°C, and igata §4 firmware
retrofit requires open-source control with documented interlocks — both of
which are seigyo's job to standardize. Commissioning seigyo R1 on a **mock
furnace** (no molten metal, no HPDC integration risk) follows the same
de-risking logic as igata's Hibachi/Tatara PoC firmware on mock die / mock
crucible (igata R1 §8 items 5–6).

## Decision

### 1. The R1 loop — ≤2 kW mock-furnace temperature PID

**Hardware (BENCH-R1 rig, total ≤10 I/O points per R0 §8 cap):**

| Item | Spec | Note |
|---|---|---|
| Furnace | ≤2 kW electric resistance benchtop chamber, element rated 400°C | second-hand lab/kiln preferred per igata §4 procurement ethic |
| Sensor | K-type thermocouple + MAX31855 (0.25°C counts) | `%IW0` |
| Actuator | SSR, slow PWM (2 s period), duty ceiling 80% | `%QX0.0` |
| Controller | commodity SBC/PC running **OpenPLC runtime** | program per §1 reference |
| L2 | **FUXA** project (trend + setpoint entry + alarm banner) | CID-attested |
| L2.5 | **open62541** OPC UA server exposing `sp_request` / `pv` / `clamp_count` | bridge target |
| **L1S (hardwired)** | series E-stop chain + contactor **upstream of the SSR**; non-resettable 300°C thermal fuse in the heater circuit | software sees read-only mirrors only |

**Reference program**: [`20-actors/seigyo/reference/bench_pid_loop.st`](../../20-actors/seigyo/reference/bench_pid_loop.st)
(IEC 61131-3 ST, canonical committed form) with envelope mirror
[`bench_pid_loop.envelope.json`](../../20-actors/seigyo/reference/bench_pid_loop.envelope.json):
setpoint 0–250°C, slew ≤5°C/min, PWM duty ≤80%, clamp counter logged for
`silenSeigyoReview`. The 250°C envelope max is **operational** (die-preheat
220°C + margin); the **safety** bound is the hardwired 300°C fuse — the
envelope is two layers below the fuse by design, demonstrating §3/§3.4
separation physically.

### 2. Council Lv6+ attestation baseline: `r1-benchtop-loop-baseline`

Single `silenSeigyoReview` record with `reviewType: "r1-benchtop-loop-baseline"`,
`councilAttestationCount: ≥3`, `approvedRPhase: "R1"`, `approvedSites:
["BENCH-R1"]`, `approvedControllers: 1`, `approvedIoPoints: ≤10`.

**Gate unlock condition**: `COUNCIL_FLEET_ATTESTATION_TX_HASH` +
`SILEN_SEIGYO_BASELINE_REVIEW_CID` set non-`None` in all 5 `seigyo_*` cells;
additionally `CONTROLS_ENGINEER_REGISTRY_CID` (§3) in the two HIGH-risk cells
(`seigyo_plc_program_lifecycle`, `seigyo_interlock_attestation`).

### 3. SME registration — controls engineer

One SME DID required (parallel to igata 3-DID block, scaled to R1 scope):

- **Controls engineer** (`CONTROLS_ENGINEER_REGISTRY_CID`): ≥5 years industrial
  controls experience (PLC programming + functional-safety design discipline,
  IEC 61131-3 + IEC 61508/61511 working knowledge), OR equivalent academic
  credential. Responsibilities: program review sign-off (§4 lifecycle), interlock
  verification protocol authorship, envelope-table review.
- Council attestation Lv6+ ≥3.

The 危険物取扱主任者-equivalent and domain SMEs remain with the paired
manufacturing actor (igata §3) — seigyo R1 has no hazardous material.

### 4. Full lifecycle exercise — the actual R1 deliverable

R1 is complete only when the §4 lifecycle has run end-to-end on real hardware:

1. `bench_pid_loop.st` static-checked + simulated (OpenPLC sim; step-response
   verified against first-principles furnace model)
2. Controls-engineer review sign-off recorded
3. `seigyo.plcProgramAttestation` issued (program CID + envelope table)
4. Deployed to the BENCH-R1 OpenPLC runtime
5. Runtime hash heartbeat verified (`seigyo.runtimeAttestation`) — including
   one **deliberate mismatch drill**: load a modified program, observe
   dispatch-freeze behavior, restore, observe recovery
6. FUXA project CID-attested (`seigyo.scadaProjectAttestation`)
7. OPC UA bridge round trip: setpoint write → envelope precheck → readback
8. **Envelope clamp drill**: request 400°C via OPC UA; verify clamp to 250°C
   at L1 + `clamp_count` increment + northbound record
9. **E-stop verification** (`seigyo.interlockVerificationRecord`): with loop
   at 220°C steady-state, press E-stop → heater power physically interrupted
   upstream of SSR (measured, not inferred from software) → **repeat with the
   controller network cable disconnected** (§3.2 demonstrated literally) →
   physical on-site reset. Engineer DID + measurement evidence CIDs anchored.
10. 7-day soak at 220°C ±2°C duty cycle with historian capture + N7 aggregate
    northbound records flowing

### 5. R1 exit → R2 entry criteria

1. All §4 lifecycle steps 1–10 complete with anchored records
2. **30-day clean runtime-attestation history** (no unexplained hash mismatch;
   the deliberate drill is recorded as a drill)
3. Loop performance: 220°C setpoint held ±2°C over the 7-day soak; slew
   compliance verified from historian (≤5°C/min throughout)
4. Zero envelope-clamp events outside drills (clamps in normal operation
   indicate an L3/L2.5 layer requesting out-of-envelope values — must be
   root-caused, not tolerated)
5. Interlock annual re-verification protocol published (open, Apache 2.0 +
   Charter Rider, per igata G3 ethic)
6. R2 target cell selected by Council (igata die-prep line OR pillow foam
   line) with its I/O point registry drafted

### 6. Constitutional invariants unchanged

No amendment to ADR-2606111000 §1–§8. The R1 rig instantiates them:

- §2 vendor prohibition: every component above is open-source or commodity
- §3 safety path: E-stop + fuse hardwired upstream of the SSR; software holds
  read-only mirrors; §4 step 9 proves the network-cable-cut property
- §3.4 envelopes: compiled into the ST program; drill in §4 step 8
- §5 telemetry: full-rate (100 ms task) stays in the site historian; northbound
  ≥1-minute buckets (no person-attributable signal exists on this rig)

## Consequences

### Positive

- The entire seigyo stack (OpenPLC + FUXA + open62541 + 5 cells + 9 Lexicons)
  is validated on hardware costing well under ¥200k, before any manufacturing
  actor depends on it.
- igata R1 inherits a commissioned die-preheat control pattern instead of
  improvising one under equipment-arrival pressure.
- The E-stop-with-network-cut drill turns the §3 invariant from prose into a
  reproducible test.

### Negative / Risk

- A 2 kW thermal loop is slow and benign; it does not exercise fast loops
  (HPDC shot profiles @ 1 kHz are explicitly out of seigyo L1 scope — igata
  retrofit handles those in dedicated real-time firmware at the L0 boundary
  per R0 §2). R2 must not over-extrapolate from R1.
- OpenPLC PID FB tuning on a high-thermal-mass furnace is forgiving; R2
  production loops will need formal step-test procedure (deferred to R2 ADR).
- Single-SME bottleneck: one controls engineer is a single point of review.
  Acceptable at R1 scale; R3 requires a controls engineer on the Council
  attestation path per R0 §8.

## Alternatives Considered

### A1: Commission seigyo R1 directly on the igata furnace (real die preheat)

Pros: no mock hardware. Cons: couples seigyo's first commissioning to igata's
equipment-procurement timeline (6–18 months, igata R1 consequences) and adds
molten-metal-adjacent risk to a control-stack shakedown. **REJECT** — mock
rig now, real die-prep at R2.

### A2: Use a Raspberry Pi GPIO directly without OpenPLC (plain Python loop)

Pros: simpler. Cons: bypasses the entire §4 lifecycle (no IEC 61131-3
artifact, nothing to attest, no runtime-hash semantics) — R1 would validate
nothing seigyo actually charters. **REJECT**.

### A3: Start with Modbus-only, no OPC UA at R1

Pros: fewer moving parts. Cons: the L2.5 bridge IS the seam every L3 cell
will use; deferring it defers the only integration risk worth retiring early.
**REJECT** — OPC UA in R1, Modbus southbound exercised at R2 with legacy I/O.

## References

- ADR-2606111000 — seigyo R0 master charter (parent)
- ADR-2605261215 — igata R1 benchtop commissioning (pairing target; §4
  procurement ethic; §8 mock-rig PoC precedent)
- ADR-2605215000 — Murakumo-only inference
- ADR-2605192200 — Charter Compliance Rider (§2 audit basis)
- `20-actors/seigyo/reference/bench_pid_loop.st` + `.envelope.json` — R1 artifacts
- IEC 61131-3 / IEC 61508 / IEC 61511 — reference discipline (no certification claim)
