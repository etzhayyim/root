;; ported from 70-tools/scripts/wave-bridges/gen55.py (unit_refactor stage 0)
;; Wave 55 — gsp-eligibility / import-refusal / treasury-rulemaking / imf-article-iv / marine-heatwave.
;; Faithful 1:1 port of the Python source-of-truth. Self-contained (inlines its
;; own snake/JSON helpers, no sibling requires). Data is string-keyed; FEEL
;; classify expressions are kept verbatim as strings. Note: this wave's
;; build-ddl-cols adds an integer->bigint heuristic (matching the .py). The
;; Python "__main__" demo (writes lexicon JSON + BPMN XML, writes per-actor DDL
;; to /tmp/wave13/w55_NN.sql) is ported behind #?(:clj ...) as `-main`.
(ns scripts.wave-bridges.gen55
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json]))
  #?(:clj (:import [java.io File])))

(def repo "/Users/junkawasaki/github/etzhayyim/root")

(def actors
  [{"slug" "gsp-eligibility"
    "app" "gspEligibility"
    "methods"
    [{"name" "recordEligibilityReview"
      "desc" "US/EU/UK GSP trade preference eligibility review (bridges tripsWaiver.flagRetaliationRisk + ustr-section-301 + wto-dispute)"
      "fields"
      [["reviewId" "string" true]
       ["programKind" "string" true ["us_gsp" "eu_gsp_plus" "eu_ebe" "uk_dcts" "japan_gsp" "canada_gpt" "australia_dcs" "china_ldc"]]
       ["beneficiaryCountryIso3" "string" true]
       ["reviewTrigger" "string" true ["petition" "self_initiated" "annual" "statutory_graduation" "labor_rights" "ip_protection" "market_access"]]
       ["retaliationVid" "string" false nil "bridges tripsWaiver.flagRetaliationRisk"]
       ["initiatedAt" "string" true]]
      "classify" nil}
     {"name" "flagEligibilityRemoval"
      "desc" "Preference suspension / country graduation / de-listing (bridges tripsWaiver.flagRetaliationRisk + wto-dispute + labour-mobility)"
      "fields"
      [["flagId" "string" true]
       ["reviewVid" "string" true nil "bridges recordEligibilityReview"]
       ["removalKind" "string" true ["full_suspension" "partial_withdrawal" "product_specific" "competitive_need" "graduation" "ip_failure" "labor_failure" "corruption"]]
       ["affectedTradeMusd" "number" false]
       ["reportedAt" "string" true]]
      "classify" nil}]}
   {"slug" "import-refusal"
    "app" "importRefusal"
    "methods"
    [{"name" "recordRefusal"
      "desc" "FDA import refusal / EU RASFF rejection / CBP hold (bridges residueMrl.flagMrlBreach + rasff-food-safety + fda-adufa)"
      "fields"
      [["refusalId" "string" true]
       ["borderAgency" "string" true ["fda" "usda_fsis" "cbp" "eu_rasff" "cfia_canada" "jma_japan" "mhlw_japan" "aqsiq_china" "fssai_india"]]
       ["originCountryIso3" "string" true]
       ["destinationCountryIso3" "string" true]
       ["productCategory" "string" true ["seafood" "fresh_produce" "meat_poultry" "dairy" "dietary_supplement" "spice" "processed" "beverage" "infant_formula" "medical_device"]]
       ["violationKind" "string" true ["pesticide_residue" "veterinary_residue" "microbial" "heavy_metal" "aflatoxin" "adulteration" "unapproved_additive" "labeling" "allergen" "radiological"]]
       ["mrlBreachVid" "string" false nil "bridges residueMrl.flagMrlBreach"]
       ["shipmentValueUsd" "number" false]
       ["refusedAt" "string" true]]
      "classify" ["severityTier" "if violationKind = \"microbial\" or violationKind = \"aflatoxin\" or violationKind = \"heavy_metal\" then \"high\" else if violationKind = \"pesticide_residue\" or violationKind = \"veterinary_residue\" then \"medium\" else \"low\"" ["low" "medium" "high"]]}
     {"name" "flagRecurringOrigin"
      "desc" "Recurring origin-country refusal pattern (bridges residueMrl.flagMrlBreach + trade-sanitary + wto-dispute)"
      "fields"
      [["patternId" "string" true]
       ["refusalVid" "string" true nil "bridges recordRefusal"]
       ["refusalsLast12mo" "integer" false]
       ["concernKind" "string" true ["systemic_origin" "producer_cluster" "single_violator" "seasonal" "climate_related" "emerging_compound" "sanitary_phytosanitary"]]
       ["reportedAt" "string" true]]
      "classify" nil}]}
   {"slug" "treasury-rulemaking"
    "app" "treasuryRulemaking"
    "methods"
    [{"name" "recordRule"
      "desc" "US Treasury / IRS Notice / NPRM / final rule (bridges iraTaxCredit.flagFeocDisqualification + IRA implementation + APA)"
      "fields"
      [["ruleId" "string" true]
       ["agency" "string" true ["treasury" "irs" "ofac" "fincen" "occ" "fsoc" "cfius" "bea"]]
       ["ruleType" "string" true ["notice" "nprm" "temp_final" "final_rule" "direct_final" "guidance" "revenue_procedure" "private_letter"]]
       ["subjectArea" "string" true ["ira_45x" "ira_45v" "ira_45q" "ira_45y" "cfius_review" "bsa_aml" "sanctions" "beneficial_ownership" "digital_asset" "foreign_trust" "cbdc"]]
       ["feocFlagVid" "string" false nil "bridges iraTaxCredit.flagFeocDisqualification"]
       ["federalRegisterNo" "string" false]
       ["publishedAt" "string" true]]
      "classify" nil}
     {"name" "flagChallenge"
      "desc" "APA challenge / Chevron step-2 / West Virginia v EPA major questions (bridges iraTaxCredit.flagFeocDisqualification + climate-litigation + wto-dispute)"
      "fields"
      [["flagId" "string" true]
       ["ruleVid" "string" true nil "bridges recordRule"]
       ["challengeKind" "string" true ["apa_arbitrary_capricious" "major_questions_doctrine" "chevron_overturned" "statutory_ultra_vires" "constitutional_takings" "equal_protection" "preemption" "retroactivity"]]
       ["plaintiffCategory" "string" false ["industry" "state_ag" "ngo" "individual" "foreign_entity" "trade_association"]]
       ["filedAt" "string" true]]
      "classify" nil}]}
   {"slug" "imf-article-iv"
    "app" "imfArticleIv"
    "methods"
    [{"name" "recordConsultation"
      "desc" "IMF Article IV / WEO / FSAP surveillance (bridges emFxReserves.flagReserveAdequacy + sovereign-debt + imf-sdr)"
      "fields"
      [["consultationId" "string" true]
       ["memberCountryIso3" "string" true]
       ["surveillanceKind" "string" true ["article_iv" "fsap" "weo_update" "global_financial_stability" "external_sector_report" "spillover_report" "weo_focus"]]
       ["reserveAdequacyVid" "string" false nil "bridges emFxReserves.flagReserveAdequacy"]
       ["staffView" "string" false ["clean_bill" "caveats" "risks_elevated" "risks_tilted_downside" "critical_imbalance"]]
       ["concludedAt" "string" true]]
      "classify" nil}
     {"name" "flagProgramRequest"
      "desc" "IMF program request (SBA/EFF/RSF/RCF/PRGT — bridges emFxReserves.flagReserveAdequacy + sovereignDebt.recordDebtRestructure)"
      "fields"
      [["programId" "string" true]
       ["consultationVid" "string" true nil "bridges recordConsultation"]
       ["programType" "string" true ["sba" "eff" "rsf" "rfi" "rcf" "pll" "fcl" "psi" "prgt" "scf"]]
       ["notionalBusd" "number" false]
       ["conditionalityCount" "integer" false]
       ["approvedAt" "string" true]]
      "classify" nil}]}
   {"slug" "marine-heatwave"
    "app" "marineHeatwave"
    "methods"
    [{"name" "recordMhwEvent"
      "desc" "Marine heatwave event (Hobday category / NOAA CRW / BOM / Copernicus — bridges coralReefBleaching.flagMortalityRisk + ocean-acidification + fisheries-iuu)"
      "fields"
      [["eventId" "string" true]
       ["regionName" "string" true]
       ["latCenter" "number" false]
       ["lonCenter" "number" false]
       ["hobdayCategory" "string" true ["cat_i_moderate" "cat_ii_strong" "cat_iii_severe" "cat_iv_extreme" "cat_v_unprecedented"]]
       ["durationDays" "integer" false]
       ["peakIntensityC" "number" false]
       ["coralBleachingVid" "string" false nil "bridges coralReefBleaching.flagMortalityRisk"]
       ["detectedAt" "string" true]]
      "classify" nil}
     {"name" "flagEcosystemImpact"
      "desc" "Fishery collapse / seabird mortality / HAB bloom cascade (bridges coralReefBleaching.flagMortalityRisk + fisheries-iuu + biodiversity-gbf)"
      "fields"
      [["impactId" "string" true]
       ["eventVid" "string" true nil "bridges recordMhwEvent"]
       ["impactKind" "string" true ["coral_bleaching" "kelp_collapse" "fishery_closure" "harmful_algal_bloom" "seabird_die_off" "whale_stranding" "cephalopod_range_shift" "shellfish_mortality"]]
       ["biomassLossPct" "number" false]
       ["reportedAt" "string" true]]
      "classify" ["severityTier" "if biomassLossPct != null and biomassLossPct >= 50 then \"catastrophic\" else if biomassLossPct != null and biomassLossPct >= 20 then \"significant\" else \"moderate\"" ["moderate" "significant" "catastrophic"]]}]}])

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
  ["count" "refusals" "doses" "shortfall" "customers" "beneficiar" "units" "tonnes"
   "volume" "persons" "capacity" "members" "passed" "impacted" "workers" "covered"
   "premises" "cases" "issued"])

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
                 out (str "/tmp/wave13/w55_" (format "%02d" i) ".sql")]
             (write-text! out ddl)
             (println (str "wrote " out)))))))
