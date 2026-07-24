;; vertex.cljc — Graph vertex tier-registry parsing, pure logic.
;;
;; Ports the pure-logic subset of etzhayyim-py vertex.py:
;;   - parse-tier-registry  : parse a deps.toml string → tier registry map
;;   - lookup-tier          : look up a table name in the registry
;;   - tier-stats           : count tables per tier
;;   - tier-tables          : sorted table list for a given tier
;;
;; IO (httpx graph calls, file reading) is DEFERRED — operator bb legs only.
;;
;; ns: etzhayyim.vertex
;; Load check: bb --classpath 70-tools/src -e "(require 'etzhayyim.vertex)(println :ok)"

(ns etzhayyim.vertex
  (:require [clojure.string :as str]
            #?(:bb [cheshire.core :as json])))

;; ── regex patterns ────────────────────────────────────────────────────────────

(def ^:private re-section
  "Matches: [vertex_tier.tier_a] (or b/c)"
  #"^\[vertex_tier\.tier_([abc])\]\s*$")

(def ^:private re-table
  "Matches:   \"vertex_foo_bar\","
  #"^\s*\"(vertex_[a-z0-9_]+)\"\s*,?\s*$")

;; ── parser ────────────────────────────────────────────────────────────────────

(defn parse-tier-registry
  "Parse a deps.toml content string into a tier-registry map.

  Returns:
    {:a       [sorted table names for tier A]
     :b       [sorted table names for tier B]
     :c       [sorted table names for tier C]
     :index   {table-name → tier-keyword}}

  Equivalent to Python: _load_vertex_tier_registry(deps_path)
  (this fn accepts the file *content* string; caller handles file I/O)"
  [content]
  (let [lines        (str/split-lines content)
        {:keys [a b c index]}
        (loop [lines     lines
               tier      nil
               in-tables false
               a []  b []  c []
               index {}]
          (if (empty? lines)
            {:a a :b b :c c :index index}
            (let [line (first lines)
                  rest-lines (rest lines)
                  trimmed (str/trim line)]
              (if-let [[_ tier-ch] (re-matches re-section trimmed)]
                ;; new [vertex_tier.tier_x] section
                (recur rest-lines (keyword (str/upper-case tier-ch)) false a b c index)
                (cond
                  ;; any other TOML section → exit vertex_tier context
                  (and (str/starts-with? trimmed "[")
                       (not (str/starts-with? trimmed "[vertex_tier.")))
                  (recur rest-lines nil false a b c index)

                  ;; no active tier → skip
                  (nil? tier)
                  (recur rest-lines nil false a b c index)

                  ;; open tables = [
                  (and (str/starts-with? trimmed "tables")
                       (str/includes? trimmed "["))
                  (recur rest-lines tier true a b c index)

                  ;; close tables ]
                  (and in-tables (str/starts-with? trimmed "]"))
                  (recur rest-lines tier false a b c index)

                  ;; inside tables: pick up table name
                  (and in-tables (re-matches re-table line))
                  (let [[_ tname] (re-matches re-table line)
                        a'     (if (= tier :A) (conj a tname) a)
                        b'     (if (= tier :B) (conj b tname) b)
                        c'     (if (= tier :C) (conj c tname) c)
                        index' (assoc index tname tier)]
                    (recur rest-lines tier true a' b' c' index'))

                  :else
                  (recur rest-lines tier in-tables a b c index))))))]
    {:a     (sort a)
     :b     (sort b)
     :c     (sort c)
     :index index}))

;; ── lookup helpers ────────────────────────────────────────────────────────────

(defn lookup-tier
  "Return the tier keyword (:A, :B, :C) for table-name, or nil if unclassified.

  Python equivalent: reg['M'].get(table_name)"
  [registry table-name]
  (get (:index registry) table-name))

(defn tier-tables
  "Return a sorted seq of table names for the given tier keyword (:A, :B or :C).

  Python equivalent: reg[tier]"
  [registry tier]
  (case tier
    :A (:a registry)
    :B (:b registry)
    :C (:c registry)
    nil))

(defn tier-stats
  "Return aggregate counts {:tier-a N :tier-b N :tier-c N :total N}.

  Python equivalent: the vertex stats command."
  [registry]
  (let [na (count (:a registry))
        nb (count (:b registry))
        nc (count (:c registry))]
    {:tier-a na
     :tier-b nb
     :tier-c nc
     :total  (+ na nb nc)}))

;; ---------------------------------------------------------------------------
;; CLI entrypoint — mirrors the `vertex` click group (JVM/bb only).
;;
;; This twin ports ONLY the pure tier-registry logic (parse/lookup/stats).  The
;; emit/query/labels subcommands are live XRPC legs that are NOT ported here
;; (no http-client in this twin) — -main dispatches them to a NOT-PORTED notice
;; rather than rewriting logic.  tier/list/stats are real read-only local-file
;; commands and run for real off 30-graph/deps.toml.
;; ---------------------------------------------------------------------------

#?(:clj
   (do
     (defn- v-parse [args bool-flags]
       (loop [a (seq args) flags {} pos []]
         (if (empty? a)
           [flags pos]
           (let [tok (first a)]
             (cond
               (contains? bool-flags tok) (recur (rest a) (assoc flags tok true) pos)
               (str/starts-with? tok "--") (recur (drop 2 a) (assoc flags tok (second a)) pos)
               :else (recur (rest a) flags (conj pos tok)))))))

     (defn- v-resolve-deps
       "Resolve the 30-graph/deps.toml path: --deps override, else 30-graph/deps.toml
        under --workspace-dir (or cwd), walking up to find it. Returns path or nil."
       [flags]
       (or (get flags "--deps")
           (let [start (java.io.File. (or (get flags "--workspace-dir")
                                          (System/getProperty "user.dir")))]
             (loop [d start]
               (when d
                 (let [c (java.io.File. d "30-graph/deps.toml")]
                   (if (.exists c) (.getPath c) (recur (.getParentFile d)))))))))

     (defn- v-load [flags]
       (let [dp (v-resolve-deps flags)]
         (when-not (and dp (.exists (java.io.File. ^String dp)))
           (throw (ex-info "30-graph/deps.toml not found; use --deps to specify path" {})))
         [dp (parse-tier-registry (slurp dp))]))

     (defn- v-usage []
       (println "usage: vertex <subcommand> [options]")
       (println "subcommands: emit query labels tier list stats")
       (println "  tier/list/stats: read 30-graph/deps.toml (read-only, ported)")
       (println "  emit/query/labels: live XRPC legs — NOT ported in cljc twin"))

     (defn -main [& args]
       (let [bool-flags #{"--json"}
             [sub & rst] args
             [flags pos] (v-parse rst bool-flags)]
         (case sub
           nil (v-usage)
           ("emit" "query" "labels")
           (println (str "vertex " sub ": live XRPC leg not ported in the cljc twin "
                         "(only tier-registry pure logic is ported); use the python CLI."))
           "tier"
           (try
             (let [[_ reg] (v-load flags)
                   tn (first pos)
                   t  (lookup-tier reg tn)]
               (cond
                 (get flags "--json")
                 (println (json/generate-string {:table tn :tier (some-> t name)
                                                 :classified (some? t)}))
                 (nil? t)
                 (do (binding [*out* *err*]
                       (println (str tn ": not classified (default tier = C per ADR-0040)")))
                     (System/exit 1))
                 :else (println (str tn "\t" (name t)))))
             (catch clojure.lang.ExceptionInfo e (println "error:" (ex-message e))))
           "list"
           (try
             (let [[_ reg] (v-load flags)
                   tf (some-> (get flags "--tier") clojure.string/upper-case keyword)
                   lim (some-> (get flags "--limit") parse-long)
                   tables (cond->> (tier-tables reg tf)
                            (and lim (pos? lim)) (take lim))]
               (if (get flags "--json")
                 (println (json/generate-string {:tier (some-> tf name) :count (count tables)
                                                 :tables (vec tables)}))
                 (doseq [t tables] (println t))))
             (catch clojure.lang.ExceptionInfo e (println "error:" (ex-message e))))
           "stats"
           (try
             (let [[dp reg] (v-load flags)
                   {:keys [tier-a tier-b tier-c total]} (tier-stats reg)]
               (if (get flags "--json")
                 (println (json/generate-string {:tier_a tier-a :tier_b tier-b :tier_c tier-c
                                                 :total total :adr "adr-0040-vertex-did-tier-policy"}))
                 (do (println (str "ADR-0040 Vertex DID Tier registry (" dp ")"))
                     (println (format "  Tier A (actor DID):         %4d" tier-a))
                     (println (format "  Tier B (sub-path did:etzhayyim): %4d" tier-b))
                     (println (format "  Tier C (no DID):            %4d" tier-c))
                     (println (format "  Total:                      %4d" total)))))
             (catch clojure.lang.ExceptionInfo e (println "error:" (ex-message e))))
           (do (println "unknown subcommand:" sub) (v-usage)))))))
