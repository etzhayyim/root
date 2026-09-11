;; etzhayyim.test-identifier-audit — identifier-audit pure-helper invariants.
;; Run: bb test:identifier-audit
;; Covers audit-jsonld-data (rule checks) + violations->report (file IO deferred).
(ns etzhayyim.test-identifier-audit
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.identifier-audit :as ia]))

(deftest audit-jsonld-clean
  (testing "valid nanoid (8-12) + did (plc/web/key/pkh) + kebab name → no violations"
    (is (= [] (ia/audit-jsonld-data
               {"nanoid" "abcde12345" "did" "did:plc:abc123" "name" "my-actor"} "p")))
    (is (= [] (ia/audit-jsonld-data {} "p")))))   ;; empty fields skip all checks

(deftest audit-jsonld-violations
  (testing "each malformed field yields its rule"
    (is (= ["nanoid-format"] (mapv :rule (ia/audit-jsonld-data {"nanoid" "ab"} "p"))))   ;; too short
    (is (= ["did-format"]    (mapv :rule (ia/audit-jsonld-data {"did" "did:eth:0xabc"} "p"))))
    (is (= ["name-lowercase"] (mapv :rule (ia/audit-jsonld-data {"name" "MyActor"} "p"))))
    (is (= ["name-lowercase"] (mapv :rule (ia/audit-jsonld-data {"name" "my_actor"} "p"))))) ;; '_' is bad
  (testing "multiple violations accumulate"
    (is (= ["nanoid-format" "did-format" "name-lowercase"]
           (mapv :rule (ia/audit-jsonld-data
                        {"nanoid" "x" "did" "did:eth:y" "name" "BadName"} "p"))))))

(deftest violations->report-summary
  (is (= {:total 3 :by-rule {"nanoid-format" 2 "did-format" 1}}
         (dissoc (ia/violations->report
                  [{:rule "nanoid-format"} {:rule "nanoid-format"} {:rule "did-format"}])
                 :violations)))
  (is (= {:total 0 :by-rule {} :violations []} (ia/violations->report []))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-identifier-audit)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
