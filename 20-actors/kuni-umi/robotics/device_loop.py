"""device_loop — R1 device-in-the-loop: the REAL open-ot WASM cells close the loop.

ADR-2606091800 follow-up #3, executed per founder direction (Council gate
exercised as PR merge, ibuki ADR-2606101200 precedent). The "device" here is the
actual deployment artefact — the open-ot IEC 61499 Rust BFB compiled to
wasm32-unknown-unknown (the same artefact class WAMR runs on Giemon field
hardware) — executed under Wasmtime by `device-loop-host`
(60-apps/etzhayyim-project-open-ot/risk1/device-loop-host) and driven, tick by
tick, by the SAME MicrogridPlant scenarios the Python twin passes:

  plant (Python MicrogridPlant)  ←command─  DROOP_P_F.wasm (real device tier)
        └─ frequency ─→  ANTI_ISLANDING_ROCOF.wasm (real latched trip guard)
                          + Python secondary-PI trim (same gains as the twin)

Outputs a deterministic golden trace (golden/device_loop_trace.json) consumed by
test_device_loop.py, so the verification suite runs without cargo/wasmtime.
Regenerate (operator-run, offline — no hardware, no network, no live actuation):

    # 1. build the device artefacts + host (once)
    cd 60-apps/etzhayyim-project-open-ot/cells
    PATH="$HOME/.cargo/bin:$PATH" cargo build --release --no-default-features \
        --target wasm32-unknown-unknown -p droop-p-f -p anti-islanding-rocof
    cd ../risk1 && PATH="$HOME/.cargo/bin:$PATH" cargo build --release -p device-loop-host
    # 2. run the loop
    cd 20-actors/kuni-umi/robotics && python3 device_loop.py

R0 invariants unchanged: this is offline sim + dry-run evidence; live dispatch
stays Council/operator-gated; the host holds no key and signs nothing.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from dataclasses import asdict, dataclass

from commissioning import run_microgrid_acceptance
from control import PID, Droop, DroopPI
from plant import MicrogridPlant

_HERE = pathlib.Path(__file__).resolve().parent
_REPO = _HERE.parents[2]
_OPEN_OT = _REPO / "60-apps" / "etzhayyim-project-open-ot"
HOST_BIN = _OPEN_OT / "risk1" / "target" / "release" / "device-loop-host"
WASM_DIR = _OPEN_OT / "cells" / "target" / "wasm32-unknown-unknown" / "release"
GEN_DIR = _OPEN_OT / "orchestrator" / "src" / "open_ot_orchestrator" / "_generated"
GOLDEN = _HERE / "golden" / "device_loop_trace.json"

UKW = 1_000_000   # µkW per kW
UHZ = 1_000_000   # µHz per Hz
QUALITY_GOOD = 0
EVENT_REQ = 0


def _gen():
    """Import the generated pack/unpack modules (layouts are the ABI contract)."""
    if str(GEN_DIR) not in sys.path:
        sys.path.insert(0, str(GEN_DIR))
    import anti_islanding_rocof as air  # noqa: PLC0415
    import droop_p_f as dpf  # noqa: PLC0415
    return dpf, air


class DeviceCell:
    """One real BFB cell running in the device-loop-host (line protocol)."""

    def __init__(self, proc: subprocess.Popen, gen, out_event_width: int):
        self._p = proc
        self.gen = gen
        wasm = WASM_DIR / f"{gen.CELL_SYMBOL}.wasm"
        if not wasm.exists():
            raise FileNotFoundError(f"device artefact missing: {wasm} (build first — see module docstring)")
        self._rpc(f"LOAD {wasm} {gen.INIT_EXPORT} {gen.TICK_EXPORT} {out_event_width}")
        self.state = gen.ECC_STATES.index(gen.ECC_INITIAL)
        self.super_step = 0

    def _rpc(self, line: str) -> str:
        self._p.stdin.write(line + "\n")
        self._p.stdin.flush()
        reply = self._p.stdout.readline().strip()
        if not reply.startswith("OK"):
            raise RuntimeError(f"device-loop-host: {reply!r} for {line.split()[0]}")
        return reply

    def init(self, params) -> None:
        blob = self.gen.pack_params(params)
        self._rpc(f"INIT {blob.hex()} {self.gen.INTERNAL_SIZE}")

    def tick(self, data_in):
        blob = self.gen.pack_data_in(data_in)
        reply = self._rpc(
            f"TICK {EVENT_REQ} {self.state} {self.super_step} {self.gen.DATA_OUT_SIZE} {blob.hex()}"
        )
        fields = dict(kv.split("=", 1) for kv in reply.split()[1:])
        self.state = int(fields["state"])
        self.super_step += 1
        return self.gen.unpack_data_out(bytes.fromhex(fields["out"])), int(fields["event"])


def _spawn_host() -> subprocess.Popen:
    if not HOST_BIN.exists():
        raise FileNotFoundError(f"device-loop-host missing: {HOST_BIN} (build first — see module docstring)")
    return subprocess.Popen(
        [str(HOST_BIN)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )


@dataclass(frozen=True)
class DeviceAcceptance:
    """One device-in-the-loop scenario outcome (mirrors run_microgrid_acceptance)."""

    scenario: str
    load_step_kw: float
    final_freq_hz: float
    freq_restored: bool
    final_command_kw: float
    rocof_trip: bool                # REAL ANTI_ISLANDING_ROCOF latched verdict
    rocof_max_uhz_per_s: int        # as measured by the device cell
    droop_final_state: str          # device ECC state at the end
    twin_final_freq_hz: float       # Python twin on the identical scenario
    twin_max_cmd_delta_kw: float    # max per-step |device-loop − twin| command
    twin_verdict_match: bool        # device trip verdict == twin verdict
    ticks: int
    dry_run: bool                   # always True: evidence, not actuation
    server_held_key: bool           # always False


def run_device_scenario(
    load_step_kw: float,
    scenario: str,
    p_max_kw: float = 200.0,
    kp: float = 4.0,
    ki: float = 20.0,
    droop_permille: int = 40,       # 4 % — matches the twin's droop_r=0.04
    rocof_trip_hz_per_s: float = 2.0,
    rocof_window_samples: int = 10, # 100 ms @ dt=10ms — matches the twin's window
    steps: int = 8000,
    dt: float = 0.01,
) -> DeviceAcceptance:
    """Close the loop with the REAL cells; run the Python twin on the same scenario."""
    dpf, air = _gen()

    # ── device side ──────────────────────────────────────────────────
    droop_proc, guard_proc = _spawn_host(), _spawn_host()
    try:
        droop = DeviceCell(droop_proc, dpf, out_event_width=1)
        droop.init(dpf.Params(
            p_rated_micro_kw=int(p_max_kw * UKW),
            p_min_micro_kw=0,
            p_max_micro_kw=int(p_max_kw * UKW),
            droop_permille=droop_permille,
            dead_band_micro_hz=0,            # parity with the (deadband-free) twin
            cycle_period_ms=int(dt * 1000),
        ))
        guard = DeviceCell(guard_proc, air, out_event_width=2)
        guard.init(air.Params(
            rocof_threshold_micro_hz_per_s=int(rocof_trip_hz_per_s * UHZ),
            rocof_window_samples=rocof_window_samples,
            voltage_min_micro_v=200_000_000,   # wide band: voltage held nominal here
            voltage_max_micro_v=300_000_000,
            voltage_window_samples=10,
            freq_min_micro_hz=int(47.0 * UHZ),
            freq_max_micro_hz=int(53.0 * UHZ),
            freq_window_samples=10,
            cycle_period_ms=int(dt * 1000),
        ))

        p_base_kw = 100.0  # pre-step dispatch base (the twin's Droop p_base)
        grid = MicrogridPlant(p_load=100.0, f=50.0)
        grid.set_load(load_step_kw)
        pi = PID(kp=kp, ki=ki, out_min=-p_max_kw, out_max=p_max_kw)
        pi.reset()

        # twin runs the identical scenario step-for-step for parity. The unit
        # conventions differ — DROOP_P_F is per-unit (Δp = Δf/(f_nom·R)·P_rated),
        # the Python Droop is absolute (Δp = Δf/R) — so the equivalent twin
        # slope is derived FROM the device params: R_twin = f_nom·R_dev/P_rated.
        droop_r_twin = 50.0 * (droop_permille / 1000.0) / p_max_kw
        twin_grid = MicrogridPlant(p_load=100.0, f=50.0)
        twin_grid.set_load(load_step_kw)
        twin = DroopPI(
            Droop(nominal=50.0, droop_r=droop_r_twin, p_base=p_base_kw,
                  p_min=0.0, p_max=p_max_kw),
            PID(kp=kp, ki=ki, out_min=-p_max_kw, out_max=p_max_kw),
        )
        twin.reset()

        tripped = False
        rocof_max = 0
        max_delta = 0.0
        cmd_kw = 0.0
        for _ in range(steps):
            f = grid.measure()
            # current_p = the FIXED dispatch base: DROOP_P_F is incremental
            # (p_setpoint = clamp(current_p + Δ(f))), so feeding the base makes
            # it the absolute droop-around-dispatch the twin computes. Feeding
            # the last total command back would turn the cell into an
            # integrator (observed: loop diverges from the twin by >180 kW).
            dout, _ev = droop.tick(dpf.DataIn(
                grid_freq=int(f * UHZ),
                freq_nominal=int(50.0 * UHZ),
                current_p=int(p_base_kw * UKW),
                freq_quality=QUALITY_GOOD,
                enable=True,
            ))
            gout, _gev = guard.tick(air.DataIn(
                grid_freq=int(f * UHZ),
                freq_nominal=int(50.0 * UHZ),
                grid_voltage=250_000_000,
                voltage_nominal=250_000_000,
                freq_quality=QUALITY_GOOD,
                voltage_quality=QUALITY_GOOD,
                enable=True,
            ))
            tripped = tripped or bool(gout.trip)
            rocof_max = max(rocof_max, abs(int(gout.rocof_micro_hz_per_s)))
            # real droop setpoint (kW) + the same secondary-PI trim the twin uses
            cmd_kw = dout.p_setpoint / UKW + pi.step(50.0 - f, dt)
            cmd_kw = min(p_max_kw, max(0.0, cmd_kw))
            grid.step(cmd_kw, dt)

            twin_cmd = twin.step(50.0 - twin_grid.measure(), dt)
            twin_grid.step(twin_cmd, dt)
            max_delta = max(max_delta, abs(cmd_kw - twin_cmd))
    finally:
        for proc in (droop_proc, guard_proc):
            try:
                proc.stdin.write("QUIT\n")
                proc.stdin.flush()
            except Exception:
                pass
            proc.terminate()

    final_f = grid.measure()
    twin_final = twin_grid.measure()
    # twin verdict: the commissioning harness's own windowed-ROCOF judgement on
    # the identical scenario (the R0 acceptance the device run must agree with).
    twin_trip = bool(run_microgrid_acceptance(load_step_kw)["rocof_tripped"])
    return DeviceAcceptance(
        scenario=scenario,
        load_step_kw=load_step_kw,
        final_freq_hz=round(final_f, 4),
        freq_restored=abs(final_f - 50.0) < 2e-2,
        final_command_kw=round(cmd_kw, 3),
        rocof_trip=tripped,
        rocof_max_uhz_per_s=rocof_max,
        droop_final_state=_gen()[0].ECC_STATES[droop.state],
        twin_final_freq_hz=round(twin_final, 4),
        twin_max_cmd_delta_kw=round(max_delta, 4),
        twin_verdict_match=tripped == twin_trip,
        ticks=steps,
        dry_run=True,
        server_held_key=False,
    )


def main() -> None:
    scenarios = [
        ("normal-load-step", 140.0),     # twin-passing acceptance: restore, no trip
        ("load-shed", 60.0),             # opposite direction
        ("islanding-scale-step", 190.0), # the guard MUST latch a trip
    ]
    results = [run_device_scenario(kw, name) for name, kw in scenarios]
    trace = {
        "generator": "device_loop.py (device-loop-host + real open-ot BFB wasm)",
        "device_cells": ["DROOP_P_F", "ANTI_ISLANDING_ROCOF"],
        "artefact_target": "wasm32-unknown-unknown (cdylib, WAMR/Cortex-M7 artefact class)",
        "results": [asdict(r) for r in results],
    }
    GOLDEN.parent.mkdir(exist_ok=True)
    GOLDEN.write_text(json.dumps(trace, indent=2) + "\n")
    for r in results:
        print(f"{r.scenario}: f={r.final_freq_hz} restored={r.freq_restored} "
              f"trip={r.rocof_trip} Δtwin={r.twin_max_cmd_delta_kw} kW state={r.droop_final_state}")
    print(f"wrote {GOLDEN}")


if __name__ == "__main__":
    main()
