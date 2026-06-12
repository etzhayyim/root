;; ported from 40-engine/svelte/design-system/src/lib/builders/swipe.ts — gold reference (Fable)
;; Headless swipe 検出。TS の閉包 + コールバックは Clojure では
;; 「不変 opts + 純粋な判定関数 + ハンドラ生成」に分解する。
;; DOM/時計は WASM/ブラウザ host capability として注入する (now-fn / 副作用は呼び出し側)。
(ns design-system.swipe)

(def default-opts {:threshold 50 :velocity-threshold 0.3})

(defn classify-swipe
  "開始点・終了点・経過時間から swipe 方向を判定する純関数。
  しきい値 (距離 OR 速度) 未達なら nil。
    start {:x :y}  end {:x :y}  dt(ms)  opts → :left/:right/:up/:down or nil"
  [{sx :x sy :y} {ex :x ey :y} dt opts]
  (let [{:keys [threshold velocity-threshold]} (merge default-opts opts)
        dx (- ex sx), dy (- ey sy)
        adx (abs dx), ady (abs dy)
        dt (max dt 1)                      ; 0 除算回避
        vx (/ adx dt), vy (/ ady dt)]
    (if (> adx ady)
      (when (or (> adx threshold) (> vx velocity-threshold))
        (if (pos? dx) :right :left))
      (when (or (> ady threshold) (> vy velocity-threshold))
        (if (pos? dy) :down :up)))))

(defn create-swipe
  "opts の :on-swipe-{left,right,up,down} を判定結果へディスパッチするハンドラを返す。
  ブラウザ action の組み立ては host 側 (このコアは方向判定 + ディスパッチのみ)。"
  [opts]
  (let [opts (merge default-opts opts)
        dispatch {:left (:on-swipe-left opts)
                  :right (:on-swipe-right opts)
                  :up (:on-swipe-up opts)
                  :down (:on-swipe-down opts)}]
    (fn on-gesture [start end dt]
      (when-let [dir (classify-swipe start end dt opts)]
        (when-let [cb (dispatch dir)] (cb))
        dir))))
