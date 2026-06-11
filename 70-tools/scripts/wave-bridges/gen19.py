#!/usr/bin/env python3
"""Wave 19 — telecom / semiconductor / piracy / aviation / disaster bridges."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "telecom-infra",
    "app": "telecomInfra",
    "methods": [
      {
        "name": "registerCable",
        "desc": "Undersea cable registry (TeleGeography — bridges cyber-compliance + carrier-esg)",
        "fields": [
          ("cableId", "string", True),
          ("cableName", "string", True),
          ("consortiumLei", "string", False),
          ("landingPointsIso3", "string", True, None, "comma-separated ISO 3166-1 alpha-3"),
          ("lengthKm", "number", False),
          ("designCapacityTbps", "number", False),
          ("rfsYear", "integer", False, None, "ready-for-service year"),
          ("status", "string", True, ["planned","under_construction","in_service","retired"]),
          ("registeredAt", "string", True),
        ],
        "classify": ("capacityTier", "if designCapacityTbps != null and designCapacityTbps >= 200 then \"mega\" else if designCapacityTbps != null and designCapacityTbps >= 50 then \"major\" else \"standard\"", ["standard","major","mega"]),
      },
      {
        "name": "flagCableFault",
        "desc": "Undersea cable fault / cut event (sanctions + cyber-incident bridge)",
        "fields": [
          ("faultId", "string", True),
          ("cableVid", "string", True, None, "bridges registerCable"),
          ("faultType", "string", True, ["anchor_drag","fishing","earthquake","landslide","sabotage_suspected","sabotage_confirmed","equipment"]),
          ("locationLat", "number", False),
          ("locationLon", "number", False),
          ("repairShipEta", "string", False),
          ("cyberIncidentVid", "string", False, None, "bridges open-cyber-incident if cyber-correlated"),
          ("detectedAt", "string", True),
        ],
        "classify": ("severityTier", "if faultType = \"sabotage_confirmed\" then \"state_sponsored\" else if faultType = \"sabotage_suspected\" then \"investigation\" else \"routine\"", ["routine","investigation","state_sponsored"]),
      },
    ],
  },
  {
    "slug": "semiconductor-fab",
    "app": "semiconductorFab",
    "methods": [
      {
        "name": "recordCapacity",
        "desc": "Semiconductor fab capacity (SEMI/TechInsights — bridges ai-supply-chain + critical-minerals + ustr-301)",
        "fields": [
          ("fabId", "string", True),
          ("operatorLei", "string", False),
          ("locationIso3", "string", True),
          ("processNodeNm", "integer", True, None, "3/4/5/7/10/14/22/28/65/180 nm"),
          ("waferSizeMm", "integer", True),
          ("monthlyCapacityWafers", "integer", False),
          ("primaryProducts", "string", False, ["logic","memory","analog","power","rf","foundry"]),
          ("euvLithographyCount", "integer", False),
          ("startupYear", "integer", False),
        ],
        "classify": ("nodeTier", "if processNodeNm <= 5 then \"leading\" else if processNodeNm <= 14 then \"advanced\" else if processNodeNm <= 65 then \"mature\" else \"legacy\"", ["legacy","mature","advanced","leading"]),
      },
      {
        "name": "flagAllocation",
        "desc": "Allocation window / shortage allocation (tariff + export-control bridge)",
        "fields": [
          ("allocationId", "string", True),
          ("fabVid", "string", True, None, "bridges recordCapacity"),
          ("customerLei", "string", False),
          ("productLine", "string", True),
          ("allocatedPct", "number", True, None, "% of requested"),
          ("waitWeeks", "integer", False),
          ("rootCause", "string", False, ["euv_constraint","rare_gas","substrate","packaging","ate","labor"]),
          ("ustrActionVid", "string", False, None, "bridges open-ustr-section-301"),
          ("mofcomControlVid", "string", False, None, "bridges open-mofcom-export-control"),
          ("flaggedAt", "string", True),
        ],
        "classify": ("scarcityTier", "if allocatedPct < 30 then \"severe\" else if allocatedPct < 60 then \"constrained\" else \"tight\"", ["tight","constrained","severe"]),
      },
    ],
  },
  {
    "slug": "maritime-piracy",
    "app": "maritimePiracy",
    "methods": [
      {
        "name": "reportAttack",
        "desc": "IMB PRC / UKMTO / MSCHOA piracy report (bridges carrier-fleet + ofac-sanctions + forced-labor)",
        "fields": [
          ("attackId", "string", True),
          ("imo", "string", False, None, "target vessel IMO"),
          ("carrierFleetVid", "string", False, None, "bridges open-carrier-fleet"),
          ("locationLat", "number", True),
          ("locationLon", "number", True),
          ("zone", "string", True, ["GoA","GoG","Malacca","SCS","Caribbean","Arabian_Sea","Somali_Basin","Nigeria_offshore"]),
          ("attackType", "string", True, ["boarding","hijacking","kidnap_for_ransom","armed_robbery","attempted","suspicious_approach"]),
          ("weaponsUsed", "boolean", False),
          ("crewTaken", "integer", False),
          ("ransomUsd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("threatTier", "if attackType = \"hijacking\" or attackType = \"kidnap_for_ransom\" then \"critical\" else if weaponsUsed = true then \"high\" else \"moderate\"", ["moderate","high","critical"]),
      },
      {
        "name": "issueTransitAdvisory",
        "desc": "High-risk area transit advisory (JWC / Lloyd's / IBF)",
        "fields": [
          ("advisoryId", "string", True),
          ("attackVid", "string", False, None, "bridges reportAttack"),
          ("zone", "string", True),
          ("issuer", "string", True, ["JWC","LLOYDS_JWC","IBF","UKMTO","MSCHOA","CMFATLANTA"]),
          ("warRiskPremiumPct", "number", False),
          ("recommendedTransit", "string", False, ["convoy","day_only","avoid","standard_bmp"]),
          ("effectiveFrom", "string", True),
          ("effectiveUntil", "string", False),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "aviation-safety",
    "app": "aviationSafety",
    "methods": [
      {
        "name": "recordIcaoAudit",
        "desc": "ICAO USOAP / IOSA / FAA IASA audit (bridges airplane + lei)",
        "fields": [
          ("auditId", "string", True),
          ("stateIso3", "string", True),
          ("operatorLei", "string", False),
          ("auditType", "string", True, ["USOAP","USOAP_CMA","IOSA","IASA","ICVM"]),
          ("effectiveImplementationPct", "number", False, None, "USOAP EI score 0-100"),
          ("significantSafetyConcern", "boolean", False, None, "USOAP SSC flag"),
          ("category1or2", "string", False, ["category_1","category_2"], "FAA IASA category"),
          ("conductedAt", "string", True),
        ],
        "classify": ("complianceTier", "if significantSafetyConcern = true or category1or2 = \"category_2\" then \"deficient\" else if effectiveImplementationPct != null and effectiveImplementationPct < 60 then \"improving\" else \"compliant\"", ["compliant","improving","deficient"]),
      },
      {
        "name": "reportAirprox",
        "desc": "Airprox / loss of separation report (bridges airplane + ai-governance if automation-related)",
        "fields": [
          ("airproxId", "string", True),
          ("flightVid", "string", False, None, "bridges open-airplane flight"),
          ("locationLat", "number", False),
          ("locationLon", "number", False),
          ("horizontalSepMeters", "number", False),
          ("verticalSepFeet", "number", False),
          ("riskClass", "string", True, ["A","B","C","D","E"]),
          ("automationRelated", "boolean", False),
          ("aiModelVid", "string", False, None, "bridges open-ai-governance if ML-ATC"),
          ("occurredAt", "string", True),
        ],
        "classify": ("severityTier", "if riskClass = \"A\" then \"serious_risk\" else if riskClass = \"B\" then \"safety_not_assured\" else \"no_risk\"", ["no_risk","safety_not_assured","serious_risk"]),
      },
    ],
  },
  {
    "slug": "disaster-response",
    "app": "disasterResponse",
    "methods": [
      {
        "name": "declareEmergency",
        "desc": "Sendai Framework / IFRC / GDACS declaration (bridges agri-food-security + water-scarcity + cofog)",
        "fields": [
          ("declarationId", "string", True),
          ("hazardType", "string", True, ["earthquake","tsunami","cyclone","flood","wildfire","drought","volcano","landslide","pandemic","industrial","nuclear","conflict"]),
          ("jurisdictionIso3", "string", True),
          ("gdacsLevel", "string", False, ["green","orange","red"]),
          ("estimatedAffected", "integer", False),
          ("estimatedDead", "integer", False),
          ("estimatedEconLossUsd", "number", False),
          ("declaredAt", "string", True),
        ],
        "classify": ("severityTier", "if gdacsLevel = \"red\" or (estimatedDead != null and estimatedDead >= 1000) then \"catastrophic\" else if gdacsLevel = \"orange\" or (estimatedDead != null and estimatedDead >= 100) then \"severe\" else \"moderate\"", ["moderate","severe","catastrophic"]),
      },
      {
        "name": "recordAppeal",
        "desc": "IFRC DREF / UN CERF appeal (bridges cofog + ofac-sanctions if conflict)",
        "fields": [
          ("appealId", "string", True),
          ("declarationVid", "string", True, None, "bridges declareEmergency"),
          ("mechanism", "string", True, ["IFRC_DREF","IFRC_EMERGENCY","UN_CERF","UN_FLASH","ECHO","BILATERAL"]),
          ("fundingRequestedUsd", "number", True),
          ("fundingReceivedUsd", "number", False),
          ("launchedAt", "string", True),
        ],
        "classify": ("coverageTier", "if fundingReceivedUsd != null and fundingRequestedUsd > 0 and (fundingReceivedUsd / fundingRequestedUsd) >= 0.8 then \"well_funded\" else if fundingReceivedUsd != null and fundingRequestedUsd > 0 and (fundingReceivedUsd / fundingRequestedUsd) >= 0.4 then \"partial\" else \"underfunded\"", ["underfunded","partial","well_funded"]),
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
