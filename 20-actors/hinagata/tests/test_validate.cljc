(ns hinagata.tests.test-validate
  "hinagata 雛形 — integrity-validator tests (ADR-2606111954). 1:1 Clojure port of
  tests/test_validate.py (pytest → clojure.test). Pure stdlib, network-free.

  Enforces the maturity invariants validate.py checks: the committed seed has ZERO structural
  errors, and its remaining soft warnings stay in the honestly-allowed categories.

  The Python __main__ demo runner is intentionally omitted (no behaviour, just printing)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [clojure.set]
            [clojure.java.io :as io]
            [hinagata.methods.analyze :as analyze]
            [hinagata.methods.validate :as validate]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def seed (io/file actor-dir "data" "seed-legal-template-graph.kotoba.edn"))

(deftest test-seed-has-zero-errors
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        [errors _] (validate/validate nodes edges)]
    (is (= errors []) (str "seed has structural integrity errors:\n  " (str/join "\n  " errors)))))

(deftest test-warnings-are-only-allowed-soft-categories
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        [_ warnings] (validate/validate nodes edges)]
    (doseq [w warnings]
      (let [ok (or (str/includes? w "does not :instantiate any concept")
                   (str/includes? w "registry-only")
                   (str/includes? w "not used by any template")
                   (str/includes? w "not instantiated by any clause")
                   (str/includes? w "has no signature clause"))]
        (is ok (str "unexpected warning category (investigate): " w))))))

(deftest test-every-template-is-complete
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        [errors _] (validate/validate nodes edges)]
    (is (not (some #(or (str/includes? % "has no clauses")
                        (str/includes? % "has no :governed-by")) errors)))))

(deftest test-all-citation-targets-are-statutes
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        [errors _] (validate/validate nodes edges)]
    (is (not (some #(str/includes? % "expected :statute") errors)))))

(deftest test-relational-edges-are-well-typed
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        conflicts (filter #(= ":conflicts-with" (get % ":en/kind")) edges)
        derived (filter #(= ":derived-from" (get % ":en/kind")) edges)]
    (is (and (seq conflicts) (seq derived))
        "the :conflicts-with / :derived-from relations should be exercised")
    (doseq [e conflicts]
      (is (= ":clause" (get-in nodes [(get e ":en/from") ":lt/kind"])))
      (is (= ":clause" (get-in nodes [(get e ":en/to") ":lt/kind"])))
      (is (not= (get e ":en/from") (get e ":en/to")) "conflict self-loop"))
    (doseq [e derived]
      (is (= ":template" (get-in nodes [(get e ":en/from") ":lt/kind"])))
      (is (= ":template" (get-in nodes [(get e ":en/to") ":lt/kind"]))))
    (let [[errors _] (validate/validate nodes edges)]
      (is (not (some #(or (str/includes? % "conflicts-with")
                          (str/includes? % "derived-from")) errors))))))

(deftest test-all-ten-edge-kinds-exercised
  (let [{:keys [nodes edges]} (analyze/load-file* seed)
        kinds (set (map #(get % ":en/kind") edges))
        expected #{":has-clause" ":cites-statute" ":mandated-by" ":instantiates" ":governed-by"
                   ":applies-in" ":translates" ":conflicts-with" ":derived-from" ":supersedes"}
        missing (clojure.set/difference expected kinds)]
    (is (empty? missing) (str "ontology edge kinds never exercised: " missing))
    ;; :supersedes must be template→template
    (doseq [e edges :when (= ":supersedes" (get e ":en/kind"))]
      (is (= ":template" (get-in nodes [(get e ":en/from") ":lt/kind"])))
      (is (= ":template" (get-in nodes [(get e ":en/to") ":lt/kind"]))))))

#?(:clj (defn -main [& _] (run-tests 'hinagata.tests.test-validate)))
