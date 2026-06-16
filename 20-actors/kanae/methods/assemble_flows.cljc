(ns kanae.methods.assemble-flows
  "assemble_flows.py — 鼎 (kanae) domestic-flow-chain-assembly method (the coded R0 method).
  1:1 Clojure port of `methods/assemble_flows.py` (ADR-2605302300).

  Consumes a danjo budget ledger (danjo.methods.budget-ledger/build-ledger) and assembles
  `com.etzhayyim.kanae.fundFlowEdge` records: the appropriation→outlay chain of the public
  budget, as a graph of FACTUAL fiscal-flow edges (domestic-flow-chain-assembly).

  danjo finds, kanae renders. This is the render-input assembler. Constitutional discipline is
  STRUCTURAL — built into the record shape, not left to the caller:
    G2  — output is kotoba-EAVT-bound datoms (no RisingWave/Postgres/Lance); here we emit the
          lexicon maps that a kotoba cell asserts.
    G4  — NON-adjudicating: `flowClass` is descriptive only; `assert-non-adjudicating` refuses
          any verdict token (crime/violation/guilt/違法/不正/有罪) anywhere in the edge.
    G5  — every edge cites ≥2 upstream gov.dataset.* record CIDs (the appropriation + its outlay).
    G6  — every edge names its open `methodNoteCid`.
    G10 — aggregate-first: endpoints are fiscal-authority / program / recipient-class aggregates;
          a named party would require `publiclyNamedBasis` (a source CID), which this method never
          fabricates — so no private recipient is named at R0.

  flowNarrative (the Murakumo-LLM factual description, G7) is NOT produced here — it requires a
  live Murakumo node, which is operator-gated. Offline we stop at the edge graph.

  House style: ':…' keyword strings stay strings; pure fns; portable .cljc. `created-at` is a
  parameter (default fixed) so assembly is deterministic + testable. The Python `__main__` offline
  demo printer is intentionally omitted — the method API (assemble / validate-edge /
  assert-non-adjudicating) is the cell contract."
  (:require [clojure.string :as str]))

(def flow-classes
  #{"appropriation" "outlay" "subaward" "procurement-award"
    "intergovernmental-transfer" "aid-disbursement" "loan" "repayment"})

;; Tokens that would turn a factual edge into a verdict — unrepresentable (G4).
(def ^:private verdict-tokens
  ["crime" "violation" "guilt" "fraud" "illegal" "違法" "不正" "有罪" "犯罪"])

(def cell-did "did:web:kanae.etzhayyim.com:cell:flow_assembler")
(def attest-did "did:web:kanae.etzhayyim.com")
(def method-note "kanae.methodNote:v1-global-seed:domestic-flow-chain-assembly:1.0.0-draft")
(def default-created-at "2026-06-07T00:00:00.000Z")

(defn- endpoint
  "An aggregate endpoint (G10). No publiclyNamedBasis ⇒ no named party asserted."
  ([kind label] (endpoint kind label "jpn"))
  ([kind label jurisdiction]
   {"endpointKind" kind "label" label "jurisdiction" jurisdiction}))

(defn assert-non-adjudicating
  "G4: refuse any verdict token anywhere in the edge (defense in depth over the schema const)."
  [edge]
  (let [blob (str/lower-case
              (str/join " " [(str (get edge "flowClass" ""))
                             (str (get-in edge ["fromEndpoint" "label"] ""))
                             (str (get-in edge ["toEndpoint" "label"] ""))]))]
    (doseq [tok verdict-tokens]
      (when (str/includes? blob tok)
        (throw (ex-info (str "G4 violation: verdict token " (pr-str tok) " in a fundFlowEdge")
                        {:token tok}))))))

(def ^:private required-fields
  ["createdAt" "sourceCellDid" "flowClass" "fromEndpoint" "toEndpoint"
   "amount" "currency" "period" "jurisdiction" "sourceRecordCids"
   "methodNoteCid" "attestingDid"])

(defn- missing?
  "Mirrors Python `not edge.get(f)` falsiness (None/False/\"\"/empty coll). 0 is handled
  separately by the `(not= v 0)` guard, exactly like `... and edge.get(f) != 0`."
  [v]
  (or (nil? v) (false? v)
      (and (string? v) (= "" v))
      (and (coll? v) (empty? v))))

(defn validate-edge
  "Lexicon + charter gate check (fundFlowEdge required fields, enum, ≥2 CIDs)."
  [edge]
  (doseq [f required-fields]
    (let [v (get edge f)]
      (when (and (missing? v) (not= v 0))
        (throw (ex-info (str "fundFlowEdge missing required field " (pr-str f)) {:field f})))))
  (when-not (contains? flow-classes (get edge "flowClass"))
    (throw (ex-info (str "flowClass " (pr-str (get edge "flowClass")) " not in lexicon enum") {})))
  (when (< (count (get edge "sourceRecordCids")) 2)
    (throw (ex-info "G5 violation: fundFlowEdge needs ≥2 sourceRecordCids" {})))
  (assert-non-adjudicating edge))

(defn- outlay-edges
  "Reduce a group's outlays into edges (ministry → recipient-class), validating each."
  [edges {:keys [created-at ministry ministry-label period g approp-cid]} outlays]
  (reduce
   (fn [edges outlay]
     (let [recipient (endpoint "recipient-class" (get outlay "recipientName"))
           outlay-edge {"createdAt"        created-at
                        "sourceCellDid"    cell-did
                        "flowClass"        "outlay"
                        "fromEndpoint"     ministry
                        "toEndpoint"       recipient
                        "amount"           (str (get outlay "amountLocal"))
                        "currency"         (get outlay "currencyIso4217")
                        "period"           period
                        "jurisdiction"    (get g "jurisdiction")
                        ;; outlay grounded by its appropriation (≥2)
                        "sourceRecordCids" [(get outlay "cid") approp-cid]
                        "methodNoteCid"    method-note
                        "stateAlignedFlag" (get outlay "stateAlignedFlag")
                        "attestingDid"     attest-did
                        ;; projection annotations (not part of the strict lexicon record):
                        "observedAt"       (get outlay "awardDateUtc")
                        "_ministryLabel"   ministry-label
                        "_recipientLabel"  (get outlay "recipientName")
                        "_programCode"     (get g "programCode")
                        "_sourceUrl"       (get outlay "sourceUrl")}]
       (validate-edge outlay-edge)
       (conj edges outlay-edge)))
   edges
   outlays))

(defn assemble
  "Budget ledger → fundFlowEdge list (appropriation + outlay chain).

  Each returned map is a lexicon-valid fundFlowEdge PLUS yoro-projection annotations
  (`observedAt`, `_ministryLabel`, `_recipientLabel`) that the projector consumes."
  ([ledger] (assemble ledger default-created-at))
  ([ledger created-at]
   (let [treasury (endpoint "fiscal-authority"
                            "日本国 一般会計 (Japan General Account / National Treasury)")]
     (reduce
      (fn [edges [_key g]]
        (let [appropriations (get g "appropriations")
              outlays        (get g "outlays")]
          (if (empty? appropriations)
            ;; cannot ground an edge without an appropriation parent (G5 chain) — skip
            edges
            (let [approp         (first appropriations)
                  ministry-label (get approp "recipientName")
                  ministry       (endpoint "fiscal-authority" ministry-label)
                  period         (str "FY" (get g "fiscalYear"))
                  approp-cid     (get approp "cid")
                  ;; corroborating second CID for the appropriation edge:
                  ;; first outlay of the same program-year (else a 2nd appropriation)
                  second-cid     (cond
                                   (seq outlays)               (get (first outlays) "cid")
                                   (> (count appropriations) 1) (get (second appropriations) "cid")
                                   :else nil)
                  edges (if second-cid
                          (let [approp-edge {"createdAt"        created-at
                                             "sourceCellDid"    cell-did
                                             "flowClass"        "appropriation"
                                             "fromEndpoint"     treasury
                                             "toEndpoint"       ministry
                                             "amount"           (str (get approp "amountLocal"))
                                             "currency"         (get approp "currencyIso4217")
                                             "period"           period
                                             "jurisdiction"    (get g "jurisdiction")
                                             "sourceRecordCids" [approp-cid second-cid]
                                             "methodNoteCid"    method-note
                                             "stateAlignedFlag" (get approp "stateAlignedFlag")
                                             "attestingDid"     attest-did
                                             "observedAt"       (get approp "awardDateUtc")
                                             "_ministryLabel"   ministry-label
                                             "_recipientLabel"  ministry-label
                                             "_programCode"     (get g "programCode")
                                             "_sourceUrl"       (get approp "sourceUrl")}]
                            (validate-edge approp-edge)
                            (conj edges approp-edge))
                          edges)]
              (outlay-edges edges
                            {:created-at created-at :ministry ministry
                             :ministry-label ministry-label :period period
                             :g g :approp-cid approp-cid}
                            outlays)))))
      []
      ;; sorted(ledger["groups"].items()) — deterministic group order by key
      (sort-by key (get ledger "groups"))))))
