;; etzhayyim.haisen — Actor wiring diagram (cljc port, wave 3b).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/haisen.py
;; (no click, no subprocess, no httpx — JSON parsing + regex scanning + graph analysis).
;;
;; API:
;;   (app-from-jsonld  data)              → HaisenApp map or nil
;;   (scan-workspace   ws-path)           → HaisenReport map
;;   (orphans          report)            → seq of HaisenApp maps (no edges)
;;   (coupling         report)            → sorted seq of [nanoid in-degree] pairs (desc)
;;
;; HaisenApp  = {:nanoid :did :name :performer-type :ui-type :runtime-type
;;               :collections :wit-imports :wit-exports}
;; HaisenEdge = {:from :to :type}   (type ∈ #{:subscribe :invoke :writes :reads :wasm-import})
;; HaisenReport = {:apps [HaisenApp] :edges [HaisenEdge]}
;;
;; I/O (filesystem) is in the #?(:clj ...) scan helpers; pure logic is platform-neutral.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.haisen :as h])
;;   (let [r (h/scan-workspace "/path/to/repo")]
;;     (println "apps" (count (:apps r)) "edges" (count (:edges r))))

(ns etzhayyim.haisen
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json])))

;; ── data constructors ─────────────────────────────────────────────────────────

(defn make-app
  "Build a HaisenApp map from a decoded kotodama.jsonld map."
  [data]
  {:nanoid         (get data "nanoid" "")
   :did            (get data "did" "")
   :name           (get data "name" "")
   :performer-type (get data "performerType" "")
   :ui-type        (get data "uiType" "")
   :runtime-type   (get data "runtimeType" "")
   :collections    (get data "collections" [])
   :wit-imports    (get data "witImports" [])
   :wit-exports    (get data "witExports" [])})

(defn app->dict
  "Serialise a HaisenApp to a string-keyed map (matches Python to_dict)."
  [app]
  {"nanoid"        (:nanoid app)
   "did"           (:did app)
   "name"          (:name app)
   "performerType" (:performer-type app)
   "uiType"        (:ui-type app)
   "runtimeType"   (:runtime-type app)
   "collections"   (:collections app)
   "witImports"    (:wit-imports app)
   "witExports"    (:wit-exports app)})

(defn edge->dict [edge]
  {"from" (:from edge) "to" (:to edge) "type" (name (:type edge))})

(defn app-from-jsonld
  "Parse a decoded kotodama.jsonld map into a HaisenApp, or nil if nanoid missing."
  [data]
  (when (seq (get data "nanoid" ""))
    (make-app data)))

;; ── pure graph analysis ───────────────────────────────────────────────────────

(defn orphans
  "Return apps that have no edges (neither source nor target)."
  [{:keys [apps edges]}]
  (let [connected (into #{} (mapcat (fn [e] [(:from e) (:to e)]) edges))]
    (remove #(contains? connected (:nanoid %)) apps)))

(defn coupling
  "Return [[nanoid in-degree] ...] sorted descending by in-degree."
  [{:keys [edges]}]
  (let [counts (reduce (fn [acc e]
                         (update acc (:to e) (fnil inc 0)))
                       {}
                       edges)]
    (sort-by (fn [[_ n]] (- n)) (seq counts))))

(defn report->dict [{:keys [apps edges]}]
  {"apps"  (mapv app->dict apps)
   "edges" (mapv edge->dict edges)})

;; ── regex patterns ────────────────────────────────────────────────────────────

;; Mirrors the Python RE patterns:
;;   _RE_INVOKE  r'(?:invoke|hostImports\.invoke)\(\s*["\']([a-z][a-z0-9.]+)["\']'
;;   _RE_WRITES  r'createRecord\(\s*["\']([a-z][a-z0-9.]+)["\']'
;;   _RE_READS   r'getRecord\(\s*["\']([a-z][a-z0-9.]+)["\']'
;;   subscribe   r'subscribe\(\s*["\']([a-z][a-z0-9.]+)["\']'

(def ^:private re-invoke
  #"(?:invoke|hostImports\.invoke)\(\s*[\"']([a-z][a-z0-9.]+)[\"']")
(def ^:private re-writes
  #"createRecord\(\s*[\"']([a-z][a-z0-9.]+)[\"']")
(def ^:private re-reads
  #"getRecord\(\s*[\"']([a-z][a-z0-9.]+)[\"']")
(def ^:private re-subscribe
  #"subscribe\(\s*[\"']([a-z][a-z0-9.]+)[\"']")

(defn- re-find-all [pattern s]
  (let [m (re-matcher pattern s)]
    (loop [results []]
      (if (.find m)
        (recur (conj results (.group m 1)))
        results))))

;; ── edge-building pure logic ──────────────────────────────────────────────────

(defn build-edges
  "Build HaisenEdge vectors from a seq of parsed app-data maps + TS source content map.
   apps-data  = seq of decoded jsonld maps (with 'nanoid', 'collections', etc.)
   src-map    = {nanoid → ts-source-string}
   Returns seq of {:from :to :type} maps (deduplicated, no self-loops)."
  [apps-data src-map]
  (let [apps         (keep app-from-jsonld apps-data)
        nanoid-set   (into #{} (map :nanoid apps))
        coll-owner   (into {} (mapcat (fn [a]
                                        (map (fn [c] [c (:nanoid a)])
                                             (:collections a)))
                                      apps))
        export-owner (into {} (mapcat (fn [a]
                                        (map (fn [e] [e (:nanoid a)])
                                             (:wit-exports a)))
                                      apps))
        seen         (atom #{})
        edges        (atom [])]

    (letfn [(add-edge! [from to etype]
              (let [k [from to etype]]
                (when (and (not= from to)
                           (not (contains? @seen k)))
                  (swap! seen conj k)
                  (swap! edges conj {:from from :to to :type etype}))))]

      (doseq [app apps]
        (let [nanoid (get app :nanoid)
              data   (some (fn [d] (when (= (get d "nanoid") nanoid) d)) apps-data)
              src    (get src-map nanoid "")]

          ;; Explicit subscribe dependencies from the jsonld "subscribes" list
          (doseq [dep (get data "subscribes" [])]
            (when (contains? nanoid-set dep)
              (add-edge! nanoid dep :subscribe)))

          ;; Subscribe from source: subscribe('col.nsid')
          (doseq [col (re-find-all re-subscribe src)]
            (when-let [owner (get coll-owner col)]
              (add-edge! nanoid owner :subscribe)))

          ;; Invoke from source
          (doseq [nsid (re-find-all re-invoke src)]
            (let [parts (str/split nsid #"\.")]
              (when (>= (count parts) 5)
                (let [candidate (str/join "." (take 4 parts))]
                  (doseq [a apps]
                    (when (and (not= (:nanoid a) nanoid)
                               (some #(str/starts-with? % candidate) (:collections a)))
                      (add-edge! nanoid (:nanoid a) :invoke)))))))

          ;; Writes / Reads from source
          (doseq [nsid (re-find-all re-writes src)]
            (when-let [owner (get coll-owner nsid)]
              (add-edge! nanoid owner :writes)))

          (doseq [nsid (re-find-all re-reads src)]
            (when-let [owner (get coll-owner nsid)]
              (add-edge! nanoid owner :reads)))

          ;; wasm-import edges from witImports vs other apps' witExports
          (doseq [imp (:wit-imports app)]
            (when-let [owner (get export-owner imp)]
              (add-edge! nanoid owner :wasm-import)))

          ;; Explicit dependency declarations from "dependencies" list
          (doseq [dep (get data "dependencies" [])]
            (when (contains? nanoid-set dep)
              (add-edge! nanoid dep :invoke))))))

    @edges))

;; ── I/O edge (Clojure/bb only) ────────────────────────────────────────────────

#?(:clj
   (do
     (require '[babashka.fs :as fs])

     (defn- read-jsonld [path]
       (try
         (json/parse-string (slurp path))
         (catch Exception _ {})))

     (defn- read-ts-src [app-dir]
       ;; Concatenate all *.ts files under app-dir
       (let [dir (fs/file app-dir)]
         (if (.isDirectory dir)
           (apply str
                  (for [f (file-seq dir)
                        :when (and (.isFile f)
                                   (str/ends-with? (.getName f) ".ts"))]
                    (try (slurp f) (catch Exception _ ""))))
           "")))

     (defn scan-workspace
       "Scan a repo root (ws-path string or File) for kotodama.jsonld files and
       return a HaisenReport {:apps [...] :edges [...]}."
       [ws-path]
       (let [ws       (fs/file ws-path)
             base     (let [b60 (fs/file ws "60-apps")]
                        (if (fs/exists? b60) b60
                          (let [bp  (fs/file ws "projects")]
                            (if (fs/exists? bp) bp ws))))
             jsonld-paths (if (fs/exists? base)
                            (filter #(str/ends-with? (str %) "kotodama.jsonld")
                                    (file-seq (fs/file base)))
                            [])
             apps-data   (mapv read-jsonld jsonld-paths)
             apps        (vec (keep app-from-jsonld apps-data))
             ;; src-map: nanoid → concatenated TS source
             src-map     (into {}
                               (for [d apps-data
                                     :let [nanoid (get d "nanoid" "")]
                                     :when (seq nanoid)
                                     :let [dir (some (fn [p]
                                                       (when (= (get (read-jsonld p) "nanoid") nanoid)
                                                         (.getParent (fs/file p))))
                                                     jsonld-paths)]
                                     :when dir]
                                 [nanoid (read-ts-src dir)]))
             edges       (build-edges apps-data src-map)]
         {:apps  apps
          :edges edges}))))
