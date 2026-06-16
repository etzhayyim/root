(ns matsurigoto.methods.datoms
  "datoms.py — matsurigoto 政 R1.B: persist module executions to the kotoba Datom log.
  1:1 Clojure port of `methods/datoms.py` (ADR-2606062300).

  Converts a service module's output dict into APPEND-ONLY EAVT datoms over the `egov-exec-v1`
  graph, and builds an offline `kg.ingest_batch` body.

  Invariants enforced HERE (mirroring egov-execution-ontology.kotoba.edn):
    G1 no-operator-master-key : the tx datom asserts :egov.tx/server-held-authority false, and a
                                persisted certificate's :egov.cert/proof is forced to nil.
    G3 authority-bearing      : :operated-by ∈ {:etzhayyim-council, :adopting-government};
                                :authority-mode ∈ {:sovereign-governance, :supplied-to-state}.
    G5 append-only            : every record datom carries :egov.record/immutable true.
    G8 outward-gated          : kg-ingest-batch(published=true) RAISES.

  A datom is an [entity attribute value] triple (EAVT).

  House style: ':…' keyword strings stay strings; datom triples are vectors; data maps stay
  string-keyed; pure fns; stdlib only.

  The per-module converters take a string-keyed module output map (`out`) and a tx-options
  map whose keys mirror the Python keyword args:
    \"tx_id\" \"service\" \"operated_by\" \"authority_mode\" \"as_of\" \"spec_basis\"
    \"sourcing\" (default \":representative\") \"atlas_did\" (optional)
  The Python __main__ demo is omitted.")

(def ALLOWED-OPERATED-BY #{":etzhayyim-council" ":adopting-government"})
(def ALLOWED-AUTHORITY-MODE #{":sovereign-governance" ":supplied-to-state"})

(defn- tx-datoms
  "Port of _tx_datoms. `module` is the module id; `tx` is the option map (string keys)."
  [tx-id module tx]
  (let [operated-by (get tx "operated_by")
        authority-mode (get tx "authority_mode")
        as-of (get tx "as_of")
        spec-basis (get tx "spec_basis")
        sourcing (get tx "sourcing" ":representative")
        atlas-did (get tx "atlas_did")
        service (get tx "service")]
    (when-not (contains? ALLOWED-OPERATED-BY operated-by)
      (throw (ex-info (str "G3: :operated-by " (pr-str operated-by) " not allowed") {})))
    (when-not (contains? ALLOWED-AUTHORITY-MODE authority-mode)
      (throw (ex-info (str "G3: :authority-mode " (pr-str authority-mode) " not allowed") {})))
    (when-not (and spec-basis (not= spec-basis ""))
      (throw (ex-info "G2: :spec-basis required" {})))
    (cond-> [[tx-id ":egov.tx/id" tx-id]
             [tx-id ":egov.tx/service" service]
             [tx-id ":egov.tx/module" module]
             [tx-id ":egov.tx/operated-by" operated-by]
             [tx-id ":egov.tx/authority-mode" authority-mode]
             [tx-id ":egov.tx/as-of" as-of]
             [tx-id ":egov.tx/spec-basis" spec-basis]
             [tx-id ":egov.tx/sourcing" sourcing]
             [tx-id ":egov.tx/server-held-authority" false]]  ; G1
      atlas-did (conj [tx-id ":egov.tx/atlas-did" atlas-did]))))

(defn- assert-unsigned
  "G1: a module-produced artifact must be unsigned (proof nil, no server-held authority)."
  [artifact]
  (when (some? (get artifact "proof"))
    (throw (ex-info "G1: a module artifact must be unsigned (proof must be None)" {})))
  (when (not= (get artifact "server_held_authority") false)
    (throw (ex-info "G1: server_held_authority must be False" {}))))

(defn- cert-datoms
  [tx-id artifact]
  (assert-unsigned artifact)
  (let [cert-e (str tx-id "#cert")
        ;; artifact.get("kind") or artifact.get("type", ["", "?"])[-1]
        kind (or (get artifact "kind")
                 (last (get artifact "type" ["" "?"])))]
    [[cert-e ":egov.cert/of-tx" tx-id]
     [cert-e ":egov.cert/kind" kind]
     [cert-e ":egov.cert/status" (get artifact "status")]
     [cert-e ":egov.cert/proof" nil]]))  ; G1 — nil until the governing organ signs externally

;; ── per-module converters (take the module's R0 output map) ──
(defn assessment-datoms
  "tax-assess output → datoms."
  [out tx-id tx]
  (cond-> (into (tx-datoms tx-id "tax-assess" tx)
                [[tx-id ":egov.assessment/of-tx" tx-id]
                 [tx-id ":egov.assessment/liability" (get out "liability")]
                 [tx-id ":egov.assessment/effective-rate" (get out "effective_rate")]
                 [tx-id ":egov.assessment/currency" (get out "currency" "XXX")]])
    (contains? out "receipt") (into (cert-datoms tx-id (get out "receipt")))))

(defn civil-datoms
  "civil-registry registration → datoms (append-only)."
  [out tx-id tx]
  (let [rec (get out "record")
        rid (get rec "record_id")]
    (into (tx-datoms tx-id "civil-registry" tx)
          (concat
           [[rid ":egov.record/id" rid]
            [rid ":egov.record/of-tx" tx-id]
            [rid ":egov.record/kind" (get rec "vital_kind")]
            [rid ":egov.record/immutable" true]]  ; G5
           (cert-datoms tx-id (get out "certificate"))))))

(defn incorporation-datoms
  "corp-registry incorporation → datoms."
  [out tx-id tx]
  (let [rec (get out "record")
        rid (get rec "record_id")]
    (into (tx-datoms tx-id "corp-registry" tx)
          (concat
           [[rid ":egov.record/id" rid]
            [rid ":egov.record/of-tx" tx-id]
            [rid ":egov.record/kind" "incorporation"]
            [rid ":egov.record/immutable" true]  ; G5
            [rid ":egov.record/lei" (get rec "lei")]]
           (cert-datoms tx-id (get out "certificate"))))))

(defn passport-datoms
  "credential-issue passport → datoms (MRZ kept off the log; only the issuance record)."
  [out tx-id tx]
  (let [rid (str tx-id "#mrtd")]
    (into (tx-datoms tx-id "credential-issue" tx)
          (concat
           [[rid ":egov.record/id" rid]
            [rid ":egov.record/of-tx" tx-id]
            [rid ":egov.record/kind" "passport"]
            [rid ":egov.record/immutable" true]]  ; G5
           (cert-datoms tx-id (get out "document"))))))

(defn kg-ingest-batch
  "Build a `kg.ingest_batch` body. G8: published=true RAISES — live ingest is Council+operator
  gated. R1 constructs the dry-run body only."
  ([datoms] (kg-ingest-batch datoms "egov-exec-v1" false))
  ([datoms graph published]
   (when published
     (throw (ex-info (str "G8: live kotoba ingest is Council+operator gated (principal A: "
                          "Council Lv7+; principal B: adopting state). Construct the body and "
                          "hand off; do not publish here.")
                     {})))
   {"op" "kg.ingest_batch"
    "graph" graph
    "published" false
    "datoms" (vec datoms)
    "count" (count datoms)}))
