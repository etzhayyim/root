#!/usr/bin/env bb
;; kotoba.clj — kosatsu 高札 kotoba Datom-log writer (local, content-addressed). ADR-2606072000
;; + ADR-2605262130 + ADR-2605312345.
;;
;; Port of kotoba.py. CID is byte-identical to kotoba.py: sha256 over the same canonical JSON:
;;   json.dumps({"prev": prev_cid, "datoms": datoms}, ensure_ascii=False,
;;              sort_keys=True, separators=(",", ":"))
;; Log written as the same custom-EDN single-line format (_tx_to_edn); read back with a custom
;; EDN parser that uses json-loads-style string unescape (matching _edn.py's json.loads path).
;;
;; EAVT = [op entity attribute value]; op is ":db/add" only (append-only — no ":db/retract",
;; 非終末論). Stdlib only. Deterministic (caller supplies tx-id + as-of; no wall clock).
;;
;; Constitutional posture: etzhayyim authors NO designation (every :asserter is a sovereign body,
;; never etzhayyim); NO verdict; NO per-subject score. The computed divergence (contested |
;; unanimous | single-asserter) is a NEUTRAL fact. ADR-2606072000.
(ns kosatsu.methods.kotoba
  (:require [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)

(defn log-default []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "kosatsu.datoms.kotoba.edn")))

;; ── ID key constants (mirrors Python ID_KEYS) ─────────────────────────────────

(def ^:private ID-KEYS #{":authority/id" ":subject/id" ":designation/id"})

;; Canonical attribute orders — mirror Python dict insertion order from the EDN seed.
;; The edn.cljc reader returns PersistentHashMap for maps with >8 keys, losing EDN
;; insertion order. These ordered lists re-impose the seed's EDN file order so that
;; the emitted datom sequence is byte-identical to kotoba.py.
;;
;; Order determined by reading seed-designation-graph.kotoba.edn directly:

(def ^:private AUTH-KEY-ORDER
  [":authority/kind" ":authority/label" ":authority/jurisdiction" ":authority/stance"
   ":authority/sourcing" ":authority/sources"])

(def ^:private SUBJ-KEY-ORDER
  [":subject/kind" ":subject/label" ":subject/jurisdiction" ":subject/sourcing"])

;; Designations: the base key order (all designations follow this; lifted-at appears
;; between posted-at and asserted-notice when present).
(def ^:private DESIG-KEY-ORDER
  [":designation/asserter" ":designation/subject" ":designation/measure"
   ":designation/program" ":designation/status" ":designation/posted-at"
   ":designation/lifted-at"       ;; optional — only emitted if the key exists in the map
   ":designation/asserted-notice" ":designation/sourcing" ":designation/sources"])

;; ── EAVT assertions ───────────────────────────────────────────────────────────

(defn- add-datom
  "One append-only EAVT assertion: [\":db/add\" <entity> <attr> <value>]."
  [entity attr value]
  [":db/add" entity attr value])

(defn- ordered-pairs
  "Return [k v] pairs from map m in the given canonical key order,
  skipping any key absent in m. Matches Python's dict iteration over these keys."
  [m key-order]
  (for [k key-order
        :when (contains? m k)]
    [k (get m k)]))

(defn- flatten-rows
  "Mirror of Python _flatten: iterate rows (dict values or list), find the ID key,
  emit one EAVT datom per (non-ID attr, scalar value). List values are expanded
  into one datom per item (matching Python `for item in (v if isinstance(v, list) else [v])`)."
  [rows key-order out]
  (let [items (if (map? rows) (vals rows) rows)]
    (doseq [row items]
      (when (map? row)
        (let [e (first (keep #(get row %) [":authority/id" ":subject/id" ":designation/id"]))]
          (when e
            (doseq [[k v] (ordered-pairs row key-order)
                    :when (not (contains? ID-KEYS k))]
              (let [scalars (if (sequential? v) v [v])]
                (doseq [item scalars]
                  (swap! out conj (add-datom e k item)))))))))))

(defn graph-datoms
  "Flatten the woven competing-claim graph into append-only EAVT assertions.
  Each designation carries its own :asserter — etzhayyim authors none. Mirrors kotoba.py graph_datoms."
  [g]
  (let [out (atom [])]
    (flatten-rows (get g "authorities") AUTH-KEY-ORDER out)
    (flatten-rows (get g "subjects")   SUBJ-KEY-ORDER out)
    (flatten-rows (get g "designations") DESIG-KEY-ORDER out)
    @out))

;; ── derived datoms ────────────────────────────────────────────────────────────

(defn derived-datoms
  "Flatten the aggregate competing-claim report into EAVT assertions, each flagged
  :kosatsu.div/derived true. Mirrors kotoba.py derived_datoms. NEVER a verdict or
  per-subject score — a politically-neutral observation recomputed on read."
  ([r] (derived-datoms r "kosatsu.div"))
  ([r prefix]
   (let [out  (atom [])
         ai   (get r "agreement_index")
         e    (str prefix "-agreement")]
     ;; agreement-index block
     (swap! out into
            [(add-datom e ":kosatsu.div/authority-count"   (get r "authority_count"))
             (add-datom e ":kosatsu.div/subject-count"     (get r "subject_count"))
             (add-datom e ":kosatsu.div/designation-count" (get r "designation_count"))
             (add-datom e ":kosatsu.div/contested"         (get ai "contested"))
             (add-datom e ":kosatsu.div/single-asserter"   (get ai "single_asserter"))
             (add-datom e ":kosatsu.div/unanimous"         (get ai "unanimous"))
             (add-datom e ":kosatsu.div/contested-ratio"   (get ai "contested_ratio"))
             (add-datom e ":kosatsu.div/derived"           true)])
     ;; per-subject divergence
     (doseq [d (get r "divergence")]
       (let [es (str prefix "-subject-" (get d "subject"))
             cls (let [c (str (get d "class"))]
                   (str ":" (str/replace c #"^:+" "")))]
         (swap! out into
                [(add-datom es ":kosatsu.div/subject"  (get d "subject"))
                 (add-datom es ":kosatsu.div/class"    cls)
                 (add-datom es ":kosatsu.div/listing"  (get d "listing"))
                 (add-datom es ":kosatsu.div/delisted" (get d "delisted"))
                 (add-datom es ":kosatsu.div/silent"   (get d "silent"))
                 (add-datom es ":kosatsu.div/derived"  true)])))
     ;; by-authority coverage
     (doseq [a (get r "by_authority")]
       (let [ea (str prefix "-authority-" (get a "authority"))]
         (swap! out into
                [(add-datom ea ":kosatsu.div/authority"       (get a "authority"))
                 (add-datom ea ":kosatsu.div/jurisdiction"    (get a "jurisdiction"))
                 (add-datom ea ":kosatsu.div/listed-subjects" (get a "listed_subjects"))
                 (add-datom ea ":kosatsu.div/derived"         true)])))
     ;; co-designation
     (dorun
      (map-indexed
       (fn [i c]
         (let [ec (str prefix "-codesig-" i)]
           (swap! out into
                  [(add-datom ec ":kosatsu.div/asserter"             (get c "asserter"))
                   (add-datom ec ":kosatsu.div/program"              (get c "program"))
                   (add-datom ec ":kosatsu.div/co-designation-count" (get c "count"))
                   (add-datom ec ":kosatsu.div/derived"              true)])))
       (get r "co_designation")))
     @out)))

;; ── JSON-based canonical serialization (byte-identical to kotoba.py) ──────────

(defn- json-val
  "Serialize a single value to JSON (no outer array/object wrapper).
  Must match Python json.dumps behaviour with ensure_ascii=False."
  [v]
  (cond
    (nil? v)     "null"
    (boolean? v) (if v "true" "false")
    (instance? Long v)    (str v)
    (instance? Integer v) (str v)
    (and (number? v) (not (float? v)) (not (instance? Double v)))
    (str (long v))
    ;; Float/Double: Java Double.toString matches Python json.dumps for all values in seed
    (or (float? v) (instance? Double v))
    (.toString (double v))
    (string? v)
    ;; JSON-encode: escape \ " \n \r \t; keep non-ASCII as-is (ensure_ascii=False)
    (str "\""
         (-> v
             (str/replace "\\" "\\\\")
             (str/replace "\"" "\\\"")
             (str/replace "\n" "\\n")
             (str/replace "\r" "\\r")
             (str/replace "\t" "\\t"))
         "\"")
    (or (sequential? v) (vector? v))
    (str "[" (str/join "," (map json-val v)) "]")
    :else (str "\"" (str v) "\"")))

(defn- canonical
  "Canonical bytes for content addressing. Matches:
   json.dumps({'prev': prev_cid, 'datoms': datoms},
              ensure_ascii=False, sort_keys=True, separators=(',', ':'))
   sort_keys=True → 'datoms' < 'prev' → datoms first."
  ^bytes [datoms prev]
  (let [datoms-json (str "[" (str/join ","
                                       (map (fn [d]
                                              (str "[" (str/join "," (map json-val d)) "]"))
                                            datoms)) "]")
        s (str "{\"datoms\":" datoms-json ",\"prev\":" (json-val prev) "}")]
    (.getBytes s "UTF-8")))

(defn- sha256-hex [^bytes b]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")]
    (apply str (map #(format "%02x" (bit-and % 0xff)) (.digest md b)))))

(defn tx-cid
  "Content address = 'b' + sha256 over (prev, datoms) — byte-identical to kotoba.py tx_cid."
  ([datoms] (tx-cid datoms ""))
  ([datoms prev] (str "b" (sha256-hex (canonical datoms prev)))))

;; ── Transaction construction ──────────────────────────────────────────────────

(defn make-tx
  "Build a content-addressed transaction. tx-id + as-of supplied by caller (no wall clock).
  Mirrors kotoba.py make_tx; uses string keys to match the Python dict."
  [datoms & {:keys [tx-id as-of prev-cid] :or {prev-cid ""}}]
  {":tx/id"     tx-id
   ":tx/as-of"  as-of
   ":tx/prev"   prev-cid
   ":tx/cid"    (tx-cid datoms prev-cid)
   ":tx/count"  (count datoms)
   ":tx/datoms" datoms})

;; ── EDN serialization (_tx_to_edn equivalent) ─────────────────────────────────

(defn- edn-val
  "Serialize a single value to EDN, matching kotoba.py _edn_val exactly:
   - bool → 'true' / 'false'
   - int/float → repr (e.g. '0.2', '42')
   - str starting with ':' → bare keyword (no quotes)
   - str not starting with ':' → json.dumps(v) (quoted, JSON-escaped)
   - list → '[' space-joined values ']'"
  [v]
  (cond
    (nil? v)     "nil"
    (boolean? v) (if v "true" "false")
    (instance? Long v)    (str v)
    (instance? Integer v) (str v)
    (and (number? v) (not (float? v)) (not (instance? Double v)))
    (str (long v))
    (or (float? v) (instance? Double v))
    (.toString (double v))
    (string? v)
    (if (str/starts-with? v ":")
      v  ;; EDN keyword — bare, no quotes
      ;; Regular string: json.dumps(v, ensure_ascii=False)
      (str "\""
           (-> v
               (str/replace "\\" "\\\\")
               (str/replace "\"" "\\\"")
               (str/replace "\n" "\\n")
               (str/replace "\r" "\\r")
               (str/replace "\t" "\\t"))
           "\""))
    (or (sequential? v) (vector? v))
    (str "[" (str/join " " (map edn-val v)) "]")
    :else (str "\"" (str v) "\"")))

(defn- tx-to-edn
  "Serialize one transaction as a single-line EDN map. Mirrors kotoba.py _tx_to_edn byte-for-byte."
  [tx]
  (let [datoms   (get tx ":tx/datoms")
        datoms-s (str/join " " (map (fn [d]
                                      (str "[" (str/join " " (map edn-val d)) "]"))
                                    datoms))]
    (str "{:tx/id " (get tx ":tx/id")
         " :tx/as-of " (get tx ":tx/as-of")
         " :tx/prev " (json-val (get tx ":tx/prev"))
         " :tx/cid " (json-val (get tx ":tx/cid"))
         " :tx/count " (get tx ":tx/count")
         " :tx/datoms [" datoms-s "]}")))

;; ── Append-only log I/O ───────────────────────────────────────────────────────

(defn append-tx
  "Append ONE transaction to the append-only log (never rewrites). Returns the tx CID.
  Mirrors kotoba.py append_tx."
  ([tx] (append-tx tx (log-default)))
  ([tx log-path]
   (let [f (io/file log-path)]
     (.mkdirs (.getParentFile (.getAbsoluteFile f)))
     (when-not (.exists f)
       (spit f (str ";; kosatsu kotoba Datom log — append-only EAVT transactions "
                    "(content-addressed DAG). Every designation is an ATTRIBUTED event; "
                    "etzhayyim authors no designation, no verdict, no score. ADR-2606072000.\n")
             :encoding "UTF-8"))
     (spit f (str (tx-to-edn tx) "\n") :append true :encoding "UTF-8")
     (get tx ":tx/cid"))))

;; ── EDN reader (matching _edn.py, with json-loads string unescape) ────────────

(def ^:private token-re
  #"[\s,]+|;[^\n]*|(\[|\]|\{|\}|\"(?:\\.|[^\"\\])*\"|[^\s,\[\]{}]+)")

(defn- edn-tokens [s]
  (->> (re-seq token-re s)
       (keep second)))

(defn- json-unescape
  "Unescape a JSON-encoded string literal (with surrounding quotes), matching _edn.py's
  json.loads path."
  [t]
  (let [inner (subs t 1 (dec (count t)))]
    (loop [sb (StringBuilder.) i 0]
      (if (>= i (count inner))
        (.toString sb)
        (let [c (.charAt inner i)]
          (if (= c \\)
            (let [esc (.charAt inner (inc i))]
              (case esc
                \" (do (.append sb \") (recur sb (+ i 2)))
                \\ (do (.append sb \\) (recur sb (+ i 2)))
                \/ (do (.append sb \/) (recur sb (+ i 2)))
                \n (do (.append sb \newline) (recur sb (+ i 2)))
                \r (do (.append sb \return) (recur sb (+ i 2)))
                \t (do (.append sb \tab) (recur sb (+ i 2)))
                \b (do (.append sb \backspace) (recur sb (+ i 2)))
                \f (do (.append sb \formfeed) (recur sb (+ i 2)))
                \u (let [hex (subs inner (+ i 2) (+ i 6))]
                     (.appendCodePoint sb (Integer/parseInt hex 16))
                     (recur sb (+ i 6)))
                (do (.append sb \\) (.append sb esc) (recur sb (+ i 2)))))
            (do (.append sb c) (recur sb (inc i)))))))))

(defn- parse-atom [t]
  (cond
    (str/starts-with? t "\"") (json-unescape t)
    (= t "true")  true
    (= t "false") false
    (= t "nil")   nil
    (str/starts-with? t ":") t   ;; keyword kept as ":ns/name" string
    :else
    (try (Long/parseLong t)
         (catch Exception _
           (try (Double/parseDouble t)
                (catch Exception _ t))))))

(def ^:private END-SENTINEL ::end)

(defn- parse-form [state]
  (let [ts @state]
    (when (empty? ts)
      (throw (ex-info "unexpected end of input" {})))
    (let [t (first ts)]
      (reset! state (rest ts))
      (cond
        (= t "[") (loop [out []]
                    (let [x (parse-form state)]
                      (if (= x END-SENTINEL) out (recur (conj out x)))))
        (= t "{") (loop [out {}]
                    (let [k (parse-form state)]
                      (if (= k END-SENTINEL)
                        out
                        (let [v (parse-form state)]
                          (recur (assoc out k v))))))
        (or (= t "]") (= t "}")) END-SENTINEL
        :else (parse-atom t)))))

(defn- parse-edn-line [line]
  (parse-form (atom (edn-tokens line))))

;; ── Log read / verify ─────────────────────────────────────────────────────────

(defn read-log
  "Read the log back as a vector of transaction maps. Returns [] if the log does not exist.
  Mirrors kotoba.py read_log."
  ([] (read-log (log-default)))
  ([log-path]
   (let [f (io/file log-path)]
     (if-not (.exists f)
       []
       (->> (str/split-lines (slurp f :encoding "UTF-8"))
            (map str/trim)
            (remove #(or (empty? %) (str/starts-with? % ";")))
            (mapv parse-edn-line))))))

(defn head-cid
  "The content-addressed HEAD = the last transaction's CID."
  ([] (head-cid (log-default)))
  ([log-path]
   (let [txs (read-log log-path)]
     (if (seq txs) (get (last txs) ":tx/cid") ""))))

(defn verify-chain
  "Recompute every CID from its datoms + prev; verify the DAG is intact.
  Returns {:ok :length :broken-at}. Mirrors kotoba.py verify_chain."
  ([] (verify-chain (log-default)))
  ([log-path]
   (let [txs (read-log log-path)]
     (loop [i 0 prev "" xs txs]
       (if (empty? xs)
         {:ok true :length (count txs) :broken-at -1}
         (let [tx     (first xs)
               dats   (get tx ":tx/datoms" [])
               expect (tx-cid dats prev)]
           (if (or (not= (get tx ":tx/cid") expect)
                   (not= (get tx ":tx/prev") prev))
             {:ok false :length (count txs) :broken-at i}
             (recur (inc i) (get tx ":tx/cid") (rest xs)))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (println "kosatsu.methods.kotoba loaded."))
