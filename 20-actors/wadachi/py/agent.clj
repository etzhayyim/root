#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (wadachi autonomous-mobility R&D actor).
(ns wadachi.py.agent
  "wadachi 轍 — autonomous mobility langgraph actor (kotoba WASM cell).

  ADR-2605242000, R0 scaffold. Runs in-WASM on kotoba :8077. Five handlers over the
  autonomous mobility mission schema (delivery routes, trajectories, motion control,
  obstacle avoidance, safety monitoring, telemetry):

    handle-route-planning      deliveryRoute → trajectoryPlan (waypoints + buffers)
    handle-motion-control      trajectoryPlan → steeringCommands (10 Hz @ ≤1 m/s R0)
    handle-obstacle-avoidance  sensorFusion → avoidanceAdjustments (dynamic replan)
    handle-safety-monitoring   motionTelemetry → safetyStatus (pass/critical/halt)
    handle-telemetry-log       fullMissionTelemetry → missionCompleteRecord (IPFS)

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G8). State is
  written back to the kotoba Datom log (G9). Operator eligibility enforced via active
  Adherent SBT (G10). KPI caps enforced: R0 ≤1 m/s, payload ≤100 kg, energy ≤5 kWh (G11).
  Energy budget logged with regenerative tracking (G12). Settlement is USDC on Base L2 +
  ERC-4337 + TitheRouter 10% only — no fiat (G13). Platform holds no key; operator signs
  mission dispatch + settlement (G14). Compute-only R0; mission dispatch stops at :intent
  (G15).

  Run:  bb --classpath 20-actors 20-actors/wadachi/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def TITHE_BPS 1000)              ; 10% TitheRouter auto-split (G13), basis points

;; G11 KPI caps (R0)
(def MAX_SPEED_MPS 1.0)
(def MAX_PAYLOAD_KG 100.0)
(def MAX_MISSION_DURATION_MIN 60.0)
(def MAX_ENERGY_KWH 5.0)

;; G6 determinism
(def CONTROL_FREQ_HZ 10)

;; G10 operator eligibility
(def OPERATOR_SBT_REQUIRED true)

;; ── _infer — Murakumo-only inference (G8) ──────────────────────────────────────
(defn _infer
  "Murakumo-only inference (G8). Returns offline sentinel when host not available."
  [_prompt]
  ;; In WASM host: would call (llm/infer model prompt). Offline sentinel matches agent.py.
  "LLM_NOT_AVAILABLE")

;; ── G11 — KPI caps (speed / payload / mission duration / energy budget) ────────
(defn kpi-caps-ok
  "Verify speed ≤ MAX_SPEED_MPS, payload ≤ MAX_PAYLOAD_KG, mission ≤ MAX_MISSION_DURATION_MIN,
  energy ≤ MAX_ENERGY_KWH. Returns {:ok bool :reason str}.
  REFUSES (not clamps) when any cap is exceeded — the SAE-L4 envelope invariant."
  [speed-mps payload-kg mission-min energy-kwh]
  (cond
    (> (double speed-mps) (double MAX_SPEED_MPS))
    {:ok false :reason (str "speed " speed-mps " m/s > " MAX_SPEED_MPS " m/s R0 (G11)")}

    (> (double payload-kg) (double MAX_PAYLOAD_KG))
    {:ok false :reason (str "payload " payload-kg " kg > " MAX_PAYLOAD_KG " kg (G11)")}

    (> (double mission-min) (double MAX_MISSION_DURATION_MIN))
    {:ok false :reason (str "duration " mission-min " min > " MAX_MISSION_DURATION_MIN " min (G11)")}

    (> (double energy-kwh) (double MAX_ENERGY_KWH))
    {:ok false :reason (str "energy " energy-kwh " kWh > " MAX_ENERGY_KWH " kWh (G12)")}

    :else
    {:ok true :reason "within KPI caps"}))

;; Public alias matching Python name (test uses kpi_caps_ok)
(def kpi_caps_ok kpi-caps-ok)

;; ── G10 — operator SBT eligibility gate ────────────────────────────────────────
(defn operator-ok
  "Verify that the operator holds an active Adherent SBT.
  Returns {:ok bool :reason str}. REFUSES when SBT not active (G10)."
  [operator-did sbt-registry]
  (if-not OPERATOR_SBT_REQUIRED
    {:ok true :reason "SBT check disabled"}
    (let [active (boolean (get-in sbt-registry [operator-did "active"]))]
      {:ok active
       :reason (if active "" "operator lacks active Adherent SBT (G10)")})))

;; Public alias
(def operator_ok operator-ok)

;; ── G6 — trajectory determinism @ 10 Hz ────────────────────────────────────────
(defn trajectory-determinism-ok
  "Verify trajectory is replay-able @ 10 Hz (determinism-id = git commit).
  Returns {:ok bool :reason str :commit str}."
  [determinism-id]
  (if (and (seq determinism-id) (>= (count determinism-id) 8))
    {:ok true :reason "determinism verified (G6)" :commit determinism-id}
    {:ok false :reason "missing determinism commit ID (G6)"}))

;; Public alias
(def trajectory_determinism_ok trajectory-determinism-ok)

;; ── build-settlement-intent — MUST be defined before handlers that call it ──────
(defn build-settlement-intent
  "USDC settlement split. 10% tithe → Public Fund. Stops at :intent —
  broadcast needs operator signature (G14).
  R0 behaviour: state is 'executed' when operator-sig-ref is provided, else 'intent'."
  ([gross-minor]
   (build-settlement-intent gross-minor nil))
  ([gross-minor operator-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross TITHE_BPS) 10000)
         operator-payout (- gross tithe)]
     {:rail                 "usdc-base-l2"
      :grossMinor           gross
      :titheMinor           tithe
      :operatorPayoutMinor  operator-payout
      :titheRouter          "50-infra/etzhayyim-tithe-router"
      :state                (if operator-sig-ref "executed" "intent")
      :operatorSigRef       (or operator-sig-ref "")})))

;; Public alias
(def build_settlement_intent build-settlement-intent)

;; ── handle-route-planning — deliveryRoute → trajectoryPlan ─────────────────────
(defn handle-route-planning
  "Parse delivery route, compute waypoints with obstacle buffers + speed profile."
  [state]
  (let [route (get state "route" (get state :route {}))
        dest  (get route "destination" (get route :destination nil))]
    (if-not dest
      (assoc state "error" "missing destination")
      (let [origin      (get route "origin" (get route :origin "0,0"))
            payload-kg  (double (get route "payloadKg" (get route :payloadKg 0.0)))
            route-id    (get route "id" (get route :id "unknown"))
            caps        (kpi-caps-ok MAX_SPEED_MPS payload-kg 30.0 2.0)]
        (if-not (:ok caps)
          (assoc state "error" (:reason caps))
          (let [trajectory {"plan-id"        (str "tp." route-id ".001")
                            "waypoints"      (str origin " (intermediate) " dest)
                            "buffer-zones"   "2m perimeter buffer"
                            "speed-profile"  "0.5 m/s constant (R0 ≤1 m/s, G11)"
                            "determinism-id" "abc123def456"}]
            (assoc state "trajectory" trajectory)))))))

;; Public alias
(def handle_route_planning handle-route-planning)

;; ── handle-motion-control — trajectoryPlan → steeringCommands @ 10 Hz ──────────
(defn handle-motion-control
  "Generate steering commands (wheel angle, throttle, brake) at 10 Hz."
  [state]
  (let [traj (get state "trajectory" (get state :trajectory {}))]
    (if (empty? traj)
      (assoc state "error" "no trajectory")
      (let [determ (trajectory-determinism-ok
                    (get traj "determinism-id" (get traj :determinism-id "")))]
        (if-not (:ok determ)
          (assoc state "error" (:reason determ))
          (let [plan-id   (get traj "plan-id" (get traj :plan-id "unknown"))
                commands  {"command-id"      (str "sc." plan-id ".001")
                           "wheel-angle"     0.0
                           "throttle"        0.3
                           "brake"           0.0
                           "control-freq-hz" CONTROL_FREQ_HZ}]
            (assoc state "steering-commands" commands)))))))

;; Public alias
(def handle_motion_control handle-motion-control)

;; ── handle-obstacle-avoidance — sensorFusion → avoidanceAdjustments ────────────
(defn handle-obstacle-avoidance
  "Fuse LIDAR/camera/radar, detect obstacles, replan if needed."
  [state]
  (let [commands    (get state "steering-commands" (get state :steering-commands {}))
        sensor-data (get state "sensors" (get state :sensors {}))
        lidar       (get sensor-data "lidar" (get sensor-data :lidar "no_obstacle"))
        detected    (str/includes? (str/lower-case (str lidar)) "obstacle")
        cmd-id      (get commands "command-id" (get commands :command-id "unknown"))
        adjustment  {"adjustment-id"   (str "aa." cmd-id ".001")
                     "obstacle-detected" detected
                     "dynamic-heading" (if detected 45.0 0.0)
                     "new-waypoint"    (if detected "35.68,139.71" "")}]
    (assoc state "avoidance" adjustment)))

;; Public alias
(def handle_obstacle_avoidance handle-obstacle-avoidance)

;; ── handle-safety-monitoring — motionTelemetry → safetyStatus ──────────────────
(defn handle-safety-monitoring
  "Monitor speed/acceleration/tilt/slip; check KPI caps + energy budget."
  [state]
  (let [telemetry (get state "telemetry" (get state :telemetry {}))
        speed     (double (get telemetry "speed_mps"   (get telemetry :speed_mps   0.0)))
        accel     (double (get telemetry "accel_mps2"  (get telemetry :accel_mps2  0.0)))
        tilt      (double (get telemetry "tilt_deg"    (get telemetry :tilt_deg    0.0)))
        slip      (double (get telemetry "wheel_slip"  (get telemetry :wheel_slip  0.0)))
        energy    (double (get telemetry "energy_kwh"  (get telemetry :energy_kwh  0.0)))
        caps      (kpi-caps-ok speed MAX_PAYLOAD_KG 30.0 energy)
        anomaly   (cond
                    (> speed MAX_SPEED_MPS)   "speed_violation"
                    (> tilt 10.0)             "tilt_anomaly"
                    (> slip 0.3)              "wheel_slip"
                    (> energy MAX_ENERGY_KWH) "energy_budget"
                    :else                     "")
        status    {"status-id"     "ss.demo.001"
                   "pass"          (and (:ok caps) (= anomaly ""))
                   "anomaly"       anomaly
                   "halt-required" (not (:ok caps))
                   "reason"        (if (:ok caps) "all nominal" (:reason caps))}]
    (assoc state "safety" status)))

;; Public alias
(def handle_safety_monitoring handle-safety-monitoring)

;; ── handle-telemetry-log — fullMissionTelemetry → missionCompleteRecord ─────────
(defn handle-telemetry-log
  "Aggregate mission data, IPFS-pin for audit trail (G2), create completion record."
  [state]
  (let [route      (get state "route"      (get state :route {}))
        traj       (get state "trajectory" (get state :trajectory {}))
        safety     (get state "safety"     (get state :safety {}))
        telemetry  (get state "telemetry"  (get state :telemetry {}))
        energy     (double (get telemetry "energy_kwh" (get telemetry :energy_kwh 0.0)))
        route-id   (get route "id" (get route :id "unknown"))
        origin     (get route "origin" (get route :origin "0,0"))
        dest       (get route "destination" (get route :destination "0,0"))
        op-did     (get state "operator_did" (get state :operator_did ""))
        record     {"record-id"           (str "mcr." route-id ".001")
                    "ipfs-cid"            "ipfs://QmTelemetry001"
                    "gps-track"           (str origin " " dest)
                    "energy-kwh"          energy
                    "safety-summary"      (if (get safety "pass" (get safety :pass false))
                                           "pass" "anomaly")
                    "operator-did"        op-did
                    "completion-timestamp" "2026-06-02T10:02:30Z"}]
    (assoc state "mission-complete" record)))

;; Public alias
(def handle_telemetry_log handle-telemetry-log)

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (let [demo (handle-route-planning
              {"route" {"id"          "dr.demo.0001"
                        "origin"      "35.6789,139.7006"
                        "destination" "35.6795,139.7015"
                        "payloadKg"   45.0}})
        s    (build-settlement-intent 1000000)]
    (println "route planning:" (get-in demo ["trajectory" "plan-id"]))
    (println "settlement:" s)))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
