#!/usr/bin/env python3
"""Wave 18 — space / agri / pharma / water / pandemic bridges."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "space-traffic",
    "app": "spaceTraffic",
    "methods": [
      {
        "name": "catalogObject",
        "desc": "Space-Track.org / 18 SDS catalog (bridges ai-supply-chain + cyber-compliance via NORAD ID)",
        "fields": [
          ("objectId", "string", True, None, "NORAD catalog number"),
          ("intlDesignator", "string", False, None, "COSPAR YYYY-NNNX"),
          ("objectType", "string", True, ["payload","rocket_body","debris","tba","unknown"]),
          ("ownerIso3", "string", False),
          ("operatorLei", "string", False),
          ("apogeeKm", "number", False),
          ("perigeeKm", "number", False),
          ("inclinationDeg", "number", False),
          ("rcsSize", "string", False, ["small","medium","large"]),
          ("launchedAt", "string", False),
          ("catalogedAt", "string", True),
        ],
        "classify": ("orbitTier", "if perigeeKm != null and perigeeKm < 2000 then \"LEO\" else if perigeeKm != null and perigeeKm < 35786 then \"MEO\" else if perigeeKm != null and perigeeKm < 40000 then \"GEO\" else \"HEO\"", ["LEO","MEO","GEO","HEO"]),
      },
      {
        "name": "flagConjunction",
        "desc": "Conjunction data message (CDM) against two tracked objects",
        "fields": [
          ("conjunctionId", "string", True),
          ("primaryObjectVid", "string", True, None, "bridges catalogObject"),
          ("secondaryObjectVid", "string", True, None, "bridges catalogObject"),
          ("tcaUtc", "string", True, None, "time of closest approach"),
          ("missDistanceM", "number", True),
          ("probabilityCollision", "number", False),
          ("assessedAt", "string", True),
        ],
        "classify": ("riskTier", "if missDistanceM < 100 then \"emergency_maneuver\" else if missDistanceM < 1000 then \"high_interest\" else \"monitor\"", ["monitor","high_interest","emergency_maneuver"]),
      },
    ],
  },
  {
    "slug": "agri-food-security",
    "app": "agriFoodSecurity",
    "methods": [
      {
        "name": "recordHarvest",
        "desc": "FAO / USDA crop harvest record (bridges commodity-trade + hs + m49 region)",
        "fields": [
          ("harvestId", "string", True),
          ("cropHsCode", "string", True, None, "HS chapter 10-12 grains/oilseeds, 07 veg, 08 fruit"),
          ("regionM49", "string", True, None, "UN M49 geographic code"),
          ("harvestYear", "integer", True),
          ("yieldKgHa", "number", False),
          ("productionTonnes", "number", True),
          ("faoStockUseRatio", "number", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("supplyTier", "if faoStockUseRatio != null and faoStockUseRatio < 0.15 then \"critical\" else if faoStockUseRatio != null and faoStockUseRatio < 0.25 then \"tight\" else \"adequate\"", ["adequate","tight","critical"]),
      },
      {
        "name": "flagPriceCrisis",
        "desc": "FAO Food Price Index crisis flag (trade-finance-factoring / commodity-trade bridge)",
        "fields": [
          ("crisisId", "string", True),
          ("harvestVid", "string", False, None, "bridges recordHarvest"),
          ("commodityTradeVid", "string", False, None, "bridges open-commodity-trade"),
          ("indexValue", "number", True, None, "FAO FPI 2014-2016=100"),
          ("yoyChangePct", "number", False),
          ("driver", "string", False, ["drought","war","export_ban","currency","pandemic","locust","flood"]),
          ("flaggedAt", "string", True),
        ],
        "classify": ("severityTier", "if indexValue >= 160 or yoyChangePct >= 40 then \"severe\" else if indexValue >= 130 or yoyChangePct >= 20 then \"elevated\" else \"normal\"", ["normal","elevated","severe"]),
      },
    ],
  },
  {
    "slug": "pharma-supply",
    "app": "pharmaSupply",
    "methods": [
      {
        "name": "registerProduct",
        "desc": "Pharma product registration (ATC + FDA NDC + EMA — bridges open-atc + open-ndc)",
        "fields": [
          ("productId", "string", True),
          ("atcCode", "string", False, None, "WHO ATC L5 code, bridges open-atc"),
          ("ndcCode", "string", False, None, "FDA NDC 10/11-digit, bridges open-ndc"),
          ("emaProductNumber", "string", False),
          ("manufacturerLei", "string", False),
          ("apiOriginIso3", "string", False, None, "active pharmaceutical ingredient country"),
          ("dosageForm", "string", False),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagShortage",
        "desc": "Drug shortage (FDA/EMA — bridges forced-labor + supply-chain-finance + critical-minerals)",
        "fields": [
          ("shortageId", "string", True),
          ("productVid", "string", True, None, "bridges registerProduct"),
          ("reporter", "string", True, ["FDA","EMA","PMDA","HC","TGA","WHO","ASHP"]),
          ("rootCause", "string", False, ["api_shortage","mfg_disruption","demand_spike","recall","regulatory","logistics"]),
          ("criticalMineralVid", "string", False, None, "bridges open-critical-minerals"),
          ("supplyChainFinanceVid", "string", False, None, "bridges open-supply-chain-finance"),
          ("estimatedRestoreDate", "string", False),
          ("flaggedAt", "string", True),
        ],
        "classify": ("severityTier", "if rootCause = \"api_shortage\" or rootCause = \"mfg_disruption\" then \"high\" else if rootCause = \"recall\" then \"critical\" else \"moderate\"", ["moderate","high","critical"]),
      },
    ],
  },
  {
    "slug": "water-scarcity",
    "app": "waterScarcity",
    "methods": [
      {
        "name": "recordBasinMetric",
        "desc": "Transboundary basin water stress (WRI Aqueduct / FAO AQUASTAT — bridges cofog + agri-food-security)",
        "fields": [
          ("metricId", "string", True),
          ("basinName", "string", True),
          ("ripariansIso3", "string", True, None, "comma-separated ISO 3166-1 alpha-3"),
          ("baselineWaterStress", "number", True, None, "WRI 0-5 scale"),
          ("droughtRisk", "number", False),
          ("regulatoryInstrument", "string", False, None, "treaty / convention name"),
          ("agriHarvestVid", "string", False, None, "bridges open-agri-food-security"),
          ("measuredYear", "integer", True),
        ],
        "classify": ("stressTier", "if baselineWaterStress >= 4 then \"extreme\" else if baselineWaterStress >= 3 then \"high\" else if baselineWaterStress >= 2 then \"medium_high\" else if baselineWaterStress >= 1 then \"medium_low\" else \"low\"", ["low","medium_low","medium_high","high","extreme"]),
      },
      {
        "name": "flagTreatyDispute",
        "desc": "Transboundary water treaty dispute (Helsinki Rules / UN Watercourses Convention)",
        "fields": [
          ("disputeId", "string", True),
          ("basinMetricVid", "string", True, None, "bridges recordBasinMetric"),
          ("complainantIso3", "string", True),
          ("respondentIso3", "string", True),
          ("issue", "string", True, ["upstream_dam","diversion","pollution","reduced_flow","groundwater_depletion","navigation"]),
          ("wtoDisputeVid", "string", False, None, "bridges open-wto-dispute if applicable"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "pandemic-preparedness",
    "app": "pandemicPreparedness",
    "methods": [
      {
        "name": "reportOutbreak",
        "desc": "WHO IHR 2005 outbreak report (bridges pharma-supply + icd10 disease + forced-labor)",
        "fields": [
          ("outbreakId", "string", True),
          ("pathogenName", "string", True),
          ("icd10Code", "string", False, None, "bridges open-icd10"),
          ("jurisdictionIso3", "string", True),
          ("casesConfirmed", "integer", False),
          ("deaths", "integer", False),
          ("cfrPct", "number", False, None, "case fatality rate"),
          ("phase", "string", True, ["alert","cluster","epidemic","pandemic_declared","controlled"]),
          ("pheicDeclared", "boolean", False, None, "Public Health Emergency of International Concern"),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if phase = \"pandemic_declared\" or (cfrPct != null and cfrPct >= 10) then \"catastrophic\" else if phase = \"epidemic\" or (cfrPct != null and cfrPct >= 3) then \"severe\" else if phase = \"cluster\" then \"elevated\" else \"routine\"", ["routine","elevated","severe","catastrophic"]),
      },
      {
        "name": "stockpileCountermeasure",
        "desc": "Medical countermeasure stockpile (vaccine / antiviral / PPE) per country",
        "fields": [
          ("stockpileId", "string", True),
          ("outbreakVid", "string", False, None, "bridges reportOutbreak"),
          ("countermeasureType", "string", True, ["vaccine","antiviral","antibody","antibiotic","ppe","diagnostic","ventilator"]),
          ("productVid", "string", False, None, "bridges open-pharma-supply"),
          ("jurisdictionIso3", "string", True),
          ("unitsStockpiled", "integer", True),
          ("daysOfSupply", "number", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("readinessTier", "if daysOfSupply != null and daysOfSupply >= 90 then \"robust\" else if daysOfSupply != null and daysOfSupply >= 30 then \"adequate\" else \"insufficient\"", ["insufficient","adequate","robust"]),
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
