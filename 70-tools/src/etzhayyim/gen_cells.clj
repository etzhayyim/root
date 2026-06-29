(ns etzhayyim.gen-cells
  "bb gen:cells — fold each actor's OWN `:actor/heartbeat-cells` declaration (in
  20-actors/<a>/manifest.edn) into the fleet cell registry
  50-infra/cluster/murakumo/cell-runner/cells.edn that the kotodama cell-runner reads.
  (Distinct from `:actor/cells`, which is the actor's internal Pregel/LangGraph cell
  catalog — a different, pre-existing key.)

  This is the ①②-unification: an actor declares its heartbeat cell ONCE in its own
  manifest (the SSoT), and `bb gen:cells --apply` registers it fleet-wide — so
  `deploy-fleet` picks it up with NO per-actor `murakumo deploy` step. `bb gen:cells`
  (or `--check`) FAILS on drift between a manifest declaration and cells.edn, the same
  generated-artifact discipline as `gen-west-manifest` (the west.yml precedent).

  clj/bb (repo rule — no new shell). Pure reconcile + a minimal, format-preserving
  textual append (existing cells stay byte-identical; only NEW declared cells are added).
  A declared cell that already exists but DIFFERS is reported, never silently rewritten.

  Scope note: only actors that adopt `:actor/cells` are reconciled here; the legacy
  hand-authored cells (infra primitives + actors not yet declaring) are preserved
  verbatim and migrate opportunistically (grandfathered, like the .sh baseline)."
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.java.io :as io]))

(def ^:dynamic *actors-dir* "20-actors")
(def ^:dynamic *cells-path* "50-infra/cluster/murakumo/cell-runner/cells.edn")

;; ── declared-cell → cells.edn cell shape ─────────────────────────────────────
(defn decl->cell
  "Map a manifest `:actor/cells` declaration to the cells.edn cell map (ordered keys
  so the emitted form is stable). cron-only triggers for now."
  [d]
  (array-map
   :name        (:cell/name d)
   :module      (:cell/module d)
   :entry       (:cell/entry d)
   :node        (:cell/node d)
   :trigger     (array-map :kind "cron" :expr (:cell/cron d))
   :healthz_port (:cell/healthz d)
   :adr         (vec (:cell/adr d))))

(defn declared-cells
  "Scan every 20-actors/<a>/manifest.edn for `:actor/cells`; return the flat vector of
  cells.edn-shaped cell maps (with :__actor source tag for messages)."
  ([] (declared-cells *actors-dir*))
  ([actors-dir]
   (->> (.listFiles (io/file actors-dir))
        (filter #(.isDirectory %))
        (mapcat
         (fn [dir]
           (let [mf (io/file dir "manifest.edn")]
             (when (.exists mf)
               (try
                 (->> (:actor/heartbeat-cells (edn/read-string (slurp mf)))
                      (map (fn [d] (assoc (decl->cell d) :__actor (.getName dir)))))
                 (catch Exception _ nil))))))
        (remove nil?)
        vec)))

(defn load-registry [] (edn/read-string (slurp *cells-path*)))

;; ── comma-free EDN emit (match cells.edn's existing space-separated style; commas
;; are EDN whitespace but the file is comma-free, so we keep it that way) ─────────
(defn- emit-map [pairs]
  (str "{" (str/join " " (map (fn [[k v]] (str (pr-str k) " " v)) pairs)) "}"))

(defn emit-cell [c]
  (emit-map
   [[:name (pr-str (:name c))]
    [:module (pr-str (:module c))]
    [:entry (pr-str (:entry c))]
    [:node (pr-str (:node c))]
    [:trigger (emit-map [[:kind (pr-str (get-in c [:trigger :kind]))]
                         [:expr (pr-str (get-in c [:trigger :expr]))]])]
    [:healthz_port (:healthz_port c)]
    [:adr (pr-str (:adr c))]]))

(defn next-healthz
  "Lowest free healthz_port in [13000,14000) not used by any registry cell."
  [registry]
  (let [used (set (keep :healthz_port (:cell registry)))]
    (first (remove used (range 13000 14000)))))

;; ── check: drift between declarations and the registry ───────────────────────
(defn check
  "Compare declared cells to the registry. Returns {:errors :warnings :present :missing}.
  A declared cell must appear in cells.edn with byte-equal value (sans :__actor)."
  []
  (let [registry (load-registry)
        by-name (into {} (map (juxt :name identity) (:cell registry)))
        decls (declared-cells)
        errs (atom []) warns (atom []) present (atom []) missing (atom [])]
    (doseq [d decls]
      (let [want (dissoc d :__actor)
            have (get by-name (:name d))]
        (cond
          (nil? have) (do (swap! missing conj (:name d))
                          (swap! errs conj (str (:__actor d) ": declared cell " (:name d)
                                                " is MISSING from cells.edn (run `bb gen:cells --apply`)")))
          (not= want have) (swap! errs conj (str (:__actor d) ": declared cell " (:name d)
                                                 " DIFFERS from cells.edn — reconcile manually"))
          :else (swap! present conj (:name d)))))
    ;; healthz collisions: ERROR only when a DECLARED cell's port collides (the case
    ;; gen:cells is responsible for); pre-existing legacy-vs-legacy duplicates are a WARN
    ;; (not introduced here — flagged for opportunistic cleanup, not a gate failure).
    (let [decl-ports (set (keep :healthz_port decls))]
      (doseq [[port n] (frequencies (keep :healthz_port (:cell registry))) :when (> n 1)]
        (if (contains? decl-ports port)
          (swap! errs conj (str "healthz_port " port " collides — a declared cell shares it (" n "×)"))
          (swap! warns conj (str "legacy healthz_port " port " used " n "× in cells.edn (pre-existing)")))))
    {:errors @errs :warnings @warns :present @present :missing @missing
     :decls (count decls) :registry-cells (count (:cell registry))}))

;; ── apply: append NEW declared cells (existing stay byte-identical) ───────────
(defn apply!
  "Append declared cells not yet present (by :name) into cells.edn via a minimal
  textual insert before the closing `]}` (existing cells unchanged). Errors if a
  declared cell exists but differs. Returns {:appended [names] :errors [...]}."
  []
  (let [registry (load-registry)
        by-name (into {} (map (juxt :name identity) (:cell registry)))
        decls (declared-cells)
        errs (atom []) to-add (atom [])]
    (doseq [d decls]
      (let [want (dissoc d :__actor)
            have (get by-name (:name d))]
        (cond
          (nil? have) (swap! to-add conj want)
          (not= want have) (swap! errs conj (str (:__actor d) ": declared cell " (:name d)
                                                  " differs from cells.edn — reconcile manually")))))
    (cond
      (seq @errs) {:appended [] :errors @errs}
      (empty? @to-add) {:appended [] :errors []}
      :else
      (let [content (slurp *cells-path*)
            idx (str/last-index-of content "]}")
            ins (str/join " " (map emit-cell @to-add))
            out (str (subs content 0 idx) " " ins (subs content idx))]
        ;; re-parse to guarantee the result is valid + the cells landed
        (let [reg2 (edn/read-string out)
              names2 (set (map :name (:cell reg2)))]
          (when-not (every? names2 (map :name @to-add))
            (throw (ex-info "apply produced invalid cells.edn (cells not found after insert)" {})))
          (spit *cells-path* out)
          {:appended (mapv :name @to-add) :errors []})))))

;; ── CLI ──────────────────────────────────────────────────────────────────────
(defn -main [& args]
  (let [apply? (some #{"--apply"} args)]
    (if apply?
      (let [{:keys [appended errors]} (apply!)]
        (doseq [e errors] (println "  ERROR " e))
        (if (seq errors)
          (do (println "❌ gen:cells --apply: reconcile errors") (System/exit 1))
          (do (println (str "✅ gen:cells --apply: appended " (count appended)
                            (when (seq appended) (str " (" (str/join ", " appended) ")"))
                            (when (empty? appended) " — already up to date")))
              ;; verify post-apply
              (let [{:keys [errors]} (check)]
                (doseq [e errors] (println "  ERROR " e))
                (System/exit (if (seq errors) 1 0))))))
      (let [{:keys [errors warnings present missing decls registry-cells]} (check)]
        (println (str "gen:cells --check — " decls " declared · " registry-cells " registry cells · "
                      (count present) " present · " (count missing) " missing"))
        (doseq [w warnings] (println "  warn  " w))
        (doseq [e errors] (println "  ERROR " e))
        (println (if (empty? errors) "✅ cells.edn in sync with actor declarations"
                     "❌ drift — run `bb gen:cells --apply`"))
        (System/exit (if (empty? errors) 0 1))))))
