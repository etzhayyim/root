(ns yoro-ui.interop.atproto
  "cljs port of the $lib/atproto-agent XRPC adapter (minimal slice).

   All XRPC goes to the PDS gateway (atproto.etzhayyim.com) — Candidate C
   topology: yoro.etzhayyim.com serves the SPA only, the PDS is the sole XRPC
   endpoint (see 60-apps/etzhayyim-project-yoro/CLAUDE.md §XRPC).

   Token resolution mirrors $lib/atproto-agent client.ts:
   (1) explicit bearer opt → (2) session accessJwt → (3) token-provider
   (passkey session JWT bridge). Unauthenticated calls simply omit the header
   and the caller handles 401 fail-open.

   Session probe rule (CLAUDE.md CRITICAL): get-session reads LOCAL state only —
   never fires com.atproto.server.getSession XRPC on unauthenticated bootstrap."
  (:require [re-frame.core :as rf]))

(def default-service "https://atproto.etzhayyim.com")

;; Public Bluesky AppView — used for unauthenticated discover/public queries
;; (atproto.etzhayyim.com is a PDS that requires auth for most reads)
(def public-appview "https://public.api.bsky.app")

;; "What's Hot" feed generator on Bluesky — used as discover feed
;; until com.etzhayyim.yoro.feed.getDiscoverFeed is deployed to yoro.etzhayyim.com
(def whats-hot-feed "at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.generator/whats-hot")

(defonce service (atom default-service))
(defonce session (atom nil))          ; {:accessJwt ... :did ...}
(defonce token-provider (atom nil))   ; (fn [] js/Promise<string|nil>)

(defn set-service! [url] (reset! service url))
(defn set-session! [s] (reset! session s))
(defn set-token-provider! [f] (reset! token-provider f))

(defn get-session
  "LOCAL session state only — no XRPC fired (401-noise rule)."
  []
  @session)

(defn- resolve-token []
  (cond
    (:accessJwt @session) (js/Promise.resolve (:accessJwt @session))
    @token-provider ((@token-provider))
    :else (js/Promise.resolve nil)))

(defn- xrpc-fetch [method nsid {:keys [params body timeout-ms]
                                :or {timeout-ms 5000}}]
  (-> (resolve-token)
      (.then
       (fn [token]
         (let [qs (when (seq params)
                    (str "?" (->> params
                                  (map (fn [[k v]]
                                         (str (js/encodeURIComponent (name k)) "="
                                              (js/encodeURIComponent (str v)))))
                                  (interpose "&")
                                  (apply str))))
               url (str @service "/xrpc/" nsid qs)
               controller (js/AbortController.)
               timeout-id (js/setTimeout #(.abort controller) timeout-ms)
               headers (cond-> {"Content-Type" "application/json"}
                         token (assoc "Authorization" (str "Bearer " token)))]
           (-> (js/fetch url
                         (clj->js (cond-> {:method method
                                           :headers headers
                                           :signal (.-signal controller)}
                                    body (assoc :body (js/JSON.stringify (clj->js body))))))
               (.then (fn [res]
                        (js/clearTimeout timeout-id)
                        (if (.-ok res)
                          (-> (.json res)
                              (.then #(js->clj % :keywordize-keys true)))
                          (js/Promise.reject
                           (ex-info "xrpc error" {:status (.-status res) :nsid nsid})))))
               (.catch (fn [e]
                         (js/clearTimeout timeout-id)
                         (js/Promise.reject e)))))))))

(defn at-query
  "XRPC query (GET). Returns js/Promise of keywordized response."
  ([nsid] (at-query nsid {}))
  ([nsid params] (xrpc-fetch "GET" nsid {:params params})))

(defn at-public-query
  "XRPC query against the public Bluesky AppView — no auth, no token resolution.
   Used for unauthenticated discover-feed reads until yoro.etzhayyim.com deploys."
  ([nsid params]
   (let [qs (when (seq params)
               (str "?" (->> params
                             (map (fn [[k v]]
                                    (str (js/encodeURIComponent (name k)) "="
                                         (js/encodeURIComponent (str v)))))
                             (interpose "&")
                             (apply str))))
         url (str public-appview "/xrpc/" nsid qs)]
     (-> (js/fetch url (clj->js {:method "GET"
                                  :headers {"Content-Type" "application/json"}}))
         (.then (fn [res]
                  (if (.-ok res)
                    (-> (.json res) (.then #(js->clj % :keywordize-keys true)))
                    (js/Promise.reject
                     (ex-info "xrpc error" {:status (.-status res) :nsid nsid})))))))))

(defn discover-feed-query
  "Fetch the discover feed: uses public AppView getFeed with What's Hot generator.
   Returns same {feed cursor} shape as com.etzhayyim.yoro.feed.getDiscoverFeed."
  [params]
  (at-public-query "app.bsky.feed.getFeed"
                   (assoc params :feed whats-hot-feed)))

(defn at-procedure
  "XRPC procedure (POST). Returns js/Promise of keywordized response."
  ([nsid] (at-procedure nsid {}))
  ([nsid body] (xrpc-fetch "POST" nsid {:body body})))

;; ---------------------------------------------------------------------------
;; re-frame fx — fire an XRPC call, dispatch on-success/on-failure
;;
;; {:atproto/procedure {:nsid "com.atproto.repo.createRecord"
;;                      :body {...}
;;                      :on-success [:ev] :on-failure [:ev]}}

(defn- run-fx [call-fn {:keys [nsid params body on-success on-failure]}]
  (-> (call-fn nsid (or params body {}))
      (.then (fn [resp]
               (when on-success
                 (if (fn? on-success)
                   (on-success resp)
                   (rf/dispatch (conj on-success resp))))))
      (.catch (fn [e]
                (when on-failure
                  (if (fn? on-failure)
                    (on-failure e)
                    (rf/dispatch (conj on-failure (str e)))))))))

(rf/reg-fx :atproto/query (fn [opts] (run-fx at-query opts)))
(rf/reg-fx :atproto/procedure (fn [opts] (run-fx at-procedure opts)))
(rf/reg-fx :atproto/public-query (fn [opts] (run-fx at-public-query opts)))
