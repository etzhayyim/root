(ns hinagata.tests.test-query
  "hinagata 雛形 — knowledge-graph query tests (ADR-2606111954). 1:1 Clojure port of
  tests/test_query.py (pytest → clojure.test). Pure stdlib, network-free.

  The Python __main__ demo runner is intentionally omitted (no behaviour, just printing)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [hinagata.methods.analyze :as analyze]
            [hinagata.methods.query :as query]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def seed (io/file actor-dir "data" "seed-legal-template-graph.kotoba.edn"))

(defn- g [] (analyze/load-file* seed))

(deftest test-templates-in-jurisdiction
  (let [{:keys [nodes edges]} (g)
        jp (query/templates-in-jurisdiction nodes edges "jx.jp")]
    (is (seq jp) "expected templates governed by Japan")
    (doseq [t jp]
      (is (= ":template" (get-in nodes [t ":lt/kind"]))))
    ;; international has the broad-reach templates
    (let [intl (query/templates-in-jurisdiction nodes edges "jx.intl")]
      (is (some #{"tmpl.sales-intl"} intl)))))

(deftest test-statutes-grounding-template-are-real-statutes
  (let [{:keys [nodes edges]} (g)
        st (query/statutes-grounding-template nodes edges "tmpl.dpa-gdpr")]
    (is (seq st) "GDPR DPA should rest on statutes")
    (doseq [s st]
      (is (= ":statute" (get-in nodes [s ":lt/kind"]))))
    ;; the DPA must rest on at least one GDPR article
    (is (some #(str/includes? % "gdpr") st))))

(deftest test-translations-of-nda-are-multilingual
  (let [{:keys [nodes edges]} (g)
        tr (query/translations-of nodes edges "tmpl.nda-mutual")]
    (is (>= (count tr) 5) (str "NDA should have many translations, got " tr))
    (let [langs (set (map #(get-in nodes [% ":template/lang"]) tr))]
      (is (>= (count langs) 5) (str "translations should span many languages, got " langs)))))

(deftest test-conflicting-clauses-symmetric-lookup
  (let [{:keys [nodes edges]} (g)
        c (query/conflicting-clauses nodes edges "cl.ip-assignment")]
    (is (or (some #{"cl.cc-license"} c) (some #{"cl.copyleft-license"} c)))
    ;; the relation resolves from either side
    (let [back (query/conflicting-clauses nodes edges "cl.copyleft-license")]
      (is (some #{"cl.ip-assignment"} back)))))

(deftest test-jurisdictions-for-concept-data-protection-is-global
  (let [{:keys [nodes edges]} (g)
        jx (query/jurisdictions-for-concept nodes edges "concept.data-protection")]
    (is (>= (count jx) 4)
        (str "data-protection should be grounded across many jurisdictions, got " jx))))

(deftest test-coverage-gaps-is-the-inverse-worklist
  (let [{:keys [nodes edges]} (g)
        have (set (query/jurisdictions-for-concept nodes edges "concept.data-protection"))
        gaps (query/coverage-gaps nodes edges "concept.data-protection")]
    ;; a gap is never something already grounded, and is always a real major-jurisdiction node
    (doseq [gap gaps]
      (is (not (contains? have gap)))
      (is (and (some #{gap} query/major-jurisdictions) (contains? nodes gap))))
    ;; electronic-signature is broadly grounded, so it should have few/zero gaps
    (let [esign-gaps (query/coverage-gaps nodes edges "concept.electronic-signature")]
      (is (<= (count esign-gaps)
              (count (query/coverage-gaps nodes edges "concept.escrow")))
          "broadly-grounded e-signature should have no more gaps than a niche concept"))))

#?(:clj (defn -main [& _] (run-tests 'hinagata.tests.test-query)))
