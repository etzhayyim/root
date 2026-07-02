;; etzhayyim.rad-metrics — BMC gate emitter for :hyp/etzhayyim-registry-value
;; (70-tools/bmc gate.cljc). etzhayyim is a NON-PROFIT: this namespace makes the
;; instrument-blocked gate ["itonami 契約の RAD attestation 参照フック" "資金チャネル
;; (寄付/助成)"] MEASURABLE by aggregating, read-only, two disclosed public facts:
;;
;;   1. RAD attestation coverage — over the sovereign-identity ledgers in
;;      80-data/kotoba-rad/*.identity.journal.edn (EAVT datoms [e a v tx op],
;;      ADR-2606231200): how many organisms are registered, how many carry an
;;      attestation reference (:rad/type :sigref), and how many of those refs
;;      carry an actual Ed25519 signature (:rad/sig) vs. remain pending.
;;   2. Funding channel — donation/grant give-records (lexicons
;;      00-contracts/lexicons/com/etzhayyim/give/*, ontology
;;      00-contracts/schemas/fund-stewardship-ontology.kotoba.edn) aggregated as
;;      an append-only give ledger. Currently 0 events (no ledger authored yet).
;;
;; This is PURE AGGREGATION + a metric emit. It NEVER signs an attestation, never
;; accepts a give, never actuates a channel — those are Council / on-chain legs.
;;
;; NON-PROFIT INVARIANT (do not break): a funding record is only counted toward
;; the channel when its purpose ∈ #{"donation" "grant"} (donation-only; no
;; cash-to-adherent, no investment instrument — mirrors fund-stewardship G2 and
;; give/usdc/donation.json). Records outside that set are surfaced as :rejected,
;; never summed into the channel total.
;;
;; The emitted map is consumed by the superproject BMC collector
;; (70-tools/bmc/collect.bb → 90-docs/business/metrics/etzhayyim.edn) under the
;; :rad key, so the gate-spec can be flipped from :needs (blocked) to a
;; machine-measurable clause, e.g. {:metric [:rad :attested-organisms] :op :>=
;; :threshold 1} + {:metric [:rad :funding-events] :op :>= :threshold 1}.
;;
;; bb usage (classpath 70-tools/src):
;;   bb rad:metrics                       ;; pprint {:rad {...}} to stdout
;;   bb rad:metrics --out metrics/etzhayyim.edn   ;; write the {:rad {...}} fragment
(ns etzhayyim.rad-metrics
  (:require [clojure.java.io :as io]
            [clojure.pprint :as pp]
            [clojure.string :as str]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.log :as log]))

;; ── RAD attestation aggregation (pure over one journal's datom vector) ───────

(defn identity-rid
  "RID (entity id) of the :rad/type :identity datom in a journal, or nil."
  [logv]
  (some #(when (and (= :rad/type (d/d-a %)) (= :identity (d/d-v %))) (d/d-e %)) logv))

(defn actor-name
  "The :rad/name value in a journal, or nil."
  [logv]
  (some #(when (= :rad/name (d/d-a %)) (d/d-v %)) logv))

(defn sigref-entities
  "Distinct entity ids that are declared :rad/type :sigref in the journal."
  [logv]
  (into #{} (comp (filter #(and (= :rad/type (d/d-a %)) (= :sigref (d/d-v %))))
                  (map d/d-e))
        logv))

(defn signed-sigref-entities
  "Sigref entity ids that carry an actual :rad/sig (Ed25519 signature) datom —
   i.e. the attestation is materialized, not merely referenced/pending."
  [logv]
  (let [refs (sigref-entities logv)]
    (into #{} (comp (filter #(and (= :rad/sig (d/d-a %)) (contains? refs (d/d-e %))))
                    (map d/d-e))
          logv)))

(defn journal-summary
  "Pure: one journal's [e a v tx op] vector → per-organism attestation state.
   :registered?       has a :rad/type :identity datom
   :attestation-ref?  has ≥1 :rad/type :sigref entity (a reference is present)
   :attested?         ≥1 of those sigrefs carries a real :rad/sig (signed)"
  [logv]
  (let [refs   (sigref-entities logv)
        signed (signed-sigref-entities logv)]
    {:name             (actor-name logv)
     :rid              (identity-rid logv)
     :registered?      (some? (identity-rid logv))
     :attestation-ref? (boolean (seq refs))
     :attested?        (boolean (seq signed))}))

(defn rad-summary
  "Aggregate a seq of journal datom-vectors →
   {:registered-organisms N :attested-organisms N :attestation-refs N
    :pending-attestations N}. attested = organism with ≥1 SIGNED sigref;
   attestation-refs = organism with ≥1 sigref (signed or pending);
   pending = referenced but not yet signed."
  [journals]
  (reduce
   (fn [acc logv]
     (let [{:keys [registered? attestation-ref? attested?]} (journal-summary logv)]
       (cond-> acc
         registered?               (update :registered-organisms inc)
         attested?                 (update :attested-organisms inc)
         attestation-ref?          (update :attestation-refs inc)
         (and attestation-ref?
              (not attested?))     (update :pending-attestations inc))))
   {:registered-organisms 0 :attested-organisms 0
    :attestation-refs 0 :pending-attestations 0}
   journals))

;; ── funding-channel aggregation (pure over give datoms) ──────────────────────
;; A give record is an entity carrying :give/type :donation with :give/purpose,
;; and either :give/amount-jpy (JPY-denominated) and/or :give/amount-micros (USDC
;; micros, per give/usdc/donation.json). We DO NOT fabricate an FX rate: only
;; explicit JPY amounts sum into :funding-jpy; USDC micros are surfaced separately
;; so nothing is silently dropped or invented.

(def allowed-purposes
  "Non-profit funding purposes the channel may count. donation-only invariant
   (no cash-to-adherent, no investment). Superset enum lives in
   com.etzhayyim.give.usdc.donation; the BMC channel counts only the give legs."
  #{"donation" "grant"})

(defn give-records
  "Group a seq of give datoms by entity → seq of attr→value maps for entities
   that declare :give/type :donation."
  [give-datoms]
  (->> give-datoms
       (group-by d/d-e)
       (keep (fn [[_ ds]]
               (let [kv (into {} (map (juxt d/d-a d/d-v)) ds)]
                 (when (= :donation (:give/type kv)) kv))))))

(defn funding-summary
  "Pure: seq of give datoms → funding-channel aggregate. Records whose purpose is
   outside allowed-purposes are counted as :rejected and excluded from totals
   (non-profit invariant enforcement)."
  [give-datoms]
  (let [recs (give-records give-datoms)
        {ok true rej false} (group-by #(contains? allowed-purposes (:give/purpose %)) recs)]
    {:funding-events        (count ok)
     :funding-jpy           (reduce + 0 (keep :give/amount-jpy ok))
     :funding-usdc-micros   (reduce + 0 (keep :give/amount-micros ok))
     :rejected-events       (count rej)}))

;; ── combined metric ──────────────────────────────────────────────────────────

(defn rad-metrics
  "Pure: journals (seq of datom vectors) + give-datoms → the BMC :rad metric map."
  [journals give-datoms]
  (let [r (rad-summary journals)
        f (funding-summary give-datoms)]
    {:registered-organisms (:registered-organisms r)
     :attested-organisms   (:attested-organisms r)
     :attestation-refs     (:attestation-refs r)
     :pending-attestations (:pending-attestations r)
     :funding-events       (:funding-events f)
     :funding-jpy          (:funding-jpy f)
     :funding-usdc-micros  (:funding-usdc-micros f)
     :rejected-funding     (:rejected-events f)}))

;; ── IO edge (file reads only; append-only ledgers, never mutated) ────────────

(defn read-journals
  "Read every 80-data/kotoba-rad/*.identity.journal.edn under rad-dir into a
   seq of datom vectors. Sorted by filename for cross-OS reproducibility (see
   etzhayyim.data-provenance/all-holdings)."
  [rad-dir]
  (->> (file-seq (io/file rad-dir))
       (filter #(and (.isFile %)
                     (str/ends-with? (.getName %) ".identity.journal.edn")))
       (sort-by #(.getName %))
       (mapv #(log/read-log (.getPath %)))))

(defn read-give-datoms
  "Read the give ledger (append-only kotoba journal) if present, else []. No
   fabrication: absent ledger ⇒ 0 funding events."
  [give-ledger]
  (if (and give-ledger (.exists (io/file give-ledger)))
    (log/read-log give-ledger)
    []))

(defn collect
  "IO edge: read the RAD dir + optional give ledger → the :rad metric map."
  [{:keys [rad-dir give-ledger]
    :or   {rad-dir "80-data/kotoba-rad"}}]
  (rad-metrics (read-journals rad-dir) (read-give-datoms give-ledger)))

(defn -main
  "bb rad:metrics [--out PATH] [--rad-dir DIR] [--give-ledger PATH].
   Emits {:rad {...}} (pprint). With --out, writes the fragment the superproject
   BMC collector merges into 90-docs/business/metrics/etzhayyim.edn."
  [& args]
  (let [argv       (vec args)
        opt        (fn [flag] (when-let [i (some #(when (= flag (argv %)) %) (range (count argv)))]
                                (get argv (inc i))))
        rad-dir    (or (opt "--rad-dir") "80-data/kotoba-rad")
        give       (opt "--give-ledger")
        out        (opt "--out")
        metric     {:rad (assoc (collect {:rad-dir rad-dir :give-ledger give})
                                :as-of (str (java.time.LocalDate/now))
                                :generated-by "etzhayyim.rad-metrics")}
        rendered   (str (with-out-str (pp/pprint metric)))]
    (if out
      (do (io/make-parents (io/file out))
          (spit out rendered)
          (println (format "→ %s (%d registered, %d attested, %d funding events)"
                           out
                           (get-in metric [:rad :registered-organisms])
                           (get-in metric [:rad :attested-organisms])
                           (get-in metric [:rad :funding-events]))))
      (print rendered))
    0))
