;; ported from 20-actors/kabuto/methods/analyze.py (concentration core) — gold reference (Fable)
;; kabuto 兜 — supply-chain concentration metrics。HHI + tier-depth (resilience map, never target)。
;; per-commodity HHI = Σ(share²) ∈ (0,1]; 1.0 = 単一 disclosed supplier (独占)、低 = 分散。
(ns kabuto.methods.concentration)

(defn commodity-hhi
  "edges から commodity ごとの Herfindahl-Hirschman Index を計算する。
  各 edge = {:supply.edge/from :supply.edge/commodity :supply.edge/criticality}。
  → [{:commodity :suppliers :hhi} …] を集中度降順で。"
  [edges]
  (let [;; commodity → {supplier → Σ criticality}
        by-commodity (reduce
                      (fn [acc e]
                        (let [s (:supply.edge/from e)
                              commodity (:supply.edge/commodity e :unknown)
                              crit (double (or (:supply.edge/criticality e) 0.0))]
                          (if (and s (pos? crit))
                            (update-in acc [commodity s] (fnil + 0.0) crit)
                            acc)))
                      {} edges)]
    (->> by-commodity
         (keep (fn [[commodity shares]]
                 (let [tot (reduce + 0.0 (vals shares))]
                   (when (pos? tot)
                     {:commodity commodity
                      :suppliers (count shares)
                      :hhi (->> (vals shares)
                                (map #(let [share (/ % tot)] (* share share)))
                                (reduce + 0.0)
                                (* 1.0)
                                (#(/ (Math/round (* % 1000.0)) 1000.0)))}))))
         (sort-by (comp - :hhi))
         vec)))

(defn- tier-depth
  "node から到達可能な supplier 連鎖の最大深さ (DFS、循環は stack で防ぐ)。
  adjacency = {node [next-nodes…]}。"
  [adjacency node]
  (letfn [(depth [n stack]
            (if (contains? stack n)
              0                                   ; 循環は打ち切り
              (let [nexts (get adjacency n [])]
                (if (empty? nexts)
                  0
                  (->> nexts
                       (map #(inc (depth % (conj stack n))))
                       (reduce max 0))))))]
    (depth node #{})))

(defn tier-depths
  "全ノードの tier-depth を depth>0 のみ、深い順に返す。"
  [adjacency]
  (->> (keys adjacency)
       (map (fn [n] [n (tier-depth adjacency n)]))
       (filter (fn [[_ d]] (pos? d)))
       (sort-by (comp - second))
       vec))
