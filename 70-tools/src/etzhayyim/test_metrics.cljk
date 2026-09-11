;; etzhayyim.test-metrics — metrics pure-helper invariants (cljc port; IO-free).
;; Run: bb test:metrics
;; Covers window-valid? · metrics-nsid · metrics-url · parse-latency/throughput/errors ·
;; format-summary · format-latency.
(ns etzhayyim.test-metrics
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.metrics :as m]))

(deftest window-validity
  (is (true? (m/window-valid? "1h")))
  (is (true? (m/window-valid? "  24h  ")))    ;; trimmed
  (is (false? (m/window-valid? "99x")))
  (is (false? (m/window-valid? "")))
  (is (false? (m/window-valid? nil))))

(deftest nsid-and-url
  (is (= "com.etzhayyim.metrics.getLatency" (m/metrics-nsid :latency)))
  (is (nil? (m/metrics-nsid :nope)))
  (is (= "https://pds.example/xrpc/com.etzhayyim.metrics.getSummary"
         (m/metrics-url "https://pds.example/" :summary)))
  (is (nil? (m/metrics-url "https://pds.example" :nope))))

(deftest response-parsers
  (is (= {:p50 10 :p95 20 :p99 30} (m/parse-latency {"p50" 10 "p95" 20 "p99" 30})))
  (is (= {:p50 nil :p95 nil :p99 nil} (m/parse-latency {})))
  (is (= {:rps 5 :rpm 300 :total 1000} (m/parse-throughput {"rps" 5 "rpm" 300 "total" 1000})))
  (is (= {:error-rate 0.01 :top-errors ["500"] :total-reqs 100}
         (m/parse-errors {"errorRate" 0.01 "topErrors" ["500"] "totalRequests" 100})))
  (is (= [] (:top-errors (m/parse-errors {})))))

(deftest formatters
  (testing "summary sorted by key into 'key: value' lines"
    (is (= ["  a: 1" "  b: 2"] (m/format-summary {"b" 2 "a" 1}))))
  (testing "latency: header + only the present percentiles"
    (is (= ["latency (1h):" "  p50: 10ms" "  p95: 20ms" "  p99: 30ms"]
           (m/format-latency {:p50 10 :p95 20 :p99 30} "1h")))
    (is (= ["latency (24h):" "  p50: 10ms"]
           (m/format-latency {:p50 10} "24h")))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-metrics)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
