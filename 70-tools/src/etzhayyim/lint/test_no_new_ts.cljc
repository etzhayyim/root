;; etzhayyim.lint.test-no-new-ts — no-new-ts gate invariants (ADR-2606251200 §Decision 6).
(ns etzhayyim.lint.test-no-new-ts
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.lint.no-new-ts :as l]))

(deftest baseline-diff-logic
  (testing "new-ts = present not in baseline (the violations)"
    (is (= ["b.ts"] (l/new-ts ["a.ts" "b.ts"] ["a.ts"])))
    (is (= [] (l/new-ts ["a.ts"] ["a.ts" "extra.ts"])))   ;; nothing new
    (is (= [] (l/new-ts [] []))))
  (testing "removed-ts = baseline no longer present (shrinks the baseline)"
    (is (= ["b.ts"] (l/removed-ts ["a.ts"] ["a.ts" "b.ts"])))
    (is (= [] (l/removed-ts ["a.ts" "b.ts"] ["a.ts"]))))
  (testing "results are sorted + deduped-by-set"
    (is (= ["a.ts" "b.ts" "c.ts"] (l/new-ts ["c.ts" "a.ts" "b.ts"] [])))))

(deftest pilot-stays-ts-free
  (testing "the explorer pilot currently has zero first-party .ts (live invariant)"
    (is (= [] (l/present-ts ["60-apps/etzhayyim-project-explorer"]))))
  (testing "present-ts excludes node_modules / build / .d.ts (no roots → empty, no crash)"
    (is (= [] (l/present-ts [])))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.lint.test-no-new-ts)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
