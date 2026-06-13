(ns yoro-ui.kotoba.log
  "Browser-local datom log backend — localStorage-backed append-only DAG.

   Mirrors the Clojure (JVM) seam functions (append-tx!, read-log, head-cid,
   verify-chain) from kotoba.datom for the :cljs host. Same EDN line format
   so a log file is interoperable with JVM/babashka tooling.

   Storage: localStorage key 'yoro-kotoba-log-v1'. Entries are EDN lines,
   one per transaction, matching kotoba.datom/tx->edn-line output.
   Individual entry limit is bounded by localStorage's ~5-10 MB quota;
   production upgrade path is OPFS (Origin Private File System)."
  (:require [kotoba.datom :as d]
            [cljs.reader :as edn]
            [clojure.string :as str]))

(def ^:private LOG-KEY "yoro-kotoba-log-v1")

(defn- ls-get [] (when (exists? js/localStorage)
                   (try (.getItem js/localStorage LOG-KEY) (catch js/Error _ nil))))

(defn- ls-set! [v] (when (exists? js/localStorage)
                     (try (.setItem js/localStorage LOG-KEY v) (catch js/Error _ nil))))

(defn read-log
  "All transactions, oldest first. Thread-safe (single-threaded JS)."
  []
  (if-let [raw (ls-get)]
    (try
      (into []
            (comp (map str/trim)
                  (remove #(or (str/blank? %) (str/starts-with? % ";")))
                  (map edn/read-string)
                  (map #(update % :tx/datoms d/normalize-datoms)))
            (str/split-lines raw))
      (catch js/Error e
        (js/console.warn "kotoba/log: read-log parse error" (.-message e))
        []))
    []))

(defn head-cid
  "CID of the most recent transaction, or \"\" if the log is empty."
  []
  (or (:tx/cid (peek (read-log))) ""))

(defn append-tx!
  "Append one EDN transaction line. Returns the CID."
  [tx]
  (let [existing (or (ls-get) d/log-header)
        new-line  (str (d/tx->edn-line tx) "\n")]
    (ls-set! (str existing new-line))
    (:tx/cid tx)))

(defn verify-chain
  "Recompute every CID from (datoms, prev). Returns {:ok bool :length n :broken-at i}."
  []
  (let [txs (read-log)]
    (loop [i 0 prev ""]
      (if (= i (count txs))
        {:ok true :length (count txs) :broken-at -1}
        (let [tx (nth txs i)]
          (if (or (not= (:tx/cid tx) (d/tx-cid (:tx/datoms tx) prev))
                  (not= (:tx/prev tx) prev))
            {:ok false :length (count txs) :broken-at i}
            (recur (inc i) (:tx/cid tx))))))))

(defn clear!
  "Wipe the local log. Irreversible — use only in dev/test."
  []
  (when (exists? js/localStorage)
    (try (.removeItem js/localStorage LOG-KEY) (catch js/Error _ nil))))
