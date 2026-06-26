(ns minori.score-test
  "minori charter + correctness tests — runnable under bb:
     bb --classpath 20-actors/minori/src:20-actors/minori/test \\
        -e \"(require 'minori.score-test) (minori.score-test/run)\""
  (:require [minori.score   :as score]
            [minori.react   :as react]
            [minori.ledger  :as ledger]
            [minori.measure :as measure]
            [minori.capture :as capture]
            [minori.social  :as social]
            [clojure.set    :as set]))

(def model
  {:weights {:eta 0.35 :adoption 0.30 :capture 0.20 :phi 0.15}
   :targets {:eta 1.0 :capture 0.01 :phi-potential 9.8 :adoption 100}})

(def adoption {:adopted 80 :target 100 :p 0.8})

(defn run []
  (let [results (atom [])
        check (fn [name ok] (swap! results conj [name (boolean ok)]))]

    ;; G ∈ [0,1]
    (let [g (:G (score/growth {} model adoption))]
      (check :G-in-range (and (>= g 0.0) (<= g 1.0))))

    ;; non-parasitism gate: η<1 ⇒ gated, reward = 0.5·(η+adoption), NOT raw G
    (let [r (score/growth {:eta-estimate 0.0} model adoption)]
      (check :gated-when-net-taker (:gated? r))
      (check :gated-reward-is-give-back (< (Math/abs (- (:reward r) (* 0.5 (+ 0.0 0.8)))) 1e-9)))

    ;; GROUNDED η≥1 ⇒ net-giver, reward = raw G (no clamp)
    (let [r (score/growth {:eta-grounded 1.0} model adoption)]
      (check :ungated-when-net-giver (and (:net-giver? r) (= (:reward r) (:G r)))))

    ;; HONESTY: a huge STUB η can never cross the net-giver gate — only GROUNDED η can
    (check :stub-cannot-cross-gate (not (:net-giver? (score/growth {:eta-estimate 5.0} model adoption))))
    (check :grounded-crosses-gate (:net-giver? (score/growth {:eta-grounded 1.0} model adoption)))

    ;; HONESTY: grounding capture to the real pre-revenue ratio LOWERS the optimistic stub
    (let [stub     (score/growth {:eta-grounded 0.8 :capture-estimate 0.005} model adoption)
          grounded (score/growth {:eta-grounded 0.8 :capture-estimate 0.005 :capture-grounded 0.0} model adoption)]
      (check :capture-grounding-lowers-G (< (:G grounded) (:G stub))))

    ;; CHARTER: the catalog cannot represent a predatory / extractive / outward-send mechanism
    (let [kinds (set (map :kind (react/catalog)))]
      (check :no-predatory-kind
             (empty? (set/intersection kinds #{:extract :capture :manipulate :send :trade}))))

    ;; CHARTER: no intervention lowers η (rank would never reward a net-taker move)
    (check :no-eta-lowering-intervention
           (every? #(>= (get-in % [:d :eta-estimate] 0.0) 0.0) (react/catalog)))

    ;; a beat produces non-negative ΔG (every charter-clean lever is growth-or-flat)
    (let [b (react/beat {:state {} :done #{}} model adoption)]
      (check :beat-nonneg-dG (>= (:dG b) 0.0))
      (check :beat-picks-something (some? (get-in b [:pick :id]))))

    ;; ledger: content-cid stable, verify-chain ok on a hand-built 2-entry chain
    (let [c1 (ledger/content-cid {:a 1})
          e0 {:a 1 :cid (ledger/sha256-hex (str c1 "|" nil "|" 0)) :parent nil :beat 0}
          c2 (ledger/content-cid {:a 2})
          e1 {:a 2 :cid (ledger/sha256-hex (str c2 "|" (:cid e0) "|" 1)) :parent (:cid e0) :beat 1}]
      (check :ledger-verify-ok (:ok (ledger/verify-chain [e0 e1])))
      (check :ledger-tamper-detected (not (:ok (ledger/verify-chain [e0 (assoc e1 :a 99)])))))

    ;; MEASURE: grounding is monotone (never lowers η) + fail-open on absent scoreboard
    (check :measure-failopen-absent (nil? (measure/colony-eta "20-actors/minori/data/__nope__.edn")))
    (check :measure-realized-phi (< (Math/abs (- (measure/realized-phi 105) (Math/log 105.0))) 1e-9))
    (let [grounded (measure/ground {:eta-grounded 0.10}
                                   {:colony-eta {:mean 0.95} :realized-phi 4.65})]
      (check :measure-grounds-eta-up (= 0.95 (:eta-grounded grounded)))
      (check :measure-monotone-no-lower
             (= 0.99 (:eta-grounded (measure/ground {:eta-grounded 0.99}
                                                    {:colony-eta {:mean 0.95}})))))
    ;; grounding capture sets the real (pre-revenue) ratio
    (check :measure-grounds-capture
           (= 0.0 (:capture-grounded (measure/ground {} {:capture {:ratio 0.0}}))))

    ;; CAPTURE source: a :template snapshot is honestly ungrounded (ratio 0); a :live one grounds for real
    (check :capture-template-ungrounded
           (let [r (capture/ratio-of {:status :template :grounded? false
                                      :a {:captured-usd-per-year 0 :addressable-usd-per-year 5.0e9}})]
             (and (not (:grounded? r)) (zero? (:ratio r)))))
    (check :capture-live-grounds
           (let [r (capture/ratio-of {:status :live :grounded? true
                                      :a {:captured-usd-per-year 5.0e6 :addressable-usd-per-year 5.0e9}
                                      :b {:captured-usd-per-year 0     :addressable-usd-per-year 3.0e9}})]
             (and (:grounded? r) (< (Math/abs (- (:ratio r) (/ 5.0e6 8.0e9))) 1e-12))))
    (check :capture-absent-failopen (not (:grounded? (capture/ratio-of nil))))

    ;; SOCIAL ACTION: the prepared digest is charter-clean + unsent; manipulative bodies are detected
    (let [d (social/digest {:eta 0.809 :adopted 105 :realized-phi 4.65
                            :next-step "wire live donation metric" :next-gate :G7-operator})]
      (check :social-prepared-unsent (= :prepared-unsent (:status d)))
      (check :social-charter-clean (:charter-clean d))
      (check :social-mentions-anti-class (clojure.string/includes? (:body d) "earns you nothing")))
    (check :social-detects-manipulation (not (social/clean? "Donate now — limited time, VIP perks!")))
    (check :social-no-server-key (get-in (social/digest {:eta 0.8 :adopted 1 :realized-phi 0.0
                                                         :next-step "x" :next-gate :none})
                                         [:charter :no-server-key]))

    (let [all @results
          pass (count (filter second all))
          tot  (count all)]
      (doseq [[n ok] all] (println (format "  %s %s" (if ok "✓" "✗") (name n))))
      (println (format "minori tests: %d/%d green" pass tot))
      (when (not= pass tot) (throw (ex-info "minori tests failed" {:results all})))
      {:pass pass :total tot})))
