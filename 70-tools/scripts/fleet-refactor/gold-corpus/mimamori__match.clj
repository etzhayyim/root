;; ported from 20-actors/mimamori/methods/match.py — gold reference (Fable)
;; mimamori offer-matching cell (ADR-2606112300 §D4)。
;; 誰の保持者でもない人間を作らない — unkept な各 member に covenant offer を1件ずつ直接届ける。
;;   G5  global person view を出さない — 戻り値は aggregate-only (count)。
;;   G3  cooldown 尊重; offer は OFFER — 断っても無視しても penalty なし。
;;   cap  各 keeper は最大 max-kept の active+offered bond — keeping は queue でなく covenant。
;; Deterministic: candidates はソート、assignment は least-loaded への round-robin。乱数/時計なし。
;;
;; engine は純データ {:state {bond status} :kept {bond keeper}} + 注入操作で表す。
;;   load-of    (fn [engine did] → int)
;;   offer!     (fn [engine keeper member] → engine')  ; cooldown 時は ex-info {:cooldown true}
(ns mimamori.methods.match)

(def max-kept 2)  ; bond (active + standing offer) a keeper may carry

(defn- kept-or-offered [engine]
  (set (for [[bid st] (:state engine)
             :when (contains? #{:active :offered} st)]
         (get-in engine [:kept bid]))))

(defn match-cycle
  "1 マッチングパス: capacity が許す限り unkept member 全員に keeper を offer。
  engine を offer 発行で更新し、aggregate-only summary を返す。"
  [engine roster {:keys [load-of offer!]}]
  (let [members (sort (set roster))
        covered (kept-or-offered engine)
        unkept (remove covered members)]
    (loop [eng engine
           [m & more] unkept
           offers 0, skip-cooldown 0, skip-capacity 0]
      (if (nil? m)
        {:engine eng
         :summary {:unkept-before (count unkept)
                   :offers-emitted offers
                   :skipped-cooldown skip-cooldown
                   :skipped-capacity skip-capacity}}
        (let [;; least-loaded willing keeper、決定的順序、自己保持しない
              keepers (->> members
                           (filter #(and (not= % m) (< (load-of eng %) max-kept)))
                           (sort-by (juxt #(load-of eng %) identity)))
              ;; 最初に offer 成功する keeper を探す (cooldown は次へ)
              result (reduce (fn [_ k]
                               (try
                                 (reduced {:engine (offer! eng k m) :placed true})
                                 (catch clojure.lang.ExceptionInfo e
                                   (if (:cooldown (ex-data e))
                                     nil           ; この pair は休む — 次の keeper
                                     (throw e)))))
                             nil keepers)]
          (cond
            (:placed result)
            (recur (:engine result) more (inc offers) skip-cooldown skip-capacity)
            (seq keepers)   ; 候補は居たが全員 cooldown
            (recur eng more offers (inc skip-cooldown) skip-capacity)
            :else           ; 候補なし (capacity)
            (recur eng more offers skip-cooldown (inc skip-capacity))))))))
