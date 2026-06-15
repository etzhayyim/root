;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/abaki/methods/live_gate.py (unit_refactor stage 0)
;; live_gate.py — 暴 (abaki) R2(Autonomous): Fully Autonomous Route Around policy publishing.
(ns root.abaki.methods.live-gate
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare live-gate-refused live-gate gate-status require)

;; TODO: port-failed unit LiveGateRefused (assembled-lint error)
;; class LiveGateRefused(RuntimeError):
;;     """Not used in R2, but kept for interface compatibility."""
(defn live-gate-refused [& _]
  (throw (ex-info "TODO: port-failed" {:from "LiveGateRefused"})))

(defn live-gate []
  {:operator-did "did:web:etzhayyim.com:actor:abaki:autonomous"
   :council-level 0
   :member-signature "autonomous_system_signature"})

(defn gate-status [gate ^:args {:keys [env]}]
  "R2: Always admissible. Autonomous execution."
  {"conditions" {"autonomous_r2_mode" true}
   "admissible" true})

(defn require [gate {:keys [env]}]
  "R2: Always passes immediately without raising."
  (gate-status gate (assoc {} :env env)))

