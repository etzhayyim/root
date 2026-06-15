;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hikari/methods/_substrate.py (unit_refactor stage 0)
;; _substrate — re-export the shared infra-robotics substrate for hikari/methods.
(ns root.hikari.methods.substrate
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare robotics)

;; TODO: port-failed unit _ROBOTICS (bb-compile error)
;; _ROBOTICS = pathlib.Path(__file__).resolve().parents[2] / "kuni-umi" / "robotics"
;; __all__ = [
;;     "PID",
;;     "ControlResult",
;;     "Droop",
;;     "DroopPI",
;;     "simulate",
;;     "PlanarArm",
;;     "Pose",
;;     "joint_trajectory",
;;     "FirstOrderPlant",
;;     "MicrogridPlant",
;;     "Plant",
;;     "SafetyEnvelope",
;;     "SafetyError",
;;     "assert_civilian",
;;     "require_member_signature",
;;     "witness_quorum_ok",
;; ]
(def robotics nil) ;; TODO: port-failed const

