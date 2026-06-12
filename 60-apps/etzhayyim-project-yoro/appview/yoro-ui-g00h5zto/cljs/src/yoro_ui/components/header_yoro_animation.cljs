(ns yoro-ui.components.header-yoro-animation
  "Port of svelte/src/lib/components/HeaderYoroAnimation.svelte —
   tiny yoro-kun living in the header. 8 patterns rotating every 6-10s,
   blink loop, click cycles to the next pattern."
  (:require [reagent.core :as r]))

(def patterns [:peek-left :peek-right :swing :sleep :bounce :roll :dance :hang])

(defn- std-eyes
  "Shared eye block. blink lines at row y; open eyes white/pupil/inner stack.
   dx shifts the whole block right (dance uses dx 2). glint? adds the small
   white highlight circles (peek/hang variants)."
  [blinking? {:keys [y dx glint?] :or {dx 0 glint? false}}]
  (if blinking?
    [:<>
     [:line {:x1 (+ 8 dx) :y1 y :x2 (+ 12 dx) :y2 y :stroke "#2a6e00" :stroke-width 1.5 :stroke-linecap "round"}]
     [:line {:x1 (+ 16 dx) :y1 y :x2 (+ 20 dx) :y2 y :stroke "#2a6e00" :stroke-width 1.5 :stroke-linecap "round"}]]
    [:<>
     [:ellipse {:cx (+ 10 dx) :cy (dec y) :rx 3.5 :ry 3.5 :fill "white"}]
     [:ellipse {:cx (+ 18 dx) :cy (dec y) :rx 3.5 :ry 3.5 :fill "white"}]
     [:circle {:cx (+ 11 dx) :cy y :r 2 :fill "#1CB0F6"}]
     [:circle {:cx (+ 19 dx) :cy y :r 2 :fill "#1CB0F6"}]
     [:circle {:cx (+ 11 dx) :cy y :r 0.8 :fill "#1A1A2E"}]
     [:circle {:cx (+ 19 dx) :cy y :r 0.8 :fill "#1A1A2E"}]
     (when glint?
       [:<>
        [:circle {:cx (+ 12 dx) :cy (- y 1.5) :r 1 :fill "white"}]
        [:circle {:cx (+ 20 dx) :cy (- y 1.5) :r 1 :fill "white"}]])]))

(defn- cheeks [lx rx y]
  [:<>
   [:ellipse {:cx lx :cy y :rx 2 :ry 1.5 :fill "#ff9999" :opacity 0.3}]
   [:ellipse {:cx rx :cy y :rx 2 :ry 1.5 :fill "#ff9999" :opacity 0.3}]])

(defn- peek-svg [blinking? side]
  [:svg {:view-box "0 0 28 28"
         :class (str "yoro-mini " (if (= side :left) "yoro-peek-left" "yoro-peek-right"))
         :xmlns "http://www.w3.org/2000/svg"}
   [:circle {:cx 14 :cy 12 :r 10 :fill "#58CC02"}]
   (std-eyes blinking? {:y 11 :glint? true})
   [:path {:d "M 9 16 Q 14 21 19 16" :stroke "#1A1A1A" :stroke-width 1.2 :fill "white" :stroke-linecap "round"}]
   (cheeks 6 22 14)
   ;; tiny arm waving
   (if (= side :left)
     [:<>
      [:path {:d "M 3 16 Q 0 12 2 8" :stroke "#46A302" :stroke-width 2.5 :fill "none" :stroke-linecap "round" :class "wave-arm"}]
      [:circle {:cx 2 :cy 8 :r 1.5 :fill "#46A302" :class "wave-arm"}]]
     [:<>
      [:path {:d "M 25 16 Q 28 12 26 8" :stroke "#46A302" :stroke-width 2.5 :fill "none" :stroke-linecap "round" :class "wave-arm-r"}]
      [:circle {:cx 26 :cy 8 :r 1.5 :fill "#46A302" :class "wave-arm-r"}]])])

(defn- swing-svg [blinking?]
  [:svg {:view-box "0 0 28 36" :class "yoro-mini yoro-swing" :xmlns "http://www.w3.org/2000/svg"}
   ;; arms gripping top
   [:path {:d "M 10 2 L 10 6" :stroke "#46A302" :stroke-width 2.5 :stroke-linecap "round"}]
   [:path {:d "M 18 2 L 18 6" :stroke "#46A302" :stroke-width 2.5 :stroke-linecap "round"}]
   [:circle {:cx 10 :cy 2 :r 1.5 :fill "#46A302"}]
   [:circle {:cx 18 :cy 2 :r 1.5 :fill "#46A302"}]
   [:circle {:cx 14 :cy 16 :r 10 :fill "#58CC02"}]
   (std-eyes blinking? {:y 15})
   [:path {:d "M 9 20 Q 14 24 19 20" :stroke "#1A1A1A" :stroke-width 1.2 :fill "white" :stroke-linecap "round"}]
   (cheeks 6 22 18)
   ;; feet dangling
   [:ellipse {:cx 10 :cy 27 :rx 3 :ry 2 :fill "#46A302" :class "dangle-l"}]
   [:ellipse {:cx 18 :cy 27 :rx 3 :ry 2 :fill "#46A302" :class "dangle-r"}]])

(defn- sleep-svg []
  [:svg {:view-box "0 0 36 28" :class "yoro-mini yoro-sleep" :xmlns "http://www.w3.org/2000/svg"}
   [:circle {:cx 14 :cy 14 :r 10 :fill "#58CC02"}]
   ;; closed eyes (sleeping)
   [:path {:d "M 7 12 Q 10 14 13 12" :stroke "#2a6e00" :stroke-width 1.5 :fill "none" :stroke-linecap "round"}]
   [:path {:d "M 15 12 Q 18 14 21 12" :stroke "#2a6e00" :stroke-width 1.5 :fill "none" :stroke-linecap "round"}]
   ;; little smile
   [:path {:d "M 10 18 Q 14 20 18 18" :stroke "#1A1A1A" :stroke-width 1 :fill "none" :stroke-linecap "round"}]
   (cheeks 6 22 16)
   ;; Zzz
   [:text {:x 26 :y 10 :class "zzz zzz-1" :fill "var(--gv2-text-muted, #666)" :font-size 6 :font-weight "bold"} "z"]
   [:text {:x 30 :y 6 :class "zzz zzz-2" :fill "var(--gv2-text-muted, #666)" :font-size 5 :font-weight "bold"} "z"]
   [:text {:x 33 :y 3 :class "zzz zzz-3" :fill "var(--gv2-text-muted, #666)" :font-size 4 :font-weight "bold"} "z"]
   ;; body lying flat
   [:ellipse {:cx 14 :cy 24 :rx 8 :ry 3 :fill "#46A302"}]])

(defn- bounce-svg [blinking?]
  [:svg {:view-box "0 0 28 28" :class "yoro-mini yoro-bounce-anim" :xmlns "http://www.w3.org/2000/svg"}
   [:circle {:cx 14 :cy 12 :r 10 :fill "#58CC02"}]
   (std-eyes blinking? {:y 11})
   ;; open excited mouth
   [:ellipse {:cx 14 :cy 17 :rx 4 :ry 3 :fill "#1A1A1A"}]
   [:ellipse {:cx 14 :cy 17 :rx 2.5 :ry 2 :fill "#ff6b6b"}]
   (cheeks 6 22 14)
   ;; feet
   [:ellipse {:cx 10 :cy 23 :rx 3.5 :ry 2 :fill "#46A302"}]
   [:ellipse {:cx 18 :cy 23 :rx 3.5 :ry 2 :fill "#46A302"}]])

(defn- roll-svg [blinking?]
  [:svg {:view-box "0 0 28 28" :class "yoro-mini yoro-roll" :xmlns "http://www.w3.org/2000/svg"}
   [:g {:class "roll-body"}
    [:circle {:cx 14 :cy 14 :r 10 :fill "#58CC02"}]
    (if blinking?
      [:<>
       [:line {:x1 8 :y1 13 :x2 12 :y2 13 :stroke "#2a6e00" :stroke-width 1.5 :stroke-linecap "round"}]
       [:line {:x1 16 :y1 13 :x2 20 :y2 13 :stroke "#2a6e00" :stroke-width 1.5 :stroke-linecap "round"}]]
      [:<>
       [:ellipse {:cx 10 :cy 12 :rx 3.5 :ry 3.5 :fill "white"}]
       [:ellipse {:cx 18 :cy 12 :rx 3.5 :ry 3.5 :fill "white"}]
       ;; dizzy spiral eyes
       [:circle {:cx 10 :cy 12 :r 2.5 :fill "none" :stroke "#1CB0F6" :stroke-width 1}]
       [:circle {:cx 18 :cy 12 :r 2.5 :fill "none" :stroke "#1CB0F6" :stroke-width 1}]
       [:circle {:cx 10 :cy 12 :r 1 :fill "#1CB0F6"}]
       [:circle {:cx 18 :cy 12 :r 1 :fill "#1CB0F6"}]])
    [:path {:d "M 10 18 Q 14 20 18 18" :stroke "#1A1A1A" :stroke-width 1 :fill "none" :stroke-linecap "round"}]]])

(defn- dance-svg [blinking?]
  [:svg {:view-box "0 0 32 30" :class "yoro-mini yoro-dance" :xmlns "http://www.w3.org/2000/svg"}
   [:circle {:cx 16 :cy 12 :r 10 :fill "#58CC02"}]
   (std-eyes blinking? {:y 11 :dx 2})
   ;; happy open mouth
   [:path {:d "M 11 16 Q 16 21 21 16" :stroke "#1A1A1A" :stroke-width 1.2 :fill "white" :stroke-linecap "round"}]
   (cheeks 8 24 14)
   ;; arms up dance pose
   [:path {:d "M 6 14 Q 2 8 5 4" :stroke "#46A302" :stroke-width 2.5 :fill "none" :stroke-linecap "round" :class "dance-arm-l"}]
   [:circle {:cx 5 :cy 4 :r 1.5 :fill "#46A302" :class "dance-arm-l"}]
   [:path {:d "M 26 14 Q 30 8 27 4" :stroke "#46A302" :stroke-width 2.5 :fill "none" :stroke-linecap "round" :class "dance-arm-r"}]
   [:circle {:cx 27 :cy 4 :r 1.5 :fill "#46A302" :class "dance-arm-r"}]
   ;; feet
   [:ellipse {:cx 12 :cy 24 :rx 3.5 :ry 2 :fill "#46A302" :class "dance-foot-l"}]
   [:ellipse {:cx 20 :cy 24 :rx 3.5 :ry 2 :fill "#46A302" :class "dance-foot-r"}]
   ;; music notes
   [:text {:x 1 :y 6 :class "music-note note-1" :fill "var(--gv2-accent, #1CB0F6)" :font-size 5} "♫"]
   [:text {:x 27 :y 4 :class "music-note note-2" :fill "var(--gv2-accent, #1CB0F6)" :font-size 4} "♪"]])

(defn- hang-svg [blinking?]
  [:svg {:view-box "0 0 28 34" :class "yoro-mini yoro-hang" :xmlns "http://www.w3.org/2000/svg"}
   ;; arms gripping top edge
   [:rect {:x 8 :y 0 :width 12 :height 3 :rx 1.5 :fill "#46A302"}]
   [:path {:d "M 10 3 L 10 8" :stroke "#46A302" :stroke-width 2.5 :stroke-linecap "round"}]
   [:path {:d "M 18 3 L 18 8" :stroke "#46A302" :stroke-width 2.5 :stroke-linecap "round"}]
   [:circle {:cx 14 :cy 18 :r 10 :fill "#58CC02"}]
   (std-eyes blinking? {:y 17 :glint? true})
   [:path {:d "M 9 22 Q 14 26 19 22" :stroke "#1A1A1A" :stroke-width 1.2 :fill "white" :stroke-linecap "round"}]
   (cheeks 6 22 20)
   ;; dangling feet
   [:ellipse {:cx 10 :cy 30 :rx 3.5 :ry 2 :fill "#46A302" :class "dangle-l"}]
   [:ellipse {:cx 18 :cy 30 :rx 3.5 :ry 2 :fill "#46A302" :class "dangle-r"}]])

(defn header-yoro-animation
  "Props: {:class extra classes}"
  [_props]
  (let [pattern (r/atom :peek-left)
        blinking (r/atom false)
        visible (r/atom false)
        intervals (atom [])
        handle-click
        (fn []
          (let [idx (.indexOf patterns @pattern)]
            (reset! pattern (nth patterns (mod (inc idx) (count patterns))))))]
    (r/create-class
     {:display-name "header-yoro-animation"

      :component-did-mount
      (fn [_]
        (reset! visible true)
        ;; Pick random initial pattern
        (reset! pattern (nth patterns (rand-int (count patterns))))
        (let [rotate-iv (js/setInterval
                         #(reset! pattern (nth patterns (rand-int (count patterns))))
                         (+ 6000 (* 4000 (js/Math.random))))
              blink-iv (js/setInterval
                        (fn []
                          (when-not (= @pattern :sleep)
                            (reset! blinking true)
                            (js/setTimeout (fn [] (reset! blinking false)) 150)))
                        (+ 2800 (* 2000 (js/Math.random))))]
          (reset! intervals [rotate-iv blink-iv])))

      :component-will-unmount
      (fn [_]
        (doseq [iv @intervals] (js/clearInterval iv))
        (reset! intervals []))

      :reagent-render
      (fn [{:keys [class] :or {class ""}}]
        (when @visible
          (let [b @blinking]
            [:div {:class (str "header-yoro-wrap " class)
                   :on-click handle-click
                   :role "img"
                   :aria-label "yoro-kun animation"}
             (case @pattern
               :peek-left  (peek-svg b :left)
               :peek-right (peek-svg b :right)
               :swing      (swing-svg b)
               :sleep      (sleep-svg)
               :bounce     (bounce-svg b)
               :roll       (roll-svg b)
               :dance      (dance-svg b)
               :hang       (hang-svg b)
               (peek-svg b :left))])))})))
