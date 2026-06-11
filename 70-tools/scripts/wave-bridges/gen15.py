#!/usr/bin/env python3
"""Wave 15 bridge actor generator — 5 actors × 2 NSIDs each.
Climate + AI governance + critical minerals + forced labor bridges.
"""
import json
from pathlib import Path

REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "climate-carbon-market",
    "app": "climateCarbonMarket",
    "methods": [
      {
        "name": "issueCarbonCredit",
        "desc": "Carbon credit issuance (EU ETS / CORSIA / VCM / ACCU bridges commodity-trade + esg-risk-rating + cofog)",
        "fields": [
          ("creditId", "string", True),
          ("registry", "string", True, ["EU_ETS","CORSIA","VCM_VERRA","VCM_GOLDSTANDARD","ACCU","CCA","KCS","CHINA_ETS"]),
          ("vintage", "string", True, None, "issuance year YYYY"),
          ("tonnesCo2e", "number", True),
          ("projectType", "string", False, ["forestry_redd","renewable_energy","methane_capture","direct_air_capture","blue_carbon","soil_sequestration","efficiency"]),
          ("projectLei", "string", False, None, "bridges open-lei"),
          ("cofogExpenditureVid", "string", False, None, "bridges open-cofog public env spend"),
          ("issuedAt", "string", True),
        ],
        "classify": ("qualityTier", "if registry = \"EU_ETS\" or registry = \"VCM_GOLDSTANDARD\" then \"tier_1\" else if registry = \"VCM_VERRA\" or registry = \"CORSIA\" then \"tier_2\" else \"tier_3\"", ["tier_1","tier_2","tier_3"]),
      },
      {
        "name": "retireCarbonCredit",
        "desc": "Credit retirement against commodity-trade settlement or esg compliance",
        "fields": [
          ("retirementId", "string", True),
          ("creditVid", "string", True, None, "bridges issueCarbonCredit"),
          ("retiredBy", "string", True, None, "LEI retiring entity"),
          ("settlementVid", "string", False, None, "bridges open-commodity-trade settleContract"),
          ("esgRatingVid", "string", False, None, "bridges open-esg-risk-rating"),
          ("purpose", "string", True, ["compliance","voluntary_neutrality","offset_product","insetting"]),
          ("retiredAt", "string", True),
        ],
        "classify": None,
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("credit_id","varchar",""),
      ("registry","varchar",""),
      ("vintage","varchar",""),
      ("tonnes_co2e","double precision",""),
      ("project_type","varchar",""),
      ("project_lei","varchar",""),
      ("cofog_expenditure_vid","varchar",""),
      ("issued_at","varchar",""),
      ("quality_tier","varchar",""),
      ("retirement_id","varchar",""),
      ("credit_vid","varchar",""),
      ("retired_by","varchar",""),
      ("settlement_vid","varchar",""),
      ("esg_rating_vid","varchar",""),
      ("purpose","varchar",""),
      ("retired_at","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
  {
    "slug": "arctic-nsr",
    "app": "arcticNsr",
    "methods": [
      {
        "name": "recordTransit",
        "desc": "Northern Sea Route / Northwest Passage transit (carrier-schedule + biosecurity + panama-transit bridge)",
        "fields": [
          ("transitId", "string", True),
          ("route", "string", True, ["NSR","NWP","TRANSPOLAR"]),
          ("imo", "string", True),
          ("carrierScheduleVid", "string", False, None, "bridges open-carrier-schedule"),
          ("biosecurityInspectionVid", "string", False, None, "bridges open-biosecurity"),
          ("iceClass", "string", False, ["PC1","PC2","PC3","PC4","PC5","PC6","PC7","IA_SUPER","IA","IB","IC"]),
          ("pilotAgencyLei", "string", False, None, "Atomflot / Transport Canada"),
          ("entryDate", "string", True),
          ("exitDate", "string", False),
          ("fuelTonnes", "number", False),
        ],
        "classify": ("feasibilityTier", "if iceClass = \"PC1\" or iceClass = \"PC2\" or iceClass = \"PC3\" then \"year_round\" else if iceClass = \"PC4\" or iceClass = \"PC5\" or iceClass = \"IA_SUPER\" then \"extended_season\" else \"summer_only\"", ["summer_only","extended_season","year_round"]),
      },
      {
        "name": "recordCommercialViability",
        "desc": "Per-transit commercial viability vs alternate (Suez / Panama / Cape)",
        "fields": [
          ("viabilityId", "string", True),
          ("transitVid", "string", True, None, "bridges recordTransit"),
          ("alternateRoute", "string", True, ["SUEZ","PANAMA","CAPE_HORN","CAPE_GOOD_HOPE"]),
          ("alternateTransitVid", "string", False, None, "bridges open-panama-transit / open-redsea-suez"),
          ("nsrDistanceNm", "number", False),
          ("alternateDistanceNm", "number", False),
          ("nsrCostUsd", "number", False),
          ("alternateCostUsd", "number", False),
          ("savingsPct", "number", False),
          ("assessedAt", "string", True),
        ],
        "classify": ("viabilityTier", "if savingsPct != null and savingsPct >= 30 then \"strongly_favored\" else if savingsPct != null and savingsPct >= 10 then \"marginal\" else \"uneconomic\"", ["uneconomic","marginal","strongly_favored"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("transit_id","varchar",""),
      ("route","varchar",""),
      ("imo","varchar",""),
      ("carrier_schedule_vid","varchar",""),
      ("biosecurity_inspection_vid","varchar",""),
      ("ice_class","varchar",""),
      ("pilot_agency_lei","varchar",""),
      ("entry_date","varchar",""),
      ("exit_date","varchar",""),
      ("fuel_tonnes","double precision",""),
      ("feasibility_tier","varchar",""),
      ("viability_id","varchar",""),
      ("transit_vid","varchar",""),
      ("alternate_route","varchar",""),
      ("alternate_transit_vid","varchar",""),
      ("nsr_distance_nm","double precision",""),
      ("alternate_distance_nm","double precision",""),
      ("nsr_cost_usd","double precision",""),
      ("alternate_cost_usd","double precision",""),
      ("savings_pct","double precision",""),
      ("assessed_at","varchar",""),
      ("viability_tier","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
  {
    "slug": "ai-governance",
    "app": "aiGovernance",
    "methods": [
      {
        "name": "registerModel",
        "desc": "AI model risk register (EU AI Act / NIST AI RMF / ISO 42001 — bridges cyber-compliance + esg-risk-rating + lei)",
        "fields": [
          ("modelId", "string", True),
          ("developerLei", "string", False, None, "bridges open-lei"),
          ("euAiActRiskClass", "string", True, ["minimal","limited","high","unacceptable","general_purpose"]),
          ("nistCategory", "string", False, ["narrow","foundation","agentic","gai"]),
          ("cyberComplianceVid", "string", False, None, "bridges open-cyber-compliance"),
          ("esgRatingVid", "string", False, None, "bridges open-esg-risk-rating"),
          ("trainingDatasetDisclosed", "boolean", False),
          ("registeredAt", "string", True),
        ],
        "classify": ("gateTier", "if euAiActRiskClass = \"unacceptable\" then \"banned\" else if euAiActRiskClass = \"high\" then \"conformity_assessment\" else if euAiActRiskClass = \"general_purpose\" then \"transparency_only\" else \"exempt\"", ["exempt","transparency_only","conformity_assessment","banned"]),
      },
      {
        "name": "reportIncident",
        "desc": "AI incident report (AIAAIC / deepfake attribution / bias / hallucination harm)",
        "fields": [
          ("incidentId", "string", True),
          ("modelVid", "string", False, None, "bridges registerModel"),
          ("incidentType", "string", True, ["deepfake","hallucination_harm","bias_discrimination","privacy_leak","ipr_infringement","autonomy_violation","physical_harm"]),
          ("reporterType", "string", True, ["self","regulator","journalist","ngo","user"]),
          ("jurisdictionIso3", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if incidentType = \"physical_harm\" or incidentType = \"autonomy_violation\" then \"critical\" else if incidentType = \"privacy_leak\" or incidentType = \"deepfake\" then \"severe\" else \"minor\"", ["minor","severe","critical"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("model_id","varchar",""),
      ("developer_lei","varchar",""),
      ("eu_ai_act_risk_class","varchar",""),
      ("nist_category","varchar",""),
      ("cyber_compliance_vid","varchar",""),
      ("esg_rating_vid","varchar",""),
      ("training_dataset_disclosed","boolean",""),
      ("registered_at","varchar",""),
      ("gate_tier","varchar",""),
      ("incident_id","varchar",""),
      ("model_vid","varchar",""),
      ("incident_type","varchar",""),
      ("reporter_type","varchar",""),
      ("jurisdiction_iso3","varchar",""),
      ("reported_at","varchar",""),
      ("severity_tier","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
  {
    "slug": "critical-minerals",
    "app": "criticalMinerals",
    "methods": [
      {
        "name": "classifyMaterial",
        "desc": "Critical raw material classification (USGS 2022 / EU CRMA / China / Japan — bridges open-hs + commodity-trade)",
        "fields": [
          ("classificationId", "string", True),
          ("hsCode", "string", True, None, "bridges open-hs"),
          ("materialName", "string", True),
          ("usgsCritical", "boolean", True, None, "USGS 2022 critical list"),
          ("euStrategic", "boolean", True, None, "EU CRMA 2023 strategic"),
          ("jpStockpiled", "boolean", False, None, "JOGMEC stockpile list"),
          ("chinaControlled", "boolean", False, None, "China export control"),
          ("primaryUseSector", "string", False, ["evs","semiconductors","defense","renewables","electronics","aerospace","medical"]),
          ("classifiedAt", "string", True),
        ],
        "classify": ("riskTier", "if usgsCritical = true and euStrategic = true and chinaControlled = true then \"extreme\" else if usgsCritical = true and euStrategic = true then \"high\" else if usgsCritical = true or euStrategic = true then \"moderate\" else \"low\"", ["low","moderate","high","extreme"]),
      },
      {
        "name": "recordConcentration",
        "desc": "Supply concentration metric (HHI) per material / origin country",
        "fields": [
          ("metricId", "string", True),
          ("classificationVid", "string", True, None, "bridges classifyMaterial"),
          ("topProducerIso3", "string", False),
          ("topProducerSharePct", "number", False),
          ("hhiIndex", "number", False, None, "Herfindahl-Hirschman Index 0-10000"),
          ("commodityTradeVid", "string", False, None, "bridges open-commodity-trade"),
          ("measuredYear", "integer", True),
        ],
        "classify": ("concentrationTier", "if hhiIndex != null and hhiIndex >= 5000 then \"monopoly_like\" else if hhiIndex != null and hhiIndex >= 2500 then \"concentrated\" else if hhiIndex != null and hhiIndex >= 1500 then \"moderately_concentrated\" else \"competitive\"", ["competitive","moderately_concentrated","concentrated","monopoly_like"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("classification_id","varchar",""),
      ("hs_code","varchar",""),
      ("material_name","varchar",""),
      ("usgs_critical","boolean",""),
      ("eu_strategic","boolean",""),
      ("jp_stockpiled","boolean",""),
      ("china_controlled","boolean",""),
      ("primary_use_sector","varchar",""),
      ("classified_at","varchar",""),
      ("risk_tier","varchar",""),
      ("metric_id","varchar",""),
      ("classification_vid","varchar",""),
      ("top_producer_iso3","varchar",""),
      ("top_producer_share_pct","double precision",""),
      ("hhi_index","double precision",""),
      ("commodity_trade_vid","varchar",""),
      ("measured_year","int",""),
      ("concentration_tier","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
  {
    "slug": "forced-labor",
    "app": "forcedLabor",
    "methods": [
      {
        "name": "flagIndicator",
        "desc": "ILO forced labor indicator / UFLPA entity listing (bridges crew-welfare + lei + sanctions + carrier-esg)",
        "fields": [
          ("flagId", "string", True),
          ("entityLei", "string", False, None, "bridges open-lei"),
          ("crewWelfareVid", "string", False, None, "bridges open-crew-welfare reportWelfareBreach"),
          ("carrierEsgVid", "string", False, None, "bridges open-carrier-esg"),
          ("sanctionsVid", "string", False, None, "bridges open-sanctions"),
          ("iloIndicator", "string", True, ["abuse_vulnerability","deception","restriction_movement","isolation","physical_sexual_violence","intimidation_threats","retention_identity_docs","withholding_wages","debt_bondage","abusive_working_conditions","excessive_overtime"]),
          ("jurisdictionIso3", "string", False),
          ("uflpaListed", "boolean", False),
          ("detectedAt", "string", True),
        ],
        "classify": ("severityTier", "if iloIndicator = \"physical_sexual_violence\" or iloIndicator = \"debt_bondage\" then \"severe\" else if iloIndicator = \"deception\" or iloIndicator = \"retention_identity_docs\" or iloIndicator = \"withholding_wages\" then \"strong\" else \"weak\"", ["weak","strong","severe"]),
      },
      {
        "name": "attestRemediation",
        "desc": "Remediation attestation (ILO Operational Guidelines / OECD Guidelines)",
        "fields": [
          ("attestationId", "string", True),
          ("flagVid", "string", True, None, "bridges flagIndicator"),
          ("remediationType", "string", True, ["wages_restored","documents_returned","worker_consulted","grievance_mechanism","third_party_audit","prosecution","workplace_closed"]),
          ("auditorLei", "string", False, None, "bridges open-lei"),
          ("effectivenessScore", "number", False, None, "0-100 scale"),
          ("attestedAt", "string", True),
        ],
        "classify": ("outcomeTier", "if effectivenessScore != null and effectivenessScore >= 80 then \"substantive\" else if effectivenessScore != null and effectivenessScore >= 40 then \"partial\" else \"nominal\"", ["nominal","partial","substantive"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("flag_id","varchar",""),
      ("entity_lei","varchar",""),
      ("crew_welfare_vid","varchar",""),
      ("carrier_esg_vid","varchar",""),
      ("sanctions_vid","varchar",""),
      ("ilo_indicator","varchar",""),
      ("jurisdiction_iso3","varchar",""),
      ("uflpa_listed","boolean",""),
      ("detected_at","varchar",""),
      ("severity_tier","varchar",""),
      ("attestation_id","varchar",""),
      ("flag_vid","varchar",""),
      ("remediation_type","varchar",""),
      ("auditor_lei","varchar",""),
      ("effectiveness_score","double precision",""),
      ("attested_at","varchar",""),
      ("outcome_tier","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
]


def snake(s):
    out = []
    for ch in s:
        if ch.isupper(): out.append("_"+ch.lower())
        else: out.append(ch)
    return "".join(out).lstrip("_")


def gen_lexicon(actor, method):
    nsid = f"com.etzhayyim.apps.{actor['app']}.{method['name']}"
    props = {}; required = []
    for f in method["fields"]:
        name, ftype, req = f[0], f[1], f[2]
        enum = f[3] if len(f)>3 else None
        desc = f[4] if len(f)>4 else None
        p = {"type": ftype}
        if enum: p["enum"] = enum
        if desc: p["description"] = desc
        if ftype == "string" and name.endswith("At"): p["format"] = "datetime"
        props[name] = p
        if req: required.append(name)
    out_props = {"ok":{"type":"boolean"},"vertexId":{"type":"string"},"instanceKey":{"type":"integer"},"error":{"type":"string"}}
    if method.get("classify"):
        col,_,enum = method["classify"]
        out_props[col] = {"type":"string","enum":enum}
    return {"lexicon":1,"id":nsid,"defs":{"main":{"type":"procedure","description":method["desc"],
        "input":{"encoding":"application/json","schema":{"type":"object","required":required,"properties":props}},
        "output":{"encoding":"application/json","schema":{"type":"object","properties":out_props}}}}}


def gen_bpmn(actor, method):
    slug = actor["slug"]
    table = f"vertex_open_{slug.replace('-','_')}"
    proc_id = f"open_{slug.replace('-','_')}_{snake(method['name'])}"
    action = f"open.{actor['app']}.{method['name']}"
    vparts = ["vertex_id: vertexId"]
    for f in method["fields"]:
        name = f[0]; col = snake(name)
        vparts.append(f"{col}: {name}")
    if method.get("classify"):
        col, expr, _ = method["classify"]
        # col is already snake_case in our definitions (or we ensure it is)
        snake_col = snake(col) if any(c.isupper() for c in col) else col
        vparts.append(f"{snake_col}: {expr}")
    vparts += ['status: "active"','created_at: string(now())','owner_did: callerDid','sensitivity_ord: 1','org_id: callerDid','user_id: callerDid',f'actor_id: "sys.bpmn.open-{slug}"']
    feel = "{" + ", ".join(vparts) + "}"
    xml_feel = feel.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_{proc_id}" targetNamespace="https://etzhayyim.com/bpmn/open-{slug}" exporter="hand-written" exporterVersion="1.0">
  <bpmn:process id="{proc_id}" name="{method['name']}" isExecutable="true">
    <bpmn:startEvent id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>
    <bpmn:serviceTask id="Task_Save" name="save">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;{table}&quot;" target="table"/><zeebe:input source="={xml_feel}" target="values"/><zeebe:input source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" targetRef="Task_Audit"/>
    <bpmn:serviceTask id="Task_Audit" name="audit">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;did:web:open-{slug}.etzhayyim.com&quot;" target="actor"/><zeebe:input source="=&quot;{action}&quot;" target="action"/><zeebe:input source="={{vertexId: vertexId}}" target="payload"/></zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>
    <bpmn:endEvent id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""


def gen_ddl(actor):
    slug = actor["slug"]; table = f"vertex_open_{slug.replace('-','_')}"
    cols = ",\n  ".join(f"{c[0]} {c[1]}{' '+c[2] if c[2] else ''}" for c in actor["table_cols"])
    return f"CREATE TABLE IF NOT EXISTS {table} (\n  {cols}\n);\n"


for a in ACTORS:
    bpmn_dir = REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    lex_dir = REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bpmn_dir.mkdir(parents=True, exist_ok=True); lex_dir.mkdir(parents=True, exist_ok=True)
    for m in a["methods"]:
        (lex_dir/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bpmn_dir/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    print(gen_ddl(a))
