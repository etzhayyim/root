(ns yoro-ui.components.ambient-background
  "Canvas ambient background — port of svelte/src/lib/superapp/AmbientBackground.svelte.
   30 particles + 8 floating shapes at 24 fps. No vibes-store dependency (uses fixed colour).
   Uses r/create-class for requestAnimationFrame lifecycle."
  (:require [reagent.core :as r]))

;; ---------------------------------------------------------------------------
;; Constants

(def ^:private MAX-PARTICLES 30)
(def ^:private MAX-SHAPES    8)
(def ^:private FPS-INTERVAL  (/ 1000 24))
(def ^:private BASE-COLOR    "#60a5fa")   ; blue-400 default (vibes neutral)

;; ---------------------------------------------------------------------------
;; Helpers

(defn- hex->rgb [hex]
  (let [h (subs hex 1)
        r (js/parseInt (subs h 0 2) 16)
        g (js/parseInt (subs h 2 4) 16)
        b (js/parseInt (subs h 4 6) 16)]
    [r g b]))

(defn- rnd
  ([lo hi] (+ lo (* (js/Math.random) (- hi lo))))
  ([n]     (* n (js/Math.random))))

;; ---------------------------------------------------------------------------
;; Object initialisation

(defn- make-particle [w h]
  {:x  (rnd w)
   :y  (rnd h)
   :vx (rnd -0.4 0.4)
   :vy (rnd -0.4 0.4)
   :r  (rnd 1.5 4.0)
   :a  (rnd 0.2 0.7)})

(defn- make-shape [w h]
  {:x          (rnd w)
   :y          (rnd h)
   :vx         (rnd -0.25 0.25)
   :vy         (rnd -0.25 0.25)
   :size       (rnd 18 55)
   :rotation   (rnd (* 2 js/Math.PI))
   :rot-speed  (rnd -0.005 0.005)
   :shape      (js/Math.floor (rnd 4))   ; 0=circle-outline 1=diamond 2=circle-fill 3=rounded-rect
   :alpha      (rnd 0.04 0.12)
   :pulse      (rnd (* 2 js/Math.PI))})

(defn- init-objects [w h]
  {:particles (vec (repeatedly MAX-PARTICLES #(make-particle w h)))
   :shapes    (vec (repeatedly MAX-SHAPES    #(make-shape w h)))})

;; ---------------------------------------------------------------------------
;; Update helpers

(defn- wrap [v lo hi]
  (cond (< v lo) hi
        (> v hi) lo
        :else v))

(defn- update-particle [p w h speed]
  (let [x (+ (:x p) (* (:vx p) speed))
        y (+ (:y p) (* (:vy p) speed))]
    (assoc p :x (wrap x -5 (+ w 5))
              :y (wrap y -5 (+ h 5)))))

(defn- update-shape [s w h speed t]
  (let [x  (+ (:x s) (* (:vx s) speed))
        y  (+ (:y s) (* (:vy s) speed))
        r  (+ (:rotation s) (:rot-speed s))
        ph (+ (:pulse s) 0.02)]
    (assoc s :x        (wrap x (- (:size s)) (+ w (:size s)))
              :y        (wrap y (- (:size s)) (+ h (:size s)))
              :rotation r
              :pulse    ph)))

;; ---------------------------------------------------------------------------
;; Draw helpers

(defn- draw-shape! [ctx s r g b]
  (let [sz  (:size s)
        x   (:x s)
        y   (:y s)
        a   (* (:alpha s) (+ 0.85 (* 0.15 (js/Math.sin (:pulse s)))))
        rot (:rotation s)]
    (set! (.-strokeStyle ctx) (str "rgba(" r "," g "," b "," a ")"))
    (set! (.-fillStyle   ctx) (str "rgba(" r "," g "," b "," (* a 0.3) ")"))
    (set! (.-lineWidth   ctx) 1.5)
    (.save ctx)
    (.translate ctx x y)
    (.rotate ctx rot)
    (.beginPath ctx)
    (case (:shape s)
      ;; circle outline
      0 (do (.arc ctx 0 0 sz 0 (* 2 js/Math.PI))
            (.stroke ctx))
      ;; diamond
      1 (do (.moveTo ctx 0 (- sz))
            (.lineTo ctx sz 0)
            (.lineTo ctx 0 sz)
            (.lineTo ctx (- sz) 0)
            (.closePath ctx)
            (.stroke ctx))
      ;; circle fill
      2 (do (.arc ctx 0 0 sz 0 (* 2 js/Math.PI))
            (.fill ctx))
      ;; rounded rect
      3 (let [rr (/ sz 4)]
          (.roundRect ctx (- sz) (- sz) (* sz 2) (* sz 2) rr)
          (.stroke ctx))
      nil)
    (.restore ctx)))

(defn- draw! [^js ctx w h [r g b] {:keys [particles shapes]}]
  ;; Background gradient
  (.clearRect ctx 0 0 w h)
  (let [grad (.createRadialGradient ctx (/ w 2) (/ h 2) 0 (/ w 2) (/ h 2) (/ (js/Math.max w h) 1.4))]
    (.addColorStop grad 0 (str "rgba(" r "," g "," b ",0.08)"))
    (.addColorStop grad 1 "rgba(10,10,10,0)")
    (set! (.-fillStyle ctx) grad)
    (.fillRect ctx 0 0 w h))
  ;; Shapes
  (doseq [s shapes] (draw-shape! ctx s r g b))
  ;; Particles
  (doseq [p particles]
    (.beginPath ctx)
    (.arc ctx (:x p) (:y p) (:r p) 0 (* 2 js/Math.PI))
    (set! (.-fillStyle ctx) (str "rgba(" r "," g "," b "," (:a p) ")"))
    (.fill ctx)))

;; ---------------------------------------------------------------------------
;; Component

(defn ambient-background []
  (let [canvas-ref  (atom nil)
        raf-id      (atom nil)
        objects     (atom nil)
        last-time   (atom 0)
        rgb         (hex->rgb BASE-COLOR)

        resize!
        (fn []
          (when-let [^js cvs @canvas-ref]
            (let [w (.-innerWidth  js/window)
                  h (.-innerHeight js/window)]
              (set! (.-width  cvs) w)
              (set! (.-height cvs) h)
              (reset! objects (init-objects w h)))))

        loop!
        (fn loop! [ts]
          (when-let [^js cvs @canvas-ref]
            (let [dt (- ts @last-time)]
              (when (>= dt FPS-INTERVAL)
                (reset! last-time ts)
                (let [w (.-width  cvs)
                      h (.-height cvs)
                      ^js ctx (.getContext cvs "2d")
                      speed  0.6
                      objs   @objects
                      next   {:particles (mapv #(update-particle % w h speed) (:particles objs))
                               :shapes    (mapv #(update-shape % w h speed ts) (:shapes objs))}]
                  (reset! objects next)
                  (draw! ctx w h rgb next)))
              (reset! raf-id (js/requestAnimationFrame loop!)))))

        skip? (and (exists? js/window)
                   (try (.matches (.matchMedia js/window "(prefers-reduced-motion: reduce)"))
                        (catch js/Error _ false)))]

    (r/create-class
     {:display-name "ambient-background"

      :component-did-mount
      (fn [_]
        ;; canvas-ref is already set by the :ref callback on the canvas element
        ;; (React fires ref callbacks before componentDidMount)
        (when-not skip?
          (resize!)
          (.addEventListener js/window "resize" resize!)
          (reset! raf-id (js/requestAnimationFrame loop!))))

      :component-will-unmount
      (fn [_]
        (when @raf-id (js/cancelAnimationFrame @raf-id))
        (.removeEventListener js/window "resize" resize!))

      :reagent-render
      (fn []
        (if skip?
          ;; Static radial gradient fallback for reduced-motion
          [:div {:class "pointer-events-none absolute inset-0 w-full h-full"
                 :style {:background "radial-gradient(ellipse at 50% 40%, rgba(96,165,250,0.07) 0%, transparent 70%)"}}]
          [:canvas {:class "pointer-events-none absolute inset-0 w-full h-full"
                    :style {:display "block"}
                    :ref   #(reset! canvas-ref %)}]))})))
