(ns kanae.methods.assemble-flows
  "kanae 鼎 domestic-flow-chain-assembly method (babashka port of assemble_flows.py).

  Consumes a danjo budget ledger and assembles `com.etzhayyim.kanae.fundFlowEdge` records.
  Constitutional discipline is structural (G2/G4/G5/G6/G10 — see Python original for full docs).
  Stdlib only. Deterministic: same ledger + created_at → same edges.")

;; ---------------------------------------------------------------------------
;; Constants
;; ---------------------------------------------------------------------------

(def FLOW-CLASSES
  #{"appropriation" "outlay" "subaward" "procurement-award"
    "intergovernmental-transfer" "aid-disbursement" "loan" "repayment"})

;; Tokens that would turn a factual edge into a verdict — unrepresentable (G4).
(def ^:private VERDICT-TOKENS
  ["crime" "violation" "guilt" "fraud" "illegal" "違法" "不正" "有罪" "犯罪"])

(def CELL-DID "did:web:kanae.etzhayyim.com:cell:flow_assembler")
(def ATTEST-DID "did:web:kanae.etzhayyim.com")
(def METHOD-NOTE "kanae.methodNote:v1-global-seed:domestic-flow-chain-assembly:1.0.0-draft")
(def DEFAULT-CREATED-AT "2026-06-07T00:00:00.000Z")

;; ---------------------------------------------------------------------------
;; Helpers (must appear before assemble)
;; ---------------------------------------------------------------------------

(defn- endpoint
  "An aggregate endpoint (G10). No publiclyNamedBasis => no named party asserted."
  ([kind label] (endpoint kind label "jpn"))
  ([kind label jurisdiction]
   {"endpointKind" kind "label" label "jurisdiction" jurisdiction}))

(defn assert-non-adjudicating
  "G4: refuse any verdict token anywhere in the edge (defense in depth over schema const)."
  [edge]
  (let [blob (clojure.string/lower-case
               (str (get edge "flowClass" "")
                    " "
                    (get-in edge ["fromEndpoint" "label"] "")
                    " "
                    (get-in edge ["toEndpoint" "label"] "")))]
    (doseq [tok VERDICT-TOKENS]
      (when (clojure.string/includes? blob tok)
        (throw (ex-info (str "G4 violation: verdict token " (pr-str tok) " in a fundFlowEdge")
                        {:token tok :blob blob}))))))

(defn validate-edge
  "Lexicon + charter gate check (fundFlowEdge required fields, enum, >=2 CIDs)."
  [edge]
  (let [required ["createdAt" "sourceCellDid" "flowClass" "fromEndpoint" "toEndpoint"
                  "amount" "currency" "period" "jurisdiction" "sourceRecordCids"
                  "methodNoteCid" "attestingDid"]]
    (doseq [f required]
      (let [v (get edge f)]
        (when (and (nil? v) (not= v 0))
          (when (or (nil? v) (and (string? v) (= v "")))
            (throw (ex-info (str "fundFlowEdge missing required field " (pr-str f))
                            {:field f}))))))
    (when-not (contains? FLOW-CLASSES (get edge "flowClass"))
      (throw (ex-info (str "flowClass " (pr-str (get edge "flowClass")) " not in lexicon enum")
                      {:flowClass (get edge "flowClass")})))
    (when (< (count (get edge "sourceRecordCids" [])) 2)
      (throw (ex-info "G5 violation: fundFlowEdge needs >=2 sourceRecordCids"
                      {:cids (get edge "sourceRecordCids")})))
    (assert-non-adjudicating edge)))

;; ---------------------------------------------------------------------------
;; assemble
;; ---------------------------------------------------------------------------

(defn assemble
  "Budget ledger -> fundFlowEdge list (appropriation + outlay chain).

  Each returned map is a lexicon-valid fundFlowEdge PLUS yoro-projection annotations
  (`observedAt`, `_ministryLabel`, `_recipientLabel`) that the projector consumes."
  ([ledger] (assemble ledger DEFAULT-CREATED-AT))
  ([ledger created-at]
   (let [treasury (endpoint "fiscal-authority"
                             "日本国 一般会計 (Japan General Account / National Treasury)")]
     (reduce
       (fn [edges [_key g]]
         (let [appropriations (get g "appropriations" [])
               outlays        (get g "outlays" [])]
           (if (empty? appropriations)
             ;; cannot ground an edge without an appropriation parent (G5 chain) — skip
             edges
             (let [approp         (first appropriations)
                   ministry-label (get approp "recipientName")
                   ministry       (endpoint "fiscal-authority" ministry-label)
                   period         (str "FY" (get g "fiscalYear"))
                   approp-cid     (get approp "cid")
                   second-cid     (or (get (first outlays) "cid")
                                      (get (second appropriations) "cid"))
                   ;; appropriation edge
                   approp-edges
                   (if second-cid
                     (let [ae {"createdAt"        created-at
                               "sourceCellDid"    CELL-DID
                               "flowClass"        "appropriation"
                               "fromEndpoint"     treasury
                               "toEndpoint"       ministry
                               "amount"           (str (get approp "amountLocal"))
                               "currency"         (get approp "currencyIso4217")
                               "period"           period
                               "jurisdiction"     (get g "jurisdiction")
                               "sourceRecordCids" [approp-cid second-cid]
                               "methodNoteCid"    METHOD-NOTE
                               "stateAlignedFlag" (get approp "stateAlignedFlag")
                               "attestingDid"     ATTEST-DID
                               "observedAt"       (get approp "awardDateUtc")
                               "_ministryLabel"   ministry-label
                               "_recipientLabel"  ministry-label
                               "_programCode"     (get g "programCode")
                               "_sourceUrl"       (get approp "sourceUrl")}]
                       (validate-edge ae)
                       [ae])
                     [])
                   ;; outlay edges
                   outlay-edges
                   (mapv (fn [outlay]
                           (let [recipient (endpoint "recipient-class" (get outlay "recipientName"))
                                 oe {"createdAt"        created-at
                                     "sourceCellDid"    CELL-DID
                                     "flowClass"        "outlay"
                                     "fromEndpoint"     ministry
                                     "toEndpoint"       recipient
                                     "amount"           (str (get outlay "amountLocal"))
                                     "currency"         (get outlay "currencyIso4217")
                                     "period"           period
                                     "jurisdiction"     (get g "jurisdiction")
                                     "sourceRecordCids" [(get outlay "cid") approp-cid]
                                     "methodNoteCid"    METHOD-NOTE
                                     "stateAlignedFlag" (get outlay "stateAlignedFlag")
                                     "attestingDid"     ATTEST-DID
                                     "observedAt"       (get outlay "awardDateUtc")
                                     "_ministryLabel"   ministry-label
                                     "_recipientLabel"  (get outlay "recipientName")
                                     "_programCode"     (get g "programCode")
                                     "_sourceUrl"       (get outlay "sourceUrl")}]
                             (validate-edge oe)
                             oe))
                         outlays)]
               (concat edges approp-edges outlay-edges)))))
       []
       (sort-by key (get ledger "groups" {}))))))
