(ns saisei-worker.core
  "saisei 再生 — Cloudflare Worker core (ADR-2607061800 follow-up: public API +
  minimal interactive UI over the existing R0 registry).

  Read-only, stateless compute over public EDN data — no signing, no custody,
  no state writes on a visitor's behalf, so this fits the `no-server-key`
  read-only-public-compute exemption (ADR-2605231525 / clarified by
  ADR-2606072802) without any new governance carve-out. G2/G3/G4/G5/G7/G10 are
  enforced by `saisei.methods.filing-plan` / `saisei.methods.coverage-report`
  themselves (orgs/etzhayyim/com-etzhayyim-saisei/saisei/methods/*.cljc) — this
  namespace only adds HTTP routing, a JSON wire adapter, and anonymous
  aggregate access logging (day/route/jurisdiction counts — no per-visitor
  identity, no cookies, no client-side tracking script; Workers Analytics
  Engine writes server-side only)."
  (:require [clojure.string :as str]
            [saisei.methods.edn :as edn]
            [saisei.methods.filing-plan :as plan]
            [saisei.methods.coverage-report :as coverage]
            [saisei-worker.data-gen :as data]
            [saisei-worker.ui :as ui]))

(defonce ^:private loaded (atom nil))

(defn- ensure-loaded!
  "Parse the build-time-embedded registries once per isolate (module-level
  memoization — a fresh isolate just re-parses, which is cheap: ~150 small
  EDN records, no network round-trip either way)."
  []
  (or @loaded
      (reset! loaded
              {:procs (->> (edn/read-edn data/procedure-registry-edn-str)
                           (filter #(contains? % ":proc/id"))
                           vec)
               :juris (->> (edn/read-edn data/jurisdictions-edn-str)
                           (filter #(contains? % ":juris/id"))
                           (reduce (fn [m j] (assoc m (get j ":juris/id") j)) {}))
               :legal-directory (->> (edn/read-edn data/legal-directory-edn-str)
                                     (filter #(contains? % ":dir/id"))
                                     vec)})))

(def ^:private cors-headers
  #js {"access-control-allow-origin" "*"
       "access-control-allow-methods" "GET, POST, OPTIONS"
       "access-control-allow-headers" "content-type"})

(defn- json-response [data status]
  (js/Response.
   (js/JSON.stringify (clj->js data))
   #js {:status status
        :headers (js/Object.assign #js {"content-type" "application/json; charset=utf-8"} cors-headers)}))

(defn- html-response [html]
  (js/Response. html #js {:status 200 :headers #js {"content-type" "text/html; charset=utf-8"}}))

(defn- today-bucket
  "Coarse UTC day bucket for the analytics index — intentionally the ONLY
  time granularity kept; no per-request timestamp, no visitor identity."
  []
  (let [d (js/Date.)
        pad #(.padStart (str %) 2 "0")]
    (str (.getUTCFullYear d) "-" (pad (inc (.getUTCMonth d))) "-" (pad (.getUTCDate d)))))

(defn- log-access!
  "Anonymous aggregate-only access log (Workers Analytics Engine). blobs =
  [route, jurisdiction-or-empty, outcome]; doubles = [1] (a plain counter);
  indexes = [day bucket]. No cookie, no IP/UA capture, no per-visitor field —
  matches the same no-tracking-script posture tate's own test suite enforces
  on its static site (test_site.cljc), just server-side instead of absent."
  [env route juris-id outcome]
  (when-let [ae (.-SAISEI_ANALYTICS env)]
    (try
      (.writeDataPoint ae #js {:blobs #js [route (or juris-id "") (or outcome "")]
                               :doubles #js [1]
                               :indexes #js [(today-bucket)]})
      (catch :default _ nil))))

(defn- juris-str [v]
  (cond
    (nil? v) ":jp"
    (and (string? v) (str/starts-with? v ":")) v
    :else (str ":" v)))

(defn- handle-coverage [env]
  (let [{:keys [procs juris]} (ensure-loaded!)
        cov (coverage/coverage procs juris)]
    (log-access! env "/api/coverage" nil "ok")
    (json-response cov 200)))

(defn- handle-filing-plan [env body-str]
  (let [{:keys [procs juris legal-directory]} (ensure-loaded!)
        parsed (try (js->clj (js/JSON.parse (if (str/blank? body-str) "{}" body-str)))
                    (catch :default _ nil))]
    (if (nil? parsed)
      (do (log-access! env "/api/filing-plan" nil "bad-request")
          (json-response {"error" "expected JSON body, e.g. {\"jurisdiction\":\"jp\"}"} 400))
      (let [situation {":sit/id" "sit:http" ":sit/jurisdiction" (juris-str (get parsed "jurisdiction"))}
            plan-out (plan/build-plan situation procs juris legal-directory)]
        (log-access! env "/api/filing-plan" (get plan-out "jurisdiction") (get plan-out "status"))
        (json-response plan-out 200)))))

(defn handle
  "Cloudflare fetch-handler entrypoint. request/env/ctx per the standard
  Workers ExportedHandler triple."
  [request env _ctx]
  (let [url (js/URL. (.-url request))
        path (.-pathname url)
        method (.-method request)]
    (cond
      (= method "OPTIONS")
      (js/Promise.resolve (js/Response. nil #js {:status 204 :headers cors-headers}))

      (= path "/health")
      (js/Promise.resolve (js/Response. "ok" #js {:status 200}))

      (= path "/")
      (js/Promise.resolve (html-response ui/page-html))

      (and (= path "/api/coverage") (= method "GET"))
      (js/Promise.resolve (handle-coverage env))

      (and (= path "/api/filing-plan") (= method "POST"))
      (-> (.text request)
          (.then (fn [body-str] (handle-filing-plan env body-str))))

      :else
      (js/Promise.resolve
       (json-response {"error" "not found"
                        "routes" ["GET /" "GET /health" "GET /api/coverage" "POST /api/filing-plan"]}
                       404)))))
