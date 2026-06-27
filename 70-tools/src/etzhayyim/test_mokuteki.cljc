;; etzhayyim.test-mokuteki — mokuteki objective-scoring pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure scoring/constructor layer (filesystem/Go-binary legs deferred):
;; resolve-rank · next-rank · make-component/component->dict · make-layer/make-axis ·
;; weighted-score · derive-axes.
(ns etzhayyim.test-mokuteki
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.mokuteki :as mk]))

(deftest resolve-rank-by-score
  (is (= "Dan 10" (:name (mk/resolve-rank 12500))))
  (is (= "Kyu 2" (:name (mk/resolve-rank 1200))))     ;; >=1000, <1500
  (is (= "Kyu 3" (:name (mk/resolve-rank 700)))))      ;; >=600, <1000

(deftest next-rank-target
  (testing "returns [next-name points-needed]"
    (is (= ["Kyu 1" 300] (mk/next-rank 1200))))         ;; next threshold 1500
  (testing "already at the top → [\"\" 0]"
    (is (= ["" 0] (mk/next-rank 12500)))))

(deftest component-construct-and-serialise
  (let [c (mk/make-component "perf" 0.5 80 "fast")]
    (is (= {:name "perf" :weight 0.5 :score 80.0 :details "fast"} c))
    (is (= {"name" "perf" "score" 80.0 "weight" 0.5 "details" "fast"}
           (mk/component->dict c)))))

(deftest layer-and-axis-constructors
  (let [l (mk/make-layer "A" "Alignment" "整合" 0.35 90 50 [])]
    (is (= "A" (:id l)))
    (is (= "整合" (:name-jp l)))
    (is (= 90.0 (:score l)))
    (is (= "整合" (get (mk/layer->dict l) "name_jp"))))
  (let [a (mk/make-axis "Engagement" 0.25 70 21 "Layer A + D" "")]
    (is (= 70.0 (:score a)))
    (is (= "Layer A + D" (get (mk/axis->dict a) "source")))))

(deftest weighted-score-sum
  (is (= 70.0 (mk/weighted-score [{:score 80.0 :weight 0.5} {:score 60.0 :weight 0.5}])))
  (is (= 0.0 (mk/weighted-score []))))

(deftest derive-axes-from-layers
  (let [axes (mk/derive-axes {:score 80.0} {:score 60.0} {:score 40.0} {:score 100.0})]
    (testing "5 axes with the documented linear combinations"
      (is (= 5 (count axes)))
      ;; engagement = A·0.5 + D·0.5 = 90 ; competence = A·0.6 + B·0.4 = 72 ;
      ;; contribution = B·0.4 + C·0.6 = 48 ; growth = C·0.5 + A·0.5 = 60 ;
      ;; resilience = B·0.5 + D·0.5 = 80
      (is (= [90.0 72.0 48.0 60.0 80.0] (mapv :score axes)))
      (is (= "Layer A + D" (:source (first axes)))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-mokuteki)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
