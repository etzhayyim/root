;; ported from 20-actors/abaki/methods/react_router.py — gold reference (Fable)
;; abaki — React & Route-Around 実行。chokepoint で blocked な vendor を safe provider へ迂回。
;; 原実装は print 副作用の連なり。Clojure では「決定をデータで返す純関数」+ 薄い report に分ける。
(ns abaki.methods.react-router)

(defn route-compute
  "compute routing 決定。requested vendor が blocked なら safe な compute provider へ迂回。
  → {:status :permitted/:routed/:failed-secure …}。副作用なし。"
  [routing-policy requested-vendor]
  (let [blocked (set (map :id (:blocked-entities routing-policy)))
        safe (->> (:safe-entities routing-policy)
                  (filter #(= (:domain %) "compute"))
                  (mapv :id))]
    (cond
      (not (contains? blocked requested-vendor))
      {:status :permitted :vendor requested-vendor}
      (seq safe)
      {:status :routed :from requested-vendor :to (first safe)
       :reason "high chokepoint index (monopolistic)"}
      :else
      {:status :failed-secure :from requested-vendor
       :reason "no safe compute providers — failing securely"})))

;; domain → 迂回先 actor + 説明 (survival tree の分岐)
(def survival-branches
  {"biology"   {:fallback "suki"    :note "F1 seeds blocked → local heirloom seed bank"}
   "logistics" {:fallback "wadachi" :note "centralized logistics blocked → autonomous mesh delivery"}
   "compute"   {:fallback "ameno"   :note "proprietary API blocked → WebGPU local inference"}})

(defn survival-tree
  "blocked entity の domain 集合から、活性化される survival 分岐の列を返す。"
  [routing-policy]
  (let [blocked-domains (set (map :domain (:blocked-entities routing-policy)))]
    (for [[domain branch] survival-branches
          :when (contains? blocked-domains domain)]
      (assoc branch :domain domain))))

(defn react
  "ポリシ全体に対する route-around 決定をまとめて返す (compute + survival)。"
  [routing-policy requested-vendor]
  {:compute (route-compute routing-policy requested-vendor)
   :survival (vec (survival-tree routing-policy))})
