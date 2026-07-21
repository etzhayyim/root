;; etzhayyim.test-code-quality — code-quality pure-helper invariants (cljc port).
;; Run: bb test:code-quality
;; Covers the pure scoring / parsing helpers (everything before the #?(:clj) IO
;; section): cap · overall-score · make-check · build-report · parse-*-output ·
;; score-sql-injection — mirroring the Python check_* command bodies.
(ns etzhayyim.test-code-quality
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.code-quality :as cq]))

(deftest cap-clamps
  (is (= 100.0 (cq/cap 150)))
  (is (= 0.0 (cq/cap -5)))
  (is (= 50.0 (cq/cap 50))))

(deftest overall-score-averages-available
  (testing "average over available + error-free checks"
    (is (= 70.0 (cq/overall-score [{:available true :error "" :score 80}
                                   {:available true :error "" :score 60}]))))
  (testing "unavailable / errored checks are excluded"
    (is (= 80.0 (cq/overall-score [{:available true :error "" :score 80}
                                   {:available false :error "" :score 0}
                                   {:available true :error "boom" :score 10}]))))
  (testing "none available → 0.0"
    (is (= 0.0 (cq/overall-score [])))
    (is (= 0.0 (cq/overall-score [{:available false :error "" :score 99}])))))

(deftest make-check-shape
  (testing "2-arity defaults"
    (is (= {:name "n" :tool "t" :available true :score 0.0 :issues 0 :details "" :error ""}
           (cq/make-check "n" "t"))))
  (testing "7-arity coerces score to double, nil error → \"\""
    (let [c (cq/make-check "n" "t" false 88 3 "d" nil)]
      (is (= 88.0 (:score c)))
      (is (= "" (:error c))))))

(deftest build-report-counts
  (let [r (cq/build-report [(cq/make-check "a" "ta" true 80 0 "" "")
                            (cq/make-check "b" "tb" true 60 0 "" "")
                            (cq/make-check "c" "tc" false 0 0 "" "")])]
    (is (= 2 (:available-tools r)))
    (is (= 1 (:skipped-tools r)))
    (is (= 700 (:overall-score r)))))  ;; round(70.0 * 10)

(deftest parse-machete
  (is (= {:unused-count 2 :details "2 unused dependencies"}
         (cq/parse-machete-output "\tfoo\n\tbar\nclean line")))
  (is (= {:unused-count 0 :details ""} (cq/parse-machete-output "no unused here"))))

(deftest parse-dup-crate
  (testing "distinct crate names matching '<name> v...' are counted"
    (is (= {:dup-count 2} (cq/parse-dup-crate-output "foo v1.0\nfoo v2.0\nbar v1.0")))
    (is (= {:dup-count 0} (cq/parse-dup-crate-output "no crates here")))))

(deftest parse-go-vet
  (testing "exit 0 → no issues"
    (is (= {:issues 0} (cq/parse-go-vet-output "anything" 0))))
  (testing "non-trivial lines counted; #, 'matched no packages', warnings skipped"
    (is (= {:issues 2}
           (cq/parse-go-vet-output
            "pkg: issue1\npkg: issue2\n# comment\nmatched no packages\ngo: warning: x" 1)))))

(deftest parse-go-mod-tidy
  (is (= {:dirty false} (cq/parse-go-mod-tidy-output "" 0)))
  (is (= {:dirty true}  (cq/parse-go-mod-tidy-output "some diff" 0)))
  (is (= {:dirty true}  (cq/parse-go-mod-tidy-output "" 1))))

(deftest score-sql-injection-detects
  (testing "clean content scores 100"
    (let [r (cq/score-sql-injection "const safe = 1;")]
      (is (= 100.0 (:score r)))
      (is (= 0 (:issues r)))))
  (testing "esc-interpolation + template-sql patterns score 0"
    (let [r (cq/score-sql-injection "x ${esc(foo)} y \"${bar}\" z")]
      (is (= 0.0 (:score r)))
      (is (= 2 (:issues r))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-code-quality)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
