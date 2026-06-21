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
  (:require [clojure.string :as str]
            [kaiyaku.methods.analyze :as analyze]
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

;; ── member-facing 解約サマリ (human-readable; dry-run honest) ────────────────

(defn member-report
  "Render a run result into a member-facing 解約サマリ markdown. Honest by
  construction: the title says dry-run, every entry shows executed=false, the
  disclosed procedure + cost-of-severance ride along, and a G8 cost discrepancy
  or an operator-verification requirement is flagged with ⚠. kaiyaku never
  presents this as a done deal — it is what WOULD happen on the member's approval."
  [{:keys [descriptors]}]
  (let [auth (filter #(get % "authorized") descriptors)
        submit (filter #(= ":member-submits" (get % "status")) descriptors)
        refused (filter #(= ":refused" (get % "status")) descriptors)
        L (transient
           [ "# kaiyaku 解約サマリ（dry-run — まだ何も実行されていません）" ""
            (str "解約候補 " (count descriptors) "件 ／ 認可(dry-run) "
                 (count (filter #(= ":authorized-dry-run" (get % "status")) descriptors))
                 "件 ／ 要 member 提出 " (count submit) "件 ／ 拒否 " (count refused) "件")
            "" "> 実行（実際の解約）は member 署名 + Council Lv6+ + operator が揃った post-R1 で行われます。" ""])]
    (doseq [d descriptors]
      (let [proc (get d "disclosed_procedure")]
        (conj! L (str "## " (or (get d "svc_label") (get d "svc"))
                      " — " (or (get d "tier") "—") " · " (get d "status")))
        (conj! L (str "- 推奨: " (get d "recommendation")
                      " · 通知: " (get d "notice_days") "日"
                      " · 違約金: ¥" (get d "penalty_jpy")))
        (conj! L (str "- authorized: " (boolean (get d "authorized"))
                      " · executed: " (boolean (get d "executed")) "（常に false / dry-run）"))
        (when-let [steps (get proc "self_submit_steps")]
          (conj! L "- 手順:")
          (doseq [[i s] (map-indexed vector steps)]
            (conj! L (str "  " (inc i) ". " s)))
          (when-let [src (get proc "disclosed_source")]
            (conj! L (str "  出典: " src))))
        (when (get d "g8_ack_required")
          (conj! L (str "- ⚠ G8: 費用相違の確認が必要 — " (str/join " / " (get d "g8_drift")))))
        (when (get d "operator_verification_required")
          (conj! L "- ⚠ 手順は :representative（未検証）— 実行前に operator 検証が必要"))
        (when-let [why (get d "why")]
          (conj! L (str "- 理由: " why)))
        (conj! L "")))
    (str (str/join "\n" (persistent! L)) "\n")))

#?(:clj
   (defn run+persist!
     "run, then append the receipt datoms as ONE content-addressed tx to the
     kotoba log (commit-DAG). Returns the run result + :receipt-cid."
     [opts log-path {:keys [tx-id as-of prev-cid] :or {prev-cid ""}}]
     (let [r (run (assoc opts :as-of as-of))
           cid (receipt/persist-receipts! (:descriptors r) log-path
                                          {:tx-id tx-id :as-of as-of :prev-cid prev-cid})]
       (assoc r :receipt-cid cid))))
