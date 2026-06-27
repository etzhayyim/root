(ns lg-chat.server
  "OSS HTTP server for lg-chat (chat.etzhayyim.com) — clj port of lg_chat/server.py
  (ADR-2606280030). FastAPI → org.httpkit.server (a bb built-in). Exposes the same
  minimal LangGraph-Cloud-compatible surface:

    POST /runs          → invoke a graph synchronously
    POST /runs/stream   → stream graph supersteps as SSE (ChatPanel target)
    GET  /ok            → liveness
    GET  /health        → readiness
    GET  /health/deep   → readiness + (RW probe skipped — deprecated substrate)

  Sprint 1 ephemeral-only: config.configurable.ephemeral has no checkpointer to
  strip in langgraph-clj (graphs compile without one), so the flag is a no-op
  here — history still lives in browser IndexedDB (ADR-2605230000)."
  (:require [org.httpkit.server :as hk]
            [cheshire.core :as json]
            [clojure.string :as str]
            [langgraph.graph :as g]
            [lg-chat.graphs.agent-chat :as agent-chat]
            [lg-chat.graphs.sodai-submit :as sodai-submit]))

(def ^:private api-key (str/trim (or (System/getenv "LG_API_KEY") "")))

(def graphs {"agent_chat" agent-chat/graph
             "sodai_submit" sodai-submit/graph})

(def ^:private boot-ts (System/currentTimeMillis))

(defn resolve-graph [assistant-id]
  (get graphs (if (str/blank? assistant-id) "agent_chat" assistant-id)))

(defn- authed? [req]
  (or (= "" api-key)
      (= api-key (get-in req [:headers "x-api-key"]))))

(defn- read-body [req]
  (let [b (:body req)]
    (cond
      (nil? b) {}
      (string? b) (json/parse-string b true)
      :else (json/parse-string (slurp b) true))))

(defn- json-resp
  ([m] (json-resp 200 m))
  ([status m] {:status status
               :headers {"Content-Type" "application/json"}
               :body (json/generate-string m)}))

;; bytes never appear in clj graph state, but mirror the py _sanitize contract.
(defn- sanitize [v]
  (cond
    (bytes? v) (str "<bytes:" (count v) "B>")
    (map? v) (into {} (map (fn [[k x]] [k (sanitize x)]) v))
    (sequential? v) (mapv sanitize v)
    :else v))

(defn handler [req]
  (let [uri (:uri req)
        method (:request-method req)]
    (cond
      (and (= method :get) (= uri "/ok"))
      (json-resp {:ok true :graphs (vec (keys graphs)) :version "0.1.0"})

      (and (= method :get) (= uri "/health"))
      (json-resp {:ok true})

      (and (= method :get) (= uri "/health/deep"))
      (json-resp {:ok true :uptimeSec (int (/ (- (System/currentTimeMillis) boot-ts) 1000))
                  :graph true :rw_ok false :rw_roundtrip_ms nil})

      (and (= method :post) (= uri "/runs"))
      (if-not (authed? req)
        (json-resp 401 {:detail "invalid x-api-key"})
        (let [body (read-body req)
              graph (resolve-graph (str (:assistant_id body)))]
          (if (nil? graph)
            (json-resp 404 {:detail (str "unknown graph: " (:assistant_id body))})
            (let [started (System/currentTimeMillis)]
              (try
                (let [result (g/invoke graph (or (:input body) {}))]
                  (json-resp {:ok true :result (sanitize result)
                              :latencyMs (int (- (System/currentTimeMillis) started))}))
                (catch Exception exc
                  (json-resp {:ok false :error (subs (str (.getMessage exc)) 0 (min 500 (count (str (.getMessage exc)))))
                              :errorType (.getSimpleName (class exc))
                              :latencyMs (int (- (System/currentTimeMillis) started))})))))))

      (and (= method :post) (= uri "/runs/stream"))
      (if-not (authed? req)
        (json-resp 401 {:detail "invalid x-api-key"})
        (let [body (read-body req)
              graph (resolve-graph (str (:assistant_id body)))]
          (if (nil? graph)
            (json-resp 404 {:detail (str "unknown graph: " (:assistant_id body))})
            (hk/as-channel
             req
             {:on-open
              (fn [ch]
                (try
                  (doseq [event (g/stream graph (or (:input body) {}))]
                    (hk/send! ch {:status 200 :headers {"Content-Type" "text/event-stream"}
                                  :body (str "data: " (json/generate-string
                                                       {:event "values" :data (sanitize (:state event))}) "\n\n")}
                              false))
                  (catch Exception exc
                    (hk/send! ch (str "data: " (json/generate-string
                                                {:event "error" :data (str (.getMessage exc))}) "\n\n") false))
                  (finally
                    (hk/send! ch "data: {\"event\": \"done\"}\n\n" false)
                    (hk/close ch))))}))))

      :else
      (json-resp 404 {:detail "not found"}))))

(defn start! [& [port]]
  (let [port (or port (Long/parseLong (or (System/getenv "PORT") "8000")))]
    (hk/run-server handler {:port port})
    (println (str "lg-chat clj server up — graphs " (vec (keys graphs)) " on :" port " (ephemeral-only)"))))

(defn -main [& argv]
  (start! (when (first argv) (Long/parseLong (first argv))))
  @(promise))
