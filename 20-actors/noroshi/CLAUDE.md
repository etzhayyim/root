# noroshi (烽) — photonics-electronics convergence (光電融合) comms chip + ISAC + packaging robotics

**DID**: `did:web:etzhayyim.com:actor:noroshi` · **Tier**: B · **Status**: R0 · **ADR**: 2606051600

## What this is

The **光電融合 (photonics-electronics convergence) communication-chip** actor — the silicon-photonic /
co-packaged-optics (CPO) sibling of the **electronic** silicon/iwakura/fuigo line and the RF **tsutae**
comms device. 烽 (狼煙, beacon-fire) is the original optical telecom: a watchtower **senses** a distant
fire and **relays** a coded message — one emission, two functions — which is exactly **ISAC**
(Integrated Sensing And Communication).

Three faces, each with a verifiable `methods/` core:

- **chip** — design + optical link budget of photonic-IC / CPO comms chips on open photonic-EDA.
  `methods/link_budget.py` (CPO = **3.96× lower energy/bit** than a front-panel pluggable on the
  reference designs).
- **isac** — one OFDM-JCAS waveform doing communication capacity **and** range-Doppler sensing.
  `methods/isac_sim.py` (OFDM-radar reciprocal processing + the comms↔sensing power-split tradeoff;
  **civilian objects only**).
- **packaging** — photonic assembly robotics (fibre↔grating active alignment, photonic wire-bond)
  under a laser-safety interlock. `methods/active_alignment.py` (Hooke-Jeeves search + IEC 60825 /
  civilian-use gate — the safety-critical coded core, like tazuna's `teleop_safety`).

## Cells (langgraph→WASM; Murakumo-only; `.solve()` raises at R0)

chip: `device_design` (naphtali) · `link_budget` (gad). isac: `isac_waveform` (asher) ·
`sense_estimate` (benjamin). packaging: **`active_alignment`** (joseph — coded reference cell, the
laser-safety/no-server-key one) · `reliability_qual` (manasseh).

## Gates (immutable R0→R5)

**G1 cleanroom-epda** (open-source photonic + digital EDA ONLY — GDSFactory / Meep / KLayout /
Verilator / yosys / OpenLane + open PDK; NO Cadence/Synopsys/Lumerical/Ansys, no NDA foundry PDK,
no decompile/trademark/fork; iwakura open-EDA + sumitsubo G1 precedent) · **G2
displacement-dividend-coupling** (packaging robotics that displaces fibre-alignment technicians live
needs a funded cohort, ADR-2606032130) · **G3 civilian-force-separation** (optical power + ISAC
sensing civilian-only; weaponisation — directed-energy / laser-dazzle / fire-control radar — is
structurally unrepresentable, Mission Charter §1.12) · **G4 sensing-not-surveillance** (an ISAC
estimate is an OBJECT's range+velocity, never a person / biometric / pattern-of-life; watari G4) ·
**G5 laser-safety-soft** (IEC 60825 enclosure-interlock + class gate is best-effort soft-safety, NOT
certified; hard-RT/certified = R5/Lv7+, kotoba-os N2) · **G6 murakumo-only** (ADR-2605215000) · **G7
no-server-key** (tapeout / mask order / robot actuation member-signed; serverHeldKey=false,
ADR-2605231525) · **G8 outward-gated** (live tapeout / mask set / measurement / laser / actuation =
Council Lv6+ + operator; Class-3B/4 near humans Lv7+) · **G9 kotoba-EAVT audit** (canonical Datom log,
no RisingWave, ADR-2605312345) · **G10 sourcing-honesty** (`:representative`; sims are arithmetic/DSP,
no measured silicon) · **G11 sbom-provenance** (a fabricated die carries a CycloneDX SBOM into kotoba,
gated at tapeout; wasm-sbom / giemon precedent).

## Non-goals

N1 no weaponisation (`:weaponizable` unrepresentable) · N2 no person-surveillance · N3 not a certified
safety controller · N4 no fabricated coverage (honest aliasing) · N5 no proprietary EDA / NDA PDK · N6
no commercial GPU / cloud-EDA · N7 not a foundry / tapeout broker at R0 · N8 no cash for labour /
demonstrations.

## Build / test

```
cd methods && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest   # cores+bridges+invariants+SSoT+well-formedness+governance (189 tests)
cd cells   && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest   # active_alignment state machine (14 tests)
python3 methods/link_budget.py      > out/link-budget.md           # offline report artifacts
python3 methods/isac_sim.py         > out/isac-report.md
python3 methods/active_alignment.py > out/alignment-report.md
python3 methods/cable_endpoint.py   > out/cable-endpoint-resilience.md   # (c) × watatsuna
python3 methods/kami_isac_bridge.py > out/kami-isac-tracks.md            # (a) × kami-autodrive
python3 methods/pic_layout.py       > out/pic-layout.md                  # (b) open-EDA layout
```

## R1 integrations (this session)

- **(c) `cable_endpoint.py`** — joins noroshi CPO chips to the **watatsuna** submarine-cable medium:
  sizes the transceiver fleet per landing → per-chokepoint demand (luzon-strait → suez → malacca →
  gibraltar). Resilience framing inherited from watatsuna (G2, never a target-list).
- **(a) `kami_isac_bridge.py` + `wit/kami-isac.wit`** — ISAC sensor as a **kami-autodrive** plant
  (ADR-2606010600); scenario → per-object range/velocity tracks; civilian objects only (N1/N2).
- **(b) `pic_layout.py`** — GDSFactory-shaped ModelOp layout plan → feeds waveguide length back into
  `link_budget.py`; real GDS write gated behind an optional `gdsfactory` import (G1/G8).

Honest: the kami-engine submodule is unpopulated and gdsfactory isn't installed here, so (a)/(b) are
bridge + contract + gated backend (sumitsubo pattern); (c) is a full offline join.

Stdlib-only (the `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` prefix avoids the global pydantic pytest plugin,
same as tazuna/karakuri). R0 = design + 3 method cores + `active_alignment` state-machine +
`:representative` device/waveform/fleet seed. **No silicon, no foundry, no live laser, no live
actuation** (all gated G8).

## Do not

- Do not introduce a `:weaponizable` force class, a directed-energy / dazzle / fire-control use, or a
  fire-control/targeting sensing mode — N1/G3 (unrepresentable in schema, lexicon, and
  `active_alignment.PERMITTED_USES`).
- Do not add a `:person` target class or any biometric / pattern-of-life field to `senseEstimate` —
  N2/G4 (an ISAC target is an object, not a person).
- Do not bundle a proprietary EDA tool, a vendor NDA foundry PDK, or decompiled/trademarked code — G1/N5.
- Do not let the platform sign a tapeout / mask order / robot actuation, or hold a robot's key — G7 /
  ADR-2605231525.
- Do not energise a hazardous-class (2/3R/3B/4) laser without an enclosure interlock + safety
  attestation — G5; and do not present this as a certified safety system — N3.
- Do not call any cell's `.solve()` — R0 scaffolds raise `RuntimeError` by design.
- Do not present a sim number as a measured device, or imply silicon exists — G10/N4.
- Do not route design/inference through a commercial GPU or cloud-EDA — G6/N6 (Murakumo-only).
