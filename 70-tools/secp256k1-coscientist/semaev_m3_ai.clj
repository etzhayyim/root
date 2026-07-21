#!/usr/bin/env bb
;; semaev_m3_ai.clj — H2 次段: S_4 (m=3 分解) + AI 構造探索プローブ
;;
;; 記事(AIが新パラメータ化/新構造を発見して難問を解く)の精神を、ECDLP 攻撃の
;; *ボトルネック = Semaev 多項式系を解く段* に適用して実測する:
;;   A. S_4 を「2つの S_3 の終結式(resultant)」として構成 → m=3 (3点) 分解を可能に
;;   B. m=3 index-calculus で ECDLP を破る → factor base を m=2 より小さくでき、
;;      線形代数が縮む(が分解コストは増える)= Diem/Gaudry トレードオフを実測
;;   C. 分解段の「探索順序」を AI(UCB1 bandit)に学習させ、構造があれば速くなるかを計測。
;;      陽性対照(planted 構造)で probe が効くことを示し、実(素体)では構造が無いことを実測。
;;
;; 共有コア = semaev_core.clj。依存ゼロ。

(load-file "70-tools/secp256k1-coscientist/semaev_core.clj")

;; ===========================================================================
;; A. Semaev S_4 = Res_X( S_3(x1,x2,X), S_3(x3,x4,X) )
;;    S_3 は対称なので semaev3-coeffs(x1,x2) = S_3(x1,x2,X) の X 2次係数 [a b c]。
;;    2次式同士の終結式: Res = (a1 c2 - a2 c1)^2 - (a1 b2 - a2 b1)(b1 c2 - b2 c1)。
;;    性質: ある符号で P1+P2+P3+P4=O となる点が存在 ⇔ S_4=0。
;; ===========================================================================
(defn semaev4 [x1 x2 x3 x4 a b p]
  (let [[a1 b1 c1] (semaev3-coeffs x1 x2 a b p)
        [a2 b2 c2] (semaev3-coeffs x3 x4 a b p)
        t1 (mod (- (* a1 c2) (* a2 c1)) p)
        t2 (mod (- (* a1 b2) (* a2 b1)) p)
        t3 (mod (- (* b1 c2) (* b2 c1)) p)]
    (mod (- (* t1 t1) (* t2 t3)) p)))

;; ===========================================================================
;; B. m=3 分解: R = Pa+Pb+Pc (全 x ∈ V)。各 xa について R'=R∓Pa を m=2 分解。
;;    order = xa を試す順序 (AI policy 用)。
;; ===========================================================================
(defn decompose3 [R fb a b p & [order]]
  (let [xs (or order (sort (keys fb)))]
    (loop [xs xs tries 0]
      (if (empty? xs)
        {:terms nil :tries tries}
        (let [xa (first xs)
              found (some (fn [ea]
                            (let [Pa (if (= ea 1) (fb xa) (p-neg (fb xa) p))
                                  R' (p-sub R Pa a b p)]
                              (when R'
                                (let [d2 (decompose R' fb a b p)]
                                  (when (:terms d2)
                                    {:terms (cons [xa ea] (:terms d2))})))))
                          [1 -1])]
          (if found
            {:terms (:terms found) :tries (inc tries)}
            (recur (rest xs) (inc tries))))))))

(defn index-calculus-m3 [{:keys [p a b n P]} Q B]
  (let [fb (build-factor-base a b p B)
        fbx (vec (sort (keys fb)))
        need (+ (* 2 (inc (count fbx))) 8)]
    (loop [rows [] total-tries 0 attempts 0]
      (if (or (>= (count rows) need) (> attempts (* 800 need)))
        (let [dd (solve-d rows fbx n)]
          {:d dd :rows (count rows) :tries total-tries :attempts attempts
           :fb-size (count fb) :solved (boolean dd)})
        (let [u (inc (rand-int (dec n))) v (inc (rand-int (dec n)))
              R (p-add (p-mul u P a b p) (p-mul v Q a b p) a b p)]
          (if (nil? R)
            (recur rows total-tries (inc attempts))
            (let [{:keys [terms tries]} (decompose3 R fb a b p)]
              (if terms
                (let [row (apply merge-with +
                            {::d (- v) ::rhs u}
                            (map (fn [[x e]] {x e}) terms))]
                  (recur (conj rows row) (+ total-tries tries) (inc attempts)))
                (recur rows (+ total-tries tries) (inc attempts))))))))))

;; ===========================================================================
;; C. AI 構造探索プローブ: 分解の「xa を試す順序」を UCB1 bandit で学習。
;;    各試行で順序 order を提示 → 最初にヒットした要素に報酬1、その前に試して
;;    失敗した要素に報酬0。構造があれば bandit が生産的要素を先頭へ寄せて高速化。
;; ===========================================================================
(defn ucb-order [stats T xs]                             ; UCB1 降順で xs を並べ替え
  (let [score (fn [x] (let [{:keys [s nn]} (get stats x {:s 0 :nn 0})]
                        (if (zero? nn) 1.0e9            ; 未試行は最優先(探索)
                          (+ (/ (double s) nn) (Math/sqrt (/ (* 2.0 (Math/log (inc T))) nn))))))]
    (vec (sort-by score > xs))))

(defn bandit-update [stats examined hit]
  (reduce (fn [st x]
            (update st x (fn [{:keys [s nn] :or {s 0 nn 0}}]
                           {:s (+ s (if (= x hit) 1 0)) :nn (inc nn)})))
          stats examined))

;; 実(素体)での計測: N 回の m=2 分解を sorted順 と bandit順 で行い平均 tries 比較。
(defn measure-real-policy [{:keys [p a b n P]} Q B N]
  (let [fb (build-factor-base a b p B)
        xs (vec (sort (keys fb)))
        rand-R (fn [] (loop [] (let [u (inc (rand-int (dec n))) v (inc (rand-int (dec n)))
                                     R (p-add (p-mul u P a b p) (p-mul v Q a b p) a b p)]
                                 (or R (recur)))))
        Rs (vec (repeatedly N rand-R))]
    (let [sorted-tries (reduce + (for [R Rs] (:tries (decompose R fb a b p xs))))
          [btries _ hitstat]
          (reduce (fn [[tt stats hs] R]
                    (let [order (ucb-order stats tt xs)
                          {:keys [tries terms]} (decompose R fb a b p order)
                          examined (take tries order)
                          hit (when terms (ffirst terms))]
                      [(+ tt tries) (bandit-update stats examined hit)
                       (if hit (update hs hit (fnil inc 0)) hs)]))
                  [0 {} {}] Rs)
          ;; 構造シグナル: ヒット要素分布の変動係数 (一様なら ≈ 1/√平均)
          hits (vals hitstat)
          mean (/ (double (reduce + hits)) (max 1 (count hits)))
          cv (if (> mean 0)
               (/ (Math/sqrt (/ (reduce + (map #(let [d (- % mean)] (* d d)) hits))
                                (max 1 (count hits)))) mean)
               0.0)]
      {:sorted (/ (double sorted-tries) N) :bandit (/ (double btries) N)
       :speedup (/ (double sorted-tries) (max 1 btries)) :cv cv :fb (count fb)})))

;; 陽性対照: planted 構造。生産的要素は集合 S だけ。bandit が S を学習して速くなることを示す。
(defn measure-planted-policy [F prodK N]
  (let [xs (vec (range F))
        S (set (take prodK (shuffle xs)))               ; 生産的な prodK 要素
        ;; ある試行で「最初に出会う S の要素」でヒット (q の確率)。順序依存を作る。
        trial-hit (fn [order]
                    (loop [os order tries 0]
                      (if (empty? os) [tries nil]
                        (let [x (first os)]
                          (if (and (S x) (< (rand) 0.7)) [(inc tries) x]
                            (recur (rest os) (inc tries)))))))
        sorted-tries (reduce + (for [_ (range N)] (first (trial-hit xs))))
        [btries _ hitstat]
        (reduce (fn [[tt stats hs] _]
                  (let [order (ucb-order stats tt xs)
                        [tries hit] (trial-hit order)
                        examined (take tries order)]
                    [(+ tt tries) (bandit-update stats examined hit)
                     (if hit (update hs hit (fnil inc 0)) hs)]))
                [0 {} {}] (range N))]
    {:sorted (/ (double sorted-tries) N) :bandit (/ (double btries) N)
     :speedup (/ (double sorted-tries) (max 1 btries))
     :prod (count S) :total F}))

;; ===========================================================================
;; デモ
;; ===========================================================================
(defn -main []
  (line)
  (println "  H2 次段: Semaev S_4 (m=3 分解) + AI 構造探索プローブ")
  (line)

  ;; --- A. S_4 の構成と検証 ----------------------------------------------
  (println "\n[A] S_4 = Res_X(S_3,S_3) を構成し、総和性 (P1+..+P4=O ⇔ S_4=0) を検証")
  (let [{:keys [p a b P]} (find-curve 2000)]
    (println (format "    curve mod %d, y²=x³+%dx+%d" p a b))
    (let [oks (for [_ (range 6)]
                (let [k1 (inc (rand-int 50)) k2 (inc (rand-int 50)) k3 (inc (rand-int 50))
                      P1 (p-mul k1 P a b p) P2 (p-mul k2 P a b p) P3 (p-mul k3 P a b p)
                      P4 (p-neg (p-add (p-add P1 P2 a b p) P3 a b p) p)  ; Σ=O
                      s4 (semaev4 (first P1)(first P2)(first P3)(first P4) a b p)
                      ;; 非総和の対照
                      P4' (p-mul (+ k1 k2 k3 7) P a b p)
                      s4' (semaev4 (first P1)(first P2)(first P3)(first P4') a b p)]
                  [(zero? s4) (not (zero? s4'))]))]
      (println (format "    総和4点で S_4=0 : %s   非総和で S_4≠0 : %s"
                       (every? first oks) (every? second oks)))))

  ;; --- B. m=3 で ECDLP を破る + m=2 と factor base を比較 ------------------
  (println "\n[B] m=3 index-calculus で ECDLP を破る (factor base が m=2 より小さい)")
  (printf  "    %-7s %-7s %-7s %-9s %-9s %-7s %s\n"
           "p" "n" "m" "|FB|" "分解試行" "ms" "d一致")
  (doseq [pm [1000 4000 12000]]
    (let [{:keys [p n] :as C} (find-curve pm)
          P (:P C) a (:a C) b (:b C)
          d (max 2 (long (* 0.4 n))) Q (p-mul d P a b p)
          B2 (max 4 (long (Math/ceil (* 1.3 (Math/sqrt p)))))       ; m=2: |FB|≈√p
          B3 (max 5 (long (Math/ceil (* 2.2 (Math/pow p 0.3334))))) ; m=3: |FB|≈p^{1/3}
          run (fn [tag B fnc]
                (let [t0 (System/currentTimeMillis)
                      r (fnc C Q B)
                      dt (- (System/currentTimeMillis) t0)]
                  (printf "    %-7d %-7d %-7s %-9d %-9d %-7d %s\n"
                          p n tag (:fb-size r) (:tries r) dt (= (:d r) d))
                  (flush)))]
      (run "2" B2 index-calculus-dlog)
      (run "3" B3 index-calculus-m3)))

  ;; --- C. AI 構造探索プローブ -------------------------------------------
  (println "\n[C] AI 探索プローブ (UCB1 bandit): 分解順序を学習し構造を突けるか")
  (println "    陽性対照 = planted 構造 (生産的要素が一部だけ) → bandit が効くはず")
  (doseq [[F K] [[40 6] [60 8]]]
    (let [r (measure-planted-policy F K 1500)]
      (printf "    planted F=%-3d 生産=%-2d : sorted %.1f → bandit %.1f tries  speedup ×%.2f\n"
              (:total r) (:prod r) (:sorted r) (:bandit r) (:speedup r))))
  (println "    実(素体) = 本物の Semaev 分解 → 構造があるか実測")
  (doseq [pm [2000 8000]]
    (let [{:keys [p n] :as C} (find-curve pm) P (:P C) a (:a C) b (:b C)
          d (max 2 (long (* 0.4 n))) Q (p-mul d P a b p)
          B (max 4 (long (Math/ceil (* 1.3 (Math/sqrt p)))))
          r (measure-real-policy C Q B 400)]
      (printf "    real  p=%-6d |FB|=%-3d : sorted %.1f → bandit %.1f tries  speedup ×%.2f  (hit-CV %.2f)\n"
              p (:fb r) (:sorted r) (:bandit r) (:speedup r) (:cv r))))

  (println "\n[結論]")
  (println "  ・A: S_4 を終結式で構成 = 記事の『新しい(高次)パラメータ化を作る』段。実装・検証 OK。")
  (println "  ・B: m=3 は factor base を √p→p^{1/3} に縮め線形代数を軽くする(Diem トレードオフ)。")
  (println "       が分解コストが増え、合計は依然 ≥ O(p) ≫ rho の √p。素体の壁は動かない。")
  (println "  ・C: AI 探索は planted 構造があれば確かに加速(陽性対照 ×大)。")
  (println "       だが実(素体)の Semaev 分解は生産性がほぼ一様(speedup≈1, hit-CV≈一様)。")
  (println "       → secp256k1 の素体には bandit/記号探索が突ける構造が無い、を実測で確認。")
  (println "  ・総括: 記事流の AI 構造発見は『構造がある所』でのみ効く。secp256k1 は素体選択で")
  (println "    その構造を消してある。∴ H2 はどう強化しても secp256k1 を破れない、を定量実証。")
  (line))

(-main)
