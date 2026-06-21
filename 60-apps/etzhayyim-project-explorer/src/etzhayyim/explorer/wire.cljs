(ns etzhayyim.explorer.wire
  "Transit (transit+json) wire codec for the kotoba query/sync path — the
   Datomic-client wire standard (ADR-2606201610 follow-up).

   Layering (deliberate): the CID preimage stays canonical-JSON (byte-identical
   across clj/py/rust — a content-addressing invariant), and on-disk snapshots
   stay EDN (`.kotoba.edn`, cljs.reader-native). Transit is used ONLY on the
   WIRE — Datom query responses and the live Datom tail — because it preserves
   rich types (keywords, sets, instants, bignums) and caches repeated map keys,
   which is exactly the Datom shape (thousands of maps sharing attribute
   keywords) and is what Datomic's client protocol uses."
  (:require [cognitect.transit :as t]))

(def ^:private reader (t/reader :json))
(def ^:private writer (t/writer :json))

(defn decode
  "transit+json string → ClojureScript data (keywords/sets/etc. preserved)."
  [s] (t/read reader s))

(defn encode
  "ClojureScript data → transit+json string (the wire form a kotoba node emits)."
  [data] (t/write writer data))

(def content-type "application/transit+json")

(defn fetch-transit
  "Fetch a transit+json resource → Promise of decoded ClojureScript data.
   This is the browser side of a Datomic-style query/sync response."
  [url]
  (-> (js/fetch url #js {:cache "no-cache"
                         :headers #js {"Accept" content-type}})
      (.then (fn [resp]
               (if (.-ok resp) (.text resp)
                   (throw (js/Error. (str "HTTP " (.-status resp)))))))
      (.then decode)))
