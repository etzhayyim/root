;; credential_issue.clj — matsurigoto 政 `credential-issue` module (R0 reference implementation).
;;
;; Clojure port of credential_issue.py (ADR-2606062300), Wave 1 of the clj-native migration
;; (ADR-2606142300). Travel-document / ID-credential engine behind passport.issue /
;; passport.renew / id.national.issue (パスポート発行): a pure-function ICAO Doc 9303 TD3 MRZ
;; (Machine Readable Zone) builder with the real 7-3-1 weighted check-digit. The ICAO 9303
;; worked example `L898902C3` → check `6`, DOB `740812` → `2` are reproduced exactly, and the
;; full ERIKSSON specimen line 2 is byte-identical with credential_issue.py. Produces the MRZ +
;; an UNSIGNED issuance record (the passport authority signs the SOD with its ICAO-PKD key, G1).
;;
;;   G1 no-operator-master-key : server-held-authority false; SOD + proof UNSIGNED here.
;;   G2 spec-derived-only      : ICAO 9303 MRZ structure + 7-3-1 check digit.
;;   G6 data-minimization      : only MRZ fields; no biometric template stored.
;;
;; stdlib only, no I/O, no network.
(ns matsurigoto.methods.modules.credential-issue
  (:require [clojure.string :as str]))

(def server-held-authority false)  ; G1
(def ^:private weights [7 3 1])

(defn- char-value
  "ICAO 9303 MRZ char value: digits = value, A-Z = 10..35, filler '<' = 0."
  [ch]
  (cond
    (= ch \<)               0
    (Character/isDigit ch)  (Character/digit ch 10)
    (and (>= (int ch) (int \A)) (<= (int ch) (int \Z))) (- (int ch) 55)
    :else (throw (ex-info (str "MRZ char must be [0-9A-Z<], got " (pr-str ch)) {:ch ch}))))

(defn mrz-check-digit
  "ICAO Doc 9303 check digit: Σ(value × weight[7,3,1 repeating]) mod 10."
  [data]
  (str (mod (reduce + 0 (map-indexed (fn [i ch] (* (char-value ch) (nth weights (mod i 3)))) data)) 10)))

(defn- pad
  "Uppercase, replace spaces with filler '<', pad/truncate to n chars."
  [s n]
  (subs (str (str/replace (str/upper-case s) " " "<") (apply str (repeat n "<"))) 0 n))

(defn build-td3-mrz
  "Build the two 44-char TD3 (passport) MRZ lines with all ICAO check digits."
  [{:keys [doc-number issuing-state nationality surname given-names dob-yymmdd sex expiry-yymmdd
           personal-number] :or {personal-number ""}}]
  (when (or (not= 3 (count issuing-state)) (not= 3 (count nationality)))
    (throw (ex-info "issuing_state and nationality must be 3-letter ICAO codes" {})))
  (when (or (not= 6 (count dob-yymmdd)) (not= 6 (count expiry-yymmdd)))
    (throw (ex-info "dates must be YYMMDD (6 digits)" {})))
  (when-not (#{"M" "F" "<"} sex) (throw (ex-info "sex must be M, F, or < (unspecified)" {})))
  (let [name-field (pad (str surname "<<" given-names) 39)
        line1      (str "P<" (str/upper-case issuing-state) name-field)
        doc        (pad doc-number 9)
        c-doc      (mrz-check-digit doc)
        c-dob      (mrz-check-digit dob-yymmdd)
        c-exp      (mrz-check-digit expiry-yymmdd)
        pers       (pad personal-number 14)
        c-pers     (mrz-check-digit pers)
        composite  (str doc c-doc dob-yymmdd c-dob expiry-yymmdd c-exp pers c-pers)
        c-comp     (mrz-check-digit composite)
        line2      (str doc c-doc (str/upper-case nationality) dob-yymmdd c-dob sex
                        expiry-yymmdd c-exp pers c-pers c-comp)]
    {:line1 line1 :line2 line2
     :check-digits {:doc c-doc :dob c-dob :expiry c-exp :personal c-pers :composite c-comp}}))

(defn validate-td3-line2
  "Verify the field + composite check digits of a TD3 MRZ line 2."
  [line2]
  (boolean
   (and (= 44 (count line2))
        (try
          (let [doc (subs line2 0 9)   c-doc (subs line2 9 10)
                dob (subs line2 13 19) c-dob (subs line2 19 20)
                exp (subs line2 21 27) c-exp (subs line2 27 28)
                pers (subs line2 28 42) c-pers (subs line2 42 43)
                c-comp (subs line2 43 44)]
            (and (= (mrz-check-digit doc) c-doc)
                 (= (mrz-check-digit dob) c-dob)
                 (= (mrz-check-digit exp) c-exp)
                 (= (mrz-check-digit pers) c-pers)
                 (= (mrz-check-digit (str doc c-doc dob c-dob exp c-exp pers c-pers)) c-comp)))
          (catch Exception _ false)))))

(defn- unsigned-document
  [kind subject mrz]
  {:type                  ["VerifiableCredential" kind]
   :credential-subject    {:id subject}
   :mrz                   mrz
   :sod                   nil                              ; G1 — issuing state signs the SOD (ICAO PKD)
   :proof                 nil
   :server-held-authority server-held-authority           ; false
   :status                "issued-unsigned"})

(defn issue-passport
  "Validate + assemble an MRTD passport (ICAO 9303). Returns MRZ + unsigned document (G1)."
  [{:keys [doc-number surname subject-did] :as params}]
  (when (str/blank? (str doc-number)) (throw (ex-info "passport: doc_number required" {})))
  (when (str/blank? (str surname)) (throw (ex-info "passport: surname required" {})))
  (let [mrz (build-td3-mrz params)]
    {:mrz mrz :document (unsigned-document "Passport" subject-did mrz)}))

(defn solve
  [& _]
  (throw (ex-info (str "credential-issue R0: reference MRZ assembly only. Live passport/ID issuance "
                       "+ SOD signing is the issuing state's ICAO-PKD authority (principal B) / "
                       "Council Lv7+ (principal A) + operator gated.")
                  {:gated true})))
