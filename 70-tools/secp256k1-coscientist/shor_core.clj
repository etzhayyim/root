#!/usr/bin/env bb
;; shor_core.clj — Shor 状態の厳密 Schmidt ランク(=ボンド次元)計算の共有コア
;; tensor_shor_ttn.clj が load-file で共有。任意の二部分割の χ を GF(p) ランクで厳密計算。
;; 依存ゼロ。

;; --- 数論 ---
(defn modpow [a e m] (.longValue (.modPow (biginteger a) (biginteger e) (biginteger m))))
(defn gcd* [a b] (if (zero? b) a (recur b (mod a b))))
(defn nbits [n] (.bitLength (biginteger (max 1 n))))
(defn order [a N] (loop [x 1 v (mod a N)] (if (= v 1) x (recur (inc x) (mod (* v a) N)))))

;; --- GF(p) スパース・ランク (実ランクを大素数体で再現) ---
(def ^long PR 2147483647)                                ; 2^31-1
(defn minv [a] (.longValue (.modInverse (biginteger (mod a PR)) (biginteger PR))))
(defn row-sub [row prow f]
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
          (recur (row-sub row prow (long (get row col)))) row)))))
(defn gf-rank [rows]
  (loop [rs rows pivots {} rank 0]
    (if (empty? rs) rank
      (let [r (reduce-row (first rs) pivots)]
        (if (empty? r) (recur (rest rs) pivots rank)
          (let [col (reduce min (keys r)) inv (minv (get r col))
                nr (into {} (map (fn [[c x]] [c (mod (* (long x) inv) PR)]) r))]
            (recur (rest rs) (assoc pivots col nr) (inc rank))))))))

;; --- pre-QFT Shor 状態の点集合 + 任意分割の Schmidt ランク ---
;; qubit 位置 0..t-1 = control x の MSB..LSB, 位置 t..T-1 = work y の MSB..LSB。
(defn shor-points [N a t]
  (let [nw (nbits (dec N)) Q (bit-shift-left 1 t) T (+ t nw)]
    {:T T :t t :nw nw :N N :a a
     :points (mapv (fn [x] (+ (* x (bit-shift-left 1 nw)) (modpow a x N))) (range Q))}))

(defn bit-at [I T p] (bit-and (bit-shift-right I (- T 1 p)) 1))
(defn subkey [I T positions] (reduce (fn [acc p] (+ (* 2 acc) (bit-at I T p))) 0 positions))

;; Lpos = 左側にある qubit 位置の集合 → その分割をまたぐ χ
(defn schmidt-rank [points T Lpos]
  (let [Ls (set Lpos)
        Rpos (vec (remove Ls (range T)))
        Lpv (vec Lpos)
        rm (reduce (fn [m I] (update m (subkey I T Lpv)
                                     #(assoc (or % {}) (subkey I T Rpos) 1)))
                   {} points)]
    (gf-rank (vals rm))))

(defn line [] (println (apply str (repeat 78 "─"))))
