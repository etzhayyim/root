;; ie-flow test runner. Run from repo root:
;;   bb -cp "70-tools/src:orgs/kotoba-lang/kotodama/src" 70-tools/src/etzhayyim/ie_flow/run_tests.clj
;; Exits non-zero on any failure. ADR-2606211200.
(require '[clojure.test :as t]
         'etzhayyim.ie-flow.test-metrics
         'etzhayyim.ie-flow.test-metrics-properties
         'etzhayyim.ie-flow.test-dynamics
         'etzhayyim.ie-flow.test-coscientist
         'etzhayyim.ie-flow.test-ledger
         'etzhayyim.ie-flow.test-lifecycle
         'etzhayyim.ie-flow.test-reward
         'etzhayyim.ie-flow.test-react
         'etzhayyim.ie-flow.test-control
         'etzhayyim.ie-flow.test-colony
         'etzhayyim.ie-flow.test-score
         'etzhayyim.ie-flow.test-gate-adapter
         'etzhayyim.ie-flow.test-boundary
         'etzhayyim.ie-flow.test-embed)

(let [{:keys [fail error]}
      (t/run-tests 'etzhayyim.ie-flow.test-metrics
                   'etzhayyim.ie-flow.test-metrics-properties
                   'etzhayyim.ie-flow.test-dynamics
                   'etzhayyim.ie-flow.test-coscientist
                   'etzhayyim.ie-flow.test-ledger
                   'etzhayyim.ie-flow.test-lifecycle
                   'etzhayyim.ie-flow.test-reward
                   'etzhayyim.ie-flow.test-react
                   'etzhayyim.ie-flow.test-control
                   'etzhayyim.ie-flow.test-colony
                   'etzhayyim.ie-flow.test-score
                   'etzhayyim.ie-flow.test-gate-adapter
                   'etzhayyim.ie-flow.test-boundary
                   'etzhayyim.ie-flow.test-embed)]
  (if (pos? (+ (or fail 0) (or error 0)))
    (do (println "── ie-flow: FAILURES above ──") (System/exit 1))
    (println "── ie-flow: ALL suites green ──")))
