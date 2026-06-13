(ns yoro-ui.interop.sound
  "Web Audio API sound engine — port of svelte/src/lib/sound.ts.
   No external assets; all sounds are synthesised with oscillators.
   Fire-and-forget; errors are silently suppressed.")

;; ---------------------------------------------------------------------------
;; AudioContext singleton — recreated if closed (e.g. after page suspend)

(defonce ^:private audio-ctx (atom nil))

(defn- get-ctx []
  (when (exists? js/AudioContext)
    (let [ctx @audio-ctx]
      (if (or (nil? ctx) (= (.-state ctx) "closed"))
        (let [c (js/AudioContext.)]
          (reset! audio-ctx c)
          c)
        ctx))))

;; ---------------------------------------------------------------------------
;; Reduced-motion / reduced-sound guard

(defn- sound-muted? []
  (when (exists? js/window)
    (try
      (or (and (exists? js/window.matchMedia)
               (.matches (.matchMedia js/window "(prefers-reduced-sound: reduce)")))
          (and (exists? js/window.matchMedia)
               (.matches (.matchMedia js/window "(prefers-reduced-motion: reduce)"))))
      (catch js/Error _ false))))

;; ---------------------------------------------------------------------------
;; Primitive: schedule one oscillator burst
;;   freq     Hz
;;   start    seconds from ctx.currentTime
;;   duration seconds
;;   gain     peak amplitude (0-1)
;;   ctx      AudioContext
;;   type     OscillatorType string (default "sine")

(defn- tone
  ([freq start duration gain ctx] (tone freq start duration gain ctx "sine"))
  ([freq start duration gain ctx type]
   (when ctx
     (try
       (let [osc (.createOscillator ctx)
             g   (.createGain ctx)
             now (.-currentTime ctx)
             t0  (+ now start)
             t1  (+ t0 duration)]
         (.connect osc g)
         (.connect g (.-destination ctx))
         (set! (.-type osc) type)
         (.setValueAtTime (.-frequency osc) freq t0)
         (.setValueAtTime (.-value (.-gain g)) gain t0)
         (.exponentialRampToValueAtTime (.-value (.-gain g)) 0.001 t1)
         (.start osc t0)
         (.stop  osc (+ t1 0.01)))
       (catch js/Error _ nil)))))

;; ---------------------------------------------------------------------------
;; Public sound functions — exact port of sound.ts

(defn play-success!
  "C5–E5–G5 ascending triad."
  []
  (when-let [ctx (get-ctx)]
    (tone 523 0.00 0.15 0.25 ctx)
    (tone 659 0.12 0.15 0.22 ctx)
    (tone 784 0.24 0.20 0.20 ctx)))

(defn play-click!
  "Brief 880 Hz click."
  []
  (when-let [ctx (get-ctx)]
    (tone 880 0 0.08 0.18 ctx)))

(defn play-notif!
  "Two-tone C6–E6 notification chime."
  []
  (when-let [ctx (get-ctx)]
    (tone 1046 0.00 0.12 0.20 ctx)
    (tone 1318 0.10 0.15 0.18 ctx)))

(defn play-fail!
  "Sawtooth descending B4–Ab4–Eb4."
  []
  (when-let [ctx (get-ctx)]
    (tone 392 0.00 0.12 0.20 ctx "sawtooth")
    (tone 349 0.10 0.12 0.18 ctx "sawtooth")
    (tone 311 0.20 0.15 0.15 ctx "sawtooth")))

(defn play-level-up!
  "Four-tone C5–E5–G5–C6 fanfare."
  []
  (when-let [ctx (get-ctx)]
    (tone 523 0.00 0.12 0.28 ctx)
    (tone 659 0.10 0.12 0.25 ctx)
    (tone 784 0.20 0.12 0.22 ctx)
    (tone 1046 0.30 0.25 0.30 ctx)))

(defn play-tap-soft!
  "Soft 720 Hz sine tap — respects reduced-motion/sound."
  []
  (when-not (sound-muted?)
    (when-let [ctx (get-ctx)]
      (tone 720 0 0.04 0.14 ctx "sine"))))

(defn play-tick!
  "Fast 1400 Hz triangle tick — respects reduced-motion/sound."
  []
  (when-not (sound-muted?)
    (when-let [ctx (get-ctx)]
      (tone 1400 0 0.02 0.08 ctx "triangle"))))

(defn play-chime-c5!
  "C5 (523 Hz) sine chime — respects reduced-motion/sound."
  []
  (when-not (sound-muted?)
    (when-let [ctx (get-ctx)]
      (tone 523 0 0.20 0.22 ctx "sine"))))

(defn play-wind-bell!
  "Wind-bell: 880 Hz + 1320 Hz harmonics — respects reduced-motion/sound."
  []
  (when-not (sound-muted?)
    (when-let [ctx (get-ctx)]
      (tone 880  0.00 0.50 0.14 ctx "sine")
      (tone 1320 0.08 0.40 0.10 ctx "sine"))))

(defn play-skibidi!
  "Sawtooth 600→80 Hz sweep in 0.4 s — respects reduced-motion/sound."
  []
  (when-not (sound-muted?)
    (when (exists? js/AudioContext)
      (try
        (let [ctx (get-ctx)]
          (when ctx
            (let [osc (.createOscillator ctx)
                  g   (.createGain ctx)
                  now (.-currentTime ctx)]
              (.connect osc g)
              (.connect g (.-destination ctx))
              (set! (.-type osc) "sawtooth")
              (.setValueAtTime (.-frequency osc) 600 now)
              (.exponentialRampToValueAtTime (.-frequency osc) 80 (+ now 0.4))
              (.setValueAtTime (.-value (.-gain g)) 0.18 now)
              (.exponentialRampToValueAtTime (.-value (.-gain g)) 0.001 (+ now 0.41))
              (.start osc now)
              (.stop  osc (+ now 0.42)))))
        (catch js/Error _ nil)))))

;; Alias — exported for legacy callers
(def play-rank-promotion! play-level-up!)
