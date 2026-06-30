(ns etzhayyim.genome
  "kotoba-genome W2 — the generalized closed learning loop (ADR-2606302205 D1).

  Generalizes the ibuki active-inference + co-scientist + kaizen loop OUT of
  20-actors/ibuki/methods/{react_loop,coscientist,metabolism}.cljc into a PURE,
  actor-agnostic library that any actor — and the RESIDENT organism heartbeat —
  folds its REAL observations through, so the running thing actually LEARNS
  (today the resident loop only measures; the learning loop is a separate cell it
  never calls — this closes that gap).

  One beat on a real reading: (1) Brier proper-SCORE the previous, pre-registered
  prediction against the new reading (leak-free: the prediction was recorded
  BEFORE the outcome), (2) kaizen-UPDATE the chosen mechanism's weight (verified →
  amplified, falsified → suppressed, bounded), (3) DECIDE the next mechanism by
  weight × base-value × prior-consensus confidence, (4) pre-register the next
  prediction. `prior-consensus` (ADR-2605232200 — the loop-closure that was
  1/18342) folds the outcome history into a per-mechanism consensus the next
  decision reads; that is what makes observe→update→act-differently a CLOSED loop.

  Pure: plain-map state, no I/O, deterministic (logical beat = history length),
  append-only history → folding the same readings yields the same state
  (crash-resume / verify-chain). The CALLER supplies the catalog (mechanisms +
  base value) and the reading (a scalar the loop predicts will rise), and owns any
  outward action — this library never acts; it learns + RECOMMENDS (dry-run; real
  self-modification stays proposal-only + human/Council-gated, ADR-2605240200).
  .cljc so it runs on JVM/bb, cljs and WASM (the kotoba-lang behavior-lib seed)."
  (:require [clojure.string :as str]))

(def learning-rate 0.4)
(def weight-floor 0.25)
(def weight-ceil 2.0)

(defn- clampd [lo hi x] (max (double lo) (min (double hi) (double x))))

;; state = {:beat n
;;          :weights {mechanism w}
;;          :pending {:mechanism kw :predicted-up p :reading-at-act r}  ; the leak-free pre-registration
;;          :history [{:beat n :reading r :chosen kw :predicted-up p
;;                     :scored {:mechanism kw :actual-up bool :brier b :score s}?} ...]}

(defn prior-consensus
  "Fold the outcome history into a per-mechanism consensus the next decision reads
  (ADR-2605232200). Returns {mechanism {:n :wins :confidence :mean-score}}.
  confidence = Laplace-smoothed win-rate; a never-tried mechanism is absent
  (callers default it to 0.5 = neither favoured nor penalised)."
  [{:keys [history]}]
  (reduce
   (fn [m {:keys [scored]}]
     (if-not scored
       m
       (let [mech (:mechanism scored)
             e    (get m mech {:n 0 :wins 0 :sum 0.0})
             e'   {:n    (inc (:n e))
                   :wins (+ (:wins e) (if (:actual-up scored) 1 0))
                   :sum  (+ (:sum e) (double (:score scored)))}]
         (assoc m mech (assoc e'
                              :confidence (/ (+ (:wins e') 0.5) (+ (:n e') 1.0))
                              :mean-score (/ (:sum e') (double (:n e'))))))))
   {}
   history))

(defn weight-of [state mech] (double (get-in state [:weights mech] 1.0)))

(defn decide
  "Rank the catalog by weight × base-value × (0.5 + consensus-confidence); choose
  the top. catalog = [{:mechanism kw :base v} …]. Returns
  {:chosen kw :ranked [...] :predicted-up p}. predicted-up = P(reading rises) in
  [0.05,1.0], blending the chosen mechanism's consensus confidence with its weight."
  [state catalog _reading]
  (let [pc (prior-consensus state)
        ranked (->> catalog
                    (map (fn [{:keys [mechanism base]}]
                           (let [w    (weight-of state mechanism)
                                 conf (double (get-in pc [mechanism :confidence] 0.5))]
                             {:mechanism mechanism :base base :weight w :confidence conf
                              :utility (* w (double base) (+ 0.5 conf))})))
                    (sort-by (juxt (comp - :utility) (comp str :mechanism))))
        chosen (first ranked)
        pred   (clampd 0.05 1.0 (* (:confidence chosen)
                                   (clampd 0.0 1.0 (/ (:weight chosen) weight-ceil))))]
    {:chosen (:mechanism chosen) :ranked ranked :predicted-up pred}))

(defn score-pending
  "Brier proper-score the pre-registered prediction against the new reading. nil
  when there is no pending prediction (the first beat). Pure."
  [{:keys [pending]} reading]
  (when pending
    (let [actual-up (> (double reading) (double (:reading-at-act pending)))
          o (if actual-up 1.0 0.0)
          p (double (:predicted-up pending))
          brier (* (- p o) (- p o))]
      {:mechanism (:mechanism pending) :actual-up actual-up
       :brier brier :score (- 1.0 brier)})))

(defn update-weights
  "Kaizen: a mechanism whose prediction VERIFIED (score>0.5) is amplified, a
  falsified one suppressed, bounded to [weight-floor, weight-ceil]. Pure."
  [weights mech score]
  (let [w  (double (get weights mech 1.0))
        w' (clampd weight-floor weight-ceil (+ w (* learning-rate (- (double score) 0.5))))]
    (assoc weights mech w')))

(defn beat
  "One closed beat on a REAL `reading` (a scalar the loop predicts will rise):
  score the previous prediction, kaizen-update, decide the next, pre-register.
  Returns the new state (append-only history; deterministic; no I/O, no action)."
  [{:keys [beat] :or {beat 0} :as state} catalog reading]
  (let [scored   (score-pending state reading)
        weights' (if scored
                   (update-weights (:weights state {}) (:mechanism scored) (:score scored))
                   (:weights state {}))
        state1   (assoc state :weights weights')
        {:keys [chosen ranked predicted-up]} (decide state1 catalog reading)
        n (inc beat)]
    {:beat n
     :weights weights'
     :pending {:mechanism chosen :predicted-up predicted-up :reading-at-act reading}
     :recommendation {:mechanism chosen :predicted-up predicted-up
                      :ranked (vec (take 3 ranked)) :status :dry-run}
     :history (conj (vec (:history state))
                    (cond-> {:beat n :reading reading :chosen chosen :predicted-up predicted-up}
                      scored (assoc :scored scored)))}))

(defn replay
  "Fold a sequence of readings from a seed state — deterministic: replaying the
  same readings yields the same state (crash-resume / verify-chain discipline)."
  [seed catalog readings]
  (reduce (fn [s r] (beat s catalog r)) seed readings))

(def empty-state {:beat 0 :weights {} :pending nil :history []})
