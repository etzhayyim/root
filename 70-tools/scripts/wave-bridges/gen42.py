#!/usr/bin/env python3
"""Wave 42 bridges — WEEE / academic / USCIRF / REIT / digital twin."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "weee-ewaste",
    "app": "weeeEwaste",
    "methods": [
      {
        "name": "recordFlow",
        "desc": "WEEE / Basel Annex IX e-waste flow (bridges chemicals-management + battery-passport + food-waste-epr + right-to-repair)",
        "fields": [
          ("flowId", "string", True),
          ("originIso3", "string", True),
          ("destinationIso3", "string", True),
          ("weeeCategory", "string", True, ["temperature_exchange","screens_monitors","lamps","large_equipment","small_equipment","small_it_telecom","photovoltaic"]),
          ("tonnes", "number", True),
          ("recyclingProcess", "string", False, ["mechanical_shredder","pyrometallurgy","hydrometallurgy","bioleaching","manual_dismantle","informal"]),
          ("recoveryRatePct", "number", False),
          ("priorInformedConsent", "boolean", False),
          ("shippedAt", "string", True),
        ],
        "classify": ("complianceTier", "if priorInformedConsent = false and recyclingProcess = \"informal\" then \"illegal\" else if recyclingProcess = \"informal\" then \"informal\" else \"regulated\"", ["regulated","informal","illegal"]),
      },
      {
        "name": "flagCriticalMineralRecovery",
        "desc": "Critical mineral recovery yield (bridges critical-minerals + battery-passport + mining-operation)",
        "fields": [
          ("recoveryId", "string", True),
          ("flowVid", "string", True, None, "bridges recordFlow"),
          ("criticalMineralVid", "string", False, None, "bridges open-critical-minerals"),
          ("element", "string", True, ["gold","silver","copper","cobalt","lithium","nickel","palladium","platinum","rare_earth","indium","tantalum"]),
          ("yieldKg", "number", True),
          ("purityPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "academic-integrity",
    "app": "academicIntegrity",
    "methods": [
      {
        "name": "recordMisconductCase",
        "desc": "Research misconduct case (ORI / UKRIO / JSPS — bridges ai-governance + precision-medicine + misinformation-observatory + press-freedom)",
        "fields": [
          ("caseId", "string", True),
          ("subjectOrcid", "string", False),
          ("institutionLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("misconductKind", "string", True, ["fabrication","falsification","plagiarism","image_manipulation","ai_undisclosed","authorship_abuse","peer_review_manipulation","data_retention_failure","ethics_violation"]),
          ("investigationStage", "string", True, ["inquiry","investigation","finding","appeal","closed"]),
          ("retractionsCount", "integer", False),
          ("openedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRetractionWatch",
        "desc": "Retraction Watch / PubPeer post-publication concern (bridges oss-vuln + precision-medicine + pharma-supply)",
        "fields": [
          ("concernId", "string", True),
          ("caseVid", "string", False, None, "bridges recordMisconductCase"),
          ("publicationDoi", "string", True),
          ("journalIssn", "string", False),
          ("concernKind", "string", True, ["duplicate_publication","image_manipulation","statistical_error","undisclosed_conflict","paper_mill","tortured_phrase","self_plagiarism"]),
          ("citesSincePublication", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if concernKind = \"paper_mill\" or concernKind = \"image_manipulation\" then \"critical\" else if concernKind = \"statistical_error\" or concernKind = \"tortured_phrase\" then \"significant\" else \"minor\"", ["minor","significant","critical"]),
      },
    ],
  },
  {
    "slug": "religious-freedom",
    "app": "religiousFreedom",
    "methods": [
      {
        "name": "recordRegistry",
        "desc": "USCIRF / Pew / Open Doors religious freedom registry (bridges press-freedom + refugee-unhcr + indigenous-rights)",
        "fields": [
          ("recordId", "string", True),
          ("countryIso3", "string", True),
          ("designation", "string", True, ["cpc","special_watch","swl","entity_of_particular_concern","not_designated"]),
          ("indexProvider", "string", True, ["uscirf","pew_rrli","pew_ggi","open_doors_wwl","religiopolitix"]),
          ("scoreValue", "number", False),
          ("cursorYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("restrictionTier", "if designation = \"cpc\" or designation = \"entity_of_particular_concern\" then \"severe\" else if designation = \"special_watch\" or designation = \"swl\" then \"significant\" else \"monitor\"", ["monitor","significant","severe"]),
      },
      {
        "name": "flagPersecutionEvent",
        "desc": "Persecution event / attack / closure (bridges press-freedom + forced-labor + refugee-unhcr)",
        "fields": [
          ("eventId", "string", True),
          ("recordVid", "string", False, None, "bridges recordRegistry"),
          ("targetGroup", "string", True),
          ("eventKind", "string", True, ["attack","arrest","closure","property_destruction","restriction_worship","conversion_ban","blasphemy_prosecution","genocide_allegation"]),
          ("victimCount", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if eventKind = \"genocide_allegation\" or eventKind = \"attack\" then \"critical\" else if eventKind = \"arrest\" or eventKind = \"blasphemy_prosecution\" then \"severe\" else \"serious\"", ["serious","severe","critical"]),
      },
    ],
  },
  {
    "slug": "reit-transparency",
    "app": "reitTransparency",
    "methods": [
      {
        "name": "recordPortfolioDisclosure",
        "desc": "REIT portfolio disclosure (EPRA / NAREIT / Japan J-REIT — bridges esg-risk-rating + climate-adaptation-finance + coastal-slr)",
        "fields": [
          ("disclosureId", "string", True),
          ("reitLei", "string", False),
          ("listingJurisdictionIso3", "string", True),
          ("reportingStandard", "string", True, ["epra_sbpr","nareit","iffas","jreit","glio"]),
          ("assetsUnderMgmtUsd", "number", True),
          ("propertyTypeBreakdown", "string", False, None, "comma: office,residential,retail,industrial,hotel,data_center,healthcare,logistics,life_science"),
          ("energyIntensityKwhM2Y", "number", False),
          ("scope1To3Tco2e", "number", False),
          ("submittedAt", "string", True),
        ],
        "classify": ("scaleTier", "if assetsUnderMgmtUsd >= 50000000000 then \"mega\" else if assetsUnderMgmtUsd >= 10000000000 then \"large\" else if assetsUnderMgmtUsd >= 1000000000 then \"mid\" else \"small\"", ["small","mid","large","mega"]),
      },
      {
        "name": "flagClimateStress",
        "desc": "Physical / transition climate risk stress test (bridges coastal-slr + urban-heat + extreme-weather-attribution + cat-bond-ils)",
        "fields": [
          ("stressId", "string", True),
          ("disclosureVid", "string", True, None, "bridges recordPortfolioDisclosure"),
          ("scenario", "string", True, ["ngfs_net_zero","ngfs_delayed","ngfs_current","iea_sds","iea_steps","physical_rcp26","physical_rcp45","physical_rcp85"]),
          ("impactedAssetsPct", "number", False),
          ("valueAtRiskUsd", "number", False),
          ("analyzedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "digital-twin-city",
    "app": "digitalTwinCity",
    "methods": [
      {
        "name": "registerCityTwin",
        "desc": "Smart-city digital twin (NIST SCF / ISO 37120 / ETSI OCF — bridges urban-heat + urban-mobility + coastal-slr + otel-observability)",
        "fields": [
          ("twinId", "string", True),
          ("operatorLei", "string", False),
          ("cityUnlocode", "string", True),
          ("standard", "string", True, ["nist_scf","iso_37120","etsi_ocf","city_protocol","ogc_city_gml"]),
          ("scopeDomains", "string", False, None, "comma: energy,water,mobility,buildings,environment,public_safety,waste,health"),
          ("dataSovereigntyModel", "string", False, ["municipal","national","federated","vendor_locked","open_data_trust"]),
          ("sensorCount", "integer", False),
          ("commissionedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordResilienceDrill",
        "desc": "Resilience drill / scenario simulation (bridges disaster-response + cyclone-prepo + extreme-weather-attribution)",
        "fields": [
          ("drillId", "string", True),
          ("twinVid", "string", True, None, "bridges registerCityTwin"),
          ("scenario", "string", True, ["flood","heat_dome","cyberattack","power_outage","pandemic","earthquake","supply_disruption","mass_gathering"]),
          ("simulatedDurationHours", "number", False),
          ("failureCascadeCount", "integer", False),
          ("recoveryTargetHours", "number", False),
          ("executedAt", "string", True),
        ],
        "classify": ("preparednessTier", "if recoveryTargetHours != null and recoveryTargetHours <= 4 then \"high\" else if recoveryTargetHours != null and recoveryTargetHours <= 24 then \"moderate\" else \"low\"", ["low","moderate","high"]),
      },
    ],
  },
]


def snake(s):
    out = []
    for ch in s:
        if ch.isupper(): out.append("_"+ch.lower())
        else: out.append(ch)
    return "".join(out).lstrip("_")


def build_ddl_cols(methods):
    seen = {"vertex_id"}
    cols = [("vertex_id","varchar","PRIMARY KEY")]
    for m in methods:
        for f in m["fields"]:
            name = f[0]; ftype = f[1]
            col = snake(name)
            if col in seen: continue
            seen.add(col)
            sql_t = {"string":"varchar","integer":"int","number":"double precision","boolean":"boolean"}.get(ftype,"varchar")
            cols.append((col, sql_t, ""))
        if m.get("classify"):
            cname = m["classify"][0]
            col = snake(cname) if any(c.isupper() for c in cname) else cname
            if col not in seen:
                seen.add(col); cols.append((col, "varchar", ""))
    for c in [("status","varchar",""),("created_at","varchar",""),("owner_did","varchar",""),("sensitivity_ord","int",""),("org_id","varchar",""),("user_id","varchar",""),("actor_id","varchar","")]:
        if c[0] not in seen:
            cols.append(c); seen.add(c[0])
    return cols


def gen_lexicon(actor, method):
    nsid = f"com.etzhayyim.apps.{actor['app']}.{method['name']}"
    props={}; required=[]
    for f in method["fields"]:
        name,ftype,req=f[0],f[1],f[2]
        enum=f[3] if len(f)>3 else None
        desc=f[4] if len(f)>4 else None
        p={"type":ftype}
        if enum: p["enum"]=enum
        if desc: p["description"]=desc
        if ftype=="string" and name.endswith("At"): p["format"]="datetime"
        props[name]=p
        if req: required.append(name)
    out_props={"ok":{"type":"boolean"},"vertexId":{"type":"string"},"instanceKey":{"type":"integer"},"error":{"type":"string"}}
    if method.get("classify"):
        col,_,enum=method["classify"]
        out_props[col]={"type":"string","enum":enum}
    return {"lexicon":1,"id":nsid,"defs":{"main":{"type":"procedure","description":method["desc"],
        "input":{"encoding":"application/json","schema":{"type":"object","required":required,"properties":props}},
        "output":{"encoding":"application/json","schema":{"type":"object","properties":out_props}}}}}


def gen_bpmn(actor, method):
    slug=actor["slug"]
    table=f"vertex_open_{slug.replace('-','_')}"
    proc_id=f"open_{slug.replace('-','_')}_{snake(method['name'])}"
    action=f"open.{actor['app']}.{method['name']}"
    vparts=["vertex_id: vertexId"]
    for f in method["fields"]:
        name=f[0]; col=snake(name)
        vparts.append(f"{col}: {name}")
    if method.get("classify"):
        col,expr,_=method["classify"]
        sc = snake(col) if any(c.isupper() for c in col) else col
        vparts.append(f"{sc}: {expr}")
    vparts+=['status: "active"','created_at: string(now())','owner_did: callerDid','sensitivity_ord: 1','org_id: callerDid','user_id: callerDid',f'actor_id: "sys.bpmn.open-{slug}"']
    feel="{"+", ".join(vparts)+"}"
    x=feel.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_{proc_id}" targetNamespace="https://etzhayyim.com/bpmn/open-{slug}" exporter="hand-written" exporterVersion="1.0">
  <bpmn:process id="{proc_id}" name="{method['name']}" isExecutable="true">
    <bpmn:startEvent id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>
    <bpmn:serviceTask id="Task_Save" name="save">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;{table}&quot;" target="table"/><zeebe:input source="={x}" target="values"/><zeebe:input source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>
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
    slug=actor["slug"]; table=f"vertex_open_{slug.replace('-','_')}"
    cols=build_ddl_cols(actor["methods"])
    body=",\n  ".join(f"{c[0]} {c[1]}{' '+c[2] if c[2] else ''}" for c in cols)
    return f"CREATE TABLE IF NOT EXISTS {table} (\n  {body}\n);\n"


for a in ACTORS:
    bd=REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    ld=REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bd.mkdir(parents=True,exist_ok=True); ld.mkdir(parents=True,exist_ok=True)
    for m in a["methods"]:
        (ld/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bd/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    print(gen_ddl(a))
