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
  (:require [clojure.string :as str]))

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
