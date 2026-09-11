;; ported from orgs/etzhayyim/com-etzhayyim-niyaku/methods/crane_dynamics.py — gold reference (Fable)
;; niyaku 荷役 — 吊り荷 anti-sway の crane 動力学。trolley を acceleration-commanded として扱い、
;; hanging-pendulum-on-trolley を RK4 で積分する。ZV (Zero-Vibration) input shaper で残留振動を消す。
;; crane は不変パラメータ map; state は [x x-dot theta theta-dot] のベクタ。純関数。
(ns niyaku.methods.crane-dynamics)

(def default-crane
  {:cable-length 30.0   ; m
   :gravity 9.81        ; m/s²
   :sway-damping 0.02   ; 粘性減衰比 proxy
   :accel-max 0.6       ; m/s² trolley 加速度包絡
   :velocity-max 4.0})  ; m/s trolley 最大速度

(defn natural-frequency
  "無減衰 sway 固有周波数 ω = sqrt(g/L) (rad/s)。"
  [{:keys [gravity cable-length]}]
  (Math/sqrt (/ gravity cable-length)))

(defn sway-period
  "sway 周期 T = 2π/ω (s) — input-shaper のインパルス間隔を決める。"
  [crane]
  (/ (* 2.0 Math/PI) (natural-frequency crane)))

(defn- clamp [v lim] (max (- lim) (min lim v)))

(defn derivatives
  "state = [x x-dot theta theta-dot] の連続時間導関数。trolley 加速度 = clamp した command u。
  theta'' = -(g/L)sinθ - (a/L)cosθ - 2ζω θ'。"
  [crane state u]
  (let [[_ x-dot theta theta-dot] state
        a (clamp u (:accel-max crane))
        l (:cable-length crane)
        g (:gravity crane)
        zeta-w (* (:sway-damping crane) (natural-frequency crane))
        theta-acc (- (- (* (/ g l) (Math/sin theta))
                        (* (/ a l) (Math/cos theta)))
                     (* 2.0 zeta-w theta-dot))]
    [x-dot a theta-dot theta-acc]))

(defn- vadd [s k h] (mapv (fn [si ki] (+ si (* h ki))) s k))

(defn step
  "古典 RK4 で 1 step 進める (stiff な sway mode に安定)。trolley 速度包絡を servo limit で強制。"
  [crane state u dt]
  (let [k1 (derivatives crane state u)
        k2 (derivatives crane (vadd state k1 (/ dt 2.0)) u)
        k3 (derivatives crane (vadd state k2 (/ dt 2.0)) u)
        k4 (derivatives crane (vadd state k3 dt) u)
        nxt (mapv (fn [s a b c d] (+ s (* (/ dt 6.0) (+ a (* 2.0 b) (* 2.0 c) d))))
                  state k1 k2 k3 k4)]
    (update nxt 1 clamp (:velocity-max crane))))

(defn zv-shaper
  "Zero-Vibration input shaper のインパルス [[t0 a0] [t1 a1]]。
  半減衰周期だけ離れた 2 インパルスが残留振動を打ち消す (Singer-Seering)。振幅和 = 1。"
  [crane]
  (let [zeta (:sway-damping crane)
        w (natural-frequency crane)
        denom (Math/sqrt (max 1e-9 (- 1.0 (* zeta zeta))))
        wd (* w denom)
        td (/ Math/PI wd)                        ; 半減衰周期
        k (Math/exp (/ (* (- zeta) Math/PI) denom))
        a0 (/ 1.0 (+ 1.0 k))
        a1 (/ k (+ 1.0 k))]
    [[0.0 a0] [td a1]]))
