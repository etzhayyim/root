(ns did-web.router
  "Pure routing decision for the etzhayyim did:web Worker — NO interop, NO I/O.

  Given a request's method + URL path, decide WHICH route handler owns it (a
  keyword) and extract any pure path parameters. This namespace is .cljc so the
  exact decision that runs in the Worker (compiled by shadow-cljs) is the one
  exercised by the babashka unit tests (run_tests.sh) — the cljs core only adds
  Response construction + dependency injection on top of this.

  Route ownership migrates here incrementally: a path resolves to a specific
  keyword once the cljs core implements it, otherwise to :fallback (the legacy
  TS handler). Keep this table the single source of truth for what the cljs core
  owns vs. delegates."
  (:require [clojure.string :as str]))

(defn- strip-trailing-slash
  "Normalize a path so \"/donate/\" and \"/donate\" route alike (but keep \"/\")."
  [path]
  (if (and (> (count path) 1) (str/ends-with? path "/"))
    (subs path 0 (dec (count path)))
    path))

(defn route
  "Resolve {:method :path} → a route map {:route <kw> & params}.

  Currently owned by the cljs core:
    :did-json   — /.well-known/did.json   (entity DID document)

  Everything else → {:route :fallback} (legacy TS handler). As routes are
  ported, add their branch here + a test, and implement them in did-web.core."
  [{:keys [path]}]
  (let [p (strip-trailing-slash path)]
    (cond
      (= p "/.well-known/did.json") {:route :did-json}
      :else                          {:route :fallback})))

(defn owned?
  "True when the cljs core owns this route (i.e. route is not :fallback)."
  [req]
  (not= :fallback (:route (route req))))
