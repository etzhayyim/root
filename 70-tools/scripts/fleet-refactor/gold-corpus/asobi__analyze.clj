;; ported from 20-actors/asobi/methods/analyze.py — gold reference (Fable)
;; asobi 遊び — edge-primary participation/enclosure analyzer。ADR-2606073200。
;; kotoba-EDN play/expression graph (:organism/* node + :en/* 縁) を読み、aggregate-first で
;; PARTICIPATION が開いている所と ENCLOSURE が telos を gate する所を surface し OPENING へ routed。
;;
;; CONSTITUTIONAL:
;;   N1/G2 — edge-primary。karma は 縁 (:en/access-load) のみ。ノードの participation-openness は
;;     incident OPENING 縁 の INTEGRAL — READ 時計算で、保存された per-work score ではない。
;;   G1 — PARTICIPATION/ACCESS map であって engagement/popularity ranking ではない。
;;   N3 — non-adjudicating。access カテゴリは DISCLOSED fact で asobi の裁定ではない。
;;
;; EDN 読み取りは ake.methods.edn を再利用する想定 (ここでは load-fn 注入)。
(ns asobi.methods.analyze)

;; disclosed access category → representative openness weight (裁定でなく schema の写し)
(def access-weight
  {:public-domain 1.0 :open-license 0.9 :free-gratis 0.7
   :ticketed 0.4 :paywalled 0.2 :proprietary 0.1})

(def opening-kinds #{:open-access :teaches :participates :hosts :performs})
(def enclosure-kinds #{:encloses})

(defn load-graph
  "asobi EDN forms から [nodes-by-id edges] を取り出す。forms は読み取り済み EDN ベクタ。"
  [forms]
  (reduce (fn [[nodes edges] f]
            (cond
              (not (map? f)) [nodes edges]
              (:organism/id f) [(assoc nodes (:organism/id f) f) edges]
              (and (:en/from f) (:en/to f)) [nodes (conj edges f)]
              :else [nodes edges]))
          [{} []] forms))

(defn analyze
  "Edge-primary 積分 (READ 時計算・transient — N1/G2)。
    :openness     {node Σ(inbound OPENING load × bearer の access weight)}
    :enclosure    {node Σ(inbound :encloses load)}
    :enclosure-out{holder Σ(outbound :encloses load)}"
  [nodes edges]
  (reduce
   (fn [acc e]
     (let [kind (:en/kind e)
           load (double (or (:en/access-load e) 0.0))
           src (:en/from e), dst (:en/to e)]
       (cond
         (contains? opening-kinds kind)
         (let [w (get access-weight (get-in nodes [dst :work/access]) 0.6)]
           (update-in acc [:openness dst] (fnil + 0.0) (* load w)))
         (contains? enclosure-kinds kind)
         (-> acc
             (update-in [:enclosure dst] (fnil + 0.0) load)
             (update-in [:enclosure-out src] (fnil + 0.0) load))
         :else acc)))
   {:openness {} :enclosure {} :enclosure-out {}}
   edges))

(defn rank
  "{node value} を value 降順で上位 limit 件、[node label value] へ。"
  [m nodes limit]
  (->> (sort-by (comp - val) m)
       (take limit)
       (mapv (fn [[nid v]]
               [nid (get-in nodes [nid :organism/label] nid) v]))))
