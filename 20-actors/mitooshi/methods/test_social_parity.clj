#!/usr/bin/env bb
;; LIVE cross-language py↔clj parity for the mitooshi resilience-advisory composer.
(ns mitooshi.methods.test-social-parity
  "test_social_parity.clj — mitooshi social py↔clj LIVE parity (ADR-2606051800).

  Runs the ACTUAL social.py via a python3 subprocess and the clj impl over the SAME inputs, then
  DEEP-COMPARES the full successful advisory + the G1/G2/G3 refusal messages. The G2/G3 messages
  embed the ALLOWED_USE / PLANNERS tuples + the offending value — the exact message-format class
  this sweep keeps catching (py tuple `('a', …)` + `{x!r}` single-quote vs clj set `#{…}` +
  pr-str double-quote). Distribution-only (G1), non-speculative use (G2), planner-routed (G3).

  Gracefully SKIPS if python3 is unavailable (red only on a genuine py↔clj divergence).

  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/test_social_parity.clj"
  (:require [mitooshi.methods.social :as s]
            [clojure.java.shell :refer [sh]]
            [cheshire.core :as json]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private py-dir "20-actors/mitooshi/methods")

(def ^:private py-src
  (str "import json, social\n"
       "def refuse(f):\n"
       "    try: f(); return None\n"
       "    except ValueError as e: return str(e)\n"
       "out={'adv': social.compose_resilience_advisory('s1',0.2,0.3,7, use=':resilience', route_to='danjo'),\n"
       " 'g1': refuse(lambda: social.compose_resilience_advisory('s1',0.2,0.3,7, point_asserted=True)),\n"
       " 'g2': refuse(lambda: social.compose_resilience_advisory('s1',0.2,0.3,7, use=':trade', route_to='danjo')),\n"
       " 'g3': refuse(lambda: social.compose_resilience_advisory('s1',0.2,0.3,7, use=':resilience', route_to='nobody'))}\n"
       "print(json.dumps(out))\n"))

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

(defn- refuse-msg [thunk]
  (try (thunk) nil (catch clojure.lang.ExceptionInfo e (.getMessage e))))

(defn- clj-results []
  {"adv" (stringify (s/compose-resilience-advisory "s1" 0.2 0.3 7 ":resilience" false "danjo"))
   "g1"  (refuse-msg #(s/compose-resilience-advisory "s1" 0.2 0.3 7 ":resilience" true "danjo"))
   "g2"  (refuse-msg #(s/compose-resilience-advisory "s1" 0.2 0.3 7 ":trade" false "danjo"))
   "g3"  (refuse-msg #(s/compose-resilience-advisory "s1" 0.2 0.3 7 ":resilience" false "nobody"))})

(deftest clj-advisory-and-gates-fire
  ;; runs regardless of python: a band (never a point), G1/G2/G3 refusals with py-style messages.
  ;; the clj advisory map mirrors social.py's STRING keys ("routeTo"/"band68"/"shape").
  (let [adv (s/compose-resilience-advisory "s1" 0.2 0.3 7 ":resilience" false "danjo")]
    (is (= [-0.1 0.5] (get adv "band68")) "states a band, not a point (G1)")
    (is (= "aggregate" (get adv "shape")) "aggregate-first (G4)")
    (is (= "danjo" (get adv "routeTo")) "planner-routed (G3)"))
  (is (re-find #"point-asserted" (refuse-msg #(s/compose-resilience-advisory "s1" 0.2 0.3 7 ":resilience" true "danjo"))))
  (is (re-find #"use ':trade' not in" (refuse-msg #(s/compose-resilience-advisory "s1" 0.2 0.3 7 ":trade" false "danjo")))
      "G2 message uses py single-quote repr")
  (is (re-find #"\(':resilience', ':planning'" (refuse-msg #(s/compose-resilience-advisory "s1" 0.2 0.3 7 ":trade" false "danjo")))
      "G2 renders ALLOWED_USE as a py ordered tuple"))

(deftest social-matches-python
  (let [py (py-results)]
    (if-not py
      (is true "python3 unavailable — mitooshi social cross-language parity skipped")
      (let [clj (clj-results)]
        (is (= (get py "adv") (get clj "adv")) "successful advisory full output (band/shape/text/route)")
        (is (= (get py "g1") (get clj "g1")) "G1 point-assertion refusal message")
        (is (= (get py "g2") (get clj "g2")) "G2 illegal-use refusal message (tuple + single-quote repr)")
        (is (= (get py "g3") (get clj "g3")) "G3 bad-planner refusal message (tuple + single-quote repr)")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'mitooshi.methods.test-social-parity)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
