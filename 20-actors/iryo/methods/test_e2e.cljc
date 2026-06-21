(ns iryo.methods.test-e2e
  (:require [clojure.test :refer [deftest is]]
            [iryo.methods.agent :as agent]
            [cheshire.core :as json]))

(def ENCOUNTER
  {"futanWari" 0.3
   "acts" [{"code" "111000110" "count" 1}
           {"code" "112011010" "count" 1}
           {"code" "160008010" "count" 1}
           {"code" "160019410" "count" 1}]
   "prescriptions" [{"shikibetsu" "21" "days" 14
                     "drugs" [{"code" "620003991" "amount" 2}]}]})

(def KARTE
  {"patient" {"pseudonymDid" "did:web:patient.iryo.etzhayyim.com:e2e1"
              "sex" "F" "birthYear" 1975}
   "insurance" {"hokenshaBango" "06270013" "futanWari" 0.3
                "honninKazoku" "honnin" "kogakuKubun" "ウ"}
   "diagnoses" [{"shobyoCode" "2500013" "icd10" "E119" "name" "2型糖尿病"
                 "onset" "2025-04-01" "outcome" "継続" "isMain" true}
                {"shobyoCode" "4019005" "icd10" "I10" "name" "高血圧症"
                 "onset" "2025-04-01" "outcome" "継続"}]})

(deftest test-handle-rezept-computes-kubun-totals
  (let [out (agent/handle-rezept {"encounter" ENCOUNTER})
        r (get out "result")]
    (is (= 291 (get-in r ["kubunTotals" "初診"])))
    (is (= 52 (get-in r ["kubunTotals" "再診"])))
    (is (= 70 (get-in r ["kubunTotals" "検査"])))
    (is (= 28 (get-in r ["kubunTotals" "投薬"])))
    (is (= (get r "totalTen")
           (+ (get-in r ["kubunTotals" "初診"])
              (get-in r ["kubunTotals" "再診"])
              (get-in r ["kubunTotals" "検査"])
              (get-in r ["kubunTotals" "投薬"]))))
    (is (= (get r "totalIryohiYen") (* (get r "totalTen") 10)))
    (is (.startsWith (str (get out "intent")) "member-principal"))))

(deftest test-handle-receden-draft-phi-free
  (let [out (agent/handle-receden {"encounter" ENCOUNTER "karte" KARTE
                                   "shinryoYear" 2026 "shinryoMonth" 6})]
    (is (= "draft" (get out "state")))
    (is (= 2 (get-in out ["summary" "SY"])))
    (is (= 1 (get-in out ["summary" "IY"])))
    (is (not (.contains (str (get out "csv")) "1975")))))

(deftest test-handle-validate-flags-and-passes
  (let [out (agent/handle-validate {"encounter" ENCOUNTER "karte" KARTE})
        codes (set (map #(get % "code") (get out "observations")))]
    (is (not (contains? codes "NO_DIAGNOSIS")))
    (is (= true (get out "ok")))))

(deftest test-validate-flags-rx-without-diagnosis
  (let [karte-no-dx (assoc KARTE "diagnoses" [])
        out (agent/handle-validate {"encounter" ENCOUNTER "karte" karte-no-dx})
        codes (set (map #(get % "code") (get out "observations")))]
    (is (or (contains? codes "RX_WITHOUT_DX") (contains? codes "NO_DIAGNOSIS")))
    (is (= false (get out "ok")))))

(deftest test-export-fhir-bundle-is-codes-only
  (let [out (agent/export-fhir {"encounter" ENCOUNTER "karte" KARTE})
        bundle (get out "bundle")]
    (is (= "Bundle" (get bundle "resourceType")))
    (let [types (set (map #(get-in % ["resource" "resourceType"]) (get bundle "entry")))]
      (is (contains? types "Coverage"))
      (is (contains? types "Condition"))
      (is (contains? types "Claim")))
    (let [claim (first (filter #(= "Claim" (get-in % ["resource" "resourceType"])) (get bundle "entry")))]
      (is (= "点" (get-in claim ["resource" "total" "unit"]))))
    (let [bundle-str (json/generate-string bundle)]
      (is (not (.contains bundle-str "1975"))))))
