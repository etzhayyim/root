#!/usr/bin/env python3
"""Wave 24 bridges — OCHA / climate litigation / AV safety / just transition / chemicals."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "ocha-funding",
    "app": "ochaFunding",
    "methods": [
      {
        "name": "recordFlow",
        "desc": "OCHA FTS humanitarian funding flow (bridges disaster-response + refugee-unhcr + climate-adaptation-finance)",
        "fields": [
          ("flowId", "string", True),
          ("sourceLei", "string", False),
          ("sourceType", "string", True, ["government","private_org","private_individual","un_agency","ngo","pooled_fund","other"]),
          ("recipientLei", "string", False),
          ("recipientType", "string", True, ["un_agency","red_cross","ngo","government","affected_population"]),
          ("destinationIso3", "string", True),
          ("emergencyCode", "string", False, None, "HRP/flash appeal code"),
          ("sectorCluster", "string", False, ["food","health","shelter","wash","education","protection","logistics","nutrition","camp"]),
          ("amountUsd", "number", True),
          ("pledged", "boolean", False, None, "pledged vs committed/paid"),
          ("flowDate", "string", True),
          ("recordedAt", "string", True),
        ],
        "classify": ("scaleTier", "if amountUsd >= 100000000 then \"mega\" else if amountUsd >= 10000000 then \"large\" else if amountUsd >= 1000000 then \"medium\" else \"small\"", ["small","medium","large","mega"]),
      },
      {
        "name": "flagAppealGap",
        "desc": "OCHA HRP / flash appeal funding gap",
        "fields": [
          ("gapId", "string", True),
          ("emergencyCode", "string", True),
          ("requestedUsd", "number", True),
          ("fundedUsd", "number", True),
          ("coveragePct", "number", True),
          ("assessedAt", "string", True),
        ],
        "classify": ("urgencyTier", "if coveragePct < 25 then \"critical\" else if coveragePct < 50 then \"severe\" else if coveragePct < 75 then \"moderate\" else \"adequate\"", ["adequate","moderate","severe","critical"]),
      },
    ],
  },
  {
    "slug": "climate-litigation",
    "app": "climateLitigation",
    "methods": [
      {
        "name": "fileCase",
        "desc": "Sabin Center climate case filing (bridges esg-risk-rating + sovereign-debt + commodity-trade)",
        "fields": [
          ("caseId", "string", True),
          ("jurisdictionIso3", "string", True),
          ("court", "string", True),
          ("claimantType", "string", True, ["individual","ngo","indigenous","youth","shareholder","investor","municipality","subnational","sovereign"]),
          ("defendantType", "string", True, ["sovereign","corporation","subnational","investor","public_authority"]),
          ("defendantLei", "string", False),
          ("claimBasis", "string", True, ["human_rights","constitutional","public_trust","tort","consumer_protection","securities_disclosure","administrative","tax_subsidy"]),
          ("reliefSought", "string", False, ["mitigation_order","adaptation_order","damages","disclosure","injunction","permit_revocation","price_subsidy"]),
          ("filedAt", "string", True),
        ],
        "classify": ("impactTier", "if claimBasis = \"constitutional\" or claimBasis = \"human_rights\" then \"precedent_setting\" else if defendantType = \"sovereign\" then \"strategic\" else \"commercial\"", ["commercial","strategic","precedent_setting"]),
      },
      {
        "name": "recordRuling",
        "desc": "Litigation ruling outcome + appeal path",
        "fields": [
          ("rulingId", "string", True),
          ("caseVid", "string", True, None, "bridges fileCase"),
          ("outcome", "string", True, ["claimant_win","claimant_partial","defendant_win","settled","withdrawn","dismissed"]),
          ("damagesAwardedUsd", "number", False),
          ("precedentCited", "string", False),
          ("appealFiled", "boolean", False),
          ("ruledAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "autonomous-vehicle-safety",
    "app": "autonomousVehicleSafety",
    "methods": [
      {
        "name": "registerOdd",
        "desc": "AV Operational Design Domain registration (SAE J3016 — bridges ai-governance + ustr-section-301 + urban-mobility)",
        "fields": [
          ("oddId", "string", True),
          ("operatorLei", "string", False),
          ("sdvClass", "string", True, ["L0","L1","L2","L3","L4","L5"]),
          ("domain", "string", True, ["highway","urban","suburban","geofenced","parking","last_mile","mining","port","farm"]),
          ("modelVid", "string", False, None, "bridges open-ai-governance"),
          ("locationIso3", "string", True),
          ("fleetSize", "integer", False),
          ("maxSpeedKph", "integer", False),
          ("certifiedAt", "string", True),
        ],
        "classify": ("autonomyTier", "if sdvClass = \"L4\" or sdvClass = \"L5\" then \"high_autonomy\" else if sdvClass = \"L3\" then \"conditional\" else \"adas\"", ["adas","conditional","high_autonomy"]),
      },
      {
        "name": "reportDisengagement",
        "desc": "AV disengagement / crash report (CA DMV / NHTSA SGO)",
        "fields": [
          ("eventId", "string", True),
          ("oddVid", "string", True, None, "bridges registerOdd"),
          ("eventType", "string", True, ["disengagement","collision","near_miss","stall","unintended_behavior"]),
          ("triggerCategory", "string", False, ["perception","planning","control","hmi","environmental","adversarial"]),
          ("injuries", "integer", False),
          ("fatalities", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if fatalities != null and fatalities >= 1 then \"fatal\" else if injuries != null and injuries >= 1 then \"injury\" else if eventType = \"collision\" then \"property\" else \"operational\"", ["operational","property","injury","fatal"]),
      },
    ],
  },
  {
    "slug": "just-transition",
    "app": "justTransition",
    "methods": [
      {
        "name": "recordSectoralShift",
        "desc": "Just transition sectoral workforce shift (bridges climate-adaptation-finance + refugee-unhcr + forced-labor)",
        "fields": [
          ("shiftId", "string", True),
          ("regionIso3", "string", True),
          ("fromSectorIsic", "string", True, None, "bridges open-isic"),
          ("toSectorIsic", "string", False),
          ("workersAffected", "integer", True),
          ("reskillingSpendUsd", "number", False),
          ("geographicScope", "string", True, ["local","regional","national"]),
          ("driver", "string", True, ["coal_phaseout","ice_ban","fishing_quota","automation","decarbonization","trade_policy"]),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "reportAdaptationOutcome",
        "desc": "Transition outcome: placement / wage delta / displacement",
        "fields": [
          ("outcomeId", "string", True),
          ("shiftVid", "string", True, None, "bridges recordSectoralShift"),
          ("placedCount", "integer", False),
          ("placementRatePct", "number", False),
          ("wageDeltaPct", "number", False),
          ("outOfLaborCount", "integer", False),
          ("measuredAt", "string", True),
        ],
        "classify": ("outcomeTier", "if placementRatePct != null and placementRatePct >= 80 and wageDeltaPct != null and wageDeltaPct >= 0 then \"successful\" else if placementRatePct != null and placementRatePct >= 50 then \"partial\" else \"inadequate\"", ["inadequate","partial","successful"]),
      },
    ],
  },
  {
    "slug": "chemicals-management",
    "app": "chemicalsManagement",
    "methods": [
      {
        "name": "listChemical",
        "desc": "Rotterdam / Stockholm / Minamata / Basel / SAICM chemical listing (bridges pharma-supply + water-scarcity + critical-minerals)",
        "fields": [
          ("listingId", "string", True),
          ("chemicalName", "string", True),
          ("casNumber", "string", False),
          ("convention", "string", True, ["rotterdam","stockholm","minamata","basel","saicm","reach_svhc","epa_toxics_release"]),
          ("annex", "string", False),
          ("useCategory", "string", False, ["pesticide","industrial","pharma","mining","processing","consumer","cosmetic"]),
          ("listedYear", "integer", False),
          ("effectiveFrom", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "reportRelease",
        "desc": "Chemical release / PRTR report (bridges mining + water-scarcity + biodiversity-gbf)",
        "fields": [
          ("releaseId", "string", True),
          ("facilityLei", "string", False),
          ("listingVid", "string", False, None, "bridges listChemical"),
          ("mediaAir", "number", False, None, "tonnes"),
          ("mediaWater", "number", False),
          ("mediaLand", "number", False),
          ("mediaTransferredOffsite", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
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
