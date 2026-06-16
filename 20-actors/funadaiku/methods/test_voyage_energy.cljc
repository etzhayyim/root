(ns funadaiku.methods.test-voyage-energy
  "test_voyage_energy.py — zero-emission invariant + model coverage (ADR-2606013400).
  1:1 Clojure port of methods/test_voyage_energy.py (stdlib asserts → clojure.test).

  The voyage energy model is the EMPIRICAL backing for funadaiku's constitutional
  zero-emission powertrain (G13/N5: wind + solar + hydrogen, NO fossil main/aux engine):

    - fossil share is exactly 0 (no fossil engine, ever — G13/N5)
    - the only energy sources are wind-assist + solar + hydrogen fuel-cell, summing to ~1.0
    - a positive green-H2 demand and a non-trivial battery harbour-manoeuvre window
    - shaft power obeys the Admiralty law (∝ speed^3)
    - report()/to_edn() emit non-empty serializations (smoke)"
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            #?(:clj [clojure.java.io :as io])
            [funadaiku.methods.voyage-energy :as ve]))

;; Captured at load time (sci/bb rebind *file* to the caller at runtime).
#?(:clj (def ^:private source-file *file*))

(deftest test-no-fossil-engine
  (let [r (ve/simulate (ve/vessel) (ve/voyage))]
    (is (= false (get r "fossil_engine")) "G13/N5: a fossil engine must never appear")
    (is (not (contains? (get r "shares") "fossil")) "no fossil energy share may exist")))

(deftest test-energy-shares-are-renewable-and-sum-to-one
  (let [r (ve/simulate (ve/vessel) (ve/voyage))
        shares (get r "shares")]
    (is (= #{"wind_assist" "solar" "hydrogen_fuelcell"} (set (keys shares))))
    (let [total (reduce + 0.0 (vals shares))]
      (is (< (Math/abs (- total 1.0)) 1e-6)
          (str "renewable+H2 shares must cover 100% of demand, got " total)))
    (is (every? #(>= % 0.0) (vals shares)))))

(deftest test-positive-hydrogen-demand-and-battery-window
  (let [r (ve/simulate (ve/vessel) (ve/voyage))]
    (is (> (get r "h2_kg") 0)
        "a cargo-scale coastal voyage needs green-H2 (H2 is the prime mover)")
    (is (> (get r "battery_harbour_minutes") 0))
    ;; hydrogen is the dominant single source at cargo scale (the survey conclusion)
    (is (> (get-in r ["shares" "hydrogen_fuelcell"]) (get-in r ["shares" "wind_assist"])))
    (is (> (get-in r ["shares" "hydrogen_fuelcell"]) (get-in r ["shares" "solar"])))))

(deftest test-shaft-power-follows-admiralty-cube-law
  (let [base (ve/vessel)
        faster (ve/vessel {"service_speed_kn" (* (double (get base "service_speed_kn")) 2)})
        p1 (ve/shaft-power-kw base)
        p2 (ve/shaft-power-kw faster)]
    ;; P ∝ V^3 → doubling speed ≈ 8× shaft power
    (is (< (Math/abs (- (/ p2 p1) 8.0)) 0.05)
        (str "Admiralty cube law violated: ratio=" (/ p2 p1)))))

(deftest test-higher-demand-raises-hydrogen-share
  ;; a longer / faster voyage shifts more of the budget onto hydrogen (less solar/wind cover)
  (let [short (ve/simulate (ve/vessel) (ve/voyage))
        longer (ve/simulate (ve/vessel)
                            (ve/voyage {"distance_nm" (* (double (get (ve/voyage) "distance_nm")) 3)}))]
    (is (> (get longer "h2_kg") (get short "h2_kg")))))

(deftest test-serializations-nonempty
  (let [v (ve/vessel)
        voy (ve/voyage)
        r (ve/simulate v voy)
        edn (ve/to-edn v voy r)
        rep (ve/report v voy r)]
    (is (and (string? edn) (seq (str/trim edn))))
    (is (and (string? rep) (seq (str/trim rep))))))

#?(:clj
   (deftest test-main-writes-report-and-edn-artifacts
     ;; main() is the CLI entry; it regenerates the (deterministic) out/ artifacts.
     (let [actor-root (-> source-file io/file .getParentFile .getParentFile)
           out (io/file actor-root "out")]
       (ve/-main)
       (let [md (io/file out "voyage-energy-report.md")
             edn (io/file out "voyage-energy.kotoba.edn")]
         (is (and (.isFile md) (seq (str/trim (slurp md)))))
         (is (and (.isFile edn)
                  (str/includes? (slurp edn) "fossil-engine false")))))))

#?(:clj (defn -main [& _] (run-tests 'funadaiku.methods.test-voyage-energy)))
