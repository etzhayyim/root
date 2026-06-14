;; test_maturity.clj — the honesty-invariant gate-verifier must pass across ALL data.
;; Run: bb test_maturity.clj   (or: clojure -M test_maturity.clj)   from methods/.
(ns root.danjo.methods.test-maturity
  (:require [clojure.string :as str]))

(load-file "maturity.clj")
(alias 'm 'root.danjo.methods.maturity)

(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))

(let [c (m/context)
      results (m/run-invariants c)]
  (check "≥9 honesty invariants defined" (>= (count results) 9))
  ;; every invariant passes across the whole dataset
  (doseq [r results]
    (check (str "invariant " (name (:id r)) " (" (:gate r) ")") (:ok r)))
  (check "ALL invariants pass" (every? :ok results))

  ;; the scorecard renders + reports the passing count + R0 status
  (let [md (m/scorecard c)]
    (check "scorecard reports 9/9 passing" (str/includes? md "9/9 passing"))
    (check "scorecard marks Status R0"     (str/includes? md "Status: R0"))
    (check "scorecard lists R1 triggers"   (str/includes? md "R1 activation triggers"))))

(println (format "── maturity: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
