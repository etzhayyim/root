;; couple.clj — 扶持 (fuchi) R1(d): Displacement-Dividend cohort coupling.
;;
;; Clojure port of couple.py (ADR-2606052300 R1 + ADR-2606032130 G2), Wave 1 of the clj-native
;; migration (ADR-2606142300). The structural join between the labor-liberation mission's two
;; halves: a displacing actor (sanae/hataori/kiyome/tazuna…) automates human toil → its SURPLUS
;; becomes a donation → TitheRouter 10% split → a per-cohort Public-Fund EARMARK that is the
;; imputed-value BUDGET CEILING 扶持's in-kind sustenance for that cohort draws on.
;;
;; **G2 coupling gate** (ADR-2606032130): NO live displacement without a funded cohort. A
;; displacement event is ADMISSIBLE only if its cohort earmark is FUNDED and the committed in-kind
;; sustenance floor is ≤ the earmark; otherwise REFUSED — the actor may not shed human toil faster
;; than the Public Fund can sustain the people affected.
;;
;; Honest note on cash: surplus→donation is a REAL USDC inflow into the Public Fund (donations are
;; USDC — allowed). What the displaced worker RECEIVES is still in-kind, cash≡0 (enforced at
;; allocate/route/book). The earmark is a budget ceiling in imputed-value USD micros/yr. stdlib only.
(ns fuchi.methods.couple
  (:require [fuchi.methods.live-gate :as lg]))

(def tithe-bps 1000)  ; 10% TitheRouter split (ADR-2605192130); basis points of 10000

(defn make-displacement-event
  [{:keys [surplus-usd-micros-yr displaced-count] :or {surplus-usd-micros-yr 0 displaced-count 0} :as e}]
  (when (< surplus-usd-micros-yr 0) (throw (ex-info "surplus cannot be negative" {})))
  (when (< displaced-count 0) (throw (ex-info "displaced_count cannot be negative" {})))
  (merge {:funded false} e))

(defn make-cohort-earmark
  [{:keys [gross-usd-micros-yr tithe-usd-micros earmark-usd-micros-yr] :as e}]
  ;; exact integer split — gross = tithe + earmark (no rounding leak)
  (when (not= (+ tithe-usd-micros earmark-usd-micros-yr) gross-usd-micros-yr)
    (throw (ex-info "TitheRouter split INVARIANT: gross must equal tithe + earmark exactly" {})))
  e)

(defn earmark-from-surplus
  "Apply the 10% TitheRouter split to a displacing actor's surplus → a per-cohort earmark.
   gross = tithe + earmark, exact integer split (no rounding leak)."
  [event]
  (let [gross   (long (:surplus-usd-micros-yr event))
        tithe   (quot (* gross tithe-bps) 10000)
        earmark (- gross tithe)]
    (make-cohort-earmark
     {:cohort-id (:cohort-id event)
      :displacing-actor (:displacing-actor event)
      :gross-usd-micros-yr gross
      :tithe-usd-micros tithe
      :earmark-usd-micros-yr earmark
      :funded (boolean (:funded event))})))

(defn coupling-gate
  "G2 coupling gate — is this displacement admissible? Admissible iff the earmark is FUNDED and the
   committed in-kind sustenance floor is within it."
  [event earmark committed-floor-usd-micros-yr]
  (let [committed (long committed-floor-usd-micros-yr)
        earmark-amt (:earmark-usd-micros-yr earmark)
        base {:event (:displacing-actor event) :cohort (:cohort-id event) :committed committed}]
    (cond
      (not (:funded earmark))
      (assoc base :headroom 0 :admissible false
             :reason (str "G2: no funded cohort earmark — displacement REFUSED "
                          "(surplus→donation has not landed in the Public Fund)"))
      (> committed earmark-amt)
      (assoc base :headroom (- earmark-amt committed) :admissible false
             :reason (str "G2: committed sustenance " committed " exceeds funded earmark "
                          earmark-amt " — displacement REFUSED (cannot shed toil faster than "
                          "the cohort can be sustained)"))
      :else
      (assoc base :headroom (- earmark-amt committed) :admissible true
             :reason "G2: funded cohort earmark covers the committed sustenance — admissible"))))

(defn events-from-seed
  [records]
  (mapv (fn [r]
          (make-displacement-event
           {:displacing-actor (get r :event/displacing-actor "?")
            :cohort-id (get r :event/cohort-id "?")
            :displaced-count (long (get r :event/displaced-count 0))
            :surplus-usd-micros-yr (long (get r :event/surplus-usd-micros-yr 0))
            :funded (boolean (get r :event/funded false))}))
        records))

(defn commit-live
  "Bind a displacement to its funded cohort earmark (LIVE) via the R2 gate, or refuse. The G2
   coupling gate still applies strictly (no live displacement without a funded cohort)."
  [event earmark committed-floor-usd-micros-yr gate]
  (lg/require-gate gate)                                 ; couple leg requires Lv7 (autonomous R2)
  (let [g (coupling-gate event earmark committed-floor-usd-micros-yr)]
    (when-not (:admissible g)
      (throw (ex-info (:reason g) {:g2-refused true})))  ; G2 — no live displacement without funded cohort
    {:cohort-id (:cohort-id earmark) :displacing-actor (:displacing-actor earmark)
     :committed-usd-micros-yr (long committed-floor-usd-micros-yr)
     :operator-did (:operator-did gate) :council-level (:council-level gate)
     :member-signature (:member-signature gate) :admissible true}))
