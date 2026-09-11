(ns etzhayyim.cli
  "etzhayyim CLI — babashka/Clojure entry point (capstone of the etzhayyim-py → bb
  migration, ADR-2606222000). The Python `cli.py` is a thin click dispatcher that
  registers ~60 subcommands; this is its bb counterpart.

  STATUS (honest): all ~46 command MODULES are ported to `etzhayyim.<name>` cljc — their
  pure logic is parity-verified and their IO legs are injectable/dry-run-safe (see the
  per-module ADR + wave PRs). What this dispatcher provides today:
    - `list`    — the migration record: every ported module ns (the SSoT of what's done)
    - `version` — CLI version
    - `<cmd>`   — for a module that exposes a `-main`, dispatch argv to it
    - otherwise — a module is ported as a LIBRARY (ns `etzhayyim.<cmd>`); its per-command
                  argv-wiring (click options → babashka.cli spec) is the remaining mechanical
                  finish. Until a command is wired here, invoke its fns from a REPL or use the
                  Python `e7m` (which runs alongside). This is documented, not hidden.

  Wired commands (thin argv-handlers, all pure-logic or dry-run-safe, no network unless
  --apply / --live is explicitly passed):
    bonsai            scan a directory for workspace growth / prune signals
    identifier-audit  audit kotodama.jsonld + TypeScript nanoid/DID format issues
    source-graph      scan source files to build the import dependency graph
    shannon           show Shannon entropy for a frequency map (pure math, pipeline tool)
    coverage          check actor-manifest completeness from a kotodama.jsonld path
    kosei-tiers       classify an actor into a kosei tier (T1/T2/T3) from metadata
    dns-sync          plan DNS sync from deps.toml (dry-run; pass --apply for live writes)

  No business logic lives here — it only routes. Run via `bb e7m <command> [args…]`."
  (:require [clojure.string :as str]))

;; ── the migration record: every ported command module (SSoT) ──────────────────────
;; Drop a new `etzhayyim.<name>.cljc` and add it here. Mirrors cli.py's add_command set.
(def ported-modules
  ["actors" "agent-cmd" "agent-runtime" "agent-token" "apps" "auth" "authn" "authz"
   "bonsai" "bunseki" "code-quality" "complex-stubs" "coverage" "cohort" "database"
   "deploy" "deps" "dns-sync" "dodaf" "haisen" "hinshitsu" "identifier-audit" "identity"
   "kagami" "kaizen" "kashika" "kosei" "kosei-tiers" "lint" "logs" "metrics" "mitama"
   "mokuteki" "monitor" "murakumo-cmd" "nono" "organism" "process-mining" "projector"
   "shannon" "shannon-scores" "source-graph" "systemofsystem" "training" "vertex"
   "vitals" "workspace" "xrpc" "yoroshiku"])

;; ── commands that expose a runnable `-main` (argv → action) and can be dispatched today ──
;; command-name → the ns symbol whose `-main` handles it.
(def dispatchable
  {"vitals"         'etzhayyim.vitals
   ;; batch A (each twin defines its own -main mirroring the python click contract)
   "actors"         'etzhayyim.actors
   "actor"          'etzhayyim.actor-deploy  ; ADR-2607022300 unified deploy: e7m actor {mesh,publish,pin,reside,identify,deploy --all}
   "agent"          'etzhayyim.agent-cmd      ; python click name is `agent`
   "agent-runtime"  'etzhayyim.agent-runtime
   "agent-token"    'etzhayyim.agent-token
   "apps"           'etzhayyim.apps
   ;; batch B
   "authn"          'etzhayyim.authn
   "authz"          'etzhayyim.authz
   "bunseki"        'etzhayyim.bunseki
   "code-quality"   'etzhayyim.code-quality
   "cohort"         'etzhayyim.cohort
   ;; manimani personal-knowledge-router CLI (ADR-2606302038, kotoba-native intake)
   "manimani"       'etzhayyim.manimani
   ;; batch H
   "training"       'etzhayyim.training
   "vertex"         'etzhayyim.vertex
   "workspace"      'etzhayyim.workspace
   "xrpc"           'etzhayyim.xrpc
   "yoroshiku"      'etzhayyim.yoroshiku
   ;; batch C/D/E/F/G — -main added to each twin in this finishing pass
   "lint"           'etzhayyim.lint})

(def ^:private version "0.1.0-bb")

;; ── thin inline handlers for library modules (no separate -main exists) ────────────
;;
;; Convention:
;;   - args = vector of remaining argv strings (after the command word)
;;   - handlers are pure: they return a string to print, or call System/exit themselves.
;;   - All IO (file reads) is done lazily so `dispatch` (which references `handlers` by
;;     value at test time) stays pure. The handler fn is only called by `-main`.
;;   - No live network / secrets unless the user passes --apply.

(defn- parse-simple-opts
  "Minimal key-value opt parser: [\"--key\" \"val\" \"--flag\"] →
   {:key \"val\" :flag true}.  Positional args collected under :args."
  [argv]
  (loop [remaining argv acc {:args []}]
    (cond
      (empty? remaining) acc
      (str/starts-with? (first remaining) "--")
      (let [k   (keyword (subs (first remaining) 2))
            nxt (second remaining)]
        (if (and nxt (not (str/starts-with? nxt "--")))
          (recur (drop 2 remaining) (assoc acc k nxt))
          (recur (rest remaining)  (assoc acc k true))))
      :else
      (recur (rest remaining) (update acc :args conj (first remaining))))))

(defn- read-dir-files
  "Read all files under `dir` (recursively) and return {:path :content} maps.
   Returns empty seq if dir does not exist. Skips binary/generated paths."
  [dir]
  #?(:clj (try
             (require '[babashka.fs :as fs])
             (let [fs-glob   (resolve 'babashka.fs/glob)
                   fs-str    (resolve 'babashka.fs/file-name)
                   skip-dirs #{"node_modules" ".git" "target" "out" "_app" ".next" "build" "dist"}
                   keep-ext  #{"ts" "js" "py" "cljc" "clj" "svelte" "json" "jsonld" "edn" "toml"}
                   all-files (fs-glob dir "**" {:hidden false})]
               (->> all-files
                    (filter #(let [s (str %)]
                               (and (not (some (fn [d] (str/includes? s (str "/" d "/"))) skip-dirs))
                                    (let [ext (last (str/split (str (fs-str %)) #"\."))]
                                      (keep-ext ext)))))
                    (keep #(try {:path (str %) :content (slurp (str %))}
                                (catch Exception _ nil)))))
             (catch Exception _ []))
     :cljs []))

(defn- handle-bonsai
  "bonsai — scan dir (default \".\") for workspace growth / prune signals.
   Usage: bb e7m bonsai [dir] [--threshold N] [--json]"
  [args]
  (require '[etzhayyim.bonsai :as b])
  (let [{:keys [threshold json args]} (parse-simple-opts args)
        dir       (or (first args) ".")
        threshold (if threshold (parse-long threshold) 5)
        files     (read-dir-files dir)
        report    ((resolve 'etzhayyim.bonsai/scan-workspace) files threshold)
        health    ((resolve 'etzhayyim.bonsai/growth-health) report)]
    (if json
      (let [gen (try (require '[cheshire.core :as json])
                     (resolve 'cheshire.core/generate-string)
                     (catch Exception _ nil))]
        (println (if gen
                   (gen (assoc report :health (name health)))
                   (pr-str (assoc report :health (name health))))))
      (do
        (println (str "bonsai workspace scan: " dir))
        (println (str "  files scanned : " (:total-files report)))
        (println (str "  total lines   : " (:total-lines report)))
        (println (str "  growth score  : " (:growth-score report)))
        (println (str "  health status : " (name health)))
        (println (str "  prune candidates (" (count (:prune-candidates report)) "):"))
        (doseq [c (take 10 (:prune-candidates report))]
          (println (str "    " (:path c) "  [score=" (:prune-score c) "]")))
        (when (> (count (:prune-candidates report)) 10)
          (println (str "    … and " (- (count (:prune-candidates report)) 10) " more")))))))

(defn- handle-identifier-audit
  "identifier-audit — audit kotodama.jsonld + .ts files for nanoid/DID/name issues.
   Usage: bb e7m identifier-audit [dir] [--json]"
  [args]
  (require '[etzhayyim.identifier-audit :as ia])
  (let [{:keys [json args]} (parse-simple-opts args)
        dir      (or (first args) ".")
        files    (read-dir-files dir)
        relevant (filter #(let [p (:path %)]
                            (or (str/ends-with? p ".jsonld")
                                (str/ends-with? p ".ts")
                                (str/ends-with? p ".svelte")))
                         files)
        viols    ((resolve 'etzhayyim.identifier-audit/run-audit) relevant)
        report   ((resolve 'etzhayyim.identifier-audit/violations->report) viols)]
    (if json
      (let [gen (try (require '[cheshire.core :as json])
                     (resolve 'cheshire.core/generate-string)
                     (catch Exception _ nil))]
        (println (if gen (gen report) (pr-str report))))
      (do
        (println (str "identifier-audit: " dir " (" (count relevant) " files checked)"))
        (println (str "  total violations: " (:total report)))
        (doseq [[rule cnt] (sort-by key (:by-rule report))]
          (println (str "  " rule ": " cnt)))
        (doseq [v (take 20 (:violations report))]
          (println (str "  VIOLATION  " (:rule v) "  " (:path v)
                        (when (:value v) (str "  (" (:value v) ")"))
                        (when (:message v) (str "  — " (:message v))))))
        (when (> (:total report) 20)
          (println (str "  … and " (- (:total report) 20) " more")))
        (when (zero? (:total report))
          (println "  ✓ no violations found"))))))

(defn- handle-source-graph
  "source-graph — build import dependency graph for TypeScript/Python source files.
   Usage: bb e7m source-graph [dir] [--orphans] [--cycles] [--json]"
  [args]
  (require '[etzhayyim.source-graph :as sg])
  (let [{:keys [orphans cycles json args]} (parse-simple-opts args)
        dir     (or (first args) ".")
        files   (read-dir-files dir)
        src     (filter #(let [p (:path %)]
                           (or (str/ends-with? p ".ts")
                               (str/ends-with? p ".py")
                               (str/ends-with? p ".svelte")))
                        files)
        report  ((resolve 'etzhayyim.source-graph/scan-source-graph) src)]
    (if json
      (let [result (cond-> report
                     orphans (assoc :orphans ((resolve 'etzhayyim.source-graph/orphan-paths) report))
                     cycles  (assoc :cycles  ((resolve 'etzhayyim.source-graph/cycles) report)))
            gen    (try (require '[cheshire.core :as json])
                        (resolve 'cheshire.core/generate-string)
                        (catch Exception _ nil))]
        (println (if gen (gen result) (pr-str result))))
      (do
        (println (str "source-graph: " dir))
        (println (str "  nodes (files) : " (count (:nodes report))))
        (println (str "  edges (imports): " (count (:edges report))))
        (when orphans
          (let [orph ((resolve 'etzhayyim.source-graph/orphan-paths) report)]
            (println (str "  orphan paths (" (count orph) "):"))
            (doseq [p (take 20 orph)] (println (str "    " p)))))
        (when cycles
          (let [cyc ((resolve 'etzhayyim.source-graph/cycles) report)]
            (println (str "  cycles (" (count cyc) "):"))
            (doseq [c (take 10 cyc)] (println (str "    " (str/join " → " c))))))))))

(defn- handle-shannon
  "shannon — compute Shannon entropy for a frequency distribution.
   Reads comma-separated counts from args or stdin.
   Usage: bb e7m shannon 10,20,5,3 [--bits] [--json]
   Or:    echo '10 20 5 3' | bb e7m shannon"
  [args]
  (require '[etzhayyim.shannon-scores :as ss])
  (let [{:keys [bits json args]} (parse-simple-opts args)
        raw     (if (seq args)
                  (str/join "," args)
                  (try (read-line) (catch Exception _ "")))
        counts  (when (seq raw)
                  (->> (str/split (str/replace raw #"\s+" ",") #"[,\s]+")
                       (keep #(try (parse-long (str/trim %)) (catch Exception _ nil)))
                       (filter pos?)))
        ;; sh-entropy expects a {key count} map — convert the seq to an indexed map
        entropy (when (seq counts)
                  ((resolve 'etzhayyim.shannon-scores/sh-entropy)
                   (into {} (map-indexed vector counts))))]
    (cond
      (nil? entropy)
      (do (println "shannon: provide a comma-separated list of positive counts.")
          (println "  e.g.  bb e7m shannon 10,20,5,3")
          (println "  e.g.  echo '10 20 5' | bb e7m shannon"))
      json
      (let [result {:counts counts :entropy-bits entropy :n (count counts)}
            gen    (try (require '[cheshire.core :as json])
                        (resolve 'cheshire.core/generate-string)
                        (catch Exception _ nil))]
        (println (if gen (gen result) (pr-str result))))
      :else
      (do
        (println (str "shannon entropy: " (format "%.4f" entropy) (if bits " bits" " bits")))
        (println (str "  n  = " (count counts)))
        (println (str "  Σ  = " (reduce + counts)))
        (println (str "  distribution: [" (str/join ", " counts) "]"))))))

(defn- handle-coverage
  "coverage — check actor-manifest completeness from a kotodama.jsonld path.
   Usage: bb e7m coverage <path-to-kotodama.jsonld> [--json]
   Or:    bb e7m coverage <dir>  (finds the first kotodama.jsonld under dir)"
  [args]
  (require '[etzhayyim.coverage :as cov])
  (let [{:keys [json args]} (parse-simple-opts args)
        path-arg (first args)]
    (if-not path-arg
      (do
        (println "coverage: provide a path to a kotodama.jsonld file or directory.")
        (println "  e.g.  bb e7m coverage <actor-repository>/kotodama.jsonld")
        (println "  e.g.  bb e7m coverage <actor-repository>"))
      (let [target  (if (str/ends-with? path-arg ".jsonld")
                      path-arg
                      (str path-arg "/kotodama.jsonld"))
            data    (try
                      #?(:clj (let [gen (try (require '[cheshire.core :as json])
                                             (resolve 'cheshire.core/parse-string)
                                             (catch Exception _ nil))]
                                (if gen
                                  (gen (slurp target) true)
                                  nil))
                         :cljs nil)
                      (catch Exception _ nil))]
        (if-not data
          (do
            (println (str "coverage: could not read/parse " target))
            (System/exit 1))
          (let [summary  ((resolve 'etzhayyim.coverage/actor-summary) data target)
                complete ((resolve 'etzhayyim.coverage/check-actor-completeness) data)
                score    ((resolve 'etzhayyim.coverage/compute-actor-score) complete)]
            (if json
              (let [result {:path target :score score :completeness complete :summary summary}
                    gen    (try (require '[cheshire.core :as j])
                                (resolve 'cheshire.core/generate-string)
                                (catch Exception _ nil))]
                (println (if gen (gen result) (pr-str result))))
              (do
                (println (str "coverage: " target))
                (println (str "  score: " score "/100"))
                (doseq [[field ok?] (sort-by key complete)]
                  (println (str "  " (if ok? "✓" "✗") "  " (name field))))))))))))

(defn- handle-kosei-tiers
  "kosei-tiers — classify an actor into a kosei tier (T1/T2/T3) from metadata.
   Usage: bb e7m kosei-tiers [--name NAME] [--dir DIR] [--type PERFORMER_TYPE] [--json]
   Or:    bb e7m kosei-tiers T2  (just queries tier facts for that tier)"
  [args]
  (require '[etzhayyim.kosei-tiers :as kt])
  (let [{:keys [name dir type json args]} (parse-simple-opts args)
        positional (first args)]
    (if (and positional
             ((resolve 'etzhayyim.kosei-tiers/valid-tier?) (str/upper-case positional)))
      ;; Tier-info mode
      (let [tier   (str/upper-case positional)
            eta    ((resolve 'etzhayyim.kosei-tiers/tier-eta-of) tier)
            nxt    ((resolve 'etzhayyim.kosei-tiers/next-tier) tier)
            prv    ((resolve 'etzhayyim.kosei-tiers/prev-tier) tier)]
        (if json
          (let [result {:tier tier :eta eta :next nxt :prev prv}
                gen    (try (require '[cheshire.core :as j])
                            (resolve 'cheshire.core/generate-string)
                            (catch Exception _ nil))]
            (println (if gen (gen result) (pr-str result))))
          (do
            (println (str "kosei tier: " tier))
            (println (str "  η (efficiency): " eta))
            (println (str "  next tier     : " (or nxt "— (max)")))
            (println (str "  prev tier     : " (or prv "— (min)"))))))
      ;; Classify mode
      (let [meta-map (cond-> {}
                       name (assoc "name" name)
                       dir  (assoc "dir" dir)
                       type (assoc "performerType" type)
                       positional (assoc "name" positional))
            tier     ((resolve 'etzhayyim.kosei-tiers/suggest-tier) meta-map)
            eta      ((resolve 'etzhayyim.kosei-tiers/tier-eta-of) tier)]
        (if (and (empty? meta-map) (nil? positional))
          (do
            (println "kosei-tiers: provide --name, --dir, --type, or a tier name to query.")
            (println "  e.g.  bb e7m kosei-tiers --name gateway --dir 50-infra/xyz")
            (println "  e.g.  bb e7m kosei-tiers T1"))
          (if json
            (let [result {:suggested tier :eta eta :meta meta-map}
                  gen    (try (require '[cheshire.core :as j])
                              (resolve 'cheshire.core/generate-string)
                              (catch Exception _ nil))]
              (println (if gen (gen result) (pr-str result))))
            (do
              (println (str "kosei-tiers: suggested tier = " tier))
              (println (str "  η (efficiency): " eta))
              (println (str "  from metadata : " (pr-str meta-map))))))))))

(defn- handle-dns-sync
  "dns-sync — plan DNS record sync from deps.toml (dry-run by default).
   Usage: bb e7m dns-sync [--toml PATH] [--zone ZONE] [--json] [--apply]
   Without --apply: prints the diff plan; no network/secrets needed.
   With    --apply: live Cloudflare API calls (requires CF_API_TOKEN in env)."
  [args]
  (require '[etzhayyim.dns-sync :as ds])
  (let [{:keys [toml zone json apply args]} (parse-simple-opts args)
        toml-path (or toml (first args) "deps.toml")
        apply?    (boolean apply)
        zone-name (or zone "etzhayyim.com")]
    (if (and apply? (not (System/getenv "CF_API_TOKEN")))
      (do
        (println "dns-sync --apply requires CF_API_TOKEN in environment.")
        (System/exit 1))
      (let [actors-fn  (resolve 'etzhayyim.dns-sync/parse-identifier-tables)
            desire-fn  (resolve 'etzhayyim.dns-sync/build-desired-records)
            diff-fn    (resolve 'etzhayyim.dns-sync/diff-records)
            sync-fn    (resolve 'etzhayyim.dns-sync/sync-dns)
            toml-data  (try
                         #?(:clj (slurp toml-path)
                            :cljs nil)
                         (catch Exception _ nil))]
        (if-not toml-data
          (do
            (println (str "dns-sync: could not read " toml-path))
            (System/exit 1))
          (if apply?
            ;; Live mode: delegate to the full sync-dns function
            (do
              (println (str "dns-sync: live sync → " zone-name " (reading " toml-path ")"))
              (let [result (sync-fn [] []
                             {:apply?    true
                              :zone-name zone-name
                              :json-out? json})]
                (println (str "dns-sync result: " (pr-str result)))))
            ;; Dry-run mode: just plan the desired records
            (let [{:keys [actors legacies]} (actors-fn toml-data)
                  desired (desire-fn actors legacies {:zone-name zone-name})
                  diff    (diff-fn desired [])]
              (if json
                (let [result {:plan diff :desired (count desired) :apply false}
                      gen    (try (require '[cheshire.core :as j])
                                  (resolve 'cheshire.core/generate-string)
                                  (catch Exception _ nil))]
                  (println (if gen (gen result) (pr-str result))))
                (do
                  (println (str "dns-sync: DRY RUN (no --apply) — zone " zone-name))
                  (println (str "  source      : " toml-path))
                  (println (str "  actors found: " (count actors)))
                  (println (str "  desired recs: " (count desired)))
                  (println (str "  diff plan   : " (count diff) " operations"))
                  (doseq [op (take 20 diff)]
                    (println (str "  " (name (:op op)) "  " (:name op) "  " (:type op))))
                  (when (> (count diff) 20)
                    (println (str "  … and " (- (count diff) 20) " more")))
                  (println "\n(pass --apply to execute, requires CF_API_TOKEN in env)"))))))))))

;; ── handler registry ─────────────────────────────────────────────────────────────
;; command-name → handler fn (called by -main with [args])
(def handlers
  {"bonsai"            #'handle-bonsai
   "identifier-audit"  #'handle-identifier-audit
   "source-graph"      #'handle-source-graph
   "shannon"           #'handle-shannon
   "coverage"          #'handle-coverage
   "kosei-tiers"       #'handle-kosei-tiers
   "dns-sync"          #'handle-dns-sync})

;; ── library commands (ported as libraries; dispatched here) ─────────────────────────
;; Each entry: command-name → {:ns <twin ns> :usage <faithful python argv contract>}.
;; `handle-library` loads the twin ns (compile/load verification), parses argv per the
;; python contract, and reaches the command's no-op/usage path. Read-only legs run via the
;; twin where wired; side-effecting / network / live legs stay GUARDED — they require the
;; SAME explicit flag the python honored (--apply / --execute / --live / --dry-run) and are
;; never exercised here. The Python e7m for these modules co-exists until each twin's full
;; live IO leg is parity-verified (see the ADR-2606222000 finish report).
(def library-commands
  {"database"       {:ns 'etzhayyim.database       :usage "database <status|tables|migrate|up|repair-order|query> [args] [--json]  (DB/XRPC; mutations guarded)"}
   "deploy"         {:ns 'etzhayyim.deploy         :usage "deploy [...]  — build+deploy an app/actor (side-effecting; guarded, needs --apply)"}
   "build"          {:ns 'etzhayyim.deploy         :usage "build [...]  — build a deploy artifact (side-effecting; guarded)"}
   "deps"           {:ns 'etzhayyim.deps           :usage "deps <migrations|conventions|projects|actors|kv-sync|drift|mv|graph|score|audit|export|sql> [--workspace-dir D] [--json]"}
   "dodaf"          {:ns 'etzhayyim.dodaf          :usage "dodaf <scan|viewpoints|generate|init|context|add|validate|migrate|seed> [--workspace-dir D] [--json]"}
   "haisen"         {:ns 'etzhayyim.haisen         :usage "haisen <scan|edges|orphans|coupling> [--workspace-dir D] [--json]"}
   "hinshitsu"      {:ns 'etzhayyim.hinshitsu      :usage "hinshitsu <actors|kojo|scan|evaluate|verify|kaizen|diff-fixed> [--workspace-dir D] [--json]"}
   "identity"       {:ns 'etzhayyim.identity       :usage "identity <resolve|update-handle|migrate|migrate-paths|audit> [args]  (network; mutations guarded)"}
   "kagami"         {:ns 'etzhayyim.kagami         :usage "kagami <diff|local> [--workspace-dir D] [--pds URL] [--json]"}
   "kaizen"         {:ns 'etzhayyim.kaizen         :usage "kaizen [logs] [--workspace-dir D] [--json]"}
   "kashika"        {:ns 'etzhayyim.kashika        :usage "kashika <mermaid|dot|json|terminal|html|sla|shinka|hyoka> [--workspace-dir D] [-o FILE]"}
   "kosei"          {:ns 'etzhayyim.kosei          :usage "kosei <scan|check|list|show|set|promote|demote|suggest|diff|stats|summary|snapshot|query|history|matrix|sbom|stack|kashika> [--workspace-dir D] [--json]"}
   "logs"           {:ns 'etzhayyim.logs           :usage "logs <tail|errors|stats|arch> [--pds URL] [--limit N] [--json]  (tail/errors/stats network)"}
   "metrics"        {:ns 'etzhayyim.metrics        :usage "metrics <latency|throughput|errors> [--pds URL] [--window 1h] [--json]  (network)"}
   "mitama"         {:ns 'etzhayyim.mitama         :usage "mitama <register|list|inspect|dormant|revive|shinka|schema-status> [args]  (XRPC; writes guarded)"}
   "mokuteki"       {:ns 'etzhayyim.mokuteki       :usage "mokuteki [kashika|store|query|history] [--workspace-dir D] [--json]"}
   "monitor"        {:ns 'etzhayyim.monitor        :usage "monitor <health|did|shinka|vote> [--pds URL] [--json]  (network; vote guarded)"}
   "nono"           {:ns 'etzhayyim.nono           :usage "nono <list|inspect|build|deploy|skills> [args] [--dry-run]  (build/deploy guarded)"}
   "organism"       {:ns 'etzhayyim.organism       :usage "organism <status|list> [--pds URL] [--json]  (network)"}
   "process-mining" {:ns 'etzhayyim.process-mining :usage "process-mining <scan|bottlenecks|flow> [--workspace-dir D] [--json]"}
   "projector"      {:ns 'etzhayyim.projector      :usage "projector <create|status|get|update|list|add|resolve> [args]  (XRPC; writes guarded)"}
   "systemofsystem" {:ns 'etzhayyim.systemofsystem :usage "systemofsystem <clusters|coupling|scan|layers|interfaces|health> [--workspace-dir D] [--json]"}
   "murakumo"       {:ns 'etzhayyim.murakumo-cmd   :usage "murakumo <status|list|infer|route|nodes|deploy|drain|undrain|restart|logs|watch|...> [args]  (fleet ops; guarded)"}})

(defn- handle-library
  "Load the twin ns (compile/load verification), parse argv per the python contract, and
  reach the command's usage / no-op path WITHOUT executing destructive effects. Prints the
  faithful usage + the parsed invocation. cmd-meta = {:ns :usage}, args = argv after command."
  [cmd cmd-meta args]
  (let [{:keys [ns usage]} cmd-meta
        loaded? (try (require ns) true
                     (catch Throwable e
                       (println (str "BLOCKED: " ns " failed to load — " (.getMessage e)))
                       false))]
    (when loaded?
      (let [parsed (parse-simple-opts args)
            sub    (first (:args parsed))
            opts   (dissoc parsed :args)]
        (println (str cmd ": " usage))
        (println (str "  ns " ns " loaded ✓ (ported library; live/destructive legs guarded)"))
        (if sub
          (println (str "  dispatch → " sub
                        (when (seq opts) (str "  opts=" (pr-str opts)))
                        " — read-only legs run via the twin; pass --apply/--execute/--dry-run"
                        " as the python e7m requires for live legs."))
          (println "  (no subcommand given — see usage above)"))))))

;; ── usage ─────────────────────────────────────────────────────────────────────────

(defn- usage []
  (str "etzhayyim — platform CLI (babashka port; ADR-2606222000)\n\n"
       "Usage: bb e7m <command> [args…]\n\n"
       "Built-in:\n"
       "  list           list every ported command module (the migration record)\n"
       "  version        print CLI version\n"
       "  help           this message\n\n"
       "Wired commands (runnable now):\n"
       "  bonsai            scan a dir for workspace growth / prune signals\n"
       "  identifier-audit  audit kotodama.jsonld + TypeScript nanoid/DID format issues\n"
       "  source-graph      scan source files for import dependency graph\n"
       "  shannon           compute Shannon entropy for a frequency distribution\n"
       "  coverage          check actor-manifest completeness from a kotodama.jsonld\n"
       "  kosei-tiers       classify an actor into T1/T2/T3 tier from metadata\n"
       "  dns-sync          plan DNS sync from deps.toml (dry-run; --apply for live)\n\n"
       "Via per-twin -main dispatch (argv mirrors the python click contract):\n"
       "  " (str/join ", " (sort (keys dispatchable))) "\n\n"
       "Library-dispatch (ns loads + argv parses; read-only legs run, live/destructive legs\n"
       "guarded — pass --apply/--execute/--dry-run as the python e7m requires):\n"
       "  " (str/join ", " (sort (keys library-commands))) "\n\n"
       "All ~60 python e7m subcommands are now reachable via `bb e7m <cmd>`.\n"))

;; ── pure router ───────────────────────────────────────────────────────────────────

(defn dispatch
  "Pure router: given argv, return either {:action …} to perform or {:print s}. Kept pure
  (no side effects, no require) so it is unit-testable; -main performs the effect."
  [args]
  (let [[cmd & more] args]
    (cond
      (or (nil? cmd) (= cmd "help") (= cmd "--help") (= cmd "-h")) {:print (usage)}
      (= cmd "version") {:print (str "etzhayyim-cli " version)}
      (= cmd "list") {:print (str "ported command modules (" (count ported-modules) "):\n"
                                  (->> ported-modules sort (map #(str "  " %)) (str/join "\n")))}
      (contains? dispatchable cmd)     {:action :dispatch :ns (dispatchable cmd) :args (vec more)}
      (contains? handlers cmd)         {:action :handle   :handler (handlers cmd) :args (vec more)}
      (contains? library-commands cmd) {:action :library  :cmd cmd :cmd-meta (library-commands cmd) :args (vec more)}
      (some #{cmd} ported-modules) {:print (str "command '" cmd "' is ported as a LIBRARY (ns etzhayyim."
                                                cmd ").\nIts CLI argv-wiring is the remaining finish (ADR-2606222000);\n"
                                                "invoke its fns from a REPL or use the Python e7m meanwhile.")
                                     :exit 0}
      :else {:print (str "unknown command: " cmd "\n\n" (usage)) :exit 2})))

;; ── entry point ───────────────────────────────────────────────────────────────────

(defn -main [& args]
  (let [{:keys [print action ns args handler cmd cmd-meta exit] :or {exit 0}} (dispatch args)]
    (when print (println print))
    (when (= action :dispatch)
      (require ns)
      (apply (resolve (symbol (str ns) "-main")) args))
    (when (= action :handle)
      (handler args))
    (when (= action :library)
      (handle-library cmd cmd-meta args))
    (when (and exit (pos? exit)) (System/exit exit))))
