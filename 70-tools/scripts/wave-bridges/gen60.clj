;; ported from 70-tools/scripts/wave-bridges/gen60.py (unit_refactor stage 0)
;; Wave 60 — civil-liability / fpic-consent / beneficial-ownership / ECA / shadow-fleet-insurance.
(ns scripts.wave-bridges.gen60
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare repo snake build-ddl-cols gen-lexicon gen-bpmn gen-ddl)

;; TODO: port-failed unit REPO (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpx43ngqkt/scratch.clj:4:42: w)
;; REPO = Path("/Users/junkawasaki/github/etzhayyim/root")
;; ACTORS = [
;;   {
;;     "slug": "civil-liability",
;;     "app": "civilLiability",
;;     "methods": [
;;       {
;;         "name": "recordTortClaim",
;;         "desc": "Tort / class action / direct liability claim (bridges csdddDirective.flagDueDiligenceGap + climate-litigation + federal-court-docket)",
;;         "fields": [
;;           ("claimId", "string", True),
;;           ("defendantLei", "string", False),
;;           ("forum", "string", True, ["us_federal","us_state","uk_high_court","nl_rechtbank","fr_tribunal","de_oberlandesgericht","br_stf","ke_high_court","za_high_court","icj_icpc","arbitration_pcc"]),
;;           ("theoryOfHarm", "string", True, ["duty_of_care","breach_statutory","nuisance","climate_attribution","workplace_harm","supply_chain_complicity","environmental_damage","securities_class","consumer_deception","rico"]),
;;           ("dueDiligenceGapVid", "string", False, None, "bridges csdddDirective.flagDueDiligenceGap"),
;;           ("aggregateDamagesMusd", "number", False),
;;           ("filedAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;       {
;;         "name": "flagDispositiveRuling",
;;         "desc": "Standing / dismissal / class certification / summary judgment (bridges csdddDirective.flagDueDiligenceGap + federal-court-docket.flagInjunction)",
;;         "fields": [
;;           ("rulingId", "string", True),
;;           ("claimVid", "string", True, None, "bridges recordTortClaim"),
;;           ("rulingKind", "string", True, ["standing_denied","motion_to_dismiss_granted","class_certified","class_decertified","summary_judgment","settlement_approved","verdict_plaintiff","verdict_defendant","daubert_exclusion","forum_non_conveniens"]),
;;           ("totalDamagesMusd", "number", False),
;;           ("ruledAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;     ],
;;   },
;;   {
;;     "slug": "fpic-consent",
;;     "app": "fpicConsent",
;;     "methods": [
;;       {
;;         "name": "recordConsentEvent",
;;         "desc": "FPIC (Free Prior Informed Consent) / UNDRIP / ILO C169 event (bridges soyMoratorium.flagMoratoriumBreach + indigenous-rights + land-tenure)",
;;         "fields": [
;;           ("eventId", "string", True),
;;           ("communityName", "string", True),
;;           ("countryIso3", "string", True),
;;           ("projectType", "string", True, ["mining","oil_gas","hydro","wind","solar_utility","agribusiness","logging","reservoir","transmission_line","pipeline","rail_corridor","tourism_resort","carbon_credit","redd_plus","defense_installation"]),
;;           ("consentStage", "string", True, ["pre_consultation","agreement_reached","ongoing_process","refused","withdrawn","legal_challenge","not_sought"]),
;;           ("moratoriumBreachVid", "string", False, None, "bridges soyMoratorium.flagMoratoriumBreach"),
;;           ("reportedAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;       {
;;         "name": "flagFpicViolation",
;;         "desc": "FPIC violation / failure to obtain / coerced consent (bridges soyMoratorium.flagMoratoriumBreach + indigenous-rights + worker-grievance)",
;;         "fields": [
;;           ("flagId", "string", True),
;;           ("eventVid", "string", True, None, "bridges recordConsentEvent"),
;;           ("violationKind", "string", True, ["no_consultation","tokenistic","coerced","manipulated_info","representative_unrecognized","proceeded_without","divide_and_rule","compensation_inadequate","land_grabbing","threats_violence"]),
;;           ("affectedPersons", "integer", False),
;;           ("reportedAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;     ],
;;   },
;;   {
;;     "slug": "beneficial-ownership-registry",
;;     "app": "beneficialOwnership",
;;     "methods": [
;;       {
;;         "name": "recordUboFiling",
;;         "desc": "UBO register filing (5AMLD / 6AMLD / US CTA / UK PSC — bridges debarmentList.flagPhoenixEntity + ofac-sanctions-sdn + lei-ownership)",
;;         "fields": [
;;           ("filingId", "string", True),
;;           ("legalEntityLei", "string", False),
;;           ("registryKind", "string", True, ["eu_5amld","eu_6amld","us_cta_fincen","uk_psc","ca_cbca","au_dibo","nz_bo_act","sg_register","hk_scr","offshore_sos","fatf_guidance"]),
;;           ("uboShareholdingPct", "number", False),
;;           ("uboJurisdictionIso3", "string", False),
;;           ("uboPepFlag", "boolean", False, None, "PEP = politically exposed person"),
;;           ("phoenixEntityVid", "string", False, None, "bridges debarmentList.flagPhoenixEntity"),
;;           ("filedAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;       {
;;         "name": "flagUboDiscrepancy",
;;         "desc": "UBO discrepancy / nominee / trust layering (bridges debarmentList.flagPhoenixEntity + ofac-sanctions-sdn + aml)",
;;         "fields": [
;;           ("flagId", "string", True),
;;           ("filingVid", "string", True, None, "bridges recordUboFiling"),
;;           ("discrepancyKind", "string", True, ["registry_vs_bank_kyc","nominee_only","trust_layering","bearer_share","opaque_tier","threshold_avoidance","delayed_filing","blank_filing","circular_ownership","dual_resident"]),
;;           ("severityTier", "string", False, ["watch","elevated","high","sdn_match"]),
;;           ("reportedAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;     ],
;;   },
;;   {
;;     "slug": "export-credit-agency",
;;     "app": "exportCreditAgency",
;;     "methods": [
;;       {
;;         "name": "recordExposure",
;;         "desc": "ECA / Berne Union / OECD arrangement exposure (bridges sovereignGuarantee.flagCallEvent + sovereign-debt + just-transition)",
;;         "fields": [
;;           ("exposureId", "string", True),
;;           ("ecaKind", "string", True, ["us_exim","jbic","nexi","kexim","ksure","cexim","sinosure","sace_italy","euler_hermes","ukef","edc_canada","efic_australia","coface","berne_union"]),
;;           ("borrowerCountryIso3", "string", True),
;;           ("sectorKind", "string", True, ["oil_gas","coal","lng","nuclear","renewable","aerospace","defense","rail","shipping","agri","infrastructure","manufacturing","ict"]),
;;           ("exposureBusd", "number", True),
;;           ("guaranteeCallVid", "string", False, None, "bridges sovereignGuarantee.flagCallEvent"),
;;           ("approvedAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;       {
;;         "name": "flagClimateCarveout",
;;         "desc": "CETP / Glasgow Statement / fossil-fuel ECA phase-out breach (bridges sovereignGuarantee.flagCallEvent + climate-value-chain + just-transition)",
;;         "fields": [
;;           ("flagId", "string", True),
;;           ("exposureVid", "string", True, None, "bridges recordExposure"),
;;           ("breachKind", "string", True, ["cetp_fossil_support","glasgow_statement_breach","limited_exemption_abuse","upstream_gas_loophole","downstream_refinery","thermal_coal","domestic_only_carveout","technical_assistance_gap","misclassification"]),
;;           ("reportedAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;     ],
;;   },
;;   {
;;     "slug": "shadow-fleet-insurance",
;;     "app": "shadowFleetInsurance",
;;     "methods": [
;;       {
;;         "name": "recordCoverage",
;;         "desc": "P&I Club / Russian reinsurance / shadow-fleet insurance (bridges priceCapCoalition.flagCapBreach + aisDarkVessel + insurance-policy)",
;;         "fields": [
;;           ("coverageId", "string", True),
;;           ("vesselImo", "string", True),
;;           ("insurerLei", "string", False),
;;           ("insurerKind", "string", True, ["igpi_club","ingosstrakh","sogaz","chubb_russia_local","turkish_insurer","indian_insurer","uae_captive","unknown","self_insured","no_cover"]),
;;           ("reinsuranceChain", "string", False),
;;           ("capBreachVid", "string", False, None, "bridges priceCapCoalition.flagCapBreach"),
;;           ("effectiveAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;       {
;;         "name": "flagGapOrFraud",
;;         "desc": "Insurance gap / fraudulent certificate / spill financial responsibility (bridges priceCapCoalition.flagCapBreach + hormuz-warrisk-premium + oilspill-clc)",
;;         "fields": [
;;           ("flagId", "string", True),
;;           ("coverageVid", "string", True, None, "bridges recordCoverage"),
;;           ("issueKind", "string", True, ["no_cover_after_eu_ban","forged_certificate","nonresponsive_insurer","sanctioned_reinsurer","coverage_gap_sts","out_of_scope_spill","policy_mismatch","flag_state_uncooperative","bunker_convention_gap","clc_gap"]),
;;           ("estLiabilityBusd", "number", False),
;;           ("reportedAt", "string", True),
;;         ],
;;         "classify": None,
;;       },
;;     ],
;;   },
;; ]
(def repo nil) ;; TODO: port-failed const

;; TODO: port-failed unit snake (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpm5vewum8/scratch.clj:2:14: w)
;; def snake(s):
;;     out = []
;;     for ch in s:
;;         if ch.isupper(): out.append("_"+ch.lower())
;;         else: out.append(ch)
;;     return "".join(out).lstrip("_")
(defn snake [& _]
  (throw (ex-info "TODO: port-failed" {:from "snake"})))

;; TODO: port-failed unit build_ddl_cols (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpx783e8y5/scratch.clj:2:1: er)
;; def build_ddl_cols(methods):
;;     seen = {"vertex_id"}
;;     cols = [("vertex_id","varchar","PRIMARY KEY")]
;;     for m in methods:
;;         for f in m["fields"]:
;;             name = f[0]; ftype = f[1]
;;             col = snake(name)
;;             if col in seen: continue
;;             seen.add(col)
;;             if ftype == "integer" and any(k in col for k in ["count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels"]):
;;                 sql_t = "bigint"
;;             else:
;;                 sql_t = {"string":"varchar","integer":"int","number":"double precision","boolean":"boolean"}.get(ftype,"varchar")
;;             cols.append((col, sql_t, ""))
;;         if m.get("classify"):
;;             cname = m["classify"][0]
;;             col = snake(cname) if any(c.isupper() for c in cname) else cname
;;             if col not in seen:
;;                 seen.add(col); cols.append((col, "varchar", ""))
;;     for c in [("status","varchar",""),("created_at","varchar",""),("owner_did","varchar",""),("sensitivity_ord","int",""),("org_id","varchar",""),("user_id","varchar",""),("actor_id","varchar","")]:
;;         if c[0] not in seen:
;;             cols.append(c); seen.add(c[0])
;;     return cols
(defn build-ddl-cols [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_ddl_cols"})))

;; TODO: port-failed unit gen_lexicon (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpwq2m24eo/scratch.clj:2:1: er)
;; def gen_lexicon(actor, method):
;;     nsid = f"com.etzhayyim.apps.{actor['app']}.{method['name']}"
;;     props={}; required=[]
;;     for f in method["fields"]:
;;         name,ftype,req=f[0],f[1],f[2]
;;         enum=f[3] if len(f)>3 else None
;;         desc=f[4] if len(f)>4 else None
;;         p={"type":ftype}
;;         if enum: p["enum"]=enum
;;         if desc: p["description"]=desc
;;         if ftype=="string" and name.endswith("At"): p["format"]="datetime"
;;         props[name]=p
;;         if req: required.append(name)
;;     out_props={"ok":{"type":"boolean"},"vertexId":{"type":"string"},"instanceKey":{"type":"integer"},"error":{"type":"string"}}
;;     if method.get("classify"):
;;         col,_,enum=method["classify"]
;;         out_props[col]={"type":"string","enum":enum}
;;     return {"lexicon":1,"id":nsid,"defs":{"main":{"type":"procedure","description":method["desc"],
;;         "input":{"encoding":"application/json","schema":{"type":"object","required":required,"properties":props}},
;;         "output":{"encoding":"application/json","schema":{"type":"object","properties":out_props}}}}}
(defn gen-lexicon [& _]
  (throw (ex-info "TODO: port-failed" {:from "gen_lexicon"})))

;; TODO: port-failed unit gen_bpmn (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp0bq4d4q3/scratch.clj:3:8: er)
;; def gen_bpmn(actor, method):
;;     slug=actor["slug"]
;;     table=f"vertex_open_{slug.replace('-','_')}"
;;     proc_id=f"open_{slug.replace('-','_')}_{snake(method['name'])}"
;;     action=f"open.{actor['app']}.{method['name']}"
;;     vparts=["vertex_id: vertexId"]
;;     for f in method["fields"]:
;;         name=f[0]; col=snake(name)
;;         vparts.append(f"{col}: {name}")
;;     if method.get("classify"):
;;         col,expr,_=method["classify"]
;;         sc = snake(col) if any(c.isupper() for c in col) else col
;;         vparts.append(f"{sc}: {expr}")
;;     vparts+=['status: "active"','created_at: string(now())','owner_did: callerDid','sensitivity_ord: 1','org_id: callerDid','user_id: callerDid',f'actor_id: "sys.bpmn.open-{slug}"']
;;     feel="{"+", ".join(vparts)+"}"
;;     x=feel.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")
;;     return f"""<?xml version="1.0" encoding="UTF-8"?>
;; <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_{proc_id}" targetNamespace="https://etzhayyim.com/bpmn/open-{slug}" exporter="hand-written" exporterVersion="1.0">
;;   <bpmn:process id="{proc_id}" name="{method['name']}" isExecutable="true">
;;     <bpmn:startEvent id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>
;;     <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>
;;     <bpmn:serviceTask id="Task_Save" name="save">
;;       <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>
;;         <zeebe:ioMapping><zeebe:input source="=&quot;{table}&quot;" target="table"/><zeebe:input source="={x}" target="values"/><zeebe:input source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>
;;       </bpmn:extensionElements>
;;       <bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>
;;     </bpmn:serviceTask>
;;     <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" targetRef="Task_Audit"/>
;;     <bpmn:serviceTask id="Task_Audit" name="audit">
;;       <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>
;;         <zeebe:ioMapping><zeebe:input source="=&quot;did:web:open-{slug}.etzhayyim.com&quot;" target="actor"/><zeebe:input source="=&quot;{action}&quot;" target="action"/><zeebe:input source="={{vertexId: vertexId}}" target="payload"/></zeebe:ioMapping>
;;       </bpmn:extensionElements>
;;       <bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>
;;     </bpmn:serviceTask>
;;     <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>
;;     <bpmn:endEvent id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>
;;   </bpmn:process>
;; </bpmn:definitions>"""
(defn gen-bpmn [& _]
  (throw (ex-info "TODO: port-failed" {:from "gen_bpmn"})))

;; TODO: port-failed unit gen_ddl (assembled-lint error)
;; def gen_ddl(actor):
;;     slug=actor["slug"]; table=f"vertex_open_{slug.replace('-','_')}"
;;     cols=build_ddl_cols(actor["methods"])
;;     body=",\n  ".join(f"{c[0]} {c[1]}{' '+c[2] if c[2] else ''}" for c in cols)
;;     return f"CREATE TABLE IF NOT EXISTS {table} (\n  {body}\n);\n"
(defn gen-ddl [& _]
  (throw (ex-info "TODO: port-failed" {:from "gen_ddl"})))

