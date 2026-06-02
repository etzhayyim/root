#!/usr/bin/env python3
"""Wave 29 bridges — DORA/NIS2 / ocean acid / UPU / disarmament / air quality."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "cyber-resilience-stress",
    "app": "cyberResilienceStress",
    "methods": [
      {
        "name": "recordStressTest",
        "desc": "DORA TLPT / NIS2 / CROE / TIBER-EU penetration test (bridges cyber-compliance + banking + antitrust-dma)",
        "fields": [
          ("testId", "string", True),
          ("entityLei", "string", False),
          ("regime", "string", True, ["dora_tlpt","nis2","tiber_eu","croe","cbest","apra_cps234","nydfs_part500"]),
          ("entityCategory", "string", True, ["bank_significant","ccp","exchange","cii","ict_third_party","cloud","crypto_casp"]),
          ("testType", "string", True, ["threat_led","red_team","tabletop","vulnerability_assessment","business_continuity"]),
          ("providerLei", "string", False),
          ("scenariosExecuted", "integer", False),
          ("completedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "reportResilienceGap",
        "desc": "Resilience gap finding (bridges cyber-incident + quantum-safe-crypto)",
        "fields": [
          ("gapId", "string", True),
          ("testVid", "string", True, None, "bridges recordStressTest"),
          ("gapCategory", "string", True, ["detection","containment","recovery","communication","third_party","identity","cryptographic"]),
          ("severity", "string", True, ["low","medium","high","critical"]),
          ("mitigationDueAt", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("rpoRtoTier", "if severity = \"critical\" then \"rpo_zero\" else if severity = \"high\" then \"rto_same_day\" else \"rto_flexible\"", ["rto_flexible","rto_same_day","rpo_zero"]),
      },
    ],
  },
  {
    "slug": "ocean-acidification",
    "app": "oceanAcidification",
    "methods": [
      {
        "name": "recordPhMeasurement",
        "desc": "OA-ICC / SDG 14.3 pH measurement (bridges biodiversity-gbf + fisheries-iuu + coastal-slr)",
        "fields": [
          ("measurementId", "string", True),
          ("stationId", "string", True),
          ("regionM49", "string", True),
          ("latitude", "number", False),
          ("longitude", "number", False),
          ("totalPh", "number", True),
          ("omegaAragonite", "number", False),
          ("temperatureC", "number", False),
          ("salinityPsu", "number", False),
          ("methodQualityFlag", "string", False, ["climate","weather","regional"]),
          ("measuredAt", "string", True),
        ],
        "classify": ("acidityTier", "if totalPh < 7.8 then \"critical\" else if totalPh < 8.0 then \"elevated\" else \"ambient\"", ["ambient","elevated","critical"]),
      },
      {
        "name": "flagCalcifierStress",
        "desc": "Calcifier stress signal (shellfish / coral / pteropod — bridges fisheries-iuu + agri-food-security)",
        "fields": [
          ("signalId", "string", True),
          ("measurementVid", "string", True, None, "bridges recordPhMeasurement"),
          ("organismGroup", "string", True, ["corals","molluscs","echinoderms","crustaceans","foraminifera","coralline_algae","pteropods"]),
          ("mortalityPct", "number", False),
          ("hatcheryImpactDescription", "string", False),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "postal-union",
    "app": "postalUnion",
    "methods": [
      {
        "name": "recordUpuFlow",
        "desc": "UPU cross-border postal flow (bridges logistics-lastmile + customs-clearance + tariff)",
        "fields": [
          ("flowId", "string", True),
          ("originIso3", "string", True),
          ("destinationIso3", "string", True),
          ("serviceClass", "string", True, ["letter","parcel","ems","registered","printed_paper","m_bag"]),
          ("itemCount", "integer", True),
          ("weightKg", "number", False),
          ("averageDeliveryDays", "number", False),
          ("terminalDuesUsd", "number", False),
          ("periodMonth", "string", True),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagIpRights",
        "desc": "UPU S-series misuse / counterfeit mail flag",
        "fields": [
          ("flagId", "string", True),
          ("flowVid", "string", True, None, "bridges recordUpuFlow"),
          ("issueType", "string", True, ["counterfeit","prohibited","dangerous","narcotics","weapons","stamp_fraud","forged_documents"]),
          ("customsDeclarationVid", "string", False, None, "bridges open-customs-clearance"),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if issueType = \"weapons\" or issueType = \"narcotics\" or issueType = \"dangerous\" then \"critical\" else if issueType = \"counterfeit\" or issueType = \"forged_documents\" then \"severe\" else \"moderate\"", ["moderate","severe","critical"]),
      },
    ],
  },
  {
    "slug": "disarmament-treaties",
    "app": "disarmamentTreaties",
    "methods": [
      {
        "name": "recordTreatyStatus",
        "desc": "NPT / CWC / BWC / CCM / CCW / APMBC / ATT / TPNW status (bridges iaea-safeguards + ofac-sanctions)",
        "fields": [
          ("statusId", "string", True),
          ("treaty", "string", True, ["npt","cwc","bwc","ccm","ccw","apmbc","att","tpnw","new_start","inf"]),
          ("partyIso3", "string", True),
          ("statusKind", "string", True, ["signed","ratified","acceded","withdrawn","suspended","not_party","observer"]),
          ("reservationsDescription", "string", False),
          ("effectiveFrom", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagViolationEvent",
        "desc": "Alleged violation / OPCW / BWC ISU / ATT Secretariat concern",
        "fields": [
          ("eventId", "string", True),
          ("statusVid", "string", True, None, "bridges recordTreatyStatus"),
          ("violationType", "string", True, ["stockpile","use","transfer","production","inspection_refusal","non_reporting"]),
          ("weaponCategory", "string", False, ["chemical","biological","nuclear","cluster_munitions","cw_agent","landmines","small_arms"]),
          ("victimsCount", "integer", False),
          ("allegedAt", "string", True),
        ],
        "classify": ("severityTier", "if violationType = \"use\" then \"critical\" else if violationType = \"production\" or violationType = \"transfer\" then \"severe\" else \"concern\"", ["concern","severe","critical"]),
      },
    ],
  },
  {
    "slug": "air-quality",
    "app": "airQuality",
    "methods": [
      {
        "name": "reportStationReading",
        "desc": "WHO AQG / EPA AirNow / EEA / OpenAQ reading (bridges pandemic-preparedness + disaster-response + cyclone-prepo)",
        "fields": [
          ("readingId", "string", True),
          ("stationId", "string", True),
          ("countryIso3", "string", True),
          ("pm25", "number", False, None, "ug/m3"),
          ("pm10", "number", False),
          ("no2", "number", False),
          ("o3", "number", False),
          ("so2", "number", False),
          ("co", "number", False),
          ("aqi", "integer", False),
          ("readingUtc", "string", True),
        ],
        "classify": ("airQualityTier", "if aqi != null and aqi >= 300 then \"hazardous\" else if aqi != null and aqi >= 200 then \"very_unhealthy\" else if aqi != null and aqi >= 150 then \"unhealthy\" else if aqi != null and aqi >= 100 then \"unhealthy_sg\" else if aqi != null and aqi >= 50 then \"moderate\" else \"good\"", ["good","moderate","unhealthy_sg","unhealthy","very_unhealthy","hazardous"]),
      },
      {
        "name": "issueHealthAlert",
        "desc": "Air-quality public health alert (bridges universal-health-coverage + pandemic-preparedness)",
        "fields": [
          ("alertId", "string", True),
          ("readingVid", "string", True, None, "bridges reportStationReading"),
          ("advisoryLevel", "string", True, ["advisory","warning","emergency"]),
          ("affectedPopulation", "integer", False),
          ("vulnerableGroups", "string", False, None, "comma: children,elderly,asthma,copd,pregnant,cardiovascular"),
          ("issuedAt", "string", True),
          ("expiresAt", "string", False),
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
