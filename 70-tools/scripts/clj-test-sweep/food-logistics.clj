#!/usr/bin/env bb
;; Green-sweep runner for the food/logistics kotoba-datomic clj test corpus.
;;
;; Runs every `test_*.clj` under the food/logistics actors, each in an ISOLATED `bb`
;; subprocess (so the parity suites that themselves spawn python3 / nested bb cannot
;; interleave output and corrupt the tally), parses each suite's `Ran N tests` +
;; `F failures, E errors`, and reports per-suite PASS / FAIL / HOLLOW.
;;
;; HOLLOW = a suite that prints "0 failures, 0 errors" but ran 0 tests — a false-green
;; (e.g. a `.cljc` that defines `-main` bb never invokes). This wave hit that class twice
;; (ADR-2606152000 / mitooshi horizon+promote); this runner makes it a STRUCTURAL failure,
;; not a silent pass. The sweep exits non-zero on ANY fail or hollow suite.
;;
;; Run:  bb 70-tools/scripts/clj-test-sweep/food-logistics.clj
;;       (from the repo root; uses `--classpath 20-actors`)
(ns food-logistics
  (:require [babashka.process :as p]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def actors
  ["umisachi" "kamado" "niyaku" "haraedo" "mizuho" "hodoki" "kanayama" "mitsuho"
   "kakaku" "meyasu" "funadaiku" "uchiwake" "kabuto" "watari" "watatsuna" "kawaraban"
   "kanjo" "mitooshi" "sanae" "todoke" "ainori"])

(defn- actor-test-files []
  (->> actors
       (mapcat (fn [a]
                 (let [d (io/file "20-actors" a)]
                   (when (.isDirectory d)
                     (->> (file-seq d)
                          (filter #(and (.isFile %)
                                        (re-matches #"test_.*\.clj" (.getName %))))
                          (map #(.getPath %)))))))))

(defn- cross-actor-invariant-files []
  ;; substrate-level invariants that span multiple actors live alongside this runner
  ;; (e.g. canonical_form_invariant.clj) — name pattern *_invariant.clj, not test_*.
  (let [d (io/file "70-tools" "scripts" "clj-test-sweep")]
    (when (.isDirectory d)
      (->> (.listFiles d)
           (filter #(and (.isFile %) (re-matches #".*_invariant\.clj" (.getName %))))
           (map #(.getPath %))))))

(defn- test-files []
  (->> (concat (actor-test-files) (cross-actor-invariant-files))
       sort
       vec))

(defn- run-suite [path]
  (let [{:keys [out err exit]} (p/sh {:out :string :err :string}
                                     "bb" "--classpath" "20-actors" path)
        combined (str out err)
        ran (some-> (re-find #"Ran (\d+) tests" combined) second parse-long)
        asserts (some-> (re-find #"containing (\d+) assertions" combined) second parse-long)
        fe (re-find #"(\d+) failures, (\d+) errors" combined)
        failures (some-> fe (nth 1) parse-long)
        errors (some-> fe (nth 2) parse-long)
        green? (and (= 0 exit) failures errors (zero? failures) (zero? errors))]
    (cond
      (and green? (or (nil? ran) (zero? ran)))
      {:status :hollow :path path :ran (or ran 0)}
      green?
      {:status :pass :path path :ran ran :asserts (or asserts 0)}
      :else
      {:status :fail :path path :exit exit
       :detail (or (some-> fe first) (last (str/split-lines combined)))})))

(defn -main [& _]
  (let [files (test-files)
        _ (println (format "food/logistics clj test sweep — %d suites across %d actors\n"
                           (count files) (count actors)))
        results (mapv run-suite files)
        by (group-by :status results)
        pass (:pass by) fail (:fail by) hollow (:hollow by)
        tot-tests (reduce + 0 (keep :ran pass))
        tot-asserts (reduce + 0 (keep :asserts pass))]
    (doseq [r fail] (println (format "  FAIL   %s  (%s)" (:path r) (:detail r))))
    (doseq [r hollow] (println (format "  HOLLOW %s  (ran 0 tests — false-green)" (:path r))))
    (println (format "\n%d PASS (%d tests / %d assertions) · %d FAIL · %d HOLLOW"
                     (count pass) tot-tests tot-asserts (count fail) (count hollow)))
    (System/exit (if (and (empty? fail) (empty? hollow)) 0 1))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
