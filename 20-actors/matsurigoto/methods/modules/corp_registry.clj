;; corp_registry.clj — matsurigoto 政 `corp-registry` module (R0 reference implementation).
;;
;; Clojure port of corp_registry.py (ADR-2606062300), Wave 1 of the clj-native migration
;; (ADR-2606142300). Company-registry engine behind corp.incorporation.register /
;; corp.change.register / corp.certificate (法人登記): pure-function VALIDATION + registry-number
;; assignment + ISO 17442 LEI issuance with a real ISO 7064 MOD 97-10 check-digit computation
;; (the same check class as IBAN — the conformance anchor of this module, like the JP 速算表 for
;; tax-assess), then an APPEND-ONLY record + an UNSIGNED incorporation certificate.
;;
;; Spec basis (G2): ISO 17442 (LEI) + GLEIF LEI-CDF + EU BRIS + W3C VC 2.0. LEI checksums are
;; byte-equivalent with corp_registry.py (BigInteger MOD 97-10).
;;
;;   G1 no-operator-master-key : server-held-authority false; certificate UNSIGNED (organ signs).
;;   G2 spec-derived-only      : ISO 17442 LEI structure + ISO 7064 MOD 97-10 checksum.
;;   G5 append-only (非終末論)  : a change is an appended amendment record; nothing overwritten.
;;
;; stdlib only, no I/O, no network.
(ns matsurigoto.methods.modules.corp-registry
  (:require [clojure.string :as str])
  (:import [java.math BigInteger]))

(def server-held-authority false)  ; G1

(def ^:private mod97 (BigInteger/valueOf 97))

;; ── ISO 17442 LEI + ISO 7064 MOD 97-10 (the conformance anchor) ──
(defn- to-digits
  "Convert an alphanumeric string to its ISO 7064 numeric form (0-9 stay; A=10 … Z=35)."
  [s]
  (apply str
         (map (fn [ch]
                (cond
                  (Character/isDigit ch)                       (str ch)
                  (and (>= (int ch) (int \A)) (<= (int ch) (int \Z))) (str (- (int ch) 55))
                  :else (throw (ex-info (str "LEI char must be [0-9A-Z], got " (pr-str ch)) {:ch ch}))))
              s)))

(defn compute-lei-check-digits
  "ISO 7064 MOD 97-10 check digits for an 18-char LEI base. check = 98 − (numeric(base+\"00\") mod 97)."
  [base18]
  (when (not= 18 (count base18))
    (throw (ex-info (str "LEI base must be 18 chars, got " (count base18)) {:base base18})))
  (let [m (.intValue (.mod (BigInteger. (to-digits (str base18 "00"))) mod97))]
    (format "%02d" (- 98 m))))

(defn validate-lei
  "A 20-char LEI is valid iff numeric(lei) mod 97 == 1 (ISO 7064 MOD 97-10)."
  [lei]
  (boolean
   (and (string? lei) (= 20 (count lei))
        (try (= BigInteger/ONE (.mod (BigInteger. (to-digits lei)) mod97))
             (catch Exception _ false)))))

(defn assign-lei
  "Build a valid LEI: 4-char LOU prefix + reserved '00' + 12-char entity id + 2 check digits."
  [lou-prefix entity-id12]
  (when (not= 4 (count lou-prefix)) (throw (ex-info "LOU prefix must be 4 chars" {:lou lou-prefix})))
  (when (not= 12 (count entity-id12)) (throw (ex-info "entity id must be 12 chars" {:eid entity-id12})))
  (let [base (str/upper-case (str lou-prefix "00" entity-id12))]
    (str base (compute-lei-check-digits base))))

;; ── registry records ──
(defn- unsigned-certificate
  [kind subject record-id]
  {:context               ["https://www.w3.org/ns/credentials/v2"]   ; serializes to JSON-LD "@context"
   :type                  ["VerifiableCredential" kind]
   :credential-subject    {:id subject :record record-id}
   :proof                 nil                                          ; G1
   :server-held-authority server-held-authority                       ; false
   :status                "issued-unsigned"})

(defn- left-pad12 [s]
  (let [t (subs s 0 (min 12 (count s)))]
    (str/upper-case (str (apply str (repeat (max 0 (- 12 (count t))) "0")) t))))

(defn register-incorporation
  "Validate + construct a company incorporation registration. Pure. Requires a name, ≥1 officer,
   non-negative capital, articles, an address. Assigns a deterministic registry number
   (jurisdiction + zero-padded sequence) and an ISO 17442 LEI."
  [{:keys [entity-name officers capital articles address jurisdiction sequence lou-prefix entity-id12]
    :or   {lou-prefix "EZHY"}}]
  (when (str/blank? (str entity-name)) (throw (ex-info "incorporation: entity_name required" {})))
  (when (empty? officers) (throw (ex-info "incorporation: at least one officer required" {})))
  (when (< capital 0) (throw (ex-info "incorporation: capital must be >= 0" {})))
  (when (str/blank? (str articles)) (throw (ex-info "incorporation: articles required" {})))
  (when (str/blank? (str address)) (throw (ex-info "incorporation: address required" {})))
  (when (< sequence 0) (throw (ex-info "incorporation: sequence must be >= 0" {})))
  (let [registry-number (str (str/upper-case jurisdiction) "-" (format "%08d" sequence))
        eid             (left-pad12 (or entity-id12 (format "%012d" sequence)))
        lei             (assign-lei lou-prefix eid)
        record          {:record-id    registry-number
                         :kind         "incorporation"
                         :entity-name  entity-name
                         :officers     (vec officers)
                         :capital      capital
                         :jurisdiction jurisdiction
                         :lei          lei
                         :immutable    true}]            ; G5
    {:record          record
     :lei             lei
     :registry-number registry-number
     :certificate     (unsigned-certificate "IncorporationCertificate" registry-number registry-number)}))

(defn register-change
  "Append-only amendment (変更登記). G5: never overwrites the incorporation record."
  [registry-number changed-fields effective-date]
  (when (str/blank? (str registry-number)) (throw (ex-info "change: registry_number required" {})))
  (when (empty? changed-fields) (throw (ex-info "change: changed_fields required" {})))
  {:record {:record-id      (str registry-number "#chg@" effective-date)
            :kind           "change"
            :registry-number registry-number
            :changed        (into {} changed-fields)
            :effective-date effective-date
            :immutable      true}})                       ; G5 — appended, not overwritten

(defn append
  "G5: append a registry record, returning a NEW vector."
  [history result]
  (conj (vec history) (:record result)))

(defn solve
  [& _]
  (throw (ex-info (str "corp-registry R0: reference validation + LEI assignment only. Live "
                       "registration against a real corporate register is Council+operator gated "
                       "(principal A: Council Lv7+; principal B: adopting state).")
                  {:gated true})))
