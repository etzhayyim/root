(ns noroshi.methods.test-cable-endpoint
  "Tests for the noroshi×watatsuna optical-network resilience join (ADR-2606051600).
  1:1 Clojure port of methods/test_cable_endpoint.py (pytest → clojure.test).

  The Python module gates the whole file with pytestmark skipif(not _SEED.exists()).
  Here the seed-present tests are simply skipped (return) when the watatsuna seed is
  absent; the tmp-seed coverage tests are self-contained."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [noroshi.methods.cable-endpoint :as C]))

#?(:clj
   (def ^:private seed-file
     (-> (java.io.File. *file*) .getParentFile .getParentFile .getParentFile
         (java.io.File. "watatsuna") (java.io.File. "data")
         (java.io.File. "seed-cable-graph.kotoba.edn"))))

#?(:clj (def ^:private seed-present? (.exists seed-file)))

#?(:clj
   (defn- tmp-edn [contents]
     (let [f (java.io.File/createTempFile "noroshi-cable" ".edn")]
       (.deleteOnExit f)
       (spit f contents)
       f)))

;; ── seed-present tests (skipped if the watatsuna seed is absent) ─────────────────
(deftest test-loads-watatsuna-graph
  (when seed-present?
    (let [g (C/load-graph)]
      (is (contains? (get g "cables") "cable.jupiter"))
      (is (some #(str/starts-with? % "station.") (keys (get g "stations"))))
      (is (> (count (get g "links")) 0)))))

(deftest test-lane-sizing-formula
  (is (= (C/lanes-for 250.0 106.25) 2353))
  (is (= (C/lanes-for 0.0 106.25) 1))
  (is (= (C/lanes-for 0.1 106.25) 1)))

(deftest test-chokepoints-ranked-by-lane-demand
  (when seed-present?
    (let [f (C/size-fleet) cps (get f "chokepoints")]
      (is (seq cps))
      (is (every? (fn [i] (>= (get (cps i) "lanes") (get (cps (inc i)) "lanes"))) (range (dec (count cps)))))
      (is (= (get (first cps) "chokepoint") ":luzon-strait")))))

(deftest test-per-cable-endpoint-power-is-realistic
  (when seed-present?
    (let [f (C/size-fleet)]
      (doseq [c (get f "per_cable")]
        (is (and (< 0.0 (get c "energy_kw")) (< (get c "energy_kw") 1000.0)))))))

(deftest test-report-frames-resilience-not-target-list
  (when seed-present?
    (let [txt (C/report)]
      (is (str/includes? (str/lower-case txt) "resilience"))
      (is (or (str/includes? txt "NEVER a target-list") (str/includes? (str/lower-case txt) "never")))
      (is (str/includes? txt ":luzon-strait")))))

;; ── coverage: status filter, missing seed, custom seed ──────────────────────────
(deftest test-missing-seed-raises-friendly-error
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (C/load-graph (java.io.File. (System/getProperty "java.io.tmpdir") "noroshi-nope-xyz.edn")))))

(deftest test-out-of-service-cable-is-skipped
  (let [seed (tmp-edn (str "[{:cable/id \"c.live\" :cable/name \"Live\" :cable/design-capacity-tbps 100.0 "
                           ":cable/status :in-service}\n"
                           " {:cable/id \"c.dead\" :cable/name \"Dead\" :cable/design-capacity-tbps 999.0 "
                           ":cable/status :decommissioned}\n"
                           " {:station/id \"s.a\" :station/name \"A\" :station/chokepoint [:malacca]}\n"
                           " {:cable.link/id \"lk1\" :cable.link/cable \"c.live\" :cable.link/station \"s.a\"}\n"
                           " {:cable.link/id \"lk2\" :cable.link/cable \"c.dead\" :cable.link/station \"s.a\"}]\n"))
        f (C/size-fleet seed)
        names (set (map #(get % "name") (get f "per_cable")))]
    (is (contains? names "Live"))
    (is (not (contains? names "Dead")))))

(deftest test-load-graph-parses-segments
  (when seed-present?
    (is (> (count (get (C/load-graph) "segments")) 0))))

(deftest test-segment-view-present-ranked-and-luzon-top
  (when seed-present?
    (let [f (C/size-fleet) segs (get f "chokepoints_via_segments")]
      (is (seq segs))
      (is (every? (fn [i] (>= (get (segs i) "lanes") (get (segs (inc i)) "lanes"))) (range (dec (count segs)))))
      (is (= (get (first segs) "chokepoint") ":luzon-strait")))))

(deftest test-segment-view-attributes-a-crossing-without-a-tagged-landing
  (let [seed (tmp-edn (str "[{:cable/id \"c.gulf\" :cable/name \"Gulf\" :cable/design-capacity-tbps 100.0 :cable/status :in-service}\n"
                           " {:station/id \"s.plain\" :station/name \"Plain\"}\n"
                           " {:cable.link/id \"lk\" :cable.link/cable \"c.gulf\" :cable.link/station \"s.plain\"}\n"
                           " {:cable.seg/id \"sg\" :cable.seg/cable \"c.gulf\" :cable.seg/traverses [:hormuz]}]\n"))
        f (C/size-fleet seed)
        station-cps (set (map #(get % "chokepoint") (get f "chokepoints")))
        segment-cps (set (map #(get % "chokepoint") (get f "chokepoints_via_segments")))]
    (is (not (contains? station-cps ":hormuz")))
    (is (contains? segment-cps ":hormuz"))))

(deftest test-station-without-chokepoint-contributes-no-chokepoint-row
  (let [seed (tmp-edn (str "[{:cable/id \"c.x\" :cable/name \"X\" :cable/design-capacity-tbps 50.0 :cable/status :in-service}\n"
                           " {:station/id \"s.nocp\" :station/name \"NoCP\"}\n"
                           " {:cable.link/id \"lk\" :cable.link/cable \"c.x\" :cable.link/station \"s.nocp\"}]\n"))
        f (C/size-fleet seed)]
    (is (= (get f "chokepoints") []))
    (is (> (get (get f "by_station_lanes") "s.nocp") 0))))

#?(:clj (defn -main [& _] (run-tests 'noroshi.methods.test-cable-endpoint)))
