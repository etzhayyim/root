(ns yoro-ui.components.brainrot-mascot
  "Port of svelte/src/lib/components/BrainrotMascot.svelte"
  (:require [reagent.core :as r]))

(def phrases-by-char
  {:yoro    ["rizz 全開！💅" "nuh uh 🚫" "no cap 🔥" "slay ✨" "W しか出ない 🏆" "bussin fr fr 🍗"]
   :skibidi ["skibidi dop dop 🚽" "toilet sigma 🗿" "bop bop yes yes 🎵" "Ohio final boss 💀"]
   :sigma   ["grindset only 💪" "stay on the path 🐺" "no distractions 🧠" "lone wolf 🌙" "mog or be mogged 😤"]
   :ohio    ["only in Ohio 💀" "Ohio ahh moment 🌽" "least weird Ohio day 🤡" "Ohio is NOT real 🌪️"]
   :rizz    ["W rizz 💅" "unspoken rizz ✨" "rizz god activated 👑" "rizzler on duty 🫡"]
   :gyatt   ["GYATT 👀" "lord have mercy 🙏" "bro is down bad 💀" "respectfully 🫣"]})

(def palette
  {:yoro    {:body "#58CC02" :belly "#8EE000" :limb "#46A302" :pupil "#1CB0F6" :hat "#e0e0e0"}
   :skibidi {:body "#1CB0F6" :belly "#5CC8F8" :limb "#0E87BF" :pupil "#FF6B9D" :hat "#f0f0f0"}
   :sigma   {:body "#6C63FF" :belly "#9B95FF" :limb "#4F46E5" :pupil "#FFD700" :hat "#2d2d2d"}
   :ohio    {:body "#FF9500" :belly "#FFB84D" :limb "#CC7700" :pupil "#58CC02" :hat "#8B4513"}
   :rizz    {:body "#FF6B9D" :belly "#FF9EC1" :limb "#D44D7A" :pupil "#A855F7" :hat "#FFD700"}
   :gyatt   {:body "#A855F7" :belly "#C084FC" :limb "#7E22CE" :pupil "#FF6B9D" :hat "#1CB0F6"}})

(def char-names
  {:yoro "YORO" :skibidi "Skibidi" :sigma "Sigma" :ohio "Ohio" :rizz "Rizz" :gyatt "Gyatt"})

(defn- hat [character c]
  (case character
    (:yoro :skibidi)
    [:g
     [:ellipse {:cx 50 :cy 22 :rx 26 :ry 8 :fill (:hat c)}]
     [:rect {:x 38 :y 10 :width 24 :height 14 :rx 4 :fill "#f0f0f0"}]
     [:ellipse {:cx 50 :cy 10 :rx 13 :ry 5 :fill (:hat c)}]
     [:rect {:x 44 :y 6 :width 12 :height 6 :rx 3 :fill "#c8c8c8"}]
     [:circle {:cx 30 :cy 22 :r 2.5 :fill "#ccc"}]
     [:circle {:cx 70 :cy 22 :r 2.5 :fill "#ccc"}]]

    :sigma
    [:g
     [:polygon {:points "30,24 35,10 42,18 50,6 58,18 65,10 70,24" :fill (:hat c)}]
     [:rect {:x 30 :y 22 :width 40 :height 6 :rx 2 :fill (:hat c)}]
     [:circle {:cx 38 :cy 14 :r 2 :fill "#FFD700"}]
     [:circle {:cx 50 :cy 8 :r 2.5 :fill "#FFD700"}]
     [:circle {:cx 62 :cy 14 :r 2 :fill "#FFD700"}]]

    :ohio
    (into
     [:g
      [:ellipse {:cx 50 :cy 18 :rx 14 :ry 18 :fill "#FFD700"}]
      [:ellipse {:cx 50 :cy 18 :rx 10 :ry 14 :fill "#FFEC80"}]]
     (concat
      (for [i (range 5)]
        [:circle {:cx (+ 42 (* i 4)) :cy (+ 10 (* (mod i 2) 4)) :r 2.5 :fill "#F5C842"}])
      (for [i (range 5)]
        [:circle {:cx (+ 42 (* i 4)) :cy (+ 18 (* (mod i 2) 4)) :r 2.5 :fill "#F5C842"}])
      [[:path {:d "M 44 2 Q 42 -4 38 0" :stroke "#46A302" :stroke-width 2 :fill "none"}]
       [:path {:d "M 56 2 Q 58 -4 62 0" :stroke "#46A302" :stroke-width 2 :fill "none"}]]))

    :rizz
    [:g
     [:circle {:cx 50 :cy 14 :r 8 :fill "none" :stroke (:hat c) :stroke-width 3}]
     [:circle {:cx 50 :cy 14 :r 3 :fill (:hat c)}]
     [:line {:x1 50 :y1 4 :x2 50 :y2 8 :stroke (:hat c) :stroke-width 2}]
     [:line {:x1 42 :y1 8 :x2 44 :y2 11 :stroke (:hat c) :stroke-width 2}]
     [:line {:x1 58 :y1 8 :x2 56 :y2 11 :stroke (:hat c) :stroke-width 2}]
     [:circle {:cx 36 :cy 20 :r 3 :fill (:hat c) :opacity 0.6}]
     [:circle {:cx 64 :cy 20 :r 3 :fill (:hat c) :opacity 0.6}]]

    :gyatt
    [:g
     [:path {:d "M 26 36 Q 26 12 50 12 Q 74 12 74 36" :stroke (:hat c) :stroke-width 5 :fill "none"}]
     [:rect {:x 20 :y 30 :width 12 :height 16 :rx 5 :fill (:hat c)}]
     [:rect {:x 68 :y 30 :width 12 :height 16 :rx 5 :fill (:hat c)}]
     [:rect {:x 22 :y 33 :width 8 :height 10 :rx 3 :fill "#333"}]
     [:rect {:x 70 :y 33 :width 8 :height 10 :rx 3 :fill "#333"}]]

    nil))

(defn- mouth [mood]
  (case mood
    (:happy :idle)
    [:g
     [:path {:d "M 36 60 Q 50 72 64 60" :stroke "#1A1A1A" :stroke-width 3 :fill "white" :stroke-linecap "round"}]
     [:path {:d "M 36 60 Q 50 72 64 60 L 64 63 Q 50 75 36 63 Z" :fill "white"}]
     [:line {:x1 43 :y1 60 :x2 43 :y2 66 :stroke "#1A1A1A" :stroke-width 1.5}]
     [:line {:x1 50 :y1 61 :x2 50 :y2 67 :stroke "#1A1A1A" :stroke-width 1.5}]
     [:line {:x1 57 :y1 60 :x2 57 :y2 66 :stroke "#1A1A1A" :stroke-width 1.5}]]

    :surprised
    [:g
     [:ellipse {:cx 50 :cy 63 :rx 8 :ry 6 :fill "#1A1A1A"}]
     [:ellipse {:cx 50 :cy 63 :rx 5 :ry 4 :fill "#ff6b6b"}]]

    :sigma
    [:path {:d "M 40 62 Q 52 68 62 60" :stroke "#1A1A1A" :stroke-width 2.5 :fill "none" :stroke-linecap "round"}]

    :nuhuh
    [:line {:x1 38 :y1 64 :x2 62 :y2 64 :stroke "#1A1A1A" :stroke-width 3 :stroke-linecap "round"}]

    nil))

(defn- accessory [character]
  (case character
    :sigma
    [:g
     [:rect {:x 27 :y 42 :rx 3 :width 19 :height 10 :fill "#1A1A2E" :opacity 0.7}]
     [:rect {:x 54 :y 42 :rx 3 :width 19 :height 10 :fill "#1A1A2E" :opacity 0.7}]
     [:line {:x1 46 :y1 46 :x2 54 :y2 46 :stroke "#1A1A2E" :stroke-width 2}]]

    :rizz
    [:g
     [:text {:x 26 :y 60 :font-size 10 :text-anchor "middle"} "💖"]
     [:text {:x 74 :y 60 :font-size 10 :text-anchor "middle"} "💖"]]

    nil))

(defn brainrot-mascot
  "Props: {:mood :idle|:happy|:surprised|:sigma|:nuhuh
           :size px (default 80)
           :class extra classes
           :animate bool (default true)
           :character :yoro|:skibidi|:sigma|:ohio|:rizz|:gyatt}"
  [{:keys [character] :or {character :yoro} :as _props}]
  (let [phrase-idx  (r/atom 0)
        show-phrase (r/atom false)
        bouncing    (r/atom false)
        blinking    (r/atom false)
        intervals   (atom [])
        phrases     (get phrases-by-char character (:yoro phrases-by-char))
        handle-click
        (fn []
          (swap! phrase-idx #(mod (inc %) (count phrases)))
          (reset! show-phrase true)
          (reset! bouncing true)
          (js/setTimeout #(reset! bouncing false) 600)
          (js/setTimeout #(reset! show-phrase false) 2200))]
    (r/create-class
     {:display-name "brainrot-mascot"

      :component-did-mount
      (fn [_]
        (let [blink-iv (js/setInterval
                        (fn []
                          (reset! blinking true)
                          (js/setTimeout #(reset! blinking false) 150))
                        3200)
              phrase-iv (js/setInterval
                         (fn []
                           (reset! phrase-idx (rand-int (count phrases)))
                           (reset! show-phrase true)
                           (js/setTimeout #(reset! show-phrase false) 2200))
                         8000)]
          (reset! intervals [blink-iv phrase-iv])))

      :component-will-unmount
      (fn [_]
        (doseq [iv @intervals] (js/clearInterval iv))
        (reset! intervals []))

      :reagent-render
      (fn [{:keys [mood size class animate character]
            :or {mood :idle size 80 class "" animate true character :yoro}}]
        (let [c            (get palette character (:yoro palette))
              eye-scale-y  (if @blinking 0.05 1)
              pupil-offset (case mood :surprised -1 :happy 2 :nuhuh -2 0)]
          [:div {:class (str "relative inline-flex flex-col items-center select-none " class)
                 :style {:width size}
                 :role "img"
                 :aria-label (get char-names character "YORO")}
           (when @show-phrase
             [:div {:class (str "absolute bottom-full mb-2 left-1/2 -translate-x-1/2 whitespace-nowrap "
                                "rounded-2xl bg-yellow-400 px-3 py-1.5 text-[13px] font-bold text-gray-900 "
                                "shadow-lg z-10 speech-bubble")}
              (nth phrases (mod @phrase-idx (count phrases)))])

           [:svg {:view-box "0 0 100 110"
                  :xmlns "http://www.w3.org/2000/svg"
                  :style {:width size :height (* size 1.1) :cursor "pointer"}
                  :class (when animate (if @bouncing "mascot-bounce" "mascot-float"))
                  :role "button"
                  :tab-index 0
                  :aria-label (get char-names character "YORO")
                  :on-click handle-click}
            ;; Shadow
            [:ellipse {:cx 50 :cy 107 :rx 22 :ry 5 :fill "rgba(0,0,0,0.12)"}]
            ;; Hat varies by character
            (hat character c)
            ;; Body
            [:ellipse {:cx 50 :cy 78 :rx 30 :ry 24 :fill (:body c)}]
            [:ellipse {:cx 50 :cy 82 :rx 16 :ry 12 :fill (:belly c)}]
            ;; Head
            [:circle {:cx 50 :cy 50 :r 28 :fill (:body c)}]
            ;; Eyes
            [:ellipse {:cx 37 :cy 46 :rx 11 :ry (* 11 eye-scale-y) :fill "white"}]
            [:ellipse {:cx 63 :cy 46 :rx 11 :ry (* 11 eye-scale-y) :fill "white"}]
            [:circle {:cx 38 :cy (+ 47 pupil-offset) :r 6 :fill (:pupil c)}]
            [:circle {:cx 64 :cy (+ 47 pupil-offset) :r 6 :fill (:pupil c)}]
            [:circle {:cx 40 :cy (+ 44 pupil-offset) :r 2.5 :fill "white"}]
            [:circle {:cx 66 :cy (+ 44 pupil-offset) :r 2.5 :fill "white"}]
            [:circle {:cx 38 :cy (+ 47 pupil-offset) :r 2.5 :fill "#1A1A2E"}]
            [:circle {:cx 64 :cy (+ 47 pupil-offset) :r 2.5 :fill "#1A1A2E"}]
            ;; Mouth
            (mouth mood)
            ;; Cheeks
            [:ellipse {:cx 28 :cy 57 :rx 6 :ry 4 :fill "#ff9999" :opacity 0.4}]
            [:ellipse {:cx 72 :cy 57 :rx 6 :ry 4 :fill "#ff9999" :opacity 0.4}]
            ;; Arms
            [:path {:d "M 22 68 Q 10 72 14 82" :stroke (:limb c) :stroke-width 8 :fill "none" :stroke-linecap "round"}]
            [:circle {:cx 14 :cy 83 :r 5 :fill (:limb c)}]
            [:path {:d "M 78 68 Q 90 72 86 82" :stroke (:limb c) :stroke-width 8 :fill "none" :stroke-linecap "round"}]
            [:circle {:cx 86 :cy 83 :r 5 :fill (:limb c)}]
            ;; Feet
            [:ellipse {:cx 36 :cy 100 :rx 12 :ry 6 :fill (:limb c)}]
            [:ellipse {:cx 64 :cy 100 :rx 12 :ry 6 :fill (:limb c)}]
            ;; Character-specific accessory
            (accessory character)]]))})))
