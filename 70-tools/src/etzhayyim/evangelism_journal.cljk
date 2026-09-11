(ns etzhayyim.evangelism-journal
  "Personal append-only journal of the founder's OWN interpersonal evangelism
  activity (Mission Charter §1.16 / ADR-2607061700) — face-to-face /
  door-to-door / street / online-dialogue.

  Writes are `com.etzhayyim.apps.etzhayyim.evangelismActivityAttestation`-
  shaped (00-contracts/lexicons/.../evangelismActivityAttestation.json):
  every record fixes the four STRUCTURAL const fields and NEVER carries a
  recipient/household/outcome field — the doctrine is 'never a target-list'
  (ADR-2606281500 rule 4), preserved unchanged by ADR-2607061700's carve-out
  (which only ever applied to actor-authored DIGITAL invitational content,
  never to this ledger). ADR-2607061700 Alternatives C also permanently
  rejected any JW-style quota/assignment system — this module never
  aggregates across Adherents or enforces a minimum; `summarize` below is
  personal recognition, not enforcement.

  This module deliberately does NOT extend tomoshibi: tomoshibi's own
  invariant (its README.md/CLAUDE.md) scopes it to digital publication only
  ('対人ではなく digital 招待発信のみを扱う — 対人伝道は信者個人の実践であり
  本actorの対象外', held across all iterations). There is also no governor
  here: a governor censors an AI's autonomously-DRAFTED content before
  publication; this is a human's own truthful self-report of activity that
  already happened, so containment doesn't apply the same way — only
  lexicon-conformance (the :pre checks below) does.

  Classification: internal confidential religious-corp data, per the
  existing `com.etzhayyim.encrypted.*` Confidentiality Tier-1 principle
  (root CLAUDE.md 'Substrate boundary' table) — this is not a new privacy
  mechanism, just this data's classification under the existing one. R0
  here ships the pure record/validate/summarize logic + an in-process
  MemStore; wiring an actual encrypted, net-kotobase/kotoba-Datom-log-backed
  `Store` is R1+ future work (same honest-maturity split as tomoshibi's own
  MemStore-only R0 — see its MATURITY.md).")

(def known-methods
  "The lexicon's `interpersonalMethod` knownValues, mirrored here so tests
  can assert against a single source (schema-drift-guarded in
  test_evangelism_journal.cljc against the real lexicon file)."
  #{"face-to-face" "door-to-door" "street" "online-dialogue"})

;; STRUCTURAL const fields per evangelismActivityAttestation.json — every
;; value here is the ONLY value the lexicon accepts (§1.16(b)-(d) + the
;; "voluntary practice, never an obligation" framing of ADR-2607061700).
(def structural-consts
  {:optOutAffordancePresent true
   :coercionAttested false
   :minorSoloSolicitationAttested false
   :voluntaryAttested true})

;; Mirrors evangelismActivityAttestation.json's `record.required` array —
;; schema-drift-guarded in test_evangelism_journal.cljc.
(def lexicon-required-fields
  #{:createdAt :mode :optOutAffordancePresent :coercionAttested
    :minorSoloSolicitationAttested :voluntaryAttested :attestingCellDid})

(defn record
  "Construct one evangelismActivityAttestation-shaped record for the
  founder's own interpersonal evangelism activity. `now` is caller-supplied
  (ISO-8601 datetime string) — no `(java.time.Instant/now)` inside, keeps
  this pure/testable. Deliberately has no parameter for recipient/household/
  address/response — there is nowhere to put one even if a caller wanted to."
  [{:keys [adherent-did interpersonal-method now attesting-cell-did]}]
  {:pre [(contains? known-methods interpersonal-method)
         (string? adherent-did) (seq adherent-did)
         (string? now) (seq now)]}
  (merge structural-consts
         {:createdAt now
          :mode "interpersonal"
          :adherentDid adherent-did
          :interpersonalMethod interpersonal-method
          :attestingCellDid (or attesting-cell-did adherent-did)}))

(defprotocol Store
  (all-records [s] "every recorded attestation, oldest first")
  (record! [s attestation] "append one immutable attestation"))

(defrecord MemStore [a]
  Store
  (all-records [_] (:records @a))
  (record! [s attestation] (swap! a update :records conj attestation) s))

(defn seed-db
  "An empty MemStore. R1+: swap for a kotoba-Datom-log/net-kotobase-backed
  Store behind the encrypted-envelope confidentiality classification
  documented above — same protocol, no rewrite of callers."
  []
  (->MemStore (atom {:records []})))

(defn month-key
  "YYYY-MM from an ISO-8601 createdAt string — the grouping key for a
  personal monthly report."
  [created-at]
  (subs created-at 0 7))

(defn summarize
  "Personal activity report over a list of attestation records: total count,
  count by interpersonalMethod, count by month. This is the entire
  'publisher report' experience this journal supports — a tally of one's OWN
  activity instances, never who was reached or how they responded. Not a
  quota: there is no target/minimum here to compare the tally against."
  [records]
  {:total (count records)
   :by-method (frequencies (map :interpersonalMethod records))
   :by-month (frequencies (map #(month-key (:createdAt %)) records))})
