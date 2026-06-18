#!/usr/bin/env bb
;; business-manager — kotoba-native internal ERP actor (babashka port of agent.py).
(ns business-manager.py.agent
  "Accounting actor: double-entry bookkeeping, approval routing, no-server-key posting,
  invoice AP/AR, aging, and budget vs actual.

  Map keys are strings to match Python dicts; keyword-valued fields are :-prefixed strings.
  Money uses integer minor units; Python // maps to quot.")

(def ^:const JOURNAL_APPROVAL_MINOR (* 1000000 100))
(def ^:const PO_APPROVAL_MINOR (* 5000000 100))
(def ^:const INVOICE_APPROVAL_MINOR (* 1000000 100))
(def ^:const _INVOICE_DIRECTIONS ["payable" "receivable"])

(defn- blank? [s]
  (or (nil? s) (and (string? s) (zero? (count (clojure.string/trim s))))))

(defn fiscal_year_of
  "Return the JP fiscal-year label for an ISO date (YYYY-MM-DD)."
  [iso-date]
  (let [parts (clojure.string/split iso-date #"-")
        y (parse-long (nth parts 0 "0"))
        m (parse-long (nth parts 1 "0"))]
    (str "FY" (if (>= m 4) y (dec y)))))

(defn is_balanced
  "True iff Σ debitMinor == Σ creditMinor and there are ≥2 lines."
  [lines]
  (and (>= (count lines) 2)
       (let [debit (reduce + (map #(parse-long (str (get % "debitMinor" 0))) lines))
             credit (reduce + (map #(parse-long (str (get % "creditMinor" 0))) lines))]
         (and (= debit credit) (pos? debit)))))

(defn approval_status
  "approval-required if amount > threshold, else auto-approved."
  [amount_minor threshold_minor]
  (if (> amount_minor threshold_minor)
    "approval-required"
    "auto-approved"))

(defn post_journal_entry
  "Validate + stage a journal entry. Rejects unbalanced or missing-poster entries."
  [entry posted_at]
  (let [lines (get entry "lines" [])]
    (cond
      (not (is_balanced lines))
      {"state" "rejected", "reason" "entry does not balance: Σdebit ≠ Σcredit (G2)"}

      (blank? (get entry "postedBy"))
      {"state" "rejected", "reason" "missing member postedBy (G4)"}

      :else
      (let [amount (reduce + (map #(parse-long (str (get % "debitMinor" 0))) lines))]
        {"state" "staged"
         "kind" "journalEntry"
         "entryId" (get entry "entryId")
         "lines" lines
         "amountMinor" amount
         "currency" "JPY"
         "fiscalYear" (fiscal_year_of posted_at)
         "approved" (approval_status amount JOURNAL_APPROVAL_MINOR)
         "postedBy" (get entry "postedBy")
         "postedSig" nil
         "appendOnly" true}))))

(defn post_purchase_order
  "Stage a purchase order; derive approved from the PO threshold."
  [po posted_at]
  (if (blank? (get po "postedBy"))
    {"state" "rejected", "reason" "missing member postedBy (G4)"}
    (let [amount (parse-long (str (get po "amountMinor" 0)))]
      {"state" "staged"
       "kind" "purchaseOrder"
       "poId" (get po "poId")
       "vendor" (get po "vendor" "")
       "amountMinor" amount
       "currency" "JPY"
       "items" (get po "items" [])
       "fiscalYear" (fiscal_year_of posted_at)
       "approved" (approval_status amount PO_APPROVAL_MINOR)
       "postedBy" (get po "postedBy")
       "postedSig" nil
       "appendOnly" true})))

(defn authorize_posting
  "Post a staged entry. Only a member-origin signature authorizes; server signature refused."
  [posting signature]
  (cond
    (not= (get posting "state") "staged")
    (assoc posting "refused" true "reason" "posting is not in :staged state")

    (not= (get signature "origin") "member")
    (assoc posting "refused" true
           "reason" "only a member passkey/wallet signature posts to the ledger (G4 no-server-key)")

    :else
    (assoc posting "state" "posted" "postedSig" (get signature "ref"))))

(defn trial_balance
  "Roll up Σdebit / Σcredit across journal entries."
  [entries]
  (let [debit (reduce + (for [e entries, l (get e "lines" [])]
                          (parse-long (str (get l "debitMinor" 0)))))
        credit (reduce + (for [e entries, l (get e "lines" [])]
                           (parse-long (str (get l "creditMinor" 0)))))]
    {"totalDebitMinor" debit, "totalCreditMinor" credit, "balanced" (= debit credit)}))

(defn post_invoice
  "Stage an invoice. direction must be payable or receivable; amount must be positive."
  [inv posted_at]
  (let [direction (get inv "direction")]
    (cond
      (not (some #(= % direction) _INVOICE_DIRECTIONS))
      {"state" "rejected",
       "reason" (str "direction must be one of [\"payable\", \"receivable\"] (got " (pr-str direction) ")")}

      (blank? (get inv "postedBy"))
      {"state" "rejected", "reason" "missing member postedBy (G4)"}

      :else
      (let [amount (parse-long (str (get inv "amountMinor" 0)))]
        (if (<= amount 0)
          {"state" "rejected", "reason" "invoice amount must be positive"}
          {"state" "staged"
           "kind" "invoice"
           "invoiceId" (get inv "invoiceId")
           "direction" direction
           "party" (get inv "party" "")
           "amountMinor" amount
           "currency" "JPY"
           "dueDate" (get inv "dueDate" "")
           "fiscalYear" (fiscal_year_of posted_at)
           "approved" (approval_status amount INVOICE_APPROVAL_MINOR)
           "paymentStatus" "open"
           "postedBy" (get inv "postedBy")
           "postedSig" nil
           "appendOnly" true})))))

(defn settle_invoice
  "Mark a posted invoice paid. Member-signed only; append-only."
  [invoice paid_at signature]
  (cond
    (not (#{"open" "overdue"} (get invoice "paymentStatus")))
    (assoc invoice "refused" true "reason" "invoice is not open/overdue")

    (not= (get signature "origin") "member")
    (assoc invoice "refused" true
           "reason" "only a member signature settles an invoice (G4 no-server-key)")

    :else
    (assoc invoice "paymentStatus" "paid" "paidAt" paid_at "settledSig" (get signature "ref"))))

(defn invoice_aging
  "Aging summary: open AP vs AR totals and overdue invoice ids."
  [invoices as_of_date]
  (loop [ap 0 ar 0 overdue [] invs invoices]
    (if (empty? invs)
      {"apOpenMinor" ap, "arOpenMinor" ar, "overdue" overdue}
      (let [inv (first invs)]
        (if (= "open" (get inv "paymentStatus"))
          (let [amt (parse-long (str (get inv "amountMinor" 0)))
                due (get inv "dueDate" "")
                overdue? (and (seq due) (< (compare due as_of_date) 0))
                new-overdue (if overdue? (conj overdue (get inv "invoiceId")) overdue)]
            (case (get inv "direction")
              "payable" (recur (+ ap amt) ar new-overdue (rest invs))
              "receivable" (recur ap (+ ar amt) new-overdue (rest invs))
              (recur ap ar new-overdue (rest invs))))
          (recur ap ar overdue (rest invs)))))))

(defn budget_vs_actual
  "Compare budget allocation to actual debit spend on the account in the fiscal year."
  [budget journal_entries]
  (let [account (get budget "account")
        fy (get budget "fiscalYear")
        allocated (parse-long (str (get budget "allocatedMinor")))
        spent (reduce +
                       (for [e journal_entries
                             :when (= fy (get e "fiscalYear"))
                             l (get e "lines" [])
                             :when (= account (get l "account"))]
                         (parse-long (str (get l "debitMinor" 0)))))
        remaining (- allocated spent)]
    {"account" account
     "fiscalYear" fy
     "allocatedMinor" allocated
     "spentMinor" spent
     "remainingMinor" remaining
     "over" (> spent allocated)}))
