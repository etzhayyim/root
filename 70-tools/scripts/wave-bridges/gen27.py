#!/usr/bin/env python3
"""Wave 27 bridges — grid / press freedom / AMS / orbital debris / SDG reporting."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "power-grid-interconnect",
    "app": "powerGridInterconnect",
    "methods": [
      {
        "name": "recordCrossBorderFlow",
        "desc": "Cross-border electricity flow (ENTSO-E / NERC / CAISO / MISO — bridges climate-carbon-market + datacenter-energy + space-weather)",
        "fields": [
          ("flowId", "string", True),
          ("interconnectName", "string", True),
          ("exportSystemOperatorLei", "string", False),
          ("importSystemOperatorLei", "string", False),
          ("exportIso3", "string", True),
          ("importIso3", "string", True),
          ("periodHour", "string", True, None, "YYYY-MM-DDTHH"),
          ("flowMwh", "number", True),
          ("marginalGenFuel", "string", False, ["coal","gas","nuclear","hydro","wind","solar","biomass","oil","geothermal"]),
          ("congestionPct", "number", False),
          ("priceEurMwh", "number", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("congestionTier", "if congestionPct != null and congestionPct >= 80 then \"saturated\" else if congestionPct != null and congestionPct >= 50 then \"stressed\" else \"normal\"", ["normal","stressed","saturated"]),
      },
      {
        "name": "flagCurtailment",
        "desc": "Renewable curtailment or load shedding event",
        "fields": [
          ("eventId", "string", True),
          ("flowVid", "string", False, None, "bridges recordCrossBorderFlow"),
          ("regionIso3", "string", True),
          ("eventKind", "string", True, ["renewable_curtailment","load_shedding","grid_separation","frequency_deviation","re_dispatch","ancillary_services"]),
          ("spaceWxEventVid", "string", False, None, "bridges open-space-weather"),
          ("energyMwh", "number", False),
          ("durationMinutes", "integer", False),
          ("occurredAt", "string", True),
        ],
        "classify": ("impactTier", "if eventKind = \"grid_separation\" or (durationMinutes != null and durationMinutes >= 180) then \"major\" else if durationMinutes != null and durationMinutes >= 30 then \"significant\" else \"routine\"", ["routine","significant","major"]),
      },
    ],
  },
  {
    "slug": "press-freedom",
    "app": "pressFreedom",
    "methods": [
      {
        "name": "recordIndex",
        "desc": "RSF / Freedom House / CPJ press-freedom index (bridges election-integrity + misinformation-observatory + election integrity)",
        "fields": [
          ("recordId", "string", True),
          ("countryIso3", "string", True),
          ("indexProvider", "string", True, ["rsf","freedom_house","cpj","ifj","v_dem","bbc_media_action"]),
          ("cursorYear", "integer", True),
          ("scoreValue", "number", True, None, "index score 0-100 (higher=freer)"),
          ("rankGlobal", "integer", False),
          ("publishedAt", "string", True),
        ],
        "classify": ("freedomTier", "if scoreValue >= 80 then \"good\" else if scoreValue >= 60 then \"satisfactory\" else if scoreValue >= 40 then \"problematic\" else if scoreValue >= 20 then \"difficult\" else \"very_serious\"", ["very_serious","difficult","problematic","satisfactory","good"]),
      },
      {
        "name": "flagJournalistIncident",
        "desc": "Journalist attack / arrest / killing (bridges ofac-sanctions + indigenous-rights + forced-labor)",
        "fields": [
          ("incidentId", "string", True),
          ("indexRecordVid", "string", False, None, "bridges recordIndex"),
          ("incidentType", "string", True, ["killed","imprisoned","harassed","surveilled","exiled","legal_prosecution","online_attack","physical_attack","equipment_seizure"]),
          ("affectedCount", "integer", True),
          ("locationIso3", "string", True),
          ("perpetratorCategory", "string", False, ["state","non_state","organized_crime","political_actor","unknown"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if incidentType = \"killed\" then \"fatal\" else if incidentType = \"imprisoned\" or incidentType = \"physical_attack\" then \"severe\" else \"serious\"", ["serious","severe","fatal"]),
      },
    ],
  },
  {
    "slug": "antimicrobial-stewardship",
    "app": "antimicrobialStewardship",
    "methods": [
      {
        "name": "recordFacilityProgram",
        "desc": "AMS program (CDC Core Elements / ECDC / Japan AMR Action Plan — bridges amr-surveillance + universal-health-coverage + pharma-supply)",
        "fields": [
          ("programId", "string", True),
          ("facilityLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("facilityType", "string", True, ["hospital","nursing_home","outpatient","livestock","aquaculture","community_pharmacy"]),
          ("coreElementsImplemented", "integer", True, None, "count of CDC Core Elements 0-7"),
          ("startedAt", "string", True),
        ],
        "classify": ("maturityTier", "if coreElementsImplemented >= 7 then \"full\" else if coreElementsImplemented >= 5 then \"established\" else if coreElementsImplemented >= 3 then \"developing\" else \"basic\"", ["basic","developing","established","full"]),
      },
      {
        "name": "reportPrescriptionMetric",
        "desc": "AWaRe category prescription rate / DDD (bridges pharma-supply + atc)",
        "fields": [
          ("metricId", "string", True),
          ("programVid", "string", True, None, "bridges recordFacilityProgram"),
          ("atcCode", "string", False, None, "bridges open-atc"),
          ("awareCategory", "string", True, ["access","watch","reserve","not_recommended"]),
          ("ddd1000PatientDays", "number", False),
          ("accessSharePct", "number", False, None, "% of total abx use in Access category"),
          ("measuredYear", "integer", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "orbital-debris",
    "app": "orbitalDebris",
    "methods": [
      {
        "name": "assessObject",
        "desc": "Orbital-debris mitigation assessment (IADC / ISO 24113 / FCC §25 — bridges space-traffic + ai-supply-chain)",
        "fields": [
          ("assessmentId", "string", True),
          ("objectVid", "string", False, None, "bridges open-space-traffic catalogObject"),
          ("operatorLei", "string", False),
          ("pmdPlanType", "string", True, ["direct_re_entry","controlled_re_entry","uncontrolled","graveyard_disposal","boost_out","atmospheric_drag"]),
          ("deorbitCompliance25yr", "boolean", False, None, "IADC 25-year rule (now 5-year proposed)"),
          ("casualtyRisk", "number", False, None, "max 1E-4"),
          ("assessedAt", "string", True),
        ],
        "classify": ("complianceTier", "if deorbitCompliance25yr = false then \"non_compliant\" else if pmdPlanType = \"uncontrolled\" then \"marginal\" else \"compliant\"", ["compliant","marginal","non_compliant"]),
      },
      {
        "name": "logBreakup",
        "desc": "Break-up / fragmentation event (bridges space-traffic conjunctions)",
        "fields": [
          ("breakupId", "string", True),
          ("parentObjectVid", "string", True, None, "bridges open-space-traffic"),
          ("fragmentCount", "integer", False),
          ("causeClass", "string", False, ["collision","propulsion_failure","deliberate_asat","battery_breach","aerodynamic","unknown"]),
          ("apogeeKmAtBreakup", "number", False),
          ("occurredAt", "string", True),
        ],
        "classify": ("kesslerContributionTier", "if causeClass = \"deliberate_asat\" or (fragmentCount != null and fragmentCount >= 500) then \"severe\" else if fragmentCount != null and fragmentCount >= 50 then \"significant\" else \"minor\"", ["minor","significant","severe"]),
      },
    ],
  },
  {
    "slug": "sdg-reporting",
    "app": "sdgReporting",
    "methods": [
      {
        "name": "submitVnr",
        "desc": "Voluntary National Review (UN HLPF — bridges biodiversity-gbf + universal-health-coverage + climate-adaptation-finance + cofog)",
        "fields": [
          ("vnrId", "string", True),
          ("countryIso3", "string", True),
          ("submissionYear", "integer", True),
          ("hlpfSession", "string", False),
          ("indicatorsCovered", "integer", False, None, "count of SDG indicators reported"),
          ("dataGapsCount", "integer", False),
          ("leaveNoOneBehindFocus", "boolean", False),
          ("submittedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "reportIndicatorProgress",
        "desc": "Per-indicator SDG progress vs 2030 target (bridges open-sdg / biodiversity-gbf)",
        "fields": [
          ("progressId", "string", True),
          ("vnrVid", "string", False, None, "bridges submitVnr"),
          ("sdgIndicator", "string", True, None, "e.g. 3.1.1 / 13.2.1"),
          ("countryIso3", "string", True),
          ("currentValue", "number", False),
          ("targetValue2030", "number", False),
          ("progressPct", "number", False, None, "% of 2030 target achieved (vs 2015 baseline)"),
          ("reportedYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("progressTier", "if progressPct != null and progressPct >= 100 then \"achieved\" else if progressPct != null and progressPct >= 70 then \"on_track\" else if progressPct != null and progressPct >= 30 then \"progressing_slowly\" else if progressPct != null and progressPct >= 0 then \"stagnating\" else \"regressing\"", ["regressing","stagnating","progressing_slowly","on_track","achieved"]),
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
