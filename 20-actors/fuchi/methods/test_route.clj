;; test_route.clj — 扶持 route: in-kind rail decomposition + governance routing, parity with
;; route.py. Run via `bb test:fuchi`. ADR-2606142300.
(ns fuchi.methods.test-route
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [fuchi.methods.route :as r]))

(def ^:private envelope
  [{:envelope/line :housing   :envelope/imputed-usd-micros-yr 12000000000}
   {:envelope/line :food      :envelope/imputed-usd-micros-yr 6000000000}
   {:envelope/line :liquidity :envelope/imputed-usd-micros-yr 2000000000}])

(deftest envelope-decomposition
  (testing "envelope lines → in-kind rails over existing actors (golden from route.py)"
    (let [rails (r/route-envelope envelope)]
      (is (= [["housing-commons" "commons-land" false]
              ["food-mitsuho" "mitsuho" false]
              ["liquidity-warifu" "warifu" true]]                  ; liquidity = MEMBER-PRINCIPAL
             (mapv (juxt :kind :provider-actor :member-principal) rails)))
      (is (= [12000000000 6000000000 2000000000] (mapv :imputed-usd-micros-yr rails))))))

(deftest cash-unrepresentable
  (testing "cash≡0 — a cash/stipend rail or non-zero cash-micros RAISES; unknown line raises"
    (is (thrown? Exception (r/route-envelope [{:envelope/line :cash}])))
    (is (thrown? Exception (r/route-envelope [{:envelope/line :stipend}])))
    (is (thrown? Exception (r/route-envelope [{:envelope/line :housing :envelope/cash-usd-micros 5}])))
    (is (thrown? Exception (r/route-envelope [{:envelope/line :unknown-need}])))))

(deftest in-kind-coverage-metric
  (testing "fraction delivered in-kind (member-principal liquidity excluded), round 4"
    (is (== 0.9 (r/in-kind-coverage (r/route-envelope envelope))))   ; 18e9 / 20e9
    (is (== 1.0 (r/in-kind-coverage [])))                            ; empty → 1.0
    (is (== 1.0 (r/in-kind-coverage [{:imputed-usd-micros-yr 0 :member-principal false}])))))  ; total 0

(deftest governance-routing
  (testing "gov-route is a pure function of (total, invariant-touch, rider) — 非裁定"
    (is (= "auto"        (r/gov-route 1000 false "")))
    (is (= "sbt-vote"    (r/gov-route 25000000000 false "")))         ; above ceiling
    (is (= "council-lv7" (r/gov-route 1000 true "")))                 ; invariant touch
    (is (= "refused"     (r/gov-route 1000 false "advertis")))        ; rider hit
    (is (= "refused"     (r/gov-route 99999999999 true "weapon")))))  ; rider beats all

(deftest rider-and-invariant-scan
  (testing "rider-hit returns the matched token; touches-invariant flags constitutional contexts"
    (is (= "advertis" (r/rider-hit "buy ad space advertis here")))
    (is (= "weapon"   (r/rider-hit "this is a weapon system")))
    (is (= ""         (r/rider-hit "housing food energy")))
    (is (true?  (r/touches-invariant "new commons-land grant")))
    (is (true?  (r/touches-invariant "a charter amendment")))
    (is (false? (r/touches-invariant "food and energy")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'fuchi.methods.test-route)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
