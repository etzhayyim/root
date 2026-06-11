"""Kusawake (草分け) MuJoCo dev preview — interactive viewer.

DEV PREVIEW ONLY. NOT religious-corp R1. NOT under 70-tools/e7m-sim/.
Throwaway sandbox per ADR-2605252615 R0-vs-R1 gap (R0 = paper, R1 = real sim
gated on Council ratify 2026-06-19 + ≥1 GPU-hr-eq/day Murakumo budget +
G5 ≥0.75 vs Isaac Sim trial reference).

Usage (mac, requires native window):
    mjpython view.py            # open viewer, programmatic control
    mjpython view.py --manual   # open viewer, manual ctrl via UI sliders

The script demonstrates that the OSS stack (MuJoCo MJX-compatible MJCF +
viewer) actually renders a 4WD/4WS wheeled platform in approximately the
Kusawake mech envelope before any religious-corp R1 work lands.
"""
from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

MODEL_PATH = Path(__file__).parent / "kusawake.xml"


def crab_steer_program(t: float) -> tuple[float, float, float, float, float]:
    """A simple time-varying drive pattern showing 4WS modes.

    Phases (each 5 s):
      0-5  s: forward Ackermann (front+rear steer in opposite direction)
      5-10 s: crab (all 4 wheels steer same direction, lateral motion)
      10-15 s: pivot spin (FL/RR vs FR/RL opposite)
      15-20 s: forward straight
    Cycle repeats.

    Returns: (steer_fl, steer_fr, steer_rl, steer_rr, drive_speed)
    """
    cycle = t % 20.0
    drive = 3.5  # rad/s = ~0.7 m/s @ r=0.2 m, well under 6 km/h cap

    if cycle < 5:  # Ackermann turn
        s = 0.35 * math.sin(cycle * math.pi / 5)
        return (s, s, -s, -s, drive)
    elif cycle < 10:  # Crab
        s = 0.30
        return (s, s, s, s, drive * 0.6)
    elif cycle < 15:  # Pivot spin
        s = 0.45
        return (s, -s, -s, s, drive * 0.5)
    else:  # Straight forward
        return (0.0, 0.0, 0.0, 0.0, drive)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", action="store_true", help="No programmatic control; use UI sliders.")
    args = parser.parse_args()

    print(f"Loading model: {MODEL_PATH}")
    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)
    print(f"  nq={model.nq}, nv={model.nv}, nu={model.nu}, nbody={model.nbody}")
    print("  actuators:", [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(model.nu)])

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.distance = 6.0
        viewer.cam.elevation = -25
        viewer.cam.azimuth = 135

        start = time.time()
        last_print = 0.0

        while viewer.is_running():
            t_sim_start = time.time()
            elapsed = t_sim_start - start

            if not args.manual:
                sfl, sfr, srl, srr, drv = crab_steer_program(elapsed)
                data.ctrl[0] = sfl
                data.ctrl[1] = sfr
                data.ctrl[2] = srl
                data.ctrl[3] = srr
                data.ctrl[4:8] = drv  # all 4 wheels same speed

            mujoco.mj_step(model, data)
            viewer.sync()

            # ~5 Hz status print
            if elapsed - last_print > 1.0:
                xy = data.body("chassis").xpos[:2]
                phase = int(elapsed % 20.0 // 5)
                names = ["Ackermann", "Crab", "Pivot", "Straight"]
                print(f"t={elapsed:5.1f}s  phase={names[phase]:9s}  chassis=({xy[0]:+.2f},{xy[1]:+.2f}) m")
                last_print = elapsed

            # Real-time-ish: timestep = 2 ms → sleep to avoid runaway
            sleep_dt = model.opt.timestep - (time.time() - t_sim_start)
            if sleep_dt > 0:
                time.sleep(sleep_dt)


if __name__ == "__main__":
    main()
