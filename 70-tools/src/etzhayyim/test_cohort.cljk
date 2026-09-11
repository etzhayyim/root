;; etzhayyim.test-cohort — cohort pure-helper invariants (cljc port).
;; Run: bb test:cohort
;; Covers the pure analytics helpers (IO fns take an injectable :http-fn / :read-fn):
;; build-gen-segment · compute-dashboard · build-coverage-matrix · find-gaps ·
;; compute-snapshot-agg · diff-snapshots · parse-segment-arg.
(ns etzhayyim.test-cohort
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.cohort :as cohort]))

(deftest gen-segment-shape
  (is (= {:pcf-l1 "L1" :role "eng" :industry "tech" :seniority "senior" :locale "en" :k 5}
         (cohort/build-gen-segment "L1" "eng" "tech" "senior" "en" 5))))

(deftest dashboard-stats
  (let [d (cohort/compute-dashboard
           [{:kind "fissioned" :pcfL1 "a" :role "r1" :locale "en"}
            {:kind "base"      :pcfL1 "a" :role "r2" :locale "en"}
            {:kind "base"      :pcfL1 "b" :role "r1" :locale "ja"}])]
    (is (= 3 (:total d)))
    (is (= 1 (:fissioned d)))
    (is (= 2 (:base d)))
    (is (< 0.33 (:fission-rate d) 0.34))
    (is (= 2 (:axis-pcf-l1 d)))    ;; {a b}
    (is (= 2 (:axis-role d)))      ;; {r1 r2}
    (is (= 2 (:axis-locale d)))))  ;; {en ja}

(deftest coverage-matrix-and-gaps
  (let [{:keys [matrix rows cols]}
        (cohort/build-coverage-matrix
         [{:role "r1" :pcfL1 "a"} {:role "r1" :pcfL1 "a"} {:role "r2" :pcfL1 "b"}]
         :role :pcfL1)]
    (testing "2D matrix grouped by row/col axis, sorted rows/cols"
      (is (= {"r1" {"a" 2} "r2" {"b" 1}} matrix))
      (is (= ["r1" "r2"] rows))
      (is (= ["a" "b"] cols)))
    (testing "find-gaps surfaces cells below min-count"
      (is (= [{:row "r1" :col "b" :count 0}]
             (cohort/find-gaps matrix ["r1"] cols 1))))))

(deftest snapshot-agg-by-axes
  (is (= {"r1|en" 2 "r2|ja" 1}
         (cohort/compute-snapshot-agg
          [{:role "r1" :locale "en"} {:role "r1" :locale "en"} {:role "r2" :locale "ja"}]
          [:role :locale]))))

(deftest diff-snapshots-delta
  (testing "keyword-keyed snapshots"
    (let [d (cohort/diff-snapshots {:total 10 :timestamp "t0"} {:total 15 :timestamp "t1"})]
      (is (= 5 (:delta d)))
      (is (= 10 (:from-total d)))
      (is (= "t1" (:to-ts d)))))
  (testing "string-keyed snapshots + negative delta"
    (is (= -2 (:delta (cohort/diff-snapshots {"total" 5} {"total" 3}))))))

(deftest parse-segment-arg-modes
  (testing "inline JSON is parsed"
    (is (= {:a 1} (cohort/parse-segment-arg "{\"a\":1}"))))
  (testing "@file uses the injected read-fn seam (no real IO)"
    (is (= {:b 2} (cohort/parse-segment-arg "@/some/path"
                                            {:read-fn (constantly "{\"b\":2}")}))))
  (testing "invalid / empty / nil input → nil (no throw)"
    (is (nil? (cohort/parse-segment-arg "not json")))
    (is (nil? (cohort/parse-segment-arg "")))
    (is (nil? (cohort/parse-segment-arg nil)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-cohort)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
