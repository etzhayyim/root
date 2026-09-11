;; etzhayyim.kotoba.metrics — concentration metrics over kotoba query results.
;;
;; The KG-mirror actors (kabuto / keizu / tsumugi / hokorobi …) all route a
;; "取-concentration" lens to redundancy/accountability. With the engine's
;; aggregate queries (etzhayyim.kotoba.query: group-by + sum/count), the
;; concentration math itself is a thin, reusable layer here — actors stop
;; carrying bespoke implementations. Pure functions over group magnitudes
;; (counts or amounts a query already produced); no engine coupling.

(ns etzhayyim.kotoba.metrics)

(defn shares
  "Normalize a seq of non-negative magnitudes into fractions summing to 1.0
   (empty if the total is zero)."
  [magnitudes]
  (let [total (reduce + 0 magnitudes)]
    (if (zero? total) [] (map #(/ % total) magnitudes))))

(defn hhi
  "Herfindahl-Hirschman Index on the 0..10000 scale over a seq of non-negative
   group magnitudes (per-actor counts or amounts). 10000 = monopoly; →0 =
   fragmented. 0.0 for empty / zero-total input.
   HHI = 10000 · Σ sᵢ²  where sᵢ = magnitudeᵢ / Σ magnitude."
  [magnitudes]
  (* 10000.0 (reduce + 0 (map #(* % %) (shares magnitudes)))))

(defn effective-n
  "Effective number of equally-weighted competitors = 1 / Σ sᵢ² (the inverse
   Simpson / inverse-normalized-HHI). A monopoly → 1; N equal players → N.
   0.0 for empty / zero-total input."
  [magnitudes]
  (let [sumsq (reduce + 0 (map #(* % %) (shares magnitudes)))]
    (if (zero? sumsq) 0.0 (/ 1.0 sumsq))))

(defn top-share
  "Largest single group's fraction of the total (0..1); 0.0 if total is zero."
  [magnitudes]
  (let [ss (shares magnitudes)]
    (if (seq ss) (double (apply max ss)) 0.0)))
