# giemon kabitori — hardware BOM (R0 benchtop prototype)

Real-world parts for the mold-removal cleaning probe whose dynamics are
simulated by `giemon_kabitori`. Scope = **R0 benchtop / hand-held proof**: a
steerable, suction-coupled rotary-brush probe for A/C drain pans + blower
housings, building gaps, and HVAC ducts. This is an engineering parts list, not
a purchase order; vendors are examples. Money/procurement is out of scope here
(Charter substrate rules apply if this is ever sourced through the corp).

> **Safety first (read before building).** Mold remediation aerosolises spores;
> **dead mold is still allergenic**. The machine MUST kill **and extract**, not
> just kill. Operate with the suction running, HEPA on the exhaust, operator in
> N95/P2 + eye protection, and never re-aerosolise. Biocide handling per its
> SDS. Mains-powered wet work near A/C electronics ⇒ isolate power + RCD/GFCI.

## System block diagram

```
            ┌──────────────── handle / carriage ────────────────┐
  operator → │ trigger + 6-DOF control │ MCU │ motor drivers      │
            └───────┬───────────────────────────────┬───────────┘
                    │ flexible probe (φ8–12 mm)      │ hoses
   feed (prismatic)─┤  steering tendons ×4           ├─ biocide feed line
                    │  drive shaft → brush           ├─ coaxial suction
                    ▼                                ▼
              ┌── brush head ──┐               extraction → HEPA → tank
              │ camera+LED     │  spinning bristle disc
              │ nozzle (mist)  │  + shroud (suction skirt)
              └────────────────┘
```

## A. Mechanism / structure

| # | Part | Spec | Maps to sim | Example |
|---|---|---|---|---|
| A1 | Flexible probe shaft | φ8–12 mm, ~600 mm, torsionally stiff / laterally compliant (coil-reinforced PU or nitinol-spine) | `link_seg1/2` continuum segments | borescope conduit / drain-snake core |
| A2 | Steering tendons | 4 × Ø0.45 mm 7×7 SS cable, antagonistic | `j_pitch`/`j_yaw` revolutes | — |
| A3 | Linear feed stage | belt or leadscrew, 0–300 mm, ~30 N | `j_feed` prismatic | OpenBuilds C-beam 250 |
| A4 | Brush drive shaft | flex shaft inside A1, ≥10 N·mm @ 3–6k rpm | `j_brush` revolute | Dremel flex-shaft 225 |
| A5 | Brush head + shroud | Ø20–30 mm nylon/abrasive disc + suction skirt | brush capsule "bristle cross" + footprint | bottle/HVAC brush; printed shroud |
| A6 | Carriage / handle | printed PETG/ABS + Al spine | fixed `base_link` | — |

## B. Actuation

| # | Part | Spec | Maps to sim | Example |
|---|---|---|---|---|
| B1 | Brush motor | BLDC/coreless, 3–6k rpm, ~5 W | `j_brush` effort=5 | N20 12 V 6 V variants / small BLDC |
| B2 | Steering servos ×2 | metal-gear, ≥2.5 N·m, tendon pulleys | `j_yaw`/`j_pitch` effort 25/30 | DS3225 25 kg·cm |
| B3 | Segment micro-servos ×2 | ≥1.0 N·m | `j_seg1/2` effort 14/10 | MG90S-class |
| B4 | Feed motor | NEMA-17 + driver, ~40 N | `j_feed` effort=80 | NEMA-17 + A4988/TMC2209 |

## C. Cleaning payload + extraction (the part the rigid sim does NOT model)

| # | Part | Spec | Note |
|---|---|---|---|
| C1 | Suction source | ≥30 L/s, sealed | coaxial around shaft; the real spore-control element |
| C2 | HEPA filter | H13 (≥99.95% @0.3 µm) on exhaust | mandatory — captures aerosolised spores |
| C3 | Collection tank | sealed wet/dry, 1–3 L | dead-mold slurry capture |
| C4 | Biocide pump + nozzle | peristaltic, 1–5 mL/min, fine mist at head | use a **registered antifungal** (e.g. quaternary-ammonium / stabilised hypochlorite per local approval) — NOT improvised |
| C5 | Drip/over-spray guard | silicone skirt | keep wet work off A/C electronics |

> Future sim work (§2 erosion field → fluid/biofilm) would model C1–C4; today
> the rigid solver only validates the A/B mechanism + brush contact.

## D. Sensing + control

| # | Part | Spec | Maps to sim |
|---|---|---|---|
| D1 | Tip camera + LED ring | φ5.5–8 mm endoscope, ≥720p | the "see it before you scrub" path; not yet in sim |
| D2 | Tip IMU (opt.) | 6-axis | probe-pose estimate ↔ `fk_world` |
| D3 | Brush current sense | INA-class on B1 | contact-force proxy ↔ solver normal impulse |
| D4 | MCU | ESP32-S3 / RP2040 | runs the controller; mirrors the sim's `tau[]` program |
| D5 | Power | 12 V 5 A + buck rails | — |

## E. Bill totals (rough order of magnitude, R0 one-off)

| Group | Indicative |
|---|---|
| A structure | mid |
| B actuation | mid |
| C extraction + biocide | **highest** (suction + HEPA dominate) + consumables |
| D sensing/control | low–mid |

Exact pricing intentionally omitted — size once a target environment (drain
line vs. duct vs. wall cavity) is fixed, because C1/C2 (airflow + HEPA) scale
with the largest cavity volume you must keep under negative pressure.

## Build order (de-risked)

1. **Bench the brush + suction shroud** against a mold-on-tile coupon — verify
   removal AND that the shroud captures debris (no aerosol escape). This is the
   make-or-break test; everything else is positioning.
2. Add the flexible shaft + brush drive (A1/A4/B1); hand-feed.
3. Add steering (A2/B2-B3) + tip camera (D1); teleoperate.
4. Add the powered feed stage (A3/B4) + MCU control (D4) running the same
   feed→dip→scrub program validated in `giemon_kabitori` simulation.

## Sim ↔ hardware correspondence (validated today)

The simulation already validates the **kinematics + contact** of A1–A6 / B1–B4:
6-DOF reach into a walled gap, brush↔surface contact-force regulation, tangential
scrub, and that scrubbing removes coverage locally (§2 mold field). It does
**not** yet validate C (airflow/biocide/biofilm) — that needs the deferred
fluid/erodible-material solvers.
