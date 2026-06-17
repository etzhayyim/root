#!/usr/bin/env bb
;; LIVE cross-language py↔clj parity for the ainori pooled-mobility agent.
(ns ainori.py.test-agent-parity
  "test_agent_parity.clj — ainori agent py↔clj LIVE parity (ADR-2606071500).

  The existing test_agent.clj is a snapshot (clj-vs-itself; the stale test_agent.PY still expects
  settlement 'intent' where the IMPLs now agree on 'executed'). This compares IMPL-to-IMPL: runs
  the ACTUAL agent.py via a python3 subprocess and the clj impl over the SAME inputs, then
  DEEP-COMPARES the FULL outputs of the DETERMINISTIC functions — the SAE-L4 safety envelope (G3
  REFUSAL not clamp), the no-surge cost-share (G2), the 10%-tithe settlement (G4 driverWage 0),
  and member-signed authorization (G5 no-server-key). `match_pool` is excluded: its matchId embeds
  Python's process-nondeterministic hash() (the documented contract-only class), un-portable.

  Gracefully SKIPS if python3 is unavailable (red only on a genuine py↔clj divergence).

  Run:  bb --classpath 20-actors 20-actors/ainori/py/test_agent_parity.clj"
  (:require [ainori.py.agent :as a]
            [clojure.java.shell :refer [sh]]
            [cheshire.core :as json]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private py-dir "20-actors/ainori/py")
(def ^:private carrier "did:web:etzhayyim.com:actor:driver1")

;; envelope cases [zone speed in-odd sae]; cost-share [fuel-wear occupancy]
(def ^:private env-cases [["residential" 12.0 true 4] ["school" 8.0 true 5]
                          ["hwy" 20.0 false 3] ["arterial" 12.0 true 4]])
(def ^:private cs-cases [[1200000 4] [1200000 1] [900000 3]])

(def ^:private py-src
  (str "import json, agent as a\n"
       "env=[a.safety_envelope_ok(z,s,o,l) for z,s,o,l in "
       "[['residential',12.0,True,4],['school',8.0,True,5],['hwy',20.0,False,3],['arterial',12.0,True,4]]]\n"
       "cs=[a.cost_share(f,o) for f,o in [[1200000,4],[1200000,1],[900000,3]]]\n"
       "s=a.build_settlement_intent(1000000,'" carrier "')\n"
       "auth=[a.authorize_settlement(s,{'origin':'member','ref':'r1'}),"
       "a.authorize_settlement(s,{'origin':'server','ref':'r2'})]\n"
       "print(json.dumps({'env':env,'cs':cs,'settle':s,'auth':auth}))\n"))

(defn- py-results []
  (try
    (let [r (sh "python3" "-c" py-src :dir py-dir)]
      (when (and (= 0 (:exit r)) (seq (:out r)))
        (json/parse-string (:out r) false)))
    (catch Exception _ nil)))

(defn- stringify [x]
  (cond
    (map? x) (into {} (map (fn [[k v]] [(if (keyword? k) (name k) k) (stringify v)]) x))
    (sequential? x) (mapv stringify x)
    :else x))

(defn- clj-results []
  (let [s (a/build-settlement-intent 1000000 carrier)]
    {"env"    (mapv #(stringify (apply a/safety-envelope-ok %)) env-cases)
     "cs"     (mapv #(a/cost-share (first %) (second %)) cs-cases)
     "settle" (stringify s)
     "auth"   [(stringify (a/authorize-settlement s {:origin "member" :ref "r1"}))
               (stringify (a/authorize-settlement s {:origin "server" :ref "r2"}))]}))

(deftest clj-envelope-and-settlement-gates-fire
  ;; runs regardless of python: G3 REFUSAL (not clamp), G2 no-surge, G4 driverWage 0, G5 member-sig.
  (is (false? (:ok (a/safety-envelope-ok "residential" 12.0 true 4))) "over-speed refused (not clamped)")
  (is (false? (:ok (a/safety-envelope-ok "school" 8.0 true 5))) "SAE>4 refused")
  (is (= 300000 (a/cost-share 1200000 4)) "no-surge flat split")
  (let [s (a/build-settlement-intent 1000000 carrier)]
    (is (= 0 (:driverWageMinor s)) "platform pays driver cash≡0")
    (is (= 100000 (:titheMinor s)) "10% tithe")
    (is (false? (:serverHeldKey s)))
    (is (true? (:signed (a/authorize-settlement s {:origin "member" :ref "r1"}))) "member sig authorizes")
    (is (true? (:refused (a/authorize-settlement s {:origin "server" :ref "r2"}))) "server sig refused (G5)")))

(deftest agent-deterministic-outputs-match-python
  (let [py (py-results)]
    (if-not py
      (is true "python3 unavailable — ainori agent cross-language parity skipped")
      (let [clj (clj-results)]
        (is (= (get py "env") (get clj "env")) "safety-envelope full outputs (4 branches + reasons)")
        (is (= (get py "cs") (get clj "cs")) "cost-share splits")
        (is (= (get py "settle") (get clj "settle")) "settlement full output (tithe + driverWage 0 + executed)")
        (is (= (get py "auth") (get clj "auth")) "authorize member+server full outputs")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'ainori.py.test-agent-parity)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
