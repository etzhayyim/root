(ns scripts.bench.langgraph-coding.test-diff
  "clojure.test suite for the diff.cljc pure delta computation. Exercises the
  pure fns on synthetic before/after result maps (improvement / regression /
  no-change / per-task breakdown) and asserts the computed deltas + overall
  pass-rate EXACTLY match the Python arithmetic (diff.py)."
  (:require [clojure.test :refer [deftest is testing]]
            [scripts.bench.langgraph-coding.diff :as d]))

;; synthetic result rows (string JSON keys, as the files carry)
(defn row [id passed cat] {"id" id "passed" passed "category" cat})

(deftest passed->int-parity
  (testing "int(row[\"passed\"]) parity"
    (is (= 1 (d/passed?->int true)))
    (is (= 0 (d/passed?->int false)))
    (is (= 1 (d/passed?->int 1)))
    (is (= 0 (d/passed?->int 0)))
    (is (= 0 (d/passed?->int nil)))))

(deftest fmt-pp-parity
  (testing "f\"{x:+.1f}\" — sign + 1 decimal + ties-to-even"
    (is (= "+0.0"  (d/fmt-pp 0.0)))
    (is (= "+33.3" (d/fmt-pp (/ (* 100.0 1) 3))))     ; 100*1/3
    (is (= "-33.3" (d/fmt-pp (/ (* 100.0 -1) 3))))
    (is (= "+50.0" (d/fmt-pp 50.0)))
    (is (= "-16.7" (d/fmt-pp -16.6666)))
    (is (= "+6.2"  (d/fmt-pp (/ 100.0 16))))          ; 6.25 → 6.2 (even)
    (is (= "+18.8" (d/fmt-pp (/ (* 100.0 3) 16))))))  ; 18.75 → 18.8 (even)

(deftest overall-improvement
  (testing "improvement: 1/4 → 3/4, delta +50.0pp"
    (let [base (d/index-by-id [(row "a" true  "x") (row "b" false "x")
                               (row "c" false "y") (row "d" false "y")])
          new  (d/index-by-id [(row "a" true  "x") (row "b" true  "x")
                               (row "c" true  "y") (row "d" false "y")])
          common (d/common-ids base new)
          o (d/overall-delta base new common)]
      (is (= 1 (:base-pass o)))
      (is (= 3 (:new-pass o)))
      (is (= 4 (:n o)))
      (is (= 50.0 (:delta-pp o)))
      (is (= "+50.0" (d/fmt-pp (:delta-pp o)))))))

(deftest overall-regression
  (testing "regression: 3/4 → 1/4, delta -50.0pp"
    (let [base (d/index-by-id [(row "a" true  "x") (row "b" true  "x")
                               (row "c" true  "y") (row "d" false "y")])
          new  (d/index-by-id [(row "a" true  "x") (row "b" false "x")
                               (row "c" false "y") (row "d" false "y")])
          o (d/overall-delta base new (d/common-ids base new))]
      (is (= 3 (:base-pass o)))
      (is (= 1 (:new-pass o)))
      (is (= -50.0 (:delta-pp o)))
      (is (= "-50.0" (d/fmt-pp (:delta-pp o)))))))

(deftest overall-no-change
  (testing "no change: 2/4 → 2/4, delta +0.0pp"
    (let [base (d/index-by-id [(row "a" true  "x") (row "b" false "x")
                               (row "c" true  "y") (row "d" false "y")])
          new  (d/index-by-id [(row "a" true  "x") (row "b" false "x")
                               (row "c" true  "y") (row "d" false "y")])
          o (d/overall-delta base new (d/common-ids base new))]
      (is (= 2 (:base-pass o)))
      (is (= 2 (:new-pass o)))
      (is (= 0.0 (:delta-pp o)))
      (is (= "+0.0" (d/fmt-pp (:delta-pp o)))))))

(deftest per-category-breakdown
  (testing "by-category: cats x and y track base/new/total separately"
    (let [base (d/index-by-id [(row "a" true  "x") (row "b" false "x")
                               (row "c" false "y") (row "d" false "y")])
          new  (d/index-by-id [(row "a" true  "x") (row "b" true  "x")
                               (row "c" true  "y") (row "d" false "y")])
          cats (d/by-category base new (d/common-ids base new))]
      (is (= {:base 1 :new 2 :total 2} (get cats "x")))
      (is (= {:base 0 :new 1 :total 2} (get cats "y")))
      ;; per-cat delta arithmetic: x +50.0pp, y +50.0pp
      (is (= "+50.0" (d/fmt-pp (/ (* 100.0 (- 2 1)) 2))))
      (is (= "+50.0" (d/fmt-pp (/ (* 100.0 (- 1 0)) 2)))))))

(deftest category-default-question-mark
  (testing "missing category defaults to \"?\" (mirrors .get(\"category\",\"?\"))"
    (let [base (d/index-by-id [{"id" "a" "passed" false}])
          new  (d/index-by-id [{"id" "a" "passed" true}])
          cats (d/by-category base new (d/common-ids base new))]
      (is (= {:base 0 :new 1 :total 1} (get cats "?"))))))

(deftest report-improvement-lines
  (testing "diff-report exit 0 + exact overall + per-cat report lines"
    (let [base (d/index-by-id [(row "t1" true  "easy") (row "t2" false "easy")
                               (row "t3" false "hard") (row "t4" false "hard")])
          new  (d/index-by-id [(row "t1" true  "easy") (row "t2" true  "easy")
                               (row "t3" true  "hard") (row "t4" false "hard")])
          {:keys [exit out err]} (d/diff-report base new 0.0)]
      (is (= 0 exit))
      (is (empty? err))
      (is (= "overall: baseline=1/4 new=3/4 delta=+50.0pp" (first out)))
      ;; sorted by category: easy before hard
      (is (= "  easy                : 1/2 → 2/2  (+50.0pp)" (nth out 1)))
      (is (= "  hard                : 0/2 → 1/2  (+50.0pp)" (nth out 2))))))

(deftest report-no-overlap
  (testing "no common ids → exit 2 + stderr line"
    (let [base (d/index-by-id [(row "a" true "x")])
          new  (d/index-by-id [(row "b" true "x")])
          {:keys [exit out err]} (d/diff-report base new 0.0)]
      (is (= 2 exit))
      (is (empty? out))
      (is (= ["[diff] no overlap between baseline and new"] err)))))

(deftest report-gate-fail
  (testing "regression below gate → exit 1 + GATE FAIL stderr"
    (let [base (d/index-by-id [(row "a" true "x") (row "b" true "x")])
          new  (d/index-by-id [(row "a" true "x") (row "b" false "x")])
          {:keys [exit err]} (d/diff-report base new 0.0)]
      (is (= 1 exit))
      (is (= ["\nGATE FAIL: delta -50.0pp < required 0.0pp"] err)))))

(deftest report-gate-pass-at-threshold
  (testing "delta == gate-pp is NOT a fail (Python `delta_pp < gate_pp`)"
    (let [base (d/index-by-id [(row "a" true "x") (row "b" false "x")])
          new  (d/index-by-id [(row "a" true "x") (row "b" false "x")])
          {:keys [exit]} (d/diff-report base new 0.0)]
      (is (= 0 exit)))))
