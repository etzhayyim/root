#!/usr/bin/env bb
;; semaev_index_calculus.clj — H2: Semaev 総和多項式 × index-calculus による ECDLP 解析
;;
;; Co-Scientist H2 仮説の実証。小さい素体 E(F_p) 上で:
;;   1. Semaev S_3 を「総和多項式」として実装 (P1+P2+P3=O ⇔ S_3(x1,x2,x3)=0)
;;   2. factor base (x 座標が小集合 V にある点) を作る
;;   3. ランダム R=uP+vQ を Semaev で R=Pa+Pb に分解 → 線形関係を収集
;;   4. mod n ガウス消去で離散対数を解き d を復元 → dP==Q を検証
;;   5. *コストを計測* し「素体では index-calculus が √n を超えない」=
;;      secp256k1 が安全な理由を実測で示す。
;;
;; 依存ゼロ。記事(AIが新パラメータ化で難問を解く)の暗号版 = 分解段階の探索コストを測る。

;; ---------------------------------------------------------------------------
;; 素体 F_p 演算 (p は小さく long に収まる)
;; ---------------------------------------------------------------------------
(defn modinv [a m] (.longValue (.modInverse (biginteger (mod a m)) (biginteger m))))
(defn mpow [b e m] (.longValue (.modPow (biginteger b) (biginteger e) (biginteger m))))
(defn legendre [a p] (let [r (mpow (mod a p) (quot (dec p) 2) p)] (if (= r (dec p)) -1 r)))
(defn qr? [a p] (let [a (mod a p)] (or (zero? a) (= 1 (legendre a p)))))
;; p ≡ 3 (mod 4) のとき sqrt = a^((p+1)/4)
(defn msqrt [a p] (let [a (mod a p)] (when (qr? a p) (mpow a (quot (inc p) 4) p))))

;; 楕円曲線 y^2 = x^3 + a x + b over F_p。無限遠点 = nil。点 = [x y]。
(defn rhs [x a b p] (mod (+ (* x x x) (* a x) b) p))
(defn on-curve? [[x y] a b p] (= (mod (* y y) p) (rhs x a b p)))

(defn p-add [P Q a b p]
  (cond
    (nil? P) Q
    (nil? Q) P
    :else
    (let [[x1 y1] P [x2 y2] Q]
      (cond
        (and (= x1 x2) (= (mod (+ y1 y2) p) 0)) nil          ; P + (-P) = O
        (and (= x1 x2) (= y1 y2))
        (let [l (mod (* (+ (* 3 x1 x1) a) (modinv (mod (* 2 y1) p) p)) p)
              x3 (mod (- (* l l) (* 2 x1)) p)
              y3 (mod (- (* l (- x1 x3)) y1) p)]
          [x3 y3])
        :else
        (let [l (mod (* (- y2 y1) (modinv (mod (- x2 x1) p) p)) p)
              x3 (mod (- (* l l) x1 x2) p)
              y3 (mod (- (* l (- x1 x3)) y1) p)]
          [x3 y3])))))

(defn p-neg [P p] (when P [(first P) (mod (- (second P)) p)]))

(defn p-mul [k P a b p]
  (loop [k (long k) acc nil base P]
    (if (zero? k)
      acc
      (recur (bit-shift-right k 1)
             (if (odd? k) (p-add acc base a b p) acc)
             (p-add base base a b p)))))

;; ---------------------------------------------------------------------------
;; 曲線探索: 群位数が素数になる小曲線を見つける (Z/nZ を体にして線形代数するため)
;; ---------------------------------------------------------------------------
(defn prime? [n]
  (and (> n 1)
       (or (= n 2)
           (and (odd? n)
                (loop [i 3] (cond (> (* i i) n) true (zero? (mod n i)) false :else (recur (+ i 2))))))))

(defn curve-order [a b p]                                ; #E(F_p) = 1 + p + Σ χ(rhs(x))
  (reduce (fn [acc x] (+ acc (legendre (rhs x a b p) p)))
          (inc p) (range p)))

(defn first-point [a b p]                                ; 任意の非 O 点 (n 素数なら生成元)
  (some (fn [x] (when-let [y (msqrt (rhs x a b p) p)] (when (pos? y) [x y]))) (range p)))

(defn find-curve [pmin]
  (some (fn [p]
          (when (and (prime? p) (= 3 (mod p 4)))
            (some (fn [[a b]]
                    (let [d (mod (+ (* 4 a a a) (* 27 b b)) p)]
                      (when (not= 0 d)
                        (let [n (curve-order a b p)]
                          (when (and (prime? n) (> n 50))
                            (when-let [P (first-point a b p)]
                              {:p p :a a :b b :n n :P P}))))))
                  (for [a (range 0 7) b (range 1 9)] [a b]))))
        (iterate inc pmin)))

;; ---------------------------------------------------------------------------
;; Semaev 総和多項式 S_3 (y^2 = x^3+ax+b)
;;   S_3 = (x1-x2)^2 x3^2 - 2((x1+x2)(x1 x2 + a)+2b) x3 + ((x1 x2 - a)^2 - 4b(x1+x2))
;; 性質: ある符号で P1+P2+P3=O となる点 (xi,*) が存在 ⇔ S_3(x1,x2,x3)=0。
;; ---------------------------------------------------------------------------
(defn semaev3 [x1 x2 x3 a b p]
  (let [t (mod (- x1 x2) p)
        c2 (mod (* t t) p)
        c1 (mod (* -2 (+ (* (+ x1 x2) (+ (* x1 x2) a)) (* 2 b))) p)
        c0 (mod (- (* (- (* x1 x2) a) (- (* x1 x2) a)) (* 4 b (+ x1 x2))) p)]
    (mod (+ (* c2 x3 x3) (* c1 x3) c0) p)))

;; S_3 を「x2 についての2次式」として根を解く (x1,x3 既知)。次数2なので t=0,1,2 で補間。
(defn solve-semaev-x2 [x1 x3 a b p]
  (let [f (fn [t] (semaev3 x1 t x3 a b p))
        f0 (f 0) f1 (f 1) f2 (f 2)
        A (mod (* (- (+ f2 f0) (* 2 f1)) (modinv 2 p)) p)   ; 2次係数
        B (mod (- f1 f0 A) p)                                ; 1次係数
        C f0]                                                ; 定数項
    (if (zero? A)
      (if (zero? B) [] [(mod (* (- C) (modinv B p)) p)])     ; 線形
      (let [disc (mod (- (* B B) (* 4 A C)) p)]
        (if-let [s (msqrt disc p)]
          (let [inv2a (modinv (mod (* 2 A) p) p)]
            (distinct [(mod (* (- s B) inv2a) p) (mod (* (- (- s) B) inv2a) p)]))
          [])))))

;; ---------------------------------------------------------------------------
;; factor base: x ∈ V={0..B-1} を持つ点。各 x の canonical 点 = (x, 小さい方の y)。
;; ---------------------------------------------------------------------------
(defn build-factor-base [a b p B]
  (into {} (for [x (range B)
                 :let [y (msqrt (rhs x a b p) p)]
                 :when (and y (pos? y))]
             [x [x (min y (- p y))]])))                  ; x -> canonical point

;; R=Pa+Pb を Semaev で分解。見つかれば {:terms [[xa εa] [xb εb]] :tries k}。
;; εa,εb ∈ {1,-1}: Pa=εa·canon(xa)。relation: εa ℓ_xa + εb ℓ_xb = log(R)。
(defn decompose [R fb a b p]
  (let [xR (first R)
        xs (sort (keys fb))]
    (loop [xs xs tries 0]
      (if (empty? xs)
        {:terms nil :tries tries}
        (let [xa (first xs)
              cand (filter fb (solve-semaev-x2 xa xR a b p))  ; xb 候補 ∩ V
              hit  (some (fn [xb]
                           (let [Pa (fb xa) Pb (fb xb)]
                             (some (fn [[ea eb]]
                                     (let [A (if (= ea 1) Pa (p-neg Pa p))
                                           Bp (if (= eb 1) Pb (p-neg Pb p))]
                                       (when (= (p-add A Bp a b p) R)
                                         [[xa ea] [xb eb]])))
                                   [[1 1] [1 -1] [-1 1] [-1 -1]])))
                         cand)]
          (if hit
            {:terms hit :tries (inc tries)}
            (recur (rest xs) (inc tries))))))))

;; ---------------------------------------------------------------------------
;; mod n で d だけを解く (n 素数)。ℓ_x 列を全消去し、残った「d だけの式」から d を読む。
;; → 一部の ℓ_x が自由変数でも d が一意に定まれば復元できる。
;; rows: 各 {x coef ... ::d coef ::rhs r}。fbx: factor base の x 一覧。
;; ---------------------------------------------------------------------------
(defn solve-d [rows fbx n]
  (let [cols (vec fbx)
        F (count cols)
        tov (fn [r] (conj (mapv #(mod (get r % 0) n) cols)
                          (mod (get r ::d 0) n) (mod (get r ::rhs 0) n)))
        M    (atom (mapv tov rows))
        used (atom #{})]
    (doseq [c (range F)]                               ; ℓ 列を前進消去
      (when-let [pr (first (filter #(and (not (@used %)) (not (zero? (nth (@M %) c))))
                                   (range (count @M))))]
        (let [ipiv (modinv (nth (@M pr) c) n)
              prow (mapv #(mod (* % ipiv) n) (nth @M pr))]
          (swap! M assoc pr prow)
          (swap! M (fn [m] (vec (map-indexed
                                  (fn [i row]
                                    (if (= i pr) row
                                      (let [f (nth row c)]
                                        (if (zero? f) row
                                          (mapv #(mod (- %1 (* f %2)) n) row prow)))))
                                  m))))
          (swap! used conj pr))))
    (let [dvals (for [i (range (count @M))             ; 残り = d のみの式
                      :when (not (@used i))
                      :let [row (nth @M i) dco (nth row F) rhs (nth row (inc F))]
                      :when (not (zero? dco))]
                  (mod (* rhs (modinv dco n)) n))]
      (when (seq dvals)
        (let [d (first dvals)]
          (when (every? #(= % d) dvals) d))))))         ; 整合する d を返す

;; ---------------------------------------------------------------------------
;; ECDLP を index-calculus で解く: Q=dP の d を復元
;; ---------------------------------------------------------------------------
(defn index-calculus-dlog [{:keys [p a b n P]} Q B]
  (let [fb (build-factor-base a b p B)
        fbx (vec (sort (keys fb)))
        vars (conj fbx ::d)                            ; 未知: 各 ℓ_x と d
        need (+ (* 2 (count vars)) 8)]                  ; full-rank に十分な余裕
    (loop [rows [] total-tries 0 attempts 0]
      (if (or (>= (count rows) need) (> attempts (* 600 need)))
        (let [dd (solve-d rows fbx n)]
          {:d dd
           :rows (count rows) :tries total-tries :attempts attempts
           :fb-size (count fb) :solved (boolean dd)})
        (let [u (inc (rand-int (dec n))) v (inc (rand-int (dec n)))
              R (p-add (p-mul u P a b p) (p-mul v Q a b p) a b p)]
          (if (nil? R)
            (recur rows total-tries (inc attempts))
            (let [{:keys [terms tries]} (decompose R fb a b p)]
              (if terms
                ;; relation: εa ℓ_xa + εb ℓ_xb - v d ≡ u  (∵ R=uP+vQ, logP-基準で logR=u+v d)
                (let [[[xa ea] [xb eb]] terms
                      row (merge-with +
                            {xa ea} (if (= xa xb) {xa eb} {xb eb})
                            {::d (- v) ::rhs u})]
                  (recur (conj rows row) (+ total-tries tries) (inc attempts)))
                (recur rows (+ total-tries tries) (inc attempts))))))))))

;; ===========================================================================
;; デモ + 計測
;; ===========================================================================
(defn line [] (println (apply str (repeat 78 "─"))))

(defn run-one [pmin secret-frac verbose]
  (let [{:keys [p a b n P] :as C} (find-curve pmin)
        d (max 2 (long (* secret-frac n)))
        Q (p-mul d P a b p)
        B (max 4 (long (Math/ceil (* 1.3 (Math/sqrt p)))))  ; |V| ≈ 1.3√p
        t0 (System/currentTimeMillis)
        res (index-calculus-dlog C Q B)
        dt (- (System/currentTimeMillis) t0)]
    (when verbose
      (println (format "  曲線 E: y²=x³+%dx+%d  (mod %d) , 群位数 n=%d (素数)" a b p n))
      (println (format "  生成元 P=%s ,  Q=dP の真の d=%d" (str P) d))
      (println (format "  factor base |V|=%d → |FB|=%d 点 ,  必要関係数≈%d"
                       B (:fb-size res) (+ (:fb-size res) 4)))
      (println (format "  Semaev 分解の総試行(=Gröbnerが置換する探索量) = %d" (:tries res)))
      (println (format "  線形系を mod n で解いた: %s" (:solved res)))
      (println (format "  >>> 復元した d = %s   真の d=%d   一致=%s   (%d ms)"
                       (:d res) d (= (:d res) d) dt)))
    (assoc res :p p :n n :B B :d-true d :d-rec (:d res) :ms dt
               :ok (= (:d res) d))))

(defn -main []
  (line)
  (println "  H2: Semaev 総和多項式 × index-calculus による ECDLP 解析 (小曲線で実証)")
  (line)
  (println "\n[1] 単一曲線で ECDLP を index-calculus で破る")
  (run-one 1000 0.37 true)

  (println "\n[2] スケーリング計測: p を増やし『分解試行数』と『FBサイズ』を測る")
  (println "    (素体では |FB|≈√p, 線形代数 O(|FB|³)≈O(p^1.5) ≫ rho の √p)")
  (printf  "    %-8s %-8s %-10s %-12s %-8s %s\n" "p" "n" "|FB|" "分解試行" "ms" "d一致")
  (doseq [pm [500 2000 8000 20000 50000]]
    (let [r (run-one pm 0.41 false)]
      (printf "    %-8d %-8d %-10d %-12d %-8d %s\n"
              (:p r) (:n r) (:fb-size r) (:tries r) (:ms r) (:ok r))
      (flush)))

  (println "\n[結論 — secp256k1 への外挿]")
  (println "  ・index-calculus は確かに ECDLP を解く。だが素体では factor base が")
  (println "    |FB|≈√p しか小さくできず、関係収集 O(p) + 線形代数 O(|FB|³)=O(p^1.5)。")
  (println "  ・rho は O(√p)。∴ 素体 ECDLP では index-calculus は rho を超えない。")
  (println "  ・secp256k1: p≈2²⁵⁶ → |FB|≈2¹²⁸, 線形代数≈2³⁸⁴ ≫ rho の 2¹²⁸。")
  (println "    Weil descent が効く拡大体/二進体と違い、素体 secp256k1 はこの攻撃に安全。")
  (println "  ・記事の AI(新パラメータ化)が刺さるのは『分解=S_m=0 を解く段』だが、")
  (println "    素体ではその段の上限改善が線形代数 O(p^1.5) の壁を崩さない。← 実測の核心。")
  (line))

(-main)
