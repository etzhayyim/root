(ns iryo.methods.agent
  (:require [iryo.methods.masters :as masters]
            [iryo.methods.rezept :as rezept]
            [iryo.methods.karte :as karte]
            [iryo.methods.receden :as receden]
            [iryo.methods.fhir :as fhir]
            [iryo.methods.handoff :as handoff]
            [clojure.string :as str]))

(def intent "member-principal-claim-substrate; non-adjudicating")

(defn- encounter-from [d]
  {:futan-wari (let [fw (get d "futanWari")] (when fw (double fw)))
   :kogaku-kubun (get d "kogakuKubun")
   :age (get d "age")
   :gen-eki (boolean (get d "genEki" false))
   :ittei-ijo (boolean (get d "itteiIjo" false))
   :nyuin (boolean (get d "nyuin" false))
   :kohi (mapv (fn [k] {"futanWari" (get k "futanWari" 0.0) "jikoFutanGendo" (get k "jikoFutanGendo")})
               (get d "kohi" []))
   :shokuji-meals (int (get d "shokujiMeals" 0))
   :shokuji-tanka-yen (int (get d "shokujiTankaYen" 490))
   :acts (mapv (fn [a] {:code (get a "code") :count (int (get a "count" 1))}) (get d "acts" []))
   :prescriptions (mapv (fn [p]
                          {:shikibetsu (get p "shikibetsu" "21")
                           :drugs (mapv (fn [x] {:code (get x "code") :amount (double (get x "amount" 1))})
                                        (get p "drugs" []))
                           :days (int (get p "days" 1))
                           :label (get p "label" "")})
                        (get d "prescriptions" []))
   :materials (mapv (fn [mt] {:code (get mt "code") :amount (double (get mt "amount" 1))
                               :shikibetsu (get mt "shikibetsu" "40")})
                    (get d "materials" []))})

(defn- karte-from [d]
  (let [p (get d "patient" {})
        ins (get d "insurance" {})]
    {:patient (karte/make-patient
               (get p "pseudonymDid" "did:web:patient.iryo.etzhayyim.com:anon")
               (get p "sex" "U")
               (get p "birthYear")
               (get p "encryptedPayloadCid"))
     :insurance (karte/make-insurance
                 (get ins "hokenshaBango" "00000000")
                 (double (get ins "futanWari" 0.3))
                 (get ins "honninKazoku" "honnin")
                 (get ins "kogakuKubun")
                 (get ins "kohi" []))
     :diagnoses (mapv (fn [x] (karte/make-diagnosis
                                (get x "shobyoCode") (get x "icd10" "") (get x "name" "")
                                (get x "onset") (get x "outcome" "継続") (boolean (get x "isMain" false))))
                      (get d "diagnoses" []))
     :notes []}))

(defn- get-masters [d]
  (if (get d "masters")
    (masters/from-dict (get d "masters"))
    (masters/load)))

(defn handle-rezept [state]
  (let [enc (encounter-from (get state "encounter"))
        m (get-masters state)
        rez (rezept/compute enc m)]
    {"result" (rezept/result->dict rez) "intent" intent}))

(defn handle-receden [state]
  (let [m (get-masters state)
        enc (encounter-from (get state "encounter"))
        kt (karte-from (get state "karte"))
        rez (rezept/compute enc m)
        inst-d (get state "institution" {})
        institution (receden/make-institution
                     (get inst-d "shinsaShiharai" "1")
                     (get inst-d "prefecture" "13")
                     :iryokikan-code (get inst-d "iryokikanCode" "1234567")
                     :name (get inst-d "name" ""))
        rows (receden/build-receden institution kt rez
                                    :shinryo-year (int (get state "shinryoYear" 2026))
                                    :shinryo-month (int (get state "shinryoMonth" 6))
                                    :jitsunissu (int (get state "jitsunissu" 1))
                                    :nyuin (boolean (get-in state ["encounter" "nyuin"] false))
                                    :tokki (get state "tokki")
                                    :comments (get state "comments")
                                    :shojo-shoki (get state "shojoShoki"))]
    {"records" rows
     "csv" (receden/to-csv rows)
     "summary" (receden/record-summary rows)
     "totalTen" (:total-ten rez)
     "patientPayYen" (:patient-pay-yen rez)
     "state" "draft"
     "intent" intent}))

(defn handle-validate [state]
  (let [m (get-masters state)
        enc (encounter-from (get state "encounter"))
        kt (karte-from (get state "karte"))
        rez (rezept/compute enc m)
        obs (atom [])]
    (when (empty? (:diagnoses kt))
      (swap! obs conj {"code" "NO_DIAGNOSIS" "msg" "傷病名が1件もない (投薬/検査の算定根拠を要確認)"}))
    (when (and (seq (:diagnoses kt)) (not-any? :is-main (:diagnoses kt)))
      (swap! obs conj {"code" "NO_MAIN_DIAGNOSIS" "msg" "主傷病が指定されていない"}))
    (when (zero? (:total-ten rez))
      (swap! obs conj {"code" "EMPTY_REZEPT" "msg" "算定点数が0 (空レセプト)"}))
    (when (and (seq (:prescriptions enc)) (empty? (:diagnoses kt)))
      (swap! obs conj {"code" "RX_WITHOUT_DX" "msg" "病名なしで投薬が算定されている"}))
    (when (:kogaku-applied rez)
      (swap! obs conj {"code" "KOGAKU_CAPPED"
                       "msg" (str "高額療養費適用: 窓口負担が限度額 " (:kogaku-limit-yen rez) "円 に調整された")}))
    (let [bad-codes #{"NO_DIAGNOSIS" "EMPTY_REZEPT" "RX_WITHOUT_DX"}]
      {"observations" @obs
       "ok" (not (some #(contains? bad-codes (get % "code")) @obs))
       "totalTen" (:total-ten rez)
       "intent" intent})))

(defn export-fhir [state]
  (let [m (get-masters state)
        enc (encounter-from (get state "encounter"))
        kt (karte-from (get state "karte"))
        rez (rezept/compute enc m)]
    {"bundle" (fhir/to-fhir-bundle kt rez) "intent" intent}))

(defn handle-ingest-billing [state]
  (handoff/handle-ingest state))
