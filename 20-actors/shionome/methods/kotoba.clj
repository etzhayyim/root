#!/usr/bin/env bb
;; kotoba.clj — shionome 潮目 kotoba Datom-log writer. ADR-2606072200 + ADR-2605312345.
;;
;; Port of kotoba.py. CID is byte-identical to kotoba.py: sha256 over the same canonical JSON:
;;   json.dumps({"prev": prev_cid, "datoms": datoms}, ensure_ascii=False,
;;              sort_keys=True, separators=(",", ":"))
;; Log written as the same custom-EDN single-line format (_tx_to_edn); read back with a custom
;; EDN parser that uses json-loads-style string unescape (matching _edn.py's json.loads path).
;;
;; EAVT = [op entity attribute value]; op is ":db/add" only (append-only — no ":db/retract",
;; 非終末論). Stdlib only. Deterministic (caller supplies tx-id + as-of; no wall clock).
(ns shionome.methods.kotoba
  (:require [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)

(defn log-default []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "shionome.datoms.kotoba.edn")))

;; ── EAVT assertions ───────────────────────────────────────────────────────────

(defn- add-datom
  "One append-only EAVT assertion: [\":db/add\" <entity> <attr> <value>]."
  [entity attr value]
  [":db/add" entity attr value])

;; Canonical EDN-file insertion order for flow map keys (all flow maps in the seed
;; use this order; kotoba.py iterates dicts in insertion order = EDN-file order).
;; Snapshot maps have ≤8 keys so PersistentArrayMap preserves insertion order already.
(def ^:private FLOW-KEY-ORDER
  [":flow/id" ":flow/source" ":flow/target" ":flow/kind" ":flow/magnitude"
   ":flow/unit" ":flow/no-trade-notice" ":flow/as-of" ":flow/sourcing" ":flow/sources"])

(defn- ordered-pairs
  "Return [k v] pairs from map m in insertion order.
  - For maps with ::shionome.methods.weave/order metadata (the outer buckets map):
    use that metadata order.
  - For PersistentArrayMap (≤8 entries): insertion order is preserved natively.
  - For PersistentHashMap (>8 entries, i.e. flow maps): sort by FLOW-KEY-ORDER,
    then any remaining keys alphabetically — this matches Python dict insertion order."
  [m]
  (let [order (:shionome.methods.weave/order (meta m))]
    (cond
      ;; outer buckets map or other omap: use ::order metadata
      (seq order)
      (map (fn [k] [k (get m k)]) order)
      ;; PersistentHashMap: apply known canonical key ordering
      (instance? clojure.lang.PersistentHashMap m)
      (let [key-rank (zipmap FLOW-KEY-ORDER (range))
            sorted-keys (sort-by (fn [k] [(get key-rank k Integer/MAX_VALUE) k]) (keys m))]
        (map (fn [k] [k (get m k)]) sorted-keys))
      ;; PersistentArrayMap: insertion order preserved natively
      :else
      (seq m))))

(defn graph-datoms
  "Flatten a woven graph into append-only EAVT assertions (buckets, flows, snapshots).
  Mirrors kotoba.py graph_datoms: bucket attrs then flow attrs then snapshot attrs,
  preserving Python dict-insertion order (via ::shionome.methods.weave/order metadata)."
  [g]
  (let [buckets (get g "buckets")
        flows   (get g "flows")
        snaps   (get g "snapshots")]
    (vec
     (concat
      ;; for bid, b in g["buckets"].items(): for a, v in b.items():
      (mapcat (fn [[bid b]]
                (for [[a v] (ordered-pairs b)]
                  (add-datom bid a v)))
              (ordered-pairs buckets))
      ;; for f in g["flows"]: fid = f[":flow/id"]: for a, v in f.items():
      (mapcat (fn [f]
                (let [fid (get f ":flow/id")]
                  (for [[a v] (ordered-pairs f)]
                    (add-datom fid a v))))
              flows)
      ;; for s in g["snapshots"]: sid = s[":snap/id"]: for a, v in s.items():
      (mapcat (fn [s]
                (let [sid (get s ":snap/id")]
                  (for [[a v] (ordered-pairs s)]
                    (add-datom sid a v))))
              snaps)))))

(defn post-datoms
  "Flatten dry-run social posts into append-only EAVT assertions (G8: status stays dry-run).
  Mirrors kotoba.py post_datoms."
  ([posts] (post-datoms posts "post"))
  ([posts prefix]
   (vec
    (apply concat
           (map-indexed
            (fn [i p]
              (let [pid (str prefix "-" (get p ":post/subject" i))]
                (for [[a v] p]
                  (add-datom pid a v))))
            posts)))))

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
    ;; Clojure integer literals are Long; longs from EDN parse are also Long
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
   - int/float → repr (e.g. '12.4', '92.0', '42')
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
  "Serialize one transaction as a single-line EDN map (the kotoba ingest body shape).
  Mirrors kotoba.py _tx_to_edn byte-for-byte."
  [tx]
  (let [datoms    (get tx ":tx/datoms")
        datoms-s  (str/join " " (map (fn [d]
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
       (spit f (str ";; shionome kotoba Datom log — append-only EAVT transactions "
                    "(content-addressed DAG). DO NOT hand-edit. ADR-2606072200.\n")
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
  json.loads path. Handles: \\\" \\\\ \\/ \\n \\r \\t \\b \\f \\uXXXX."
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
  (println "shionome.methods.kotoba loaded."))
