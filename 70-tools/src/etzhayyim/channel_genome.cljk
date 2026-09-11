(ns etzhayyim.channel-genome
  "kotoba-genome W1×W2 — an actor learns WHICH channel to grow on (ADR-2606302205).

  W1 (etzhayyim.channel) gave every actor N egress channels (at-proto / email /
  telegram / x / line). W2 (etzhayyim.genome) is a PURE closed learning loop. This
  bridges them: each channel gets its OWN genome that folds that channel's real
  growth reading (reach / replies / new followers — a scalar that RISES when the
  channel grew the actor). `preferred-channel` then recommends the channel with the
  highest REALISED growth-rate — the genome's prior-consensus up-rate
  (ADR-2605232200, the loop-closure signal), NOT merely the most predictable channel.
  (The genome's Brier weight rewards prediction accuracy, which is orthogonal to how
  much a channel actually grows the actor; channel choice must reward realised
  growth, so up-rate is primary and weight only a tiebreak.)

  Pure + deterministic (folding the same readings yields the same recommendation) and
  RECOMMENDS only (dry-run): the actor owns the outward post, and any self-
  modification stays proposal-only + human/Council-gated (ADR-2605240200). The
  content/disclosure catastrophe scan (etzhayyim.channel) is unchanged and still
  fronts every real emit — this only chooses WHERE to grow, never WHAT to say.
  .cljc so it runs on JVM/bb, cljs and WASM (the kotoba-lang behavior-lib seed)."
  (:require [etzhayyim.genome :as genome]))

;; The W1 reference channels (mirror etzhayyim.channel/default-registry!); the
;; fallback catalog when a caller does not name a channel set.
(def default-channels [:at-proto :email :telegram :x :line])

(defn- channels-of [channels] (or (seq channels) default-channels))

(def empty-state {:channels {} :round 0})

(defn beat-channels
  "Fold one round of per-channel growth readings. `readings` = {channel scalar} — a
  scalar that RISES when that channel grew the actor. Each channel folds its own
  reading through its OWN genome (single-mechanism catalog = the channel itself), so
  the channels learn independently. Channels absent from `readings` are untouched.
  Returns the new {:channels {channel genome-state} :round n}. Pure."
  [{:keys [channels round] :or {round 0}} readings]
  {:round    (inc round)
   :channels (reduce-kv
              (fn [m c r]
                (assoc m c (genome/beat (get channels c genome/empty-state)
                                        [{:mechanism c :base 1.0}] r)))
              channels
              readings)})

(defn channel-growth
  "Per-channel realised-growth summary from its genome (prior-consensus): the
  up-rate = Laplace-smoothed frequency that the channel's reading ROSE (the honest
  growth signal; 0.5 = untried), the count of scored beats, and the prediction weight
  as a secondary confidence. Pure."
  [{:keys [channels]} c]
  (let [gs (get channels c)
        e  (get (when gs (genome/prior-consensus gs)) c)]
    {:channel c
     :up-rate (double (get e :confidence 0.5))
     :n       (long (get e :n 0))
     :weight  (if gs (genome/weight-of gs c) 1.0)}))

(defn preferred-channel
  "Recommend the channel to grow on next: argmax by realised growth up-rate, then by
  prediction weight, then name. Reads a folded state (defaults to the channels seen,
  else the W1 defaults); pure, dry-run recommendation. Returns
  {:channel kw :ranked [{:channel :up-rate :n :weight}…] :status :dry-run}."
  [{:keys [channels] :as state} & {chs :channels}]
  (let [cs     (channels-of (or chs (keys channels)))
        scored (mapv #(channel-growth state %) cs)
        ranked (sort-by (juxt (comp - :up-rate) (comp - :weight) (comp str :channel)) scored)]
    {:channel (:channel (first ranked)) :ranked (vec ranked) :status :dry-run}))
