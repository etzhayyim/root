;; etzhayyim.source-graph — Source-level import/dependency graph (cljc port, wave 1).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/source_graph.py
;; (no click, no subprocess, no network I/O — regex scanning + graph analysis).
;;
;; API:
;;   (parse-ts-imports   content)          → seq of import strings
;;   (parse-py-imports   content)          → seq of module names
;;   (scan-source-graph  files)            → SGReport map
;;   (orphan-paths       report)           → sorted seq of unreferenced paths
;;   (cycles             report)           → seq of cycle paths
;;   (layer-violations   report)           → seq of cross-layer violation maps
;;
;; files = seq of {:path str :content str} — callers supply pre-read content.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.source-graph :as sg])
;;   (let [report (sg/scan-source-graph
;;                  [{:path "src/app.ts" :content (slurp "src/app.ts")}])]
;;     (println "nodes:" (count (:nodes report))
;;              "cycles:" (count (sg/cycles report))))

(ns etzhayyim.source-graph
  (:require [clojure.string :as str]))

;; ── regex patterns ──────────────────────────────────────────────────────────────

;; TypeScript/Svelte: import 'x' | from 'x' | import "x" | from "x"
(def ^:private re-ts-import #"(?:import|from)\s+['\"]([^'\"]+)['\"]")
;; Python: import foo | from foo.bar
(def ^:private re-py-import #"(?m)^(?:import|from)\s+([\w.]+)")

(def ^:private skip-dirs    #{"node_modules" ".git" "__pycache__" ".venv" "dist" "build"})
(def ^:private skip-prefixes ["@" "node:" "bun:" "https://" "http://"])

;; ── layer order (mirrors Python source_graph._LAYER_ORDER) ─────────────────────

(def ^:private layer-order
  ["00-contracts" "10-protocol" "20-actors" "30-graph" "40-engine"
   "50-infra" "60-apps" "70-tools" "80-packages" "90-docs"])

(defn- layer-of
  "Return the layer prefix string for a path, or nil."
  [path]
  (some #(when (or (str/starts-with? path (str % "/"))
                   (str/includes? (str "/" path) (str "/" % "/")))
           %)
        layer-order))

(defn- layer-index
  [layer]
  (if layer
    (let [idx (.indexOf layer-order layer)]
      (if (neg? idx) -1 idx))
    -1))

;; ── import parsers ──────────────────────────────────────────────────────────────

(defn parse-ts-imports
  "Extract import/from strings from TypeScript/Svelte source.
   Skips node: / bun: / @ / http(s):// specifiers."
  [content]
  (->> (re-seq re-ts-import (or content ""))
       (map second)
       (remove (fn [s] (some #(str/starts-with? s %) skip-prefixes)))
       vec))

(defn parse-py-imports
  "Extract Python top-level module names.
   Skips private modules starting with '_'."
  [content]
  (->> (re-seq re-py-import (or content ""))
       (map second)
       (remove #(str/starts-with? % "_"))
       vec))

;; ── helpers ─────────────────────────────────────────────────────────────────────

(defn- skip-path? [path]
  (some skip-dirs (str/split path #"/")))

(defn- ext-of [path]
  (let [base (last (str/split path #"/"))
        dot  (str/last-index-of base ".")]
    (if (and dot (pos? dot)) (subs base dot) "")))

;; ── scan-source-graph ───────────────────────────────────────────────────────────

(defn scan-source-graph
  "Scan a collection of {:path str :content str} file maps.
   Returns an SGReport map:
     {:nodes [{:path :lang :imports} ...]
      :edges [{:source :target} ...]}"
  [files]
  (let [{:keys [nodes edges seen-edges]}
        (reduce
         (fn [acc {:keys [path content]}]
           (if (skip-path? path)
             acc
             (let [ext (ext-of path)]
               (cond
                 (#{"ts" ".ts" "svelte" ".svelte"} ext)
                 (let [imports  (parse-ts-imports content)
                       node     {:path path :lang "typescript" :imports imports}
                       ;; For relative imports (./ or ../), we can only mark
                       ;; the raw import string as a target since we don't have
                       ;; real filesystem resolution here.
                       new-edges (keep (fn [imp]
                                         (when (str/starts-with? imp ".")
                                           {:source path :target imp}))
                                       imports)
                       unseen   (remove #((:seen-edges acc) [(:source %) (:target %)]) new-edges)]
                   (-> acc
                       (update :nodes conj node)
                       (update :edges into unseen)
                       (update :seen-edges into (map #(vector (:source %) (:target %)) unseen))))

                 (#{"py" ".py"} ext)
                 (let [imports (parse-py-imports content)
                       node    {:path path :lang "python" :imports imports}]
                   (update acc :nodes conj node))

                 :else acc))))
         {:nodes [] :edges [] :seen-edges #{}}
         files)]
    {:nodes (vec nodes)
     :edges (vec edges)}))

;; ── graph analysis ──────────────────────────────────────────────────────────────

(defn orphan-paths
  "Paths that are neither a source nor a target of any edge — unreferenced modules.
   Returns a sorted seq of path strings."
  [{:keys [nodes edges]}]
  (let [imported (into #{} (map :target edges))
        sources  (into #{} (map :source edges))
        all      (into #{} (map :path nodes))]
    (sort (clojure.set/difference all imported sources))))

(defn cycles
  "Detect cycles in the import graph using iterative DFS.
   Returns a seq of cycle path vectors.
   Capped at 50 cycles to avoid quadratic blowup on large graphs."
  [{:keys [edges]}]
  (let [max-cycles 50
        adj (reduce (fn [m {:keys [source target]}]
                      (update m source (fnil conj #{}) target))
                    {}
                    edges)
        found      (atom [])
        visited    (atom #{})
        rec-stack  (atom #{})]
    (letfn [(dfs [node path]
              (when (< (count @found) max-cycles)
                (swap! visited conj node)
                (swap! rec-stack conj node)
                (doseq [nb (get adj node #{})]
                  (when (< (count @found) max-cycles)
                    (if (not (@visited nb))
                      (dfs nb (conj path nb))
                      (when (@rec-stack nb)
                        (let [idx (or (.indexOf path nb) 0)
                              cyc (conj (vec (drop idx path)) nb)]
                          (when-not (some #(= % cyc) @found)
                            (swap! found conj cyc)))))))
                (swap! rec-stack disj node)))]
      (doseq [n (keys adj)]
        (when (and (not (@visited n))
                   (< (count @found) max-cycles))
          (dfs n [n])))
      @found)))

(defn layer-violations
  "Find imports from a higher-numbered layer into a lower-numbered layer.
   Returns a seq of {:source :target :source-layer :target-layer :direction} maps."
  [{:keys [edges]}]
  (->> edges
       (keep (fn [{:keys [source target]}]
               (let [sl (layer-of source)
                     tl (layer-of target)]
                 (when (and sl tl (not= sl tl))
                   (let [si (layer-index sl)
                         ti (layer-index tl)]
                     (when (> si ti)
                       {:source source :target target
                        :source-layer sl :target-layer tl
                        :direction (str sl " → " tl " (lower layer)")}))))))
       vec))
