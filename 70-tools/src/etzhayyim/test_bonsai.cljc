;; etzhayyim.test-bonsai — bonsai prune-detector invariants (cljc port).
;; Run: bb test:bonsai
;; Covers classify-tier / score-node / scan-workspace / growth-health — the pure
;; logic of the 盆栽 workspace evaluator (the daemon surfaces, never prunes).
(ns etzhayyim.test-bonsai
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.bonsai :as b]))

(deftest classify-tier-precedence
  (testing "most-specific tier hints win"
    (is (= "seed"   (b/classify-tier "CLAUDE.md")))   ;; seed beats the generic .md leaf
    (is (= "seed"   (b/classify-tier "deps.toml")))
    (is (= "trunk"  (b/classify-tier "pyproject.toml")))
    (is (= "fruit"  (b/classify-tier "TODO.md")))      ;; TODO hint beats .md
    (is (= "flower" (b/classify-tier "foo_test.py")))
    (is (= "leaf"   (b/classify-tier "notes.md"))))
  (testing "extension fallbacks"
    (is (= "branch" (b/classify-tier "main.ts")))
    (is (= "branch" (b/classify-tier "lib.rs")))        ;; source-ext fallback
    (is (= "leaf"   (b/classify-tier "data.json")))))   ;; default

(deftest score-node-signals
  (testing "empty file scores 40 with the 'empty file' signal"
    (let [{:keys [prune-score signals]} (b/score-node "x.py" "")]
      (is (= 40 prune-score))
      (is (some #{"empty file"} signals))))
  (testing "trivial (<5 lines) scores +20"
    (let [{:keys [prune-score signals]} (b/score-node "x.py" "one\ntwo")]
      (is (= 20 prune-score))
      (is (some #(re-find #"trivial" %) signals))))
  (testing "TODO/FIXME count contributes (capped at 30)"
    (let [{:keys [prune-score signals]} (b/score-node "x.py" "a\nTODO\nFIXME\nb\nc\nd")]
      (is (= 20 prune-score))                ;; 2 markers → +20, 6 lines → not trivial
      (is (some #(re-find #"TODO/FIXME" %) signals))))
  (testing "legacy filename adds +30"
    (is (= 30 (:prune-score (b/score-node "legacy_foo.py" "a\nb\nc\nd\ne\nf")))))
  (testing "empty + legacy-name sum (40 + 30)"
    (is (= 70 (:prune-score (b/score-node "legacy_old.py" "")))))
  (testing "score is capped at 100 when every signal fires"
    ;; TODO×3 (+30) · dead (+20) · trivial 4 lines (+20) · legacy name (+30) = 110 → 100
    (is (= 100 (:prune-score (b/score-node "legacy_x.py" "// dead\nTODO\nTODO\nTODO")))))
  (testing "nil content is treated as an empty file"
    (is (= 40 (:prune-score (b/score-node "x.py" nil))))))

(deftest scan-workspace-aggregates
  (let [files [{:path "src/a.py"               :content "TODO\n"}
               {:path "node_modules/dep/b.py"  :content "TODO"}     ;; skipped
               {:path "deps.lock"              :content "x"}        ;; ignored ext
               {:path "README.md"              :content "hello"}]
        r (b/scan-workspace files)]
    (testing "node_modules is skipped and ignore-exts excluded"
      (is (= 2 (:total-files r)))                                  ;; a.py + README.md
      (is (= 1 (get-in r [:tier-counts "branch"])))               ;; a.py
      (is (= 1 (get-in r [:tier-counts "leaf"]))))                ;; README.md
    (testing "a low-threshold scan surfaces the trivial source file"
      (let [r2 (b/scan-workspace files 20)]
        (is (some #(= "src/a.py" (:path %)) (:prune-candidates r2)))))
    (testing "the default-threshold scan keeps the report shape"
      (is (contains? r :growth-score))
      (is (vector? (:prune-candidates r))))))

(deftest growth-health-thresholds
  (is (= :healthy       (b/growth-health {:growth-score 70})))
  (is (= :healthy       (b/growth-health {:growth-score 100})))
  (is (= :needs-pruning (b/growth-health {:growth-score 40})))
  (is (= :overgrown     (b/growth-health {:growth-score 0}))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-bonsai)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
