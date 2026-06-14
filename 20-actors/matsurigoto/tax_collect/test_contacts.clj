;; matsurigoto 政 — tax-collect / 連絡先 registry の conformance test。ADR-2606062300。
(ns matsurigoto.tax-collect.test-contacts
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [matsurigoto.tax-collect.contacts :as c]))

(def ^:private REG (c/load-registry))

(deftest central-contacts-authoritative
  (is (= "03-3581-4161" (:phone (c/national-tax-agency REG))) "国税庁代表")
  (is (= "100-8978" (:postal (c/national-tax-agency REG))))
  (is (= "0570-01-5901" (:phone (c/etax-helpdesk REG))) "e-Taxヘルプデスク")
  (is (= :authoritative (:provenance (c/national-tax-agency REG))))
  (is (= :authoritative (:provenance (c/etax-helpdesk REG)))))

(deftest bureau-routing-by-prefecture
  (is (= "東京国税局" (:ja (c/bureau-for-prefecture REG "東京"))))
  (is (= "東京国税局" (:ja (c/bureau-for-prefecture REG "神奈川"))) "神奈川は東京局管轄")
  (is (= "大阪国税局" (:ja (c/bureau-for-prefecture REG "大阪"))))
  (is (= "関東信越国税局" (:ja (c/bureau-for-prefecture REG "新潟"))))
  (is (= "沖縄国税事務所" (:ja (c/bureau-for-prefecture REG "沖縄"))))
  (is (nil? (c/bureau-for-prefecture REG "海外")) "未収載は nil"))

(deftest all-47-prefectures-mapped
  (let [covered (mapcat :prefectures (c/bureaus REG))]
    (is (= 47 (count covered)) "47都道府県すべてが国税局に対応")
    (is (= 47 (count (distinct covered))) "重複なし")))

(deftest contact-plan-shape
  (let [plan (c/contact-plan REG "東京")]
    (is (= "東京国税局" (get-in plan [:bureau :ja])))
    (is (= "法人課税(第一)部門" (get-in plan [:tax-office :division])) "源泉=法人課税部門")
    (is (= "0570-01-5901" (get-in plan [:etax-helpdesk :phone])))
    (is (nil? (:unresolved plan)))
    (testing "個別局電話は要確認と明示 (G5 honesty)"
      (is (= :pending-verification (get-in plan [:bureau :phone-provenance])))
      (is (= :pending-live-ingest (get-in plan [:tax-office :provenance])))))
  (testing "未収載都道府県は honest に unresolved"
    (is (some? (:unresolved (c/contact-plan REG "火星"))))))

(deftest coverage-is-honest
  (let [cov (c/coverage REG)]
    (is (= 12 (:bureaus cov)) "12局")
    (is (= 47 (:prefectures-covered cov)))
    (is (= 2 (:authoritative-phones cov)) "確証ある電話は中央2窓口のみ")
    (is (= :pending-verification (:bureau-phone-status cov)))))

(defn -main [& _]
  (let [r (run-tests 'matsurigoto.tax-collect.test-contacts)]
    (when (pos? (+ (:fail r) (:error r))) (System/exit 1))))
