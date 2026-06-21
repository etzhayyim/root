(ns etzhayyim.explorer.organism.bonsai
  "Tree-of-Life bonsai renderer (ADR-2606201610). Reagent/SVG port of the
   etzhayyim-organism-viz bonsai.py geometry: a central trunk, 10 branches (the
   constitutional axes) radiating across the upper arc, leaves per axis score,
   roots = LANDS/MEMBERS. Health colours the branch & leaves; it is a band, not
   a target, so we colour by 'in healthy range', not 'near a goal'."
  (:require [clojure.string :as str]))

(def ^:private W 560)
(def ^:private H 460)
(def ^:private cx (/ W 2))
(def ^:private cy 300)             ; trunk top / branch origin
(def ^:private span-deg 120.0)     ; branches fan from -150° to -30°
(def ^:private start-deg -150.0)

(defn- deg->rad [d] (* d (/ Math/PI 180.0)))

(defn- branch-color [score]
  (cond
    (nil? score) "var(--absent)"
    (>= score 8) "var(--leaf)"
    (>= score 5) "var(--gold)"
    :else "var(--clay)"))

(defn- branch [{:keys [en ja score]} i n]
  (let [t (if (<= n 1) 0.5 (/ i (dec n)))
        ang (deg->rad (+ start-deg (* span-deg t)))
        len (+ 120 (* 8 (or score 0)))
        tipx (+ cx (* len (Math/cos ang)))
        tipy (+ cy (* len (Math/sin ang)))
        col (branch-color score)
        left? (< tipx cx)
        leaves (when score (range score))]
    [:g {:key (str "br-" i)}
     ;; branch limb
     [:line {:x1 cx :y1 cy :x2 tipx :y2 tipy
             :stroke col
             :stroke-width (+ 1.5 (/ (or score 0) 3.0))
             :stroke-linecap "round"
             :opacity 0.9}]
     ;; leaves along the outer half of the limb
     (for [j leaves]
       (let [lt (/ (+ j 1) (+ score 1))
             r (* len (+ 0.55 (* 0.45 lt)))
             lx (+ cx (* r (Math/cos ang)))
             ly (+ cy (* r (Math/sin ang)))]
         [:circle {:key (str "lf-" i "-" j) :cx lx :cy ly :r 3.4 :fill col :opacity 0.85}]))
     ;; label
     [:text {:x (+ tipx (if left? -7 7)) :y tipy
             :text-anchor (if left? "end" "start")
             :dominant-baseline "middle"
             :font-size 11 :fill "var(--ink)"}
      (str en " " (if score (str score "/10") "—"))
      [:tspan {:dx (if left? -4 4) :font-size 9 :fill "var(--ink-soft)"} ja]]]))

(defn tree
  "axis-scores → SVG hiccup. `roots` is an optional {:lands n :members n} caption."
  [axis-scores & [{:keys [lands members]}]]
  (let [n (count axis-scores)]
    [:svg.bonsai {:viewBox (str "0 0 " W " " H) :role "img"
                  :aria-label "organism tree of life"}
     ;; ground line
     [:line {:x1 60 :y1 (+ cy 96) :x2 (- W 60) :y2 (+ cy 96)
             :stroke "var(--line)" :stroke-width 1}]
     ;; roots (downward, faint)
     (for [k (range 5)]
       (let [ang (deg->rad (+ 60 (* 15 k)))
             rx (+ cx (* 70 (Math/cos ang)))
             ry (+ cy 96 (* 40 (Math/sin ang)))]
         [:line {:key (str "rt-" k) :x1 cx :y1 (+ cy 90) :x2 rx :y2 ry
                 :stroke "var(--line)" :stroke-width 1.5 :opacity 0.7}]))
     ;; trunk (= charter)
     [:path {:d (str "M " (- cx 10) " " (+ cy 92)
                     " L " (- cx 4) " " cy
                     " L " (+ cx 4) " " cy
                     " L " (+ cx 10) " " (+ cy 92) " Z")
             :fill "var(--ink)" :opacity 0.82}]
     ;; branches
     (map-indexed (fn [i a] (branch a i n)) axis-scores)
     ;; roots caption
     [:text {:x cx :y (+ cy 124) :text-anchor "middle"
             :font-size 10.5 :fill "var(--ink-soft)"}
      (str "roots · " (or lands "—") " lands · " (or members "—") " members")]]))
