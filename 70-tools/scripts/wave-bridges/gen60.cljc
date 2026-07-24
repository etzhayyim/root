;; ported from 70-tools/scripts/wave-bridges/gen60.py (unit_refactor stage 0)
;; Wave 60 — civil-liability / fpic-consent / beneficial-ownership / ECA / shadow-fleet-insurance.
;; Faithful 1:1 port of the Python source-of-truth. Self-contained (inlines its
;; own snake/JSON helpers, no sibling requires). Data is string-keyed; FEEL
;; classify expressions are kept verbatim as strings. This wave's build-ddl-cols
;; uses the integer->bigint heuristic (matching the .py, with this wave's key
;; list). The Python "__main__" demo (writes lexicon JSON + BPMN XML, writes
;; per-actor DDL to /tmp/wave13/w60_NN.sql) is ported behind #?(:clj ...).
(ns scripts.wave-bridges.gen60
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json]))
  #?(:clj (:import [java.io File])))

(def repo "/Users/junkawasaki/github/etzhayyim/root")

(def actors
  [{"slug" "civil-liability"
    "app" "civilLiability"
    "methods"
    [{"name" "recordTortClaim"
      "desc" "Tort / class action / direct liability claim (bridges csdddDirective.flagDueDiligenceGap + climate-litigation + federal-court-docket)"
      "fields"
      [["claimId" "string" true]
       ["defendantLei" "string" false]
       ["forum" "string" true ["us_federal" "us_state" "uk_high_court" "nl_rechtbank" "fr_tribunal" "de_oberlandesgericht" "br_stf" "ke_high_court" "za_high_court" "icj_icpc" "arbitration_pcc"]]
       ["theoryOfHarm" "string" true ["duty_of_care" "breach_statutory" "nuisance" "climate_attribution" "workplace_harm" "supply_chain_complicity" "environmental_damage" "securities_class" "consumer_deception" "rico"]]
       ["dueDiligenceGapVid" "string" false nil "bridges csdddDirective.flagDueDiligenceGap"]
       ["aggregateDamagesMusd" "number" false]
       ["filedAt" "string" true]]
      "classify" nil}
     {"name" "flagDispositiveRuling"
      "desc" "Standing / dismissal / class certification / summary judgment (bridges csdddDirective.flagDueDiligenceGap + federal-court-docket.flagInjunction)"
      "fields"
      [["rulingId" "string" true]
       ["claimVid" "string" true nil "bridges recordTortClaim"]
       ["rulingKind" "string" true ["standing_denied" "motion_to_dismiss_granted" "class_certified" "class_decertified" "summary_judgment" "settlement_approved" "verdict_plaintiff" "verdict_defendant" "daubert_exclusion" "forum_non_conveniens"]]
       ["totalDamagesMusd" "number" false]
       ["ruledAt" "string" true]]
      "classify" nil}]}
   {"slug" "fpic-consent"
    "app" "fpicConsent"
    "methods"
    [{"name" "recordConsentEvent"
      "desc" "FPIC (Free Prior Informed Consent) / UNDRIP / ILO C169 event (bridges soyMoratorium.flagMoratoriumBreach + indigenous-rights + land-tenure)"
      "fields"
      [["eventId" "string" true]
       ["communityName" "string" true]
       ["countryIso3" "string" true]
       ["projectType" "string" true ["mining" "oil_gas" "hydro" "wind" "solar_utility" "agribusiness" "logging" "reservoir" "transmission_line" "pipeline" "rail_corridor" "tourism_resort" "carbon_credit" "redd_plus" "defense_installation"]]
       ["consentStage" "string" true ["pre_consultation" "agreement_reached" "ongoing_process" "refused" "withdrawn" "legal_challenge" "not_sought"]]
       ["moratoriumBreachVid" "string" false nil "bridges soyMoratorium.flagMoratoriumBreach"]
       ["reportedAt" "string" true]]
      "classify" nil}
     {"name" "flagFpicViolation"
      "desc" "FPIC violation / failure to obtain / coerced consent (bridges soyMoratorium.flagMoratoriumBreach + indigenous-rights + worker-grievance)"
      "fields"
      [["flagId" "string" true]
       ["eventVid" "string" true nil "bridges recordConsentEvent"]
       ["violationKind" "string" true ["no_consultation" "tokenistic" "coerced" "manipulated_info" "representative_unrecognized" "proceeded_without" "divide_and_rule" "compensation_inadequate" "land_grabbing" "threats_violence"]]
       ["affectedPersons" "integer" false]
       ["reportedAt" "string" true]]
      "classify" nil}]}
   {"slug" "beneficial-ownership-registry"
    "app" "beneficialOwnership"
    "methods"
    [{"name" "recordUboFiling"
      "desc" "UBO register filing (5AMLD / 6AMLD / US CTA / UK PSC — bridges debarmentList.flagPhoenixEntity + ofac-sanctions-sdn + lei-ownership)"
      "fields"
      [["filingId" "string" true]
       ["legalEntityLei" "string" false]
       ["registryKind" "string" true ["eu_5amld" "eu_6amld" "us_cta_fincen" "uk_psc" "ca_cbca" "au_dibo" "nz_bo_act" "sg_register" "hk_scr" "offshore_sos" "fatf_guidance"]]
       ["uboShareholdingPct" "number" false]
       ["uboJurisdictionIso3" "string" false]
       ["uboPepFlag" "boolean" false nil "PEP = politically exposed person"]
       ["phoenixEntityVid" "string" false nil "bridges debarmentList.flagPhoenixEntity"]
       ["filedAt" "string" true]]
      "classify" nil}
     {"name" "flagUboDiscrepancy"
      "desc" "UBO discrepancy / nominee / trust layering (bridges debarmentList.flagPhoenixEntity + ofac-sanctions-sdn + aml)"
      "fields"
      [["flagId" "string" true]
       ["filingVid" "string" true nil "bridges recordUboFiling"]
       ["discrepancyKind" "string" true ["registry_vs_bank_kyc" "nominee_only" "trust_layering" "bearer_share" "opaque_tier" "threshold_avoidance" "delayed_filing" "blank_filing" "circular_ownership" "dual_resident"]]
       ["severityTier" "string" false ["watch" "elevated" "high" "sdn_match"]]
       ["reportedAt" "string" true]]
      "classify" nil}]}
   {"slug" "export-credit-agency"
    "app" "exportCreditAgency"
    "methods"
    [{"name" "recordExposure"
      "desc" "ECA / Berne Union / OECD arrangement exposure (bridges sovereignGuarantee.flagCallEvent + sovereign-debt + just-transition)"
      "fields"
      [["exposureId" "string" true]
       ["ecaKind" "string" true ["us_exim" "jbic" "nexi" "kexim" "ksure" "cexim" "sinosure" "sace_italy" "euler_hermes" "ukef" "edc_canada" "efic_australia" "coface" "berne_union"]]
       ["borrowerCountryIso3" "string" true]
       ["sectorKind" "string" true ["oil_gas" "coal" "lng" "nuclear" "renewable" "aerospace" "defense" "rail" "shipping" "agri" "infrastructure" "manufacturing" "ict"]]
       ["exposureBusd" "number" true]
       ["guaranteeCallVid" "string" false nil "bridges sovereignGuarantee.flagCallEvent"]
       ["approvedAt" "string" true]]
      "classify" nil}
     {"name" "flagClimateCarveout"
      "desc" "CETP / Glasgow Statement / fossil-fuel ECA phase-out breach (bridges sovereignGuarantee.flagCallEvent + climate-value-chain + just-transition)"
      "fields"
      [["flagId" "string" true]
       ["exposureVid" "string" true nil "bridges recordExposure"]
       ["breachKind" "string" true ["cetp_fossil_support" "glasgow_statement_breach" "limited_exemption_abuse" "upstream_gas_loophole" "downstream_refinery" "thermal_coal" "domestic_only_carveout" "technical_assistance_gap" "misclassification"]]
       ["reportedAt" "string" true]]
      "classify" nil}]}
   {"slug" "shadow-fleet-insurance"
    "app" "shadowFleetInsurance"
    "methods"
    [{"name" "recordCoverage"
      "desc" "P&I Club / Russian reinsurance / shadow-fleet insurance (bridges priceCapCoalition.flagCapBreach + aisDarkVessel + insurance-policy)"
      "fields"
      [["coverageId" "string" true]
       ["vesselImo" "string" true]
       ["insurerLei" "string" false]
       ["insurerKind" "string" true ["igpi_club" "ingosstrakh" "sogaz" "chubb_russia_local" "turkish_insurer" "indian_insurer" "uae_captive" "unknown" "self_insured" "no_cover"]]
       ["reinsuranceChain" "string" false]
       ["capBreachVid" "string" false nil "bridges priceCapCoalition.flagCapBreach"]
       ["effectiveAt" "string" true]]
      "classify" nil}
     {"name" "flagGapOrFraud"
      "desc" "Insurance gap / fraudulent certificate / spill financial responsibility (bridges priceCapCoalition.flagCapBreach + hormuz-warrisk-premium + oilspill-clc)"
      "fields"
      [["flagId" "string" true]
       ["coverageVid" "string" true nil "bridges recordCoverage"]
       ["issueKind" "string" true ["no_cover_after_eu_ban" "forged_certificate" "nonresponsive_insurer" "sanctioned_reinsurer" "coverage_gap_sts" "out_of_scope_spill" "policy_mismatch" "flag_state_uncooperative" "bunker_convention_gap" "clc_gap"]]
       ["estLiabilityBusd" "number" false]
       ["reportedAt" "string" true]]
      "classify" nil}]}])

;; --- helpers (faithful port) ---

(defn upper? [^Character ch]
  (and (Character/isLetter ch) (Character/isUpperCase ch)))

(defn snake
  "def snake(s): per-char, uppercase -> '_'+lower, then lstrip('_')."
  [s]
  (let [out (apply str (map (fn [ch]
                              (if (upper? ch)
                                (str "_" (str/lower-case (str ch)))
                                (str ch)))
                            s))]
    (str/replace out #"^_+" "")))

(def ^:private sql-type-map
  {"string" "varchar" "integer" "int" "number" "double precision" "boolean" "boolean"})

(def ^:private bigint-keys
  ["count" "hours" "refusals" "doses" "shortfall" "customers" "beneficiar" "units" "tonnes"
   "volume" "persons" "capacity" "members" "passed" "impacted" "workers" "covered"
   "premises" "cases" "issued" "barrels"])

(defn build-ddl-cols [methods]
  (loop [methods methods
         seen #{"vertex_id"}
         cols [["vertex_id" "varchar" "PRIMARY KEY"]]]
    (if-let [m (first methods)]
      (let [[seen cols]
            (loop [fs (get m "fields") seen seen cols cols]
              (if-let [f (first fs)]
                (let [name (nth f 0) ftype (nth f 1)
                      col (snake name)]
                  (if (contains? seen col)
                    (recur (rest fs) seen cols)
                    (let [sql-t (if (and (= ftype "integer")
                                         (some #(str/includes? col %) bigint-keys))
                                  "bigint"
                                  (get sql-type-map ftype "varchar"))]
                      (recur (rest fs) (conj seen col) (conj cols [col sql-t ""])))))
                [seen cols]))
            classify (get m "classify")
            [seen cols]
            (if classify
              (let [cname (nth classify 0)
                    col (if (some upper? cname) (snake cname) cname)]
                (if (contains? seen col)
                  [seen cols]
                  [(conj seen col) (conj cols [col "varchar" ""])]))
              [seen cols])]
        (recur (rest methods) seen cols))
      (loop [extra [["status" "varchar" ""] ["created_at" "varchar" ""] ["owner_did" "varchar" ""]
                    ["sensitivity_ord" "int" ""] ["org_id" "varchar" ""] ["user_id" "varchar" ""]
                    ["actor_id" "varchar" ""]]
             seen seen cols cols]
        (if-let [c (first extra)]
          (if (contains? seen (nth c 0))
            (recur (rest extra) seen cols)
            (recur (rest extra) (conj seen (nth c 0)) (conj cols c)))
          cols)))))

(defn gen-lexicon [actor method]
  (let [nsid (str "com.etzhayyim.apps." (get actor "app") "." (get method "name"))]
    (loop [fs (get method "fields") props {} required []]
      (if-let [f (first fs)]
        (let [name (nth f 0) ftype (nth f 1) req (nth f 2)
              enum (when (> (count f) 3) (nth f 3))
              desc (when (> (count f) 4) (nth f 4))
              p (cond-> {"type" ftype}
                  enum (assoc "enum" enum)
                  desc (assoc "description" desc)
                  (and (= ftype "string") (str/ends-with? name "At")) (assoc "format" "datetime"))]
          (recur (rest fs)
                 (assoc props name p)
                 (if req (conj required name) required)))
        (let [base-out {"ok" {"type" "boolean"}
                        "vertexId" {"type" "string"}
                        "instanceKey" {"type" "integer"}
                        "error" {"type" "string"}}
              classify (get method "classify")
              out-props (if classify
                          (let [col (nth classify 0) enum (nth classify 2)]
                            (assoc base-out col {"type" "string" "enum" enum}))
                          base-out)]
          {"lexicon" 1
           "id" nsid
           "defs" {"main" {"type" "procedure"
                           "description" (get method "desc")
                           "input" {"encoding" "application/json"
                                    "schema" {"type" "object" "required" required "properties" props}}
                           "output" {"encoding" "application/json"
                                     "schema" {"type" "object" "properties" out-props}}}}})))))

(defn- xml-escape [s]
  (-> s
      (str/replace "&" "&amp;")
      (str/replace "\"" "&quot;")
      (str/replace "<" "&lt;")
      (str/replace ">" "&gt;")))

(defn gen-bpmn [actor method]
  (let [slug (get actor "slug")
        table (str "vertex_open_" (str/replace slug "-" "_"))
        proc-id (str "open_" (str/replace slug "-" "_") "_" (snake (get method "name")))
        action (str "open." (get actor "app") "." (get method "name"))
        field-parts (map (fn [f]
                           (let [name (nth f 0) col (snake name)]
                             (str col ": " name)))
                         (get method "fields"))
        classify (get method "classify")
        classify-part (when classify
                        (let [col (nth classify 0) expr (nth classify 1)
                              sc (if (some upper? col) (snake col) col)]
                          [(str sc ": " expr)]))
        vparts (concat ["vertex_id: vertexId"]
                       field-parts
                       (or classify-part [])
                       ["status: \"active\""
                        "created_at: string(now())"
                        "owner_did: callerDid"
                        "sensitivity_ord: 1"
                        "org_id: callerDid"
                        "user_id: callerDid"
                        (str "actor_id: \"sys.bpmn.open-" slug "\"")])
        feel (str "{" (str/join ", " vparts) "}")
        x (xml-escape feel)]
    (str "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<bpmn:definitions xmlns:bpmn=\"http://www.omg.org/spec/BPMN/20100524/MODEL\" xmlns:zeebe=\"http://camunda.org/schema/zeebe/1.0\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" id=\"Definitions_" proc-id "\" targetNamespace=\"https://etzhayyim.com/bpmn/open-" slug "\" exporter=\"hand-written\" exporterVersion=\"1.0\">
  <bpmn:process id=\"" proc-id "\" name=\"" (get method "name") "\" isExecutable=\"true\">
    <bpmn:startEvent id=\"Start\"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id=\"Flow_S\" sourceRef=\"Start\" targetRef=\"Task_Save\"/>
    <bpmn:serviceTask id=\"Task_Save\" name=\"save\">
      <bpmn:extensionElements><zeebe:taskDefinition type=\"generic.db.insert\"/>
        <zeebe:ioMapping><zeebe:input source=\"=&quot;" table "&quot;\" target=\"table\"/><zeebe:input source=\"=" x "\" target=\"values\"/><zeebe:input source=\"=&quot;ignore&quot;\" target=\"onConflict\"/></zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id=\"Flow_A\" sourceRef=\"Task_Save\" targetRef=\"Task_Audit\"/>
    <bpmn:serviceTask id=\"Task_Audit\" name=\"audit\">
      <bpmn:extensionElements><zeebe:taskDefinition type=\"generic.audit.emit\"/>
        <zeebe:ioMapping><zeebe:input source=\"=&quot;did:web:open-" slug ".etzhayyim.com&quot;\" target=\"actor\"/><zeebe:input source=\"=&quot;" action "&quot;\" target=\"action\"/><zeebe:input source=\"={vertexId: vertexId}\" target=\"payload\"/></zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id=\"Flow_End\" sourceRef=\"Task_Audit\" targetRef=\"End\"/>
    <bpmn:endEvent id=\"End\"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>")))

(defn gen-ddl [actor]
  (let [slug (get actor "slug")
        table (str "vertex_open_" (str/replace slug "-" "_"))
        cols (build-ddl-cols (get actor "methods"))
        body (str/join ",\n  "
                       (map (fn [c]
                              (str (nth c 0) " " (nth c 1)
                                   (if (seq (nth c 2)) (str " " (nth c 2)) "")))
                            cols))]
    (str "CREATE TABLE IF NOT EXISTS " table " (\n  " body "\n);\n")))

;; --- host I/O demo (Python __main__) ---
#?(:clj
   (defn- write-text! [^String path ^String content]
     (let [f (File. path)]
       (.mkdirs (.getParentFile f))
       (spit f content))))

#?(:clj
   (defn -main [& _]
     (doseq [[i a] (map-indexed (fn [i a] [(inc i) a]) actors)]
         (let [bd (str repo "/00-contracts/bpmn/com/etzhayyim/open-" (get a "slug"))
               ld (str repo "/00-contracts/lexicons/com/etzhayyim/apps/" (get a "app"))]
           (.mkdirs (File. bd))
           (.mkdirs (File. ld))
           (doseq [m (get a "methods")]
             (write-text! (str ld "/" (get m "name") ".json")
                          (json/generate-string (gen-lexicon a m) {:pretty true}))
             (write-text! (str bd "/" (get m "name") ".bpmn")
                          (gen-bpmn a m)))
           (let [ddl (gen-ddl a)
                 out (str "/tmp/wave13/w60_" (format "%02d" i) ".sql")]
             (write-text! out ddl)
             (println (str "wrote " out)))))))
