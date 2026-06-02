#!/usr/bin/env python3
"""Wave 22 bridges — mobility / UHC / AMR / indigenous rights / geoengineering."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "urban-mobility",
    "app": "urbanMobility",
    "methods": [
      {
        "name": "registerMaasRoute",
        "desc": "Mobility-as-a-Service multimodal route (bridges logistics-lastmile + datacenter + open-transit)",
        "fields": [
          ("routeId", "string", True),
          ("providerLei", "string", False),
          ("cityUnlocode", "string", True),
          ("modes", "string", True, None, "comma: bus,metro,rail,bike,scooter,carshare,ride,ferry"),
          ("originStopVid", "string", False),
          ("destStopVid", "string", False),
          ("avgTravelSec", "integer", False),
          ("priceUsd", "number", False),
          ("co2GPerTrip", "number", False),
          ("activatedAt", "string", True),
        ],
        "classify": ("sustainabilityTier", "if co2GPerTrip != null and co2GPerTrip <= 10 then \"zero_low\" else if co2GPerTrip != null and co2GPerTrip <= 50 then \"low_carbon\" else if co2GPerTrip != null and co2GPerTrip <= 150 then \"standard\" else \"high_carbon\"", ["zero_low","low_carbon","standard","high_carbon"]),
      },
      {
        "name": "reportDisruption",
        "desc": "Service disruption across MaaS modes (bridges disaster-response + cyber-incident)",
        "fields": [
          ("disruptionId", "string", True),
          ("routeVid", "string", True, None, "bridges registerMaasRoute"),
          ("mode", "string", True),
          ("cause", "string", True, ["weather","incident","cyber","strike","infra","demand_spike","political"]),
          ("severityMinutes", "integer", True),
          ("cyberIncidentVid", "string", False, None, "bridges open-cyber-incident"),
          ("reportedAt", "string", True),
        ],
        "classify": ("impactTier", "if severityMinutes >= 240 then \"major\" else if severityMinutes >= 60 then \"significant\" else \"minor\"", ["minor","significant","major"]),
      },
    ],
  },
  {
    "slug": "universal-health-coverage",
    "app": "universalHealthCoverage",
    "methods": [
      {
        "name": "reportUhcIndex",
        "desc": "WHO UHC Service Coverage Index (bridges pharma-supply + pandemic-preparedness + cofog)",
        "fields": [
          ("reportId", "string", True),
          ("countryIso3", "string", True),
          ("scoreValue", "integer", True, None, "UHC SCI 0-100"),
          ("financialProtectionScore", "integer", False),
          ("catastrophicExpenditurePct", "number", False),
          ("reportedYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("coverageTier", "if scoreValue >= 80 then \"advanced\" else if scoreValue >= 60 then \"developed\" else if scoreValue >= 40 then \"progressing\" else \"foundational\"", ["foundational","progressing","developed","advanced"]),
      },
      {
        "name": "recordEssentialMedicineAvailability",
        "desc": "WHO EML stock availability (bridges pharma-supply + atc)",
        "fields": [
          ("recordId", "string", True),
          ("reportVid", "string", True, None, "bridges reportUhcIndex"),
          ("atcCode", "string", True, None, "bridges open-atc"),
          ("productVid", "string", False, None, "bridges open-pharma-supply"),
          ("availabilityPct", "number", True, None, "% of facilities stocked"),
          ("stockoutDays", "integer", False),
          ("measuredYear", "integer", True),
        ],
        "classify": ("availabilityTier", "if availabilityPct >= 90 then \"high\" else if availabilityPct >= 60 then \"moderate\" else \"low\"", ["low","moderate","high"]),
      },
    ],
  },
  {
    "slug": "amr-surveillance",
    "app": "amrSurveillance",
    "methods": [
      {
        "name": "reportResistancePattern",
        "desc": "GLASS / EARS-Net / JANIS AMR pattern (bridges pandemic-preparedness + agri-food-security + pharma-supply)",
        "fields": [
          ("reportId", "string", True),
          ("pathogen", "string", True, None, "WHO priority pathogen"),
          ("antibiotic", "string", True, None, "AWaRe classification"),
          ("resistancePct", "number", True),
          ("specimenCount", "integer", True),
          ("jurisdictionIso3", "string", True),
          ("reportedYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("threatTier", "if resistancePct >= 50 then \"critical\" else if resistancePct >= 20 then \"high\" else if resistancePct >= 5 then \"elevated\" else \"background\"", ["background","elevated","high","critical"]),
      },
      {
        "name": "flagOneHealthSignal",
        "desc": "One Health AMR signal linking human/animal/env (WOAH + FAO + UNEP)",
        "fields": [
          ("signalId", "string", True),
          ("patternVid", "string", True, None, "bridges reportResistancePattern"),
          ("sectorsInvolved", "string", True, None, "comma: human,animal,food,water,soil,wildlife"),
          ("foodSecurityVid", "string", False, None, "bridges open-agri-food-security"),
          ("waterBasinVid", "string", False, None, "bridges open-water-scarcity"),
          ("flaggedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "indigenous-rights",
    "app": "indigenousRights",
    "methods": [
      {
        "name": "registerTerritory",
        "desc": "Indigenous territory registration (UNDRIP / ILO 169 — bridges mining + cultural-heritage + biodiversity-gbf)",
        "fields": [
          ("territoryId", "string", True),
          ("peopleName", "string", True),
          ("countryIso3", "string", True),
          ("areaHectares", "number", False),
          ("recognitionStatus", "string", True, ["titled","recognized_unregistered","claimed","overlap_protected","contested","unrecognized"]),
          ("legalInstrument", "string", False),
          ("miningOverlapVid", "string", False, None, "bridges open-mining-operation"),
          ("gbfProtectedVid", "string", False, None, "bridges open-biodiversity-gbf"),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFpicViolation",
        "desc": "Free Prior Informed Consent violation (bridges forced-labor + mining)",
        "fields": [
          ("violationId", "string", True),
          ("territoryVid", "string", True, None, "bridges registerTerritory"),
          ("actorLei", "string", False),
          ("violationType", "string", True, ["no_consultation","coerced_consent","misrepresentation","excluded_benefits","retaliation","forced_displacement"]),
          ("miningVid", "string", False, None, "bridges open-mining-operation"),
          ("forcedLaborVid", "string", False, None, "bridges open-forced-labor"),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if violationType = \"forced_displacement\" or violationType = \"coerced_consent\" then \"severe\" else if violationType = \"retaliation\" then \"strong\" else \"moderate\"", ["moderate","strong","severe"]),
      },
    ],
  },
  {
    "slug": "geoengineering-registry",
    "app": "geoengineeringRegistry",
    "methods": [
      {
        "name": "registerExperiment",
        "desc": "Geoengineering experiment registry (CDR + SRM — bridges climate-carbon-market + water-scarcity + biodiversity-gbf)",
        "fields": [
          ("experimentId", "string", True),
          ("operatorLei", "string", False),
          ("technologyClass", "string", True, ["SAI","MCB","CCT","OAF","DAC","BECCS","ERW","OIF","SAH","biochar","afforestation"]),
          ("locationIso3", "string", True),
          ("locationLat", "number", False),
          ("locationLon", "number", False),
          ("scaleTier", "string", False, ["lab","field_small","field_medium","field_large","commercial"]),
          ("expectedCo2eTonnes", "number", False),
          ("startedAt", "string", True),
          ("endsAt", "string", False),
        ],
        "classify": ("riskTier", "if technologyClass = \"SAI\" or technologyClass = \"MCB\" or technologyClass = \"OIF\" then \"planetary\" else if technologyClass = \"ERW\" or technologyClass = \"OAF\" then \"regional\" else \"local\"", ["local","regional","planetary"]),
      },
      {
        "name": "reportGovernanceGap",
        "desc": "Geoengineering governance gap (London Convention / CBD / UNEA moratoria)",
        "fields": [
          ("gapId", "string", True),
          ("experimentVid", "string", True, None, "bridges registerExperiment"),
          ("instrumentApplicable", "string", False, ["london_convention","cbd_moratorium","unea","unfccc","none"]),
          ("complianceStatus", "string", True, ["compliant","ambiguous","non_compliant","jurisdiction_gap"]),
          ("flaggedAt", "string", True),
        ],
        "classify": None,
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
