;; etzhayyim.kotoba.log — append-only Datom journal persistence (root-side).
;;
;; The journal is EDN-lines (one [e a v tx op] datom per line) for O(1) append,
;; written under 80-data/ — NEVER inside the kotoba subrepo. A snapshot
;; materializer renders the live log into the canonical [ ... ] vector shape
;; used by 80-data/*/​*-datoms.kotoba.edn so downstream tools read one format.

(ns etzhayyim.kotoba.log
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.cid :as cid]))

(def default-journal "80-data/datomic_mock/journal.edn")

(defn ensure-journal! [path]
  (let [f (io/file path)]
    (io/make-parents f)
    (when-not (.exists f) (spit f ""))
    path))

(defn read-log
  "Read the append-only journal into a vector of [e a v tx op] datoms."
  [path]
  (if (.exists (io/file path))
    (->> (str/split-lines (slurp path))
         (remove str/blank?)
         (mapv edn/read-string))
    []))

(defn append!
  "Append `datoms` (seq of [e a v tx op]) to the journal. Returns count."
  [path datoms]
  (ensure-journal! path)
  (with-open [w (io/writer path :append true)]
    (doseq [dm datoms]
      (.write w (pr-str (vec dm)))
      (.write w "\n")))
  (count datoms))

(defn max-tx
  "Highest tx integer present in `log`, or 0 if empty."
  [log]
  (reduce (fn [m dm] (max m (or (d/d-tx dm) 0))) 0 log))

(defn head-cid
  "Content-address of the whole journal log (ordered datom vector).
   Advances on every committed transaction — the log's head pointer."
  [log]
  (cid/cid-of-edn (vec log)))

(defn snapshot->kotoba-edn!
  "Materialize the live state of `log` into a canonical .kotoba.edn vector file
   at `out-path` (the genome-datoms shape: a vector of live [e a v tx :add])."
  [log out-path & {:keys [header]}]
  (let [live (etzhayyim.kotoba.datom/live-datoms log)
        ;; preserve a representative tx per surviving triple (first assert)
        tx-of (reduce (fn [m dm]
                        (if (d/assert? dm)
                          (update m [(d/d-e dm) (d/d-a dm) (d/d-v dm)]
                                  (fn [x] (or x (d/d-tx dm))))
                          m))
                      {} log)
        rows (->> live
                  (sort-by (fn [[e a _]] [(str e) (str a)]))
                  (mapv (fn [[e a v]] [e a v (get tx-of [e a v] 1) :add])))]
    (io/make-parents (io/file out-path))
    (spit out-path
          (str (or header
                   ";; GENERATED kotoba Datom snapshot (etzhayyim.kotoba.log).\n;; Canonical live EAVT state [e a v tx op]. DO NOT hand-edit.\n")
               "[\n"
               (str/join "\n" (map pr-str rows))
               "\n]\n"))
    {:rows (count rows) :out out-path :head (head-cid log)}))
