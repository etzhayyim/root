#!/usr/bin/env bb
;; ecdsa_coscientist.clj — secp256k1 / ECDSA cryptanalysis PoC (research/教育用)
;;
;; AI Co-Scientist (Generation→Reflection→Ranking→Evolution→Meta-review) が収束した
;; 仮説を *自分で発行した鍵* に対してのみ実証する。
;;
;; 重要な事実訂正:
;;   - Bitcoin は RSA を使っていない。署名は ECDSA over secp256k1。
;;   - 守っている難問は「素因数分解」ではなく「楕円曲線離散対数 (ECDLP)」。
;;   - 健全な鍵の ECDLP は古典で約 2^128 演算 = 破れない。
;;   - *破れるのは「壊れた nonce 運用」だけ*。本 PoC はそれを自分の鍵で再現する。
;;
;; 依存ゼロ: secp256k1 の体・点演算・ECDSA・LLL を素の BigInteger / 有理数で自前実装。

;; ---------------------------------------------------------------------------
;; secp256k1 パラメータ
;; ---------------------------------------------------------------------------
(defn h [s] (BigInteger. (str s) 16))
(def P  (h "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F"))
(def N  (h "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141"))
(def Gx (h "79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798"))
(def Gy (h "483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8"))
(def G  [Gx Gy])
(def ZERO BigInteger/ZERO)
(def TWO  (biginteger 2))
(def THREE (biginteger 3))

;; ---------------------------------------------------------------------------
;; 素体 F_p 演算
;; ---------------------------------------------------------------------------
(defn fadd [a b] (.mod (.add a b) P))
(defn fsub [a b] (.mod (.subtract a b) P))
(defn fmul [a b] (.mod (.multiply a b) P))
(defn finv [a] (.modInverse (.mod a P) P))

;; 楕円曲線 y^2 = x^3 + 7。無限遠点 = nil。
(defn pdbl [pt]
  (when pt
    (let [[x y] pt
          l  (fmul (fmul THREE (fmul x x)) (finv (fmul TWO y)))
          x3 (fsub (fsub (fmul l l) x) x)
          y3 (fsub (fmul l (fsub x x3)) y)]
      [x3 y3])))

(defn padd [pp qq]
  (cond
    (nil? pp) qq
    (nil? qq) pp
    :else
    (let [[x1 y1] pp [x2 y2] qq]
      (if (= x1 x2)
        (if (= y1 y2) (pdbl pp) nil)               ; P + (-P) = O
        (let [l  (fmul (fsub y2 y1) (finv (fsub x2 x1)))
              x3 (fsub (fsub (fmul l l) x1) x2)
              y3 (fsub (fmul l (fsub x1 x3)) y1)]
          [x3 y3])))))

(defn pmul [k pt]                                    ; double-and-add
  (loop [k (.mod k N) acc nil base pt]
    (if (zero? (.signum k))
      acc
      (recur (.shiftRight k 1)
             (if (.testBit k 0) (padd acc base) acc)
             (pdbl base)))))

;; ---------------------------------------------------------------------------
;; スカラ体 F_n 演算 + ECDSA
;; ---------------------------------------------------------------------------
(defn nmod [a] (.mod a N))
(defn ninv [a] (.modInverse (.mod a N) N))

(def ^java.security.SecureRandom rng (java.security.SecureRandom.))
(defn rand-scalar []
  (let [k (BigInteger. 256 rng)]
    (if (and (pos? (.signum k)) (neg? (.compareTo k N))) k (recur))))

(defn sha256-int [^String s]
  (BigInteger. 1 (.digest (java.security.MessageDigest/getInstance "SHA-256")
                          (.getBytes s "UTF-8"))))

(defn keygen []
  (let [d (rand-scalar)] {:d d :Q (pmul d G)}))

(defn sign [d z k]
  (let [[xr _] (pmul k G)
        r (nmod xr)
        s (nmod (.multiply (ninv k) (.add z (.multiply r d))))]
    {:r r :s s :z z :k k}))

(defn verify [Q z {:keys [r s]}]
  (let [w  (ninv s)
        u1 (nmod (.multiply z w))
        u2 (nmod (.multiply r w))
        [x _] (padd (pmul u1 G) (pmul u2 Q))]
    (and (pos? (.signum r)) (= (nmod x) r))))

;; ---------------------------------------------------------------------------
;; 攻撃 A: nonce 再利用 (同じ k を2回) → 鍵を厳密復元 (純モジュラ演算)
;;   実在の Bitcoin 盗難手口 (Android SecureRandom バグ 2013 等) と同型。
;; ---------------------------------------------------------------------------
(defn attack-reused-nonce [sig1 sig2]
  (let [{r :r s1 :s z1 :z} sig1
        {s2 :s z2 :z} sig2
        k (nmod (.multiply (.subtract z1 z2) (ninv (.subtract s1 s2))))
        d (nmod (.multiply (.subtract (.multiply s1 k) z1) (ninv r)))]
    {:k k :d d}))

;; ---------------------------------------------------------------------------
;; 整数保存 LLL (Cohen "A Course in Computational Algebraic Number Theory"
;; Algorithm 2.6.3, delta = 3/4)。GS 情報を整数 d_i (主小行列式) と
;; λ_{i,j}=d_j·μ_{i,j} で持つので有理数の分母爆発が無く、256/512bit entries でも高速。
;; 1-based 索引。状態は atom の map で保持 (次元は小さいので十分)。
;; ---------------------------------------------------------------------------
(defn idot [u v] (reduce + 0N (map * u v)))
(defn vsub [u v] (mapv - u v))
(defn vscale [c v] (mapv #(* c %) v))
(defn abig [x] (if (neg? x) (- x) x))
(defn fdiv [a b] (quot (- a (mod a b)) b))           ; floor division, b>0
(defn nint [a b] (fdiv (+ (* 2 a) b) (* 2 b)))       ; round(a/b) to nearest, b>0

(defn lll [rows]
  (let [n   (count rows)
        b   (atom (into {} (map-indexed (fn [i r] [(inc i) (mapv bigint r)]) rows)))
        d   (atom {0 1N})
        lam (atom {})]
    (doseq [i (range 1 (inc n))]                     ; 整数 Gram-Schmidt 初期化
      (doseq [j (range 1 (inc i))]
        (let [u (reduce (fn [u l]
                          (fdiv (- (* (@d l) u) (* (get @lam [i l] 0N) (get @lam [j l] 0N)))
                                (@d (dec l))))
                        (idot (@b i) (@b j)) (range 1 j))]
          (if (< j i) (swap! lam assoc [i j] u) (swap! d assoc i u)))))
    (letfn [(red [k l]
              (let [lkl (get @lam [k l] 0N) dl (@d l)]
                (when (> (* 2 (abig lkl)) dl)
                  (let [q (nint lkl dl)]
                    (swap! b update k #(vsub % (vscale q (@b l))))
                    (swap! lam update [k l] (fnil #(- % (* q dl)) 0N))
                    (doseq [i (range 1 l)]
                      (swap! lam update [k i] (fnil #(- % (* q (get @lam [l i] 0N))) 0N)))))))
            (swp [k]
              (let [bk (@b k) bk1 (@b (dec k))]
                (swap! b assoc k bk1 (dec k) bk))
              (doseq [j (range 1 (dec k))]
                (let [a (get @lam [k j] 0N) c (get @lam [(dec k) j] 0N)]
                  (swap! lam assoc [k j] c [(dec k) j] a)))
              (let [lm (get @lam [k (dec k)] 0N)
                    dk (@d k) dk1 (@d (dec k)) dk2 (@d (- k 2))
                    B (fdiv (+ (* dk2 dk) (* lm lm)) dk1)]
                (doseq [i (range (inc k) (inc n))]
                  (let [t   (get @lam [i k] 0N)
                        nik (fdiv (- (* dk (get @lam [i (dec k)] 0N)) (* lm t)) dk1)
                        nk1 (fdiv (+ (* B t) (* lm nik)) dk)]
                    (swap! lam assoc [i k] nik [i (dec k)] nk1)))
                (swap! d assoc (dec k) B)))]
      (loop [k 2]
        (when (<= k n)
          (red k (dec k))
          (let [dk (@d k) dk1 (@d (dec k)) dk2 (@d (- k 2))
                lm (get @lam [k (dec k)] 0N)]
            (if (< (* 4 dk dk2) (- (* 3 dk1 dk1) (* 4 lm lm)))
              (do (swp k) (recur (max (dec k) 2)))
              (do (doseq [l (range (- k 2) 0 -1)] (red k l))
                  (recur (inc k))))))))
    (mapv #(@b %) (range 1 (inc n)))))

;; ---------------------------------------------------------------------------
;; 攻撃 B: 短い nonce (壊れた RNG) → Hidden Number Problem → LLL で鍵復元
;;   各 nonce が L ビット未満 (上位ビットが 0)。複数署名から d を解く。
;;   k_i = a_i + b_i*d (mod n),  a_i = s^-1 z,  b_i = s^-1 r,  0 <= k_i < K=2^L
;; ---------------------------------------------------------------------------
(defn attack-short-nonce [Q sigs L]
  (let [K (.shiftLeft BigInteger/ONE L)
        m (count sigs)
        as (mapv (fn [{:keys [s z]}] (nmod (.multiply (ninv s) z))) sigs)
        bs (mapv (fn [{:keys [s r]}] (nmod (.multiply (ninv s) r))) sigs)
        Nb (bigint N) Kb (bigint K)
        ;; (m+2)x(m+2) 整数格子 (全体を n 倍してスケール)
        rows
        (concat
          (for [i (range m)]                         ; n^2 * I_m
            (mapv #(if (= % i) (* Nb Nb) 0N) (range (+ m 2))))
          [(into (mapv #(* Nb (bigint %)) bs) [Kb 0N])]      ; t行: n*b_i ... K 0
          [(into (mapv #(* Nb (bigint %)) as) [0N (* Kb Nb)])]) ; 埋め込み行: n*a_i ... 0 K*n
        reduced (lll (mapv vec rows))
        target  (* Kb Nb)]
    ;; 最終座標が ±K*n の行を探し d = (前座標)/K を取り出す
    (some (fn [row]
            (let [last (peek row)
                  dk   (nth row m)]
              (when (= (.abs (biginteger last)) (biginteger target))
                (let [sign (if (neg? last) -1 1)
                      d (nmod (biginteger (* sign (/ dk Kb))))]
                  (when (= (pmul d G) Q) d)))))
          reduced)))

;; ===========================================================================
;; デモ実行
;; ===========================================================================
(defn hex [^BigInteger x] (format "%064x" x))
(defn line [] (println (apply str (repeat 76 "─"))))

(defn -main []
  (line)
  (println "  secp256k1 / ECDSA Co-Scientist 解析 PoC  —  自分で発行した鍵のみを攻撃")
  (line)

  ;; --- 1. 自分の鍵を発行 ----------------------------------------------------
  (let [{:keys [d Q]} (keygen)
        [Qx Qy] Q]
    (println "\n[1] 鍵ペアを発行 (これが攻撃対象 = 私たち自身の鍵)")
    (println "    秘密鍵 d  :" (hex d))
    (println "    公開鍵 Qx :" (hex Qx))
    (println "    公開鍵 Qy :" (hex Qy))
    (spit "70-tools/secp256k1-coscientist/our-key.json"
          (str "{\n  \"curve\": \"secp256k1\",\n"
               "  \"private_key_hex\": \"" (hex d) "\",\n"
               "  \"public_key_x_hex\": \"" (hex Qx) "\",\n"
               "  \"public_key_y_hex\": \"" (hex Qy) "\",\n"
               "  \"note\": \"self-issued test key for cryptanalysis PoC — holds no funds\"\n}\n"))
    (println "    → our-key.json に保存")

    ;; --- 2. 健全な署名は安全であることを確認 -------------------------------
    (println "\n[2] 健全な署名 (毎回ランダム nonce) — verify が通る / 鍵は漏れない")
    (let [z (sha256-int "kingdom of god on blockchain")
          sig (sign d z (rand-scalar))]
      (println "    verify =" (verify Q z sig) " (ECDLP は約 2^128、ここからは d を復元できない)"))

    ;; --- 3. 攻撃 A: nonce 再利用 ------------------------------------------
    (println "\n[3] 攻撃A: nonce 再利用 (同じ k で2つの異なるメッセージに署名)")
    (let [k (rand-scalar)
          z1 (sha256-int "send 1 BTC to alice")
          z2 (sha256-int "send 2 BTC to bob")
          sig1 (sign d z1 k)
          sig2 (sign d z2 k)
          {dr :d kr :k} (attack-reused-nonce sig1 sig2)]
      (println "    2署名の r が一致 :" (= (:r sig1) (:r sig2)))
      (println "    復元した nonce k :" (hex kr) " 正解:" (= kr k))
      (println "    復元した秘密鍵 d :" (hex dr))
      (println "    >>> d 完全一致    :" (= dr d) "  ★鍵を奪取★"))

    ;; --- 4. 攻撃 B: 短い nonce (壊れた RNG) → HNP/LLL ---------------------
    (println "\n[4] 攻撃B: 壊れた RNG が 128bit の短い nonce を生成 → 5署名 → LLL で復元")
    (let [L 128
          sigs (vec (for [i (range 5)]
                      (let [z (sha256-int (str "tx-" i))
                            k (BigInteger. L rng)]              ; 上位128bitが 0
                        (sign d z k))))
          t0 (System/currentTimeMillis)
          dr (attack-short-nonce Q sigs L)
          dt (- (System/currentTimeMillis) t0)]
      (println "    全署名が個別に verify :" (every? #(verify Q (:z %) %) sigs))
      (println "    LLL 復元した秘密鍵 d  :" (when dr (hex dr)))
      (println "    >>> d 完全一致         :" (= dr d) (str "  (" dt " ms) ★鍵を奪取★")))

    (println "\n[結論] 数学(ECDLP)は無傷。破れたのは『壊れた nonce 運用』だけ。")
    (println "       → 教訓: RFC 6979 決定的 nonce を必ず使う。これが防御。")
    (line)))

(-main)
