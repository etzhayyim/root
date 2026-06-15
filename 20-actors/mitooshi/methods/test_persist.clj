#!/usr/bin/env bb
;; Working Clojure port of methods/test_persist.py.
(ns mitooshi.methods.test-persist
  "Tests for the mitooshi append-only chokepoint-intel persistence (methods/persist.clj).

  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/test_persist.clj

  The load-bearing property under test: the trail is APPEND-ONLY (非終末論). A re-run is
  idempotent; a new snapshot is additive; an existing observation is NEVER removed or
  mutated; the emitted EDN round-trips through the same reader a live ingest would use."
  (:require [mitooshi.methods.bridge :as mb]
            [mitooshi.methods.persist :as mp]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)

(defn- bridge-data-dir []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "bridge")))

(defn- by-actor []
  {"watari"    (mb/load-edn (io/file (bridge-data-dir) "watari-sample.edn"))
   "watatsuna" (mb/load-edn (io/file (bridge-data-dir) "watatsuna-sample.edn"))})

;; ── helper: parse EDN from a string (load-trail only takes a path) ────────────
(defn- load-edn-from-str [s]
  (let [tmp (java.io.File/createTempFile "persist-test-" ".edn")]
    (try
      (spit tmp s)
      (let [[series obs] (mp/load-trail tmp)]
        ;; return flat list of all records, matching Python load_edn_from_str behaviour
        (concat (vals series) obs))
      (finally
        (.delete tmp)))))

;; ── tests ─────────────────────────────────────────────────────────────────────

(deftest test-append-to-empty-trail-adds-all
  (let [b (mb/bridge (by-actor) 1)
        [merged added dup] (mp/append-obs [] (get b "obs"))]
    (is (= added (count (get b "obs"))))
    (is (= dup 0))
    (is (= (count merged) (count (get b "obs"))))))

(deftest test-reappend-same-snapshot-is-idempotent
  (let [b (mb/bridge (by-actor) 1)
        [merged _ _] (mp/append-obs [] (get b "obs"))
        [merged2 added2 dup2] (mp/append-obs merged (get b "obs"))]
    ;; nothing new, all duplicates
    (is (= added2 0))
    (is (= dup2 (count (get b "obs"))))
    ;; trail unchanged
    (is (= (count merged2) (count merged)))))

(deftest test-new-snapshot-is-additive-never-removes
  (let [b1 (mb/bridge (by-actor) 1)
        b2 (mb/bridge (by-actor) 2)
        [merged _ _] (mp/append-obs [] (get b1 "obs"))
        before-ids (set (map #(get % ":obs/id") merged))
        [merged2 added2 dup2] (mp/append-obs merged (get b2 "obs"))
        after-ids (set (map #(get % ":obs/id") merged2))]
    ;; 非終末論: never drops an obs
    (is (every? #(contains? after-ids %) before-ids))
    ;; different ts → all new
    (is (= added2 (count (get b2 "obs"))))
    (is (= dup2 0))))

(deftest test-existing-obs-values-are-not-mutated
  (let [b1 (mb/bridge (by-actor) 1)
        [merged _ _] (mp/append-obs [] (get b1 "obs"))
        snapshot (into {} (map (fn [o] [(get o ":obs/id") (get o ":obs/value")]) merged))
        ;; a later (hypothetically revised) snapshot at the same ts must NOT overwrite
        [merged2 added dup] (mp/append-obs merged (get b1 "obs"))
        after (into {} (map (fn [o] [(get o ":obs/id") (get o ":obs/value")]) merged2))]
    (is (= after snapshot))
    (is (= added 0))))

(deftest test-merge-series-is-union-first-wins
  (let [b (mb/bridge (by-actor) 1)
        merged (mp/merge-series {} (get b "series"))]
    (is (= (set (keys merged)) (set (keys (get b "series")))))
    ;; re-merging keeps the first definition (stable identity)
    (let [again (mp/merge-series merged (get b "series"))]
      (is (= again merged)))))

(deftest test-emit-round-trips-through-reader
  (let [b (mb/bridge (by-actor) 1)
        [merged-obs _ _] (mp/append-obs [] (get b "obs"))
        edn-str (mp/emit-trail-edn (get b "series") merged-obs)
        recs (load-edn-from-str edn-str)
        obs    (filter #(contains? % ":obs/id") recs)
        series (filter #(contains? % ":series/id") recs)]
    (is (= (count obs) (count merged-obs)))
    (is (= (count series) (count (get b "series"))))
    ;; values survive the round-trip
    (let [vals-after  (sort (map #(get % ":obs/value") obs))
          vals-before (sort (map #(get % ":obs/value") merged-obs))]
      (is (= vals-after vals-before)))))

(deftest test-persist-to-disk-two-snapshots-accumulate
  (let [tmp-dir (java.io.File/createTempFile "persist-test-dir-" "")
        _ (.delete tmp-dir)
        _ (.mkdirs tmp-dir)
        trail (io/file tmp-dir "chokepoint-trail.kotoba.edn")]
    (try
      (let [s1 (mp/persist trail (mb/bridge (by-actor) 1))
            s2 (mp/persist trail (mb/bridge (by-actor) 2))
            s3 (mp/persist trail (mb/bridge (by-actor) 2))]   ; idempotent re-run
        (is (> (get s1 "added") 0))
        (is (= (get s2 "added") (get s1 "added")))
        (is (= (get s2 "duplicate") 0))
        (is (= (get s3 "added") 0))
        (is (= (get s3 "duplicate") (get s2 "added")))
        ;; on-disk trail holds both snapshots
        (let [[_ obs] (mp/load-trail trail)
              ats (sort (set (map #(get % ":obs/observed-at") obs)))]
          (is (= ats [1 2]))))
      (finally
        ;; clean up temp files
        (doseq [f (reverse (file-seq tmp-dir))]
          (.delete f))))))

(deftest test-persist-header-marks-derived-and-gated
  (let [b (mb/bridge (by-actor) 1)
        [merged-obs _ _] (mp/append-obs [] (get b "obs"))
        edn-str (mp/emit-trail-edn (get b "series") merged-obs)]
    (is (str/includes? edn-str "APPEND-ONLY"))
    (is (str/includes? edn-str "DERIVED"))
    (is (str/includes? edn-str "G10-gated"))
    (is (str/includes? edn-str "非終末論"))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'mitooshi.methods.test-persist)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
