#!/usr/bin/env python3
"""Wave 33 bridges — textile / LAWS / language / EV charging / Antarctic."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "textile-circularity",
    "app": "textileCircularity",
    "methods": [
      {
        "name": "recordGarmentFlow",
        "desc": "Garment lifecycle flow (EU ESPR / DPP / EPR textile — bridges chemicals-management + forced-labor + food-waste-epr + plastic-treaty)",
        "fields": [
          ("flowId", "string", True),
          ("brandLei", "string", False),
          ("hsCode", "string", False),
          ("productCategory", "string", True, ["fast_fashion","luxury","sport","workwear","home_textile","medical","technical"]),
          ("fiberMix", "string", False, None, "comma: cotton,polyester,nylon,wool,viscose,recycled,elastane"),
          ("stage", "string", True, ["design","production","distribution","use","collection","reuse","recycle","incineration","landfill"]),
          ("tonnes", "number", True),
          ("originIso3", "string", False),
          ("destinationIso3", "string", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("circularityTier", "if stage = \"reuse\" or stage = \"recycle\" then \"circular\" else if stage = \"collection\" then \"recovery\" else if stage = \"incineration\" or stage = \"landfill\" then \"linear\" else \"in_use\"", ["linear","in_use","recovery","circular"]),
      },
      {
        "name": "registerDppBadge",
        "desc": "Digital Product Passport (ESPR Reg 2024/1781 — bridges slsa-supply-chain + forced-labor + chemicals-management)",
        "fields": [
          ("dppId", "string", True),
          ("flowVid", "string", True, None, "bridges recordGarmentFlow"),
          ("dppStandard", "string", True, ["jtc24_iso_iec","catena_x","gs1_digital_link","cirpass"]),
          ("recycledContentPct", "number", False),
          ("durabilityIndex", "number", False),
          ("repairabilityIndex", "number", False),
          ("substancesOfConcernFlagged", "boolean", False, None, "bridges open-chemicals-management"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "laws-autonomous-weapons",
    "app": "lawsAutonomousWeapons",
    "methods": [
      {
        "name": "recordDeclaration",
        "desc": "LAWS declaration / position under UN GGE / CCW (bridges disarmament-treaties + ai-governance + esports-integrity)",
        "fields": [
          ("declarationId", "string", True),
          ("stateIso3", "string", True),
          ("forum", "string", True, ["un_gge","ccw","unga1","unga6","icrc","tpnw_review"]),
          ("positionType", "string", True, ["moratorium_calling","prohibit_laws","regulate_laws","no_laws_policy","opposed_restriction","silent"]),
          ("keyElements", "string", False, None, "meaningful_human_control / accountability / ihl_compliance / proliferation"),
          ("declaredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSystemDeployment",
        "desc": "Alleged LAWS battlefield deployment (bridges disarmament-treaties + ai-governance)",
        "fields": [
          ("deploymentId", "string", True),
          ("systemName", "string", True),
          ("operatorIso3", "string", True),
          ("conflictName", "string", False),
          ("autonomyLevel", "string", True, ["human_on_the_loop","human_in_the_loop","fully_autonomous","swarm"]),
          ("aiModelVid", "string", False, None, "bridges open-ai-governance"),
          ("sourceType", "string", False, ["open_source","ngo_report","state_claim","journalism","uav_log"]),
          ("allegedAt", "string", True),
        ],
        "classify": ("concernTier", "if autonomyLevel = \"fully_autonomous\" or autonomyLevel = \"swarm\" then \"critical\" else if autonomyLevel = \"human_on_the_loop\" then \"elevated\" else \"routine\"", ["routine","elevated","critical"]),
      },
    ],
  },
  {
    "slug": "language-preservation",
    "app": "languagePreservation",
    "methods": [
      {
        "name": "registerEndangeredLanguage",
        "desc": "UNESCO ILC / ELPublishing / Ethnologue endangered language (bridges indigenous-rights + cultural-heritage + misinformation-observatory)",
        "fields": [
          ("languageId", "string", True, None, "ISO 639-3"),
          ("languageName", "string", True),
          ("regionsIso3", "string", True),
          ("speakerCount", "integer", False),
          ("unescoStatus", "string", True, ["safe","vulnerable","definitely_endangered","severely_endangered","critically_endangered","extinct"]),
          ("writingSystem", "string", False),
          ("transmissionIntergenPct", "number", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("urgencyTier", "if unescoStatus = \"critically_endangered\" or unescoStatus = \"extinct\" then \"extreme\" else if unescoStatus = \"severely_endangered\" then \"high\" else if unescoStatus = \"definitely_endangered\" then \"elevated\" else \"monitor\"", ["monitor","elevated","high","extreme"]),
      },
      {
        "name": "recordRevitalizationProgram",
        "desc": "Language revitalization program (bridges indigenous-rights + climate-adaptation-finance)",
        "fields": [
          ("programId", "string", True),
          ("languageVid", "string", True, None, "bridges registerEndangeredLanguage"),
          ("programKind", "string", True, ["immersion_school","adult_apprentice","media","digital_corpus","dictionary","ai_model","orthography"]),
          ("sponsorLei", "string", False),
          ("annualBudgetUsd", "number", False),
          ("startedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ev-charging-ocpp",
    "app": "evChargingOcpp",
    "methods": [
      {
        "name": "registerStation",
        "desc": "EV charging station (OCPP 2.0.1 / ISO 15118 / NACS-CCS bridge — bridges urban-mobility + power-grid-interconnect + datacenter-energy)",
        "fields": [
          ("stationId", "string", True),
          ("operatorLei", "string", False),
          ("locationIso3", "string", True),
          ("cpoName", "string", False),
          ("ocppVersion", "string", False, ["1.6j","2.0.1","2.1"]),
          ("connectorStandards", "string", False, None, "comma: ccs1,ccs2,nacs,chademo,gb_t,mennekes,type2"),
          ("maxPowerKw", "number", False),
          ("v2gCapable", "boolean", False),
          ("iso15118PnCSupported", "boolean", False),
          ("commissionedAt", "string", True),
        ],
        "classify": ("chargingTier", "if maxPowerKw != null and maxPowerKw >= 350 then \"ultra_fast\" else if maxPowerKw != null and maxPowerKw >= 100 then \"fast\" else if maxPowerKw != null and maxPowerKw >= 50 then \"rapid\" else \"ac_slow\"", ["ac_slow","rapid","fast","ultra_fast"]),
      },
      {
        "name": "flagReliabilityMetric",
        "desc": "Station reliability / uptime metric",
        "fields": [
          ("metricId", "string", True),
          ("stationVid", "string", True, None, "bridges registerStation"),
          ("measurementMonth", "string", True),
          ("uptimePct", "number", True),
          ("sessionSuccessPct", "number", False),
          ("meanSessionKwh", "number", False),
          ("reasonFailures", "string", False, None, "comma: connector,payment,network,authorization,power,hardware"),
          ("recordedAt", "string", True),
        ],
        "classify": ("reliabilityTier", "if uptimePct >= 99 then \"excellent\" else if uptimePct >= 97 then \"good\" else if uptimePct >= 90 then \"fair\" else \"poor\"", ["poor","fair","good","excellent"]),
      },
    ],
  },
  {
    "slug": "antarctic-treaty",
    "app": "antarcticTreaty",
    "methods": [
      {
        "name": "recordActivity",
        "desc": "Antarctic Treaty System activity (ATCM / CCAMLR / CEP — bridges fisheries-iuu + biodiversity-gbf + cultural-heritage + bbnj-highseas)",
        "fields": [
          ("activityId", "string", True),
          ("stateIso3", "string", True),
          ("activityType", "string", True, ["scientific","tourism","fishing","logistic","station_construction","environmental_monitoring"]),
          ("areaCode", "string", False, None, "e.g. Ross Sea MPA / ASPA-NN / CCAMLR 48.3"),
          ("seasonYear", "integer", True),
          ("personnelCount", "integer", False),
          ("vesselImo", "string", False),
          ("startedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMadridViolation",
        "desc": "Madrid Protocol environmental violation (ATCM Recommendation XV-1 / CEP)",
        "fields": [
          ("violationId", "string", True),
          ("activityVid", "string", True, None, "bridges recordActivity"),
          ("annexViolated", "string", True, ["I_eia","II_flora_fauna","III_waste","IV_marine_pollution","V_protected_area","VI_liability"]),
          ("severity", "string", True, ["minor","transitory","more_than_minor_or_transitory"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("concernTier", "if severity = \"more_than_minor_or_transitory\" then \"critical\" else if severity = \"transitory\" then \"elevated\" else \"monitor\"", ["monitor","elevated","critical"]),
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
