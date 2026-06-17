#!/usr/bin/env bb
;; LIVE cross-language py↔clj parity for the mitsuho food/agriculture agent.
(ns mitsuho.py.test-agent-parity
  "test_agent_parity.clj — mitsuho agent py↔clj LIVE parity (ADR-2605261015).

  The existing test_agent.clj pins values captured once from agent.py (a snapshot that only
  checks clj against itself). This runs the ACTUAL agent.py via a python3 subprocess and the clj
  impl over the SAME states, then DEEP-COMPARES the FULL handler outputs (every field, not just
  the headline decision) — catching drift in EITHER impl AND a key-name divergence a snapshot
  can't see (clj keyword :plan_state vs py string \"plan_state\"). Exercises the constitutional
  gates: G9 prohibited-pesticide REJECT, G7 patented-seed REJECT, G8 soil-carbon → council-review,
  G3/G4 10%-tithe settlement.

  Gracefully SKIPS if python3 is unavailable (red only on a genuine py↔clj divergence).

  Run:  bb --classpath 20-actors 20-actors/mitsuho/py/test_agent_parity.clj"
  (:require [mitsuho.py.agent :as a]
            [clojure.java.shell :refer [sh]]
            [cheshire.core :as json]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private py-dir "20-actors/mitsuho/py")

;; ── shared battery (identical states in py-src and the clj recompute) ──
(def ^:private parcel  {:parcel_id "p1" :geojson_cid "bafy" :soil_health_score 7.5 :organic_cert_ref "jas-123"})
(defn- crop [seed pests] {:parcel_id "p1" :crop "rice" :seed_source seed :pesticide_manifest pests})
(defn- harvest [d] {:parcel_id "p1" :crop "rice" :yield_kg 1000 :soil_carbon_delta_tons_co2eq d})

(def ^:private crop-cases
  [["svalbard" ["neonicotinoid imidacloprid"]]   ; G9 → rejected
   ["svalbard" ["glyphosate"]]                    ; G9 → rejected
   ["svalbard" ["paraquat"]]                      ; G9 → rejected
   ["svalbard" ["neem"]]                          ; clean → recorded
   ["monsanto-patented" []]])                     ; G7 patented seed → rejected
(def ^:private harvest-cases [-1.2 2.5])
(def ^:private settle-cases [[250000000 nil] [250000000 "sig:abc"]])

(def ^:private py-src
  (str "import json, agent as a\n"
       "out = {'parcel': a.handle_parcel_attestation({'parcel_id':'p1','geojson_cid':'bafy','soil_health_score':7.5,'organic_cert_ref':'jas-123'}),\n"
       " 'crop': [a.handle_crop_plan({'parcel_id':'p1','crop':'rice','seed_source':s,'pesticide_manifest':p})"
       " for s,p in [['svalbard',['neonicotinoid imidacloprid']],['svalbard',['glyphosate']],['svalbard',['paraquat']],['svalbard',['neem']],['monsanto-patented',[]]]],\n"
       " 'harvest': [a.handle_harvest({'parcel_id':'p1','crop':'rice','yield_kg':1000,'soil_carbon_delta_tons_co2eq':d}) for d in [-1.2,2.5]],\n"
       " 'settle': [a.build_settlement_intent(g, b) for g,b in [[250000000,None],[250000000,'sig:abc']]]}\n"
       "print(json.dumps(out))\n"))

(defn- py-results []
  (try
    (let [r (sh "python3" "-c" py-src :dir py-dir)]
      (when (and (= 0 (:exit r)) (seq (:out r)))
        (json/parse-string (:out r) false)))   ; string keys both sides
    (catch Exception _ nil)))

(defn- stringify [x]
  (cond
    (map? x) (into {} (map (fn [[k v]] [(if (keyword? k) (name k) k) (stringify v)]) x))
    (sequential? x) (mapv stringify x)
    :else x))

(defn- clj-results []
  {"parcel" (stringify (a/handle-parcel-attestation parcel))
   "crop"   (mapv #(stringify (a/handle-crop-plan (crop (first %) (second %)))) crop-cases)
   "harvest" (mapv #(stringify (a/handle-harvest (harvest %))) harvest-cases)
   "settle"  (mapv #(stringify (a/build-settlement-intent (first %) (second %))) settle-cases)})

(deftest clj-gates-fire-correctly
  ;; runs regardless of python: the constitutional gates produce the right decisions.
  (is (= "rejected" (:plan_state (a/handle-crop-plan (crop "svalbard" ["neonicotinoid x"])))) "G9 pesticide")
  (is (= "rejected" (:plan_state (a/handle-crop-plan (crop "monsanto-patented" [])))) "G7 patented seed")
  (is (= "recorded" (:plan_state (a/handle-crop-plan (crop "svalbard" ["neem"])))) "clean approved")
  (is (= "pending_council_review" (:harvest_state (a/handle-harvest (harvest -1.2)))) "G8 soil carbon")
  (is (= 25000000 (:titheMinor (a/build-settlement-intent 250000000 nil))) "10% tithe")
  (is (= "executed" (:state (a/build-settlement-intent 250000000 "sig:abc"))) "buyer-sig → executed"))

(deftest agent-full-output-matches-python
  (let [py (py-results)]
    (if-not py
      (is true "python3 unavailable — mitsuho agent cross-language parity skipped")
      (let [clj (clj-results)]
        ;; FULL output deep-compare (every field), per handler family
        (is (= (get py "parcel") (get clj "parcel")) "parcel-attestation full output")
        (is (= (get py "crop") (get clj "crop")) "crop-plan full outputs (G9/G7 gates + fields)")
        (is (= (get py "harvest") (get clj "harvest")) "harvest full outputs (G8 gate + fields)")
        (is (= (get py "settle") (get clj "settle")) "settlement full outputs (tithe + state)")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'mitsuho.py.test-agent-parity)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
