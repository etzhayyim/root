;; autorun.clj — 弾正 (danjo) revenue-ledger AUTONOMOUS heartbeat (offline, fleet-runnable).
;; ADR-2605301600. The clj sibling of danjo/methods/autorun.py: each cycle OBSERVES the offline
;; pre-published corpus + registries → emits the FULL datom set (revenue/account/transfer/
;; appropriation/outlay + national+local tax + org mirror + 交付税/譲与税 transfer + non-adjudicating
;; reconciliation observation) → persists ONE content-addressed transaction to the append-only LOCAL
;; kotoba Datom log, chaining the previous tx CID into a verifiable commit-DAG.
;;
;; Deterministic / resume-safe / NO external I/O. Discipline holds by construction: passive-only
;; (offline registries, G3); non-adjudicating (observation datoms carry :danjo.obs/non-adjudicating
;; true, G4 — all-datoms/observation-datoms RAISE on any verdict token); ≥2 source CIDs (G5);
;; the loop persists to the LOCAL log only — live kotoba transact + publication stay G7/Council-gated.
(ns root.danjo.methods.autorun
  (:require [clojure.java.io :as io]))

(load-file "maturity.clj")        ; transitively loads every revenue-ledger namespace + m/context
(alias 'm  'root.danjo.methods.maturity)
(alias 'rl 'root.danjo.methods.revenue-ledger)
(alias 't  'root.danjo.methods.taxes)
(alias 'o  'root.danjo.methods.org-actor)
(alias 'tr 'root.danjo.methods.transfers)
(alias 'd  'root.danjo.methods.discrepancy)

(def log-default "../data/persisted/danjo.revenue.autorun.kotoba.edn")

(defn cycle-extra-datoms
  "The non-model datoms a heartbeat adds on top of run-cycle!'s all-datoms(model): the national+
   local tax registry, the org mirror-actors, the 国→地方 transfers/grants, and the appropriation↔
   outlay reconciliation observations (FY2024). Pure over the offline context."
  [ctx]
  (vec (concat (t/tax-datoms (:comb ctx))
               (o/org-datoms (:orgs ctx) (:comb ctx))
               (tr/transfer-datoms (:xfer ctx))
               (d/observation-datoms (d/observations (:model ctx) 2024)))))

(defn heartbeat!
  "Run `cycles` heartbeat cycles → append one tx each to the local log (chained). `:fresh` clears
   the log first. Returns {:cycles :head-cid :datoms-per-cycle :chain}. Offline; deterministic."
  [{:keys [cycles fresh log-path] :or {cycles 1 log-path log-default}}]
  (when (and fresh (.exists (io/file log-path))) (.delete (io/file log-path)))
  (let [ctx   (m/context)
        extra (cycle-extra-datoms ctx)
        results (vec (for [i (range cycles)]
                       (rl/run-cycle! {:seed (:model ctx) :extra-datoms extra
                                       :log-path log-path :as-of (inc i)})))]
    {:cycles cycles
     :head-cid (:head-cid (peek results))
     :datoms-per-cycle (:datom-count (peek results))
     :chain (rl/verify-chain log-path)}))

(defn -main [& args]
  (let [cycles (if (seq args) (Integer/parseInt (first args)) 3)
        r (heartbeat! {:cycles cycles :fresh true})]
    (println (format "danjo revenue-ledger heartbeat: %d cycles, %d datoms/cycle"
                     (:cycles r) (:datoms-per-cycle r)))
    (println "  head-cid:" (:head-cid r))
    (println "  chain:" (if (:ok (:chain r))
                          (str "ok, " (:length (:chain r)) " txs (commit-DAG verified)")
                          (str "BROKEN at " (:broken-at (:chain r)))))))
