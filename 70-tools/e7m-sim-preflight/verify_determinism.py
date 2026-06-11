"""G7 invariant pre-flight: bit-identical replay on the same hardware.

ADR-2605261600 G7 requires: same model + same hardware → bit-identical replay,
cross-hardware drift ≤1e-4 L2/step. This sandbox check covers the same-hardware
case only.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import mujoco
import numpy as np

MODEL = Path(__file__).parent / "kusawake.xml"
N_STEPS = 5000
CTRL_PATTERN = np.array([0.20, 0.20, -0.20, -0.20, 3.0, 3.0, 3.0, 3.0])  # Ackermann


def rollout(seed: int = 0) -> tuple[np.ndarray, np.ndarray, str]:
    m = mujoco.MjModel.from_xml_path(str(MODEL))
    d = mujoco.MjData(m)
    states = np.empty((N_STEPS, m.nq + m.nv))
    for i in range(N_STEPS):
        d.ctrl[:] = CTRL_PATTERN
        mujoco.mj_step(m, d)
        states[i, : m.nq] = d.qpos
        states[i, m.nq :] = d.qvel
    final = np.concatenate([d.qpos, d.qvel])
    h = hashlib.sha256(states.tobytes()).hexdigest()
    return states, final, h


def main() -> int:
    print(f"Model: {MODEL}")
    print(f"Steps: {N_STEPS}, dt=2ms → {N_STEPS * 0.002:.1f} s sim")
    print()
    print("Run A...")
    states_a, final_a, h_a = rollout()
    print(f"  sha256 trace: {h_a}")
    print(f"  final qpos[:3] (chassis xyz): {final_a[:3]}")
    print()
    print("Run B...")
    states_b, final_b, h_b = rollout()
    print(f"  sha256 trace: {h_b}")
    print(f"  final qpos[:3] (chassis xyz): {final_b[:3]}")
    print()

    diff = np.abs(states_a - states_b)
    l2_per_step = np.linalg.norm(states_a - states_b, axis=1)

    print(f"Max abs diff: {diff.max():.3e}")
    print(f"Mean L2/step: {l2_per_step.mean():.3e}")
    print(f"Max L2/step:  {l2_per_step.max():.3e}")
    print()

    g7_target = 1e-4
    hash_match = h_a == h_b
    l2_pass = l2_per_step.max() <= g7_target

    print(f"G7 same-hardware bit-identical: {'PASS' if hash_match else 'FAIL'} (sha256 match)")
    print(f"G7 L2/step ≤ {g7_target:.0e}:        {'PASS' if l2_pass else 'FAIL'}")
    print()
    print("Note: G7 also requires ≤1e-4 L2/step cross-hardware; not tested here.")
    return 0 if (hash_match and l2_pass) else 1


if __name__ == "__main__":
    sys.exit(main())
