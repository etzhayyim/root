# noroshi 烽 — 光電融合 comms chip · ISAC · photonic packaging robotics

> **DID** `did:web:etzhayyim.com:actor:noroshi` · Tier-B · R0 · ADR-2606051600

烽 (狼煙, *beacon-fire*) is the oldest optical telecom: a watchtower **senses** a distant fire and
**relays** a coded message. One emission, two functions — which is exactly **ISAC** (Integrated
Sensing And Communication). noroshi is the **photonics-electronics convergence (光電融合)**
communication-chip actor: the silicon-photonic / co-packaged-optics (CPO) sibling of the **electronic**
`silicon`/`iwakura`/`fuigo` line and the RF `tsutae` comms device, and the transceiver-chip end of the
`watatsuna` submarine-cable medium.

## Three faces (each a verifiable `methods/` core)

| Face | What | Core | Result |
|---|---|---|---|
| **chip** | silicon-photonic / CPO comms-chip design + optical link budget | `methods/link_budget.py` | CPO closes a 2 km/100G link at **+10 dB margin** + **3.96× less energy/bit** than a pluggable; receiver sensitivity from a target BER (Q-factor + thermal-noise), PIN **and** APD (avalanche gain vs excess noise) |
| **isac** | one OFDM-JCAS waveform → communication capacity **and** range-Doppler sensing | `methods/isac_sim.py` | recovers a civilian object's range+velocity (single + **multi-target CLEAN** + **CA-CFAR detection** + **Pd-vs-SNR** characterisation); sweeps the **comms↔sensing power-split** tradeoff |
| **packaging** | photonic assembly robotics: fibre↔grating active alignment + laser safety | `methods/active_alignment.py` | two-stage (raster OR early-stop **spiral** acquisition → Hooke-Jeeves refine) finds the coupling peak to **<1 dB**, robust to a far/narrow-lobe start; IEC 60825 + civilian-use interlock |

## Charter shape (why this is charter-clean, not just a chip project)

- **Civilian by construction (G3/N1)** — optical power and ISAC sensing are civilian only.
  Weaponisation (directed-energy weapon, laser dazzler, fire-control/targeting radar) is
  **structurally unrepresentable** in the schema, lexicons, and `active_alignment.PERMITTED_USES`
  (the iwakura/nusa `:class` precedent).
- **Sensing ≠ surveillance (G4/N2)** — an ISAC estimate is an **object's** range+velocity; there is no
  `:person` target class, no biometric, no pattern-of-life (the watari invariant).
- **Clean-room open-EDA (G1/N5)** — open photonic + digital EDA only (GDSFactory / Meep / KLayout /
  Verilator / yosys / OpenLane + open PDK), extending the verified iwakura RTL→sky130 GDSII flow to
  photonics. No Cadence/Synopsys/Lumerical/Ansys, no NDA foundry PDK, no decompile/trademark.
- **Laser-safety soft-gate (G5/N3)** — IEC 60825 enclosure-interlock + class gate, best-effort
  soft-safety, **not** a certified controller (kotoba-os N2 precedent).
- **no-server-key (G7)** + **outward-gated (G8)** — tapeout / mask order / robot actuation are
  member/operator-signed; live fab / live laser / live actuation is Council Lv6+ (Class-3B/4 Lv7+).
- **displacement-dividend coupling (G2)** — packaging robots displace fibre-alignment technicians, so a
  live fleet requires a funded tenure-weighted cohort (ADR-2606032130).
- **kotoba-EAVT canonical state (G9)** + **`:representative` honesty (G10)** — every device, budget,
  waveform, estimate, and job is a Datom; no silicon exists, sims are arithmetic/DSP.

## R1 integrations (this session)

The three follow-ups, each a verifiable bridge that composes noroshi with an existing actor/engine:

| Bridge | Wires | Core | Result |
|---|---|---|---|
| **(c) optical-network resilience** | noroshi CPO chips ↔ **watatsuna** submarine-cable medium | `methods/cable_endpoint.py` | sizes the CPO-transceiver fleet at every cable's landings → per-chokepoint demand by **station-tag** AND **authoritative `:cable.seg/traverses` physical-crossing** views (luzon-strait top in both). Resilience, **never a target-list** (inherits watatsuna G2 / watatsumi N8) |
| **(a) ISAC sensor in the GNC loop** | noroshi ISAC ↔ **kami-autodrive** (ADR-2606010600) | `methods/kami_isac_bridge.py` + `wit/kami-isac.wit` | drives the ISAC estimator from a moving-object scenario → per-object range/velocity tracks (the `IsacSensor` plant). Civilian objects only (N1/N2) |
| **(b) PIC layout → budget loop** | noroshi chip face ↔ **open-EDA** (GDSFactory-shaped) | `methods/pic_layout.py` | emits neutral ModelOp layout plans for the **transmitter AND receiver** PIC (sumitsubo pattern); both waveguide lengths feed the end-to-end `link_budget.py`; real GDS write gated behind an optional `gdsfactory` import (G1/G8) |

**Honest integration state (G10)**: the `40-engine/kami-engine` submodule is unpopulated and
`gdsfactory` is not installed in this checkout, so (a) ships as a Python bridge + WIT contract (not a
compiled crate) and (b) as a ModelOp plan + gated GDS backend — the sumitsubo "op-list now, live tool
binding follow-up" pattern. (c) is a full offline join over the present watatsuna seed.

## Layout

```
noroshi/
├── manifest.edn / manifest.jsonld   # actor SSoT (gates / non-goals / cells / lex / EPDA tiers)
├── methods/                         # 3 cores + 3 R1 bridges + charter-invariants (stdlib, 189 tests)
│   ├── link_budget.py · isac_sim.py · active_alignment.py         # the 3 faces
│   ├── cable_endpoint.py · kami_isac_bridge.py · pic_layout.py    # R1 bridges (c/a/b)
│   ├── test_charter_invariants.py   # structural civilian-only / no-server-key / open-EDA guard
│   └── _edn.py · test_*.py
├── cells/                           # 6 langgraph→WASM cells; active_alignment is the coded one (14 tests)
│   └── active_alignment/{cell.py,state_machine.py}
├── lex/                             # 5 com.etzhayyim.noroshi.* lexicons
├── wit/kami-isac.wit                # ISAC-sensor WIT contract (kami-autodrive plant)
├── kotoba/{schema.edn,seed.edn}     # EAVT vocab + :representative seed
├── data/seed-photonic-fleet.kotoba.edn   # packaging robotics fleet (G2 dividend-coupled)
└── out/                             # generated link-budget / isac / alignment / bridge reports
```

## Test

```sh
cd methods && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest   # 189 passed (cores+bridges+invariants+SSoT+well-formedness+governance)
cd cells   && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest   # 14 passed
```

**R0 = design + simulation only.** No foundry tapeout, no measured device, no live laser, no live
robot. See `90-docs/adr/2606051600-noroshi-photonic-electronic-convergence-comms-chip-isac.md`.
