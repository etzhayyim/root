#!/usr/bin/env bb
;; kaiyaku 解約 — the full R1 dry-run pipeline, composed end-to-end.
(ns kaiyaku.methods.pipeline
  "pipeline.cljc — kaiyaku 解約 R1 end-to-end composition (ADR-2606112201 R1).

  One function that threads the whole R1 pipeline so the seven pieces are proven
  to compose (and interface drift between them is caught by one integration test):

    analyze (edge-primary burden + cascade-guard, G2)
      → plan   (T1/T2/T3 routing, dry-run, G3/G8)
      → enrich (attach the disclosed real procedure from the catalog; G8 drift)
      → dispatch (capability-gated authorization, NEVER execute; G3/G5/G6 +
                  cascade + exactly-once)
      → serviceop (map each AUTHORIZED T1/T2 plan to a karakuri ServiceOp; T3 →
                   member-submits, no op)
      → receipt  (every descriptor → a :kaiyaku.receipt/* audit datom; G9)

  Stays entirely dry-run: there is NO live I/O anywhere in the chain (the only
  optional file I/O is appending the receipt tx to the local kotoba log). The
  driver authorizes; a post-R1 component executes (G6). Deterministic: caller
  supplies :now-epoch + :as-of (no wall clock). Pure except the receipt persist
  edge. Portable .cljc."
  (:require [kaiyaku.methods.analyze :as analyze]
            [kaiyaku.methods.plan :as plan]
            [kaiyaku.methods.catalog :as catalog]
            [kaiyaku.methods.driver :as driver]
            [kaiyaku.methods.karakuri-bridge :as kb]
            [kaiyaku.methods.receipt :as receipt]))

(defn run
  "Compose the full R1 dry-run pipeline over a loaded ledger graph.

  opts: {:nodes :edges     the ledger graph (analyze/load-file* shape)
         :catalog          catalog by-id map (catalog/by-id …) | nil
         :bundle           member-presented capability bundle (cap.cljc) | nil
         :now-epoch        deterministic epoch for the leash check
         :as-of            tx time string for the receipts}

  Returns {:plans :enriched :descriptors :serviceops :receipt-datoms :severed}.
  Never throws on a gate failure (a refused tie just yields a :refused descriptor)."
  [{:keys [nodes edges catalog bundle now-epoch as-of]}]
  (let [plans    (plan/plans nodes edges)
        enriched (catalog/enrich-plans plans (or catalog {}))
        {:keys [results severed]} (driver/dispatch-batch
                                   enriched {:bundle bundle :now-epoch now-epoch})
        ;; karakuri ServiceOps only for AUTHORIZED T1/T2 plans (T3 → member-submits → nil)
        serviceops (->> (map vector enriched results)
                        (filter (fn [[_ d]] (get d "authorized")))
                        (keep (fn [[p _]] (kb/plan->serviceop p)))
                        vec)
        rec-datoms (receipt/receipt-datoms results as-of)]
    {:plans plans
     :enriched enriched
     :descriptors results
     :serviceops serviceops
     :receipt-datoms rec-datoms
     :severed severed}))

#?(:clj
   (defn run+persist!
     "run, then append the receipt datoms as ONE content-addressed tx to the
     kotoba log (commit-DAG). Returns the run result + :receipt-cid."
     [opts log-path {:keys [tx-id as-of prev-cid] :or {prev-cid ""}}]
     (let [r (run (assoc opts :as-of as-of))
           cid (receipt/persist-receipts! (:descriptors r) log-path
                                          {:tx-id tx-id :as-of as-of :prev-cid prev-cid})]
       (assoc r :receipt-cid cid))))
