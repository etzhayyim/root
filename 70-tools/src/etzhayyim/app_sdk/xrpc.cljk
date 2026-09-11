(ns etzhayyim.app-sdk.xrpc
  "etzhayyim shared app-SDK — the AT-Proto **XRPC** request-shaping module
  (ADR-2606251200 §Decision 4).

  Pure, app-agnostic request builders every `60-apps` app currently re-derives in
  its TypeScript `@etzhayyim/sdk` wrapper: the `/xrpc/<nsid>` URL, bearer auth
  headers, and the query (GET) vs procedure (POST) request shapes. Portable .cljc —
  runs on bb/clj and compiles under squint, so the request shaping is written once
  and shared with the actor/PDS side (mirrors the per-actor build-xrpc-request
  helpers in etzhayyim.{metrics,agent-cmd,mitama,training}).

  These builders are TRANSPORT-FREE: they return a request map
  `{:method :url :headers :params?/:body?}`; the caller's http-fn executes it (so
  the SDK stays testable offline and dispatch is injectable). The SDK's 3rd module
  alongside `record` (validation) and `etzhayyim.tithe` (payment math).")

(defn xrpc-url
  "Build the XRPC endpoint URL: `<base>/xrpc/<nsid>` (one trailing slash on base
  is stripped)."
  [base nsid]
  (let [b (if (and (string? base) (pos? (count base))
                   (= \/ (nth base (dec (count base)))))
            (subs base 0 (dec (count base)))
            base)]
    (str b "/xrpc/" nsid)))

(defn auth-headers
  "Content-Type + optional Bearer Authorization from a token string."
  [token]
  (cond-> {"Content-Type" "application/json"}
    (and token (pos? (count (str token)))) (assoc "Authorization" (str "Bearer " token))))

(defn query
  "Shape a com.atproto.* **query** (GET) request: `{:method :get :url :headers :params}`.
  opts: :token (bearer), :params (query-string map, default {})."
  [base nsid {:keys [token params]}]
  {:method  :get
   :url     (xrpc-url base nsid)
   :headers (auth-headers token)
   :params  (or params {})})

(defn procedure
  "Shape a com.atproto.* **procedure** (POST) request: `{:method :post :url :headers :body}`.
  opts: :token (bearer), :body (the JSON payload value)."
  [base nsid {:keys [token body]}]
  {:method  :post
   :url     (xrpc-url base nsid)
   :headers (auth-headers token)
   :body    body})
