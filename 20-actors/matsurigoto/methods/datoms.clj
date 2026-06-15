;; datoms.clj — matsurigoto 政: persist module executions to the kotoba Datom log (R1.B).
;;
;; Clojure port of datoms.py (ADR-2606062300), Wave 1 of the clj-native migration
;; (ADR-2606142300) — the EAVT membrane that ties the ported reference modules (tax-assess /
;; civil-registry / corp-registry / credential-issue) into the kotoba Datom log. Converts a
;; module's output into APPEND-ONLY EAVT datoms over the `egov-exec-v1` graph and builds an
;; offline `kg.ingest_batch` body; state becomes canonical, as-of, replayable
;; (ADR-2605262130 + 2605312345).
;;
;; Invariants (mirroring 00-contracts/schemas/egov-execution-ontology.kotoba.edn):
;;   G1 no-operator-master-key : :egov.tx/server-held-authority false; a persisted certificate's
;;                               :egov.cert/proof is nil — a module signs nothing (ADR-2605231525).
;;   G3 authority-bearing      : :operated-by ∈ {:etzhayyim-council :adopting-government};
;;                               :authority-mode ∈ {:sovereign-governance :supplied-to-state}.
;;   G5 append-only            : every record datom carries :egov.record/immutable true.
;;   G8 outward-gated          : kg-ingest-batch with :published true RAISES — live ingest is
;;                               Council+operator gated; R0/R1 is dry-run body construction only.
;;
;; A datom is an [entity attribute value] triple (EAVT). Consumes the clj module outputs
;; (keyword keys). stdlib only.
(ns matsurigoto.methods.datoms
  (:require [clojure.string :as str]))

(def allowed-operated-by #{:etzhayyim-council :adopting-government})
(def allowed-authority-mode #{:sovereign-governance :supplied-to-state})

(defn- tx-datoms
  [tx-id {:keys [service module operated-by authority-mode as-of spec-basis sourcing atlas-did]
          :or   {sourcing :representative}}]
  (when-not (allowed-operated-by operated-by)
    (throw (ex-info (str "G3: :operated-by " (pr-str operated-by) " not allowed") {:operated-by operated-by})))
  (when-not (allowed-authority-mode authority-mode)
    (throw (ex-info (str "G3: :authority-mode " (pr-str authority-mode) " not allowed") {:authority-mode authority-mode})))
  (when (str/blank? (str spec-basis))
    (throw (ex-info "G2: :spec-basis required" {})))
  (cond-> [[tx-id :egov.tx/id tx-id]
           [tx-id :egov.tx/service service]
           [tx-id :egov.tx/module module]
           [tx-id :egov.tx/operated-by operated-by]
           [tx-id :egov.tx/authority-mode authority-mode]
           [tx-id :egov.tx/as-of as-of]
           [tx-id :egov.tx/spec-basis spec-basis]
           [tx-id :egov.tx/sourcing sourcing]
           [tx-id :egov.tx/server-held-authority false]]   ; G1
    atlas-did (conj [tx-id :egov.tx/atlas-did atlas-did])))

(defn- assert-unsigned!
  "G1: a module-produced artifact must be unsigned (proof nil, no server-held authority)."
  [artifact]
  (when (some? (:proof artifact))
    (throw (ex-info "G1: a module artifact must be unsigned (proof must be nil)" {})))
  (when (not= false (:server-held-authority artifact))
    (throw (ex-info "G1: server-held-authority must be false" {}))))

(defn- cert-datoms
  [tx-id artifact]
  (assert-unsigned! artifact)
  (let [cert-e (str tx-id "#cert")
        kind   (or (:kind artifact) (last (or (:type artifact) ["" "?"])))]
    [[cert-e :egov.cert/of-tx tx-id]
     [cert-e :egov.cert/kind kind]
     [cert-e :egov.cert/status (:status artifact)]
     [cert-e :egov.cert/proof nil]]))                       ; G1 — nil until the organ signs externally

;; ── per-module converters (take the clj module's R0 output) ──
(defn assessment-datoms
  "tax-assess output → datoms."
  [out tx-opts]
  (let [tx-id (:tx-id tx-opts)]
    (cond-> (into (tx-datoms tx-id (assoc tx-opts :module "tax-assess"))
                  [[tx-id :egov.assessment/of-tx tx-id]
                   [tx-id :egov.assessment/liability (:liability out)]
                   [tx-id :egov.assessment/effective-rate (:effective-rate out)]
                   [tx-id :egov.assessment/currency (:currency out "XXX")]])
      (:receipt out) (into (cert-datoms tx-id (:receipt out))))))

(defn civil-datoms
  "civil-registry registration → datoms (append-only)."
  [out tx-opts]
  (let [tx-id (:tx-id tx-opts)
        rec   (:record out)
        rid   (:record-id rec)]
    (-> (tx-datoms tx-id (assoc tx-opts :module "civil-registry"))
        (into [[rid :egov.record/id rid]
               [rid :egov.record/of-tx tx-id]
               [rid :egov.record/kind (:vital-kind rec)]
               [rid :egov.record/immutable true]])          ; G5
        (into (cert-datoms tx-id (:certificate out))))))

(defn incorporation-datoms
  "corp-registry incorporation → datoms."
  [out tx-opts]
  (let [tx-id (:tx-id tx-opts)
        rec   (:record out)
        rid   (:record-id rec)]
    (-> (tx-datoms tx-id (assoc tx-opts :module "corp-registry"))
        (into [[rid :egov.record/id rid]
               [rid :egov.record/of-tx tx-id]
               [rid :egov.record/kind "incorporation"]
               [rid :egov.record/immutable true]            ; G5
               [rid :egov.record/lei (:lei rec)]])
        (into (cert-datoms tx-id (:certificate out))))))

(defn passport-datoms
  "credential-issue passport → datoms (MRZ kept off the log; only the issuance record)."
  [out tx-opts]
  (let [tx-id (:tx-id tx-opts)
        rid   (str tx-id "#mrtd")]
    (-> (tx-datoms tx-id (assoc tx-opts :module "credential-issue"))
        (into [[rid :egov.record/id rid]
               [rid :egov.record/of-tx tx-id]
               [rid :egov.record/kind "passport"]
               [rid :egov.record/immutable true]])          ; G5
        (into (cert-datoms tx-id (:document out))))))

(defn kg-ingest-batch
  "Build a `kg.ingest_batch` body. G8: :published true RAISES — live ingest is Council+operator
   gated. R1 constructs the dry-run body only."
  ([datoms] (kg-ingest-batch datoms {}))
  ([datoms {:keys [graph published] :or {graph "egov-exec-v1" published false}}]
   (when published
     (throw (ex-info (str "G8: live kotoba ingest is Council+operator gated (principal A: Council "
                          "Lv7+; principal B: adopting state). Construct the body and hand off.")
                     {:gated true})))
   {:op "kg.ingest_batch" :graph graph :published false
    :datoms (vec datoms) :count (count datoms)}))
