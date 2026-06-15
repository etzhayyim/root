;; test_crosscheck.clj — uchiwake⇄kabuto coverage-linkage crosscheck, byte-parity with crosscheck.py.
;; Auto-discovered by `bb test:actors` (path-matching ns). ADR-2606142300.
(ns uchiwake.methods.test-crosscheck
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [uchiwake.methods.crosscheck :as cc]))

(def ^:private s (cc/crosscheck))

(deftest linkage-headline
  (testing "measured uchiwake→kabuto linkage matches crosscheck.py exactly (golden)"
    (is (true? (:kabuto-available s)))
    (is (= 1719 (:kabuto-company-count s)))
    (is (= 26 (:distinct-company-refs s)))
    (is (= 21 (:distinct-resolved s)))
    (is (== 80.8 (:linkage-pct s)))))                       ; round(100*21/26, 1)

(deftest by-kind-counts
  (testing "per-reference-kind total/resolved (golden)"
    (is (= {:total 10 :resolved 8}  (get-in s [:by-kind "brand-owner"])))
    (is (= {:total 15 :resolved 14} (get-in s [:by-kind "bom-supplier"])))
    (is (= {:total 4  :resolved 4}  (get-in s [:by-kind "process-operator"])))
    (is (= {:total 2  :resolved 2}  (get-in s [:by-kind "logistics-carrier"])))
    (is (= {:total 3  :resolved 0}  (get-in s [:by-kind "ownership-child"])))
    (is (= {:total 3  :resolved 1}  (get-in s [:by-kind "ownership-parent"])))))

(deftest ownership-rollup-and-gap
  (testing "子会社 rollup recovers a subsidiary→ultimate-parent link; unresolved is the honest gap (G5)"
    (is (= [{:ref "org.corp.jp.sony-semicon" :ultimate "org.corp.jp.sony" :kind "bom-supplier"}
            {:ref "org.corp.jp.sony-semicon" :ultimate "org.corp.jp.sony" :kind "ownership-child"}]
           (:rollup-recovered s)))
    (is (= ["org.corp.it.ferrero" "org.corp.jp.sony-semicon" "org.corp.lu.ferrero-intl"
            "org.corp.us.coca-cola" "org.corp.us.coca-cola-na"]
           (:unresolved s)))))

(deftest reverse-coverage
  (testing "reverse coverage (how much of kabuto has product-level BOM detail) — the honest figure"
    (let [r (:reverse s)]
      (is (= 233 (:kabuto-supply-companies r)))
      (is (= 15 (:with-product-detail r)))
      (is (== 6.438 (:reverse-pct r)))                      ; round(100*15/233, 3)
      (is (== 1.163 (:all-company-coverage-pct r)))         ; round(100*covered/1719, 3)
      ;; worklist = top-15 highest-out-degree kabuto suppliers with NO product detail.
      ;; assert length + that the top entry has the max out-degree (tie-order is impl-specific).
      (is (= 15 (count (:worklist r))))
      (is (= 3 (:supply-out-degree (first (:worklist r)))))
      (is (apply >= (map :supply-out-degree (:worklist r)))))))   ; worklist sorted desc by out-degree

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'uchiwake.methods.test-crosscheck)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
