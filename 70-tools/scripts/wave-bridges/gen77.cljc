;; ported from 70-tools/scripts/wave-bridges/gen77.py (unit_refactor stage 0)
;; Wave 77 — spyware-export / internet-shutdown / universal-design / treasury-stress / codex-standard.
;; Faithful 1:1 port of the Python source-of-truth. Self-contained (inlines its
;; own snake/JSON helpers, no sibling requires). Data is string-keyed; FEEL
;; classify expressions are kept verbatim as strings. This wave's build-ddl-cols
;; uses the integer->bigint heuristic (matching the .py, with this wave's larger
;; key list). The Python "__main__" demo (writes lexicon JSON + BPMN XML, writes
;; per-actor DDL to /tmp/wave13/w77_NN.sql) is ported behind #?(:clj ...).
(ns scripts.wave-bridges.gen77
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json]))
  #?(:clj (:import [java.io File])))

(def repo "/Users/junkawasaki/github/etzhayyim/root")

(def actors
  [{"slug" "spyware-export"
    "app" "spywareExport"
    "methods"
    [{"name" "recordExportLicense"
      "desc" "Commercial spyware / dual-use / Wassenaar export license (bridges pressFreedomIndex.flagDeclineFactor + ofac-sanctions-sdn + cyber-vuln-cve)"
      "fields"
      [["licenseId" "string" true]
       ["vendorLei" "string" false]
       ["productKind" "string" true ["nso_pegasus" "intellexa_predator" "cytrox" "candiru" "quadream" "hacking_team_legacy" "finfisher" "darkmatter" "paragon" "ring_zero" "macos_zero_click" "android_zero_click"]]
       ["exportCountryIso3" "string" true]
       ["importCountryIso3" "string" true]
       ["endUseCert" "string" false ["le_lawful_intercept" "national_security" "counter_terror" "counter_narcotics" "dual_use_civilian" "research" "ban_exceptions" "none"]]
       ["pressDeclineVid" "string" false nil "bridges pressFreedomIndex.flagDeclineFactor"]
       ["issuedAt" "string" true]]
      "classify" nil}
     {"name" "flagMisuse"
      "desc" "Spyware misuse / journalist target / HRD surveillance (bridges pressFreedomIndex.flagDeclineFactor + transnational-repression + civil-liability)"
      "fields"
      [["flagId" "string" true]
       ["licenseVid" "string" true nil "bridges recordExportLicense"]
       ["misuseKind" "string" true ["journalist_targeting" "hrd_surveillance" "dissident_targeting" "political_opponent" "pro_eu_russia_targeting" "diplomatic_staff" "government_official" "family_member" "spouse" "lawyer" "cross_border_targeting" "autonomous_community"]]
       ["reportedDetectionCount" "integer" false]
       ["reportedAt" "string" true]]
      "classify" nil}]}
   {"slug" "internet-shutdown"
    "app" "internetShutdown"
    "methods"
    [{"name" "recordShutdown"
      "desc" "Internet shutdown / blackout / throttling event (Access Now STOP / KeepItOn — bridges cellBroadcastAlert.flagDeliveryGap + press-freedom + press-finance-coercion)"
      "fields"
      [["shutdownId" "string" true]
       ["countryIso3" "string" true]
       ["shutdownKind" "string" true ["full_blackout" "partial_regional" "platform_specific" "throttling" "dns_blocking" "bgp_route_null" "mobile_suspend" "sms_only" "vpn_block" "tor_block" "bandwidth_cap" "peak_time_off"]]
       ["triggerKind" "string" true ["election" "protest" "exam_cheating" "religious_violence" "communal_riot" "military_ops" "state_security" "visit_diplomatic" "sports_event" "border_dispute"]]
       ["deliveryGapVid" "string" false nil "bridges cellBroadcastAlert.flagDeliveryGap"]
       ["hoursDark" "integer" false]
       ["beganAt" "string" true]]
      "classify" nil}
     {"name" "flagEconomicImpact"
      "desc" "Economic / social impact of shutdown (bridges cellBroadcastAlert.flagDeliveryGap + digital-public-infra + refugee-unhcr)"
      "fields"
      [["flagId" "string" true]
       ["shutdownVid" "string" true nil "bridges recordShutdown"]
       ["impactKind" "string" true ["gdp_loss_pct" "remittance_halt" "exam_disrupt" "medical_telemed" "banking_halt" "emergency_alerts_off" "schools_online_halt" "pandemic_info_halt" "agri_price_info" "msme_impact" "tourism_hit" "elections_affected"]]
       ["estBusdLoss" "number" false]
       ["reportedAt" "string" true]]
      "classify" nil}]}
   {"slug" "universal-design"
    "app" "universalDesign"
    "methods"
    [{"name" "recordStandard"
      "desc" "Universal Design / ISO 21542 / IDeA / OHB public building (bridges assistiveTechProcure.flagSupplyGap + crpd-disability + accessibility-wcag)"
      "fields"
      [["standardId" "string" true]
       ["region" "string" true ["global_iso" "us_ada_aba" "eu_fn_aabbes" "jp_tokubetsu" "kr_ud_act" "ca_bim_a17_1" "au_disability_act" "in_rpwd_act" "nor_ohba" "se_bb_16" "dk_tilgænge" "br_nbr_9050"]]
       ["designDomain" "string" true ["architectural" "product" "interior" "transport" "ict" "outdoor_urban" "housing" "education" "healthcare" "workplace" "cultural"]]
       ["supplyGapVid" "string" false nil "bridges assistiveTechProcure.flagSupplyGap"]
       ["releasedAt" "string" true]]
      "classify" nil}
     {"name" "flagImplementationShortfall"
      "desc" "Implementation shortfall / legacy building / accessibility retrofit (bridges assistiveTechProcure.flagSupplyGap + crpd-disability + land-tenure)"
      "fields"
      [["flagId" "string" true]
       ["standardVid" "string" true nil "bridges recordStandard"]
       ["shortfallKind" "string" true ["legacy_building" "retrofit_cost" "historic_bldg_exemption" "rural_budget" "public_transit_gap" "private_sector_uncovered" "accessible_housing_shortage" "wayfinding_absent" "enforcement_weak" "exemptions_abused" "certification_fraud"]]
       ["coverageRatePct" "number" false]
       ["reportedAt" "string" true]]
      "classify" nil}]}
   {"slug" "treasury-market-stress"
    "app" "treasuryMarketStress"
    "methods"
    [{"name" "recordStressEvent"
      "desc" "US Treasury market stress event / basis trade unwind (bridges marginCall.flagFailure + nbfi-stress + ccp-oversight)"
      "fields"
      [["eventId" "string" true]
       ["stressKind" "string" true ["basis_trade_unwind" "swap_spread_blow" "dash_for_cash" "on_run_off_run_widen" "srf_activation" "bond_liquidity_gap" "mbs_basis" "bid_ask_widen" "cbb_sofr_arm_spike" "atr_spike" "repo_mmt_spike"]]
       ["depthImpactLevel" "string" true ["tolerable" "elevated" "impaired" "crisis" "systemic"]]
       ["marginCallVid" "string" false nil "bridges marginCall.flagFailure"]
       ["detectedAt" "string" true]]
      "classify" nil}
     {"name" "flagFedIntervention"
      "desc" "Fed intervention / standing repo / emergency dealer lending (bridges marginCall.flagFailure + liquidity-facility + bank-resolution)"
      "fields"
      [["flagId" "string" true]
       ["eventVid" "string" true nil "bridges recordStressEvent"]
       ["interventionKind" "string" true ["srf" "pdcf_emergency" "open_market_purchases" "qe_restart" "dealer_lending" "term_auction" "money_market_guarantee" "fhl_expansion" "fima_repo" "swap_line_activation" "direct_lending_nbfi"]]
       ["notionalBusd" "number" false]
       ["reportedAt" "string" true]]
      "classify" nil}]}
   {"slug" "codex-standard"
    "app" "codexStandard"
    "methods"
    [{"name" "recordStandardAdoption"
      "desc" "Codex Alimentarius / CCGP / CCFAC standard adoption (bridges foodFraud.flagNetwork + residue-mrl + rasff-food-safety)"
      "fields"
      [["adoptionId" "string" true]
       ["committee" "string" true ["cac" "ccgp" "ccfac" "ccpr" "ccrvdf" "ccrol" "ccmas" "ccffp" "ccfh" "ccfl" "ccnfsdu" "ccgen" "ccsis" "ccasia" "ccafrica" "ccnea" "ccnasma" "cclac" "ccexec"]]
       ["standardKind" "string" true ["max_residue" "hygiene_practice" "labeling" "sampling" "contamination" "additives" "novel_food" "traceability" "authentication" "species_id" "allergen" "supplement"]]
       ["foodFraudVid" "string" false nil "bridges foodFraud.flagNetwork"]
       ["adoptedAt" "string" true]]
      "classify" nil}
     {"name" "flagNonHarmonization"
      "desc" "Non-harmonization / national deviation / transition period (bridges foodFraud.flagNetwork + wto-trade-cbam + rasff-food-safety)"
      "fields"
      [["flagId" "string" true]
       ["adoptionVid" "string" true nil "bridges recordStandardAdoption"]
       ["issueKind" "string" true ["stricter_national" "weaker_national" "transition_delay" "private_standard_super" "regional_divergence" "eu_vs_fda" "multi_sector_conflict" "jurisdiction_gap" "enforcement_divergence" "data_gap_lmics"]]
       ["affectedCountriesCount" "integer" false]
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
  ["size" "months" "years" "days" "count" "recommendations" "hours" "refusals" "doses"
   "shortfall" "customers" "beneficiar" "units" "tonnes" "volume" "persons" "population"
   "children" "excluded" "capacity" "members" "passed" "impacted" "workers" "covered"
   "premises" "cases" "issued" "barrels" "claimants" "corridors" "objects" "investigators"
   "sku" "complainants" "statutes" "casualties" "leaked" "tco2e" "affected" "notch" "bps"
   "pages" "sentence" "devices" "incidents" "countries" "detections" "dark"])

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
                 out (str "/tmp/wave13/w77_" (format "%02d" i) ".sql")]
             (write-text! out ddl)
             (println (str "wrote " out)))))))
