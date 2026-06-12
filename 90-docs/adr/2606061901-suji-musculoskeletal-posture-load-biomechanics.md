---
id: adr-2606061901-suji-musculoskeletal-posture-load-biomechanics
renumbered_from: "2606061900"
title: "ADR-2606061901: suji (筋) — Musculoskeletal Posture-Load Biomechanics Simulator"
status: proposed
doc_type: adr
topic: suji-musculoskeletal-biomechanics
authoritative: true
last_verified: 2026-06-06
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "first musculoskeletal biomechanics actor; the physics-simulation layer between kizashi (sensing) and mitate (diagnosis) in the L4 Care tier"
authoritative_for:
  - suji
  - musculoskeletal-biomechanics
  - posture-load-simulation
depends_on:
  - 2605312700
  - 2605261000
  - 2605311500
  - 2605311800
  - 2605312345
  - 2605215000
  - 2605231525
  - 2605181100
related:
  - 2605260100
  - 2605263000
  - 2606010030
  - 2606010600
  - 2605261800
  - 2606051600
  - 2605241900
  - 2606042330
  - 2605192100
supersedes: []
superseded_by: []
---

# ADR-2606061901: suji (筋) — Musculoskeletal Posture-Load Biomechanics Simulator

**Status**: proposed
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

A request: *「kami engine, kotoba で人体の骨・筋肉のシミュレーションを行なって、ノートパソコンの
姿勢が人体にどういった緊張・強張りを作るかを物理シミュレーション (Isaac Sim)」* — simulate the
human skeleton and muscles, and physically simulate what tension (緊張) and stiffness (強張り) a
laptop posture builds in the body.

The L4 Care tier already has a **sensing** actor — `kizashi` 兆 (ADR-2605312700), the multimodal
non-invasive scan pod that reads posture/gait/筋硬度 — and **clinical** actors `mitate` (diagnosis)
and `iyashi` (treatment). What was missing is the **mechanics engine in between**: given a posture,
what are the joint loads and muscle tensions, and how do they accumulate into stiffness over a work
session? That is a physics problem (static inverse dynamics + a muscle model), not a sensing or a
clinical problem — and physics is exactly what `kami-engine` (the kami-genesis articulated
rigid-body solver, ADR-2605311500/1800) and `kotoba` (the canonical Datom log, ADR-2605312345) are
for.

The hazard is the **medical boundary**. A tool that takes a body and reports "tension/stiffness" is
one careless schema field away from practising medicine without a licence (医師法 §17) or shipping an
unregulated medical device (薬機法/SaMD). `kizashi`'s constitutional discipline (non-diagnostic,
device-boundary, encrypted-PII, anti-pseudoscience, Murakumo-only) is the precedent; suji must
inherit it and add one of its own: it is a *simulation*, so it must never become a sensor or a clinic.

# Decision

Create **`suji` 筋** (muscle/sinew **and** line-of-force/reasoning — the double meaning of a static
force-balance engine), a Tier-B L4-Care **biomechanics-simulation / instrument** actor, upstream of
clinical adjudication:

> `kizashi` senses → **`suji` simulates the loads** → `mitate` diagnoses → `iyashi` treats

## Physics (runnable, validated)

1. **Skeleton** — a sagittal-plane articulated **segment chain** (head → cervical → thorax → lumbar
   + arm) built from de Leva / Winter anthropometry (`methods/segment.py`). This is exactly the
   `PlanarChain` articulation kami-genesis solves.
2. **Posture** — `methods/posture.py` maps a laptop **workstation** (screen-below-eye, keyboard
   height, backrest, arm support) to sagittal joint angles by a documented monotonic kinematic
   model (NOT a biometric measurement — `kizashi` owns sensing).
3. **Bones / loads** — `methods/load.py` solves the **static inverse dynamics** (the gravity term of
   Featherstone RNEA) for the per-joint moment, and the cervical compressive load. The cervical leg
   is **VALIDATED against Hansraj (2014)** (*Surgical Technology International* 25): neutral ≈ head
   weight rising to ~5× at 60° flexion (the "60-lb tech-neck" figure), reproduced within ~10%.
4. **Muscles** — `methods/muscle.py` distributes joint moments to a Hill-type moment-arm muscle
   model (force = moment / arm; %MVC = force / F_max) over the laptop-relevant set: cervical
   extensors, upper trapezius, levator scapulae, anterior deltoid, erector spinae. %MVC **is** 緊張.
5. **強張り (stiffness)** — `methods/strain.py` accumulates the Rohmert sustained-isometric dose
   (endurance time falling steeply with %MVC, plus the chronic low-load "Cinderella" term that
   drives desk-work 肩こり) into a `[0,1]` stiffness index over a held session.
6. **Answer** — `methods/analyze.py` runs laptop-on-lap (23.6 kgf neck) vs laptop-on-desk vs
   external-monitor-at-eye-level (8.1 kgf, **−66%**), self-referenced (the same body across setups).
7. **kotoba** — `methods/datoms.py` projects the run into schema-conformant EAVT Datoms (G9 audit,
   as-of, 非終末論), drift-locked against `kotoba/schema.edn`.

## Isaac Sim / kami-genesis

`wit/kami-biomech.wit` is the articulation contract a kami-genesis `PlanarChain` / nv-compat
`isaacsim.core.api` `Articulation` would implement; `methods/kami_biomech_bridge.py` builds the
link/joint/gravity spec and returns the same static joint moments the full RNEA backend would. Honest
R0: the `40-engine/kami-engine` submodule is unpopulated, so this is the WIT contract + Python
reference, not a compiled backend (the `noroshi` pattern). No live actuation — the body is passive.

## Constitutional gates (G1–G10)

- **G1 NON-DIAGNOSTIC (医師法 §17)** — every output is a mechanical quantity. No
  `diagnosis`/`disease`/`icd`/`prescription`/`treatment`/`condition` field is representable in the
  schema, the lexicons, OR the `load_solve` cell (`assert_nondiagnostic` refuses a clinical key by
  construction — the nusa `:thc-class` / tazuna `:weaponizable` / kamado `:fossil-virgin-crude`
  pattern). A licensed clinician (`mitate`/`iyashi`) owns any diagnosis.
- **G2 simulation-only / not-a-medical-device (薬機法/SaMD)** — no sensing hardware, no biometric
  capture; inputs are posture parameters.
- **G3 self-referenced Wellbecoming** — `as-of` stiffness trajectory, same-member comparison only;
  `strain_accumulate` refuses any population-ranking field (percentile/rank/cohort/…). 非終末論.
- **G4 encrypted envelope on a real scan** (ADR-2605181100) — a body built from a real `kizashi`
  scan carries 要配慮 PII → `encryptedPayloadCid`; suji's own bodies are `:representative` averages.
- **G5 Murakumo-only · G6 no-server-key · G7 sourcing-honest · G8 outward-gated · G9 kotoba-EAVT ·
  G10 anti-pseudoscience** (Hill-model muscles only; 経絡/気/波動 excluded — `kizashi` N8).

# Consequences

- L4 Care gains its missing mechanics layer; a member can ask "what does my laptop setup do to my
  neck/shoulders?" and get a validated physical answer with an ergonomic comparison — without any
  clinical claim.
- The non-diagnostic boundary is now enforced **structurally** (schema + lexicon + cell-gate), not by
  convention, strengthening the `kizashi` precedent across the tier.
- A concrete, tested consumer of the kami-genesis `PlanarChain` / Isaac articulation surface exists
  as a WIT contract, ready to bind when the `kami-engine` submodule is populated.
- **Honest R0**: design + runnable physics + a validated cervical model. Anthropometry/muscle/
  endurance are `:representative` (the cervical leg is validated; the muscle %MVC and Rohmert strain
  legs are mechanistically grounded but illustrative). No hardware, no live member scan, no live
  kami-genesis backend. Cells `.solve()` raise at R0; `load_solve` + `strain_accumulate` transitions
  are unit-tested. **45 tests green**; WIT valid. Live `kizashi` feed / clinical handoff to `mitate`
  is Council Lv6+ + operator gated (G8). **ZERO invariant amendments.**

# Alternatives Considered

- **Fold into `kizashi`.** Rejected: `kizashi` is the *sensor* (and its discipline is built around
  encrypted biometric capture); suji is a *simulator* with no capture. Keeping them separate is what
  lets suji's inputs be public posture parameters and keeps the SaMD surface minimal.
- **Full forward-dynamic muscle sim now.** Rejected for R0: requires the unpopulated kami-genesis
  crate and a musculotendon solver. The static inverse-dynamics special case is independently
  checkable in stdlib, validates against Hansraj, and is the gravity term the full RNEA backend
  returns — so the WIT contract is exercised today and the dynamic upgrade is additive.
- **3-D (frontal + transverse) model.** Deferred: the sagittal plane captures the dominant
  laptop-posture loads (forward head, trunk lean, shoulder reach); 3-D is an R2 extension.

# References

- `20-actors/suji/` — manifest, methods, cells, lex, kotoba, wit, README, CLAUDE.md
- ADR-2605312700 — kizashi (sensing instrument, L4 Care)
- ADR-2605311500 / 2605311800 — kami-genesis articulation (PlanarChain, Featherstone RNEA)
- ADR-2606010030 — kami-genesis maturation (nv-compat Isaac `ArticulationView`/`ArticulationBatch`)
- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605231525 — no-server-key · ADR-2605215000 — Murakumo-only · ADR-2605181100 — encrypted envelope
- Hansraj KK (2014), "Assessment of stresses in the cervical spine caused by posture and position of
  the head", *Surgical Technology International* 25 — cervical-load validation anchor
- Winter DA, *Biomechanics and Motor Control of Human Movement* (4e) — segment parameters; Rohmert W
  (1960) — isometric endurance
