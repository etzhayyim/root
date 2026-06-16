(ns hinagata.tests.test-maturity
  "hinagata 雛形 — maturity-scorecard tests (ADR-2606111954). 1:1 Clojure port of
  tests/test_maturity.py (pytest → clojure.test). Pure stdlib, network-free.

  maturity.CORE_CLAUSES is private in the existing maturity.cljc port, so the eight core
  clauses are mirrored here as `core-clauses` (the same module constant the Python test
  references). analyze.CITE_KINDS = analyze/cite-kinds.

  The Python __main__ demo runner is intentionally omitted (no behaviour, just printing)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [hinagata.methods.analyze :as analyze]
            [hinagata.methods.maturity :as maturity]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def seed (io/file actor-dir "data" "seed-legal-template-graph.kotoba.edn"))

;; mirrors maturity.CORE_CLAUSES (private in maturity.cljc — same module constant)
(def core-clauses
  ["cl.signature-esign" "cl.data-subject-rights" "cl.warranty-conformity"
   "cl.employment-termination" "cl.lease-term-generic" "cl.ip-assignment"
   "cl.cooling-off" "cl.dispute-arbitration"])

(deftest test-scorecard-renders-and-is-generated-banner
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        md (maturity/maturity nodes edges)]
    (is (and (str/starts-with? md "# hinagata") (str/includes? md "GENERATED")))
    (doseq [section ["## Size" "## Quality gates" "## Core-clause worldwide grounding"
                     "## Readiness"]]
      (is (str/includes? md section) (str "missing section " section)))))

(deftest test-scorecard-reports-clean-integrity
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        md (maturity/maturity nodes edges)]
    (is (str/includes? md "0 errors / 0 warnings") "scorecard should reflect clean integrity")))

(deftest test-core-clauses-grounded-across-multiple-jurisdictions
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        st-jx (into {} (for [n (vals nodes) :when (= ":statute" (get n ":lt/kind"))]
                         [(get n ":lt/id") (get n ":statute/jurisdiction")]))]
    (doseq [cl core-clauses]
      (is (contains? nodes cl) (str "core clause " cl " missing from graph"))
      (let [jx (set (for [e edges
                          :when (and (contains? analyze/cite-kinds (get e ":en/kind"))
                                     (= cl (get e ":en/from")))]
                      (get st-jx (get e ":en/to"))))
            jx (set (filter some? jx))]
        (is (>= (count jx) 2)
            (str "core clause " cl " grounded in only " (count jx) " jurisdiction(s)"))))))

#?(:clj (defn -main [& _] (run-tests 'hinagata.tests.test-maturity)))
