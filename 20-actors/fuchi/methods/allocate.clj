;; allocate.clj — 扶持 (fuchi) maintainer sustenance allocation.
;;
;; Clojure port of allocate.py (ADR-2606052300), Wave 1 of the clj-native migration
;; (ADR-2606142300) — the FIRST fuchi clj method. THE HEART of the actor and the charter-clean
;; inverse of an investment fund's cap-table: for a cohort of covenant-bound maintainers (信者)
;; who keep etzhayyim's actors alive, computes each one's tenure weight (the Displacement-Dividend
;; curve), share of cohort PRIORITY (sums to 1, NOT cash), priority rank under a scarce stage cap,
;; and a decaying in-kind sustenance floor.
;;
;; The invariants that make this charter-clean and NOT an investment vehicle:
;;   * cash≡0 structurally for every allocation (ADR-2605301020 N1);
;;   * the instrument ∈ {in-kind-grant sustenance tooling-access compute-access} — equity / debt /
;;     convertible / revenue-share / carry / dividend … RAISE (G1, Charter-Rider §2(b));
;;   * the maintainer's work product is commons (owns-payoff structurally false, G5).
;; No NAV, IRR, exit, or liquidation. A "share" governs only SEQUENCING + the in-kind floor.
;;
;; Float math (Math/log1p) is byte-equivalent with allocate.py; round(x,6)/int(round(x)) mirror
;; Python's half-to-even. stdlib only, deterministic.
(ns fuchi.methods.allocate
  (:require [clojure.string :as str])
  (:import [java.math BigDecimal RoundingMode]))

(def tenure-cap-years 40.0)
(def hazard-min 1.0)
(def hazard-max 2.0)
(def horizon-years 5.0)

(def allowed-instruments #{"in-kind-grant" "sustenance" "tooling-access" "compute-access"})  ; G1
(def forbidden-instruments
  #{"equity" "debt" "convertible" "revenue-share" "profit-claim" "carry" "dividend"
    "loan" "interest" "warrant" "option" "exit"})

(defn assert-instrument
  "G1 INVARIANT — only a sustenance instrument is allocatable. Anything resembling an
   investment / debt / return claim RAISES (扶持 is sustenance, not a fund)."
  [instrument]
  (let [instr (str/lower-case (str/replace (str (or instrument "")) #"^:+" ""))]
    (when (forbidden-instruments instr)
      (throw (ex-info (str "G1: instrument " (pr-str instr) " is an investment/return vehicle — "
                           "UNREPRESENTABLE (扶持 is sustenance, not a fund; Charter-Rider §2(b))") {})))
    (when-not (allowed-instruments instr)
      (throw (ex-info (str "G1: instrument " (pr-str instr) " not in " allowed-instruments) {})))
    instr))

(defn- round-n [x scale]
  (.doubleValue (.setScale (BigDecimal/valueOf (double x)) (int scale) RoundingMode/HALF_EVEN)))

(defn- round-int [x]  ; Python int(round(x)) — half-to-even, then integer
  (.longValue (.setScale (BigDecimal/valueOf (double x)) 0 RoundingMode/HALF_EVEN)))

(defn- capped-tenure-years [tenure-months] (min (/ tenure-months 12.0) tenure-cap-years))

(defn- hazard [hazard-permille]
  (let [h (/ hazard-permille 1000.0)]
    (when-not (<= hazard-min h hazard-max) (throw (ex-info (str "hazard out of [1.0,2.0]: " h) {})))
    h))

(defn tenure-weight
  "w = ln(1 + min(tenure-years, cap)) × hazard. Log compresses the gradient so a 40y maintainer
   is ~2× a 5y one (not 8×) — honours service without a per-person income leaderboard."
  [m]
  (* (Math/log1p (capped-tenure-years (:tenure-months m))) (hazard (:hazard-permille m))))

(defn floor-decay
  "decay(t) = clamp(1 − t/HORIZON, 0, 1). The sustenance floor tapers over 5 years toward BHI."
  [elapsed-months]
  (let [t (/ elapsed-months 12.0)]
    (max 0.0 (min 1.0 (- 1.0 (/ t horizon-years))))))

(defn make-allocation
  "Construct an allocation, asserting the structural proofs (cash≡0, no-server-key, instrument)."
  [{:keys [cash-usd-micros server-held-key instrument] :or {cash-usd-micros 0 server-held-key false} :as a}]
  (when (not= 0 cash-usd-micros)
    (throw (ex-info "cash≡0 INVARIANT (G2/N4): 扶持 never disburses cash" {})))
  (when server-held-key
    (throw (ex-info "no-server-key INVARIANT (G9): allocation is member/Council-signed" {})))
  (assert-instrument instrument)
  (merge {:cash-usd-micros 0 :server-held-key false} a))

(defn allocate
  "Allocate tenure-weighted in-kind sustenance over a maintainer cohort. Only `vowed` maintainers
   join the tenure-weighted share pool (covenant gate, G4); `outreach` maintainers receive a
   minimal floor (share 0) until they vow. Raises on owns-payoff (G5) or an investment instrument (G1)."
  ([cohort stage-ceiling] (allocate cohort stage-ceiling 0 "sustenance"))
  ([cohort stage-ceiling elapsed-months instrument]
   (let [instr (assert-instrument instrument)]
     (when (some :owns-payoff cohort)
       (throw (ex-info "G5: a maintainer cannot own the payoff — work product is commons" {})))
     (let [vowed   (filter #(= "vowed" (:covenant %)) cohort)
           total-w (reduce + 0.0 (map tenure-weight vowed))
           decay   (floor-decay elapsed-months)
           ranked  (sort-by tenure-weight (fn [a b] (compare b a)) vowed)  ; desc, stable
           rank-of (into {} (map-indexed (fn [i m] [(:did m) (inc i)]) ranked))
           allocs  (mapv
                    (fn [m]
                      (if (= "vowed" (:covenant m))
                        (let [w (tenure-weight m)]
                          (make-allocation
                           {:maintainer-did (:did m) :instrument instr
                            :weight (round-n w 6)
                            :share (round-n (if (pos? total-w) (/ w total-w) 0.0) 6)
                            :priority-rank (rank-of (:did m))
                            :floor-usd-micros-yr (round-int (* (min (:prior-imputed-usd-micros-yr m 0) stage-ceiling) decay))
                            :cash-usd-micros 0 :server-held-key false}))
                        (make-allocation
                         {:maintainer-did (:did m) :instrument instr
                          :weight 0.0 :share 0.0
                          :priority-rank (inc (count vowed))
                          :floor-usd-micros-yr (round-int (* (min (:prior-imputed-usd-micros-yr m 0) stage-ceiling) decay 0.25))
                          :cash-usd-micros 0 :server-held-key false})))
                    cohort)]
       ;; vowed allocations first (priority order), then outreach
       (vec (sort-by (juxt :priority-rank #(- (:weight %))) allocs))))))

(defn cohort-from-seed
  "Build a cohort from seed :maintainer/* maps (edn keyword-keyed)."
  [records]
  (let [kw (fn [v] (-> (str (or v "")) (str/replace #"^:+" "") (str/split #"/") last str/lower-case))]
    (mapv (fn [r]
            {:did                         (get r :maintainer/did "?")
             :tenure-months               (long (get r :maintainer/tenure-months 0))
             :hazard-permille             (long (get r :maintainer/hazard-permille 1000))
             :maintains                   (vec (get r :maintainer/maintains []))
             :prior-imputed-usd-micros-yr (long (get r :maintainer/prior-imputed-usd-micros-yr 0))
             :covenant                    (kw (get r :maintainer/covenant ":vowed"))
             :owns-payoff                 (boolean (get r :maintainer/owns-payoff false))})
          records)))
