#!/usr/bin/env bb
;; Working Clojure test for methods/ingest.clj (replaces the failed unit_refactor cljc stub).
(ns watatsuna.methods.test-ingest
  "Tests for the watatsuna 綿津綱 TeleGeography-bridge ingester (methods/ingest.clj).

  Guards the G2 (chokepoints only from input + only KNOWN names, never synthesized),
  G5 (offline = :representative), and G7 (live fetch refused without operator gate) invariants
  + the seed-wins dedup merge.

  Run:  bb --classpath 20-actors 20-actors/watatsuna/methods/test_ingest.clj"
  (:require [watatsuna.methods.ingest :as ing]
            [watatsuna.methods.analyze :as a]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- sample []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "ingest" "telegeography-sample.json")))
(defn- seed []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "seed-cable-graph.kotoba.edn")))

(deftest bridge-sample-counts
  (let [{:keys [cables stations links]} (ing/bridge-source (sample))]
    (is (= (count cables) 4))
    (is (= (count stations) 12))
    (is (= (count links) 14))))     ; echo 3 + apricot 4 + smw6 4 + jga-s 3

(deftest station-id-is-country-slugged
  (let [{:keys [stations]} (ing/bridge-source (sample))
        by-name (into {} (map (juxt :station/name identity) stations))]
    (is (= (:station/id (by-name "Changi")) "station.sg.changi"))
    (is (= (:station/id (by-name "Eureka, CA")) "station.us.eureka-ca"))))

(deftest g2-chokepoints-only-known-from-input
  ;; a synthetic source: one known + one fabricated chokepoint → only the known survives
  (let [tmp (java.io.File/createTempFile "watatsuna-ing" ".json")]
    (try
      (spit tmp (str "{\"cables\":[{\"id\":\"x\",\"name\":\"X\",\"landing_point_ids\":[\"p1\"]}],"
                     "\"landing_points\":[{\"id\":\"p1\",\"name\":\"Port One\",\"country\":\"SG\","
                     "\"chokepoints\":[\"malacca\",\"atlantis-fake\"]}]}"))
      (let [{:keys [stations]} (ing/bridge-source tmp)
            st (first stations)]
        (is (= (:station/chokepoint st) ["malacca"]) "fabricated chokepoint dropped (G2)")
        (is (not (some #{"atlantis-fake"} (:station/chokepoint st)))))
      (finally (.delete tmp)))))

(deftest sourcing-is-representative-offline
  (let [{:keys [cables stations links]} (ing/bridge-source (sample))]
    (is (every? #(= (:cable/sourcing %) :representative) cables))
    (is (every? #(= (:station/sourcing %) :representative) stations))
    (is (every? #(= (:cable.link/sourcing %) :representative) links))))

(deftest cable-fields-typed
  (let [{:keys [cables]} (ing/bridge-source (sample))
        echo (first (filter #(= (:cable/name %) "Echo") cables))]
    (is (= (:cable/id echo) "cable.echo"))
    (is (= (:cable/length-km echo) 17184))
    (is (= (:cable/design-capacity-tbps echo) 160.0))
    (is (= (:cable/status echo) :in-service))
    (is (vector? (:cable/owner-consortium echo)))))

(deftest merge-dedups-seed-wins
  (let [seed-recs (a/load-edn (seed))
        {:keys [cables stations links]} (ing/bridge-source (sample))
        bridged (concat cables stations links)
        merged (ing/merge-graph seed-recs bridged)
        ids (map #(some % [:cable/id :station/id :cable.link/id :cable.seg/id :cable.fault/id]) merged)]
    (is (= (count ids) (count (distinct ids))) "no duplicate ids after merge")
    (is (>= (count merged) (count (filter map? seed-recs))) "merge keeps at least the whole seed")))

(deftest g7-live-refused-without-gate
  (is (some? (ing/live-refusal ["--live" "http://x"] nil)) "live without gate is refused")
  (is (clojure.string/includes? (ing/live-refusal ["--live"] nil) "G7/Council-gated"))
  ;; even WITH a gate token it is an R0 scaffold (still refused)
  (is (clojure.string/includes? (ing/live-refusal ["--live"] "tok") "R0 scaffold"))
  ;; offline (no --live) is NOT refused
  (is (nil? (ing/live-refusal [] nil))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'watatsuna.methods.test-ingest)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
