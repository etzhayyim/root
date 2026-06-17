(ns tatara.methods.test-analyze
  "tatara 鑪 — analyzer tests (ADR-2606171800).

  Covers the aggregate roll-ups (sector concentration / HHI, chokepoint export-dependence,
  country employment rollup, capacity rollup) AND the load-bearing charter invariant: tatara
  carries DISCLOSED AGGREGATE facility figures only — an individual worker is structurally
  unrepresentable (no :worker/* / :person/* attribute anywhere). G4."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]
            [tatara.methods.analyze :as az]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def seed (io/file actor-dir "data" "seed-plant-graph.kotoba.edn"))

(defn load* []
  (let [g (az/classify (az/load-edn seed))]
    [g (az/analyze g)]))

(deftest test-classify-buckets-the-seed
  (let [[g _] (load*)]
    (is (= 22 (count (:plants g))))
    (is (= 6  (count (:hubs g))))
    (is (= 22 (count (:flows g))))))

(deftest test-sector-counts
  (let [[_ a] (load*)]
    (is (= 5 (get-in a [:sector-stats :semiconductor :plants])))
    (is (= 5 (get-in a [:sector-stats :automotive :plants])))
    (is (= 4 (get-in a [:sector-stats :battery :plants])))
    (is (= 3 (get-in a [:sector-stats :steel :plants])))
    (is (= 8 (count (:sector-stats a))))))

(deftest test-aggregate-employment-is-sum-of-disclosed-figures
  (let [[_ a] (load*)]
    ;; disclosed aggregate facility employment, summed — NEVER per-worker
    (is (= 610500 (:global-headcount a)))))

(deftest test-semiconductor-concentration
  (let [[_ a] (load*)
        st (get-in a [:sector-stats :semiconductor])]
    (is (= 0.36 (:hhi st)))           ;; TW 1, KR 2, US 2 → 0.04+0.16+0.16
    (is (= "KR" (:top-country st)))   ;; KR/US tie → lexically-smallest (deterministic)
    (is (= 0.4 (:top-share st)))
    (is (false? (:single-source st))))) ;; 0.4 < 0.6 threshold — honestly NOT flagged

(deftest test-chokepoint-export-dependence
  (let [[_ a] (load*)
        n (fn [cp] (count (get-in a [:choke-plants cp])))]
    (is (= 10 (n :malacca)))
    (is (= 6  (n :luzon-strait)))
    (is (= 4  (n :gibraltar)))
    (is (= 3  (n :suez-red-sea)))
    (is (= 1  (n :panama)))
    ;; malacca is the top export-dependence chokepoint
    (is (= :malacca (first (az/chokes-by-load a))))))

(deftest test-country-employment-rollup
  (let [[_ a] (load*)]
    ;; KR holds 5 charted plants (Samsung, SK hynix, Hyundai, POSCO, HD Hyundai)
    (is (= 5 (get-in a [:country-roll "KR" :plants])))
    (is (= 5 (get-in a [:country-roll "US" :plants])))
    (is (= 4 (get-in a [:country-roll "CN" :plants])))))

(deftest test-capacity-rollup-units-are-per-sector-consistent
  (let [[_ a] (load*)]
    (is (= :wafers-300mm-kpm (get-in a [:sector-capacity :semiconductor :unit])))
    (is (= :vehicles-yr (get-in a [:sector-capacity :automotive :unit])))
    ;; automotive total = 1.4M + 0.5M + 0.78M + 0.95M + 0.4M = 4.03M vehicles/yr
    (is (= 4030000.0 (get-in a [:sector-capacity :automotive :value])))))

(deftest test-no-per-worker-attribute-is-representable  ;; ── load-bearing G4 gate ──
  (let [[g _] (load*)]
    (doseq [p (:plants g)]
      (doseq [k (keys p)]
        (is (not (#{"worker" "person"} (namespace k)))
            (str "forbidden per-individual attribute leaked: " k)))
      ;; the aggregate SIZE is present and is a plain number, not a roster
      (is (number? (:plant/headcount-est p))))))

(deftest test-report-and-datoms-render
  (let [[g a] (load*)
        report (az/render-report g a)
        datoms (az/render-datoms a)]
    (is (re-find #"manufacturing concentration" report))
    (is (re-find #"malacca" report))
    (is (re-find #":concentration/derived true" datoms))
    (is (re-find #":concentration/sector :semiconductor" datoms))))

#?(:clj
   (defn -main [& _]
     (let [{:keys [fail error]} (run-tests 'tatara.methods.test-analyze)]
       (System/exit (if (zero? (+ fail error)) 0 1)))))
