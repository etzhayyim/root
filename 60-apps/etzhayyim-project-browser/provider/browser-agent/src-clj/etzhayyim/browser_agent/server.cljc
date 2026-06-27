(ns etzhayyim.browser-agent.server
  "HTTP server — faithful clj port of server.py (aiohttp SSE) to httpkit.

  aiohttp.web -> org.httpkit.server (bb built-in). Routes:
    GET  /health  -> {:ok true :app \"browser-agent\"}
    POST /search  -> text/event-stream of {type ...} events, terminated by
                     `data: [DONE]`.

  Event parity with python: `phase` transitions per node, `source` per newly
  scraped url, `section` per synthesized section, `error` on failure. The
  python `token` events came from langchain's `on_chat_model_stream`; the clj
  chat seam is non-streaming, so token-level events are intentionally dropped
  (phase/source/section/error/DONE preserved)."
  (:require [cheshire.core :as json]
            [clojure.string :as str]
            [etzhayyim.browser-agent.graph :as graph]
            [etzhayyim.browser-agent.state :as state]
            [org.httpkit.server :as hk]))

(def ^:private phase-map
  {:plan-queries  "planning"
   :search-web    "searching"
   :scrape-pages  "scraping"
   :synthesize    "synthesizing"
   :quality-check "done"})

(defn- sse [ch data]
  (hk/send! ch {:body (str "data: " (json/generate-string data) "\n\n")} false))

(defn- read-json [req]
  (let [b (:body req)]
    (when b (json/parse-string (slurp b) true))))

(defn search-handler
  "POST /search — stream the browser-search graph as Server-Sent Events."
  [req]
  (hk/as-channel
   req
   {:on-open
    (fn [ch]
      (let [body (read-json req)
            query (str/trim (or (:query body) ""))
            page-url (or (:page_url body) "")]
        (if (str/blank? query)
          (hk/send! ch {:status 400
                        :headers {"Content-Type" "application/json"}
                        :body (json/generate-string {:error "query required"})}
                    true)
          (do
            (hk/send! ch {:status 200
                          :headers {"Content-Type" "text/event-stream"
                                    "Cache-Control" "no-cache"
                                    "X-Accel-Buffering" "no"
                                    "Access-Control-Allow-Origin" "*"}
                          :body ""}
                      false)
            (try
              (graph/run-graph
               (state/init-state query page-url)
               (fn [node delta _state]
                 (when-let [p (phase-map node)]
                   (sse ch {:type "phase" :phase p}))
                 (when (= node :scrape-pages)
                   (doseq [r (:scraped-contents delta)]
                     (sse ch {:type "source" :url (:url r)})))
                 (when (= node :synthesize)
                   (doseq [s (:sections delta)]
                     (sse ch {:type "section" :title (:title s) :content (:content s)})))))
              (catch Exception e
                (sse ch {:type "error" :message (.getMessage e)})))
            (hk/send! ch {:body "data: [DONE]\n\n"} false)
            (hk/close ch)))))}))

(defn app
  "Ring handler: /health (GET) and /search (POST)."
  [req]
  (case [(:request-method req) (:uri req)]
    [:get "/health"]
    {:status 200
     :headers {"Content-Type" "application/json"}
     :body (json/generate-string {:ok true :app "browser-agent"})}

    [:post "/search"]
    (search-handler req)

    {:status 404
     :headers {"Content-Type" "application/json"}
     :body (json/generate-string {:error "not found"})}))

(defn -main [& _]
  (let [port (Integer/parseInt (or (System/getenv "PORT") "8000"))]
    (hk/run-server app {:port port :ip "0.0.0.0"})
    (println (str "browser-agent (clj) listening on 0.0.0.0:" port))
    @(promise)))
