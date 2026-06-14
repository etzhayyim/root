;; kotoba.clj — danjo kotoba Datom-log writer (local, content-addressed).
;;
;; Clojure port of kotoba.py (ADR-2605301600 + 2605262130 + 2605312345), Wave 1 of the
;; clj-native migration (ADR-2606142300). The local, autonomous-loop write path: a
;; self-driving heartbeat appends content-addressed transactions to a local append-only
;; EDN log with NO external I/O, so danjo runs its observe→cross-reference→persist
;; public-accountability cycle on the Murakumo fleet with no human or live node in the loop.
;;
;; Constitutional posture preserved by construction (the censor's EYE, never the SWORD):
;; only FACTUAL discrepancy observations over the public record are representable, NEVER a
;; verdict (G4 — :danjo.obs/non-adjudicating is always true; `derived-datoms` RAISES if a
;; verdict token appears in any attr); every observation cites ≥2 source CIDs (G5) + an open
;; method-note CID (G6). The loop persists exactly what `analyze/run-all` produced.
;;
;;   graph-datoms / derived-datoms → EAVT [:db/add E A V] assertions (op :db/add only —
;;     append-only, 非終末論, no :db/retract). derived-datoms is flagged non-adjudicating (G4).
;;   tx-cid / make-tx / append-tx / read-log / head-cid / verify-chain — content-addressed commit-DAG.
;;
;; The content-bearing **derived-observation transaction is BYTE-IDENTICAL with kotoba.py**:
;; `tx_cid` = "b" + sha256 over json.dumps({"prev",..,"datoms",..}, ensure_ascii=False,
;; sort_keys, separators (",",":")) — reproduced by `canonical-json`. NOTE: `graph-datoms`
;; emission order is canonicalized (sorted by attr) for parser-independent determinism — the
;; JSON key order kotoba.py inherits from dict iteration is not reproducible through cheshire,
;; and a deterministic order is the resume-safety property that actually matters. clojure.edn
;; reads the log back natively. stdlib + cheshire (bundled in bb) only.
(ns root.danjo.methods.kotoba
  (:require [cheshire.core :as json]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.java.io :as io])
  (:import [java.security MessageDigest]))

(def forbidden-verdict-tokens
  "G4 — an attr whose name implies a VERDICT must never appear in a persisted observation."
  ["verdict" "guilt" "wrongdoing" "finding" "culprit" "illegal" "crime" "violation"
   "unlawful" "fraud" "sanction"])

(defn- add
  "One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."
  [entity attr value]
  [:db/add entity attr value])

(defn graph-datoms
  "Flatten the public procurement corpus into append-only EAVT assertions. E = the record's
   public-record CID; attrs are :gov.procurement/*. Public pre-published record only (G3).
   Per-record attrs are emitted in a deterministic (sorted) order."
  [records]
  (vec
   (mapcat
    (fn [r]
      (when (and (map? r) (get r "cid"))
        (let [e (get r "cid")]
          (->> (dissoc r "cid")
               (sort-by key)
               (map (fn [[k v]] (add e (keyword (str "gov.procurement/" k)) v)))))))
    records)))

(defn- oget
  "Read an observation field tolerant of string (canonical analyze.cljc / Python) OR keyword keys."
  ([o k] (oget o k nil))
  ([o k d] (let [s (get o (name k))] (if (some? s) s (get o k d)))))

(defn- obs-id
  "A stable, deterministic entity id for an observation (category + first source CID)."
  [o]
  (let [cid0 (or (first (oget o :sourceRecordCids)) "?")]
    (str "danjo-obs:" (or (oget o :category) "?") ":" cid0)))

(defn derived-datoms
  "Flatten danjo.discrepancyObservation records into append-only EAVT assertions, each carrying
   :danjo.obs/non-adjudicating true (G4 — a FACT, never a verdict), ≥2 source CIDs (G5), and the
   open method-note CID (G6). RAISES if a verdict token ever creeps into an attr (G4 structural)."
  [observations]
  (let [out (vec
             (mapcat
              (fn [o]
                (let [e (obs-id o)]
                  [(add e :danjo.obs/category (keyword (str/replace (str (oget o :category "?")) #"^:" "")))
                   (add e :danjo.obs/non-adjudicating true)
                   (add e :danjo.obs/pattern (oget o :observedPattern ""))
                   (add e :danjo.obs/source-record-cids (vec (oget o :sourceRecordCids [])))
                   (add e :danjo.obs/method-note-cid (oget o :methodNoteCid ""))
                   (add e :danjo.obs/known-false-positive-modes (vec (oget o :knownFalsePositiveModes [])))
                   (add e :danjo.obs/sourcing :representative)]))
              observations))]
    (doseq [d out]
      (let [attr (str/lower-case (str (nth d 2)))]
        (when (some #(str/includes? attr %) forbidden-verdict-tokens)
          (throw (ex-info (str "G4: verdict attr " (pr-str (nth d 2)) " is unrepresentable") {:datom d})))))
    out))

;; ── content-addressed commit-DAG (byte-identical with kotoba.py tx_cid) ──────────
;; canonical JSON = json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",",":")).
;; keywords render as their ":"-prefixed string (matching kotoba.py's ":db/add" string literals).
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
    (keyword? x)    (esc-str (str x))   ; :db/add → ":db/add" (matches kotoba.py string literal)
    (string? x)     (esc-str x)
    (boolean? x)    (if x "true" "false")
    (integer? x)    (str x)
    (nil? x)        "null"
    :else           (throw (ex-info (str "canonical-json: unsupported type " (type x)) {:value x}))))

(defn- sha256-hex
  [^String s]
  (let [d (.digest (MessageDigest/getInstance "SHA-256") (.getBytes s "UTF-8"))]
    (apply str (map #(format "%02x" (bit-and (int %) 0xff)) d))))

(defn tx-cid
  "Content address = \"b\" + sha256 over (prev_cid, datoms) → a commit-DAG. Byte-identical w/ kotoba.py."
  ([datoms] (tx-cid datoms ""))
  ([datoms prev-cid]
   (str "b" (sha256-hex (canonical-json {"prev" prev-cid "datoms" (vec datoms)})))))

(defn make-tx
  [datoms {:keys [tx-id as-of prev-cid] :or {prev-cid ""}}]
  {:tx/id     tx-id
   :tx/as-of  as-of
   :tx/prev   prev-cid
   :tx/cid    (tx-cid datoms prev-cid)
   :tx/count  (count datoms)
   :tx/datoms (vec datoms)})

;; ── EDN serialization (matches kotoba.py _tx_to_edn: ":"-strings/keywords bare, others quoted) ──
(defn- edn-val
  [v]
  (cond
    (boolean? v)    (if v "true" "false")
    (integer? v)    (str v)
    (float? v)      (str v)
    (keyword? v)    (str v)                       ; :db/add → :db/add (bare)
    (string? v)     (if (str/starts-with? v ":") v (json/generate-string v))
    (sequential? v) (str "[" (str/join " " (map edn-val v)) "]")
    :else           (json/generate-string (str v))))

(defn tx->edn
  [tx]
  (let [datoms (str/join " " (map (fn [d] (str "[" (str/join " " (map edn-val d)) "]")) (:tx/datoms tx)))]
    (str "{:tx/id " (:tx/id tx) " :tx/as-of " (:tx/as-of tx)
         " :tx/prev " (json/generate-string (:tx/prev tx))
         " :tx/cid " (json/generate-string (:tx/cid tx))
         " :tx/count " (:tx/count tx)
         " :tx/datoms [" datoms "]}")))

(def log-default "../data/persisted/danjo.datoms.kotoba.edn")

(defn append-tx
  "Append ONE transaction to the append-only log (never rewrites). Returns the tx CID."
  ([tx] (append-tx tx log-default))
  ([tx log-path]
   (let [f (io/file log-path)]
     (.mkdirs (.getParentFile f))
     (when-not (.exists f)
       (spit f (str ";; danjo kotoba Datom log — append-only EAVT transactions "
                    "(content-addressed DAG). The censor's EYE, never the SWORD: "
                    "non-adjudicating observations only (G4). DO NOT hand-edit. ADR-2605301600.\n")))
     (spit f (str (tx->edn tx) "\n") :append true)
     (:tx/cid tx))))

(defn read-log
  "Read the append-only log back (clojure.edn — native). Skips the comment header."
  ([] (read-log log-default))
  ([log-path]
   (let [f (io/file log-path)]
     (if-not (.exists f)
       []
       (->> (str/split-lines (slurp f))
            (map str/trim)
            (remove #(or (str/blank? %) (str/starts-with? % ";")))
            (mapv edn/read-string))))))

(defn head-cid
  ([] (head-cid log-default))
  ([log-path] (let [txs (read-log log-path)] (if (seq txs) (:tx/cid (last txs)) ""))))

(defn verify-chain
  "Recompute every CID from its datoms + prev; verify the DAG is intact. {:ok :length :broken-at}."
  ([] (verify-chain log-default))
  ([log-path]
   (let [txs (read-log log-path)]
     (loop [i 0 prev "" ts txs]
       (if (empty? ts)
         {:ok true :length (count txs) :broken-at -1}
         (let [tx (first ts)
               expect (tx-cid (:tx/datoms tx []) prev)]
           (if (or (not= (:tx/cid tx) expect) (not= (:tx/prev tx) prev))
             {:ok false :length (count txs) :broken-at i}
             (recur (inc i) (:tx/cid tx) (rest ts)))))))))
