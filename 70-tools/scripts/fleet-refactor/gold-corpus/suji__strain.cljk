;; ported from orgs/etzhayyim/com-etzhayyim-suji/methods/strain.py — gold reference (Fable)
;; suji 筋 — sustained-load strain → 強張り (stiffness) over a work session。
;; 緊張 (instantaneous %MVC) が held されると 強張り になる。静的姿勢 = work session 長の等尺性収縮で、
;; 等尺性負荷は %MVC で急落する endurance limit を持つ (Rohmert 1960)。
;;   ACUTE  — held-time が T_end に近づくほど fatigue 蓄積。
;;   CHRONIC— 閾値以下でも連続動員される low-threshold 運動単位が時間で strain 蓄積 (desk-work 肩こり)。
;; stiffness index ∈ [0,1) = 1 - exp(-dose)。
;; NON-DIAGNOSTIC (G1): index は normalised load-time dose で医学的所見ではない。
;; SELF-REFERENCED (G3): 同一 member の他姿勢とのみ比較、人間横断のランキングはしない。
(ns suji.methods.strain)

(def chronic-threshold-pct 2.0)   ; これ以下の %MVC は持続的動員ほぼ無し
(def chronic-weight 0.45)         ; chronic low-load dose の重み (acute 比)
(def endurance-floor-pct 8.0)     ; これ以下は acute endurance を実質無限扱い

(defn endurance-minutes
  "与えられた %MVC での Rohmert 型等尺性 endurance time (分)。
  floor 以下は ##Inf (low-load static work に acute failure point は無い)。
  T_end(f) ≈ 0.2 · f^-2.32: 50%≈1min, 25%≈5min, 15%≈~16min。"
  [mvc-pct]
  (if (<= mvc-pct endurance-floor-pct)
    ##Inf
    (let [f (/ mvc-pct 100.0)]
      (* 0.2 (Math/pow f -2.32)))))

(defn muscle-strain
  "1 筋が mvc-pct を session-minutes 保持して蓄積する stiffness。→ strain map。"
  [{:keys [name mvc-pct]} session-minutes]
  (when (neg? session-minutes)
    (throw (ex-info "session-minutes must be >= 0" {:session-minutes session-minutes})))
  (let [t-end (endurance-minutes mvc-pct)
        acute (if (infinite? t-end) 0.0 (/ session-minutes t-end))
        excess (/ (max 0.0 (- mvc-pct chronic-threshold-pct)) 100.0)
        chronic (* chronic-weight excess (/ session-minutes 60.0))
        dose (+ acute chronic)
        stiffness (- 1.0 (Math/exp (- dose)))]
    {:name name
     :mvc-pct mvc-pct
     :session-minutes session-minutes
     :endurance-minutes t-end
     :acute-dose acute
     :chronic-dose chronic
     :stiffness-index stiffness
     :over-endurance (and (not (infinite? t-end)) (> session-minutes t-end))}))

(defn session-strain
  "work session 全体の stiffness map (既定 2 時間の連続姿勢)。"
  ([tensions] (session-strain tensions 120.0))
  ([tensions session-minutes]
   (mapv #(muscle-strain % session-minutes) tensions)))

(defn stiffness-band
  "stiffness index の粗い人間可読バンド (表示用、非診断)。"
  [stiffness-index]
  (cond
    (< stiffness-index 0.20) "low"
    (< stiffness-index 0.45) "moderate"
    (< stiffness-index 0.70) "high"
    :else "very-high"))
