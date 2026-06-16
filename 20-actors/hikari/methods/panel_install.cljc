;; ported from 20-actors/hikari/methods/panel_install.py (real port replacing the
;; unit_refactor stage-0 "TODO: port-failed" stub). NS fixed:
;; root.hikari.methods.panel-install -> hikari.methods.panel-install (20-actors is the
;; bb source root). The only require is the SIBLING REAL substrate port
;; (hikari.methods.substrate.cljc) — _substrate.py's faithful port, not a stub.
(ns hikari.methods.panel-install
  "panel_install.py — hikari solar_pv_install robot motion loop (R0 :representative).

  1:1 Clojure port of methods/panel_install.py. Plans an Otete-arm motion that places
  a PV panel at a target pose and refuses to dispatch unless every structural gate
  holds: N1 civilian-use, G15/G7 no-server-key, G8 witness quorum >=2, and the motion
  safety envelope. PanelInstallPlan is a string-keyed map; pure (no host I/O)."
  (:require [hikari.methods.substrate :as sub]))

(def PERMITTED-USES #{"install" "service" "inspect" "clean"})

;; Otete arm :representative geometry — a 2-link planar reach model (metres).
(def OTETE-ARM (sub/planar-arm [1.2 1.0]))

(defn plan-panel-install
  "Plan an install motion. Raises before planning if a structural gate fails.
  Gate order is fail-fast: civilian use, then no-server-key, then witness quorum.
  A witness-quorum miss does NOT raise (it is a Council-escalation Datom), so the
  plan is returned with witness-ok=false for the audit trail. Returns a string-keyed
  PanelInstallPlan map."
  [target-xy member-sig witness-sigs
   & {:keys [q-start use human-present steps dt server-sig]
      :or {q-start [0.0 0.0] use "install" human-present false steps 60 dt 0.1 server-sig ""}}]
  (sub/assert-civilian use PERMITTED-USES)              ; N1
  (sub/require-member-signature member-sig server-sig)  ; G15/G7
  (let [quorum (sub/witness-quorum-ok witness-sigs)     ; G8 (record, do not raise)
        [x y] target-xy
        reachable (sub/arm-reachable OTETE-ARM x y)
        joints-goal (when reachable (sub/arm-ik2 OTETE-ARM x y true))
        env (sub/safety-envelope {:max-joint-speed 1.0 :human-proximity-speed 0.25
                                  :max-reach (:max-reach OTETE-ARM)})
        traj (if (some? joints-goal) (sub/joint-trajectory q-start joints-goal steps) [])
        check (when (some? joints-goal) (sub/check-trajectory env traj dt human-present))
        envelope-ok (if check (get check "ok") false)
        violations (if check (get check "violations") [])]
    {"use" use
     "target_xy" target-xy
     "reachable" reachable
     "joints_goal" joints-goal
     "trajectory_steps" (count traj)
     "envelope_ok" envelope-ok
     "envelope_violations" violations
     "human_present" human-present
     "member_sig" member-sig
     "witness_ok" (get quorum "ok")
     "server_held_key" false   ; G15: structural invariant
     "dry_run" true}))         ; G10: R0 offline only

(defn to-datoms
  "Project an install plan into kotoba EAVT-shaped datoms (G6)."
  ([plan job-id] (to-datoms plan job-id "otete-01"))
  ([plan job-id robot-id]
   {":install/id" job-id
    ":install/robot" robot-id
    ":install/use" (get plan "use")
    ":install/target-x" (first (get plan "target_xy"))
    ":install/target-y" (second (get plan "target_xy"))
    ":install/reachable" (get plan "reachable")
    ":install/trajectory-steps" (get plan "trajectory_steps")
    ":install/envelope-ok" (get plan "envelope_ok")
    ":install/human-present" (get plan "human_present")
    ":install/member-sig" (get plan "member_sig")
    ":install/witness-ok" (get plan "witness_ok")
    ":install/server-held-key" (get plan "server_held_key") ; G15: always false
    ":install/dry-run" (get plan "dry_run")}))              ; G10
