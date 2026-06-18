(ns did-web.proxy
  "Apex reverse proxy — faithful cljs port of buildUpstreamRequest +
  rewriteUpstreamResponse + applyApexSecurityHeaders (src/worker.ts §4). All paths
  the cljs core does not own locally and that are not /xrpc/* are reverse-proxied
  to the yoro Worker via the YORO service binding (which bypasses the CF Bot
  Management block that public-HTTP fetch hits inside the same zone).

  This is pure request/response plumbing — header stripping + host rewrite — so it
  uses only Web API externs (URL/Headers/Request/Response) plus the YORO binding
  (called via rename-safe .call interop)."
  (:require [goog.object :as gobj]))

(def ^:private upstream-host "yoro.etzhayyim.com")
(def ^:private permissions-policy "interest-cohort=(), browsing-topics=()")

(def ^:private stripped-response-headers
  ["set-cookie" "content-security-policy" "content-security-policy-report-only"
   "strict-transport-security" "alt-svc"])

(def ^:private stripped-request-headers ["cookie" "host"])
(def ^:private clear-cookie-paths #{"/" "/privacy"})

(defn- strip-incoming-cookies! [headers]
  (doseq [h stripped-request-headers] (.delete headers h)))

(defn- apply-apex-security! [headers pathname]
  (.set headers "strict-transport-security" "max-age=31536000; includeSubDomains")
  (.set headers "permissions-policy" permissions-policy)
  (when (contains? clear-cookie-paths pathname)
    (.set headers "clear-site-data" "\"cookies\"")))

(defn- build-upstream-request [request]
  (let [u (js/URL. (.-url request))]
    (set! (.-hostname u) upstream-host)
    (set! (.-protocol u) "https:")
    (set! (.-port u) "")
    (let [fwd (js/Headers. (.-headers request))]
      (strip-incoming-cookies! fwd)
      (.set fwd "x-forwarded-host" "etzhayyim.com")
      (.set fwd "x-forwarded-proto" "https")
      (js/Request. (.toString u)
                   #js {:method (.-method request)
                        :headers fwd
                        :body (.-body request)
                        :redirect "manual"}))))

(defn- rewrite-upstream-response [upstream pathname]
  (let [headers (js/Headers. (.-headers upstream))]
    (doseq [h stripped-response-headers] (.delete headers h))
    (apply-apex-security! headers pathname)
    (.set headers "x-proxied-by" "etzhayyim-did-web")
    (.set headers "x-proxied-upstream" upstream-host)
    (.set headers "x-etzhayyim-no-cookie" "1")
    (let [loc (.get headers "location")]
      (when loc
        (try
          (let [loc-url (js/URL. loc (str "https://" upstream-host "/"))]
            (when (= (.-hostname loc-url) upstream-host)
              (set! (.-hostname loc-url) "etzhayyim.com")
              (.set headers "location" (.toString loc-url))))
          (catch :default _ nil))))
    (js/Response. (.-body upstream)
                  #js {:status (.-status upstream)
                       :statusText (.-statusText upstream)
                       :headers headers})))

(defn reverse-proxy
  "Reverse-proxy `request` to the yoro Worker via env.YORO. Returns
  Promise<Response>. Faithful to worker.ts §4 (service-binding fetch + 502 on
  failure)."
  [request env]
  (let [pathname (.-pathname (js/URL. (.-url request)))
        yoro (gobj/get env "YORO")
        yoro-fetch (gobj/get yoro "fetch")]
    (-> (.call yoro-fetch yoro (build-upstream-request request))
        (.then (fn [upstream] (rewrite-upstream-response upstream pathname)))
        (.catch (fn [err]
                  (js/Response.
                   (str "Service binding fetch to kotodama-yoro failed: "
                        (if (instance? js/Error err) (.-message err) (str err)))
                   #js {:status 502
                        :headers #js {"content-type" "text/plain; charset=utf-8"
                                      "x-proxied-by" "etzhayyim-did-web"
                                      "x-proxied-upstream" "service:kotodama-yoro"}}))))))
