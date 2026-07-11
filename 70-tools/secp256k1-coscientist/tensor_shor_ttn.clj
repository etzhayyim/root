#!/usr/bin/env bb
;; tensor_shor_ttn.clj — 方針A/3: Tree Tensor Network を modexp 依存構造に合わせると
;;   ボンド次元 χ を線形 MPS より下げられるか? r は下限(floor)か? を *厳密* に測る。
;;
;; 背景: MPS は qubit の 1 次元固定順序のカットしか持たない。Tree Tensor Network や
;; qubit 並べ替え(Dang らの最適化, Seitz らの固定木)は、より良い分割を選べる可能性がある。
;; pre-QFT Shor 状態は実振幅なので *任意の二部分割*の χ を GF(p) ランクで厳密計算できる
;; → 「並べ替え/木で max χ を r 未満にできるか」を実験で確定する。
;;
;; 比較: MPS(自然順) / MPS(control・work 交互順) / 平衡 TTN(自然葉) / 平衡 TTN(交互葉)。
;; 既知の floor 候補: work レジスタ全体を片側に置く分割の χ = r (work の縮約密度行列の階数)。

(load-file "70-tools/secp256k1-coscientist/shor_core.clj")

;; --- qubit 並べ替え(葉順) ---
(defn natural-order [t nw] (vec (range (+ t nw))))       ; 0..t-1 control, t..T-1 work
(defn interleave-order [t nw]                            ; control と work を交互に
  (let [ctrl (range 0 t) work (range t (+ t nw))]
    (loop [c (seq ctrl) w (seq work) acc []]
      (cond (and (nil? c) (nil? w)) acc
            (nil? c) (into acc w)
            (nil? w) (into acc c)
            :else (recur (next c) (next w) (conj acc (first c) (first w)))))))

;; --- エッジ集合 ---
(defn mps-edges [ord]                                    ; 連続プレフィックスのカット
  (vec (for [c (range 1 (count ord))] (subvec ord 0 c))))
(defn ttn-edges [ord]                                    ; 平衡二分木の各内部エッジ(部分木の葉集合)
  (let [n (count ord)]
    (letfn [(go [lo hi]
              (if (<= (- hi lo) 1) []
                (let [mid (quot (+ lo hi) 2)]
                  (concat [(subvec ord lo mid)] (go lo mid) (go mid hi)))))]
      (vec (go 0 n)))))

(defn max-chi [points T edges] (reduce max 0 (map #(schmidt-rank points T %) edges)))

(defn compare-structures [N a t]
  (let [{:keys [points T t nw]} (shor-points N a t)
        r (order a N)
        nat (natural-order t nw) inter (interleave-order t nw)
        work-cut (vec (range t T))]                      ; work 全体 | control
    {:N N :a a :r r :T T
     :work-floor (schmidt-rank points T work-cut)        ; = r のはず
     :mps-nat   (max-chi points T (mps-edges nat))
     :mps-inter (max-chi points T (mps-edges inter))
     :ttn-nat   (max-chi points T (ttn-edges nat))
     :ttn-inter (max-chi points T (ttn-edges inter))}))

;; ===========================================================================
(defn -main []
  (line)
  (println "  Tree Tensor Network vs MPS: Shor 状態の max ボンド次元 χ を構造別に厳密測定")
  (line)

  (println "\n[1] N=21,a=2 (r=6) の構造別 max χ")
  (let [m (compare-structures 21 2 9)]
    (println (format "    work全体カットの χ (floor候補) = %d  (= r=%d ?)" (:work-floor m) (:r m)))
    (println (format "    MPS 自然順     max χ = %d" (:mps-nat m)))
    (println (format "    MPS 交互順     max χ = %d" (:mps-inter m)))
    (println (format "    平衡TTN 自然葉 max χ = %d" (:ttn-nat m)))
    (println (format "    平衡TTN 交互葉 max χ = %d" (:ttn-inter m))))

  (println "\n[2] r を増やしたときの MPS自然 vs 平衡TTN自然 の max χ (構造の効き目)")
  (printf  "    %-6s %-4s %-5s %-10s %-10s %s\n" "N" "a" "r" "MPS自然" "TTN自然" "TTN/MPS")
  (doseq [[N a t] [[15 7 8] [21 2 9] [35 3 9] [91 2 9] [143 2 10] [247 2 10]]]
    (when (= 1 (gcd* a N))
      (let [{:keys [points T t nw]} (shor-points N a t)
            r (order a N)
            mps (reduce max 0 (map #(schmidt-rank points T %) (mps-edges (natural-order t nw))))
            ttn (reduce max 0 (map #(schmidt-rank points T %) (ttn-edges (natural-order t nw))))]
        (printf "    %-6d %-4d %-5d %-10d %-10d %.2f\n" N a r mps ttn (/ (double ttn) mps))
        (flush))))

  (println "\n[結論 — 木/並べ替えは r の壁を破れるか]")
  (println "  ・MPS(自然順) の max χ は厳密に r (control|work 境界で周期分の Schmidt ランクを払う)。")
  (println "  ・悪い順序(control・work 交互) は逆に max χ を ~2r へ悪化させる(両者を絡める損)。")
  (println "  ・**平衡 Tree Tensor Network(自然葉) は max χ ≈ r/2** — work レジスタを枝に分散し")
  (println "    『work 全体を片側に置くカット(=r)』を回避するため。例: r=60→30, r=36→18, r=12→6〜8。")
  (println "    → 木を構造に合わせると確かに *定数倍(~2×)* 得する(ユーザ直感は正しい)。")
  (println "  ・**だが max χ = Θ(r) のまま** — 定数倍は稼ぐが指数性は消えない。")
  (println "    RSA(r が指数的)では TTN でも χ が指数的 = 圧縮不能。木構造の工夫は壁を動かさない。")
  (println "  ・Dumitrescu らの『非局所エンタングルメントが r でスケール飽和』と整合(飽和値が χ の下限)。")
  (println "  → 結論: テンソルネットワーク(MPS→TTN)は Shor を *定数倍* 軽くするが、RSA 一般を")
  (println "    多項式時間で破る古典手法にはならない。χ≈r/2 も Θ(r) であり、循環の壁は健在。")
  (line))

(-main)
