;; soma 杣 — test suite (clojure.test, babashka-runnable).
;; Run: bb --classpath 20-actors 20-actors/soma/methods/test_soma.clj
;; Per ADR-2606142010 (soma R0).
(ns soma.methods.test-soma
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [soma.methods.fell-plan :as fp]
            [soma.methods.harvester :as hv]
            [soma.methods.extraction :as ex]
            [soma.methods.analyze :as az]
            [soma.methods.datom-emit :as de]
            [soma.methods.handoff :as ho]))

;; ── fell_plan: geometry ───────────────────────────────────────────────────────
(deftest angle-helpers
  (testing "azimuth normalisation + smallest angular difference"
    (is (= 350.0 (fp/norm-az -10.0)))
    (is (= 10.0 (fp/norm-az 370.0)))
    (is (= 0.0 (fp/ang-diff 10.0 10.0)))
    (is (= 20.0 (fp/ang-diff 350.0 10.0)))   ; wraps the short way
    (is (= 180.0 (fp/ang-diff 0.0 180.0)))))

(deftest hinge-width-scales-with-diameter
  (testing "G5 — hinge holding-wood ≈ 10% of DBH; positive diameter required"
    (is (< (Math/abs (- 0.045 (fp/hinge-width-m 0.45))) 1e-9))
    (is (< (fp/hinge-width-m 0.30) (fp/hinge-width-m 0.60)))
    (is (thrown? clojure.lang.ExceptionInfo (fp/hinge-width-m 0.0)))))

(deftest predict-fall-follows-aim-and-lean
  (testing "no lean → fall follows the aim; strong lean pulls toward the lean"
    ;; no lean, no wind → fall az == aim az
    (is (< (fp/ang-diff 90.0
                        (fp/predict-fall-az {:aim-az 90.0 :lean-az 0.0 :lean-deg 0.0}))
           1e-6))
    ;; aim 0°, hard lean toward 90° → resultant pulled toward 90°
    (let [az (fp/predict-fall-az {:aim-az 0.0 :lean-az 90.0 :lean-deg 15.0})]
      (is (> az 0.0)))))

(deftest wind-perturbs-fall-line
  (testing "a cross-wind nudges the fall line toward the wind azimuth"
    (let [calm (fp/predict-fall-az {:aim-az 0.0 :lean-az 0.0 :lean-deg 0.0 :wind-mps 0.0})
          windy (fp/predict-fall-az {:aim-az 0.0 :lean-az 0.0 :lean-deg 0.0
                                     :wind-az 90.0 :wind-mps 3.0})]
      (is (< (fp/ang-diff calm 0.0) 1e-6))
      (is (> (fp/ang-diff windy 0.0) 0.0)))))   ; pulled off the aim

;; ── fell_plan: the safety gate (G5 + G7) ──────────────────────────────────────
(deftest fall-zone-detects-intrusion
  (testing "an exclusion in the fall sector + radius is in the zone; one behind isn't"
    (let [tree {:id "t" :coord [0 0] :height-m 20.0}]
      ;; point due east at 10 m, fall az 0° (east) → in the zone
      (is (fp/in-fall-zone? [0 0] 0.0 20.0 [10 0]))
      ;; same point but the tree falls WEST (180°) → behind, not in the zone
      (is (not (fp/in-fall-zone? [0 0] 180.0 20.0 [10 0])))
      ;; far beyond 1.5× height (>30 m) → out of range
      (is (not (fp/in-fall-zone? [0 0] 0.0 20.0 [40 0]))))))

(deftest safe-fell-predicate
  (testing "safe iff not protected AND no exclusion in the fall zone"
    (let [tree {:id "t" :coord [0 0] :height-m 20.0 :diameter-m 0.4}
          crew {:id "x" :kind :human :coord [10 0]}]
      (is (fp/safe-fell? tree 180.0 [crew]))        ; falls away from crew
      (is (not (fp/safe-fell? tree 0.0 [crew])))))) ; falls toward crew

(deftest plan-fell-raises-on-exclusion
  (testing "G5 — a fall zone overlapping a human/road/watercourse RAISES"
    (let [tree {:id "t-1" :coord [0 0] :height-m 20.0 :diameter-m 0.4
                :lean-az 0.0 :lean-deg 0.0 :wind-mps 0.0}
          crew {:id "x-crew" :kind :human :coord [10 0]}]
      ;; aim east (0°), crew is due east → must raise
      (is (thrown? clojure.lang.ExceptionInfo (fp/plan-fell tree 0.0 [crew])))
      ;; aim west (180°), crew east → safe plan returned
      (let [plan (fp/plan-fell tree 180.0 [crew])]
        (is (:exclusions-clear plan))
        (is (pos? (:hinge-m plan)))))))

(deftest plan-fell-raises-on-protected
  (testing "G7 — a protected / no-cut tree RAISES regardless of clear fall line"
    (let [old {:id "t-keep" :coord [0 0] :height-m 30.0 :diameter-m 0.9
               :protected true :no-cut true}]
      (is (fp/protected? old))
      (is (thrown? clojure.lang.ExceptionInfo (fp/plan-fell old 180.0 []))))))

;; ── harvester: bucking DP + reach ─────────────────────────────────────────────
(deftest grapple-reach
  (testing "G8 — head reaches a stem within boom reach, not beyond"
    (is (hv/reachable? [0 0] 7.5 [5 0]))
    (is (not (hv/reachable? [0 0] 7.5 [10 0])))))

(deftest bucking-maximises-value
  (testing "cut-to-length DP picks the value-maximising assortment"
    (let [pt [{:class :sawlog :length-m 5.0 :price 95.0}
              {:class :sawlog :length-m 4.0 :price 88.0}
              {:class :pulp   :length-m 3.0 :price 42.0}
              {:class :pulp   :length-m 2.0 :price 38.0}]
          ;; a 10 m stem: DP finds 4+4+2 (88+88+38=214) beats 5+5 (190)
          r (hv/buck-stem 10.0 pt)]
      (is (= 214.0 (:value r)))
      (is (= 3 (count (:cuts r))))
      (is (< (:waste-m r) 0.01))
      ;; value is the optimum: no assortment of these classes within 10 m beats it
      (is (>= (:value r) 190.0))
      (is (thrown? clojure.lang.ExceptionInfo (hv/buck-stem -1.0 pt))))))

(deftest bucking-summary-rolls-up
  (testing "summary counts logs by class"
    (let [pt [{:class :sawlog :length-m 5.0 :price 95.0}
              {:class :pulp   :length-m 2.0 :price 38.0}]
          s (hv/buck-summary (hv/buck-stem 10.0 pt))]
      (is (= 190.0 (:value s)))
      (is (= 2 (:n-logs s)))
      (is (= 2 (get-in s [:by-class :sawlog]))))))

;; ── extraction: slope + ground-impact gates (G2) ──────────────────────────────
(deftest slope-gate
  (testing "a segment within max grade is OK; steeper is not"
    (let [fwd {:max-grade-pct 35.0}]
      (is (ex/grade-ok? fwd 28.0))
      (is (not (ex/grade-ok? fwd 40.0))))))

(deftest ground-impact-gate
  (testing "G2 — firm soil bears the machine; wet over-bears; protected never"
    (let [fwd {:ground-pressure-kpa 45.0 :bearing-firm-kpa 80.0 :bearing-wet-kpa 30.0}]
      (is (ex/ground-ok? fwd :firm))            ; 45 ≤ 80
      (is (not (ex/ground-ok? fwd :wet)))       ; 45 > 30
      (is (not (ex/ground-ok? fwd :protected)))))) ; never

(deftest plan-route-raises-on-overgrade-and-overpressure
  (testing "G2 — over-grade segment OR over-bearing/protected soil RAISES"
    (let [fwd {:max-grade-pct 35.0 :ground-pressure-kpa 45.0
               :bearing-firm-kpa 80.0 :bearing-wet-kpa 30.0}
          segs [{:from "a" :to "landing" :grade-pct 12.0 :length-m 14.0}
                {:from "b" :to "landing" :grade-pct 40.0 :length-m 20.0}]]
      ;; over-grade segment on firm soil → raises
      (is (thrown? clojure.lang.ExceptionInfo (ex/plan-route fwd :firm segs)))
      ;; wet soil over-bears → raises before even checking grade
      (is (thrown? clojure.lang.ExceptionInfo
                   (ex/plan-route fwd :wet [{:from "a" :to "landing" :grade-pct 5.0 :length-m 10.0}])))
      ;; firm soil, all in grade → feasible plan
      (let [ok (ex/plan-route fwd :firm [{:from "a" :to "landing" :grade-pct 12.0 :length-m 14.0}])]
        (is (:feasible ok))
        (is (= 1 (:n-segments ok)))))))

;; ── analyze + datom_emit (end-to-end over the seed) ──────────────────────────
(def seed (az/load-seed "20-actors/soma/data/stand.edn"))

(deftest analyze-end-to-end
  (let [res (az/run seed)]
    (testing "every tree is classified exactly once into fells/refused/unsafe"
      (is (= (:n-trees res)
             (+ (count (:fells res)) (count (:refused res)) (count (:unsafe res))))))
    (testing "G7 — the old-growth seed-tree is refused, never felled"
      (is (contains? (set (map :tree (:refused res))) "t-keep"))
      (is (not (contains? (set (map :tree (:fells res))) "t-keep"))))
    (testing "felled trees carry a fall azimuth, hinge, and bucked value"
      (is (pos? (count (:fells res))))
      (doseq [f (:fells res)]
        (is (number? (:fall-az f)))
        (is (pos? (:hinge-m f)))
        (is (pos? (get-in f [:buck :value])))))
    (testing "extraction route is feasible + total value is positive"
      (is (:feasible (:extraction res)))
      (is (pos? (:total-value res))))))

(deftest datom-emit-shape
  (let [res (az/run seed)
        out (de/emit seed res 1)]
    (testing "emits ground :add datoms + transient :derived readouts"
      (is (re-find #":soma\.tree/species" out))
      (is (re-find #":soma\.tree/protected" out))
      (is (re-find #":soma\.exclusion/kind" out))
      (is (re-find #":en/kind :felled" out))
      (is (re-find #":en/kind :refused-protected" out))
      (is (re-find #":bond/total-value" out))
      (is (re-find #":derived\]" out))
      ;; well-formed EDN vector of datoms
      (is (vector? (clojure.edn/read-string out))))))

;; ── handoff (cross-actor chain edges: soma→tatekata timber supply) ───────────
(deftest outbound-to-tatekata
  (testing "bucked-log assortments → tatekata lumber-supply intents, source-attributed"
    (let [hs (ho/outbound-handoff [{:log-id "l1" :grade :sawlog :length-m 5.0 :volume-m3 0.42}
                                   {:log-id "l2" :grade :pulp :length-m 3.0 :volume-m3 0.18}])]
      (is (= 2 (count hs)))
      (is (every? #(= "soma" (:from-actor %)) hs))
      (is (every? #(= "tatekata" (:to-actor %)) hs))
      (is (= :timber-supply (:kind (first hs))))
      (is (= :sawlog (get-in (first hs) [:payload :grade])))
      (is (= 0.42 (get-in (first hs) [:payload :volume-m3]))))))

(deftest handoff-provenance-gate
  (testing "G9 — an orphan handoff (no source/destination) RAISES"
    (is (thrown? clojure.lang.ExceptionInfo (ho/assert-handoff! {:id "x" :to-actor "tatekata"})))
    (is (thrown? clojure.lang.ExceptionInfo (ho/assert-handoff! {:id "x" :from-actor "soma"})))
    (is (= "soma" (:from-actor (ho/assert-handoff! {:id "x" :from-actor "soma" :to-actor "tatekata"}))))))

(deftest handoff-emit-shape
  (testing "emits well-formed EDN :handoff/* 縁 with actor provenance on every edge"
    (let [hs (ho/outbound-handoff [{:log-id "l1" :grade :sawlog :length-m 5.0 :volume-m3 0.42}])
          out (ho/emit hs 1)]
      (is (re-find #":handoff/from-actor" out))
      (is (re-find #":handoff/to-actor" out))
      (is (re-find #"en\.handoff\.soma\.tatekata\." out))
      (is (vector? (clojure.edn/read-string out))))))

(let [{:keys [fail error]} (run-tests 'soma.methods.test-soma)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
