#!/usr/bin/env python3
"""Wave 34 bridges — a11y / CDR / rail OSJD / cable repair / data adequacy."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "digital-accessibility",
    "app": "digitalAccessibility",
    "methods": [
      {
        "name": "recordConformance",
        "desc": "WCAG 2.2 / EN 301 549 / Section 508 / EAA conformance audit (bridges antitrust-dma + ai-governance + misinformation-observatory)",
        "fields": [
          ("auditId", "string", True),
          ("productLei", "string", False),
          ("standard", "string", True, ["wcag_2_1","wcag_2_2","wcag_3","en_301_549","section_508","eaa","jis_x_8341","gb_t_37668"]),
          ("conformanceLevel", "string", True, ["a","aa","aaa","not_compliant"]),
          ("criteriaPassed", "integer", False),
          ("criteriaFailed", "integer", False),
          ("auditMethod", "string", False, ["automated","manual_expert","user_testing","hybrid"]),
          ("auditedAt", "string", True),
        ],
        "classify": ("complianceTier", "if conformanceLevel = \"aaa\" then \"exemplary\" else if conformanceLevel = \"aa\" then \"compliant\" else if conformanceLevel = \"a\" then \"partial\" else \"non_compliant\"", ["non_compliant","partial","compliant","exemplary"]),
      },
      {
        "name": "flagAccessibilityComplaint",
        "desc": "EAA / ADA / JIS complaint / structured negotiation (bridges antitrust-dma)",
        "fields": [
          ("complaintId", "string", True),
          ("auditVid", "string", False, None, "bridges recordConformance"),
          ("complainantCategory", "string", True, ["individual","ngo","enforcement_body","competitor"]),
          ("disabilityCategory", "string", False, ["visual","hearing","motor","cognitive","speech","multiple"]),
          ("outcome", "string", False, ["remediated","settled","fined","dismissed","escalated","ongoing"]),
          ("fineUsd", "number", False),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cdr-verification",
    "app": "cdrVerification",
    "methods": [
      {
        "name": "recordRemovalEvent",
        "desc": "Carbon removal verification (ERW / DAC / BECCS — bridges climate-carbon-market + geoengineering-registry + climate-value-chain)",
        "fields": [
          ("eventId", "string", True),
          ("operatorLei", "string", False),
          ("technologyClass", "string", True, ["DAC","BECCS","ERW","OAF","ocean_alkalinity","biochar","reforestation","DACCS","mineralization"]),
          ("tonnesCo2eGross", "number", True),
          ("verifierLei", "string", False),
          ("mrvMethodology", "string", False, ["puro_earth","isometric","verra_vm0044","gs_soils","cdr_fi_v0"]),
          ("storageDurability", "string", True, ["geologic_1000yr","mineral_10000yr","biological_100yr","biological_30yr"]),
          ("verifiedAt", "string", True),
        ],
        "classify": ("durabilityTier", "if storageDurability = \"geologic_1000yr\" or storageDurability = \"mineral_10000yr\" then \"durable\" else if storageDurability = \"biological_100yr\" then \"long_term\" else \"short_term\"", ["short_term","long_term","durable"]),
      },
      {
        "name": "flagReversalRisk",
        "desc": "Reversal risk signal (fire / permafrost / leakage — bridges extreme-weather-attribution + geoengineering-registry)",
        "fields": [
          ("riskId", "string", True),
          ("eventVid", "string", True, None, "bridges recordRemovalEvent"),
          ("reversalCause", "string", True, ["fire","flood","drought","disease","harvest","seepage","saturation","permafrost"]),
          ("tonnesReversed", "number", False),
          ("bufferPoolClaimed", "boolean", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "rail-cross-border",
    "app": "railCrossBorder",
    "methods": [
      {
        "name": "recordCorridorFlow",
        "desc": "International rail corridor flow (OTIF / OSJD / CIM / SMGS — bridges carrier-schedule + customs-clearance + logistics-lastmile + urban-mobility)",
        "fields": [
          ("flowId", "string", True),
          ("operatorLei", "string", False),
          ("corridorName", "string", True),
          ("originIso3", "string", True),
          ("destinationIso3", "string", True),
          ("regimeDocument", "string", True, ["cim_smgs","cim","smgs","uz_smgs","amtrak","intercity"]),
          ("gaugeProfile", "string", False, ["standard","broad_1520","broad_1676","cape","iberian","dual","metre"]),
          ("wagonCount", "integer", False),
          ("tonnesNet", "number", False),
          ("transitHours", "number", False),
          ("periodMonth", "string", True),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInteropFailure",
        "desc": "Interoperability failure (gauge change / ERTMS / ETCS — bridges space-weather + cyber-incident)",
        "fields": [
          ("failureId", "string", True),
          ("flowVid", "string", True, None, "bridges recordCorridorFlow"),
          ("failureKind", "string", True, ["gauge_mismatch","etcs_level","power_supply","traffic_mgmt","customs_doc","brakes","signalling"]),
          ("delayHours", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cable-repair-fleet",
    "app": "cableRepairFleet",
    "methods": [
      {
        "name": "registerRepairVessel",
        "desc": "Cable ship / repair agreement (ACMA / MECMA / Yokohama Zone — bridges telecom-infra + carrier-fleet + biosecurity)",
        "fields": [
          ("vesselId", "string", True),
          ("imo", "string", True),
          ("operatorLei", "string", False),
          ("agreement", "string", True, ["ACMA","MECMA","Yokohama","NAZ","NCS","EAR","SAR"]),
          ("homeportUnlocode", "string", False),
          ("cableCapabilities", "string", False, None, "comma: submarine_splice,plough,rov,jet,trench,survey"),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "logRepairMission",
        "desc": "Cable fault repair mission (bridges telecom-infra flagCableFault)",
        "fields": [
          ("missionId", "string", True),
          ("vesselVid", "string", True, None, "bridges registerRepairVessel"),
          ("faultVid", "string", False, None, "bridges open-telecom-infra flagCableFault"),
          ("mobilizationDays", "number", False),
          ("onSiteDays", "number", False),
          ("restoreDays", "number", False),
          ("conditions", "string", False, ["calm","rough","storm","ice","tropical"]),
          ("missionOutcome", "string", True, ["full_repair","partial_repair","survey_only","aborted"]),
          ("completedAt", "string", False),
        ],
        "classify": ("efficiencyTier", "if restoreDays != null and restoreDays <= 14 then \"rapid\" else if restoreDays != null and restoreDays <= 45 then \"standard\" else \"prolonged\"", ["prolonged","standard","rapid"]),
      },
    ],
  },
  {
    "slug": "data-adequacy",
    "app": "dataAdequacy",
    "methods": [
      {
        "name": "recordTransferMechanism",
        "desc": "Cross-border data transfer mechanism (GDPR adequacy / APEC CBPR / PIPL Standard Contract — bridges mica-crypto + data-broker-registry + tax-transparency)",
        "fields": [
          ("mechanismId", "string", True),
          ("originRegime", "string", True, ["eu_gdpr","uk_gdpr","swiss_fadp","cn_pipl","kr_pipa","jp_appi","br_lgpd","ca_pipeda","us_state"]),
          ("destinationIso3", "string", True),
          ("mechanism", "string", True, ["adequacy","sccs","bcrs","cbpr","csa","approved_certification","exception_consent","exception_vital_interest"]),
          ("dataCategories", "string", False, None, "comma: personal,sensitive,financial,health,biometric,children,employee"),
          ("dataVolumeMonthly", "integer", False),
          ("effectiveFrom", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSupervisoryAction",
        "desc": "Supervisory authority action (bridges antitrust-dma + data-broker-registry)",
        "fields": [
          ("actionId", "string", True),
          ("mechanismVid", "string", True, None, "bridges recordTransferMechanism"),
          ("authority", "string", True, ["edpb","cnil","ico","bfdi","apd","acm","cac","pipc","ppc","opc","anpd","fpb"]),
          ("actionKind", "string", True, ["reprimand","fine","suspension","order_to_cease","certification_withdrawal","adequacy_reassessment"]),
          ("fineEur", "number", False),
          ("actedAt", "string", True),
        ],
        "classify": ("severityTier", "if actionKind = \"order_to_cease\" or actionKind = \"adequacy_reassessment\" then \"systemic\" else if actionKind = \"suspension\" or actionKind = \"certification_withdrawal\" then \"severe\" else \"moderate\"", ["moderate","severe","systemic"]),
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
