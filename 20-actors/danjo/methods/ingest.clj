;; ingest.clj — 弾正 (danjo) revenue-corpus ingest (passive-only, G3). ADR-2605301600.
;;
;; Projects the pre-published `com.etzhayyim.gov.dataset.*Record` corpus
;; (data/gov-revenue-corpus.jp.edn) → the revenue model that revenue_ledger.clj consumes
;; ({:accounts :revenue-lines :transfers :outlays}). The sibling of budget_ledger.py, but for
;; the REVENUE side and in Clojure.
;;
;; Discipline (inherited from danjo + budget_ledger.py):
;;   G3 — PASSIVE: the corpus IS the input; this never fetches a live portal.
;;   G4 — FACTUAL structure only; no crime/violation field exists or is computed.
;;   G5 — every projected model entry carries ≥2 source CIDs (its own record CID + the
;;        dataset manifest CID), so downstream trace/outlay datoms satisfy danjo G5.
;;   account-EARMARK is accounting LAW (特別会計法 / 復興財源確保法), encoded here as a constant —
;;        NOT a fetched record. That is what keeps the per-yen-traceability decision honest.
;;
;; Pure + JVM stdlib only; runs under bb and clojure.
(ns root.danjo.methods.ingest
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as str])
  (:import [java.security MessageDigest]))

;; The account-boundary framework is LAW, not data (so it is a constant, not ingested).
(def account-law
  [{:id :general                :kind :general :ja "一般会計"
    :earmark? false
    :note "non-earmarked: fungible revenue, per-yen expenditure linkage unrepresentable (ノン・アフェクタシオン原則)"}
   {:id :special/reconstruction :kind :special :ja "東日本大震災復興特別会計"
    :earmark? true
    :note "closed earmarked boundary: 繰入→歳出 traceable to the yen within the account (復興財源確保法)"}])

(defn- sha256-hex [^String s]
  (let [md (MessageDigest/getInstance "SHA-256")]
    (apply str (map #(format "%02x" (bit-and % 0xff)) (.digest md (.getBytes s "UTF-8"))))))

(defn- canonical
  "Deterministic canonical string for a record: keys sorted, stable (same record → same CID)."
  [m]
  (str "{" (str/join "," (for [k (sort (map str (keys m)))]
                           (str k " " (pr-str (get m (edn/read-string k)))))) "}"))

(defn record-cid
  "gov.dataset record CID: locator + sha256[:24] content digest (G5 provenance). Mirrors the
   string shape of budget_ledger.py record_cid, generalized over :record-kind."
  [rec]
  (let [kind   (name (or (:record-kind rec) :unknown))
        sensor (or (:source-sensor rec) "unknown")
        fy     (or (:fiscal-year rec) 0)
        rid    (or (:record-id rec) "unknown")]
    (str "gov.dataset." kind "Record:" sensor ":" fy ":" rid "#"
         (subs (sha256-hex (canonical rec)) 0 24))))

(defn dataset-cid
  "Content CID over the whole corpus manifest (the dataset the records came from) — the 2nd
   source CID every projected entry carries, so G5 (≥2) holds structurally."
  [corpus]
  (str "gov.dataset.manifest:" (or (:source-sensor corpus) "unknown") "#"
       (subs (sha256-hex (canonical (dissoc corpus :records))) 0 24)))

(defn- non-neg-int! [rec]
  (let [a (:amount-local rec)]
    (when-not (and (integer? a) (>= a 0))
      (throw (ex-info (str "amount-local must be a non-negative integer (1円 minor units), got " (pr-str a))
                      {:record (:record-id rec)})))
    a))

(defn ingest-corpus
  "Project a gov.dataset corpus map → the revenue model. Passive (G3). Each model entry's
   :source-record-cids = [its own record CID, the dataset manifest CID] (G5 ≥2)."
  [corpus]
  (let [recs    (:records corpus)
        ds-cid  (dataset-cid corpus)
        cids    (fn [rec] [(record-cid rec) ds-cid])
        by-kind (group-by :record-kind recs)]
    {:source-sensor       (:source-sensor corpus)
     :jurisdiction        (:jurisdiction corpus)
     :currency-iso4217    (:currency-iso4217 corpus)
     :verification-status (:verification-status corpus)
     :primary-sources     (:primary-sources corpus)
     :dataset-cid         ds-cid
     :accounts            account-law
     :revenue-lines
     (vec (for [r (:revenue by-kind)]
            {:record-id (:record-id r) :tax-kind (:tax-kind r) :account (:account r)
             :ja (:program-name r) :fiscal-year (:fiscal-year r)
             :amount-jpy (non-neg-int! r) :source-record-cids (cids r) :tier "A"}))
     :transfers
     (vec (for [r (:transfer by-kind)]
            {:record-id (:record-id r) :tax-kind (:tax-kind r)
             :from (:from r) :to (:to r) :fiscal-year (:fiscal-year r)
             :amount-jpy (non-neg-int! r) :source-record-cids (cids r) :tier "A"}))
     :outlays
     (vec (for [r (:outlay by-kind)]
            {:record-id (:record-id r) :account (:account r)
             :program-code (:program-code r) :program-name (:program-name r)
             :cofog (:cofog r) :recipient-class (:recipient-class r)
             :fiscal-year (:fiscal-year r) :amount-jpy (non-neg-int! r)
             :source-record-cids (cids r) :tier "A"}))}))

(defn load-corpus
  "Read the pre-published corpus EDN (passive, G3). Defaults to the actor data dir."
  ([] (load-corpus nil))
  ([path]
   (let [f (io/file (or path "20-actors/danjo/data/gov-revenue-corpus.jp.edn"))
         f (if (.exists f) f (io/file "../data/gov-revenue-corpus.jp.edn"))]
     (edn/read-string (slurp f)))))

(defn ingest
  "Convenience: load + project the JP revenue corpus into the model."
  ([] (ingest-corpus (load-corpus)))
  ([path] (ingest-corpus (load-corpus path))))

(defn -main [& args]
  (let [model (ingest (first args))]
    (println "ingested" (:source-sensor model) "→ dataset-cid" (:dataset-cid model))
    (println " " (count (:revenue-lines model)) "revenue-lines,"
             (count (:transfers model)) "transfers,"
             (count (:outlays model)) "outlays")
    (doseq [rl (:revenue-lines model)]
      (println "  rev" (:tax-kind rl) (:amount-jpy rl) "← " (first (:source-record-cids rl))))))
