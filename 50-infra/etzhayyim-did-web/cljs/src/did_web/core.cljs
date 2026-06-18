(ns did-web.core
  "Request-handling core for the etzhayyim did:web Worker, compiled to ESM and
  delegated to by the thin TypeScript shell (src/worker.ts).

  Migration stance (ADR-2606013800 lineage): the cljs core OWNS a growing set of
  routes; any route it does not own is handed back to `fallback` — the legacy TS
  handler — so the cut-over is incremental and rollback-safe. When every route is
  owned, the fallback becomes the 404/proxy tail and the TS routing is deleted.

  `handle` is intentionally a thin dispatcher over pure route fns; the routing
  decision and any pure transforms live in did-web.routes / did-web.* so they are
  shareable with bb-run unit tests (.cljc).

  CRITICAL interop rule (caught by the build pilot): under :advanced compilation
  the Closure compiler RENAMES dotted property access on objects it cannot type
  (`(.-didDoc deps)` → `d.Qb`). Built-in Web APIs (Request/URL/Response/Headers)
  have externs so `(.-method request)` etc. are safe — but the injected `deps`
  object is OUR untyped JS, so its fields MUST be read with string access via
  `goog.object/get`. Never use `(.-foo deps)` on the injection object."
  (:require [goog.object :as gobj]
            [did-web.router :as router]))

(defn dep
  "Read a field from the injected `deps` object by string key (rename-safe)."
  [deps k]
  (gobj/get deps k))

;; ─── interop helpers ────────────────────────────────────────────────────────

(defn- ->url [request] (js/URL. (.-url request)))

(defn json-response
  "A JSON Response with sane defaults. `opts` may override :status / :content-type
  / :cache (Cache-Control)."
  ([body] (json-response body nil))
  ([body {:keys [status content-type cache]
          :or   {status 200
                 content-type "application/json; charset=utf-8"
                 cache "public, max-age=300"}}]
   (js/Response.
    (if (string? body) body (js/JSON.stringify body))
    #js {:status status
         :headers #js {"content-type" content-type
                       "cache-control" cache}})))

;; ─── route: entity DID document ─────────────────────────────────────────────
;;
;; First route migrated off TS. The static did.json is injected via `deps`
;; (the shell owns the JSON import) — the DI seam that mirrors the actor-cell
;; SubstratePort pattern. Behaviour is byte-for-byte faithful to the TS handler:
;; pretty JSON (2-space) + trailing newline, content-type application/did+json,
;; and the full security-header set.

(def ^:private permissions-policy "interest-cohort=(), browsing-topics=()")

(defn- did-json-route
  "Serve did:web:etzhayyim.com at /.well-known/did.json (GET/HEAD only)."
  [request deps]
  (let [method (.-method request)]
    (if (and (not= method "GET") (not= method "HEAD"))
      (js/Response. "Method Not Allowed"
                    #js {:status 405 :headers #js {"allow" "GET, HEAD"}})
      (js/Response.
       (str (js/JSON.stringify (dep deps "didDoc") nil 2) "\n")
       #js {:status 200
            :headers #js {"content-type" "application/did+json; charset=utf-8"
                          "cache-control" "public, max-age=300, must-revalidate"
                          "access-control-allow-origin" "*"
                          "x-content-type-options" "nosniff"
                          "strict-transport-security" "max-age=31536000; includeSubDomains"
                          "permissions-policy" permissions-policy
                          "x-etzhayyim-no-cookie" "1"}}))))

;; ─── dispatcher ─────────────────────────────────────────────────────────────

(defn handle
  "ESM entry. `deps` is the JS injection object from the shell (static did.json,
  compiled registries, helpers); `fallback` is the legacy TS fetch handler.
  Returns a Response or a Promise<Response>.

  The route decision is delegated to the pure did-web.router (.cljc, bb-tested);
  this fn only maps the decided route → its interop handler, or hands unowned
  routes back to the TS fallback."
  [request env ctx deps fallback]
  (let [url    (->url request)
        method (.-method request)
        {:keys [route]} (router/route {:method method
                                       :path   (.-pathname url)})]
    (case route
      :did-json (did-json-route request deps)
      ;; :fallback (and any not-yet-mapped route) → legacy TS handler
      (fallback request env ctx))))
