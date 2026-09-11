;; etzhayyim.kotoba.boundary — machine-enforce the root↔subrepo data boundary.
;;
;; DIRECTIVE (2026-06-14, restated across the loop): "kotoba subrepo にはデータ/
;; 実装を置かず、データ・実装は root に置く." This guard makes that invariant
;; structural rather than a habit: religious-corp DATA artifacts must never land
;; physically inside the kotoba subrepo (40-engine/kotoba/, a separate generic
;; engine repo). They belong in root — 00-contracts/schemas/ (vocabularies) and
;; 80-data/ (Datom logs/snapshots).
;;
;; What counts as a violation: a religious-corp DATA/VOCAB artifact physically in
;; the subrepo, identified by the *.kotoba.edn extension — the etzhayyim-specific
;; marker used by EVERY root data/schema file (00-contracts/schemas/*.kotoba.edn,
;; 80-data/**/*-datoms.kotoba.edn). The generic engine never uses this extension,
;; so the rule is precise (no false positives on the engine's own *.json/*.edn
;; demo fixtures, e.g. crates/kotoba-wasm/web/seed-datoms.json).
;;
;; The kotoba-kotodama crate legitimately REFERENCES root data by path
;; (e.g. "80-data/...") — code-in-subrepo reading data-in-root, the correct
;; direction, and is NOT flagged.
;;
;; Run: bb lint:kotoba-boundary   (asserts clean; non-zero exit on violation)

(ns etzhayyim.kotoba.boundary
  (:require [clojure.java.io :as io]
            [clojure.string :as str]))

(def subrepo-root "40-engine/kotoba")

(defn- data-artifact?
  "True if `name` is a religious-corp data/vocab artifact (the .kotoba.edn marker)."
  [^String name]
  (str/ends-with? name ".kotoba.edn"))

(defn scan
  "Return a seq of relative paths of data artifacts found inside `root`
   (default the kotoba subrepo). Empty seq = boundary clean."
  ([] (scan subrepo-root))
  ([root]
   (let [base (io/file root)]
     (when (.exists base)
       (->> (file-seq base)
            (filter #(.isFile %))
            (filter #(data-artifact? (.getName %)))
            (map #(.getPath %))
            (remove #(str/includes? % "/.git/"))
            (sort)
            (vec))))))

(defn check
  "Return {:clean? bool :violations [paths] :root subrepo-root}."
  ([] (check subrepo-root))
  ([root]
   (let [v (vec (scan root))]
     {:clean? (empty? v) :violations v :root root})))

(defn -main [& _]
  (let [{:keys [clean? violations root]} (check)]
    (if clean?
      (println (str "✓ kotoba boundary clean: no religious-corp data artifacts in " root "/"))
      (do (println (str "✗ kotoba boundary VIOLATION: " (count violations)
                        " data artifact(s) inside the subrepo " root "/ —"
                        " move them to 00-contracts/schemas/ or 80-data/:"))
          (doseq [p violations] (println "   " p))
          (println "   (the kotoba subrepo is the generic engine; religious-corp data lives in root)")
          (System/exit 1)))))
