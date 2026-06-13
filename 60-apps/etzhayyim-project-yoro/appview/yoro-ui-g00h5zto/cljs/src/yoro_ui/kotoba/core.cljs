(ns yoro-ui.kotoba.core
  "Browser-local kotoba Datom log — public API.

   Call (init!) once at app startup to bind the sha-256 host seam and verify
   chain integrity. Then use (transact! datoms) to append EAVT assertions.

   The log is content-addressed (append-only commit-DAG) and stored in
   localStorage. CIDs are byte-compatible with the Python/JVM implementation
   so logs are portable to a running kotoba engine via kotoba_bridge."
  (:require [kotoba.datom :as d]
            [yoro-ui.kotoba.sha256 :as sha256]
            [yoro-ui.kotoba.log :as log]))

(defonce ^:private initialized? (atom false))

(defn init!
  "Bind the SHA-256 host seam and verify local log integrity.
   Idempotent — safe to call on hot-reload."
  []
  (when-not @initialized?
    (set! d/*sha256-hex* sha256/sha256-hex)
    (reset! initialized? true))
  (let [result (log/verify-chain)]
    (when-not (:ok result)
      (js/console.warn "kotoba: chain broken at tx" (:broken-at result)
                       "— run (yoro-ui.kotoba.log/clear!) to reset"))
    result))

(defn transact!
  "Append a transaction to the local log. Returns the CID string.
   datoms  — seq of [entity attribute value] (use kotoba.datom/add to build)
   opts    :actor  string label for the tx-id (default 'yoro-browser')
           :as-of  ISO-8601 string (default js/Date.now)"
  ([datoms] (transact! datoms {}))
  ([datoms {:keys [actor as-of] :or {actor "yoro-browser"}}]
   (when-not @initialized? (init!))
   (let [prev  (log/head-cid)
         tx-id (str actor "-" (js/Date.now))
         as-of (or as-of (.toISOString (js/Date.)))
         tx    (d/make-tx datoms {:tx-id tx-id :as-of as-of :prev-cid prev})]
     (log/append-tx! tx))))

(defn read-log
  "All local transactions, oldest first."
  []
  (log/read-log))

(defn head-cid
  "CID of the most recent local transaction, or \"\"."
  []
  (log/head-cid))

(defn verify-chain
  "Verify local log chain integrity. Returns {:ok bool :length n :broken-at i}."
  []
  (log/verify-chain))
