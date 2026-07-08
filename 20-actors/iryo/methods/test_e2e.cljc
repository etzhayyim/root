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

;; ── karute -> iryo hand-off boundary (agent.cljc wiring; karute/MATURITY.md #11) ──

(deftest test-handle-ingest-billing-is-wired-through-agent
  (let [request {"patientDid" "did:web:patient.iryo.etzhayyim.com:e2e1"
                 "encounterDid" "at://did:web:karute.etzhayyim.com/com.etzhayyim.karute.encounter/enc1"
                 "facilityDid" "did:web:clinic-example.etzhayyim.com"
                 "consentCapabilityUri" "at://did:web:patient.iryo.etzhayyim.com:e2e1/com.etzhayyim.consent.capability/cap1"}
        capability {"granterDid" "did:web:patient.iryo.etzhayyim.com:e2e1"
                    "granteeDid" "did:web:iryo.etzhayyim.com"
                    "purpose" "insurance-billing"
                    "scope" ["com.etzhayyim.karute.encounter"]
                    "expiresAt" "2026-08-01T00:00:00Z"}
        out (agent/handle-ingest-billing (assoc request "capability" capability "now" "2026-07-08T00:00:00Z"))]
    (is (= true (get out "ack")))
    (is (= "pending" (get out "iryoStatus")))
    (is (.startsWith (str (get out "iryoClaimRef")) "iryo-req-"))))
