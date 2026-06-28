(ns sheets.gitoffice-normalize-test
  "Tests for the sheets GitOffice edge adapter (clj port of
  tests/test_gitoffice_normalize.py). Parity fixtures identical to
  gitoffice.cljc / kotoba.gitoffice (drift guard)."
  (:require [clojure.test :refer [deftest is]]
            [sheets.gitoffice-normalize :as gn]))

(def sample-grid
  {"Sheet1" [["売上" "Q1" "Q2"]
             ["製品A" "100" "120"]
             ["製品B" "" "80"]]})

(deftest a1-roundtrip
  (is (= (gn/col->a1 0) "A"))
  (is (= (gn/col->a1 1) "B"))
  (is (= (gn/col->a1 25) "Z"))
  (is (= (gn/col->a1 26) "AA"))
  (is (= (gn/col->a1 27) "AB"))
  (doseq [c [0 1 25 26 27 51 52 700]]
    (is (= (gn/a1->col (gn/col->a1 c)) c)))
  (is (= (gn/cell-id "Sheet1" 1 1) "Sheet1!B2")))

(deftest grid-roundtrip-trimmed
  (let [ops (gn/grid->cell-ops "book1" sample-grid)
        rows (gn/ops->rows ops)
        out (gn/cells->grid rows "book1")
        expected {"Sheet1" (gn/trim-grid (get sample-grid "Sheet1"))}]
    (is (= out expected))))

(deftest cells-are-sparse
  (let [ops (gn/grid->cell-ops "book1" sample-grid)
        ids (set (map #(nth % 1) ops))]
    (is (not (contains? ids "Sheet1!B3")))  ;; the empty cell is not stored
    (is (contains? ids "Sheet1!C2"))))

(deftest trailing-empties-dropped
  (let [grid {"S" [["x" "" ""] ["" "" ""]]}
        rows (gn/ops->rows (gn/grid->cell-ops "bk" grid))]
    (is (= (gn/cells->grid rows "bk") {"S" [["x"]]}))))

(deftest value-preserved
  (let [ops (gn/grid->cell-ops "book1" sample-grid)
        rows (gn/ops->rows ops)
        vals (into {} (for [[e a v] rows :when (= (gn/bare a) "cell/value")] [e v]))]
    (is (= (get vals "Sheet1!C2") "120"))
    (is (= (get vals "Sheet1!A1") "売上"))))
