#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (the kakaku price-difference / supply-demand core).
(ns kakaku.py.agent
  "kakaku 価格 — global price-difference / supply-demand intel core (ADR-2605091200).

  Handlers over one EAVT graph of products / merchants / offers / append-only priceHistory:
  handle-rank (cheapest / best-overall / suspicious on LANDED price) · handle-arbitrage
  (cross-merchant + cross-region price SPREAD) · handle-supply-demand (availability +
  price-velocity → a bounded supply/demand index) · handle-demand (observation-frequency proxy,
  never a forecast) · handle-intel (aggregate-first transparency report) · handle-social
  (charter-clean aggregate post). These are exactly the kakaku signals meyasu 目安 fuses.

  G2 non-speculative (surfaces price DIFFERENCE for the buyer + routes scarcity to resilience;
  never a buy/sell signal; forecasting is mitooshi's job) · G3 no ads/affiliate (landed-price +
  trust only) · G4 aggregate-first · no-server-key (live social post operator-gated). Narration is
  the Murakumo `llm` host binding (nil in the clj port — no external LLM).

  Run:  bb --classpath 20-actors 20-actors/kakaku/py/agent.clj"
  (:require [clojure.string :as str]))

(def social-weekly-ceiling 100)
(def notable-spread-fraction 0.15)
(def ^:private availability-rank
  {"in-stock" 2 "preorder" 1 "backorder" 0 "out-of-stock" -2 "unknown" -1})

(defn- r1 [x] (/ (Math/round (* (double x) 10.0)) 10.0))
(defn- r4 [x] (/ (Math/round (* (double x) 10000.0)) 10000.0))

(defn landed-price
  "price + shippingFee in minor units — the single cross-site comparison basis (never sticker)."
  [offer]
  (+ (long (or (:price offer) 0)) (long (or (:shippingFee offer) 0))))

(defn- best-overall-score [offer merchants]
  (let [landed (landed-price offer)
        avail (get availability-rank (get offer :availability "unknown") -1)
        eta (double (or (:deliveryEtaDays offer) 14))
        trust (double (or (:reputationScore (get merchants (:merchantId offer) {})) 0.5))
        price-reward (/ 1000000.0 (+ landed 1.0))]
    (+ price-reward (* avail 2.0) (- (* eta 0.05)) (* trust 3.0))))

(defn- median [xs]
  (let [s (vec (sort xs)) n (count s)]
    (cond (zero? n) 0
          (odd? n) (nth s (quot n 2))
          :else (/ (+ (nth s (dec (quot n 2))) (nth s (quot n 2))) 2.0))))

(defn- suspicious? [offer landed-vals merchants]
  (let [m (get merchants (:merchantId offer) {})]
    (cond
      (not (#{nil "active"} (:status m))) true
      (or (not (:availability offer)) (= (:availability offer) "unknown")) true
      (not (:productUrl offer)) true
      (>= (count landed-vals) 3) (let [med (median landed-vals)]
                                   (and (> med 0) (< (landed-price offer) (* med 0.4))))
      :else false)))

(defn handle-rank [state]
  (let [offers (vec (get state :offers [])) merchants (get state :merchants {})]
    (if (empty? offers)
      (assoc state :cheapest nil :bestOverall nil :suspicious [])
      (let [landed-vals (map landed-price offers)
            sus-idx (set (filter #(suspicious? (offers %) landed-vals merchants) (range (count offers))))
            suspicious (mapv offers sus-idx)
            clean (let [c (vec (remove (fn [[i _]] (sus-idx i)) (map-indexed vector offers)))]
                    (if (seq c) (mapv second c) offers))]
        (assoc state
               :cheapest (apply min-key landed-price clean)
               :bestOverall (apply max-key #(best-overall-score % merchants) clean)
               :suspicious suspicious)))))

(defn handle-arbitrage [state]
  (let [offers (vec (remove :suspicious (get state :offers [])))]
    (if (< (count offers) 2)
      (assoc state :spread 0 :spreadFraction 0.0 :notable false :byRegion {})
      (let [landed (mapv (fn [o] [(landed-price o) o]) offers)
            [lo-val lo] (apply min-key first landed)
            [hi-val hi] (apply max-key first landed)
            spread (- hi-val lo-val)
            frac (if (pos? lo-val) (/ spread (double lo-val)) 0.0)
            by-region (reduce (fn [m [val o]]
                                (let [region (get o :region "unknown") cur (get m region)]
                                  (if (or (nil? cur) (< val (:minLanded cur)))
                                    (assoc m region {:minLanded val :merchantId (:merchantId o)}) m)))
                              {} landed)]
        (assoc state :minLanded lo-val :maxLanded hi-val :cheapestMerchant (:merchantId lo)
               :dearestMerchant (:merchantId hi) :spread spread :spreadFraction (r4 frac)
               :notable (>= frac notable-spread-fraction) :byRegion by-region
               :intent "buyer-transparency+supply-resilience")))))

(defn- price-velocity [history]
  (let [pts (sort-by #(get % :observedAt "") history)]
    (if (< (count pts) 2)
      0.0
      (let [first* (long (or (:totalPrice (first pts)) (:price (first pts)) 0))
            last* (long (or (:totalPrice (last pts)) (:price (last pts)) 0))]
        (if (zero? first*) 0.0 (/ (- last* first*) (double first*)))))))

(defn handle-supply-demand [state]
  (let [offers (get state :offers []) history (get state :priceHistory [])]
    (if (empty? offers)
      (assoc state :supplyDemandIndex 0.0 :inStockRatio 0.0 :priceVelocity 0.0)
      (let [in-stock (count (filter #(= (:availability %) "in-stock") offers))
            ratio (/ in-stock (double (count offers)))
            scarcity (- 1.0 ratio)
            velocity (price-velocity history)
            scarcity-signed (* (- scarcity 0.5) 2.0)
            velocity-clamped (max -1.0 (min 1.0 (* velocity 4.0)))
            index (max -1.0 (min 1.0 (/ (+ scarcity-signed velocity-clamped) 2.0)))]
        (assoc state :supplyDemandIndex (r4 index) :inStockRatio (r4 ratio)
               :priceVelocity (r4 velocity)
               :reading (cond (> index 0.33) "scarcity" (< index -0.33) "glut" :else "balanced"))))))

(defn handle-demand [state]
  (let [history (get state :priceHistory [])
        obs (count history)
        cohort (long (or (:cohortObservationTotal state) 0))
        share (if (pos? cohort) (/ obs (double cohort)) 0.0)]
    (assoc state :observationCount obs
           :merchantCount (count (set (map :merchantId history)))
           :demandShare (r4 share) :kind "present-interest-proxy")))

(defn handle-intel [state]
  (let [arb (handle-arbitrage state) sd (handle-supply-demand state)
        summary {:productId (:productId state) :minLanded (:minLanded arb) :spread (:spread arb)
                 :spreadFraction (:spreadFraction arb) :notable (:notable arb)
                 :supplyDemandIndex (:supplyDemandIndex sd) :reading (:reading sd) :shape "aggregate"}]
    (assoc state :intel summary :narration nil)))

(defn handle-social [state]
  (let [intel (or (:intel state) (:intel (handle-intel state)))
        posts-week (long (or (:postsThisWeek state) 0))]
    (if (>= posts-week social-weekly-ceiling)
      (assoc state :post nil :refused true
             :reason (str "weekly aggregate ceiling reached (" social-weekly-ceiling "/wk, G4)"))
      (let [frac-pct (r1 (* (double (or (:spreadFraction intel) 0.0)) 100))
            post {:text (str "価格透明性: " (or (:productId intel) "product") " の現在の最安 landed 価格差は "
                             frac-pct "% (" (or (:reading intel) "balanced") ")。"
                             " 購買勧誘ではなく公共的な価格可視化です。")
                  :shape "aggregate" :lexicon "app.bsky.feed.post" :affiliate false :nudge false}
            op (:operatorRef state)]
        (if-not op
          (assoc state :post post :state "draft" :reason "live broadcast is operator-gated (G11)")
          (assoc state :post post :state "posted" :operatorRef op))))))

(defn main [& _]
  (let [offers [{:merchantId "a_com" :price 10000 :shippingFee 500 :availability "in-stock"
                 :deliveryEtaDays 2 :productUrl "https://a/p" :region "jp"}
                {:merchantId "b_com" :price 9000 :shippingFee 2000 :availability "in-stock"
                 :deliveryEtaDays 7 :productUrl "https://b/p" :region "us"}]
        arb (handle-arbitrage {:offers offers})]
    (println (format "kakaku arbitrage: spread %d (%.1f%%) cheapest=%s notable=%s — %s"
                     (:spread arb) (* 100.0 (:spreadFraction arb)) (:cheapestMerchant arb)
                     (:notable arb) (:intent arb)))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
