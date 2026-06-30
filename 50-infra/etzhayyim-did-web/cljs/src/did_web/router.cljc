(ns did-web.router
  "Pure routing decision for the etzhayyim did:web Worker — NO interop, NO I/O.

  Given a request's method + URL path, decide WHICH route handler owns it (a
  keyword) and extract any pure path parameters. This namespace is .cljc so the
  exact decision that runs in the Worker (compiled by shadow-cljs) is the one
  exercised by the babashka unit tests (run_tests.sh) — the cljs core only adds
  Response construction + dependency injection on top of this.

  Route ownership migrates here incrementally. The cljs core currently OWNS the
  local content/identity surface; the heavy I/O plumbing (ipfs gateway, kotoba
  block CAS, xrpc proxy, reverse proxy) still resolves to :fallback (the legacy
  TS handler) and migrates in a later batch. Keep this table the single source of
  truth for what the cljs core owns vs. delegates."
  (:require [clojure.string :as str]))

;; Routes that only accept GET/HEAD (a non-GET/HEAD request → 405 in the core).
(def get-head-only
  #{:home-html :did-json :donation-json :donate-html :actors-json :actors-html
    :gov-units-json :gov-procedures-json :gov-html :organism-html :system-dynamics-html
    :actor-did :actor-profile :actor-procedures :actor-system-dynamics-html
    :ipfs})

(defn- strip-trailing-slash
  "Normalize a path so \"/donate/\" and \"/donate\" route alike (but keep \"/\")."
  [path]
  (if (and (> (count path) 1) (str/ends-with? path "/"))
    (subs path 0 (dec (count path)))
    path))

(def ^:private actor-did-re      #"^/actor/([^/]+)/did\.json$")
(def ^:private actor-profile-re  #"^/actor/([^/]+)/profile\.json$")
(def ^:private actor-procs-re    #"^/actor/([^/]+)/procedures\.json$")
(def ^:private actor-system-dynamics-re #"^/actor/([^/]+)/system-dynamics/?$")
(def ^:private ipfs-re           #"^/ipfs/([A-Za-z0-9]+)$")

(defn route
  "Resolve {:method :path} → a route map {:route <kw> & params}.

  Owned by the cljs core (local content/identity surface):
    :home-html :did-json :donation-json :donate-html :actors-json :actors-html
    :gov-units-json :gov-procedures-json :gov-html :organism-html
    :system-dynamics-html
    :actor-did :actor-profile :actor-procedures  (each + :handle, the RAW path
      segment — the core decodes + lower-cases + validates it)
    :actor-system-dynamics-html (per-actor HTML dynamics view + :handle)

  Everything else → {:route :fallback} (legacy TS handler: xrpc proxy / reverse
  proxy). As those migrate, add their branch here + a test."
  [{:keys [path method]}]
  (let [p (strip-trailing-slash path)
        get-head? (or (= method "GET") (= method "HEAD"))]
    (or
     ;; method-aware kotoba CAS endpoints (matched BEFORE the generic /xrpc
     ;; fallback, faithful to worker.ts section 2d ordering). A method mismatch
     ;; falls through to :fallback (the generic xrpc proxy), exactly as in TS.
     (when (and (= p "/xrpc/com.etzhayyim.apps.kotoba.block.put") (= method "POST"))
       {:route :kotoba-block-put})
     (when (and (= p "/xrpc/com.etzhayyim.apps.kotoba.block.has") (= method "POST"))
       {:route :kotoba-block-has})
     (when (and (= p "/xrpc/com.etzhayyim.apps.kotoba.root") get-head?)
       {:route :kotoba-root})
     (when (and (= p "/xrpc/com.etzhayyim.apps.kotoba.stats") get-head?)
       {:route :kotoba-stats})
     (when-let [[_ c] (and get-head? (re-matches #"^/kotoba/blocks/([A-Za-z0-9]+)$" path))]
       {:route :kotoba-block-get :cid c})
     ;; exact static paths
     (case p
       "/"                                  {:route :home-html}
       "/index.html"                        {:route :home-html}
       "/.well-known/did.json"            {:route :did-json}
       "/.well-known/donation.json"       {:route :donation-json}
       "/donate"                          {:route :donate-html}
       "/.well-known/actors.json"         {:route :actors-json}
       "/.well-known/gov-units.json"      {:route :gov-units-json}
       "/.well-known/gov-procedures.json" {:route :gov-procedures-json}
       ;; /gov is the one inline-HTML page (not a referenceable builder fn) —
       ;; it stays on the TS fallback until the next batch extracts it.
       "/actors"                          {:route :actors-html}
       "/organism"                        {:route :organism-html}
       "/organism/index.html"             {:route :organism-html}
       "/system-dynamics"                 {:route :system-dynamics-html}
       nil)
     ;; parameterized actor paths (matched on the ORIGINAL path, not stripped —
     ;; a trailing slash here is part of no valid actor route)
     (when-let [[_ h] (re-matches actor-did-re path)]     {:route :actor-did       :handle h})
     (when-let [[_ h] (re-matches actor-profile-re path)] {:route :actor-profile   :handle h})
     (when-let [[_ h] (re-matches actor-procs-re path)]   {:route :actor-procedures :handle h})
     (when-let [[_ h] (re-matches actor-system-dynamics-re path)] {:route :actor-system-dynamics-html :handle h})
     (when-let [[_ c] (re-matches ipfs-re path)]          {:route :ipfs :cid c})
     ;; generic /xrpc/<nsid> → cljs xrpc dispatch (kotoba xrpc endpoints were
     ;; matched above; the cljs handler delegates ONLY the CACAO-crypto auth
     ;; short-circuits back to the TS fallback).
     (when-let [[_ n] (re-matches #"^/xrpc/([A-Za-z0-9._-]+)$" path)] {:route :xrpc :nsid n})
     ;; /gov — civic wayfinding search page (CLJS-owned, shell + gov-search.js).
     (when (= p "/gov")                                  {:route :gov-html})
     ;; everything else (SPA routes, apex landing, …) → cljs reverse proxy
     {:route :reverse-proxy})))

(defn owned?
  "True when the cljs core owns this route (i.e. route is not :fallback)."
  [req]
  (not= :fallback (:route (route req))))

(defn method-allowed?
  "For a GET/HEAD-only owned route, is `method` permitted? Non-owned/other
  routes are always 'allowed' here (their method policy lives in the handler)."
  [route-kw method]
  (if (contains? get-head-only route-kw)
    (or (= method "GET") (= method "HEAD"))
    true))
