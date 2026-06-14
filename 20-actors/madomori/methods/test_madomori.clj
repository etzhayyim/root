;; madomori 窓守 — test suite (clojure.test, babashka-runnable).
;; Run: bb --classpath 20-actors 20-actors/madomori/methods/test_madomori.clj
;; Per ADR-2606142020 (madomori R0).
(ns madomori.methods.test-madomori
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.edn :as edn]
            [madomori.methods.facade-path :as fp]
            [madomori.methods.wind-envelope :as we]
            [madomori.methods.adhesion :as ad]
            [madomori.methods.analyze :as az]
            [madomori.methods.datom-emit :as de]
            [madomori.methods.coverage :as cov]
            [madomori.methods.multi-face :as mf]
            [madomori.methods.water-recovery :as wr]
            [madomori.methods.handoff :as ho]))

;; ── facade_path ──────────────────────────────────────────────────────────────
(deftest boustrophedon-visits-every-pane-once
  (testing "S-shape coverage visits every pane exactly once"
    (let [path (fp/boustrophedon 3 4)
          cov (fp/coverage path 3 4)]
      (is (= 12 (count path)))
      (is (:complete? cov))
      (is (not (:duplicate? cov)))
      (is (empty? (:missing cov))))))

(deftest boustrophedon-alternates-direction
  (testing "row 0 left→right, row 1 right→left (minimal-turn sweep)"
    (let [path (fp/boustrophedon 2 3)]
      (is (= [[0 0] [0 1] [0 2] [1 2] [1 1] [1 0]] path)))))

(deftest boustrophedon-rejects-negative
  (is (thrown? clojure.lang.ExceptionInfo (fp/boustrophedon -1 4))))

(deftest path-length-and-budget-scale
  (testing "longer grids cost more path; budget scales per-pane (G2)"
    (let [p1 (fp/boustrophedon 2 2)
          p2 (fp/boustrophedon 4 4)]
      (is (< (fp/path-length-m p1 4.0 3.0) (fp/path-length-m p2 4.0 3.0)))
      (let [b (fp/consumable-budget 16 0.25 4.0)]
        (is (= 16 (:panes b)))
        (is (= 4.0 (:water-l b)))
        (is (= 64.0 (:agent-ml b)))))))

(deftest coverage-detects-missing-and-duplicate
  (testing "an incomplete or double-pass path is not complete"
    (is (not (:complete? (fp/coverage [[0 0] [0 1]] 2 2))))         ; missing
    (is (not (:complete? (fp/coverage [[0 0] [0 0] [0 1] [1 0] [1 1]] 2 2)))))) ; dup

;; ── wind_envelope (★ G5) ─────────────────────────────────────────────────────
(deftest sway-grows-with-wind-and-rope
  (testing "sway amplitude grows with wind speed and rope length"
    (is (< (we/sway-amplitude-m 50.0 14.0 4.0)
           (we/sway-amplitude-m 50.0 14.0 8.0)))      ; more wind
    (is (< (we/sway-amplitude-m 25.0 14.0 6.0)
           (we/sway-amplitude-m 80.0 14.0 6.0)))      ; more rope
    (is (thrown? clojure.lang.ExceptionInfo (we/sway-amplitude-m 50.0 0.0 4.0)))))  ; bad mass

(deftest wind-work-stop-raises-above-threshold
  (testing "★ G5 — work-permitted? RAISES at/above the wind work-stop threshold"
    (let [two [{:independent true} {:independent true}]]
      (is (true? (we/work-permitted? {:speed-mps 6.0 :gust-mps 8.0 :stop-threshold-mps 10.0} two)))
      (is (thrown? clojure.lang.ExceptionInfo
                   (we/work-permitted? {:speed-mps 11.0 :stop-threshold-mps 10.0} two)))
      ;; a gust alone above threshold also stops work
      (is (thrown? clojure.lang.ExceptionInfo
                   (we/work-permitted? {:speed-mps 6.0 :gust-mps 12.0 :stop-threshold-mps 10.0} two))))))

(deftest single-anchor-plan-raises
  (testing "★ G5 — a descent needs ≥2 independent anchors; single-anchor RAISES"
    (is (not (we/fall-arrest-redundant? [{:independent true}])))
    (is (we/fall-arrest-redundant? [{:independent true} {:independent true}]))
    ;; a non-independent second anchor does not count
    (is (not (we/fall-arrest-redundant? [{:independent true} {:independent false}])))
    (is (thrown? clojure.lang.ExceptionInfo
                 (we/work-permitted? {:speed-mps 3.0 :stop-threshold-mps 10.0}
                                     [{:independent true}])))))

;; ── adhesion (★ G7) ──────────────────────────────────────────────────────────
(deftest adhesion-fos-by-surface
  (testing "glass seals better than stone → higher factor-of-safety"
    (is (> (ad/factor-of-safety 900.0 :glass 14.0)
           (ad/factor-of-safety 900.0 :stone 14.0)))
    (is (thrown? clojure.lang.ExceptionInfo (ad/effective-adhesion-n 900.0 :unknown)))))

(deftest adhesion-safe-raises-below-margin
  (testing "★ G7 — adhesion-safe? RAISES when FoS is below the required factor"
    (is (true? (ad/adhesion-safe? {:suction-force-n 900.0 :surface :glass
                                   :mass-kg 14.0 :required-fos 2.5})))
    ;; porous stone (efficiency 0.45) can't make the margin at this load → RAISE
    (is (thrown? clojure.lang.ExceptionInfo
                 (ad/adhesion-safe? {:suction-force-n 900.0 :surface :stone
                                     :mass-kg 20.0 :required-fos 2.5})))
    ;; too heavy on glass → RAISE
    (is (thrown? clojure.lang.ExceptionInfo
                 (ad/adhesion-safe? {:suction-force-n 900.0 :surface :glass
                                     :mass-kg 60.0 :required-fos 2.5})))))

;; ── G3 privacy-by-construction (structural) ──────────────────────────────────
(def seed (az/load-seed "20-actors/madomori/data/facade.edn"))

(deftest imagery-is-on-device-only-and-no-recognition
  (testing "★ G3 — imagery never leaves the device; no person/interior recognition"
    (let [img (get-in seed [:robot :imagery])]
      (is (true? (:on-device-only img)))
      (is (= :pane-edge-only (:recognition img)))
      ;; the data model cannot express off-device imagery or biometric/interior recognition
      (is (not (contains? img :off-device)))
      (is (not (contains? img :cloud)))
      (is (not= :person (:recognition img)))
      (is (not= :interior (:recognition img)))
      (is (not= :biometric (:recognition img))))
    (testing "the emitted Datom log carries only the on-device imagery flag"
      (let [out (de/emit seed (az/run seed) 1)]
        (is (re-find #":mado\.robot/imagery-on-device true" out))
        (is (nil? (re-find #"(?i)off-device|cloud|biometric|interior" out)))))))

;; ── analyze + datom_emit (end-to-end over the seed) ──────────────────────────
(deftest analyze-end-to-end
  (let [res (az/run seed)]
    (testing "coverage is complete over the full pane grid"
      (is (:complete? (get-in res [:coverage :coverage])))
      (is (= (* (get-in res [:face :rows]) (get-in res [:face :cols]))
             (get-in res [:coverage :coverage :total])))
      (is (pos? (get-in res [:coverage :length-m]))))
    (testing "safety envelope + adhesion present; reference seed is a GO"
      (is (contains? (:envelope res) :permitted?))
      (is (:fall-arrest-redundant? (:envelope res)))          ; 2 independent anchors
      (is (:permitted? (:envelope res)))                       ; wind 6 m/s < 10
      (is (:safe? (:adhesion res)))                            ; glass FoS ≥ 2.5
      (is (true? (:go? res))))))

(deftest analyze-stops-on-high-wind
  (testing "★ G5 — a high-wind seed is NOT a GO (envelope refuses)"
    (let [windy (assoc-in seed [:wind :speed-mps] 14.0)
          res (az/run windy)]
      (is (not (:permitted? (:envelope res))))
      (is (false? (:go? res))))))

(deftest datom-emit-shape
  (let [res (az/run seed)
        out (de/emit seed res 1)]
    (testing "emits ground :add datoms + transient :derived readouts"
      (is (re-find #":mado\.face/surface" out))
      (is (re-find #":mado\.robot/required-fos" out))
      (is (re-find #":en/kind :anchored-by" out))
      (is (re-find #":mado\.anchor/independent" out))
      (is (re-find #":bond/adhesion-fos" out))
      (is (re-find #":bond/go" out))
      (is (re-find #":derived\]" out))
      ;; well-formed EDN vector of datoms
      (is (vector? (clojure.edn/read-string out))))))

;; ── handoff (cross-actor chain edge: madomori→tatekata repair-order) ─────────
(deftest outbound-to-tatekata
  (testing "a detected façade defect → tatekata repair-order intent, source-attributed"
    (let [h (ho/repair-handoff {:pane-id "p-12-04" :defect-kind :cracked-pane :severity :high})]
      (is (= "madomori" (:from-actor h)))
      (is (= "tatekata" (:to-actor h)))
      (is (= :repair-order (:kind h)))
      (is (= :cracked-pane (get-in h [:payload :defect-kind])))
      (is (= :high (get-in h [:payload :severity])))
      (is (= "p-12-04" (get-in h [:payload :pane-id]))))))

(deftest outbound-handoffs-maps-every-defect
  (testing "every detected defect becomes exactly one tatekata repair-order handoff"
    (let [hs (ho/outbound-handoffs [{:pane-id "p-1" :defect-kind :cracked-pane :severity :high}
                                    {:pane-id "p-2" :defect-kind :sealant-failure :severity :medium}
                                    {:pane-id "p-3" :defect-kind :spalling :severity :low}])]
      (is (= 3 (count hs)))
      (is (every? #(= "madomori" (:from-actor %)) hs))
      (is (every? #(= "tatekata" (:to-actor %)) hs))
      (is (every? #(= :repair-order (:kind %)) hs)))))

(deftest handoff-provenance-gate
  (testing "G9 — an orphan handoff (no source/destination) RAISES"
    (is (thrown? clojure.lang.ExceptionInfo (ho/assert-handoff! {:id "x" :to-actor "tatekata"})))
    (is (thrown? clojure.lang.ExceptionInfo (ho/assert-handoff! {:id "x" :from-actor "madomori"})))
    (is (= "madomori" (:from-actor (ho/assert-handoff! {:id "x" :from-actor "madomori" :to-actor "tatekata"}))))))

(deftest handoff-emit-shape
  (testing "emits well-formed EDN :handoff/* 縁 with actor provenance on every edge"
    (let [hs (ho/outbound-handoffs [{:pane-id "p-12-04" :defect-kind :cracked-pane :severity :high}
                                    {:pane-id "p-07-11" :defect-kind :sealant-failure :severity :medium}])
          out (ho/emit hs 1)]
      (is (re-find #":handoff/from-actor" out))
      (is (re-find #":handoff/to-actor" out))
      (is (re-find #"en\.handoff\.madomori\.tatekata\." out))
      (is (vector? (edn/read-string out))))))

(deftest handoff-carries-no-imagery-or-person-data
  (testing "★ G3 — a repair handoff carries ONLY the structural defect descriptor; no imagery/interior/person"
    (let [h (ho/repair-handoff {:pane-id "p-12-04" :defect-kind :cracked-pane :severity :high})
          payload-keys (set (keys (:payload h)))]
      (is (= #{:pane-id :defect-kind :severity} payload-keys))
      ;; no image/photo/imagery/interior/person/biometric/camera keys are representable
      (is (not-any? (fn [k] (re-find #"(?i)image|photo|imagery|interior|person|biometric|camera"
                                     (name k)))
                    payload-keys))
      ;; and the same holds through the emitted Datom log (structural defect only)
      (let [out (ho/emit [h] 1)]
        (is (nil? (re-find #"(?i)image|photo|imagery|interior|person|biometric|camera" out)))))))

;; ── coverage (HONEST occupation sub-task map; G5 sourcing-honesty) ───────────
(deftest coverage-fraction-is-honest
  (testing "coverage fraction in (0,1] and equals covered/total"
    (let [{:keys [total covered coverage]} (cov/report)]
      (is (pos? coverage))
      (is (<= coverage 1.0))
      (is (= coverage (/ (double covered) total))))))

(deftest coverage-gaps-are-exactly-the-uncovered
  (testing "★ G5 — :gaps is exactly the uncovered sub-tasks and is non-empty (partial by design)"
    (let [gaps (:gaps (cov/report))]
      (is (seq gaps))
      (is (= (set (filter (complement :covered?) cov/sub-tasks)) (set gaps)))
      (is (not-any? :covered? gaps)))))

(deftest coverage-covered-names-a-method
  (testing "every covered sub-task names a non-nil backing method"
    (is (every? (fn [s] (some? (:method s)))
                (filter :covered? cov/sub-tasks)))))

;; ── multi_face (multi-face campaign routing) ─────────────────────────────────
(def mf-faces
  [{:face-id :south :access-point [2 0]  :rows 12 :cols 8}
   {:face-id :north :access-point [2 30] :rows 12 :cols 8}
   {:face-id :east  :access-point [20 0] :rows 10 :cols 6}])

(def mf-pane {:pane-h-m 1.4 :pane-w-m 1.0})

(deftest face-sequence-visits-every-face-once
  (testing "the sequence visits every face exactly once (no skip, no repeat)"
    (let [{:keys [order reposition-distance]} (mf/face-sequence mf-faces [0 0])]
      (is (= (count mf-faces) (count order)))
      (is (= (set (map :face-id mf-faces)) (set order)))
      (is (= (count order) (count (distinct order))))
      (is (pos? reposition-distance)))))

(deftest face-sequence-nearest-first
  (testing "nearest-neighbour puts the closest access point first"
    ;; from dock [0 0]: south [2 0] is nearest (d=2), then east [20 0], then north [2 30]
    (let [{:keys [order]} (mf/face-sequence mf-faces [0 0])]
      (is (= :south (first order)))
      ;; explicit: a face whose access point is the closest to the origin leads
      (let [closer [{:face-id :far  :access-point [99 99] :rows 2 :cols 2}
                    {:face-id :near :access-point [1 0]   :rows 2 :cols 2}]]
        (is (= :near (first (:order (mf/face-sequence closer [0 0])))))))))

(deftest campaign-coverage-sums-per-face-lengths
  (testing "campaign coverage total = Σ per-face path lengths (positive)"
    (let [camp (mf/campaign-coverage mf-faces mf-pane [0 0])
          sum-per-face (reduce + 0.0 (map :coverage-length-m (:per-face camp)))]
      (is (pos? (:coverage-length-m camp)))
      (is (= (:coverage-length-m camp) sum-per-face))
      (is (every? #(pos? (:coverage-length-m %)) (:per-face camp)))
      ;; total = coverage + reposition, and exceeds coverage alone (reposition > 0)
      (is (= (:total-length-m camp)
             (+ (:coverage-length-m camp) (:reposition-distance camp))))
      (is (> (:total-length-m camp) (:coverage-length-m camp))))))

(deftest multi-face-carries-no-imagery-or-person-data
  (testing "★ G3 — no imagery/person/interior/biometric key in any returned map"
    (let [camp (mf/campaign-coverage mf-faces mf-pane [0 0])
          ks (fn collect [x]
               (cond
                 (map? x) (concat (mapcat (fn [[k v]] (cons k (collect v))) x))
                 (sequential? x) (mapcat collect x)
                 :else nil))
          all-keys (->> (concat (ks camp) (ks (mf/face-sequence mf-faces [0 0])))
                        (filter keyword?))]
      (is (seq all-keys))
      (is (not-any? (fn [k] (re-find #"(?i)image|photo|imagery|interior|person|biometric|camera"
                                     (name k)))
                    all-keys)))))

;; ── water_recovery (★ G2 eco — runoff/detergent capture water balance) ───────
(deftest water-balance-fraction-and-loss
  (testing "recovery-fraction = captured/applied; lost = applied - captured"
    (let [b (wr/water-balance {:applied-l 8.0 :captured-l 6.0 :detergent-ml 64.0})]
      (is (= 0.75 (:recovery-fraction b)))
      (is (= 2.0 (:lost-l b)))
      ;; a dry pass cannot be balanced
      (is (thrown? clojure.lang.ExceptionInfo (wr/water-balance {:applied-l 0.0 :captured-l 0.0}))))))

(deftest water-balance-compliance-by-threshold
  (testing "★ G2 — above the eco floor is compliant?, below is not (non-raising)"
    (is (:compliant? (wr/water-balance {:applied-l 8.0 :captured-l 6.4})))        ; 80% ≥ 70%
    (is (not (:compliant? (wr/water-balance {:applied-l 8.0 :captured-l 4.0}))))  ; 50% < 70%
    ;; an explicit stricter floor flips a borderline pass non-compliant
    (is (not (:compliant? (wr/water-balance {:applied-l 8.0 :captured-l 6.4 :min-recovery 0.9}))))))

(deftest assert-compliant-raises-below-floor
  (testing "★ G2 — assert-compliant! RAISES below the floor, returns the balance above"
    (let [b (wr/assert-compliant! {:applied-l 8.0 :captured-l 6.4 :detergent-ml 64.0})]
      (is (:compliant? b))
      (is (= 0.8 (:recovery-fraction b))))
    ;; a leaky pass that escapes its detergent runoff must surface, not be forced
    (is (thrown? clojure.lang.ExceptionInfo
                 (wr/assert-compliant! {:applied-l 8.0 :captured-l 4.0 :detergent-ml 64.0})))))

(deftest water-balance-carries-no-imagery-or-person-data
  (testing "★ G3 — the balance map is purely fluid quantities; no imagery/person/interior key"
    (let [b (wr/water-balance {:applied-l 8.0 :captured-l 6.0 :detergent-ml 64.0})
          ks (keys b)]
      (is (every? keyword? ks))
      (is (not-any? (fn [k] (re-find #"(?i)image|photo|imagery|interior|person|biometric|camera"
                                     (name k)))
                    ks)))))

(let [{:keys [fail error]} (run-tests 'madomori.methods.test-madomori)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
