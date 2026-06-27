(ns sheets.kotoba-datomic
  "kotoba datomic XRPC client for lg-sheets (clj port of lg_sheets/kotoba_datomic.py).

  Wraps ai.etzhayyim.apps.kotoba.datomic.{transact,q,pull} — the canonical
  write/read surface for spreadsheets (graph sheets-v1). httpx -> babashka.http-client
  (ADR-2606280030 / actor-tree httpx->bb port pattern, PR #2612); JSON -> cheshire.
  Synchronous (blocking) — the Python AsyncClient becomes a plain per-call client.

  Endpoint resolution honors KOTOBA_XRPC_URL / KOTOBA_URL (default in-cluster
  Service :8080). Auth = Bearer JWT (KOTOBA_BEARER)."
  (:require [babashka.http-client :as http]
            [cheshire.core :as json]
            [clojure.string :as str]
            [sheets.edn-tx :as edn-tx])
  (:import [java.security MessageDigest]))

(def kotoba-xrpc
  (str/replace
   (or (System/getenv "KOTOBA_XRPC_URL")
       (System/getenv "KOTOBA_URL")
       "http://kotoba.kotoba.svc.cluster.local:8080")
   #"/+$" ""))

(def kotoba-bearer (or (System/getenv "KOTOBA_BEARER") ""))

;; ── content-addressed graph CID (kotoba_cid / graph_cid_for_label) ────────────

(def ^:private b32-alphabet "abcdefghijklmnopqrstuvwxyz234567")

(defn- base32-lower-nopad
  "RFC-4648 base32 (lowercase, no padding) — matches base64.b32encode().lower().rstrip('=')."
  [^bytes data]
  (let [sb (StringBuilder.)]
    (loop [i 0 buffer 0 bits 0]
      (cond
        (>= bits 5)
        (let [bits' (- bits 5)
              idx (bit-and (unsigned-bit-shift-right buffer bits') 0x1f)]
          (.append sb (.charAt b32-alphabet idx))
          (recur i buffer bits'))

        (< i (count data))
        (let [b (bit-and (aget data i) 0xff)]
          (recur (inc i) (bit-or (bit-shift-left buffer 8) b) (+ bits 8)))

        :else
        (do
          (when (> bits 0)
            (let [idx (bit-and (bit-shift-left buffer (- 5 bits)) 0x1f)]
              (.append sb (.charAt b32-alphabet idx))))
          (.toString sb))))))

(defn kotoba-cid [^bytes payload]
  (let [digest (.digest (MessageDigest/getInstance "SHA-256") payload)
        prefix (byte-array [(unchecked-byte 0x01) (unchecked-byte 0x71)
                            (unchecked-byte 0x12) (unchecked-byte 0x20)])
        cid (byte-array (concat (seq prefix) (seq digest)))]
    (str "b" (base32-lower-nopad cid))))

(defn graph-cid-for-label
  "Stable kotoba graph CID from a human-readable label (multibase passthrough)."
  [label]
  (if (and (str/starts-with? label "b") (re-matches #"b[a-z2-7]{58,80}" label))
    label
    (kotoba-cid (.getBytes ^String label "UTF-8"))))

(def default-graph (graph-cid-for-label (or (System/getenv "KOTOBA_GRAPH") "sheets-v1")))

(defn- headers []
  (if (str/blank? kotoba-bearer)
    {"Content-Type" "application/json"}
    {"Authorization" (str "Bearer " kotoba-bearer) "Content-Type" "application/json"}))

(defn- post-json [path body]
  (http/post (str kotoba-xrpc "/xrpc/" path)
             {:headers (headers) :body (json/generate-string body) :throw false}))

;; ── attribute-folding for pull ────────────────────────────────────────────────

(defn- bare-attr [a]
  (let [s (str a)]
    (if (str/starts-with? s ":") (subs s 1) s)))

(defn datoms->attr-map
  "Fold pull datoms ({a, v_edn, added}) into {bare_attr: value}."
  [datoms]
  (when (seq datoms)
    (let [out (reduce (fn [acc d]
                        (if (or (not (map? d)) (false? (get d "added")))
                          acc
                          (if-let [a (get d "a")]
                            (assoc acc (bare-attr a) (edn-tx/parse-edn-value (get d "v_edn" "")))
                            acc)))
                      {} datoms)]
      (when (seq out) out))))

;; ── client record ─────────────────────────────────────────────────────────────

(defrecord KotobaDatomic [graph])

(defn make
  ([] (->KotobaDatomic default-graph))
  ([graph] (->KotobaDatomic graph)))

(defn transact [dm ops & {:keys [expected-parent]}]
  (let [body (cond-> {:graph (:graph dm) :tx_edn (edn-tx/encode-tx-data ops)}
               expected-parent (assoc :expected_parent expected-parent))
        resp (post-json "ai.etzhayyim.apps.kotoba.datomic.transact" body)]
    (when (>= (:status resp) 400)
      (throw (ex-info "kotoba transact failed" {:status (:status resp) :body (:body resp)})))
    (json/parse-string (:body resp))))

(defn q
  ([dm query-edn] (q dm query-edn nil))
  ([dm query-edn inputs-edn]
   (let [body (cond-> {:graph (:graph dm) :query_edn query-edn}
                (seq inputs-edn) (assoc :inputs_edn inputs-edn))
         resp (post-json "ai.etzhayyim.apps.kotoba.datomic.q" body)]
     (when (>= (:status resp) 400)
       (throw (ex-info "kotoba q failed" {:status (:status resp) :body (:body resp)})))
     (let [rows (or (get (json/parse-string (:body resp)) "rows_edn") [])]
       (mapv (fn [row] (mapv edn-tx/parse-edn-value row)) rows)))))

(defn pull [dm entity]
  (let [body {:graph (:graph dm) :entity entity}
        resp (post-json "ai.etzhayyim.apps.kotoba.datomic.pull" body)]
    (cond
      (= 404 (:status resp)) nil
      (>= (:status resp) 400) (throw (ex-info "kotoba pull failed"
                                              {:status (:status resp) :body (:body resp)}))
      :else (datoms->attr-map (or (get (json/parse-string (:body resp)) "datoms") [])))))
