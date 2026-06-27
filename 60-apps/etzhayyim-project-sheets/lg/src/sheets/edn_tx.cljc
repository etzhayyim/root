(ns sheets.edn-tx
  "EDN tx-op helpers for kotoba datomic (clj port of lg_sheets/edn.py).

  In Python a hand-rolled encoder was needed; in Clojure EDN is native, so
  `encode` / `encode-tx-data` are `pr-str` over plain clj data (vectors of
  [:db/add E A V] ops with keyword attributes). `parse-edn-value` decodes a
  single EDN scalar string returned by the kotoba server (tolerant)."
  (:require [clojure.string :as str]))

(defn ->attr
  "\"sheet/type\" or :sheet/type -> :sheet/type keyword (strips a leading colon)."
  [a]
  (cond
    (keyword? a) a
    (str/starts-with? (str a) ":") (keyword (subs (str a) 1))
    :else (keyword a)))

(defn encode
  "EDN-encode a single clj value (native pr-str — total over EDN-printable data)."
  [value]
  (pr-str value))

(defn tx-add
  "[:db/add <e> <a> <v>] tx op."
  [e a v]
  [:db/add e (->attr a) v])

(defn tx-retract
  "[:db/retract <e> <a> <v>] tx op."
  [e a v]
  [:db/retract e (->attr a) v])

(defn tx-retract-entity
  "[:db.fn/retractEntity <e>] — atomic full-entity delete (hard delete)."
  [e]
  [:db.fn/retractEntity e])

(defn encode-tx-data
  "Encode a sequence of tx-ops as a single EDN vector string."
  [ops]
  (pr-str (vec ops)))

;; ── EDN scalar decode (server returns rows / datom values as EDN strings) ──────

(def ^:private int-re #"^-?\d+$")
(def ^:private float-re #"^-?\d+\.\d+([eE][+-]?\d+)?$")

(defn parse-edn-value
  "Decode a single EDN scalar string to a clj value (tolerant; mirrors edn.py)."
  [s]
  (if-not (string? s)
    s
    (cond
      (and (str/starts-with? s "\"") (str/ends-with? s "\"") (>= (count s) 2))
      (-> (subs s 1 (dec (count s)))
          (str/replace "\\\"" "\"")
          (str/replace "\\\\" "\\")
          (str/replace "\\n" "\n"))
      (= s "true") true
      (= s "false") false
      (= s "nil") nil
      (re-matches int-re s) (Long/parseLong s)
      (re-matches float-re s) (Double/parseDouble s)
      :else s)))
