#!/usr/bin/env bb
;; Working Clojure port of methods/last_mile.py (parity-tested mirror of the todoke-route Rust core).
(ns todoke.methods.last-mile
  "last_mile — the todoke-route core (ADR-2606042300): last-mile stop sequencing (NN + 2-opt) +
  the SAE-L4 sidewalk-ODD safety envelope, plus courier-liberation sizing. A faithful clj mirror of
  methods/last_mile.py / the Rust `todoke-route` crate — same per-zone caps, NN/2-opt order, and
  G7 refusals (the parity test pins the identical visiting order).

  G7: the envelope REFUSES (raises) out-of-ODD zone / over-speed / SAE>4 — never silently clamps.

  Run:  bb --classpath 20-actors 20-actors/todoke/methods/last_mile.clj"
  (:require [clojure.string :as str]))

(def sae-level-ceiling 4)  ; N2: Level 5 is a non-goal

;; per-zone speed caps in m/s (road = nil → not in the todoke ODD, N2)
(def zone-speed-cap-mps
  {"sidewalk" 1.8 "crosswalk" 1.4 "doorpath" 1.0 "bikelane" 4.2 "road" nil})

(defn envelope-violation [msg] (throw (ex-info msg {:type :envelope-violation})))
(defn envelope-violation? [e]
  (and (instance? clojure.lang.ExceptionInfo e) (= :envelope-violation (:type (ex-data e)))))

(defn stop [id x y zone] {:id id :x (double x) :y (double y) :zone zone})
(defn- dist [a b] (Math/hypot (- (:x a) (:x b)) (- (:y a) (:y b))))

(defn- check-envelope [stops sae-level commanded-mps]
  (when (> sae-level sae-level-ceiling)
    (envelope-violation (str "G7: SAE level " sae-level " exceeds ceiling " sae-level-ceiling " (N2)")))
  (doseq [s stops]
    (let [cap (get zone-speed-cap-mps (:zone s) ::missing)]
      (when (or (= cap ::missing) (nil? cap))
        (envelope-violation (str "G7: stop " (:id s) " zone " (pr-str (:zone s)) " outside todoke ODD (N2)")))
      (when (> commanded-mps cap)
        (envelope-violation (str "G7: commanded " commanded-mps " m/s exceeds " (:zone s)
                                 " cap " cap " m/s at stop " (:id s)))))))

(defn- nearest-neighbour [stops]
  (let [n (count stops)]
    (loop [visited #{0} tour [0] cur 0]
      (if (= (count tour) n)
        tour
        (let [best (first
                    (reduce (fn [[best best-d] j]
                              (if (visited j)
                                [best best-d]
                                (let [d (dist (stops cur) (stops j))]
                                  (if (or (< d (- best-d 1e-12))
                                          (and (<= d (+ best-d 1e-12)) (or (nil? best) (< j best))))
                                    [j d] [best best-d]))))
                            [nil ##Inf] (range n)))]
          (recur (conj visited best) (conj tour best) best))))))

(defn- reverse-segment [tour i k]
  (vec (concat (subvec tour 0 i) (reverse (subvec tour i (inc k))) (subvec tour (inc k)))))

(defn- two-opt [seed stops]
  (let [n (count seed)]
    (if (< n 4)
      seed
      (loop [tour (vec seed)]
        (let [improved
              (reduce (fn [t i]
                        (reduce (fn [t k]
                                  (let [a (stops (t (dec i))) b (stops (t i)) c (stops (t k))
                                        d-next (when (< (inc k) n) (stops (t (inc k))))
                                        before (+ (dist a b) (if d-next (dist c d-next) 0.0))
                                        after (+ (dist a c) (if d-next (dist b d-next) 0.0))]
                                    (if (< (+ after 1e-9) before) (reverse-segment t i k) t)))
                                t (range (inc i) n)))
                      tour (range 1 (dec n)))]
          (if (= improved tour) tour (recur improved)))))))

(defn plan-last-mile
  "Return [order-of-ids length-m] for a safety-validated last-mile path (stops[0] = depot/drop
  curb; open path). Raises (envelope-violation) if the run would break the envelope (G7)."
  [stops & {:keys [sae-level commanded-mps] :or {sae-level 4 commanded-mps 1.5}}]
  (when (empty? stops) (envelope-violation "G7: no stops to route"))
  (check-envelope stops sae-level commanded-mps)
  (let [stops (vec stops)
        seq* (two-opt (nearest-neighbour stops) stops)
        length (reduce + 0.0 (map (fn [i] (dist (stops (seq* i)) (stops (seq* (inc i)))))
                                  (range (dec (count seq*)))))]
    [(mapv #(:id (stops %)) seq*) length]))

;; ── labour-liberation sizing (mission + G2 coupling) ──────────────────────────
(defn courier-freed-hours [headcount hours-per-worker-yr automation-fraction]
  (* (double headcount) (double hours-per-worker-yr) (double automation-fraction)))

(defn displacement-cohort-size [headcount automation-fraction]
  (long (Math/round (* (double headcount) (double automation-fraction)))))

(defn main [& _]
  (let [head 1.9e7
        fh (courier-freed-hours head 2200 0.30)]
    (println (format "todoke illustrative: automating 30%% of last-mile stops frees %.1fB courier-hours/yr; cohort ≈ %.1fM roles."
                     (/ fh 1e9) (/ (displacement-cohort-size head 0.30) 1e6)))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
