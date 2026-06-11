#!/usr/bin/env python3
"""Wave 20 bridges — elections / refugees / mining / adaptation finance / heritage."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "election-integrity",
    "app": "electionIntegrity",
    "methods": [
      {
        "name": "recordObservation",
        "desc": "Election observation finding (OSCE/ODIHR / EU EOM / Carter Center — bridges ai-governance + cyber-incident)",
        "fields": [
          ("observationId", "string", True),
          ("jurisdictionIso3", "string", True),
          ("electionDate", "string", True),
          ("missionType", "string", True, ["OSCE_ODIHR","EU_EOM","CARTER","OAS","AU","ANFREL","COMMONWEALTH"]),
          ("findingCode", "string", True, ["vote_suppression","media_bias","campaign_finance","disinformation","cyber_interference","ballot_integrity","tabulation_anomaly","judicial_interference"]),
          ("aiModelVid", "string", False, None, "bridges open-ai-governance if deepfake"),
          ("cyberIncidentVid", "string", False, None, "bridges open-cyber-incident"),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if findingCode = \"tabulation_anomaly\" or findingCode = \"cyber_interference\" then \"critical\" else if findingCode = \"disinformation\" or findingCode = \"vote_suppression\" then \"serious\" else \"concern\"", ["concern","serious","critical"]),
      },
      {
        "name": "recordRecount",
        "desc": "Recount / audit result vs original tally",
        "fields": [
          ("recountId", "string", True),
          ("observationVid", "string", False, None, "bridges recordObservation"),
          ("contestDescription", "string", True),
          ("originalMargin", "integer", False),
          ("recountedMargin", "integer", False),
          ("changedOutcome", "boolean", False),
          ("certifiedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "refugee-unhcr",
    "app": "refugeeUnhcr",
    "methods": [
      {
        "name": "recordPopulation",
        "desc": "UNHCR population snapshot (bridges forced-labor + disaster-response + cofog)",
        "fields": [
          ("snapshotId", "string", True),
          ("originIso3", "string", True),
          ("asylumIso3", "string", True),
          ("populationType", "string", True, ["refugee","asylum_seeker","idp","returnee","stateless","other_protected"]),
          ("populationSize", "integer", True),
          ("causeDisasterVid", "string", False, None, "bridges open-disaster-response"),
          ("snapshotMonth", "string", True, None, "YYYY-MM"),
        ],
        "classify": ("scaleTier", "if populationSize >= 1000000 then \"mass\" else if populationSize >= 100000 then \"large\" else if populationSize >= 10000 then \"significant\" else \"small\"", ["small","significant","large","mass"]),
      },
      {
        "name": "logRepatriation",
        "desc": "Voluntary repatriation / resettlement / integration tracking",
        "fields": [
          ("eventId", "string", True),
          ("snapshotVid", "string", True, None, "bridges recordPopulation"),
          ("solutionType", "string", True, ["voluntary_repatriation","local_integration","resettlement","naturalization","complementary_pathway"]),
          ("personsCount", "integer", True),
          ("destinationIso3", "string", False),
          ("assistedBy", "string", False),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "mining-operation",
    "app": "miningOperation",
    "methods": [
      {
        "name": "registerMine",
        "desc": "Mining operation registry (S&P Capital IQ / USGS MRDS — bridges critical-minerals + forced-labor + water-scarcity)",
        "fields": [
          ("mineId", "string", True),
          ("operatorLei", "string", False),
          ("commodityHs", "string", False, None, "primary commodity HS"),
          ("criticalMineralVid", "string", False, None, "bridges open-critical-minerals"),
          ("locationIso3", "string", True),
          ("locationLat", "number", False),
          ("locationLon", "number", False),
          ("mineType", "string", True, ["open_pit","underground","placer","ISL","heap_leach","asm"]),
          ("status", "string", True, ["prospect","development","production","suspended","closed","reclamation"]),
          ("waterBasinVid", "string", False, None, "bridges open-water-scarcity"),
          ("registeredAt", "string", True),
        ],
        "classify": ("riskTier", "if mineType = \"asm\" then \"artisanal\" else if mineType = \"open_pit\" then \"large_scale\" else \"industrial\"", ["artisanal","industrial","large_scale"]),
      },
      {
        "name": "reportTailings",
        "desc": "Tailings dam safety report (GISTM — bridges disaster-response + water-scarcity)",
        "fields": [
          ("reportId", "string", True),
          ("mineVid", "string", True, None, "bridges registerMine"),
          ("gistmClassification", "string", True, ["extreme","very_high","high","significant","low"]),
          ("storageVolumeM3", "number", False),
          ("lastIndependentReviewAt", "string", False),
          ("failureMode", "string", False, ["overtopping","static_liquefaction","seismic","foundation","piping","erosion"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "climate-adaptation-finance",
    "app": "climateAdaptationFinance",
    "methods": [
      {
        "name": "approveProject",
        "desc": "GCF / GEF / AF / LDN climate adaptation project (bridges cofog + water-scarcity + agri-food-security)",
        "fields": [
          ("projectId", "string", True),
          ("fund", "string", True, ["GCF","GEF","AF","LDN","IDA","IDB","EBRD","AIIB","BILATERAL_ODA"]),
          ("recipientIso3", "string", True),
          ("implementingLei", "string", False),
          ("sector", "string", True, ["water","agriculture","coastal","forestry","energy","infra","health","urban"]),
          ("adaptationPct", "number", False, None, "% allocated to adaptation vs mitigation"),
          ("fundingUsd", "number", True),
          ("waterBasinVid", "string", False, None, "bridges open-water-scarcity"),
          ("harvestVid", "string", False, None, "bridges open-agri-food-security"),
          ("approvedAt", "string", True),
        ],
        "classify": ("scaleTier", "if fundingUsd >= 100000000 then \"large\" else if fundingUsd >= 10000000 then \"medium\" else \"small\"", ["small","medium","large"]),
      },
      {
        "name": "reportImpact",
        "desc": "Ex-post adaptation impact report",
        "fields": [
          ("reportId", "string", True),
          ("projectVid", "string", True, None, "bridges approveProject"),
          ("beneficiariesDirect", "integer", False),
          ("beneficiariesIndirect", "integer", False),
          ("hectaresRestored", "number", False),
          ("co2AvoidedTonnes", "number", False),
          ("disbursedPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cultural-heritage",
    "app": "culturalHeritage",
    "methods": [
      {
        "name": "listProperty",
        "desc": "UNESCO WHL / Intangible Heritage / Memory of the World (bridges disaster-response + water-scarcity)",
        "fields": [
          ("propertyId", "string", True),
          ("listType", "string", True, ["whc_cultural","whc_natural","whc_mixed","ich","mow","geopark"]),
          ("countryIso3", "string", True),
          ("inscribedYear", "integer", False),
          ("criteria", "string", False, None, "WHC criterion letters i-x"),
          ("areaHectares", "number", False),
          ("inscribedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagThreat",
        "desc": "Heritage threat (in-Danger list / SOC — bridges disaster-response + maritime-piracy + forced-labor)",
        "fields": [
          ("threatId", "string", True),
          ("propertyVid", "string", True, None, "bridges listProperty"),
          ("threatType", "string", True, ["armed_conflict","climate","development","tourism","poaching","pollution","natural_disaster","neglect"]),
          ("disasterVid", "string", False, None, "bridges open-disaster-response"),
          ("inDangerListing", "boolean", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if inDangerListing = true or threatType = \"armed_conflict\" then \"critical\" else if threatType = \"climate\" or threatType = \"natural_disaster\" then \"high\" else \"moderate\"", ["moderate","high","critical"]),
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
