(ns minori.autorun
  "minori 稔り resident-runtime heartbeat — one react beat per invocation, persisted to an
   append-only content-addressed ledger, with a growth evaluation (G_prev → G_now, dG, η, adoption).
   Deterministic + resume-safe (beat index = ledger length; no wall-clock, no randomness):
   re-running with no new lever = idempotent no-op. Run under bb:

     bb --classpath 20-actors/minori/src \\
        -e \"(require 'minori.autorun) (minori.autorun/-main)\"

   Live legs (real ie-flow scoreboard JOIN, real donation/OSS metrics, sending any social action)
   are G7/operator/member-gated — this loop only OBSERVES the MAP + SoS roster and PREPARES (dry-run)."
  (:require [minori.score  :as score]
            [minori.react  :as react]
            [minori.ledger :as ledger]
            [clojure.edn   :as edn]))

(def defaults
  {:system    "20-actors/minori/system.edn"
   :valuation "80-data/ie-flow/social-capital-valuation.edn"
   :sos       "80-data/ie-flow/system-of-systems.edn"
   :ledger    "20-actors/minori/data/ledger.edn"})

(defn run
  ([] (run defaults))
  ([{:keys [system valuation sos ledger] :as paths}]
   (let [sys      (edn/read-string (slurp system))
         model    (:score/model sys)
         _val     (score/read-edn valuation)            ; the MAP being tracked (presence = observed)
         adoption (score/roster-adoption sos (:adoption (:targets model)))
         led      (ledger/load-ledger ledger)
         prev     (ledger/head led)
         state    (or (:state prev) {})
         done     (set (or (:done prev) []))
         {:keys [pick state' done' measure-before measure-after dG reward gated?]}
           (react/beat {:state state :done done} model adoption)
         entry    {:actor "minori"
                   :adr "2606261114"
                   :kind :react-beat
                   :observed {:valuation valuation :sos-adopted (:adopted adoption)}
                   :pick pick
                   :state state'
                   :done (vec done')
                   :G (:G measure-after)
                   :G-prev (:G measure-before)
                   :dG dG
                   :eta (:eta measure-after)
                   :net-giver? (:net-giver? measure-after)
                   :gated? gated?
                   :reward reward
                   :components (:components measure-after)
                   :adoption (:p adoption)}
         appended (ledger/append! ledger entry)
         appended? (:appended? appended)
         head     (:head appended)
         chain    (ledger/verify-chain (:ledger appended))]
     {:appended? appended?
      :beat (:beat head)
      :pick pick
      :G-prev (:G measure-before)
      :G (:G measure-after)
      :dG dG
      :eta (:eta measure-after)
      :adoption (:p adoption)
      :sos-adopted (:adopted adoption)
      :gated? gated?
      :reward reward
      :components (:components measure-after)
      :head-cid (:cid head)
      :verify-chain chain})))

(defn -main [& args]
  (let [paths (if (seq args) (merge defaults (apply hash-map (map read-string args))) defaults)
        r (run paths)]
    (println "─── minori 稔り react beat ───────────────────────────")
    (println (format "beat #%s   pick=%s (%s)" (:beat r) (name (:id (:pick r))) (name (:kind (:pick r)))))
    (println (format "G: %.4f → %.4f   ΔG=%+.5f   η=%.3f   adoption=%d actors (%.3f)"
                     (:G-prev r) (:G r) (:dG r) (:eta r) (:sos-adopted r) (:adoption r)))
    (println (format "reward=%.4f  gated?=%s (η<1 ⇒ only η+adoption rewarded)  appended?=%s"
                     (:reward r) (:gated? r) (:appended? r)))
    (println (format "components: η=%.3f adoption=%.3f capture=%.3f Φ=%.3f"
                     (get-in r [:components :eta]) (get-in r [:components :adoption])
                     (get-in r [:components :capture]) (get-in r [:components :phi])))
    (println (format "head-cid=%s…  verify-chain=%s" (subs (str (:head-cid r)) 0 12) (:verify-chain r)))
    r))
