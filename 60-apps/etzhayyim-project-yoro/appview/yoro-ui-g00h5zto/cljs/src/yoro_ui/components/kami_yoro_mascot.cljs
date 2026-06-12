(ns yoro-ui.components.kami-yoro-mascot
  "Port of svelte/src/lib/KamiYoroMascot.svelte — YORO mascot with KAMI Engine
   3D (iframe) + SVG fallback.

   Strategy:
   1. Show SVG immediately (no loading spinner)
   2. If WebGPU is available, load iframe with KAMI Engine embed
   3. iframe loads → hide SVG, show 3D
   4. iframe fails/timeout (3s) → keep SVG"
  (:require [reagent.core :as r]))

(defn kami-yoro-mascot
  "Props: {:width px (200) :height px (220) :interactive bool (true) :class str}"
  [_props]
  (let [mounted (r/atom false)
        kami3d-ready (r/atom false)
        tapped (r/atom false)
        blink (r/atom false)
        alive (atom true)
        blink-loop (fn blink-loop []
                     (js/setTimeout
                      (fn []
                        (when @alive
                          (reset! blink true)
                          (js/setTimeout #(when @alive (reset! blink false)) 150)
                          (blink-loop)))
                      (+ 3000 (* 3000 (js/Math.random)))))
        handle-tap (fn [interactive]
                     (when interactive
                       (reset! tapped true)
                       (js/setTimeout #(when @alive (reset! tapped false)) 400)))]
    (r/create-class
     {:display-name "kami-yoro-mascot"

      :component-did-mount
      (fn [_]
        (reset! mounted true)
        (blink-loop)
        ;; Try WebGPU iframe (non-blocking, 3s timeout)
        (try
          (when (and (exists? js/navigator) (.-gpu js/navigator))
            (let [timeout (js/setTimeout (fn [] #_keep-svg) 3000)
                  iframe (.getElementById js/document "kami-yoro-iframe")]
              (when iframe
                (set! (.-onload iframe)
                      (fn []
                        (js/clearTimeout timeout)
                        ;; Give KAMI Engine 1s to init after iframe load
                        (js/setTimeout #(when @alive (reset! kami3d-ready true)) 1000)))
                (set! (.-onerror iframe)
                      (fn [] (js/clearTimeout timeout))))))
          (catch js/Error _ #_keep-svg)))

      :component-will-unmount
      (fn [_] (reset! alive false))

      :reagent-render
      (fn [{:keys [width height interactive class]
            :or {width 200 height 220 interactive true class ""}}]
        [:div {:class (str "relative " class)
               :style {:width width :height height}
               :on-click #(handle-tap interactive)}
         ;; KAMI Engine 3D iframe (hidden until ready)
         (when @mounted
           [:iframe {:id "kami-yoro-iframe"
                     :src "/kami-web/embed.html"
                     :class "absolute inset-0 w-full h-full rounded-2xl border-0"
                     :style {:display (if @kami3d-ready "block" "none")
                             :background "transparent"}
                     :title "YORO 3D"
                     :sandbox "allow-scripts allow-same-origin"
                     :loading "lazy"}])

         ;; SVG Fallback (shown until 3D is ready)
         (when (and (not @kami3d-ready) @mounted)
           [:div {:class "w-full h-full flex items-center justify-center"}
            [:svg {:view-box "0 0 200 240"
                   :class (str "yoro-svg" (when @tapped " yoro-tap"))
                   :style {:width width :height height}
                   :role "img"
                   :aria-label "YORO mascot"}
             [:ellipse {:cx 100 :cy 232 :rx 38 :ry 7 :fill "rgba(0,0,0,0.1)" :class "yoro-shadow"}]
             [:ellipse {:cx 76 :cy 214 :rx 17 :ry 8 :fill "#46A302"}]
             [:ellipse {:cx 124 :cy 214 :rx 17 :ry 8 :fill "#46A302"}]
             [:ellipse {:cx 100 :cy 165 :rx 46 :ry 40 :fill "#58CC02"}]
             [:ellipse {:cx 100 :cy 173 :rx 26 :ry 20 :fill "#8EE000"}]
             [:path {:d "M 54 152 Q 30 158 32 178" :stroke "#46A302" :stroke-width 13 :fill "none" :stroke-linecap "round" :class "yoro-arm-l"}]
             [:circle {:cx 32 :cy 179 :r 8 :fill "#46A302" :class "yoro-arm-l"}]
             [:path {:d "M 146 152 Q 170 158 168 178" :stroke "#46A302" :stroke-width 13 :fill "none" :stroke-linecap "round" :class "yoro-arm-r"}]
             [:circle {:cx 168 :cy 179 :r 8 :fill "#46A302" :class "yoro-arm-r"}]
             [:circle {:cx 100 :cy 102 :r 48 :fill "#58CC02"}]
             (if @blink
               [:<>
                [:line {:x1 65 :y1 98 :x2 90 :y2 98 :stroke "#2a6e00" :stroke-width 3 :stroke-linecap "round"}]
                [:line {:x1 110 :y1 98 :x2 135 :y2 98 :stroke "#2a6e00" :stroke-width 3 :stroke-linecap "round"}]]
               [:<>
                [:ellipse {:cx 78 :cy 96 :rx 17 :ry 17 :fill "white"}]
                [:ellipse {:cx 122 :cy 96 :rx 17 :ry 17 :fill "white"}]
                [:circle {:cx 80 :cy 100 :r 10 :fill "#1CB0F6"}]
                [:circle {:cx 124 :cy 100 :r 10 :fill "#1CB0F6"}]
                [:circle {:cx 80 :cy 100 :r 4.5 :fill "#1A1A2E"}]
                [:circle {:cx 124 :cy 100 :r 4.5 :fill "#1A1A2E"}]
                [:circle {:cx 85 :cy 94 :r 3.5 :fill "white"}]
                [:circle {:cx 129 :cy 94 :r 3.5 :fill "white"}]])
             [:path {:d "M 73 116 Q 100 140 127 116" :stroke "#1A1A1A" :stroke-width 2.5 :fill "white" :stroke-linecap "round"}]
             [:line {:x1 88 :y1 117 :x2 88 :y2 126 :stroke "#1A1A1A" :stroke-width 1.2}]
             [:line {:x1 100 :y1 118 :x2 100 :y2 128 :stroke "#1A1A1A" :stroke-width 1.2}]
             [:line {:x1 112 :y1 117 :x2 112 :y2 126 :stroke "#1A1A1A" :stroke-width 1.2}]
             [:ellipse {:cx 58 :cy 110 :rx 9 :ry 5.5 :fill "#ff9999" :opacity 0.3}]
             [:ellipse {:cx 142 :cy 110 :rx 9 :ry 5.5 :fill "#ff9999" :opacity 0.3}]
             [:ellipse {:cx 100 :cy 62 :rx 36 :ry 9 :fill "#e0e0e0"}]
             [:rect {:x 72 :y 42 :width 56 :height 22 :rx 7 :fill "#ececee"}]
             [:ellipse {:cx 100 :cy 42 :rx 26 :ry 9 :fill "#e0e0e0"}]
             [:rect {:x 82 :y 32 :width 36 :height 13 :rx 5 :fill "#d8d8da"}]
             [:circle {:cx 74 :cy 62 :r 2 :fill "#ccc"}]
             [:circle {:cx 126 :cy 62 :r 2 :fill "#ccc"}]]])])})))
