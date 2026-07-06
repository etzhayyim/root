(ns meibo-worker.core
  "meibo 名簿 — Cloudflare Worker core (ADR-2607062200: public API + minimal
  browsable UI over the verified legal-institution directory registry).

  Read-only, stateless compute over public EDN data — no signing, no custody,
  no state writes on a visitor's behalf; fits the `no-server-key`
  read-only-public-compute exemption (ADR-2605231525 / ADR-2606072802)
  cleanly, same as saisei-worker. G1/G2/G10 are enforced by
  `meibo.methods.directory` / `meibo.methods.coverage-report` themselves
  (20-actors/meibo/methods/*.cljc, required verbatim below) — this namespace
  only adds HTTP routing and anonymous aggregate access logging."
  (:require [clojure.string :as str]
            [meibo.methods.edn :as edn]
            [meibo.methods.directory :as dir]
            [meibo.methods.coverage-report :as coverage]
            [meibo-worker.data-gen :as data]
            [meibo-worker.ui :as ui]))

(defonce ^:private loaded (atom nil))

(defn- ensure-loaded! []
  (or @loaded
      (reset! loaded
              (->> (edn/read-edn data/legal-directory-edn-str)
                   (filter #(contains? % ":dir/id"))
                   vec))))

(def ^:private cors-headers
  #js {"access-control-allow-origin" "*"
       "access-control-allow-methods" "GET, OPTIONS"
       "access-control-allow-headers" "content-type"})

(defn- json-response [data status]
  (js/Response.
   (js/JSON.stringify (clj->js data))
   #js {:status status
        :headers (js/Object.assign #js {"content-type" "application/json; charset=utf-8"} cors-headers)}))

(defn- html-response [html]
  (js/Response. html #js {:status 200 :headers #js {"content-type" "text/html; charset=utf-8"}}))

(defn- today-bucket []
  (let [d (js/Date.)
        pad #(.padStart (str %) 2 "0")]
    (str (.getUTCFullYear d) "-" (pad (inc (.getUTCMonth d))) "-" (pad (.getUTCDate d)))))

(defn- log-access!
  "Anonymous aggregate-only access log — same posture as saisei-worker's:
  no cookie, no IP/UA capture, no per-visitor field."
  [env route juris-id]
  (when-let [ae (.-MEIBO_ANALYTICS env)]
    (try
      (.writeDataPoint ae #js {:blobs #js [route (or juris-id "")]
                               :doubles #js [1]
                               :indexes #js [(today-bucket)]})
      (catch :default _ nil))))

(defn- juris-str [v]
  (cond
    (nil? v) nil
    (and (string? v) (str/starts-with? v ":")) v
    :else (str ":" v)))

(defn- handle-directory [env juris-param]
  (let [entries (ensure-loaded!)
        juris-id (juris-str juris-param)
        result (if juris-id (dir/by-jurisdiction juris-id entries) [])]
    (log-access! env "/api/directory" juris-id)
    (json-response {"jurisdiction" juris-id "entries" result} 200)))

(defn- handle-coverage [env]
  (let [entries (ensure-loaded!)
        cov (coverage/coverage entries)]
    (log-access! env "/api/coverage" nil)
    (json-response cov 200)))

(defn handle
  [request env _ctx]
  (let [url (js/URL. (.-url request))
        path (.-pathname url)
        method (.-method request)
        juris-param (.get (.-searchParams url) "jurisdiction")]
    (cond
      (= method "OPTIONS")
      (js/Promise.resolve (js/Response. nil #js {:status 204 :headers cors-headers}))

      (= path "/health")
      (js/Promise.resolve (js/Response. "ok" #js {:status 200}))

      (= path "/")
      (js/Promise.resolve (html-response ui/page-html))

      (and (= path "/api/directory") (= method "GET"))
      (js/Promise.resolve (handle-directory env juris-param))

      (and (= path "/api/coverage") (= method "GET"))
      (js/Promise.resolve (handle-coverage env))

      :else
      (js/Promise.resolve
       (json-response {"error" "not found"
                        "routes" ["GET /" "GET /health" "GET /api/directory?jurisdiction=jp" "GET /api/coverage"]}
                       404)))))
