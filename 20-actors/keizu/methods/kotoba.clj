#!/usr/bin/env bb
;; kotoba.clj — keizu 系図 kotoba Datom-log writer (local, content-addressed). ADR-2606066000
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
;; Constitutional posture: an accountability MAP, NEVER a target-list; edge-primary — every
;; derived signal is a concentration/co-occurrence computed on read from edges/flows, never a
;; per-person score (G4); FACTUAL + non-adjudicating; no-doxxing — PII node attrs are
;; unrepresentable (validated upstream by weave). ADR-2606066000.
;;
;; Key-ordering note: edn.cljc reads rels and money as PersistentHashMap (9 keys > 8 threshold),
;; losing EDN insertion order. KEY-ORDER vectors below re-impose seed EDN file order so the
;; emitted datom sequence is byte-identical to kotoba.py.
(ns keizu.methods.kotoba
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [keizu.methods.weave :as w]))

(def ^:private this-file *file*)

(defn log-default []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "keizu.datoms.kotoba.edn")))

;; ── ID key constants (mirrors Python ID_KEYS) ─────────────────────────────────

(def ^:private ID-KEYS #{":node/id" ":committee/id" ":rel/id" ":money/id" ":statement/id"})

;; Canonical attribute orders — mirror Python dict insertion order from the EDN seed.
;; edn.cljc returns PersistentHashMap for maps with >8 keys (rels + money = 9 keys), losing
;; EDN insertion order. These ordered lists re-impose the seed's EDN file order so that the
;; emitted datom sequence is byte-identical to kotoba.py.

(def ^:private NODE-KEY-ORDER
  [":node/scope" ":node/label" ":node/jurisdiction" ":node/organ"
   ":node/sourcing" ":node/sources"])

(def ^:private COMMITTEE-KEY-ORDER
  [":committee/label" ":committee/jurisdiction" ":committee/organ" ":committee/members"
   ":committee/term-from" ":committee/sourcing" ":committee/sources"])

(def ^:private REL-KEY-ORDER
  [":rel/source" ":rel/target" ":rel/kind" ":rel/weight" ":rel/as-of"
   ":rel/non-adjudicating-notice" ":rel/sourcing" ":rel/sources"])

(def ^:private MONEY-KEY-ORDER
  [":money/payer" ":money/payee" ":money/kind" ":money/amount" ":money/currency"
   ":money/as-of" ":money/sourcing" ":money/sources"])

(def ^:private STATEMENT-KEY-ORDER
  [":statement/speaker" ":statement/topic" ":statement/venue"
   ":statement/as-of" ":statement/sourcing" ":statement/sources"])

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

(defn- flatten-row
  "Mirror of Python _flatten: given entity id e, emit one EAVT datom per (non-ID attr,
  scalar value) in canonical key-order. List values are expanded into one datom per item
  (matching Python `for item in (v if isinstance(v, list) else [v])`)."
  [row key-order e out]
  (when e
    (doseq [[k v] (ordered-pairs row key-order)
            :when (not (contains? ID-KEYS k))]
      (let [scalars (if (sequential? v) v [v])]
        (doseq [item scalars]
          (swap! out conj (add-datom e k item)))))))

(defn- omap-items
  "Return [k v] pairs in insertion order from an omap (weave's ::order-tagged map).
  Falls back to (seq m) if no ::order metadata."
  [m]
  (let [order (::w/order (meta m))]
    (if order
      (map (fn [k] [k (get m k)]) order)
      (seq m))))

(defn graph-datoms
  "Flatten the woven relation graph into append-only EAVT assertions. Power-entity nodes only
  (PII node attrs are unrepresentable, validated upstream by weave). Mirrors kotoba.py graph_datoms."
  [g]
  (let [out (atom [])]
    ;; nodes: omap — use ::w/order metadata for insertion order
    (doseq [[_ row] (omap-items (get g "nodes"))]
      (let [e (get row ":node/id")]
        (flatten-row row NODE-KEY-ORDER e out)))
    ;; committees: omap — use ::w/order metadata
    (doseq [[_ row] (omap-items (get g "committees"))]
      (let [e (get row ":committee/id")]
        (flatten-row row COMMITTEE-KEY-ORDER e out)))
    ;; rels: plain vector, 9-key PersistentHashMap — use KEY-ORDER
    (doseq [row (get g "rels")]
      (let [e (get row ":rel/id")]
        (flatten-row row REL-KEY-ORDER e out)))
    ;; money: plain vector, 9-key PersistentHashMap — use KEY-ORDER
    (doseq [row (get g "money")]
      (let [e (get row ":money/id")]
        (flatten-row row MONEY-KEY-ORDER e out)))
    ;; statements: plain vector, 7-key PersistentArrayMap — use KEY-ORDER for consistency
    (doseq [row (get g "statements")]
      (let [e (get row ":statement/id")]
        (flatten-row row STATEMENT-KEY-ORDER e out)))
    @out))

;; ── derived datoms ────────────────────────────────────────────────────────────

(defn derived-datoms
  "Flatten the aggregate, edge-primary concentration metrics into EAVT assertions, each flagged
  :keizu.conc/derived true. Mirrors kotoba.py derived_datoms. NEVER a per-person score or a
  target-list — G4. `c` is (w/concentration g)."
  ([c] (derived-datoms c "keizu.conc"))
  ([c prefix]
   (let [out (atom [])]
     ;; headline counts
     (let [e (str prefix "-counts")]
       (swap! out into
              [(add-datom e ":keizu.conc/node-count"      (get c "node_count"))
               (add-datom e ":keizu.conc/committee-count" (get c "committee_count"))
               (add-datom e ":keizu.conc/rel-count"       (get c "rel_count"))
               (add-datom e ":keizu.conc/money-count"     (get c "money_count"))
               (add-datom e ":keizu.conc/statement-count" (get c "statement_count"))
               (add-datom e ":keizu.conc/derived"         true)]))
     ;; money concentration (by payee) + payer concentration
     (let [mc (get c "money_concentration")
           pc (get c "payer_concentration")
           em (str prefix "-money")]
       (swap! out into
              [(add-datom em ":keizu.conc/money-hhi"   (get mc "hhi"))
               (add-datom em ":keizu.conc/money-total" (get mc "total"))
               (add-datom em ":keizu.conc/payer-hhi"   (get pc "hhi"))
               (add-datom em ":keizu.conc/derived"     true)])
       ;; payee shares — round(share, 4) mirrored via w/pyround
       (doseq [[payee share] (get mc "shares")]
         (let [e (str prefix "-payee-" payee)]
           (swap! out into
                  [(add-datom e ":keizu.conc/payee"   payee)
                   (add-datom e ":keizu.conc/share"   (w/pyround (double share) 4))
                   (add-datom e ":keizu.conc/derived" true)])))
       ;; payer shares
       (doseq [[payer share] (get pc "shares")]
         (let [e (str prefix "-payer-" payer)]
           (swap! out into
                  [(add-datom e ":keizu.conc/payer"   payer)
                   (add-datom e ":keizu.conc/share"   (w/pyround (double share) 4))
                   (add-datom e ":keizu.conc/derived" true)]))))
     ;; committee cross-organ concentration
     (doseq [r (get c "committee_cross_organ")]
       (let [e (str prefix "-xorgan-" (get r "committee"))]
         (swap! out into
                [(add-datom e ":keizu.conc/committee"       (get r "committee"))
                 (add-datom e ":keizu.conc/member-count"    (get r "member_count"))
                 (add-datom e ":keizu.conc/distinct-organs" (get r "distinct_organs"))
                 (add-datom e ":keizu.conc/derived"         true)])))
     ;; cross-committee seats (co-membership)
     (doseq [r (get c "cross_committee_seats")]
       (let [e (str prefix "-xseat-" (get r "seat"))]
         (swap! out into
                [(add-datom e ":keizu.conc/seat"            (get r "seat"))
                 (add-datom e ":keizu.conc/committee-count" (get r "committee_count"))
                 (add-datom e ":keizu.conc/derived"         true)])))
     ;; cross-organ connector seats
     (doseq [r (get c "connector_seats")]
       (let [e (str prefix "-connector-" (get r "seat"))]
         (swap! out into
                [(add-datom e ":keizu.conc/connector-seat" (get r "seat"))
                 (add-datom e ":keizu.conc/organs-bridged" (get r "organs_bridged"))
                 (add-datom e ":keizu.conc/derived"        true)])))
     ;; revolving-door chains (non-adjudicating, as-of)
     (dorun
      (map-indexed
       (fn [i r]
         (let [e (str prefix "-revolving-" i)]
           (swap! out into
                  [(add-datom e ":keizu.conc/revolving-from"   (get r "from_label"))
                   (add-datom e ":keizu.conc/revolving-to"     (get r "to_label"))
                   (add-datom e ":keizu.conc/as-of"            (get r "as_of"))
                   (add-datom e ":keizu.conc/non-adjudicating" true)
                   (add-datom e ":keizu.conc/derived"          true)])))
       (get c "revolving_door")))
     ;; award-and-fund co-occurrence (FACTUAL, non-adjudicating)
     (doseq [r (get c "award_and_fund")]
       (let [e (str prefix "-awardfund-" (get r "node"))]
         (swap! out into
                [(add-datom e ":keizu.conc/award-and-fund-node" (get r "node"))
                 (add-datom e ":keizu.conc/received-total"      (get r "received_total"))
                 (add-datom e ":keizu.conc/donated-total"       (get r "donated_total"))
                 (add-datom e ":keizu.conc/non-adjudicating"    true)
                 (add-datom e ":keizu.conc/derived"             true)])))
     ;; by-jurisdiction
     (doseq [j (get c "by_jurisdiction")]
       (let [e (str prefix "-juris-" (get j "jurisdiction"))]
         (swap! out into
                [(add-datom e ":keizu.conc/jurisdiction" (get j "jurisdiction"))
                 (add-datom e ":keizu.conc/nodes"        (get j "nodes"))
                 (add-datom e ":keizu.conc/committees"   (get j "committees"))
                 (add-datom e ":keizu.conc/money-total"  (get j "money_total"))
                 (add-datom e ":keizu.conc/derived"      true)])))
     @out)))

;; ── JSON-based canonical serialization (byte-identical to kotoba.py) ──────────

(defn- py-float-repr
  "Render a double as Python json.dumps renders it: plain decimal notation
  (no exponential) for |x| in [1e-4, 1e16); matches json.dumps(ensure_ascii=False).
  Copies py-float-repr from weave.cljc verbatim."
  [^double x]
  (cond
    (zero? x) "0.0"
    :else
    (let [s  (Double/toString x)
          ax (Math/abs x)]
      (if (and (>= ax 1.0e-4) (< ax 1.0e16))
        (let [p (.toPlainString (java.math.BigDecimal. s))]
          (if (str/includes? p ".")
            (let [t (str/replace p #"0+$" "")]
              (if (str/ends-with? t ".") (str t "0") t))
            (str p ".0")))
        s))))

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
    ;; Float/Double: use py-float-repr to match Python's json.dumps output exactly
    (or (float? v) (instance? Double v))
    (py-float-repr (double v))
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
    ;; Float/Double: Python _edn_val uses repr(v) which for round values gives e.g. "1.0"
    ;; and for floats with small/large magnitudes matches py-float-repr output
    (or (float? v) (instance? Double v))
    (py-float-repr (double v))
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
       (spit f (str ";; keizu kotoba Datom log — append-only EAVT transactions "
                    "(content-addressed DAG). Accountability map, never a target-list; "
                    "edge-primary, non-adjudicating, no-doxxing. DO NOT hand-edit. ADR-2606066000.\n")
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
  (println "keizu.methods.kotoba loaded."))
