;; etzhayyim.logs — OCEL v2 log viewer and arch-layer analysis (cljc port, wave 4a).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/logs.py.
;; (no click, no httpx, no subprocess at load time)
;;
;; API (pure functions — no IO at load time):
;;   (classify-layer path)          → layer keyword string
;;   (classify-scope path layer)    → scope string
;;   (parse-arch-log lines)         → seq of commit event maps
;;   (arch-report   events)         → aggregated report map
;;
;; IO legs (deferred — operator-gated):
;;   The git-log subprocess and XRPC HTTP calls (logs/tail/errors/stats) are host
;;   edges NOT included here. A babashka task can drive classify-layer/classify-scope
;;   after invoking `git log --stat` via babashka.process.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.logs :as logs])
;;   (logs/classify-layer "60-apps/foo")

(ns etzhayyim.logs
  "OCEL log viewer + architecture-layer commit distribution — pure logic layer."
  (:require [clojure.string :as str]))

;; ── Layer prefixes (matches Python _LAYER_PREFIXES order) ─────────────────────

(def ^:private layer-prefixes
  [["orgs/etzhayyim/com-etzhayyim-" "actors"]
   ["60-apps/"     "projects"]
   ["50-infra/"    "infra"]
   ["20-actors/"   "actors"] ; historical events emitted before flat-west migration
   ["90-docs/"     "docs"]
   ["40-engine/"   "engine"]
   ["30-graph/"    "graph"]
   ["00-contracts/" "contracts"]
   ["70-tools/"    "tools"]])

(defn classify-layer
  "Return the architecture-layer string for a file path.
   Matches Python _classify_layer — first-prefix-match wins, default \"root\"."
  [path]
  (or (some (fn [[prefix layer]]
              (when (str/starts-with? (str path) prefix)
                layer))
            layer-prefixes)
      "root"))

(defn classify-scope
  "Return the scope (second path segment) for a file path + layer string.
   Matches Python _classify_scope: returns \"root\" for root layer or short paths,
   otherwise the second path segment."
  [path layer]
  (let [parts (str/split (str path) #"/")]
    (if (or (= layer "root") (< (count parts) 2))
      "root"
      (nth parts 1))))

;; ── Arch-log parser ────────────────────────────────────────────────────────────
;; Parses the output of:
;;   git log --pretty=format:"%H|%aI|%an|%s" --stat --since=... -nN
;;
;; Returns a seq of commit-event maps:
;;   {:sha str :ts str :author str :message str
;;    :added int :removed int :layer str :scope str :files [str]}

(defn- flush-commit
  "Finalise a buffered commit map using the accumulated file list.
   Returns the completed map."
  [cur cur-files]
  (when cur
    (let [layer-counts (reduce (fn [m f]
                                 (let [ly (classify-layer f)]
                                   (assoc m ly (inc (get m ly 0)))))
                               {} cur-files)
          dominant (if (empty? layer-counts)
                     "root"
                     (key (apply max-key val layer-counts)))
          scope (if (seq cur-files)
                  (classify-scope (first cur-files) dominant)
                  "root")]
      (assoc cur
             :layer dominant
             :scope scope
             :files (vec cur-files)))))

(defn- header-line?
  "A header line matches SHA|timestamp|author|subject."
  [line]
  (boolean (re-find #"^[0-9a-f]{40}\|" line)))

(defn- parse-stat-additions
  "Extract added / removed line counts from a git --stat summary line."
  [line]
  (let [added   (re-find #"(\d+) insertion" line)
        removed (re-find #"(\d+) deletion"  line)]
    {:added   (if added   (Long/parseLong (second added))   0)
     :removed (if removed (Long/parseLong (second removed)) 0)}))

(defn- stat-line?
  "True if the line looks like the 'N files changed' summary."
  [line]
  (boolean (re-find #"^\s*\d+ files? changed" line)))

(defn- file-stat-line?
  "True if the line looks like a per-file stat entry (path | changes)."
  [line]
  (and (re-find #"^\s*.+\s+\|\s+\d+" line)
       (not (re-find #"^\s*(Bin |binary)" line))))

(defn parse-arch-log
  "Parse git log --stat --pretty=format:'%H|%aI|%an|%s' output lines into a
   seq of commit event maps. Pure — operates on a seq of strings."
  [lines]
  (let [result (atom [])
        cur    (atom nil)
        files  (atom [])]
    (doseq [line lines]
      (cond
        (header-line? line)
        (do
          (when-let [done (flush-commit @cur @files)]
            (swap! result conj done))
          (let [[sha ts author msg] (str/split line #"\|" 4)]
            (reset! cur {:sha     (subs sha 0 (min 12 (count sha)))
                         :ts      (str ts)
                         :author  (str author)
                         :message (str msg)
                         :added   0
                         :removed 0})
            (reset! files [])))

        (nil? @cur) nil   ;; skip lines before first commit header

        (stat-line? line)
        (let [{:keys [added removed]} (parse-stat-additions line)]
          (swap! cur assoc :added added :removed removed))

        (file-stat-line? line)
        (let [m (re-find #"^\s*(.+?)\s+\|\s+\d+" line)]
          (when m
            (swap! files conj (str/trim (second m)))))))
    ;; flush last
    (when-let [done (flush-commit @cur @files)]
      (swap! result conj done))
    @result))

(defn arch-report
  "Aggregate commit events into a report map with :by-layer, :by-scope, :total-events, :events.
   Optionally merges in deploy-state map under :deploy-state."
  ([events] (arch-report events {}))
  ([events deploy-state]
   (let [by-layer (reduce (fn [m ev]
                            (let [ly (:layer ev "root")]
                              (assoc m ly (inc (get m ly 0)))))
                          {} events)
         by-scope (reduce (fn [m ev]
                            (let [sc (:scope ev "root")]
                              (assoc m sc (inc (get m sc 0)))))
                          {} events)]
     {:total-events  (count events)
      :by-layer      by-layer
      :by-scope      by-scope
      :events        (vec events)
      :deploy-state  deploy-state})))
