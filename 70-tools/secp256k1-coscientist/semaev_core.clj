#!/usr/bin/env bb
;; semaev_core.clj — 共有コア (素体/EC/曲線探索/Semaev S_3/factor base/分解/線形代数)
;; semaev_index_calculus.clj (m=2) と semaev_m3_ai.clj (m=3 + AI) が load-file で共有。
;; 依存ゼロ。

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
(defn p-sub [P Q a b p] (p-add P (p-neg Q p) a b p))

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

;; S_3 の「変数 j についての2次係数 [A B C]」(他2変数固定)。次数2なので t=0,1,2 補間。
(defn semaev3-coeffs [fix1 fix2 a b p]
  ;; S_3(fix1, t, fix2) を t の2次式 A t^2 + B t + C とみなす
  (let [f (fn [t] (semaev3 fix1 t fix2 a b p))
        f0 (f 0) f1 (f 1) f2 (f 2)
        A (mod (* (- (+ f2 f0) (* 2 f1)) (modinv 2 p)) p)
        B (mod (- f1 f0 A) p)
        C f0]
    [A B C]))

(defn solve-quadratic [A B C p]                          ; A x^2+B x+C=0 mod p の根
  (if (zero? A)
    (if (zero? B) [] [(mod (* (- C) (modinv B p)) p)])
    (let [disc (mod (- (* B B) (* 4 A C)) p)]
      (if-let [s (msqrt disc p)]
        (let [inv2a (modinv (mod (* 2 A) p) p)]
          (distinct [(mod (* (- s B) inv2a) p) (mod (* (- (- s) B) inv2a) p)]))
        []))))

;; S_3(x1,·,x3)=0 を x2 について解く (x1,x3 既知)
(defn solve-semaev-x2 [x1 x3 a b p]
  (let [[A B C] (semaev3-coeffs x1 x3 a b p)] (solve-quadratic A B C p)))

;; ---------------------------------------------------------------------------
;; factor base: x ∈ V={0..B-1} を持つ点。各 x の canonical 点 = (x, 小さい方の y)。
;; ---------------------------------------------------------------------------
(defn build-factor-base [a b p B]
  (into {} (for [x (range B)
                 :let [y (msqrt (rhs x a b p) p)]
                 :when (and y (pos? y))]
             [x [x (min y (- p y))]])))                  ; x -> canonical point

;; R=Pa+Pb を Semaev で分解 (m=2)。order = xa を試す順序 (AI policy 用)。
;; 見つかれば {:terms [[xa εa] [xb εb]] :tries k}。
(defn decompose [R fb a b p & [order]]
  (let [xR (first R)
        xs (or order (sort (keys fb)))]
    (loop [xs xs tries 0]
      (if (empty? xs)
        {:terms nil :tries tries}
        (let [xa (first xs)
              cand (filter fb (solve-semaev-x2 xa xR a b p))
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
;; rows: 各 {x coef ... ::d coef ::rhs r}。fbx: factor base の x 一覧。
;; ---------------------------------------------------------------------------
(defn solve-d [rows fbx n]
  (let [cols (vec fbx)
        F (count cols)
        tov (fn [r] (conj (mapv #(mod (get r % 0) n) cols)
                          (mod (get r ::d 0) n) (mod (get r ::rhs 0) n)))
        M    (atom (mapv tov rows))
        used (atom #{})]
    (doseq [c (range F)]
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
    (let [dvals (for [i (range (count @M))
                      :when (not (@used i))
                      :let [row (nth @M i) dco (nth row F) rhs (nth row (inc F))]
                      :when (not (zero? dco))]
                  (mod (* rhs (modinv dco n)) n))]
      (when (seq dvals)
        (let [d (first dvals)]
          (when (every? #(= % d) dvals) d))))))

;; ---------------------------------------------------------------------------
;; m=2 ECDLP index-calculus: Q=dP の d を復元
;; ---------------------------------------------------------------------------
(defn index-calculus-dlog [{:keys [p a b n P]} Q B]
  (let [fb (build-factor-base a b p B)
        fbx (vec (sort (keys fb)))
        need (+ (* 2 (inc (count fbx))) 8)]
    (loop [rows [] total-tries 0 attempts 0]
      (if (or (>= (count rows) need) (> attempts (* 600 need)))
        (let [dd (solve-d rows fbx n)]
          {:d dd :rows (count rows) :tries total-tries :attempts attempts
           :fb-size (count fb) :solved (boolean dd)})
        (let [u (inc (rand-int (dec n))) v (inc (rand-int (dec n)))
              R (p-add (p-mul u P a b p) (p-mul v Q a b p) a b p)]
          (if (nil? R)
            (recur rows total-tries (inc attempts))
            (let [{:keys [terms tries]} (decompose R fb a b p)]
              (if terms
                (let [[[xa ea] [xb eb]] terms
                      row (merge-with +
                            {xa ea} (if (= xa xb) {xa eb} {xb eb})
                            {::d (- v) ::rhs u})]
                  (recur (conj rows row) (+ total-tries tries) (inc attempts)))
                (recur rows (+ total-tries tries) (inc attempts))))))))))

(defn line [] (println (apply str (repeat 78 "─"))))
