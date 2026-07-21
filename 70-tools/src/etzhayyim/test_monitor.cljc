;; etzhayyim.test-monitor — monitor scoring/analysis pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure scoring/analysis/format helpers (HTTP/firehose legs deferred):
;; compute-shinka-score · coverage-grade · tier-score · normalize-domain-lookup ·
;; extract-collection-literals · extract-sub-did-paths · gate-check · format-health-line.
(ns etzhayyim.test-monitor
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.monitor :as mon]))

(deftest shinka-score-rules
  (is (= 45 (mon/compute-shinka-score {:has-joucho true :has-inbox true})))   ;; 30+15
  (is (= 0 (mon/compute-shinka-score {})))
  (is (= 0 (mon/compute-shinka-score {:has-old-timer true})))                  ;; -30 floored
  (testing "all capabilities (no old-timer) = 100"
    (is (= 100 (mon/compute-shinka-score
                {:has-joucho true :has-inbox true :has-cadence true :has-drill true
                 :has-validate true :has-analyze true :has-engage true}))))
  (testing "old-timer penalty subtracts 30"
    (is (= 70 (mon/compute-shinka-score
               {:has-joucho true :has-inbox true :has-cadence true :has-drill true
                :has-validate true :has-analyze true :has-engage true :has-old-timer true})))))

(deftest coverage-grade-bands
  (is (= "S" (mon/coverage-grade 80)))
  (is (= "A" (mon/coverage-grade 60)))
  (is (= "B" (mon/coverage-grade 40)))
  (is (= "C" (mon/coverage-grade 20)))
  (is (= "D" (mon/coverage-grade 19))))

(deftest tier-score-ramp
  (is (= 0.0 (mon/tier-score 0 10 20 30)))
  (is (= 100.0 (mon/tier-score 30 10 20 30)))     ;; >= t3
  (is (= 10.0 (mon/tier-score 5 10 20 30)))        ;; 0..t1: 20·(5/10)
  (is (= 40.0 (mon/tier-score 15 10 20 30)))       ;; t1..t2: 20 + 40·0.5
  (is (= 80.0 (mon/tier-score 25 10 20 30))))      ;; t2..t3: 60 + 40·0.5

(deftest domain-and-source-analysis
  (is (= "my_domain" (mon/normalize-domain-lookup "  my-domain ")))
  (testing "collection literals filtered by ns-candidate prefix"
    (is (= ["com.etzhayyim.apps.cargo.profile"]
           (mon/extract-collection-literals "x \"com.etzhayyim.apps.cargo.profile\" y" ["cargo"])))
    (is (= [] (mon/extract-collection-literals "\"com.etzhayyim.apps.other.x\"" ["cargo"])))
    (testing "no candidates → accept all matches"
      (is (= ["com.etzhayyim.apps.cargo.x"]
             (mon/extract-collection-literals "\"com.etzhayyim.apps.cargo.x\"" [])))))
  (testing "sub-did path declarations, de-duplicated in order"
    (is (= ["/a" "/b"] (mon/extract-sub-did-paths "path: \"/a\" path: \"/b\" path: \"/a\"")))))

(deftest gate-check-regression
  (testing "no regression → empty failure list"
    (is (= [] (mon/gate-check {:avg-score 50 :prev-avg 50 :top10-avg 80 :prev-top10 80
                               :low-count 2 :prev-low 2
                               :max-avg-drop 3.0 :max-top10-drop 5.0 :max-low-increase 5}))))
  (testing "avg score drop beyond threshold → one failure"
    (let [fs (mon/gate-check {:avg-score 40 :prev-avg 50 :max-avg-drop 3.0
                              :max-top10-drop 5.0 :max-low-increase 5})]
      (is (= 1 (count fs)))
      (is (re-find #"avg_hyoka drop" (first fs))))))

(deftest health-line-display
  (is (= "  [OK  ] /h  200  12ms"
         (mon/format-health-line {:path "/h" :ok true :status 200 :latency-ms 12})))
  (is (= "  [FAIL] /h  500  error=boom"
         (mon/format-health-line {:path "/h" :ok false :status 500 :error "boom"}))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-monitor)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
