(ns etzhayyim.registry.sync-node
  "A kotoba SYNC NODE — serves the live Datom tail over the XRPC endpoint
     GET /xrpc/com.etzhayyim.apps.kotoba.sync.subscribe?cursor=N
   as Server-Sent Events whose frames are transit+json (the Datomic-client wire
   standard). The browser's live tail (live.cljs) connects here and decodes each
   frame with transit-cljs — keywords/types preserved end to end.

   The stream is the canonical kotoba Datom state: it reads the vitals EAVT
   snapshot (content-addressed EDN on disk) and live-tails its datoms from the
   requested cursor, then holds the connection with heartbeats. A minimal
   java.net socket server (no extra HTTP dep); production form is a bb task under
   launchd fronted by the apex Worker.

   Note: this is the WIRE only — the CID preimage stays canonical-JSON and the
   on-disk log stays EDN."
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [cognitect.transit :as t])
  (:import [java.net ServerSocket Socket]
           [java.io BufferedReader InputStreamReader OutputStream ByteArrayOutputStream]
           [java.util.concurrent Executors]))

(def port 8720)
(def vitals-path "../public/organism/vitals.kotoba.edn")
(def endpoint "com.etzhayyim.apps.kotoba.sync.subscribe")

(defn- transit-json [data]
  (let [out (ByteArrayOutputStream.)]
    (t/write (t/writer out :json) data)
    (.toString out "UTF-8")))

(defn- load-datoms
  "The kotoba Datom stream: vitals EAVT [e a v tx op] → [entity attr value] adds."
  []
  (->> (edn/read-string (slurp vitals-path))
       (filter (fn [[_ _ _ _ op]] (= op :add)))
       (mapv (fn [[e a v _ _]] [e a v]))))

(defn- write-line [^OutputStream out ^String s]
  (.write out (.getBytes s "UTF-8")) (.flush out))

(def ^:private sse-headers
  (str "HTTP/1.1 200 OK\r\n"
       "Content-Type: text/event-stream\r\n"
       "Cache-Control: no-cache\r\n"
       "Connection: keep-alive\r\n"
       "Access-Control-Allow-Origin: *\r\n"   ; EventSource cross-origin (browser:8710 → node:8720)
       "\r\n"))

(defn- cursor-of [req-line]
  (or (some-> (re-find #"cursor=(\d+)" (str req-line)) second parse-long) 0))

(defn- handle [^Socket sock datoms]
  (try
    (let [in (BufferedReader. (InputStreamReader. (.getInputStream sock)))
          out (.getOutputStream sock)
          req-line (.readLine in)]
      (loop [l (.readLine in)]                      ; drain request headers
        (when (and l (not (str/blank? l))) (recur (.readLine in))))
      (if (and req-line (str/includes? req-line endpoint))
        (let [cursor (cursor-of req-line)
              tail (subvec datoms (min cursor (count datoms)))]
          (write-line out sse-headers)
          (write-line out (str "event: open\ndata: "
                               (transit-json {:wire/format "transit+json"
                                              :sync/endpoint endpoint
                                              :sync/from-cursor cursor
                                              :sync/total (count datoms)}) "\n\n"))
          ;; live-tail the datoms from the cursor as transit+json frames
          (doseq [[i d] (map-indexed vector tail)]
            (write-line out (str "id: " (+ cursor i) "\ndata: "
                                 (transit-json {:datom d :seq (+ cursor i)
                                                :as-of (+ cursor i 1)}) "\n\n"))
            (Thread/sleep 200))
          ;; keep the subscription open (heartbeat comments)
          (dotimes [_ 100000]
            (write-line out ": hb\n\n")
            (Thread/sleep 5000)))
        ;; any other path → a tiny status response
        (do (write-line out "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nAccess-Control-Allow-Origin: *\r\n\r\n")
            (write-line out (str "kotoba sync node · GET /xrpc/" endpoint "?cursor=0\n")))))
    (catch Exception _ nil)
    (finally (try (.close sock) (catch Exception _ nil)))))

(defn -main [& _]
  (let [datoms (load-datoms)
        pool (Executors/newFixedThreadPool 16)
        server (ServerSocket. port)]
    (println (format "kotoba sync node on :%d — %d datoms" port (count datoms)))
    (println (format "  GET http://localhost:%d/xrpc/%s?cursor=0  (transit+json SSE)" port endpoint))
    (loop []
      (let [sock (.accept server)]
        (.submit pool ^Runnable (fn [] (handle sock datoms)))
        (recur)))))
