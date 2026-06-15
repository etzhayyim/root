#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (the meyasu 統合 arbitrage fuse/publish/persist core).
(ns meyasu.py.agent
  "meyasu 目安 — unified arbitrage / supply-demand intel orchestrator (ADR-2606073201).

  The 統合 arbitrage actor: meyasu computes NO price or forecast math itself — it FUSES the
  outputs of kakaku 価格 (cross-merchant price SPREAD + present supply/demand index) and mitooshi
  見通し (the forecast DISTRIBUTION of that index) into one per-product public-good intel card,
  then publishes aggregate-first + hands attention cards to a planner. A 目安 (yardstick), NOT a
  trade — it never emits a trade/price-target and settles no money.

  G1 non-speculative · G2 distribution-respecting (a consumed forecast MUST be a distribution
  with a resilience use — a point/speculative forecast is REFUSED) · G3 aggregate-first ·
  G4 non-adjudicating (attention cards ROUTED to a planner; meyasu states, the planner decides) ·
  no-server-key (publication operator-gated; default :draft).

  Run:  bb --classpath 20-actors 20-actors/meyasu/py/agent.clj"
  (:require [clojure.string :as str]))

;; G2 — a consumed forecast's use must be non-speculative (mirrors mitooshi ALLOWED_USE)
(def resilience-uses #{:resilience :planning :nowcast :early-warning :research})
(def buyer-planner "okaimono")      ; G4 buyer side
(def resilience-planner "danjo")    ; G4 accountability/resilience planner
(def trajectory-delta 0.1)

(defn- round4 [x] (/ (Math/round (* (double x) 10000.0)) 10000.0))
(defn- value-error [msg] (throw (ex-info msg {:type :value-error})))

(defn trajectory
  "Forecast supply/demand mean vs present index → tightening / easing / stable (or unknown)."
  [now-index forecast-mean]
  (if (or (nil? now-index) (nil? forecast-mean))
    "unknown"
    (let [d (- (double forecast-mean) (double now-index))]
      (cond (> d trajectory-delta) "tightening"
            (< d (- trajectory-delta)) "easing"
            :else "stable"))))

(defn fuse-one
  "Fuse one product's kakaku + mitooshi records into a unified arbitrage-intel card. Raises
  (value-error) if the forecast is a point assertion or a speculative use (G2)."
  [item]
  (let [k (get item :kakaku {}) f (get item :mitooshi {})]
    (when (seq f)
      (when (:pointAsserted f)
        (value-error "G2: consumed forecast is point-asserted (distribution-only)"))
      (when (and (:use f) (not (resilience-uses (:use f))))
        (value-error (str "G2: forecast use " (pr-str (:use f)) " is not in the resilience set"))))
    (let [now-index (:supplyDemandIndex k) mean (:mean f) sd (:sd f)
          traj (trajectory now-index mean)
          notable (boolean (:notable k))
          attention (and notable (= traj "tightening"))]
      {:productId (:productId item)
       :priceSpread (:spread k) :spreadFraction (:spreadFraction k) :notableSpread notable
       :cheapestMerchant (:cheapestMerchant k) :supplyDemandNow now-index :reading (:reading k)
       :forecastBand (when (and (some? mean) (some? sd)) [(round4 (- mean sd)) (round4 (+ mean sd))])
       :trajectory traj :attention attention
       :routeTo (if attention resilience-planner buyer-planner)
       :intent "buyer-transparency+supply-resilience"})))

(defn handle-fuse
  "Fuse a batch of {:kakaku :mitooshi} records into cards; a G2-violating forecast is refused
  per-item with a reason (never silently dropped)."
  [state]
  (let [{:keys [cards refused]}
        (reduce (fn [acc item]
                  (try (update acc :cards conj (fuse-one item))
                       (catch clojure.lang.ExceptionInfo e
                         (update acc :refused conj {:productId (:productId item) :reason (.getMessage e)}))))
                {:cards [] :refused []} (get state :items []))]
    (assoc state :cards cards :refused refused)))

(defn compose-card-post
  "Compose ONE aggregate-first post from a unified card (buyer transparency + resilience framing;
  no urgency / affiliate / purchase nudge / trade call — G1/G3)."
  [card]
  (let [frac-pct (round4 (* (double (or (:spreadFraction card) 0.0)) 100))]
    {:text (str "目安: " (or (:productId card) "product") " の現在の最安価格差は約 " frac-pct "%、"
                "供給/需要は " (or (:reading card) "balanced") "、見通しは " (or (:trajectory card) "unknown")
                "。 公共的な価格・供給の透明化であり、売買の勧誘ではありません。")
     :shape "aggregate" :lexicon "app.bsky.feed.post" :nudge false :affiliate false
     :routeTo (:routeTo card)}))

(defn handle-publish
  "Compose aggregate posts from fused cards + (optionally) publish. Attention cards are handed
  off to their planner (G4); publication is operator-gated (no-server-key) — without operatorRef
  posts are :draft. Aggregate-share is 100% (never targets an individual)."
  [state]
  (let [op (:operatorRef state)
        posts (mapv (fn [c] (assoc (compose-card-post c) :state (if op "posted" "draft")))
                    (get state :cards []))
        handoffs (vec (for [c (get state :cards []) :when (:attention c)]
                        {:productId (:productId c) :routeTo (:routeTo c)
                         :reason "notable spread + tightening forecast → resilience review"}))]
    (assoc state :posts posts :handoffs handoffs :broadcast (boolean op)
           :aggregateSharePct (if (seq posts) 100 0))))

(defn card-to-datoms
  "Flatten a fused card into kotoba Datoms ([eid attr value]). A forecast is written as a BAND
  (forecast-band-lo/hi), NEVER a point (G1/G2). Pure."
  [card observed-at]
  (let [pid (or (:productId card) "unknown")
        eid (str "meyasu.card." pid "." observed-at)
        band (:forecastBand card)
        base [[eid :meyasu.card/id eid]
              [eid :meyasu.card/product pid]
              [eid :meyasu.card/price-spread (long (or (:priceSpread card) 0))]
              [eid :meyasu.card/spread-fraction (double (or (:spreadFraction card) 0.0))]
              [eid :meyasu.card/notable-spread (boolean (:notableSpread card))]
              [eid :meyasu.card/supply-demand-now (double (or (:supplyDemandNow card) 0.0))]
              [eid :meyasu.card/reading (keyword (or (:reading card) "balanced"))]
              [eid :meyasu.card/trajectory (keyword (or (:trajectory card) "unknown"))]
              [eid :meyasu.card/attention (boolean (:attention card))]
              [eid :meyasu.card/route-to (or (:routeTo card) buyer-planner)]
              [eid :meyasu.card/intent (or (:intent card) "buyer-transparency+supply-resilience")]
              [eid :meyasu.card/observed-at observed-at]]]
    (if band
      (conj base [eid :meyasu.card/forecast-band-lo (double (first band))]
            [eid :meyasu.card/forecast-band-hi (double (second band))])
      base)))

(defn handle-persist
  "Build the kotoba Datom transaction for the fused cards. no-server-key: the tx is RETURNED,
  not written, unless an operatorRef is present (G6/G11 outward-gated)."
  [state]
  (let [observed-at (get state :observedAt "1970-01-01T00:00:00Z")
        datoms (vec (mapcat #(card-to-datoms % observed-at) (get state :cards [])))
        op (:operatorRef state)]
    (assoc state :datoms datoms :datomCount (count datoms)
           :writeState (if op "committed" "tx-only") :operatorRef op)))

(defn main [& _]
  (let [item {:productId "demo" :kakaku {:spread 700 :spreadFraction 0.22 :notable true
                                         :cheapestMerchant "a_com" :supplyDemandIndex 0.1 :reading "balanced"}
              :mitooshi {:mean 0.6 :sd 0.3 :use :resilience :pointAsserted false}}
        fused (handle-fuse {:items [item]})
        pub (handle-publish fused)]
    (println (format "meyasu fuse→publish: %d card(s), %d refused, %d handoff(s), aggregate %d%%"
                     (count (:cards fused)) (count (:refused fused)) (count (:handoffs pub))
                     (:aggregateSharePct pub)))
    (println "  card:" (pr-str (first (:cards fused))))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
