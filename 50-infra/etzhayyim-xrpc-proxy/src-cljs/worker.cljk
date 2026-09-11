;; etzhayyim XRPC reverse-proxy — ClojureScript (squint) port of the former
;; src/worker.ts (ADR-2606251200 TS→cljs+edn; ADR-2606271400 legacy-prune state).
;;
;; Routes inbound requests on the etzhayyim.com zone to the matching etzhayyim.com-
;; zoned upstream workers via service bindings, letting the etzhayyim.com namespace
;; serve the existing Bluesky stack without redeploying the upstreams:
;;
;;   bsky.etzhayyim.com   → etzhayyim-appview      (AppView)
;;   authn.etzhayyim.com  → etzhayyim-auth         (Passkey)
;;   mcp.etzhayyim.com    → etzhayyim-agentgateway (MCP router)
;;
;; The legacy `atproto.etzhayyim.com → PDS` leg was removed (ADR-2606271400): that
;; host now points to the independent clj+kotoba PDS via a Cloudflare Tunnel, NOT
;; through this proxy.
;;
;; Build: `npm run build` (squint compile → src-cljs/worker.mjs); wrangler `main`
;; points at the compiled .mjs. Env bindings (APPVIEW/AUTHN/MCP: Fetcher) are typed
;; by the Worker runtime, not TS.
(ns worker)

(def host-map
  {"bsky.etzhayyim.com"  {:upstream "APPVIEW" :rewrite-host "bsky.etzhayyim.com"}
   "authn.etzhayyim.com" {:upstream "AUTHN"   :rewrite-host "authn.etzhayyim.com"}
   "mcp.etzhayyim.com"   {:upstream "MCP"     :rewrite-host "mcp.etzhayyim.com"}})

;; Headers DELETED from upstream responses (the proxy never writes a cookie — it
;; removes inbound Set-Cookie). no-cookie: allow strip-list.
(def stripped-response-headers
  ["set-cookie"
   "content-security-policy"
   "content-security-policy-report-only"
   "strict-transport-security"
   "alt-svc"])

(defn build-upstream-request [request rewrite-host]
  (let [original-host (.-hostname (js/URL. (.-url request)))
        upstream-url (js/URL. (.-url request))]
    (set! (.-hostname upstream-url) rewrite-host)
    (set! (.-protocol upstream-url) "https:")
    (set! (.-port upstream-url) "")
    (let [fwd-headers (js/Headers. (.-headers request))]
      (.delete fwd-headers "host")
      (.set fwd-headers "x-forwarded-host" original-host)
      (.set fwd-headers "x-forwarded-proto" "https")
      (js/Request. (.toString upstream-url)
                   #js {:method (.-method request)
                        :headers fwd-headers
                        :body (.-body request)
                        :redirect "manual"}))))

(defn rewrite-upstream-response [upstream original-host rewrite-host]
  (let [headers (js/Headers. (.-headers upstream))]
    (doseq [h stripped-response-headers] (.delete headers h))
    (.set headers "strict-transport-security" "max-age=31536000; includeSubDomains")
    (.set headers "x-proxied-by" "etzhayyim-xrpc-proxy")
    (.set headers "x-proxied-upstream" rewrite-host)
    ;; Rewrite a redirect Location back to the etzhayyim host so the client stays
    ;; on the etzhayyim.com namespace.
    (let [loc (.get headers "location")]
      (when loc
        (try
          (let [loc-url (js/URL. loc (str "https://" rewrite-host "/"))]
            (when (= (.-hostname loc-url) rewrite-host)
              (set! (.-hostname loc-url) original-host)
              (.set headers "location" (.toString loc-url))))
          (catch :default _ nil))))      ; relative or malformed — leave alone
    (js/Response. (.-body upstream)
                  #js {:status (.-status upstream)
                       :statusText (.-statusText upstream)
                       :headers headers})))

(defn ^:async fetch-handler [request env]
  (let [url (js/URL. (.-url request))
        route (get host-map (.-hostname url))]
    (if-not route
      (js/Response. (str "No upstream binding for host: " (.-hostname url))
                    #js {:status 404
                         :headers #js {"content-type" "text/plain; charset=utf-8"}})
      (try
        (let [fetcher (aget env (:upstream route))
              upstream (js-await (.fetch fetcher
                                         (build-upstream-request request (:rewrite-host route))))]
          (rewrite-upstream-response upstream (.-hostname url) (:rewrite-host route)))
        (catch :default err
          (js/Response.
           (str "Service binding fetch failed (" (:upstream route) " → " (:rewrite-host route) "): "
                (if (instance? js/Error err) (.-message err) (str err)))
           #js {:status 502
                :headers #js {"content-type" "text/plain; charset=utf-8"
                              "x-proxied-by" "etzhayyim-xrpc-proxy"
                              "x-proxied-upstream" (str "service:" (:upstream route))}}))))))

(def ^:export default #js {:fetch fetch-handler})
