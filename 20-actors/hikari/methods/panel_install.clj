;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hikari/methods/panel_install.py (unit_refactor stage 0)
;; panel_install — hikari solar_pv_install robot motion loop (R0 :representative).
(ns root.hikari.methods.panel-install
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare permitted-uses panel-install-plan plan-panel-install to-datoms)

(def PERMITTED_USES (set ["install" "service" "inspect" "clean"]))

(defn otete-arm []
  (let [planar-arm (fn [link-lengths]
                       {:link-lengths link-lengths})]
    (planar-arm [1.2 1.0])))

(def OTETE_ARM (otete-arm))

;; TODO: port-failed unit PanelInstallPlan (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmplgygf8vt/scratch.clj:2:1: er)
;; class PanelInstallPlan:
;;     """A dry-run panel-install motion plan (R0). Never an actuation command."""
;; 
;;     use: str
;;     target_xy: tuple[float, float]
;;     reachable: bool
;;     joints_goal: tuple[float, float] | None
;;     trajectory_steps: int
;;     envelope_ok: bool
;;     envelope_violations: list[str]
;;     human_present: bool
;;     member_sig: str
;;     witness_ok: bool
;;     server_held_key: bool
;;     dry_run: bool
(defn panel-install-plan [& _]
  (throw (ex-info "TODO: port-failed" {:from "PanelInstallPlan"})))

;; TODO: port-failed unit plan_panel_install (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpdsq274jc/scratch.clj:29:7: e)
;; def plan_panel_install(
;;     target_xy: tuple[float, float],
;;     member_sig: str,
;;     witness_sigs: list[str],
;;     q_start: tuple[float, float] = (0.0, 0.0),
;;     use: str = "install",
;;     human_present: bool = False,
;;     steps: int = 60,
;;     dt: float = 0.1,
;;     server_sig: str = "",
;; ) -> PanelInstallPlan:
;;     """Plan an install motion. Raises before planning if a structural gate fails.
;; 
;;     Gate order is fail-fast: civilian use, then no-server-key, then witness quorum.
;;     Only after the gates pass do we solve IK and check the trajectory envelope.
;;     A witness-quorum miss does not raise (it is a Council-escalation Datom), so the
;;     plan is returned with witness_ok=False for the audit trail.
;;     """
;;     assert_civilian(use, PERMITTED_USES)               # N1
;;     require_member_signature(member_sig, server_sig)   # G15/G7
;;     quorum = witness_quorum_ok(witness_sigs)           # G8 (record, do not raise)
;; 
;;     x, y = target_xy
;;     reachable = OTETE_ARM.reachable(x, y)
;;     joints_goal = OTETE_ARM.ik2(x, y, elbow_up=True) if reachable else None
;; 
;;     env = SafetyEnvelope(max_joint_speed=1.0, human_proximity_speed=0.25, max_reach=OTETE_ARM.max_reach)
;;     traj: list[tuple[float, ...]] = []
;;     envelope_ok = False
;;     violations: list[str] = []
;;     if joints_goal is not None:
;;         traj = joint_trajectory(q_start, joints_goal, steps=steps)
;;         check = env.check_trajectory(traj, dt=dt, human_present=human_present)
;;         envelope_ok = check["ok"]
;;         violations = check["violations"]
;; 
;;     return PanelInstallPlan(
;;         use=use,
;;         target_xy=target_xy,
;;         reachable=reachable,
;;         joints_goal=joints_goal,
;;         trajectory_steps=len(traj),
;;         envelope_ok=envelope_ok,
;;         envelope_violations=violations,
;;         human_present=human_present,
;;         member_sig=member_sig,
;;         witness_ok=quorum["ok"],
;;         server_held_key=False,  # G15: structural invariant
;;         dry_run=True,           # G10: R0 offline only
;;     )
(defn plan-panel-install [& _]
  (throw (ex-info "TODO: port-failed" {:from "plan_panel_install"})))

(defn to-datoms [plan job-id]
  "Project an install plan into kotoba EAVT-shaped datoms (G6)."
  (let [robot-id "otete-01"]
    {:install/id job-id
     :install/robot robot-id
     :install/use (:use plan)
     :install/target-x (:target-xy plan 0)
     :install/target-y (:target-xy plan 1)
     :install/reachable (:reachable plan)
     :install/trajectory-steps (:trajectory-steps plan)
     :install/envelope-ok (:envelope-ok plan)
     :install/human-present (:human-present plan)
     :install/member-sig (:member-sig plan)
     :install/witness-ok (:witness-ok plan)
     :install/server-held-key (:server-held-key plan) ; G15: always false
     :install/dry-run (:dry-run plan)})) ; G10

