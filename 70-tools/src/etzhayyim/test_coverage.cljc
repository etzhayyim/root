;; etzhayyim.test-coverage — coverage pure-helper invariants (cljc port; IO-free).
;; Run: bb test:coverage
;; Covers check-actor-completeness · compute-actor-score · actor-summary ·
;; extract-json-block (brace-matching) · oil-match? · governance-issues/ok?.
(ns etzhayyim.test-coverage
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.coverage :as cov]))

(deftest completeness-and-score
  (testing "empty data → every checked field is false"
    (let [c (cov/check-actor-completeness {})]
      (is (map? c))
      (is (every? false? (vals c)))))
  (testing "compute-actor-score = % of truthy fields"
    (is (= 50 (cov/compute-actor-score {"a" true "b" true "c" false "d" false})))
    (is (= 100 (cov/compute-actor-score {"a" true})))
    (is (= 0 (cov/compute-actor-score {})))))

(deftest actor-summary-shape
  (let [s (cov/actor-summary {"nanoid" "n1" "name" "foo"} "20-actors/foo/manifest.jsonld")]
    (is (= "n1" (:nanoid s)))
    (is (= "foo" (:name s)))
    (is (= "20-actors/foo/manifest.jsonld" (:path s)))
    (is (integer? (:score s)))
    (is (vector? (:missing s)))
    (is (map? (:completeness s)))))

(deftest extract-json-block-brace-matching
  (is (= "{\"a\":1}" (cov/extract-json-block "noise {\"a\":1} trailing")))
  (testing "nested objects"
    (is (= "{\"a\":{\"b\":2}}" (cov/extract-json-block "x {\"a\":{\"b\":2}} y"))))
  (testing "braces inside string literals do not close the block"
    (is (= "{\"a\":\"}\"}" (cov/extract-json-block "{\"a\":\"}\"}"))))
  (testing "no brace / non-string → nil"
    (is (nil? (cov/extract-json-block "no json here")))
    (is (nil? (cov/extract-json-block nil)))))

(deftest oil-match-keywords
  (is (true? (cov/oil-match? {"name" "Oil Refinery"})))
  (is (true? (cov/oil-match? {"description" "crude petroleum exports"})))
  (is (false? (cov/oil-match? {"name" "Community Garden" "description" "vegetables"}))))

(deftest governance-completeness
  (testing "issues = missing/blank governance fields"
    (is (= [] (cov/governance-issues {"operator" "x" "authority" "y" "visibility" "z"})))
    (is (= ["authority" "visibility"] (cov/governance-issues {"operator" "x"})))
    (is (= ["operator" "authority" "visibility"] (cov/governance-issues {}))))
  (testing "ok? iff no issues"
    (is (true? (cov/governance-ok? {"operator" "x" "authority" "y" "visibility" "z"})))
    (is (false? (cov/governance-ok? {"operator" "x"})))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-coverage)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
