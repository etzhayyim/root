;; ported from 70-tools/scripts/wave-bridges/gen26.py (unit_refactor stage 0)
;; Wave 26 bridges — mental health / coastal / data broker / cyclone / esports.
;; Faithful 1:1 port of the Python source-of-truth. Self-contained (inlines its
;; own snake/JSON helpers, no sibling requires). Data is string-keyed; FEEL
;; classify expressions are kept verbatim as strings. The Python "__main__" demo
;; (filesystem writes of generated lexicon JSON + BPMN XML + DDL printout) is
;; ported behind #?(:clj ...) as `-main`.
(ns scripts.wave-bridges.gen26
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json]))
  #?(:clj (:import [java.io File])))

(def repo "/Users/junkawasaki/github/etzhayyim/root")

(def actors
  [{"slug" "mental-health-parity"
    "app" "mentalHealthParity"
    "methods"
    [{"name" "reportParityMetric"
      "desc" "WHO mhGAP + Atlas + MHPAEA / insurance parity metric (bridges universal-health-coverage + pharma-supply)"
      "fields"
      [["metricId" "string" true]
       ["jurisdictionIso3" "string" true]
       ["indicator" "string" true ["mh_budget_pct" "psychiatrists_per_100k" "beds_per_100k" "mh_workforce_density" "service_coverage_pct" "depression_coverage_pct" "psychosis_coverage_pct" "suicide_rate_100k"]]
       ["valueNumeric" "number" true]
       ["parityReference" "number" false nil "comparable physical-health metric"]
       ["reportingYear" "integer" true]
       ["reportedAt" "string" true]]
      "classify" ["gapTier" "if parityReference != null and valueNumeric < parityReference * 0.3 then \"severe\" else if parityReference != null and valueNumeric < parityReference * 0.6 then \"significant\" else \"approaching\"" ["approaching" "significant" "severe"]]}
     {"name" "flagCoverageDenial"
      "desc" "Insurance denial pattern (MHPAEA NQTL exam / EU health systems assessment)"
      "fields"
      [["denialId" "string" true]
       ["metricVid" "string" false nil "bridges reportParityMetric"]
       ["insurerLei" "string" false]
       ["nqtlCategory" "string" true ["prior_auth" "network_adequacy" "concurrent_review" "reimbursement_rate" "step_therapy" "tx_setting" "experimental_exclusion"]]
       ["appealsUpheldPct" "number" false]
       ["flaggedAt" "string" true]]
      "classify" nil}]}
   {"slug" "coastal-slr"
    "app" "coastalSlr"
    "methods"
    [{"name" "recordSlrMeasurement"
      "desc" "Sea-level / coastal erosion measurement (bridges climate-adaptation-finance + disaster-response + water-scarcity + biodiversity-gbf)"
      "fields"
      [["measurementId" "string" true]
       ["stationId" "string" true nil "PSMSL / GLOSS tide gauge ID"]
       ["countryIso3" "string" true]
       ["locationLat" "number" false]
       ["locationLon" "number" false]
       ["msMmPerYear" "number" false nil "mean sea-level trend mm/yr"]
       ["shorelineRetreatMm" "number" false nil "annual retreat"]
       ["reliabilityScore" "number" false]
       ["measuredYear" "integer" true]
       ["recordedAt" "string" true]]
      "classify" ["exposureTier" "if msMmPerYear != null and msMmPerYear >= 6 then \"extreme\" else if msMmPerYear != null and msMmPerYear >= 3.3 then \"high\" else if msMmPerYear != null and msMmPerYear >= 2 then \"moderate\" else \"low\"" ["low" "moderate" "high" "extreme"]]}
     {"name" "declareCoastalAdaptation"
      "desc" "Coastal protect / accommodate / retreat plan (bridges climate-adaptation-finance)"
      "fields"
      [["planId" "string" true]
       ["measurementVid" "string" false nil "bridges recordSlrMeasurement"]
       ["adaptationType" "string" true ["protect_hard" "protect_soft" "accommodate" "managed_retreat" "advance" "hybrid"]]
       ["financeProjectVid" "string" false nil "bridges open-climate-adaptation-finance"]
       ["budgetUsd" "number" false]
       ["timelineYears" "integer" false]
       ["housingUnitsAffected" "integer" false]
       ["declaredAt" "string" true]]
      "classify" nil}]}
   {"slug" "data-broker-registry"
    "app" "dataBrokerRegistry"
    "methods"
    [{"name" "registerBroker"
      "desc" "Data broker registration (CA CCPA / VT / TX / EU DGA — bridges cyber-compliance + antitrust-dma + misinformation-observatory)"
      "fields"
      [["brokerId" "string" true]
       ["brokerLei" "string" false]
       ["registrationJurisdiction" "string" true ["ca" "vt" "tx" "or" "eu_dga" "uk_gdpr" "kr_pipa" "sg_pdpa"]]
       ["dataCategories" "string" true nil "identifiers / commercial / biometric / geolocation / inference / health / children"]
       ["sourceTypes" "string" false nil "voter_reg / credit / public_records / scraped / loyalty / location"]
       ["sellsChildrenData" "boolean" false]
       ["optOutMechanism" "string" false ["global_privacy_control" "individual_request" "sectoral" "none"]]
       ["registeredAt" "string" true]]
      "classify" ["riskTier" "if sellsChildrenData = true then \"severe\" else if optOutMechanism = \"none\" then \"high\" else if optOutMechanism = \"individual_request\" then \"moderate\" else \"low\"" ["low" "moderate" "high" "severe"]]}
     {"name" "flagEnforcement"
      "desc" "Data broker enforcement action (CPPA / CFPB / FTC / EDPB)"
      "fields"
      [["actionId" "string" true]
       ["brokerVid" "string" true nil "bridges registerBroker"]
       ["enforcer" "string" true ["cppa" "cfpb" "ftc" "edpb" "doj" "state_ag" "dma_compliance"]]
       ["violation" "string" true]
       ["fineUsd" "number" false]
       ["remedyRequired" "string" false]
       ["actedAt" "string" true]]
      "classify" nil}]}
   {"slug" "cyclone-prepo"
    "app" "cyclonePrepo"
    "methods"
    [{"name" "issueForecast"
      "desc" "Tropical cyclone forecast (JTWC / RSMC / NOAA NHC — bridges disaster-response + agri-food-security + refugee-unhcr)"
      "fields"
      [["forecastId" "string" true]
       ["stormId" "string" true nil "JTWC / RSMC storm ID"]
       ["basin" "string" true ["NATL" "EPAC" "CPAC" "WPAC" "NIO" "SIO" "SPAC" "AUS"]]
       ["issuer" "string" true ["nhc" "jtwc" "jma" "rsmc_lre" "imd" "bom" "fiji_rsmc" "mauritius_rsmc"]]
       ["saffirSimpsonCategory" "integer" false nil "1-5"]
       ["maxWindKmh" "number" false]
       ["estimatedLandfallIso3" "string" false]
       ["forecastValidUtc" "string" true]
       ["issuedAt" "string" true]]
      "classify" ["intensityTier" "if saffirSimpsonCategory != null and saffirSimpsonCategory >= 4 then \"major\" else if saffirSimpsonCategory != null and saffirSimpsonCategory >= 1 then \"hurricane\" else \"tropical_storm\"" ["tropical_storm" "hurricane" "major"]]}
     {"name" "logPrePositioning"
      "desc" "Pre-positioning of relief supplies (OCHA / IFRC / USAID BHA)"
      "fields"
      [["logId" "string" true]
       ["forecastVid" "string" true nil "bridges issueForecast"]
       ["operatorLei" "string" false]
       ["supplyCategory" "string" true ["wash" "shelter" "food" "medical" "power" "telecom" "fuel"]]
       ["unitsDeployed" "integer" true]
       ["stagingPortVid" "string" false nil "bridges open-ports"]
       ["recordedAt" "string" true]]
      "classify" nil}]}
   {"slug" "esports-integrity"
    "app" "esportsIntegrity"
    "methods"
    [{"name" "logCompetition"
      "desc" "Esports / online gambling competition registry (bridges election-integrity + antitrust-dma + misinformation-observatory)"
      "fields"
      [["competitionId" "string" true]
       ["title" "string" true]
       ["sanctioningBody" "string" true ["esic" "iso" "iesf" "nba2kl" "olympic" "riot_games" "blizzard" "faceit"]]
       ["prizePoolUsd" "number" false]
       ["stateIso3" "string" true]
       ["bettingMarketLei" "string" false]
       ["startedAt" "string" true]
       ["endedAt" "string" false]]
      "classify" nil}
     {"name" "flagIntegrityIncident"
      "desc" "Match-fixing / doping / DDoS / smurfing / AI-assist incident"
      "fields"
      [["incidentId" "string" true]
       ["competitionVid" "string" true nil "bridges logCompetition"]
       ["incidentType" "string" true ["match_fixing" "doping" "ddos" "account_sharing" "ai_assist" "smurfing" "collusion" "sponsor_breach"]]
       ["playerHandle" "string" false]
       ["aiModelVid" "string" false nil "bridges open-ai-governance"]
       ["investigationStatus" "string" false ["alleged" "confirmed" "dismissed" "pending"]]
       ["reportedAt" "string" true]]
      "classify" ["severityTier" "if incidentType = \"match_fixing\" or incidentType = \"ai_assist\" then \"critical\" else if incidentType = \"ddos\" or incidentType = \"collusion\" then \"severe\" else \"moderate\"" ["moderate" "severe" "critical"]]}]}])

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
    ;; lstrip("_")
    (str/replace out #"^_+" "")))

(def ^:private sql-type-map
  {"string" "varchar" "integer" "int" "number" "double precision" "boolean" "boolean"})

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
                    (let [sql-t (get sql-type-map ftype "varchar")]
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
      ;; trailing fixed columns
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
     (doseq [a actors]
         (let [bd (str repo "/00-contracts/bpmn/com/etzhayyim/open-" (get a "slug"))
               ld (str repo "/00-contracts/lexicons/com/etzhayyim/apps/" (get a "app"))]
           (.mkdirs (File. bd))
           (.mkdirs (File. ld))
           (doseq [m (get a "methods")]
             (write-text! (str ld "/" (get m "name") ".json")
                          (json/generate-string (gen-lexicon a m) {:pretty true}))
             (write-text! (str bd "/" (get m "name") ".bpmn")
                          (gen-bpmn a m)))
           (println (gen-ddl a))))))
