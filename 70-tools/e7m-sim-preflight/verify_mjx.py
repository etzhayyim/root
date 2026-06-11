"""Verify MuJoCo MJX (JAX backend) per ADR-2605261600 §Reference Composition.

MJX is the actual ADR binding for articulated physics (Apache 2.0, GPU-parallel
via JAX/XLA). This script:
  1. Loads kusawake.xml into MJX
  2. Runs N parallel rollouts in JIT-compiled batch
  3. Compares to MuJoCo C++ rollout (rough cross-check, not bit-identical
     across implementations — different solver tolerances are expected)
"""
from __future__ import annotations

import time
from pathlib import Path

import jax
import jax.numpy as jp
import mujoco
import numpy as np
from mujoco import mjx

MODEL = Path(__file__).parent / "kusawake_mjx.xml"  # capsule-wheel variant (MJX collision-pair support)
N_PARALLEL = 16
N_STEPS = 200


def main() -> None:
    print(f"JAX backend: {jax.default_backend()}, devices: {jax.devices()}")
    print()

    # Load shared model
    m = mujoco.MjModel.from_xml_path(str(MODEL))
    mx = mjx.put_model(m)
    print(f"Model: nq={m.nq}, nv={m.nv}, nu={m.nu}")

    # Reference (MuJoCo C++)
    d_ref = mujoco.MjData(m)
    ctrl = np.array([0.30, 0.30, -0.30, -0.30, 3.0, 3.0, 3.0, 3.0])
    t0 = time.time()
    for _ in range(N_STEPS):
        d_ref.ctrl[:] = ctrl
        mujoco.mj_step(m, d_ref)
    t_ref = time.time() - t0
    final_ref = np.array(d_ref.qpos)
    print(f"MuJoCo C++ 1× rollout (N={N_STEPS}): {t_ref * 1000:.1f} ms")
    print(f"  final chassis xyz: {final_ref[:3]}")
    print()

    # MJX batched
    @jax.jit
    def step_batch(dx_batch, ctrl_batch):
        def step_one(dx, c):
            dx = dx.replace(ctrl=c)
            return mjx.step(mx, dx)
        return jax.vmap(step_one)(dx_batch, ctrl_batch)

    # Initialize batch — N_PARALLEL identical initial states
    dx_single = mjx.make_data(mx)
    dx_batch = jax.tree.map(lambda x: jp.broadcast_to(x, (N_PARALLEL, *x.shape)), dx_single)
    ctrl_batch = jp.broadcast_to(jp.array(ctrl, dtype=jp.float32), (N_PARALLEL, m.nu))

    # Warm up JIT
    print("MJX JIT warm-up...")
    t0 = time.time()
    dx_batch = step_batch(dx_batch, ctrl_batch)
    jax.block_until_ready(dx_batch.qpos)
    t_jit = time.time() - t0
    print(f"  first-call (JIT compile + 1 step): {t_jit * 1000:.0f} ms")

    # Steady-state batched
    t0 = time.time()
    for _ in range(N_STEPS - 1):
        dx_batch = step_batch(dx_batch, ctrl_batch)
    jax.block_until_ready(dx_batch.qpos)
    t_mjx = time.time() - t0
    print(f"MJX {N_PARALLEL}× parallel rollout (N={N_STEPS - 1}): {t_mjx * 1000:.1f} ms")
    print(f"  per-rollout effective: {t_mjx * 1000 / N_PARALLEL:.2f} ms")
    print(f"  speedup vs C++ single: {t_ref / (t_mjx / N_PARALLEL):.1f}×")
    print()

    # Cross-check
    final_mjx = np.asarray(dx_batch.qpos[0])
    print(f"MJX[0] final chassis xyz: {final_mjx[:3]}")
    print(f"diff vs C++:              {final_mjx[:3] - final_ref[:3]}")
    max_diff = float(np.abs(final_mjx - final_ref).max())
    print(f"max abs diff (qpos):      {max_diff:.3e}")
    print()
    if max_diff < 0.05:
        print("MJX vs C++: close (different solver paths but consistent envelope)")
    else:
        print(f"MJX vs C++: max diff {max_diff:.3e} larger than 0.05 — investigate before R1 binding")


if __name__ == "__main__":
    main()
