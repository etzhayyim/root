#!/usr/bin/env python3
"""Wave 21 bridges — fisheries IUU / sovereign debt / plastic treaty / data center / biodiversity."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "fisheries-iuu",
    "app": "fisheriesIuu",
    "methods": [
      {
        "name": "flagVessel",
        "desc": "IUU fishing vessel flag (RFMO blacklists — bridges carrier-fleet + forced-labor + biosecurity)",
        "fields": [
          ("flagId", "string", True),
          ("imo", "string", False),
          ("vesselName", "string", False),
          ("flagStateIso3", "string", False),
          ("rfmo", "string", True, ["ICCAT","IOTC","WCPFC","IATTC","NAFO","NEAFC","SEAFO","CCAMLR","SIOFA","SPRFMO"]),
          ("violationCode", "string", True, ["unreported","illegal_gear","closed_area","unauthorized","quota_breach","transhipment","non_compliant_flag","human_trafficking"]),
          ("forcedLaborVid", "string", False, None, "bridges open-forced-labor"),
          ("carrierFleetVid", "string", False, None, "bridges open-carrier-fleet"),
          ("listedAt", "string", True),
        ],
        "classify": ("severityTier", "if violationCode = \"human_trafficking\" or violationCode = \"illegal_gear\" then \"critical\" else if violationCode = \"unauthorized\" or violationCode = \"closed_area\" then \"severe\" else \"major\"", ["major","severe","critical"]),
      },
      {
        "name": "recordCatch",
        "desc": "RFMO catch documentation (MSC/CDS — bridges hs + commodity-trade)",
        "fields": [
          ("catchId", "string", True),
          ("imo", "string", False),
          ("speciesAsfis", "string", True, None, "FAO ASFIS 3-alpha species, bridges open-asfis"),
          ("hsCode", "string", False),
          ("catchAreaFao", "string", False, None, "FAO major fishing area"),
          ("gearType", "string", False, ["longline","purse_seine","trawl","gillnet","troll","pole_line","dredge"]),
          ("tonnesLanded", "number", True),
          ("landedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "sovereign-debt",
    "app": "sovereignDebt",
    "methods": [
      {
        "name": "recordIssuance",
        "desc": "Sovereign bond issuance (IMF IFS / World Bank DRS — bridges banking + commodity-trade)",
        "fields": [
          ("issuanceId", "string", True),
          ("issuerIso3", "string", True),
          ("instrumentType", "string", True, ["eurobond","domestic","sukuk","linker","brady","panda","samurai","green","social","sdg"]),
          ("currency", "string", True, None, "ISO 4217"),
          ("amountFacial", "number", True),
          ("couponPct", "number", False),
          ("tenorYears", "number", True),
          ("yieldAtIssuancePct", "number", False),
          ("issuedAt", "string", True),
          ("maturesAt", "string", True),
        ],
        "classify": ("stressTier", "if yieldAtIssuancePct != null and yieldAtIssuancePct >= 15 then \"distressed\" else if yieldAtIssuancePct != null and yieldAtIssuancePct >= 8 then \"elevated\" else \"normal\"", ["normal","elevated","distressed"]),
      },
      {
        "name": "flagRestructuring",
        "desc": "Sovereign restructuring / common framework / Paris Club flag",
        "fields": [
          ("restructuringId", "string", True),
          ("issuerIso3", "string", True),
          ("framework", "string", True, ["paris_club","common_framework","london_club","london_terms","naples_terms","evian","private_only","bondholder_committee"]),
          ("imfProgram", "string", False, None, "IMF arrangement name if any"),
          ("hairCutPct", "number", False),
          ("extendedMaturityYears", "number", False),
          ("announcedAt", "string", True),
        ],
        "classify": ("severityTier", "if hairCutPct != null and hairCutPct >= 50 then \"deep\" else if hairCutPct != null and hairCutPct >= 20 then \"significant\" else \"reprofiling\"", ["reprofiling","significant","deep"]),
      },
    ],
  },
  {
    "slug": "plastic-treaty",
    "app": "plasticTreaty",
    "methods": [
      {
        "name": "recordTradeFlow",
        "desc": "Plastic waste / resin trade flow (Basel Convention Annex IX — bridges hs + customs + commodity-trade)",
        "fields": [
          ("flowId", "string", True),
          ("hsCode", "string", True, None, "HS 3915 / 3901-3914"),
          ("exporterIso3", "string", True),
          ("importerIso3", "string", True),
          ("baselCategory", "string", True, ["B3011","Y48","A3210","dissoluble","non_covered"]),
          ("tonnes", "number", True),
          ("priorInformedConsent", "boolean", False),
          ("customsDeclarationVid", "string", False, None, "bridges open-customs-clearance"),
          ("shippedAt", "string", True),
        ],
        "classify": ("complianceTier", "if priorInformedConsent = false and baselCategory = \"Y48\" then \"illegal_shipment\" else if baselCategory = \"B3011\" then \"compliant_mixed\" else \"compliant\"", ["compliant","compliant_mixed","illegal_shipment"]),
      },
      {
        "name": "reportCountryPledge",
        "desc": "UN INC-5 plastic treaty national pledge (targets + capacity)",
        "fields": [
          ("pledgeId", "string", True),
          ("countryIso3", "string", True),
          ("target", "string", True, ["production_cap","recycled_content","epr_scheme","single_use_ban","reusable_quota","chemical_of_concern"]),
          ("baselineYear", "integer", False),
          ("targetYear", "integer", True),
          ("targetValue", "number", False),
          ("unit", "string", False),
          ("submittedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "datacenter-energy",
    "app": "datacenterEnergy",
    "methods": [
      {
        "name": "registerFacility",
        "desc": "Hyperscale / colocation DC registry (Uptime Institute / iMasons / LBNL — bridges ai-supply-chain + water-scarcity)",
        "fields": [
          ("facilityId", "string", True),
          ("operatorLei", "string", False),
          ("locationIso3", "string", True),
          ("itCapacityMw", "number", True),
          ("tier", "string", False, ["I","II","III","IV"], "Uptime Institute tier"),
          ("pueAnnual", "number", False, None, "Power Usage Effectiveness"),
          ("werAnnual", "number", False, None, "Water Usage Effectiveness L/kWh"),
          ("primaryCooling", "string", False, ["air","liquid","immersion","free_air","adiabatic"]),
          ("powerSource", "string", False),
          ("commissionedAt", "string", True),
        ],
        "classify": ("efficiencyTier", "if pueAnnual != null and pueAnnual <= 1.2 then \"exemplary\" else if pueAnnual != null and pueAnnual <= 1.5 then \"efficient\" else if pueAnnual != null and pueAnnual <= 1.8 then \"standard\" else \"legacy\"", ["legacy","standard","efficient","exemplary"]),
      },
      {
        "name": "recordLoad",
        "desc": "DC load measurement (AI training vs inference vs general compute)",
        "fields": [
          ("loadId", "string", True),
          ("facilityVid", "string", True, None, "bridges registerFacility"),
          ("periodMonth", "string", True, None, "YYYY-MM"),
          ("aiTrainingMwh", "number", False),
          ("aiInferenceMwh", "number", False),
          ("generalMwh", "number", False),
          ("avgCarbonGCo2Kwh", "number", False),
          ("waterConsumedLitres", "number", False),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "biodiversity-gbf",
    "app": "biodiversityGbf",
    "methods": [
      {
        "name": "recordIndicator",
        "desc": "KM-GBF target indicator (CBD COP15 — bridges mining + agri-food-security + cultural-heritage)",
        "fields": [
          ("indicatorId", "string", True),
          ("countryIso3", "string", True),
          ("gbfTarget", "string", True, None, "target 1-23"),
          ("indicatorCode", "string", True, None, "A.1 / A.2 / B.1 etc"),
          ("valueNumeric", "number", False),
          ("unit", "string", False),
          ("baselineValue", "number", False),
          ("targetValue2030", "number", False),
          ("reportedYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("progressTier", "if valueNumeric != null and baselineValue != null and targetValue2030 != null and (valueNumeric - baselineValue) / (targetValue2030 - baselineValue) >= 0.7 then \"on_track\" else if valueNumeric != null and baselineValue != null and targetValue2030 != null and (valueNumeric - baselineValue) / (targetValue2030 - baselineValue) >= 0.3 then \"partial\" else \"off_track\"", ["off_track","partial","on_track"]),
      },
      {
        "name": "declareProtectedArea",
        "desc": "30x30 protected area declaration (WDPA — bridges mining + water + cultural-heritage)",
        "fields": [
          ("areaId", "string", True, None, "WDPA ID"),
          ("countryIso3", "string", True),
          ("iucnCategory", "string", False, ["ia","ib","ii","iii","iv","v","vi","not_assigned","oecm"]),
          ("governance", "string", False, ["state","shared","private","indigenous_community"]),
          ("areaHectares", "number", True),
          ("marineArea", "boolean", False),
          ("designatedAt", "string", True),
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
