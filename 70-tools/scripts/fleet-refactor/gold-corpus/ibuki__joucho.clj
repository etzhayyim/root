;; ported from 20-actors/ibuki/methods/joucho.py — gold reference (Fable)
;; ibuki 情緒 — mood は event の fold から emerge する (定数 stub の置換)。
;; 5-axis scores (各 0-100) を append-only event log の fold で導出。replay-events が as-of mood query。
;; scores は不変 map {:joy :calm :stress :gratitude :focus}。fold は純関数 (new scores を返す)。
(ns ibuki.methods.joucho
  (:import [java.security MessageDigest]))

(def axes [:joy :calm :stress :gratitude :focus])

(def default-scores {:joy 50 :calm 50 :stress 30 :gratitude 50 :focus 50})

(defn personality-baseline
  "決定的な per-organism baseline: sha256(code) → [25,75] の 5 値。stress 軸は [25,65] に制限
  (stress は LIVED event から来る — 生まれつき永久 stressed を避ける)。I/O なし。"
  [code]
  (let [h (.digest (MessageDigest/getInstance "SHA-256") (.getBytes (str code) "UTF-8"))
        v (fn [i] (+ 25 (mod (bit-or (bit-shift-left (bit-and (aget h (* i 2)) 0xff) 8)
                                     (bit-and (aget h (inc (* i 2))) 0xff))
                             51)))
        vals (mapv v (range 5))
        ;; stress → [25,65]
        vals (assoc vals 2 (+ 25 (quot (* (- (vals 2) 25) 41) 51)))]
    (zipmap axes vals)))

(defn determine-mood
  "高 stress 優先; さもなくば ≥60 の最優位軸; さもなくば neutral。"
  [scores]
  (if (>= (:stress scores) 70)
    "stressed"
    (let [ranked (sort-by (comp - second)
                          [["joyful" (:joy scores)] ["calm" (:calm scores)]
                           ["grateful" (:gratitude scores)] ["focused" (:focus scores)]])
          [label v] (first ranked)]
      (if (< v 60) "neutral" label))))

;; CLOSED vocabulary — 未知の event kind は例外 (表現不能な刺激は mood を動かせない)。
;; delta = {:joy :calm :stress :gratitude :focus}。
(def event-deltas
  {:event/post-emitted    {:focus 1}
   :event/follower-gained {:joy 2 :gratitude 2}
   :event/inbox-pressure  {:calm -1 :stress 4}
   :event/kaizen-merged   {:calm 3 :stress -3 :gratitude 1}
   :event/kaizen-rejected {:stress 2 :focus 1}
   :event/idle            {}})

(defn- clamp [v] (max 0 (min 100 v)))

(defn- drift
  "homeostasis の 1 step: idle beat は各軸を baseline へ 1 引き寄せる。"
  [v base]
  (cond (> v base) (dec v), (< v base) (inc v), :else v))

(defn fold-event
  "観測した 1 event を scores へ fold する (純 — new scores)。"
  [scores event baseline]
  (when-not (contains? event-deltas event)
    (throw (ex-info (str "unknown joucho event kind (closed vocab): " event) {:event event})))
  (if (= event :event/idle)
    (reduce (fn [s a] (assoc s a (drift (s a) (baseline a)))) scores axes)
    (let [d (event-deltas event)]
      (reduce (fn [s a] (assoc s a (clamp (+ (s a) (get d a 0))))) scores axes))))

(defn replay-events
  "baseline から event stream を replay する — as-of mood query。
  up-to-tx N の events を渡せば tx N での mood が出る。"
  [baseline events]
  (reduce (fn [scores ev] (fold-event scores ev baseline)) baseline events))
