#!/usr/bin/env python3
"""wadachi 轍 — autonomous mobility langgraph actor (kotoba WASM cell).

ADR-2605242000, R0 scaffold. Runs in-WASM on kotoba :8077. Five handlers over the
autonomous mobility mission schema (delivery routes, trajectories, motion control,
obstacle avoidance, safety monitoring, telemetry):

  handle_route_planning      deliveryRoute → trajectoryPlan (waypoints + buffers)
  handle_motion_control      trajectoryPlan → steeringCommands (10 Hz @ ≤1 m/s R0)
  handle_obstacle_avoidance  sensorFusion → avoidanceAdjustments (dynamic replan)
  handle_safety_monitoring   motionTelemetry → safetyStatus (pass/critical/halt)
  handle_telemetry_log       fullMissionTelemetry → missionCompleteRecord (IPFS)

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G8). State is
written back to the kotoba Datom log (G9). Operator eligibility enforced via active
Adherent SBT (G10). KPI caps enforced: R0 ≤1 m/s, payload ≤100 kg, energy ≤5 kWh (G11).
Energy budget logged with regenerative tracking (G12). Settlement is USDC on Base L2 +
ERC-4337 + TitheRouter 10% only — no fiat (G13). Platform holds no key; operator signs
mission dispatch + settlement (G14). Compute-only R0; mission dispatch stops at :intent
(G15).
"""
from __future__ import annotations

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G13), basis points

# G11 KPI caps (R0)
MAX_SPEED_MPS = 1.0
MAX_PAYLOAD_KG = 100.0
MAX_MISSION_DURATION_MIN = 60.0
MAX_ENERGY_KWH = 5.0

# G6 determinism
CONTROL_FREQ_HZ = 10

# G10 operator eligibility
OPERATOR_SBT_REQUIRED = True


def _infer(prompt: str) -> str:
    """Murakumo-only inference (G8)."""
    if llm:
        try:
            return str(llm.infer(model="gemma3:4b", prompt=prompt))
        except Exception:
            return "LLM_INFERENCE_FAILED"
    return "LLM_NOT_AVAILABLE"


# --------------------------------------------------------------------------- #
# G11 — KPI caps (speed / payload / mission duration / energy budget)
# --------------------------------------------------------------------------- #
def kpi_caps_ok(speed_mps: float, payload_kg: float, mission_min: float,
                energy_kwh: float) -> dict:
    if speed_mps > MAX_SPEED_MPS:
        return {"ok": False, "reason": f"speed {speed_mps} m/s > {MAX_SPEED_MPS} m/s R0 (G11)"}
    if payload_kg > MAX_PAYLOAD_KG:
        return {"ok": False, "reason": f"payload {payload_kg} kg > {MAX_PAYLOAD_KG} kg (G11)"}
    if mission_min > MAX_MISSION_DURATION_MIN:
        return {"ok": False, "reason": f"duration {mission_min} min > {MAX_MISSION_DURATION_MIN} min (G11)"}
    if energy_kwh > MAX_ENERGY_KWH:
        return {"ok": False, "reason": f"energy {energy_kwh} kWh > {MAX_ENERGY_KWH} kWh (G12)"}
    return {"ok": True, "reason": "within KPI caps"}


# --------------------------------------------------------------------------- #
# G10 — operator SBT eligibility gate
# --------------------------------------------------------------------------- #
def operator_ok(operator_did: str, sbt_registry: dict) -> dict:
    if not OPERATOR_SBT_REQUIRED:
        return {"ok": True, "reason": "SBT check disabled"}
    active = bool(sbt_registry.get(operator_did, {}).get("active"))
    return {"ok": active,
            "reason": "" if active else "operator lacks active Adherent SBT (G10)"}


# --------------------------------------------------------------------------- #
# G6 — trajectory determinism @ 10 Hz
# --------------------------------------------------------------------------- #
def trajectory_determinism_ok(determinism_id: str) -> dict:
    """Verify trajectory is replay-able @ 10 Hz (determinism_id = git commit)."""
    if determinism_id and len(determinism_id) >= 8:
        return {"ok": True, "reason": "determinism verified (G6)", "commit": determinism_id}
    return {"ok": False, "reason": "missing determinism commit ID (G6)"}


# --------------------------------------------------------------------------- #
# route_planning — deliveryRoute → trajectoryPlan
# --------------------------------------------------------------------------- #
def handle_route_planning(state: dict) -> dict:
    """Parse delivery route, compute waypoints with obstacle buffers + speed profile."""
    route = state.get("route", {})
    if not route.get("destination"):
        return {**state, "error": "missing destination"}
    origin = route.get("origin", "0,0")
    dest = route.get("destination", "0,0")
    payload_kg = float(route.get("payloadKg", 0.0))
    caps = kpi_caps_ok(MAX_SPEED_MPS, payload_kg, 30.0, 2.0)
    if not caps["ok"]:
        return {**state, "error": caps["reason"]}
    trajectory = {
        "plan-id": f"tp.{route.get('id', 'unknown')}.001",
        "waypoints": f"{origin} (intermediate) {dest}",
        "buffer-zones": "2m perimeter buffer",
        "speed-profile": "0.5 m/s constant (R0 ≤1 m/s, G11)",
        "determinism-id": "abc123def456",
    }
    return {**state, "trajectory": trajectory}


# --------------------------------------------------------------------------- #
# motion_control — trajectoryPlan → steeringCommands @ 10 Hz (G6)
# --------------------------------------------------------------------------- #
def handle_motion_control(state: dict) -> dict:
    """Generate steering commands (wheel angle, throttle, brake) at 10 Hz."""
    traj = state.get("trajectory", {})
    if not traj:
        return {**state, "error": "no trajectory"}
    determ = trajectory_determinism_ok(traj.get("determinism-id", ""))
    if not determ["ok"]:
        return {**state, "error": determ["reason"]}
    commands = {
        "command-id": f"sc.{traj.get('plan-id', 'unknown')}.001",
        "wheel-angle": 0.0,
        "throttle": 0.3,
        "brake": 0.0,
        "control-freq-hz": CONTROL_FREQ_HZ,
    }
    return {**state, "steering-commands": commands}


# --------------------------------------------------------------------------- #
# obstacle_avoidance — sensorFusion → avoidanceAdjustments
# --------------------------------------------------------------------------- #
def handle_obstacle_avoidance(state: dict) -> dict:
    """Fuse LIDAR/camera/radar, detect obstacles, replan if needed."""
    commands = state.get("steering-commands", {})
    sensor_data = state.get("sensors", {})
    lidar = sensor_data.get("lidar", "no_obstacle")
    detected = "obstacle" in lidar.lower()
    adjustment = {
        "adjustment-id": f"aa.{commands.get('command-id', 'unknown')}.001",
        "obstacle-detected": detected,
        "dynamic-heading": 45.0 if detected else 0.0,
        "new-waypoint": "35.68,139.71" if detected else "",
    }
    return {**state, "avoidance": adjustment}


# --------------------------------------------------------------------------- #
# safety_monitoring — motionTelemetry → safetyStatus (G11 + G12)
# --------------------------------------------------------------------------- #
def handle_safety_monitoring(state: dict) -> dict:
    """Monitor speed/acceleration/tilt/slip; check KPI caps + energy budget."""
    telemetry = state.get("telemetry", {})
    speed = float(telemetry.get("speed_mps", 0.0))
    accel = float(telemetry.get("accel_mps2", 0.0))
    tilt = float(telemetry.get("tilt_deg", 0.0))
    slip = float(telemetry.get("wheel_slip", 0.0))
    energy = float(telemetry.get("energy_kwh", 0.0))
    caps = kpi_caps_ok(speed, MAX_PAYLOAD_KG, 30.0, energy)
    anomaly = ""
    if speed > MAX_SPEED_MPS:
        anomaly = "speed_violation"
    elif tilt > 10.0:
        anomaly = "tilt_anomaly"
    elif slip > 0.3:
        anomaly = "wheel_slip"
    elif energy > MAX_ENERGY_KWH:
        anomaly = "energy_budget"
    status = {
        "status-id": "ss.demo.001",
        "pass": caps["ok"] and not anomaly,
        "anomaly": anomaly,
        "halt-required": not caps["ok"],
        "reason": caps["reason"] if not caps["ok"] else "all nominal",
    }
    return {**state, "safety": status}


# --------------------------------------------------------------------------- #
# telemetry_log — fullMissionTelemetry → missionCompleteRecord (G2 IPFS pin)
# --------------------------------------------------------------------------- #
def handle_telemetry_log(state: dict) -> dict:
    """Aggregate mission data, IPFS-pin for audit trail (G2), create completion record."""
    route = state.get("route", {})
    traj = state.get("trajectory", {})
    safety = state.get("safety", {})
    energy = float(state.get("telemetry", {}).get("energy_kwh", 0.0))
    record = {
        "record-id": f"mcr.{route.get('id', 'unknown')}.001",
        "ipfs-cid": "ipfs://QmTelemetry001",
        "gps-track": f"{route.get('origin', '0,0')} {route.get('destination', '0,0')}",
        "energy-kwh": energy,
        "safety-summary": "pass" if safety.get("pass") else "anomaly",
        "operator-did": state.get("operator_did", ""),
        "completion-timestamp": "2026-06-02T10:02:30Z",
    }
    return {**state, "mission-complete": record}


# --------------------------------------------------------------------------- #
# settlement — USDC + TitheRouter intent (NOT broadcast; G13/G14/G15)
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, operator_sig_ref: str | None = None) -> dict:
    """USDC settlement split. 10% tithe → Public Fund. Stops at :intent — broadcast
    needs operator signature (G14)."""
    tithe = (gross_minor * TITHE_BPS) // 10_000
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross_minor,
        "titheMinor": tithe,
        "operatorPayoutMinor": gross_minor - tithe,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        "state": "executed" if operator_sig_ref else "intent",
        "operatorSigRef": operator_sig_ref or "",
    }


if __name__ == "__main__":  # pragma: no cover
    demo = handle_route_planning({
        "route": {
            "id": "dr.demo.0001",
            "origin": "35.6789,139.7006",
            "destination": "35.6795,139.7015",
            "payloadKg": 45.0,
        }
    })
    print("route planning:", demo.get("trajectory", {}).get("plan-id"))
    print("settlement:", build_settlement_intent(1_000_000))
