(ns jinushi.methods.emit-real
  "jinushi 地主 — emit the REAL acquisition onto the canonical kotoba Datom log (the actor's telos).

  Folds the committed multi-source snapshots → the world-coverage dataset → analyze → a canonical
  EAVT Datom log (ground :owner/* + :parcel/* :add datoms + derived :jinushi/* transient
  aggregates), written to the repo DATA LAYER and content-addressed to a CIDv1 (like genome's
  genome-datoms.kotoba.edn, ADR-2605241500). This is what makes the acquired world land data
  FIRST-CLASS canonical state (ADR-2605312345), not just a side file.

  G1 carries through: the real Datom log holds no :person/* dimension and no precise coordinate
  (owners are public buckets, persons fold to aggregate) — test-enforced."
  (:require [clojure.java.io :as io]
            [jinushi.methods.analyze :as analyze]
            [jinushi.methods.ingest :as ingest]
            [jinushi.methods.datom-emit :as datom-emit]
            [jinushi.methods.cid :as cid]))

(defn real-datom-log
  "Pure-ish: snapshots → canonical EAVT Datom-log text for the world-coverage (counting) dataset."
  ([snaps] (real-datom-log snaps 1))
  ([snaps tx]
   (let [ds (ingest/counting-dataset snaps)]
     (datom-emit/emit ds (analyze/analyze ds) tx))))

(defn -main [& argv]
  (let [here (or (some-> (when (and *file* (not= *file* "NO_SOURCE_PATH")) (io/file *file*))
                         .getParentFile .getParentFile)
                 (io/file "20-actors/jinushi"))
        root (or (some-> here .getParentFile .getParentFile) (io/file "."))
        dir (ingest/data-dir root)
        snaps (ingest/load-all-snapshots dir)
        out (io/file dir "jinushi-land-datoms.kotoba.edn")]
    (spit out (real-datom-log snaps 1))
    (println (str "real kotoba Datom log → " out))
    (println (str "CIDv1: " (cid/file->cidv1 out)))
    0))
