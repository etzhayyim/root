# e7m-sim scene path — `kusawake/`

**Status**: R0 path reservation only. Zero runtime code per ADR-2605261600 §R0 (`R0 deliverable: this charter ADR + reserved scaffold path + Isaac Lab task DSL port path + scoring evidence skeleton. NO code, NO Pregel cells, NO lexicons land at R0.`).

## Binding

- **Robot class ADR**: ADR-2605252615 — Kusawake (草分け) autonomous agri-mobile platform R0.
- **Manufacturer ADR**: ADR-2605261500 — suki Wave 2 (orchard/vineyard <50 hp electric carve-out).
- **Operator ADR**: ADR-2605261015 — mitsuho.autonomous_mobile + harvest_robotics cells.
- **Substrate ADR**: ADR-2605261600 — e7m-sim 5-stack reference.

## R1+ layout (reserved, no code yet)

```
70-tools/e7m-sim/scenes/kusawake/
├── README.md           # this file
├── usd/                # OpenUSD scene composition
│   ├── platform.usda   # Kusawake mech (≤300 kg, 4WD/4WS LFP)
│   ├── orchard.usda    # Wave 2 orchard-row reference field
│   └── pasture.usda    # livestock-herd reference field
├── mjx/                # MuJoCo MJX articulated physics models
│   └── platform.mjcf
├── lidar/              # CARLA lidar kernel + Vulkan RT scene config
├── render/             # HdCycles photoreal + Mitsuba 3 differentiable
├── tasks/              # ported Isaac Lab task DSL (Apache 2.0 header port only)
└── attestation/        # simulationRunAttestation lexicon outputs (R1+)
```

## Preflight evidence (R0 companion)

Pre-flight stack-validation harness lives at `70-tools/e7m-sim-preflight/` and
the scoring narrative at `90-docs/baien/sim-substrate-scoring-260526.md`.
That harness exercises MuJoCo / MJX / Mitsuba 3 / USD / mj_ray on a developer
Mac with the same MJCF design as Kusawake R1 will use, and surfaces concrete
R1 constraints (libLLVM dep, MJX capsule-only wheels, BSDF-not-pose autodiff,
JAX CPU vs C++ tradeoff). This path stays code-empty until R1 lands.

## R0 → R1 gate (per ADR-2605261600 + ADR-2605252615)

R1 PoC must satisfy:

1. MuJoCo MJX single-platform rollout on `orchard.usda` for ≥1000 sim seconds.
2. Mitsuba 3 differentiable RGB consistency check vs HdCycles photoreal render.
3. **G5 quantitative gate ≥ 0.75** vs Isaac Sim trial reference scene (one-time-use isolated machine per ADR-2605261600 G5 carve-out — Isaac Sim never connected to religious-corp infra).
4. `simulationRunAttestation` lexicon emitted (G6).
5. Bit-identical replay on identical hardware; ≤1e-4 L2/step cross-hardware noise (G7).
6. ≤1 GPU-hour-eq/day Murakumo budget cap (G12, R1).

## Constitutional non-goals (R0–R3, immutable)

- **N6 (ADR-2605252615) inherits ADR-2605261600 N3**: NVIDIA Omniverse Kit / Isaac Sim runtime / Isaac Lab runtime / RTX Renderer / OptiX / Replicator / DriveSim / Omniverse Cloud / Nucleus = NEVER.
- **PhysX 5 SDK (BSD-3 standalone OSS release)** = acceptable per ADR-2605261600 N6 carve-out (library only, not the Omniverse Kit bundling).
- No NVIDIA-account-required tool in runtime (G8).
- No telemetry, no usage analytics, no crash reporting (G13).
