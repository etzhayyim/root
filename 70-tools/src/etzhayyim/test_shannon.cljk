;; etzhayyim.test-shannon — Shannon redundancy-check pure invariants (cljc port; IO-free).
;; Run via the aggregate: bb test:helpers
;; Covers make-item/item->dict · make-check/check->dict · norm-line · hash8 ·
;; dedup-items · make-check-result · ordered-check-names · assemble-checks.
(ns etzhayyim.test-shannon
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.shannon :as sh]))

(deftest item-construct-and-serialise
  (let [it (sh/make-item "a.ts" "dup" 0.5)]
    (is (= {:path "a.ts" :kind "dup" :redundancy 0.5 :duplicate-of "" :detail ""} it))
    (testing "item->dict drops blank duplicate_of/detail"
      (is (= {"path" "a.ts" "kind" "dup" "redundancy" 0.5} (sh/item->dict it))))
    (testing "item->dict keeps present duplicate_of/detail"
      (let [d (sh/item->dict (sh/make-item "b" "k" 0.1 "orig.ts" "near-clone"))]
        (is (= "orig.ts" (get d "duplicate_of")))
        (is (= "near-clone" (get d "detail")))))))

(deftest check-construct-and-serialise
  (let [c (sh/make-check "claude_md_duplication")]
    (is (= "claude_md_duplication" (:name c)))
    (is (= 100.0 (:score c)))
    (is (= 0 (:violations c)))
    (is (= [] (:items c))))
  (testing "check->dict round-trips to string keys"
    (let [d (sh/check->dict (sh/make-check "c" 80.0 1.0 2 "two dups" []))]
      (is (= "c" (get d "name")))
      (is (= 80.0 (get d "score")))
      (is (= 2 (get d "violations"))))))

(deftest norm-line-normalisation
  (is (= "hello world" (sh/norm-line "  **Hello**  World ")))
  (is (= "code x" (sh/norm-line "`code` *x*")))
  (is (= "a b c" (sh/norm-line "A   B\tC"))))

(deftest hash8-sha256-prefix
  (let [h (sh/hash8 "etzhayyim")]
    (is (re-matches #"[0-9a-f]{16}" h))
    (is (= h (sh/hash8 "etzhayyim")))
    (is (not= h (sh/hash8 "etzhayyin")))))

(deftest dedup-items-by-key
  (testing "dedup on path|kind|detail, first occurrence wins"
    (let [items [{:path "a" :kind "k" :detail "d"}
                 {:path "a" :kind "k" :detail "d"}   ;; dup
                 {:path "b" :kind "k" :detail "d"}]]
      (is (= 2 (count (sh/dedup-items items))))
      (is (= "a" (:path (first (sh/dedup-items items))))))))

(deftest make-check-result-scoring
  (is (= 50.0 (:score (sh/make-check-result "c" 5 10 []))))
  (is (= 100.0 (:score (sh/make-check-result "c" 0 0 []))))    ;; total 0 → no penalty
  (testing "score is clamped to [0,100]"
    (is (= 0.0 (:score (sh/make-check-result "c" 20 10 []))))))

(deftest checks-ordering-and-assembly
  (testing "canonical order = 9 named checks"
    (is (= 9 (count (sh/ordered-check-names))))
    (is (= "claude_md_duplication" (first (sh/ordered-check-names)))))
  (testing "assemble-checks fills all 9 in order; supplied check is used"
    (let [custom (sh/make-check "dead_code_entropy" 42.0 0.0 3 "" [])
          out    (sh/assemble-checks {"dead_code_entropy" custom})]
      (is (= (sh/ordered-check-names) (mapv :name out)))
      (is (= 42.0 (:score (first (filter #(= "dead_code_entropy" (:name %)) out)))))
      (testing "Go-AST-only checks stubbed at score 100"
        (is (= 100.0 (:score (first (filter #(= "rust_duplication" (:name %)) out)))))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-shannon)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
