#!/usr/bin/env bb
;; tensor_shor.clj — Shor 前段状態のテンソルネットワーク圧縮性を *厳密に* 測る
;;
;; 仮説(ユーザ提案): 「ある N,a では Shor 状態が低ランク構造を持ち、特殊ケースの
;; 古典周期発見になりうる。だが χ(ボンド次元) は周期 r で決まり、χ を抑えられる⟺
;; r が小さい⟺既に周期をほぼ知っている、という危険な循環がある」。これを実測する。
;;
;; 方法: 最終 QFT 前の Shor 波動関数
;;   |ψ⟩ = (1/√Q) Σ_{x=0}^{Q-1} |x⟩_control ⊗ |a^x mod N⟩_work
;; は実振幅(0/√Q)なので、任意のカットをまたぐ Schmidt ランク(=MPSボンド次元 χ)は
;; 0/1 二部行列のランクに等しい → GF(p) ガウス消去で *厳密に* 計算できる(SVD不要)。
;;
;; 既知: control|work カットの χ = r (周期)。本コードは control 内部の各カットでも
;; χ を測り、χ のプロファイルと max χ vs r の関係を出す。依存ゼロ・bb。

;; ---------------------------------------------------------------------------
;; 数論 + GF(p) スパース・ランク
;; ---------------------------------------------------------------------------
(defn modpow [a e m] (.longValue (.modPow (biginteger a) (biginteger e) (biginteger m))))
(defn gcd* [a b] (if (zero? b) a (recur b (mod a b))))
(defn nbits [n] (.bitLength (biginteger (max 1 n))))
(defn order [a N]                                        ; ord_N(a), gcd(a,N)=1 前提
  (loop [x 1 v (mod a N)] (if (= v 1) x (recur (inc x) (mod (* v a) N)))))

(def ^long PR 2147483647)                                ; 2^31-1 (素数) で実ランクを再現
(defn minv [a] (.longValue (.modInverse (biginteger (mod a PR)) (biginteger PR))))

(defn row-sub [row prow f]                               ; row - f*prow (mod PR), prow[lead]=1
  (persistent!
    (reduce (fn [acc [c x]]
              (let [nv (mod (- (long (get acc c 0)) (* f (long x))) PR)]
                (if (zero? nv) (dissoc! acc c) (assoc! acc c nv))))
            (transient row) prow)))

(defn reduce-row [row pivots]
  (loop [row row]
    (if (empty? row) row
      (let [col (reduce min (keys row))]
        (if-let [prow (get pivots col)]
          (recur (row-sub row prow (long (get row col))))
          row)))))

(defn gf-rank [rows]                                     ; rows = seq of {col->1} → ランク
  (loop [rs rows pivots {} rank 0]
    (if (empty? rs)
      rank
      (let [r (reduce-row (first rs) pivots)]
        (if (empty? r)
          (recur (rest rs) pivots rank)
          (let [col (reduce min (keys r))
                inv (minv (get r col))
                nr  (into {} (map (fn [[c x]] [c (mod (* (long x) inv) PR)]) r))]
            (recur (rest rs) (assoc pivots col nr) (inc rank))))))))

;; ---------------------------------------------------------------------------
;; pre-QFT Shor 状態の各カットでのボンド次元 χ
;;   qubit 順: control x の上位→下位 (t bit) ++ work y の上位→下位 (nw bit)
;;   グローバル添字 I = x·2^nw + y。カット c は上位 c qubit | 残りで分割。
;; ---------------------------------------------------------------------------
(defn bond-profile [N a t]
  (let [nw (nbits (dec N))                               ; y ∈ [0,N) を表す bit 数
        Q  (bit-shift-left 1 t)
        T  (+ t nw)
        pts (mapv (fn [x] (+ (* x (bit-shift-left 1 nw)) (modpow a x N))) (range Q))]
    (vec (for [c (range 1 T)]
           (let [sh (- T c) mask (dec (bit-shift-left 1 sh))
                 rowmap (reduce (fn [m I]
                                  (let [l (bit-shift-right I sh) r (bit-and I mask)]
                                    (update m l #(assoc (or % {}) r 1))))
                                {} pts)]
             {:cut c :region (if (< c t) :control (if (= c t) :ctrl|work :work))
              :chi (gf-rank (vals rowmap))})))))

(defn analyze [N a t]
  (let [r (order a N)
        prof (bond-profile N a t)
        chi-cw (:chi (first (filter #(= (:cut %) t) prof)))
        chi-ctrl (reduce max 0 (map :chi (filter #(= :control (:region %)) prof)))
        chi-max (reduce max 0 (map :chi prof))]
    {:N N :a a :t t :r r :Q (bit-shift-left 1 t)
     :chi-ctrl|work chi-cw :chi-ctrl-internal-max chi-ctrl :chi-max chi-max :prof prof}))

;; ---------------------------------------------------------------------------
;; 方針B: 全状態を保持せず QFT 後の確率 P(m) のピークだけ使い周期 r を復元→因数分解
;;   P(m) = Σ_y |(1/Q) Σ_{x:a^x=y} ω^{xm}|²  (ω=e^{2πi/Q})
;;   ピーク m ≈ sQ/r を連分数展開して r を得る。コスト ∝ Q·r (= χ に比例)。
;; ---------------------------------------------------------------------------
(defn dft-power [N a t]                                  ; P(m) を全 m について
  (let [Q (bit-shift-left 1 t)
        ;; work 値 y ごとに control 添字集合 {x: a^x=y}
        groups (reduce (fn [m x] (update m (modpow a x N) (fnil conj []) x)) {} (range Q))
        two-pi-over-Q (/ (* 2.0 Math/PI) Q)]
    (vec (for [m (range Q)]
           (reduce (fn [acc xs]                          ; Σ_y |Σ_x ω^{xm}|²
                     (let [[re im] (reduce (fn [[r i] x]
                                             (let [th (* two-pi-over-Q (mod (* x m) Q))]
                                               [(+ r (Math/cos th)) (+ i (Math/sin th))]))
                                           [0.0 0.0] xs)]
                       (+ acc (/ (+ (* re re) (* im im)) (* (double Q) Q)))))
                   0.0 (vals groups))))))

(defn convergents [m Q]                                  ; m/Q の連分数収束分母 = r 候補
  (loop [n m d Q pm1 1 pm2 0 qm1 0 qm2 1 acc []]
    (if (zero? d)
      acc
      (let [a (quot n d) p (+ (* a pm1) pm2) q (+ (* a qm1) qm2)]
        (recur d (- n (* a d)) p pm1 q qm1 (conj acc q))))))

(defn recover-order [N a t]                              ; ピーク→連分数→r (order を使わず復元)
  (let [Q (bit-shift-left 1 t)
        P (dft-power N a t)
        peaks (->> (range 1 Q) (sort-by P >) (take (* 2 (nbits N))))  ; 上位ピーク m
        cands (for [m peaks q (convergents m Q)
                    :when (and (> q 1) (< q N) (= 1 (modpow a q N)))] q)]
    (when (seq cands) (reduce min cands))))

(defn factor-via-order [N a r]
  (when (and r (even? r))
    (let [h (modpow a (quot r 2) N)]
      (when (not= h (dec N))                             ; a^{r/2} ≢ -1
        (let [g1 (gcd* (mod (dec h) N) N) g2 (gcd* (mod (inc h) N) N)]
          (->> [g1 g2] (filter #(and (< 1 %) (< % N))) first))))))

;; ===========================================================================
;; デモ
;; ===========================================================================
(defn line [] (println (apply str (repeat 78 "─"))))

(defn -main []
  (line)
  (println "  Shor 前段波動関数のテンソルネットワーク圧縮性 (ボンド次元 χ を厳密測定)")
  (line)

  ;; [1] 1例のカット・プロファイル: どこで χ がピークか
  (println "\n[1] N=21, a=2 のカット別ボンド次元プロファイル (χ_k)")
  (let [{:keys [r prof Q]} (analyze 21 2 9)]
    (println (format "    N=21, a=2, 周期 r=ord=%d, 制御 t=9 (Q=%d)" r Q))
    (print   "    χ profile: ")
    (doseq [{:keys [chi region]} prof]
      (print (str chi (when (= region :ctrl|work) "*") " ")))
    (println "\n    (* = control|work カット。control 内部の各カットの χ も表示)"))

  ;; [2] スケーリング: 複数 (N,a) で r と χ の関係 = 仮説の核心
  (println "\n[2] max χ は周期 r で決まるか (圧縮性 ⟺ r が小さい を実測)")
  (printf  "    %-6s %-5s %-6s %-7s %-14s %-12s %s\n"
           "N" "a" "r" "Q" "χ(ctrl|work)" "χ(ctrl内最大)" "max χ")
  (doseq [[N a t] [[15 2 8] [15 7 8] [15 4 8]
                   [21 2 9] [21 5 9]
                   [33 2 9] [33 5 9]
                   [35 2 9] [35 3 9]]]
    (when (= 1 (gcd* a N))
      (let [{:keys [r chi-ctrl|work chi-ctrl-internal-max chi-max Q]} (analyze N a t)]
        (printf "    %-6d %-5d %-6d %-7d %-14d %-12d %d\n"
                N a r Q chi-ctrl|work chi-ctrl-internal-max chi-max)
        (flush))))

  ;; [3] 方針B: QFT ピークだけで周期復元 → 因数分解 (全状態を保持しない)
  (println "\n[3] 方針B: QFT のピークから周期 r を復元し N を因数分解 (order() を使わず)")
  (printf  "    %-6s %-5s %-6s %-10s %-10s %s\n" "N" "a" "t" "復元 r" "真の r" "因数分解")
  (doseq [[N a t] [[15 7 8] [15 2 8] [21 2 9] [33 5 9] [35 3 9]]]
    (when (= 1 (gcd* a N))
      (let [r (recover-order N a t) rt (order a N)
            f (factor-via-order N a r)]
        (printf "    %-6d %-5d %-6d %-10s %-10d %s\n"
                N a t (str r) rt
                (if f (format "%d = %d × %d" N f (quot N f)) "(r 奇 or a^{r/2}=-1 → 別 a)"))
        (flush))))
  (println "    → 全 2^(t+nw) 振幅を持たず、ピーク m だけで r を取り出せる(方針B)。")
  (println "      ただしコストは Q·r ∝ χ。r が指数的(RSA)なら結局この縮約も重い。")

  (println "\n[結論 — 危険な循環の実測]")
  (println "  ・control|work カットの χ は厳密に r に一致 (Schmidt ランク = 周期)。")
  (println "  ・control 内部のカットでも max χ は r で頭打ち(非局所だが r でバウンド)。")
  (println "  ・∴ TN で圧縮可能(χ小) ⟺ r が小さい ⟺ *既に周期をほぼ知っている*。")
  (println "    周期 r が大きい(RSA の一般ケース)= χ も大きい = 圧縮不能 = 状態ベクトル法に回帰。")
  (println "  ・到達可能な小 N では r が小さく χ も小さい(=今回測れた)。χ が爆発する領域は")
  (println "    N を大きくしないと現れず、その N は状態を作るのが因数分解そのものと同じ難しさ。")
  (println "  → ユーザ提案の『圧縮できれば周期が分かる/圧縮には周期構造が要る』循環を定量確認。")
  (line))

(-main)
