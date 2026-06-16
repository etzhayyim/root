(ns meisai.methods.kotoba
  "kotoba 言葉 — meisai content-addressed EAVT Datom log.
  1:1 Clojure port of `methods/kotoba.py` (ADR-2606122400).

  Subset: vectors [], maps {}, :keyword strings, \"string\", number, bool, nil.
  Keywords are kept as\":...\" strings (not Clojure keywords) to mirror Python.
  SHA-256 via java.security.MessageDigest; file I/O via java.io.File."
  (:require [clojure.string :as str])
  #?(:clj (:import [java.security MessageDigest]
                   [java.io File])))

;; ── basic helpers ──────────────────────────────────────────────────────────

(defn add
  "One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."
  [entity attr value]
  [":db/add" entity attr value])

;; ── content-addressing ─────────────────────────────────────────────────────

(defn- json-escape [s]
  (-> s
      (str/replace "\\" "\\\\")
      (str/replace "\"" "\\\"")
      (str/replace "\b" "\\b")
      (str/replace "\f" "\\f")
      (str/replace "\n" "\\n")
      (str/replace "\r" "\\r")
      (str/replace "\t" "\\t")))

(defn- json-str [s]
  (str "\"" (json-escape s) "\""))

(defn- json-val [v]
  (cond
    (true? v) "true"
    (false? v) "false"
    (number? v) (str v)
    (string? v) (json-str v)
    :else (json-str (str v))))

(defn- canonical
  "Byte-identical to Python's _canonical: json.dumps with
  sort_keys=True and separators=(',',':')."
  [datoms prev-cid]
  (let [datoms-json (str "["
                         (str/join ","
                                   (map (fn [d]
                                          (str "["
                                               (str/join "," (map json-val d))
                                               "]"))
                                        datoms))
                         "]")]
    (str "{\"datoms\":" datoms-json ",\"prev\":" (json-str prev-cid) "}")))

(defn tx-cid
  "Content address = sha256 over (prev-cid, datoms) → a commit-DAG CID."
  ([datoms]
   (tx-cid datoms ""))
  ([datoms prev-cid]
   #?(:clj
      (let [md (MessageDigest/getInstance "SHA-256")
            ^bytes bs (.getBytes (canonical datoms prev-cid) "UTF-8")]
        (.update md bs)
        (str "b" (apply str (map #(format "%02x" (bit-and % 0xFF)) (.digest md)))))
      :cljs
      (throw (ex-info "tx-cid requires SHA-256 on the JVM" {})))))

(defn make-tx
  "Bundle datoms into a content-addressed transaction map."
  [datoms {:keys [tx-id as-of prev-cid]}]
  {:tx/id tx-id
   :tx/as-of as-of
   :tx/prev (or prev-cid "")
   :tx/cid (tx-cid datoms (or prev-cid ""))
   :tx/count (count datoms)
   :tx/datoms datoms})

;; ── EDN serialization ───────────────────────────────────────────────────────

(defn- _edn_val [v]
  (cond
    (true? v) "true"
    (false? v) "false"
    (number? v) (str v)
    (string? v) (if (str/starts-with? v ":")
                  v
                  (json-str v))
    (sequential? v) (str "[" (str/join " " (map _edn_val v)) "]")
    :else (json-str (str v))))

(defn tx->edn
  "Render a transaction map as EDN (matches Python `_tx_to_edn`)."
  [tx]
  (let [datoms-str (str/join " "
                             (map (fn [d]
                                    (str "[" (str/join " " (map _edn_val d)) "]"))
                                  (:tx/datoms tx)))
        prev (:tx/prev tx)
        cid (:tx/cid tx)]
    (str "{:tx/id " (:tx/id tx)
         " :tx/as-of " (:tx/as-of tx)
         " :tx/prev " (json-str prev)
         " :tx/cid " (json-str cid)
         " :tx/count " (:tx/count tx)
         " :tx/datoms [" datoms-str "]}")))

;; ── minimal EDN reader (subset) ─────────────────────────────────────────────

(def ^:private tok-re
  ;; Python: _TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
  #"[\s,]+|;[^\n]*|(\[|\]|\{|\}|\"(?:\\.|[^\"\\])*\"|[^\s,\[\]{}]+)")

(defn- tokens [s]
  (let [m (re-matcher tok-re s)]
    ((fn step []
       (lazy-seq
        (when (.find m)
          (let [t (.group m 1)]
            (if (nil? t)
              (step)
              (cons t (step))))))))))

(defn- atom-of [t]
  (cond
    (str/starts-with? t "\"")
    (-> (subs t 1 (dec (count t)))
        (str/replace "\\\"" "\"")
        (str/replace "\\\\" "\\"))

    (= t "true") true
    (= t "false") false
    (= t "nil") nil

    (str/starts-with? t ":") t

    :else
    (let [as-long (try (Long/parseLong t)
                       (catch #?(:clj Exception :cljs :default) _ ::nan))]
      (if (not= as-long ::nan)
        as-long
        (let [as-dbl (try (Double/parseDouble t)
                          (catch #?(:clj Exception :cljs :default) _ ::nan))]
          (if (not= as-dbl ::nan) as-dbl t))))))

(def ^:private end-marker ::end)

(defn- parse-step [toks i]
  (let [t (nth toks i)
        i (inc i)]
    (cond
      (= t "[")
      (loop [i i, out []]
        (let [[x i] (parse-step toks i)]
          (if (= x end-marker)
            [out i]
            (recur i (conj out x)))))

      (= t "{")
      (loop [i i, out {}]
        (let [[k i] (parse-step toks i)]
          (if (= k end-marker)
            [out i]
            (let [[v i] (parse-step toks i)]
              (recur i (assoc out k v))))))

      (or (= t "]") (= t "}"))
      [end-marker i]

      :else
      [(atom-of t) i])))

(defn parse-edn
  "Parse ONE EDN form (map / vector / atom) from a string."
  [s]
  (let [toks (vec (tokens s))]
    (first (parse-step toks 0))))

;; ── log I/O ───────────────────────────────────────────────────────────────

(defn- log-default []
  #?(:clj
     (let [f (File. "20-actors/meisai/data/persisted/meisai.datoms.kotoba.edn")]
       (.getAbsolutePath f))
     :cljs nil))

(defn append-tx
  "Append ONE transaction to the append-only log. Returns the tx CID."
  ([tx]
   (append-tx tx (log-default)))
  ([tx log-path]
   #?(:clj
      (let [f (File. (str log-path))]
        (.mkdirs (.getParentFile f))
        (when-not (.exists f)
          (spit f (str ";; meisai kotoba Datom log — append-only EAVT transactions "
                       "(content-addressed DAG). MEMBER-OWN card statements only; this file "
                       "lives under the gitignored data/ and is NEVER committed, pinned, or "
                       "published (G3). DO NOT hand-edit. ADR-2606122400.\n")))
        (spit f (str (tx->edn tx) "\n") :append true)
        (:tx/cid tx))
      :cljs
      (throw (ex-info "append-tx requires file I/O on the JVM" {})))))

(defn read-log
  "Read transactions from log file."
  ([]
   (read-log (log-default)))
  ([log-path]
   #?(:clj
      (let [f (File. (str log-path))]
        (if-not (.exists f)
          []
          (into []
                (comp (map str/trim)
                      (remove str/blank?)
                      (remove #(str/starts-with? % ";"))
                      (map parse-edn))
                (str/split-lines (slurp f)))))
      :cljs
      (throw (ex-info "read-log requires file I/O on the JVM" {})))))

(defn head-cid
  "Return the CID of the last transaction in the log (empty string if none)."
  ([]
   (head-cid (log-default)))
  ([log-path]
   (let [txs (read-log log-path)]
     (if (seq txs)
       (get (last txs) ":tx/cid" "")
       ""))))

(defn verify-chain
  "Recompute every CID from its datoms + prev; verify the DAG is intact.
  Returns {:ok bool :length int :broken_at int}."
  ([]
   (verify-chain (log-default)))
  ([log-path]
   (let [txs (read-log log-path)]
     (loop [prev ""
            i 0]
       (if (>= i (count txs))
         {:ok true :length (count txs) :broken_at -1}
         (let [tx (nth txs i)
               datoms (get tx ":tx/datoms" [])
               expect (tx-cid datoms prev)]
           (if (and (= (get tx ":tx/cid") expect)
                    (= (get tx ":tx/prev") prev))
             (recur expect (inc i))
             {:ok false :length (count txs) :broken_at i})))))))
