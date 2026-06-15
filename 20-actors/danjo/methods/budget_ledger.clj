;; budget_ledger.clj — 弾正 (danjo) budget_ledger ingest method.
;;
;; Clojure port of budget_ledger.py (ADR-2605301600), part of the clj-native
;; migration of danjo onto the kotoba EAVT Datom-log stack (ADR-2606142300,
;; Wave 1 — finishes danjo after the revenue-ledger family landed in #1742).
;;
;; Reads gov.dataset.budgetRecord-shaped records (com.etzhayyim.gov.dataset.budgetRecord)
;; and normalizes them into a *budget ledger*: per-record content CIDs + a per-(programCode,
;; fiscalYear) grouping of appropriation vs outlay lines that kanae_flow_assembler consumes
;; downstream (domestic-flow-chain-assembly, ADR-2605302300).
;;
;; danjo is the censor's EYE, never the sword (ADR-2605301600). This method is PASSIVE and
;; NON-ADJUDICATING by construction:
;;   G3 — reads pre-published records only; it never fetches a live portal (the seed is the corpus).
;;   G4 — it emits FACTUAL ledger structure only; no crime/violation/guilt field exists or is computed.
;;   G5 — every ledger line carries its source-record CID; downstream edges need ≥2 of them.
;;   G13 — `stateAlignedFlag` passes through unchanged (not independently verified here).
;;
;; A "CID" here is a deterministic content hash (sha256 over the canonical record) prefixed with
;; the gov.dataset record locator — the same string shape kanae cites in `sourceRecordCids`. To
;; keep a Python→Clojure swap transparent, `record-cid` is BYTE-IDENTICAL with budget_ledger.py:
;; the canonical form is Python's `json.dumps(rec, ensure_ascii=False, sort_keys=True,
;; separators=(",",":"))` reproduced exactly by `canonical-json` below, then sha256 hex[:24].
;; Stdlib + cheshire (bundled in bb) only. Runs under `bb` or `clojure`.
(ns root.danjo.methods.budget-ledger
  (:require [cheshire.core :as json]
            [clojure.string :as str]
            [clojure.java.io :as io])
  (:import [java.security MessageDigest]))

(def valid-record-kinds
  "budgetRecord lexicon enum (recordKind)."
  #{"appropriation" "obligation" "outlay" "subaward"})

;; ── Python-compatible canonical JSON ────────────────────────────────────────────
;; Mirrors json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",",":")):
;;   sorted keys · no whitespace · non-ASCII emitted literally · Python json string escapes.
(defn- esc-str
  [^String s]
  (let [sb (StringBuilder.)]
    (.append sb \")
    (doseq [c s]
      (cond
        (= c \")          (.append sb "\\\"")
        (= c \\)          (.append sb "\\\\")
        (= c \newline)    (.append sb "\\n")
        (= c \return)     (.append sb "\\r")
        (= c \tab)        (.append sb "\\t")
        (= c \backspace)  (.append sb "\\b")
        (= c \formfeed)   (.append sb "\\f")
        (< (int c) 0x20)  (.append sb (format "\\u%04x" (int c)))
        :else             (.append sb c)))
    (.append sb \")
    (.toString sb)))

(defn canonical-json
  "Canonical JSON byte-for-byte equal to Python json.dumps(sort_keys, separators (\",\",\":\"),
   ensure_ascii=False). Handles the value types a budgetRecord carries (string/int/bool/nil)
   plus nested maps/vectors defensively."
  [x]
  (cond
    (map? x)        (str "{"
                         (->> x
                              (sort-by (fn [[k _]] (if (keyword? k) (name k) (str k))))
                              (map (fn [[k v]]
                                     (str (esc-str (if (keyword? k) (name k) (str k)))
                                          ":" (canonical-json v))))
                              (str/join ","))
                         "}")
    (sequential? x) (str "[" (str/join "," (map canonical-json x)) "]")
    (string? x)     (esc-str x)
    (boolean? x)    (if x "true" "false")
    (integer? x)    (str x)
    (nil? x)        "null"
    :else           (throw (ex-info (str "canonical-json: unsupported value type " (type x))
                                    {:value x}))))

(defn- sha256-hex
  [^String s]
  (let [d (.digest (MessageDigest/getInstance "SHA-256") (.getBytes s "UTF-8"))]
    (apply str (map #(format "%02x" (bit-and (int %) 0xff)) d))))

(defn- as-int
  "Mirror Python int(): accept an integer as-is or parse a string."
  [v]
  (if (integer? v) (long v) (Long/parseLong (str v))))

(defn record-cid
  "Deterministic gov.dataset record CID: locator + sha256 content digest (G5 provenance).
   Byte-identical with budget_ledger.py record_cid."
  [rec]
  (let [digest (subs (sha256-hex (canonical-json rec)) 0 24)
        fy     (get rec "fiscalYear" "0")
        rid    (get rec "recordId" "unknown")
        sensor (get rec "sourceSensor" "unknown")]
    (str "gov.dataset.budgetRecord:" sensor ":" fy ":" rid "#" digest)))

(defn normalize-record
  "One ledger line from a budgetRecord. Pure; carries its own CID (G5)."
  [rec]
  (let [kind   (get rec "recordKind")
        _      (when-not (valid-record-kinds kind)
                 (throw (ex-info (str "unknown recordKind " (pr-str kind)
                                      " (budgetRecord lexicon enum)")
                                 {:recordKind kind})))
        amount (get rec "amountLocal")
        _      (when-not (and (integer? amount) (>= amount 0))
                 (throw (ex-info (str "amountLocal must be a non-negative integer (minor units), got "
                                      (pr-str amount))
                                 {:amountLocal amount})))]
    {:cid              (record-cid rec)
     :recordKind       kind
     :jurisdiction     (get rec "jurisdiction" "jpn")
     :programName      (get rec "programName" "")
     :programCode      (get rec "programCode" "")
     :amountLocal      amount
     :currencyIso4217  (get rec "currencyIso4217" "JPY")
     :fiscalYear       (as-int (get rec "fiscalYear" 0))
     :recipientName    (get rec "recipientName" "")
     :recipientLocalId (get rec "recipientLocalId" "")
     :recipientLei     (get rec "recipientLei" "")
     :awardDateUtc     (get rec "awardDateUtc" "")
     :sourceUrl        (get rec "sourceUrl" "")
     :stateAlignedFlag (boolean (get rec "stateAlignedFlag" false))}))

(defn build-ledger
  "Ingest budgetRecords → a budget ledger grouped by (programCode, fiscalYear).

   Returns {:lines  [normalized line …]                ; every record, with CID
            :groups {\"JP-MEXT-EDUSCI|2024\" {:programCode :programName :fiscalYear
                                              :jurisdiction :appropriations [..] :outlays [..]}
                     …}}                                ; appropriation/outlay split per program-year"
  [records]
  (let [lines (mapv normalize-record records)]
    {:lines lines
     :groups
     (reduce
      (fn [groups ln]
        (let [k (str (:programCode ln) "|" (:fiscalYear ln))
              g (get groups k {:programCode  (:programCode ln)
                               :programName  (:programName ln)
                               :fiscalYear   (:fiscalYear ln)
                               :jurisdiction (:jurisdiction ln)
                               :appropriations []
                               :outlays        []})
              g (if (= "appropriation" (:recordKind ln))
                  (update g :appropriations conj ln)
                  (update g :outlays conj ln))]
          (assoc groups k g)))
      {}
      lines)}))

(defn load-seed
  "Read a budgetRecord seed (JSON). Returns the :records vector (or a bare list)."
  [path]
  (let [doc (json/parse-string (slurp (io/file path)))]
    (cond
      (and (map? doc) (contains? doc "records")) (get doc "records")
      (sequential? doc)                          doc
      :else                                      [])))

(defn -main
  [& args]
  (let [seed   (or (first args) "20-actors/danjo/data/gov-fiscal-seed.jp.json")
        ledger (build-ledger (load-seed seed))]
    (println (format "budget_ledger: %d lines, %d program-year groups"
                     (count (:lines ledger)) (count (:groups ledger))))
    (doseq [[k g] (:groups ledger)]
      (println (format "  %s: %d appropriation / %d outlay"
                       k (count (:appropriations g)) (count (:outlays g)))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
