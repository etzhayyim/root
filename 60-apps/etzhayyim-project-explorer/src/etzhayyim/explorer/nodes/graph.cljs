(ns etzhayyim.explorer.nodes.graph
  "Tiny, dependency-free force layout for the node-distribution mesh
   (ADR-2606201610: 'a tiny in-house sim' — no d3 dependency). Deterministic:
   seeded by node index, no Math.random, so the layout is stable across reloads
   and reproducible (which the repo's no-Date/no-random discipline favours).

   Computes a fixed number of iterations synchronously; the dataset is ~100
   nodes so this is cheap and fine to run in render-prep."
  (:require [clojure.string :as str]))

(def ^:private W 640)
(def ^:private H 480)

(defn- seed-pos
  "Deterministic initial placement on a phyllotactic spiral (golden angle),
   so even disconnected nodes spread out instead of stacking."
  [i n]
  (let [golden 2.399963229728653
        a (* i golden)
        r (* (/ (Math/sqrt (inc i)) (Math/sqrt (max 1 n))) (* 0.42 (min W H)))]
    {:x (+ (/ W 2) (* r (Math/cos a)))
     :y (+ (/ H 2) (* r (Math/sin a)))}))

(defn- clampv [v lo hi] (-> v (max lo) (min hi)))

(defn layout
  "nodes → {id {:x :y :node n}}. Edges are derived from each node's outDeg as a
   light attractive pull toward higher-connected neighbours; with no explicit
   edge list we approximate cohesion by pulling everyone toward the centroid of
   nodes sharing their class, and repelling overlapping pairs."
  [nodes]
  (let [n (count nodes)
        init (into {} (map-indexed (fn [i nd]
                                     [(:id nd) (assoc (seed-pos i n) :node nd)])
                                   nodes))
        iters 80
        repel 1400.0
        center 0.012]
    (loop [pos init, it 0]
      (if (>= it iters)
        pos
        (let [ks (keys pos)
              ;; repulsion (O(n^2) but n≈100, fine)
              forces
              (reduce
               (fn [acc a]
                 (let [{ax :x ay :y} (pos a)]
                   (reduce
                    (fn [acc b]
                      (if (= a b)
                        acc
                        (let [{bx :x by :y} (pos b)
                              dx (- ax bx) dy (- ay by)
                              d2 (max 16.0 (+ (* dx dx) (* dy dy)))
                              f (/ repel d2)]
                          (-> acc
                              (update-in [a :fx] + (* f dx))
                              (update-in [a :fy] + (* f dy))))))
                    acc ks)))
               (into {} (map (fn [k] [k {:fx 0.0 :fy 0.0}]) ks))
               ks)]
          (recur
           (into {}
                 (map (fn [k]
                        (let [{:keys [x y] :as p} (pos k)
                              {:keys [fx fy]} (forces k)
                              ;; pull to center
                              cx (* center (- (/ W 2) x))
                              cy (* center (- (/ H 2) y))
                              nx (clampv (+ x (* 0.5 (+ fx cx)) ) 24 (- W 24))
                              ny (clampv (+ y (* 0.5 (+ fy cy)) ) 24 (- H 24))]
                          [k (assoc p :x nx :y ny)]))
                      ks))
           (inc it)))))))

(def viewbox (str "0 0 " W " " H))

(defn reflex-color [reflex]
  (case (some-> reflex str/lower-case)
    "green" "var(--leaf)"
    "red"   "var(--clay)"
    "absent" "var(--absent)"
    "var(--gold)"))

(defn node-radius [{:keys [score cells]}]
  (let [base (+ 3 (/ (or score 0) 12.0))]
    (min 14 (+ base (* 0.6 (or cells 0))))))
