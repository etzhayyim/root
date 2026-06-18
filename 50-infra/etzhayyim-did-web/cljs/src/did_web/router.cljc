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
  #{:did-json :donation-json :donate-html :actors-json :actors-html
    :gov-units-json :gov-procedures-json :organism-html
    :actor-did :actor-profile :actor-procedures})

(defn- strip-trailing-slash
  "Normalize a path so \"/donate/\" and \"/donate\" route alike (but keep \"/\")."
  [path]
  (if (and (> (count path) 1) (str/ends-with? path "/"))
    (subs path 0 (dec (count path)))
    path))

(def ^:private actor-did-re      #"^/actor/([^/]+)/did\.json$")
(def ^:private actor-profile-re  #"^/actor/([^/]+)/profile\.json$")
(def ^:private actor-procs-re    #"^/actor/([^/]+)/procedures\.json$")

(defn route
  "Resolve {:method :path} → a route map {:route <kw> & params}.

  Owned by the cljs core (local content/identity surface):
    :did-json :donation-json :donate-html :actors-json :actors-html
    :gov-units-json :gov-procedures-json :gov-html :organism-html
    :actor-did :actor-profile :actor-procedures  (each + :handle, the RAW path
      segment — the core decodes + lower-cases + validates it)

  Everything else → {:route :fallback} (legacy TS handler: ipfs / kotoba block /
  xrpc / reverse proxy). As those migrate, add their branch here + a test."
  [{:keys [path]}]
  (let [p (strip-trailing-slash path)]
    (or
     ;; exact static paths
     (case p
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
       nil)
     ;; parameterized actor paths (matched on the ORIGINAL path, not stripped —
     ;; a trailing slash here is part of no valid actor route)
     (when-let [[_ h] (re-matches actor-did-re path)]     {:route :actor-did       :handle h})
     (when-let [[_ h] (re-matches actor-profile-re path)] {:route :actor-profile   :handle h})
     (when-let [[_ h] (re-matches actor-procs-re path)]   {:route :actor-procedures :handle h})
     ;; not owned → legacy TS handler
     {:route :fallback})))

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
