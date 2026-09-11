;; etzhayyim.deps — deps.toml analysis pure logic (cljc port, wave 3a).
;;
;; Pure-logic port of the non-IO core of
;; 70-tools/etzhayyim-py/src/etzhayyim/deps.py
;;
;; Ported (pure logic, no IO):
;;   build-kv-records       — build Cloudflare KV entries from actor list
;;   summarize-deps-graph   — compute link-coverage scorecard from a graph API response map
;;   filter-layers          — filter layer entries by section and/or tag
;;   render-deps-tree       — format layer DAG as a text tree string
;;   render-deps-mermaid    — format layer DAG as a Mermaid BT diagram string
;;   deps-mv-name           — extract VIEW name from CREATE MATERIALIZED VIEW stmt
;;   deps-summary           — extract summary counts from a loaded deps.toml data map
;;   migrations-by-status   — filter migrations list by status string
;;   governance-score       — compute governance score from WIT/manifest/app findings
;;
;; IO legs deferred (NOT ported):
;;   _load                  — TOML file read (babashka.fs/slurp + clj-toml or clj-yaml)
;;   _cf_kv_list            — httpx.get Cloudflare API → babashka.http-client
;;   _cf_kv_bulk_put        — httpx.put Cloudflare API → babashka.http-client
;;   _fetch_deps_graph      — httpx.get deps.etzhayyim.com → babashka.http-client
;;   _load_layer_rules      — reads deps.toml → babashka.fs + TOML parse
;;   _extract_wit_stats     — reads world.wit + src/app.ts → babashka.fs
;;   All click CLI commands — wave 4+ (babashka.cli)
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.deps :as deps])
;;   (deps/build-kv-records [{"name" "foo" "nanoid" "abc12345" "did" "did:web:foo.etzhayyim.com"}])
;;   (deps/summarize-deps-graph {"summary" {"totalResolvedLinks" 10 "totalUnresolvedLinks" 2}})

(ns etzhayyim.deps
  (:require [clojure.string :as str]))

;; ── KV record builder ─────────────────────────────────────────────────────────────

(defn build-kv-records
  "Build Cloudflare KV entries from a seq of actor maps.
   Returns a vector of {:key str :value json-str} maps plus an actors:index entry.
   Mirrors Python _build_kv_records(actors)."
  [actors]
  (let [actor-maps (filter map? actors)
        sorted     (sort-by #(get % "name" "") actor-maps)
        entries    (reduce (fn [acc a]
                             (let [name    (get a "name" "")
                                   handles (get a "handles" [])
                                   handle  (or (get a "domain" "")
                                               (first handles)
                                               "")
                                   rec     (cond-> {"name"   name
                                                    "did"    (get a "did" "")
                                                    "handle" handle}
                                             (seq (get a "nanoid" ""))
                                             (assoc "nanoid" (get a "nanoid" ""))
                                             (seq (get a "legacy_did_web" ""))
                                             (assoc "legacyDidWeb" (get a "legacy_did_web" ""))
                                             (seq (get a "description" ""))
                                             (assoc "description" (get a "description" "")))]
                               (if (str/blank? name)
                                 acc
                                 (conj acc {:key   (str "actor:" name)
                                            :value (pr-str rec)}))))
                           []
                           sorted)
        names      (mapv #(get % "name" "") (filter #(not (str/blank? (get % "name" ""))) sorted))]
    (conj entries {:key   "actors:index"
                   :value (pr-str names)})))

;; ── deps graph summarizer ─────────────────────────────────────────────────────────

(defn- py-or
  "Python-style falsy-or: return a if a is non-nil and non-zero, else b.
   Mirrors Python's 'a or b' semantics where 0 is falsy."
  [a b]
  (if (and (some? a) (not (zero? a))) a b))

(defn summarize-deps-graph
  "Compute a link-coverage scorecard map from a raw deps-graph API response.
   graph = map as returned by /api/deps/graph endpoint.
   Mirrors Python _summarize_deps_graph(graph).
   Note: uses Python falsy-or semantics (0 falls through to the fallback)."
  [graph]
  (let [summary    (get graph "summary" {})
        linker     (get graph "linkerStatus" {})
        lk-summary (get linker "summary" {})
        scorecard  (or (get graph "scorecard" {}) {})
        ;; Python: a or b — 0 is falsy so 0 falls through to the addition
        total      (py-or (get lk-summary "totalLinks" 0)
                          (+ (get summary "totalResolvedLinks" 0)
                             (get summary "totalUnresolvedLinks" 0)))
        resolved   (py-or (get lk-summary "resolvedLinks" 0)
                          (get summary "totalResolvedLinks" 0))
        unresolved (py-or (get lk-summary "unresolvedLinks" 0)
                          (get summary "totalUnresolvedLinks" 0))
        coverage   (if (pos? total)
                     (let [scale 10000.0]
                       (/ (Math/rint (* (/ (double resolved) total) scale)) scale))
                     0.0)]
    {"generatedAt"           (get graph "generatedAt" "")
     "totalLinks"            total
     "resolvedLinks"         resolved
     "unresolvedLinks"       unresolved
     "linkCoverageRate"      coverage
     "totalComponents"       (or (get lk-summary "totalComponents")
                                 (get summary "totalLinkerComponents" 0))
     "isolatedCount"         (or (get summary "totalIsolatedComponents")
                                 (get scorecard "isolatedComponentsCount" 0))
     "governanceUnresolved"  (get summary "governanceUnresolvedCount" 0)
     "workerRegisteredApps"  (or (get summary "totalRegisteredApps")
                                 (get scorecard "workerRegisteredAppCount" 0))
     "workerDeployedApps"    (or (get summary "totalWorkerDeployedApps")
                                 (get scorecard "workerDeployedAppCount" 0))
     "workerDeployCoverage"  (let [v (or (get summary "workerDeployCoverageRate")
                                         (get scorecard "workerDeployCoverageRate" 0.0))
                                   scale 10000.0]
                               (/ (Math/rint (* (double v) scale)) scale))
     "governanceCoverage"    (let [v (or (get summary "governanceCoverageRate")
                                         (get scorecard "governanceCoverageRate" 0.0))
                                   scale 10000.0]
                               (/ (Math/rint (* (double v) scale)) scale))
     "wprotoIntegrationScore" (let [v (or (get summary "wProtoIntegrationScore")
                                           (get scorecard "wProtoIntegrationScore" 0.0))
                                    scale 10.0]
                                (/ (Math/rint (* (double v) scale)) scale))}))

;; ── layer filtering ──────────────────────────────────────────────────────────────

(defn filter-layers
  "Filter layer entries by section and tag.
   section = \"packages\" | \"infra\" | \"all\" | \"\"
   tag     = string to match against each entry's :tags vector, or \"\" to skip.
   Mirrors Python _filter_layers(layers, section, tag)."
  [layers section tag]
  (cond->> layers
    (not (contains? #{"all" ""} section))
    (filter #(= (:section %) section))
    (not (str/blank? tag))
    (filter #(some #{tag} (get % :tags [])))))

;; ── layer DAG renderers ──────────────────────────────────────────────────────────

(defn render-deps-tree
  "Format a layer DAG as a text tree string.
   layers  = seq of layer-entry maps (as returned by filter-layers)
   section = string label for the header
   Mirrors Python _render_deps_tree(layers, section)."
  [layers section]
  (let [by-layer (group-by :layer layers)
        lines    (atom [(str "deps layer DAG  [" section "]") ""])]
    (doseq [layer-num (sort (keys by-layer))]
      (swap! lines conj (str "Layer " layer-num ":"))
      (doseq [entry (get by-layer layer-num)]
        (let [dep-str (if (seq (:depends-on entry))
                        (str "  ← " (str/join ", " (:depends-on entry)))
                        "")
              tag-str (if (seq (:tags entry))
                        (str "  [" (str/join "," (:tags entry)) "]")
                        "")
              desc    (subs (get entry :description "") 0 (min 40 (count (get entry :description ""))))]
          (swap! lines conj
                 (str "  " (format "%-30s" (:name entry))
                      "  " desc tag-str dep-str))))
      (swap! lines conj ""))
    (str/join "\n" @lines)))

(defn render-deps-mermaid
  "Format a layer DAG as a Mermaid BT diagram string.
   Mirrors Python _render_deps_mermaid(layers, section)."
  [layers section]
  (let [safe-name (fn [s] (-> s
                              (str/replace "-" "_")
                              (str/replace "." "_")))
        lines     (atom [(str "# deps layer DAG [" section "]")
                         ""
                         "```mermaid"
                         "graph BT"])]
    (doseq [entry layers]
      (let [safe  (safe-name (:name entry))
            label (:name entry)]
        (swap! lines conj (str "  " safe "[\"" label "\"]"))))
    (swap! lines conj "")
    (doseq [entry layers]
      (let [safe (safe-name (:name entry))]
        (doseq [dep (:depends-on entry)]
          (swap! lines conj (str "  " (safe-name dep) " --> " safe)))))
    (swap! lines into ["```" ""])
    (str/join "\n" @lines)))

;; ── deps.toml summary helpers ────────────────────────────────────────────────────

(defn deps-summary
  "Extract summary counts from a loaded deps.toml data map.
   data = map (e.g. from clj-toml parse of deps.toml).
   Returns a map with :has-deps-toml :migrations :conventions :projects :mitama-actors.
   Mirrors the summary built in the Python deps CLI default command."
  [data]
  {:has-deps-toml   (boolean (seq data))
   :migrations      (count (get data "migrations" []))
   :conventions     (count (get data "conventions" []))
   :projects        (count (get data "projects" []))
   :mitama-actors   (count (get data "mitama_actors" []))})

(defn migrations-by-status
  "Filter migrations from a deps.toml data map by status string.
   status = \"pending\" | \"done\" | \"blocked\" | \"\" (all).
   Mirrors Python: migrations = [m for m in data.get('migrations',[]) if m.get('status')==filter_status]."
  [data status]
  (let [migs (get data "migrations" [])]
    (if (str/blank? status)
      migs
      (filter #(= (get % "status") status) migs))))

;; ── governance WIT scoring ────────────────────────────────────────────────────────

(defn governance-score
  "Compute a governance compliance score (0.0-100.0) from a findings map.
   findings = {:wit-ok bool :app-ok bool :gov-ok bool :extra-findings [str]}
   Mirrors Python: score = (int(wit_ok) + int(app_ok) + int(gov_ok)) / n_checks * 100."
  [{:keys [wit-ok app-ok gov-ok]}]
  (let [n 3]
    (double (* (/ (+ (if wit-ok 1 0) (if app-ok 1 0) (if gov-ok 1 0)) n) 100))))

(defn governance-verdict
  "Derive a governance verdict string from a governance-score and findings list.
   Mirrors Python: 'not-suitable' if score < 60, 'partial' if findings, else 'suitable'."
  [score extra-findings]
  (cond
    (< score 60.0)     "not-suitable"
    (seq extra-findings) "partial"
    :else              "suitable"))

;; ── deps MV name extraction ───────────────────────────────────────────────────────

(defn deps-mv-name
  "Extract the VIEW name from a CREATE MATERIALIZED VIEW IF NOT EXISTS <name> AS ... statement.
   Mirrors Python _deps_mv_name(stmt)."
  [stmt]
  (let [words (str/split stmt #"\s+")]
    (or (some (fn [[i w]]
                (when (= (str/upper-case w) "EXISTS")
                  (some-> (nth words (inc i) nil)
                          (str/replace #";$" "")
                          str/trim)))
              (map-indexed vector words))
        (some (fn [[i w]]
                (when (and (= (str/upper-case w) "VIEW")
                           (not= (str/upper-case (nth words (inc i) "")) "IF"))
                  (some-> (nth words (inc i) nil)
                          (str/replace #";$" "")
                          str/trim)))
              (map-indexed vector words))
        "?")))
