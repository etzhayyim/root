(ns minori.autorun
  "minori 稔り resident-runtime heartbeat — one react beat per invocation, persisted to an
   append-only content-addressed ledger, with a growth evaluation (G_prev → G_now, dG, η, adoption).
   Deterministic + resume-safe (beat index = ledger length; no wall-clock, no randomness):
   re-running with no new lever = idempotent no-op. Run under bb:

     bb --classpath 20-actors/minori/src \\
        -e \"(require 'minori.autorun) (minori.autorun/-main)\"

   Live legs (real ie-flow scoreboard JOIN, real donation/OSS metrics, sending any social action)
   are G7/operator/member-gated — this loop only OBSERVES the MAP + SoS roster and PREPARES (dry-run)."
  (:require [minori.score   :as score]
            [minori.react   :as react]
            [minori.measure :as measure]
            [minori.ledger  :as ledger]
            [clojure.edn    :as edn]))

(def defaults
  {:system           "20-actors/minori/system.edn"
   :valuation        "80-data/ie-flow/social-capital-valuation.edn"
   :sos              "80-data/ie-flow/system-of-systems.edn"
   :scoreboard       "80-data/ie-flow/scoreboard.edn"
   :capture-snapshot "80-data/social-capital/capture-snapshot.edn"
   :ledger           "20-actors/minori/data/ledger.edn"})

(defn next-worklist
  "The :intervention-worklist export (system.edn) — the prioritized REAL (mostly G7-gated) next
   step to MOVE the truth, ranked by lowest component first (highest leverage). minori sees the
   truth; its job is to surface what would actually raise it (dry-run; live legs operator/member-gated)."
  [m-after obs]
  (let [comps (:components m-after)
        items [{:lever :capture :value (:capture comps)
                :step "wire live donation-flow + OSS-adoption metric → real captured÷addressable"
                :gate :G7-operator}
               {:lever :eta :value (:eta comps)
                :step "raise REAL net-export (η→1) via member-principal deepen-symbiosis live leg"
                :gate :G7-member}
               {:lever :phi :value (:phi comps)
                :step "raise adopted toward n=18342 via SoS-rule rollout to the remaining roster"
                :gate :none}
               {:lever :adoption :value (:adoption comps)
                :step "sustain SoS-reward adoption across the roster"
                :gate :none}]]
    (assoc (first (sort-by :value items))
           :capture-note (get-in obs [:capture :note]))))

(defn run
  ([] (run defaults))
  ([{:keys [system valuation sos scoreboard capture-snapshot ledger] :as paths}]
   (let [sys      (edn/read-string (slurp system))
         model    (:score/model sys)
         _val     (score/read-edn valuation)            ; the MAP being tracked (presence = observed)
         adoption (score/roster-adoption sos (:adoption (:targets model)))
         led      (ledger/load-ledger ledger)
         prev     (ledger/head led)
         state    (or (:state prev) {})
         done     (set (or (:done prev) []))
         {:keys [pick state' done' measure-before]}
           (react/beat {:state state :done done} model adoption)
         ;; 観測: minori is an observatory — it reads ALL available truth every beat (η from the
         ;; scoreboard, Φ from the roster, capture from the valuation MAP) and GROUNDS it into the
         ;; score (truth beats the loop's stubs; grounding can LOWER an optimistic stub — honest).
         obs      (measure/observe {:scoreboard scoreboard :capture-snapshot capture-snapshot} (:adopted adoption))
         state''  (measure/ground state' obs)
         grounded? (boolean (get-in obs [:colony-eta :mean]))
         m-after  (score/growth state'' model adoption)
         dG       (- (:G m-after) (:G measure-before))
         reward   (:reward m-after)
         gated?   (:gated? m-after)
         next-action (next-worklist m-after obs)        ; the :intervention-worklist export
         entry    {:actor "minori"
                   :adr "2606261114"
                   :kind :react-beat
                   :observed {:valuation valuation :sos-adopted (:adopted adoption)
                              :colony-eta (get-in obs [:colony-eta :mean])
                              :realized-phi (:realized-phi obs)
                              :capture-grounded (get-in obs [:capture :ratio])
                              :grounded? grounded?}
                   :pick pick
                   :state state''
                   :done (vec done')
                   :G (:G m-after)
                   :G-prev (:G measure-before)
                   :dG dG
                   :eta (:eta m-after)
                   :net-giver? (:net-giver? m-after)
                   :gated? gated?
                   :reward reward
                   :components (:components m-after)
                   :next-action next-action
                   :adoption (:p adoption)}
         appended (ledger/append! ledger entry)
         appended? (:appended? appended)
         head     (:head appended)
         chain    (ledger/verify-chain (:ledger appended))]
     {:appended? appended?
      :beat (:beat head)
      :pick pick
      :G-prev (:G measure-before)
      :G (:G m-after)
      :dG dG
      :eta (:eta m-after)
      :adoption (:p adoption)
      :sos-adopted (:adopted adoption)
      :grounded? grounded?
      :colony-eta (get-in obs [:colony-eta :mean])
      :realized-phi (:realized-phi obs)
      :next-action next-action
      :gated? gated?
      :reward reward
      :components (:components m-after)
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
    (when (:colony-eta r)
      (println (format "観測: colony-η=%.3f (real scoreboard)  realized-Φ=ln(adopted)=%.2f  grounded?=%s"
                       (:colony-eta r) (or (:realized-phi r) 0.0) (:grounded? r))))
    (when-let [na (:next-action r)]
      (println (format "次の一手: [%s %.3f, gate=%s] %s"
                       (name (:lever na)) (:value na) (name (:gate na)) (:step na))))
    (println (format "head-cid=%s…  verify-chain=%s" (subs (str (:head-cid r)) 0 12) (:verify-chain r)))
    r))
