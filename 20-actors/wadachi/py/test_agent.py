#!/usr/bin/env python3
"""wadachi 轍 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605242000. Exercises the autonomous mobility constitutional gates: KPI caps (G11),
operator SBT eligibility (G10), safety monitoring, USDC + tithe settlement (G13/G14),
and trajectory determinism (G6).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_kpi_speed_cap() -> bool:
    return _check("speed over 1.0 m/s rejected (G11)",
                  agent.kpi_caps_ok(1.5, 50.0, 30.0, 2.0)["ok"] is False)


def test_kpi_payload_cap() -> bool:
    return _check("payload over 100 kg rejected (G11)",
                  agent.kpi_caps_ok(0.5, 150.0, 30.0, 2.0)["ok"] is False)


def test_kpi_duration_cap() -> bool:
    return _check("mission > 60 min rejected (G11)",
                  agent.kpi_caps_ok(0.5, 50.0, 90.0, 2.0)["ok"] is False)


def test_kpi_energy_cap() -> bool:
    return _check("energy > 5 kWh rejected (G12)",
                  agent.kpi_caps_ok(0.5, 50.0, 30.0, 6.0)["ok"] is False)


def test_kpi_within() -> bool:
    return _check("within KPI caps accepted (G11/G12)",
                  agent.kpi_caps_ok(0.5, 50.0, 30.0, 2.0)["ok"] is True)


def test_operator_lacks_sbt() -> bool:
    return _check("operator without active SBT rejected (G10)",
                  agent.operator_ok("did:unknown", {})["ok"] is False)


def test_operator_has_sbt() -> bool:
    sbt = {"did:web:op.example": {"active": True}}
    return _check("operator with active SBT accepted (G10)",
                  agent.operator_ok("did:web:op.example", sbt)["ok"] is True)


def test_trajectory_determinism_ok() -> bool:
    return _check("determinism commit verified (G6)",
                  agent.trajectory_determinism_ok("abc123def456")["ok"] is True)


def test_trajectory_determinism_missing() -> bool:
    return _check("missing determinism commit rejected (G6)",
                  agent.trajectory_determinism_ok("")["ok"] is False)


def test_route_planning_missing_dest() -> bool:
    out = agent.handle_route_planning({"route": {}})
    return _check("route planning rejects missing destination",
                  out.get("error") is not None)


def test_route_planning_ok() -> bool:
    out = agent.handle_route_planning({
        "route": {
            "id": "dr.0001",
            "origin": "35.6789,139.7006",
            "destination": "35.6795,139.7015",
            "payloadKg": 45.0,
        }
    })
    return _check("route planning succeeds with valid input",
                  out.get("trajectory", {}).get("plan-id") is not None)


def test_motion_control_no_trajectory() -> bool:
    out = agent.handle_motion_control({"trajectory": {}})
    return _check("motion control rejects missing trajectory",
                  out.get("error") is not None)


def test_obstacle_avoidance_no_obstacle() -> bool:
    out = agent.handle_obstacle_avoidance({
        "steering-commands": {"command-id": "sc.001"},
        "sensors": {"lidar": "clear"}
    })
    return _check("obstacle avoidance detects clear (no obstacle)",
                  out.get("avoidance", {}).get("obstacle-detected") is False)


def test_obstacle_avoidance_detected() -> bool:
    out = agent.handle_obstacle_avoidance({
        "steering-commands": {"command-id": "sc.001"},
        "sensors": {"lidar": "obstacle at 5m"}
    })
    return _check("obstacle avoidance detects obstacle",
                  out.get("avoidance", {}).get("obstacle-detected") is True)


def test_safety_monitoring_speed_violation() -> bool:
    out = agent.handle_safety_monitoring({
        "telemetry": {
            "speed_mps": 1.5,
            "accel_mps2": 0.5,
            "tilt_deg": 2.0,
            "wheel_slip": 0.1,
            "energy_kwh": 2.0,
        }
    })
    return _check("safety monitoring catches speed violation (G11)",
                  out.get("safety", {}).get("anomaly") == "speed_violation")


def test_safety_monitoring_energy_violation() -> bool:
    out = agent.handle_safety_monitoring({
        "telemetry": {
            "speed_mps": 0.5,
            "accel_mps2": 0.5,
            "tilt_deg": 2.0,
            "wheel_slip": 0.1,
            "energy_kwh": 6.5,
        }
    })
    return _check("safety monitoring catches energy budget violation (G12)",
                  out.get("safety", {}).get("anomaly") == "energy_budget")


def test_safety_monitoring_pass() -> bool:
    out = agent.handle_safety_monitoring({
        "telemetry": {
            "speed_mps": 0.5,
            "accel_mps2": 0.5,
            "tilt_deg": 2.0,
            "wheel_slip": 0.1,
            "energy_kwh": 2.0,
        }
    })
    return _check("safety monitoring passes nominal telemetry",
                  out.get("safety", {}).get("pass") is True)


def test_telemetry_log_complete() -> bool:
    out = agent.handle_telemetry_log({
        "route": {
            "id": "dr.0001",
            "origin": "35.6789,139.7006",
            "destination": "35.6795,139.7015",
        },
        "trajectory": {"id": "tp.0001"},
        "safety": {"pass": True},
        "telemetry": {"energy_kwh": 1.5},
        "operator_did": "did:web:op.example",
    })
    return _check("telemetry log creates mission complete record",
                  out.get("mission-complete", {}).get("record-id") is not None)


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(10_000_000)
    return _check("10% tithe + stops at intent (G13/G14)",
                  s["titheMinor"] == 1_000_000 and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(1_000_000, operator_sig_ref="0xsig")
    return _check("settlement executes only with operator signature (G14)",
                  s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"wadachi agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
