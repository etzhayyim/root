;; etzhayyim.test-bunseki — process-mining pure-helper invariants (cljc port).
;; Run: bb test:bunseki
;; Covers the pure OCEL/DFG helpers (no IO — the XRPC/CF-Analytics legs are
;; deferred): arch-grade · build-traces · build-dfg · analyze-variants ·
;; analyze-performance · check-conformance · compute-score.
(ns etzhayyim.test-bunseki
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.bunseki :as bun]))

(deftest arch-grade-bands
  (is (= "A" (bun/arch-grade 95)))
  (is (= "B" (bun/arch-grade 80)))
  (is (= "C" (bun/arch-grade 70)))
  (is (= "D" (bun/arch-grade 60)))
  (is (= "F" (bun/arch-grade 59))))

(deftest build-traces-grouping
  (testing "events group by auth key, in order"
    (is (= {"u1" ["login" "post"] "u2" ["login"]}
           (bun/build-traces [{:auth "u1" :activity "login"}
                              {:auth "u1" :activity "post"}
                              {:auth "u2" :activity "login"}]))))
  (testing "auth/activity fall back to :method"
    (is (= {"GET" ["GET"]}
           (bun/build-traces [{:method "GET"}]))))
  (testing "object-type filters events by :type"
    (is (= {"u1" ["a"]}
           (bun/build-traces [{:auth "u1" :activity "a" :type "post"}
                              {:auth "u1" :activity "b" :type "like"}]
                             "post")))))

(deftest build-dfg-counts
  (let [dfg (bun/build-dfg {"u1" ["a" "b" "c"] "u2" ["a" "b"]})]
    (testing "directly-follows pairs are counted, sorted by -count"
      (is (= {:from "a" :to "b"} (select-keys (first dfg) [:from :to])))
      (is (= 2 (:count (first dfg))))
      (is (= 2 (count dfg))))))      ;; a→b, b→c

(deftest analyze-variants-signatures
  (let [vs (bun/analyze-variants {"u1" ["a" "b"] "u2" ["a" "b"] "u3" ["a"]})]
    (is (= "a→b" (:variant (first vs))))
    (is (= 2 (:count (first vs))))
    (is (= 2 (count vs)))))

(deftest analyze-performance-p95-and-slow
  (let [perf (bun/analyze-performance
              [{:activity "x" :duration_ms 100} {:activity "x" :duration_ms 600}
               {:activity "y" :duration_ms 1000}])
        by (into {} (map (juxt :activity identity) perf))]
    (testing "sorted by -p95; slow flags activities with p95 > 500ms"
      (is (= "y" (:activity (first perf))))
      (is (true? (:slow (by "x"))))
      (is (true? (:slow (by "y"))))
      (is (= 2 (:count (by "x")))))))

(deftest check-conformance-deviations
  (testing "traces deviating from the most-common variant are flagged"
    (let [devs (bun/check-conformance {"u1" ["a" "b"] "u2" ["a" "b"] "u3" ["a" "c"]})]
      (is (= 1 (count devs)))
      (is (= "u3" (:trace_id (first devs))))
      (is (= "a→b" (:expected (first devs)))))))

(deftest compute-score-shape
  (let [events [{:activity "a" :duration_ms 10} {:activity "b" :duration_ms 20}]
        traces {"u1" ["a" "b"] "u2" ["a" "b"]}
        r (bun/compute-score events traces)]
    (is (number? (:score r)))
    (is (= 2 (:total_traces r)))
    (is (= 2 (:total_events r)))
    (is (= 100.0 (:conformance_rate_pct r)))   ;; both traces match the single variant
    (is (contains? r :slow_activities))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-bunseki)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
