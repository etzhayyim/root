(ns did-web.core
  "Request-handling core for the etzhayyim did:web Worker, compiled to ESM and
  delegated to by the thin TypeScript shell (src/worker.ts).

  Migration stance (operator decision 2026-06-18): the cljs core OWNS the local
  content/identity surface (DID docs, actor records, donation + atlas pages);
  the heavy I/O plumbing (ipfs gateway, kotoba block CAS, xrpc proxy, reverse
  proxy) is routed by the same cljs router but still handled by the legacy TS
  `fallback` until a later batch — so the cut-over is route-by-route and
  rollback-safe. The route DECISION lives in did-web.router (.cljc, bb-tested);
  this namespace only adds Response construction + dependency injection.

  CRITICAL interop rule (caught by the build pilot): under :advanced compilation
  the Closure compiler RENAMES dotted property access on objects it cannot type
  (`(.-didDoc deps)` → `d.Qb`). Built-in Web APIs (Request/URL/Response/Headers)
  have externs so `(.-method request)` etc. are safe — but the injected `deps`
  object is OUR untyped JS, so its fields MUST be read with string access via
  `goog.object/get`. Never use `(.-foo deps)` on the injection object."
  (:require [goog.object :as gobj]
            [did-web.router :as router]
            [did-web.ipfs :as ipfs]
            [did-web.kotoba :as kotoba]
            [did-web.proxy :as proxy]
            [did-web.xrpc :as xrpc]))

;; ─── injected-deps access (rename-safe) ──────────────────────────────────────

(defn dep
  "Read a field from the injected `deps` object by string key (rename-safe)."
  [deps k]
  (gobj/get deps k))

(defn- call
  "Invoke an injected closure `deps[k]` with args (rename-safe)."
  [deps k & args]
  (apply (gobj/get deps k) args))

;; ─── header sets (byte-faithful to worker.ts) ────────────────────────────────

(def ^:private permissions-policy "interest-cohort=(), browsing-topics=()")

;; CORS + the standard security set shared by the local JSON surfaces.
(def ^:private base-sec
  {"access-control-allow-origin" "*"
   "x-content-type-options" "nosniff"
   "strict-transport-security" "max-age=31536000; includeSubDomains"
   "permissions-policy" permissions-policy
   "x-etzhayyim-no-cookie" "1"})

;; HTML pages: no CORS (same-origin), CSP set per-route.
(def ^:private html-sec
  {"x-content-type-options" "nosniff"
   "strict-transport-security" "max-age=31536000; includeSubDomains"
   "permissions-policy" permissions-policy
   "x-etzhayyim-no-cookie" "1"})

;; ACTOR_JSON_HEADERS — note: max-age=60 and NO permissions-policy (matches TS).
(def ^:private actor-json-headers
  {"content-type" "application/json; charset=utf-8"
   "cache-control" "public, max-age=60, must-revalidate"
   "access-control-allow-origin" "*"
   "x-content-type-options" "nosniff"
   "strict-transport-security" "max-age=31536000; includeSubDomains"
   "x-etzhayyim-no-cookie" "1"})

(defn- resp
  "Build a js/Response. `headers` is a Clojure map with string keys (rename-safe
  via clj->js). `body` may be a string or nil."
  [body status headers]
  (js/Response. body #js {:status status :headers (clj->js headers)}))

(defn- json-pretty [x] (str (js/JSON.stringify x nil 2) "\n"))
(defn- json-compact [x] (str (js/JSON.stringify x) "\n"))

(defn- method-not-allowed
  "A fresh 405 Response per call — a Response body is a single-use stream in the
  Workers runtime, so a shared instance must not be returned for two requests."
  []
  (js/Response. "Method Not Allowed"
                #js {:status 405 :headers #js {"allow" "GET, HEAD"}}))

;; ─── local JSON routes ───────────────────────────────────────────────────────

(defn- did-json-route [deps]
  (resp (json-pretty (dep deps "didDoc")) 200
        (assoc base-sec
               "content-type" "application/did+json; charset=utf-8"
               "cache-control" "public, max-age=300, must-revalidate")))

(defn- donation-json-route [deps]
  (resp (json-pretty (dep deps "donationPolicy")) 200
        (assoc base-sec
               "content-type" "application/json; charset=utf-8"
               "cache-control" "public, max-age=300, must-revalidate")))

(defn- actors-json-route
  "Async: buildActorsJson(env) → Promise. Pretty JSON."
  [deps env]
  (.then (call deps "buildActorsJson" env)
         (fn [obj]
           (resp (json-pretty obj) 200
                 (assoc base-sec
                        "content-type" "application/json; charset=utf-8"
                        "cache-control" "public, max-age=300, must-revalidate")))))

(defn- gov-units-route
  "Served from ACTOR_KV (gov-atlas:index). Async kvGet(env, key) → string|nil."
  [deps env]
  (.then (call deps "kvGet" env "gov-atlas:index")
         (fn [raw]
           (let [body (if raw raw "{\"error\":\"gov-atlas index not provisioned (run gen-gov-atlas-index + kv put gov-atlas:index)\"}")
                 status (if raw 200 503)]
             (resp (str body "\n") status
                   (assoc base-sec
                          "content-type" "application/json; charset=utf-8"
                          "cache-control" "public, max-age=300, must-revalidate"))))))

(defn- gov-procedures-route [deps]
  (let [m (dep deps "govProcMeta")]
    (resp (json-compact
           #js {:graph "actors-v1"
                :adr #js ["2606021600" "2606042330"]
                :note "Observational mirror: public administrative procedures grouped by owning gov entity-actor handle. NOT the government, NOT an official channel, never filed on anyone's behalf (→ toritsugi, gated). All rows :representative / :unverified-seed (G5)."
                :generatedAt (gobj/get m "generatedAt")
                :count (gobj/get m "total")
                :owners (gobj/get m "owners")
                :jurisdictions (gobj/get m "jurisdictions")
                :procedures (dep deps "govProcList")})
          200
          (assoc base-sec
                 "content-type" "application/json; charset=utf-8"
                 "cache-control" "public, max-age=300, must-revalidate"))))

;; ─── local HTML routes ───────────────────────────────────────────────────────

(defn- html-resp [body csp]
  (resp body 200
        (assoc html-sec
               "content-type" "text/html; charset=utf-8"
               "cache-control" "public, max-age=300, must-revalidate"
               "content-security-policy" csp)))

(defn- home-route [deps]
  (html-resp (dep deps "homeHtml")
             "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'"))

(defn- donate-route [deps]
  (html-resp (dep deps "donateHtml")
             "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"))

(defn- actors-html-route [deps]
  (html-resp (call deps "actorsHtml")
             "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'"))

(defn- organism-route [deps]
  (html-resp (call deps "organismHtml")
             "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'"))

;; ─── per-actor routes (async, kotoba-first resolution via injected deps) ──────

(defn- norm-handle [raw] (.toLowerCase (js/decodeURIComponent raw)))

(defn- actor-did-route [deps env ctx raw-handle]
  (let [handle (norm-handle raw-handle)]
    (cond
      (not (call deps "handleValid" handle))
      (resp (js/JSON.stringify
             #js {:error "HandleInvalid"
                  :message "handle must be 1-63 chars, lowercase alnum + hyphen, no leading/trailing hyphen"})
            400 {"content-type" "application/json; charset=utf-8"})

      (not (call deps "isKnownHandle" handle))
      (resp (js/JSON.stringify
             #js {:error "HandleNotInRegistry"
                  :message (str "handle '" handle "' matches a namespaced registry shape but is not registered")
                  :registry "com.etzhayyim.apps.unispsc"
                  :registryTotalCount (dep deps "unispscTotal")})
            404 {"content-type" "application/json; charset=utf-8"
                 "cache-control" "public, max-age=60, must-revalidate"})

      :else
      (.then
       (call deps "resolveActorRecord" handle env ctx)
       (fn [rec]
         (let [doc (if rec
                     (call deps "toDidDoc" rec env)
                     (call deps "buildPerActorDidDoc" handle env))
               source (or (when rec (gobj/get rec "source")) "scaffold")
               base-headers (assoc base-sec
                                   "content-type" "application/did+json; charset=utf-8"
                                   "cache-control" "public, max-age=60, must-revalidate"
                                   "x-etzhayyim-actor-source" source)
               finish (fn [cid]
                        (let [hdrs (if cid
                                     (assoc base-headers
                                            "x-etzhayyim-did-doc-cid" cid
                                            "link" (str "<https://etzhayyim.com/ipfs/" cid ">; rel=\"canonical\"; type=\"application/did+json\""))
                                     base-headers)]
                          (resp (json-pretty doc) 200 hdrs)))]
           (if rec
             (.then (call deps "didDocCid" rec env) finish)
             (finish nil))))))))

(defn- actor-profile-route [deps env ctx raw-handle]
  (let [handle (norm-handle raw-handle)]
    (cond
      (not (call deps "handleValid" handle))
      (resp (js/JSON.stringify #js {:error "HandleInvalid"}) 400 actor-json-headers)

      :else
      (.then
       (call deps "resolveActorRecord" handle env ctx)
       (fn [rec]
         (if-not rec
           (resp (js/JSON.stringify
                  #js {:error "ProfileNotFound"
                       :message (str "'" handle "' is not a registered actor; profiles for free-form handles resolve via the PDS, not the actor registry")})
                 404 actor-json-headers)
           (resp (json-pretty (call deps "toGetProfileView" rec)) 200
                 (assoc actor-json-headers "x-etzhayyim-actor-source" (gobj/get rec "source")))))))))

(defn- actor-procedures-route [deps raw-handle]
  (let [handle (norm-handle raw-handle)]
    (if-not (call deps "handleValid" handle)
      (resp (js/JSON.stringify #js {:error "HandleInvalid"}) 400 actor-json-headers)
      (let [procs (call deps "govProcsByOwner" handle)]
        (resp (json-pretty
               #js {:handle handle
                    :did (str "did:web:etzhayyim.com:actor:" handle)
                    :adr #js ["2606021600" "2606042330"]
                    :note "Observational mirror of public procedures done at this administrative unit. NOT the government, NOT an official channel; never filed on anyone's behalf (→ toritsugi, gated). All rows :representative / :unverified-seed (G5)."
                    :count (.-length procs)
                    :procedures procs})
              200 actor-json-headers)))))

;; ─── dispatcher ──────────────────────────────────────────────────────────────

(defn handle
  "ESM entry. `deps` is the JS injection object from the shell (static data +
  leaf closures); `fallback` is the legacy TS fetch handler. Returns a Response
  or a Promise<Response>. The route decision is the pure did-web.router; this fn
  maps the decided route → its interop handler, enforces GET/HEAD-only where the
  router says so, and hands unowned routes back to the TS fallback."
  [request env ctx deps fallback]
  (let [url    (js/URL. (.-url request))
        method (.-method request)
        {:keys [route handle cid nsid]} (router/route {:method method
                                                       :path   (.-pathname url)})]
    (if-not (router/method-allowed? route method)
      (method-not-allowed)
      (case route
        :home-html           (home-route deps)
        :did-json            (did-json-route deps)
        :donation-json       (donation-json-route deps)
        :donate-html         (donate-route deps)
        :actors-json         (actors-json-route deps env)
        :actors-html         (actors-html-route deps)
        :gov-units-json      (gov-units-route deps env)
        :gov-procedures-json (gov-procedures-route deps)
        :organism-html       (organism-route deps)
        :actor-did           (actor-did-route deps env ctx handle)
        :actor-profile       (actor-profile-route deps env ctx handle)
        :actor-procedures    (actor-procedures-route deps handle)
        :ipfs                (ipfs/handle-ipfs request env cid)
        ;; kotoba member-signed block CAS (ADR-2605312345 / 2605231525)
        :kotoba-block-put    (kotoba/handle-block-put request env)
        :kotoba-block-has    (kotoba/handle-block-has request env)
        :kotoba-root         (kotoba/handle-root-get url env)
        :kotoba-stats        (kotoba/handle-stats-get url env)
        :kotoba-block-get    (.then (kotoba/serve-block-from-kv cid env)
                                    (fn [r] (or r (fallback request env ctx))))
        ;; generic /xrpc dispatch (delegates only CACAO-crypto auth to fallback)
        :xrpc                (xrpc/handle request env ctx deps fallback nsid)
        ;; default site path → cljs reverse proxy to the yoro Worker
        :reverse-proxy       (proxy/reverse-proxy request env)
        ;; :fallback (/gov inline HTML) → legacy TS handler
        (fallback request env ctx)))))
