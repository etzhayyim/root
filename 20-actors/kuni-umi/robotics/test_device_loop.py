"""Tests for the R1 device-in-the-loop evidence (real open-ot WASM cells).

Two layers:
  * Golden verification (always runs, stdlib-only): the committed
    golden/device_loop_trace.json must show the REAL device tier passing the
    same acceptance the Python twin passes — frequency restored on normal
    steps, the real ANTI_ISLANDING_ROCOF latching on the islanding-scale step,
    per-step command parity with the twin at integer-quantisation level, and
    the dry-run/no-server-key invariants on every record.
  * Live end-to-end (runs when the built host + wasm artefacts exist on this
    machine; skipped otherwise): re-runs one scenario through Wasmtime and
    cross-checks it against the committed golden.

Run:
    cd 20-actors/kuni-umi/robotics
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_device_loop.py
"""

from __future__ import annotations

import json
import pathlib

import pytest

from device_loop import GOLDEN, HOST_BIN, WASM_DIR

# Parity bound: DROOP_P_F quantises to integer µkW, so the device and the
# (float) twin may differ by up to ~1e-3 kW per step once trajectory-coupled.
PARITY_KW = 1e-2


@pytest.fixture(scope="module")
def trace() -> dict:
    assert GOLDEN.exists(), (
        f"golden device trace missing at {GOLDEN}; regenerate per the "
        "device_loop.py docstring (build cells + host, then run device_loop.py)"
    )
    return json.loads(GOLDEN.read_text())


def _by_scenario(trace: dict) -> dict:
    return {r["scenario"]: r for r in trace["results"]}


def test_trace_covers_the_three_acceptance_scenarios(trace):
    s = _by_scenario(trace)
    assert {"normal-load-step", "load-shed", "islanding-scale-step"} <= set(s)
    assert trace["device_cells"] == ["DROOP_P_F", "ANTI_ISLANDING_ROCOF"]
    assert "wasm32-unknown-unknown" in trace["artefact_target"]


def test_device_restores_frequency_on_normal_step(trace):
    r = _by_scenario(trace)["normal-load-step"]
    assert r["freq_restored"] is True
    assert abs(r["final_freq_hz"] - 50.0) < 2e-2
    assert r["rocof_trip"] is False
    assert r["droop_final_state"] == "Responding"


def test_device_restores_frequency_on_load_shed(trace):
    r = _by_scenario(trace)["load-shed"]
    assert r["freq_restored"] is True
    assert r["rocof_trip"] is False


def test_real_guard_latches_on_islanding_scale_step(trace):
    r = _by_scenario(trace)["islanding-scale-step"]
    assert r["rocof_trip"] is True, "the REAL ANTI_ISLANDING_ROCOF must latch"
    assert r["rocof_max_uhz_per_s"] > 2_000_000  # above the 2 Hz/s threshold


def test_device_verdicts_match_python_twin(trace):
    for r in trace["results"]:
        assert r["twin_verdict_match"] is True, (
            f"{r['scenario']}: device trip verdict diverged from the twin"
        )


def test_device_command_parity_with_twin_at_quantisation_level(trace):
    for r in trace["results"]:
        assert r["twin_max_cmd_delta_kw"] <= PARITY_KW, (
            f"{r['scenario']}: max per-step command delta "
            f"{r['twin_max_cmd_delta_kw']} kW exceeds {PARITY_KW} kW"
        )
        assert abs(r["final_freq_hz"] - r["twin_final_freq_hz"]) < 1e-3


def test_every_record_is_dry_run_and_keyless(trace):
    for r in trace["results"]:
        assert r["dry_run"] is True
        assert r["server_held_key"] is False


# ─── live end-to-end (device tier actually executed on this machine) ──

_LIVE_READY = HOST_BIN.exists() and (WASM_DIR / "droop_p_f.wasm").exists() and (
    WASM_DIR / "anti_islanding_rocof.wasm"
).exists()


@pytest.mark.skipif(not _LIVE_READY, reason="device-loop-host / wasm artefacts not built")
def test_live_device_run_matches_committed_golden(trace):
    from device_loop import run_device_scenario

    live = run_device_scenario(140.0, "normal-load-step")
    golden = _by_scenario(trace)["normal-load-step"]
    assert live.freq_restored is True
    assert live.rocof_trip is False
    assert live.final_freq_hz == pytest.approx(golden["final_freq_hz"], abs=1e-6)
    assert live.twin_max_cmd_delta_kw == pytest.approx(
        golden["twin_max_cmd_delta_kw"], abs=1e-6
    )


@pytest.mark.skipif(not _LIVE_READY, reason="device-loop-host / wasm artefacts not built")
def test_live_guard_trips_deterministically():
    from device_loop import run_device_scenario

    live = run_device_scenario(190.0, "islanding-scale-step")
    assert live.rocof_trip is True
    assert live.twin_verdict_match is True
