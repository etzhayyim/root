(ns noroshi.methods.test-pic-layout
  "Tests for the noroshi photonic-IC layout generator (ADR-2606051600).
  1:1 Clojure port of methods/test_pic_layout.py (pytest → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [noroshi.methods.link-budget :as lb]
            [noroshi.methods.pic-layout :as P]))

(deftest test-transmitter-plan-has-expected-components
  (let [plan (P/transmitter-plan)]
    (is (= (set (get plan "components")) #{"laser0" "mzm0" "gc0"}))
    (is (= (count (filter #(= (get % "op") "route") (get plan "ops"))) 2))))

(deftest test-total-waveguide-is-sum-of-routes
  (let [plan (P/transmitter-plan "noroshi-tx-pic" 1500.0)]
    (is (= (get plan "total_waveguide_um") (+ 200.0 1500.0)))))

(deftest test-layout-feeds-link-budget-and-closes
  (let [plan (P/transmitter-plan)
        budget (lb/compute (P/plan-to-link-design plan))]
    (is (get budget "closes"))))

(deftest test-longer-routing-lowers-margin
  (let [short (lb/compute (P/plan-to-link-design (P/transmitter-plan "noroshi-tx-pic" 500.0)))
        long  (lb/compute (P/plan-to-link-design (P/transmitter-plan "noroshi-tx-pic" 5000.0)))]
    (is (< (get long "margin_db") (get short "margin_db")))))

(deftest test-gds-build-is-gated-or-built
  (let [plan (P/transmitter-plan)
        res (P/try-build-gds plan)]
    (is (contains? #{true false} (get res "built")))
    (when-not (get res "built")
      (is (or (str/includes? (get res "reason") "gated") (str/includes? (get res "reason") "not available"))))))

(deftest test-report-renders-open-eda-framing
  (let [txt (P/report)]
    (is (str/includes? txt "ModelOp"))
    (is (or (str/includes? txt "open-EDA") (str/includes? txt "gdsfactory")))
    (is (or (str/includes? txt "G1") (str/includes? (str/lower-case txt) "no proprietary eda") (str/includes? txt "NDA")))))

(deftest test-non-positive-route-length-rejected
  (is (thrown? #?(:clj Exception :cljs js/Error) (P/transmitter-plan "noroshi-tx-pic" 0.0)))
  (is (thrown? #?(:clj Exception :cljs js/Error) (P/transmitter-plan "noroshi-tx-pic" -100.0))))

(deftest test-plan-to-link-design-uses-custom-base-rx-waveguide
  (let [plan (P/transmitter-plan)
        d (P/plan-to-link-design plan (lb/link-design :rx_waveguide_cm 3.0))]
    (is (= (get d "rx_waveguide_cm") 3.0))
    (is (= (get d "tx_waveguide_cm") (/ (get plan "total_waveguide_um") 1e4)))))

(deftest test-routes-carry-port-pairs
  (let [plan (P/transmitter-plan)
        routes (filter #(= (get % "op") "route") (get plan "ops"))]
    (is (every? #(= (count (get % "ports")) 2) routes))
    (is (= (get (last routes) "ports") ["mzm0.o" "gc0.i"]))))

(deftest test-receiver-plan-has-coupler-and-photodetector
  (let [rx (P/receiver-plan)
        routes (filter #(= (get % "op") "route") (get rx "ops"))]
    (is (= (set (get rx "components")) #{"gc_in" "pd0"}))
    (is (= (count routes) 1))
    (is (= (get (first routes) "ports") ["gc_in.o" "pd0.i"]))))

(deftest test-receiver-plan-rejects-non-positive-route
  (is (thrown? #?(:clj Exception :cljs js/Error) (P/receiver-plan "noroshi-rx-pic" 0.0))))

(deftest test-full-link-design-uses-both-waveguides
  (let [tx (P/transmitter-plan) rx (P/receiver-plan)
        d (P/full-link-design tx rx)]
    (is (= (get d "tx_waveguide_cm") (/ (get tx "total_waveguide_um") 1e4)))
    (is (= (get d "rx_waveguide_cm") (/ (get rx "total_waveguide_um") 1e4)))))

(deftest test-full-link-closes-and-longer-rx-lowers-margin
  (let [tx (P/transmitter-plan)
        short (lb/compute (P/full-link-design tx (P/receiver-plan "noroshi-rx-pic" 500.0)))
        long  (lb/compute (P/full-link-design tx (P/receiver-plan "noroshi-rx-pic" 8000.0)))]
    (is (get short "closes"))
    (is (< (get long "margin_db") (get short "margin_db")))))

(deftest test-report-mentions-receiver-and-end-to-end
  (let [txt (P/report)]
    (is (str/includes? txt "receiver plan"))
    (is (str/includes? txt "end-to-end"))))

#?(:clj (defn -main [& _] (run-tests 'noroshi.methods.test-pic-layout)))
