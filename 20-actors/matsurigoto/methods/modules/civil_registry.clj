;; civil_registry.clj — matsurigoto 政 `civil-registry` module (R0 reference implementation).
;;
;; Clojure port of civil_registry.py (ADR-2606062300), Wave 1 of the clj-native migration
;; (ADR-2606142300). The CRVS (Civil Registration & Vital Statistics) engine behind
;; civil.birth/death/marriage.register / residency.move-in / residency.certificate — 住所管理・戸籍.
;; Pure-function VALIDATION + APPEND-ONLY record construction shaped on UN CRVS + OpenCRVS:
;; a registration is validated (birth needs a child + ≥1 parent + non-future occurrence; a
;; marriage needs two DISTINCT, unmarried partners; a death needs a decedent), then emitted as
;; an immutable record + an UNSIGNED W3C-VC certificate skeleton (the governing organ signs).
;;
;;   G1 no-operator-master-key : server-held-authority false; certificates UNSIGNED.
;;   G2 spec-derived-only      : UN CRVS + OpenCRVS + W3C VC 2.0 shapes only.
;;   G5 append-only (非終末論)  : every helper RETURNS A NEW record list; nothing overwritten —
;;                               a correction is itself an appended record (ADR-2605312345).
;;   G6 data-minimization      : only the fields the vital event requires.
;;
;; stdlib only, no I/O, no network. ISO-8601 strings sort lexically (ordering + non-future only).
(ns matsurigoto.methods.modules.civil-registry
  (:require [clojure.string :as str]))

(def server-held-authority false)  ; G1

(defn- iso
  "Validate an ISO-8601 timestamp (year-leading); strings sort lexically for ordering/non-future."
  [s]
  (if (and (string? s) (>= (count s) 4) (every? #(Character/isDigit %) (subs s 0 4)))
    s
    (throw (ex-info (str "timestamp must be ISO-8601, got " (pr-str s)) {:ts s}))))

(defn- future? [occurred-at now]
  (pos? (compare (iso occurred-at) (iso now))))

(defn- unsigned-certificate
  [kind subject record-id]
  {:context               ["https://www.w3.org/ns/credentials/v2"]    ; JSON-LD "@context"
   :type                  ["VerifiableCredential" (str (str/capitalize kind) "Certificate")]
   :credential-subject    {:id subject :record record-id}
   :proof                 nil                                          ; G1
   :server-held-authority server-held-authority                       ; false
   :status                "issued-unsigned"})

(defn- record-of
  "An immutable CRVS record (append-only). 非終末論: one event, never a final state."
  [kind record-id fields occurred-at]
  {:record-id   record-id
   :vital-kind  kind
   :occurred-at occurred-at
   :fields      fields           ; data-minimized (G6)
   :immutable   true})           ; G5

(defn register-birth
  "Validate + construct a birth registration (UN CRVS). Requires child, ≥1 parent, place,
   non-future occurrence."
  [record-id child parents place occurred-at now]
  (when (str/blank? (str child)) (throw (ex-info "birth: child is required" {})))
  (when (empty? parents) (throw (ex-info "birth: at least one parent is required" {})))
  (when (str/blank? (str place)) (throw (ex-info "birth: place is required" {})))
  (when (future? occurred-at now) (throw (ex-info "birth: occurrence cannot be in the future" {})))
  {:record      (record-of "birth" record-id {:child child :parents (vec parents) :place place} occurred-at)
   :certificate (unsigned-certificate "birth" child record-id)})

(defn register-death
  "Validate + construct a death registration (UN CRVS). Optional ICD-11 `cause`."
  ([record-id decedent place occurred-at now] (register-death record-id decedent place occurred-at now nil))
  ([record-id decedent place occurred-at now cause]
   (when (str/blank? (str decedent)) (throw (ex-info "death: decedent is required" {})))
   (when (str/blank? (str place)) (throw (ex-info "death: place is required" {})))
   (when (future? occurred-at now) (throw (ex-info "death: occurrence cannot be in the future" {})))
   (let [fields (cond-> {:decedent decedent :place place} (and cause (seq (str cause))) (assoc :cause cause))]
     {:record      (record-of "death" record-id fields occurred-at)
      :certificate (unsigned-certificate "death" decedent record-id)})))

(defn register-marriage
  "Validate + construct a marriage registration (UN CRVS). Requires two DISTINCT partners, a
   place, a non-future occurrence, and that neither partner is already in an active marriage
   within `existing-marriages` (a coll of partner pairs)."
  ([record-id partner-a partner-b place occurred-at now]
   (register-marriage record-id partner-a partner-b place occurred-at now []))
  ([record-id partner-a partner-b place occurred-at now existing-marriages]
   (when (or (str/blank? (str partner-a)) (str/blank? (str partner-b)))
     (throw (ex-info "marriage: two partners are required" {})))
   (when (= partner-a partner-b) (throw (ex-info "marriage: partners must be distinct" {})))
   (when (str/blank? (str place)) (throw (ex-info "marriage: place is required" {})))
   (when (future? occurred-at now) (throw (ex-info "marriage: occurrence cannot be in the future" {})))
   (let [already (set (mapcat seq existing-marriages))]
     (when (or (already partner-a) (already partner-b))
       (throw (ex-info "marriage: a partner is already in an active marriage" {}))))
   {:record      (record-of "marriage" record-id
                            {:partners (vec (sort [partner-a partner-b])) :place place} occurred-at)
    :certificate (unsigned-certificate "marriage" record-id record-id)}))

(defn register-residency
  "Residence registration (転入届). Append-only — a move-in is a new record, the prior address
   is retained in history (非終末論), never overwritten (G5)."
  ([record-id person new-address occurred-at now] (register-residency record-id person new-address occurred-at now nil))
  ([record-id person new-address occurred-at now prior-address]
   (when (str/blank? (str person)) (throw (ex-info "residency: person is required" {})))
   (when (str/blank? (str new-address)) (throw (ex-info "residency: new_address is required" {})))
   (when (future? occurred-at now) (throw (ex-info "residency: occurrence cannot be in the future" {})))
   (let [fields (cond-> {:person person :address new-address}
                  (and prior-address (seq (str prior-address))) (assoc :prior-address prior-address))]
     {:record      (record-of "residency" record-id fields occurred-at)
      :certificate (unsigned-certificate "residency" person record-id)})))

(defn append
  "G5: append a registration to a history, returning a NEW vector (never mutate in place)."
  [history result]
  (conj (vec history) (:record result)))

(defn current-address
  "Latest residency record for a person = current address (max occurred-at). 非終末論."
  [history person]
  (let [moves (filter #(and (= "residency" (:vital-kind %)) (= person (get-in % [:fields :person]))) history)]
    (when (seq moves)
      ;; occurred-at is an ISO string → compare lexically (max-key needs Numbers); first-on-tie like Python max.
      (get-in (reduce (fn [a b] (if (pos? (compare (:occurred-at b) (:occurred-at a))) b a)) moves)
              [:fields :address]))))

(defn solve
  [& _]
  (throw (ex-info (str "civil-registry R0: reference validation + record construction only. Live "
                       "registration against a real civil register is Council+operator gated "
                       "(principal A: Council Lv7+; principal B: adopting state).")
                  {:gated true})))
