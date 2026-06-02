#!/usr/bin/env python3
"""Wave 38 bridges — merger / heritage / IMEO / GDST / battery passport."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "merger-review",
    "app": "mergerReview",
    "methods": [
      {
        "name": "notifyTransaction",
        "desc": "HSR / EUMR / SAMR merger notification (bridges antitrust-dma + global-tax + lei)",
        "fields": [
          ("notificationId", "string", True),
          ("acquirerLei", "string", False),
          ("targetLei", "string", False),
          ("jurisdictions", "string", True, None, "comma: us_hsr,eu_mr,uk_cma,cn_samr,jp_jftc,kr_kftc,in_cci,br_cade,au_accc"),
          ("transactionValueUsd", "number", False),
          ("sector", "string", False),
          ("filingPhase", "string", True, ["phase_1","phase_2","pre_notification","simplified","full"]),
          ("notifiedAt", "string", True),
        ],
        "classify": ("complexityTier", "if filingPhase = \"phase_2\" or filingPhase = \"full\" then \"in_depth\" else if filingPhase = \"pre_notification\" then \"engagement\" else \"simplified\"", ["simplified","engagement","in_depth"]),
      },
      {
        "name": "recordRemedy",
        "desc": "Merger clearance remedy / commitment",
        "fields": [
          ("remedyId", "string", True),
          ("notificationVid", "string", True, None, "bridges notifyTransaction"),
          ("remedyKind", "string", True, ["divestiture","licensing","firewall","conduct","interoperability","carve_out","monitoring_trustee","behavioural"]),
          ("outcome", "string", True, ["cleared_unconditional","cleared_with_remedies","prohibited","withdrawn","referred"]),
          ("remedyScopeDescription", "string", False),
          ("decidedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "intangible-heritage",
    "app": "intangibleHeritage",
    "methods": [
      {
        "name": "listIchElement",
        "desc": "UNESCO Intangible Heritage / Memory of the World listing (bridges cultural-heritage + language-preservation + indigenous-rights)",
        "fields": [
          ("elementId", "string", True),
          ("elementName", "string", True),
          ("countryIso3", "string", True),
          ("domain", "string", True, ["oral_traditions","performing_arts","social_practices","nature_knowledge","traditional_craftsmanship"]),
          ("listType", "string", True, ["representative","urgent_safeguarding","good_safeguarding_practices","mow"]),
          ("inscribedYear", "integer", False),
          ("communityLei", "string", False),
          ("inscribedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordOralHistoryArchive",
        "desc": "Oral history / community archive record (bridges language-preservation + cultural-heritage + bbnj-highseas DSI)",
        "fields": [
          ("archiveId", "string", True),
          ("elementVid", "string", True, None, "bridges listIchElement"),
          ("stewardLei", "string", False),
          ("languageId", "string", False),
          ("durationMinutes", "number", False),
          ("mediaType", "string", True, ["audio","video","transcript","annotation","interactive_map"]),
          ("licenseSpdx", "string", False),
          ("consentModel", "string", False, ["community_consent","individual_consent","traditional_knowledge_label","cc0","all_rights_reserved"]),
          ("archivedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "methane-tracker",
    "app": "methaneTracker",
    "methods": [
      {
        "name": "reportEmissionEvent",
        "desc": "IMEO / MARS / EDF MethaneSAT plume observation (bridges climate-carbon-market + hydrogen-economy + agri-food-security)",
        "fields": [
          ("eventId", "string", True),
          ("source", "string", True, ["oil_gas","coal","landfill","livestock","rice_paddy","wetland","permafrost","wastewater"]),
          ("locationIso3", "string", True),
          ("locationLat", "number", False),
          ("locationLon", "number", False),
          ("emissionKgPerHour", "number", True),
          ("detectionPlatform", "string", True, ["tropomi","methanesat","carbonmapper","emit","sentinel5p","ghgsat","ground"]),
          ("operatorLei", "string", False),
          ("observedAt", "string", True),
        ],
        "classify": ("plumeTier", "if emissionKgPerHour >= 10000 then \"super_emitter\" else if emissionKgPerHour >= 1000 then \"large\" else if emissionKgPerHour >= 100 then \"moderate\" else \"background\"", ["background","moderate","large","super_emitter"]),
      },
      {
        "name": "flagMitigationAction",
        "desc": "Mitigation action / MARS alert response",
        "fields": [
          ("actionId", "string", True),
          ("eventVid", "string", True, None, "bridges reportEmissionEvent"),
          ("operatorLei", "string", False),
          ("actionKind", "string", True, ["shut_in","equipment_repair","vent_to_flare","ldar_upgrade","abandoned_well_plug","livestock_diet","manure_digester","landfill_capture"]),
          ("reductionKgPerHour", "number", False),
          ("responseHours", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "seafood-traceability",
    "app": "seafoodTraceability",
    "methods": [
      {
        "name": "recordKdeEvent",
        "desc": "GDST 1.1 / UNSCEFACT seafood KDE event (bridges fisheries-iuu + customs-clearance + biosecurity + biodiversity-gbf)",
        "fields": [
          ("eventId", "string", True),
          ("kdeType", "string", True, ["catch","landing","processing","aggregation","shipment","sale_to_consumer"]),
          ("speciesAsfis", "string", True, None, "FAO ASFIS 3-alpha"),
          ("weightKg", "number", False),
          ("gearType", "string", False),
          ("vesselImo", "string", False),
          ("faoArea", "string", False),
          ("recordingPartyLei", "string", False),
          ("occurredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagChainOfCustodyBreak",
        "desc": "Chain of custody break / species substitution (bridges fisheries-iuu + consumer-protection)",
        "fields": [
          ("breakId", "string", True),
          ("eventVid", "string", False, None, "bridges recordKdeEvent"),
          ("breakKind", "string", True, ["species_substitution","origin_mislabeling","weight_mismatch","certificate_forgery","record_gap","iuu_association"]),
          ("lossKg", "number", False),
          ("detectedAt", "string", True),
        ],
        "classify": ("severityTier", "if breakKind = \"iuu_association\" or breakKind = \"certificate_forgery\" then \"severe\" else if breakKind = \"species_substitution\" or breakKind = \"origin_mislabeling\" then \"significant\" else \"minor\"", ["minor","significant","severe"]),
      },
    ],
  },
  {
    "slug": "battery-passport",
    "app": "batteryPassport",
    "methods": [
      {
        "name": "registerPassport",
        "desc": "EU Battery Passport (Reg 2023/1542 — bridges ev-charging-ocpp + critical-minerals + slsa-supply-chain + forced-labor)",
        "fields": [
          ("passportId", "string", True),
          ("manufacturerLei", "string", False),
          ("batteryCategory", "string", True, ["ev","lmt","industrial","sli","stationary","portable"]),
          ("chemistry", "string", True, ["lfp","nmc","nca","lto","lmfp","sodium_ion","solid_state","lithium_metal"]),
          ("capacityKwh", "number", False),
          ("recycledCobaltPct", "number", False),
          ("recycledLithiumPct", "number", False),
          ("recycledNickelPct", "number", False),
          ("cradleToGateKgCo2e", "number", False),
          ("supplyChainDiligenceUri", "string", False, None, "bridges open-forced-labor + critical-minerals"),
          ("registeredAt", "string", True),
        ],
        "classify": ("circularityTier", "if recycledCobaltPct != null and recycledCobaltPct >= 20 then \"high_recycled\" else if recycledCobaltPct != null and recycledCobaltPct >= 5 then \"mid_recycled\" else \"virgin_heavy\"", ["virgin_heavy","mid_recycled","high_recycled"]),
      },
      {
        "name": "logSecondLifeTransfer",
        "desc": "Second-life / recycle transfer (bridges chemicals-management + textile-circularity)",
        "fields": [
          ("transferId", "string", True),
          ("passportVid", "string", True, None, "bridges registerPassport"),
          ("recipientLei", "string", False),
          ("useCase", "string", True, ["second_life_stationary","second_life_bulk","recycling","disposal"]),
          ("stateOfHealthPct", "number", False),
          ("transferredAt", "string", True),
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
