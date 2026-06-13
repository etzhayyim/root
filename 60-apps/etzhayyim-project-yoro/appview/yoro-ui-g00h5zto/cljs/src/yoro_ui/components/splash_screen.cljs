(ns yoro-ui.components.splash-screen
  "Splash screen with canvas floating shapes + yoro logo + loading dots.
   Auto-dismisses after ~2.5 s with a success sound.
   Uses r/create-class for canvas lifecycle (prefers-reduced-motion respected)."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.interop.sound :as snd]))

;; ---------------------------------------------------------------------------
;; re-frame glue

(rf/reg-event-db :splash/dismiss (fn [db _] (assoc db :splash-done? true)))
(rf/reg-sub :splash/done?        (fn [db _] (get db :splash-done? false)))

;; ---------------------------------------------------------------------------
;; Canvas — 25 floating translucent circles (reduced-motion → skipped)

(defn- rnd [lo hi] (+ lo (* (js/Math.random) (- hi lo))))

(defn- make-orb [w h]
  {:x  (rnd 0 w)   :y  (rnd 0 h)
   :vx (rnd -0.3 0.3) :vy (rnd -0.3 0.3)
   :r  (rnd 20 70)
   :a  (rnd 0.03 0.10)
   :ph (rnd 0 (* 2 js/Math.PI))})

(def ^:private COLORS ["#58CC02" "#1CB0F6" "#a78bfa" "#34d399" "#f472b6"])

(defn- canvas-loop [canvas-ref orbs-ref raf-ref last-t-ref]
  (fn loop! [ts]
    (when-let [^js cvs @canvas-ref]
      (let [w   (.-width  cvs)
            h   (.-height cvs)
            ^js ctx (.getContext cvs "2d")
            dt  (- ts @last-t-ref)]
        (when (>= dt (/ 1000 24))
          (reset! last-t-ref ts)
          (.clearRect ctx 0 0 w h)
          (swap! orbs-ref
                 (fn [orbs]
                   (mapv (fn [o]
                           (let [x  (+ (:x o) (:vx o))
                                 y  (+ (:y o) (:vy o))
                                 ph (+ (:ph o) 0.015)
                                 pulse (+ 0.8 (* 0.2 (js/Math.sin ph)))]
                             (.beginPath ctx)
                             (.arc ctx x y (* (:r o) pulse) 0 (* 2 js/Math.PI))
                             (set! (.-fillStyle ctx)
                                   (let [[cr cg cb]
                                         (-> (nth COLORS (mod (hash o) (count COLORS)))
                                             (subs 1)
                                             ((fn [h]
                                                [(js/parseInt (subs h 0 2) 16)
                                                 (js/parseInt (subs h 2 4) 16)
                                                 (js/parseInt (subs h 4 6) 16)])))]
                                     (str "rgba(" cr "," cg "," cb "," (:a o) ")")))
                             (.fill ctx)
                             (assoc o :x  (cond (< x (- (:r o))) (+ w (:r o))
                                                (> x (+ w (:r o))) (- (:r o))
                                                :else x)
                                      :y  (cond (< y (- (:r o))) (+ h (:r o))
                                                (> y (+ h (:r o))) (- (:r o))
                                                :else y)
                                      :ph ph)))
                         orbs))))
        (reset! raf-ref (js/requestAnimationFrame loop!))))))

;; ---------------------------------------------------------------------------
;; Loading dots sub-component

(defn- loading-dots []
  [:div {:class "flex gap-2 justify-center mt-6"}
   (for [i (range 3)]
     ^{:key i}
     [:div {:class "w-2 h-2 rounded-full bg-white/60"
            :style {:animation (str "splash-dot 1.2s ease-in-out " (* i 0.2) "s infinite")}}])])

;; ---------------------------------------------------------------------------
;; Component

(defn splash-screen []
  (let [done?      @(rf/subscribe [:splash/done?])
        canvas-ref (atom nil)
        orbs-ref   (atom [])
        raf-ref    (atom nil)
        last-t-ref (atom 0)
        skip?      (and (exists? js/window)
                        (try (.matches (.matchMedia js/window "(prefers-reduced-motion: reduce)"))
                             (catch js/Error _ false)))
        fading?    (r/atom false)]

    (when done? nil)

    (r/create-class
     {:display-name "splash-screen"

      :component-did-mount
      (fn [this]
        ;; Dismiss after 2.5 s
        (js/setTimeout
         (fn []
           (reset! fading? true)
           (js/setTimeout
            (fn []
              (snd/play-success!)
              (rf/dispatch [:splash/dismiss]))
            400))
         2100)
        ;; Start canvas animation
        (when-not skip?
          (let [node (r/dom-node this)
                cvs  (.querySelector node "canvas")]
            (reset! canvas-ref cvs)
            (let [w (.-innerWidth js/window)
                  h (.-innerHeight js/window)]
              (set! (.-width  cvs) w)
              (set! (.-height cvs) h)
              (reset! orbs-ref (vec (repeatedly 25 #(make-orb w h)))))
            (reset! raf-ref (js/requestAnimationFrame
                             (canvas-loop canvas-ref orbs-ref raf-ref last-t-ref))))))

      :component-will-unmount
      (fn [_]
        (when @raf-ref (js/cancelAnimationFrame @raf-ref)))

      :reagent-render
      (fn []
        (when-not @(rf/subscribe [:splash/done?])
          [:div {:class (str "fixed inset-0 z-[100] flex flex-col items-center justify-center"
                             " bg-[#0a0a0a] transition-opacity duration-400"
                             (if @fading? " opacity-0 pointer-events-none" " opacity-100"))}
           ;; Canvas layer
           (when-not skip?
             [:canvas {:class "absolute inset-0 w-full h-full pointer-events-none"}])

           ;; Content
           [:div {:class "relative z-10 flex flex-col items-center"}
            ;; yoro logo
            [:img {:src   "/yoro-final.svg"
                   :alt   "yoro"
                   :class "w-28 h-28 drop-shadow-[0_0_24px_rgba(88,204,2,0.6)]"
                   :style {:animation "splash-yoro-float 2s ease-in-out infinite"}}]

            ;; App name
            [:h1 {:class "mt-5 text-[28px] font-black text-white tracking-wide"}
             "yoro"]

            ;; Tagline
            [:p {:class "text-[13px] text-white/50 mt-1 font-medium"}
             "powered by etzhayyim"]

            ;; Dots
            [loading-dots]]]))})))
