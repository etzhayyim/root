# 70-tools/e7m-sim-preflight

**Status**: PRE-FLIGHT stack validation harness for the e7m-sim charter.

**Authority**: ADR-2605261600 (substrate charter) + ADR-2605252615 (Kusawake R0).
Lives **alongside but distinct from** `70-tools/e7m-sim/` (which is R0 = zero-code per charter §R0).

## What this is

A self-contained, Murakumo-independent harness that exercises the OSS sim
stack mandated by ADR-2605261600 (MuJoCo / MuJoCo MJX / Mitsuba 3 / OpenUSD /
Embree) on a single developer machine, producing concrete pass/fail evidence
that feeds the scoring document at `90-docs/baien/sim-substrate-scoring-260526.md`.

It is **not** the operational sim substrate:

| Aspect | `e7m-sim/` (operational, R0 = empty) | `e7m-sim-preflight/` (this) |
|---|---|---|
| Authority | ADR-2605261600 R1+ deliverable | ADR-2605261600 R0 "scoring evidence skeleton" |
| Murakumo fleet placement | required (G4) | optional (runs on a dev Mac) |
| simulationRunAttestation emission | required (G6) | not emitted |
| Witness quorum (≥2 Ed25519) | required (G11) | not enforced |
| G5 ≥ 0.75 vs Isaac Sim ground truth | required for R-phase advance | not measured (no Isaac trial machine here) |
| Charter Rider §2 asset scan | required (G10) | not run (primitive shapes only, no marketplace assets) |
| Decommission point | never (it is the R1+ SoT) | when R1 lands and supersedes this evidence |

## What this validates

| # | Question | Script | Evidence file |
|---|---|---|---|
| 1 | Same-hardware bit-identical replay (G7 pre-flight) | `verify_determinism.py` | stdout |
| 2 | MuJoCo MJX (JAX) runs Kusawake mech on Apple Silicon CPU | `verify_mjx.py` | stdout |
| 3 | Mitsuba 3 forward render on Apple Silicon | `verify_mitsuba.py` | `out/kusawake_render.png` |
| 4 | Mitsuba 3 differentiable rendering (PRB) wires through | `verify_mitsuba_diff.py` | `out/diff_target.png` + `out/diff_final.png` |
| 5 | OpenUSD scene composition + reference fleet | `verify_usd.py` | `out/kusawake.usda` + `out/kusawake_fleet.usda` |
| 6 | Geometric raycast lidar proxy (precursor to R2 CARLA kernel) | `verify_lidar.py` | `out/kusawake_lidar.ply` |

## What this does **not** validate

- Vulkan RT GPU sensor backbone (Apple Silicon is not a Vulkan RT platform)
- CARLA lidar kernel (R2 binding; this harness ships a `mj_ray`-based proxy)
- BlenderProc synthetic data (R2)
- G5 ≥ 0.75 vs Isaac Sim ground truth (requires the one-time-use isolated
  Isaac Sim trial machine described in ADR-2605261600 §G5 carve-out)
- `simulationRunAttestation` lexicon (R1 ADR work)
- Bit-identical replay across hardware (G7 R1 deliverable; only same-hw here)
- HdCycles render delegate (R1 work; this harness uses Mitsuba 3 only)

## Run

```bash
cd 70-tools/e7m-sim-preflight
uv venv --python 3.12 .venv
.venv/bin/python -m pip install -q mujoco mujoco-mjx jax mitsuba usd-core numpy

# Mitsuba 3 differentiable needs libLLVM (Homebrew):
#   brew install llvm
#   export DRJIT_LIBLLVM_PATH=/opt/homebrew/opt/llvm/lib/libLLVM.dylib

.venv/bin/python verify_determinism.py        # G7 same-hw bit-identical
.venv/bin/python verify_mjx.py                # MJX 16× JIT parallel rollout
.venv/bin/python verify_usd.py                # USD compose + reference fleet
.venv/bin/python verify_lidar.py              # mj_ray sweep → .ply
DRJIT_LIBLLVM_PATH=/opt/homebrew/opt/llvm/lib/libLLVM.dylib .venv/bin/python verify_mitsuba.py
DRJIT_LIBLLVM_PATH=/opt/homebrew/opt/llvm/lib/libLLVM.dylib .venv/bin/python verify_mitsuba_diff.py

.venv/bin/mjpython view.py                    # interactive viewer (mac native)
```

Output evidence accumulates in `out/`. Committed snapshots (PNGs, .usda,
.usdc, .ply) form the empirical companion to ADR-2605261600's scoring claims.

## Constitutional posture

- **License**: Apache 2.0 + Charter Compliance Rider v2.0 (root `CHARTER-RIDER.md`).
- **Murakumo**: not used (G4 carve-out — this is preflight, not operational).
- **No commercial GPU rental**: Apple Silicon local only; no RunPod / Vertex /
  OpenAI / Bedrock / Linode (ADR-2605215000 invariant respected — though this
  harness is not under that invariant since it does not invoke inference).
- **Vendor rejection chain**: zero NVIDIA Omniverse / Isaac Sim / Isaac Lab /
  OptiX / RTX Renderer / Replicator / DriveSim / Omniverse Cloud / Nucleus
  imports anywhere (`grep -rE "omniverse|isaac.?sim|optix|replicator" .` → 0).
- **PhysX 5 SDK**: not used in this harness (MuJoCo is the physics path).
  ADR-2605261600 permits PhysX 5 BSD-3 standalone OSS library use; not exercised here.

## Decommission

When ADR-2605252630 (Kusawake R1) or a comparable R1 sim ADR lands and
populates `70-tools/e7m-sim/` with the operational substrate, this preflight
harness can be deleted. The committed evidence in `out/` and the scoring
document in `90-docs/baien/sim-substrate-scoring-260526.md` remain as
historical record of the R0 pre-flight gate having passed.
