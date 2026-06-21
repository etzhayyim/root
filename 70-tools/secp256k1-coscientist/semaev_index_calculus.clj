#!/usr/bin/env bb
;; semaev_index_calculus.clj — H2: Semaev 総和多項式 × index-calculus による ECDLP 解析
;;
;; Co-Scientist H2 仮説の実証 (m=2 = 2点分解)。小さい素体 E(F_p) 上で:
;;   1. Semaev S_3 を「総和多項式」として実装 (P1+P2+P3=O ⇔ S_3(x1,x2,x3)=0)
;;   2. factor base (x 座標が小集合 V にある点) を作る
;;   3. ランダム R=uP+vQ を Semaev で R=Pa+Pb に分解 → 線形関係を収集
;;   4. mod n ガウス消去で離散対数を解き d を復元 → dP==Q を検証
;;   5. *コストを計測* し「素体では index-calculus が √n を超えない」=
;;      secp256k1 が安全な理由を実測で示す。
;; 共有コアは semaev_core.clj。m=3 + AI 探索は semaev_m3_ai.clj。

(load-file "70-tools/secp256k1-coscientist/semaev_core.clj")

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
  (println "  H2: Semaev 総和多項式 × index-calculus による ECDLP 解析 (m=2, 小曲線で実証)")
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
