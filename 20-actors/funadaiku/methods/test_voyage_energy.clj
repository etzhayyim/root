#!/usr/bin/env bb
;; Working Clojure port of methods/test_voyage_energy.py — the zero-emission invariant suite.
(ns funadaiku.methods.test-voyage-energy
  "funadaiku voyage_energy — zero-emission invariant + model coverage (ADR-2606013400).

  The voyage energy model is the EMPIRICAL backing for funadaiku's constitutional
  zero-emission powertrain (G13/N5: wind + solar + hydrogen, NO fossil engine). These lock
  the invariants that must never silently drift:
    - fossil share is exactly 0 (no fossil engine, ever)
    - the only sources are wind-assist + solar + hydrogen fuel-cell, summing to ~1.0
    - a positive green-H2 demand + a non-trivial battery harbour window
    - shaft power obeys the Admiralty law (∝ speed^3)
    - report()/to-edn() emit non-empty serializations (smoke)

  Run:  bb --classpath 20-actors 20-actors/funadaiku/methods/test_voyage_energy.clj"
  (:require [funadaiku.methods.voyage-energy :as ve]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(deftest no-fossil-engine
  (let [r (ve/simulate ve/default-vessel ve/default-voyage)]
    (is (false? (:fossil-engine r)) "G13/N5: a fossil engine must never appear")
    (is (not (contains? (:shares r) :fossil)) "no fossil energy share may exist")))

(deftest energy-shares-are-renewable-and-sum-to-one
  (let [r (ve/simulate ve/default-vessel ve/default-voyage)
        shares (:shares r)]
    (is (= (set (keys shares)) #{:wind-assist :solar :hydrogen-fuelcell}))
    (is (< (Math/abs (- (reduce + (vals shares)) 1.0)) 1e-6)
        "renewable+H2 shares must cover 100% of demand")
    (is (every? #(>= % 0.0) (vals shares)))))

(deftest positive-hydrogen-demand-and-battery-window
  (let [r (ve/simulate ve/default-vessel ve/default-voyage)
        s (:shares r)]
    (is (> (:h2-kg r) 0) "a cargo-scale coastal voyage needs green-H2 (H2 is the prime mover)")
    (is (> (:battery-harbour-minutes r) 0))
    ;; hydrogen is the dominant single source at cargo scale (the survey conclusion)
    (is (> (:hydrogen-fuelcell s) (:wind-assist s)))
    (is (> (:hydrogen-fuelcell s) (:solar s)))))

(deftest shaft-power-follows-admiralty-cube-law
  (let [base ve/default-vessel
        faster (assoc base :service-speed-kn (* (:service-speed-kn base) 2))
        p1 (ve/shaft-power-kw base)
        p2 (ve/shaft-power-kw faster)]
    ;; P ∝ V^3 → doubling speed ≈ 8× shaft power
    (is (< (Math/abs (- (/ p2 p1) 8.0)) 0.05) "Admiralty cube law violated")))

(deftest higher-demand-raises-hydrogen
  (let [short (ve/simulate ve/default-vessel ve/default-voyage)
        longer (ve/simulate ve/default-vessel
                            (assoc ve/default-voyage
                                   :distance-nm (* (:distance-nm ve/default-voyage) 3)))]
    (is (> (:h2-kg longer) (:h2-kg short)))))

(deftest serializations-nonempty
  (let [v ve/default-vessel voy ve/default-voyage
        r (ve/simulate v voy)
        edn (ve/to-edn v voy r)
        rep (ve/report v voy r)]
    (is (and (string? edn) (seq (.trim edn))))
    (is (and (string? rep) (seq (.trim rep))))))

(deftest main-writes-report-and-edn-artifacts
  (ve/main)
  (let [out (io/file (actor-root) "out")
        md (io/file out "voyage-energy-report.md")
        edn (io/file out "voyage-energy.kotoba.edn")]
    (is (and (.isFile md) (seq (.trim (slurp md)))))
    (is (and (.isFile edn) (str/includes? (slurp edn) "fossil-engine false")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'funadaiku.methods.test-voyage-energy)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
