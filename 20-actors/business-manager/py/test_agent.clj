#!/usr/bin/env bb
;; Clojure port of test_agent.py for business-manager agent.
(ns business-manager.py.test-agent
  "business-manager — accounting actor gate tests (offline, no kotoba host)."
  (:require [clojure.test :refer [deftest is run-tests testing]]
            [clojure.java.io :as io]))

;; The actor directory is hyphenated (business-manager); ns hyphens become underscores in
;; classpath lookup. Load-file the sibling agent.clj so its ns is registered, then require it.
(load-file (.getCanonicalPath
            (io/file (io/file (System/getProperty "babashka.file")) ".." "agent.clj")))
(require '[business-manager.py.agent :as agent])

(defn- _balanced_entry
  ([debit credit]
   (_balanced_entry debit credit {}))
  ([debit credit extra]
   (merge {"entryId" "je-1"
           "postedBy" "did:plc:cfo"
           "lines" [{"account" "5000" "debitMinor" debit "creditMinor" 0}
                    {"account" "1000" "debitMinor" 0 "creditMinor" credit}]}
          extra)))

(defn- _inv
  ([]
   (_inv {}))
  ([extra]
   (merge {"invoiceId" "inv-1"
           "direction" "payable"
           "party" "mitsuho"
           "amountMinor" (* 500000 100)
           "dueDate" "2026-06-30"
           "postedBy" "did:plc:ap"}
          extra)))

(deftest test-april-starts-new-fy
  (is (= "FY2026" (agent/fiscal_year_of "2026-04-01"))))

(deftest test-march-is-prior-fy
  (is (= "FY2026" (agent/fiscal_year_of "2027-03-31"))))

(deftest test-balanced-true
  (is (true? (agent/is_balanced [{"debitMinor" 500 "creditMinor" 0}
                                 {"debitMinor" 0 "creditMinor" 500}]))))

(deftest test-unbalanced-false
  (is (false? (agent/is_balanced [{"debitMinor" 500 "creditMinor" 0}
                                  {"debitMinor" 0 "creditMinor" 400}]))))

(deftest test-single-line-false
  (is (false? (agent/is_balanced [{"debitMinor" 500 "creditMinor" 0}]))))

(deftest test-unbalanced-entry-rejected
  (let [e (_balanced_entry 50000000 40000000)
        out (agent/post_journal_entry e "2026-05-01")]
    (is (= "rejected" (get out "state")))
    (is (clojure.string/includes? (get out "reason") "G2"))))

(deftest test-journal-auto-approved-below-1m
  (let [e (_balanced_entry (* 500000 100) (* 500000 100))
        out (agent/post_journal_entry e "2026-05-01")]
    (is (= "staged" (get out "state")))
    (is (= "auto-approved" (get out "approved")))))

(deftest test-journal-approval-required-above-1m
  (let [e (_balanced_entry (* 2000000 100) (* 2000000 100))
        out (agent/post_journal_entry e "2026-05-01")]
    (is (= "approval-required" (get out "approved")))))

(deftest test-caller-cannot-self-approve
  (let [e (_balanced_entry (* 2000000 100) (* 2000000 100) {"approved" "auto-approved"})
        out (agent/post_journal_entry e "2026-05-01")]
    (is (= "approval-required" (get out "approved")))))

(deftest test-po-threshold-5m
  (let [below (agent/post_purchase_order {"poId" "po1"
                                          "vendor" "mitsuho"
                                          "amountMinor" (* 4000000 100)
                                          "postedBy" "did:plc:buyer"} "2026-05-01")
        above (agent/post_purchase_order {"poId" "po2"
                                          "vendor" "x"
                                          "amountMinor" (* 6000000 100)
                                          "postedBy" "did:plc:buyer"} "2026-05-01")]
    (is (= "auto-approved" (get below "approved")))
    (is (= "approval-required" (get above "approved")))))

(deftest test-member-signature-posts
  (let [staged (agent/post_journal_entry (_balanced_entry 100000 100000) "2026-05-01")
        out (agent/authorize_posting staged {"origin" "member" "ref" "sig-1"})]
    (is (= "posted" (get out "state")))
    (is (= "sig-1" (get out "postedSig")))))

(deftest test-server-signature-refused
  (let [staged (agent/post_journal_entry (_balanced_entry 100000 100000) "2026-05-01")
        out (agent/authorize_posting staged {"origin" "server" "ref" "x"})]
    (is (true? (get out "refused")))
    (is (clojure.string/includes? (get out "reason") "G4"))))

(deftest test-missing-poster-rejected
  (let [e (_balanced_entry 100 100 {"postedBy" ""})
        out (agent/post_journal_entry e "2026-05-01")]
    (is (= "rejected" (get out "state")))))

(deftest test-append-only-flag
  (let [staged (agent/post_journal_entry (_balanced_entry 100000 100000) "2026-05-01")]
    (is (true? (get staged "appendOnly")))))

(deftest test-ledger-nets-to-zero
  (let [es [(_balanced_entry 100 100) (_balanced_entry 250 250)]
        tb (agent/trial_balance es)]
    (is (true? (get tb "balanced")))
    (is (= (get tb "totalDebitMinor") (get tb "totalCreditMinor")))))

(deftest test-payable-staged-auto-approved
  (let [out (agent/post_invoice (_inv) "2026-05-01")]
    (is (= "staged" (get out "state")))
    (is (= "payable" (get out "direction")))
    (is (= "auto-approved" (get out "approved")))
    (is (= "open" (get out "paymentStatus")))))

(deftest test-large-invoice-approval-required
  (let [out (agent/post_invoice (_inv {"amountMinor" (* 2000000 100)}) "2026-05-01")]
    (is (= "approval-required" (get out "approved")))))

(deftest test-bad-direction-rejected
  (is (= "rejected" (get (agent/post_invoice (_inv {"direction" "both"}) "2026-05-01") "state"))))

(deftest test-nonpositive-rejected
  (is (= "rejected" (get (agent/post_invoice (_inv {"amountMinor" 0}) "2026-05-01") "state"))))

(deftest test-settle-member-only
  (let [staged (agent/post_invoice (_inv) "2026-05-01")
        srv (agent/settle_invoice staged "2026-06-01" {"origin" "server" "ref" "x"})
        mem (agent/settle_invoice staged "2026-06-01" {"origin" "member" "ref" "s"})]
    (is (true? (get srv "refused")))
    (is (= "paid" (get mem "paymentStatus")))
    (is (= "2026-06-01" (get mem "paidAt")))))

(deftest test-aging-splits-ap-ar-and-overdue
  (let [invs [(agent/post_invoice (_inv {"invoiceId" "ap1"
                                         "direction" "payable"
                                         "amountMinor" 100
                                         "dueDate" "2026-01-01"}) "2026-05-01")
              (agent/post_invoice (_inv {"invoiceId" "ar1"
                                         "direction" "receivable"
                                         "amountMinor" 250
                                         "dueDate" "2026-12-31"}) "2026-05-01")]
        out (agent/invoice_aging invs "2026-06-07")]
    (is (= 100 (get out "apOpenMinor")))
    (is (= 250 (get out "arOpenMinor")))
    (is (some #(= "ap1" %) (get out "overdue")))
    (is (not (some #(= "ar1" %) (get out "overdue"))))))

(deftest test-budget-vs-actual-variance
  (let [budget {"account" "5000" "fiscalYear" "FY2026" "allocatedMinor" 1000000}
        entries [{"fiscalYear" "FY2026" "lines" [{"account" "5000" "debitMinor" 300000 "creditMinor" 0}]}
                 {"fiscalYear" "FY2026" "lines" [{"account" "5000" "debitMinor" 200000 "creditMinor" 0}]}
                 {"fiscalYear" "FY2025" "lines" [{"account" "5000" "debitMinor" 999 "creditMinor" 0}]}]
        out (agent/budget_vs_actual budget entries)]
    (is (= 500000 (get out "spentMinor")))
    (is (= 500000 (get out "remainingMinor")))
    (is (false? (get out "over")))))

(deftest test-over-budget-flagged
  (let [budget {"account" "5000" "fiscalYear" "FY2026" "allocatedMinor" 100}
        entries [{"fiscalYear" "FY2026" "lines" [{"account" "5000" "debitMinor" 250 "creditMinor" 0}]}]
        out (agent/budget_vs_actual budget entries)]
    (is (true? (get out "over")))
    (is (= -150 (get out "remainingMinor")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests (quote business-manager.py.test-agent))]
    (System/exit (if (zero? (+ fail error)) 0 1))))
