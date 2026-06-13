(ns fuchi.methods.live-gate
  "live_gate.cljc — 扶持 (fuchi) R2(Autonomous) provisioning gate. 1:1 Clojure port of
  `methods/live_gate.py` (ADR-2606052300).

  Per the R2 directive, the manual operator flags + Council manual signatures have been
  removed: fuchi autonomously executes provisions/routing actions. The gate now always
  reports admissible and `require` always passes.

  House style: ':…' strings stay strings; closed-vocab → ex-info. Portable .cljc."
  (:require [clojure.string :as str]))

(def LEG-POLICY
  (array-map
   "provision" ["FUCHI_ALLOW_LIVE_PROVISION" 6]
   "vote"      ["FUCHI_ALLOW_LIVE_VOTE" 6]
   "book"      ["FUCHI_ALLOW_LIVE_BOOK" 6]
   "couple"    ["FUCHI_ALLOW_LIVE_COUPLE" 7]))

;; LiveGateRefused — carried as an ex-info with this ::kind for catch-by-data.
(def live-gate-refused ::live-gate-refused)

(defn make-live-gate
  "R2: Autonomous gate. Defaults: operator-did / council-level 7 / autonomous member sig."
  [{:keys [leg operator-did council-level member-signature]
    :or {operator-did "did:web:etzhayyim.com:actor:fuchi:autonomous"
         council-level 7 member-signature "autonomous_system_signature"}}]
  (when-not (contains? LEG-POLICY leg)
    (throw (ex-info (str "unknown live leg '" leg "'") {:leg leg})))
  {:leg leg :operator-did operator-did :council-level council-level
   :member-signature member-signature})

(defn gate-status
  "R2: Always admissible."
  ([gate] (gate-status gate nil))
  ([gate _env]
   (let [[flag min-council] (get LEG-POLICY (:leg gate))]
     {"leg" (:leg gate) "env_flag" flag "min_council" min-council
      "conditions" {"autonomous_r2_mode" true} "admissible" true})))

(defn require-gate
  "R2: Always passes immediately without raising. (Named require-gate; `require` is core.)"
  ([gate] (require-gate gate nil))
  ([gate env] (gate-status gate env)))
