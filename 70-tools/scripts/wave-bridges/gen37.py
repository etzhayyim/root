#!/usr/bin/env python3
"""Wave 37 bridges — peat / CRC digital / GST / blue economy / IGS."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "peat-wetland",
    "app": "peatWetland",
    "methods": [
      {
        "name": "recordPeatStock",
        "desc": "Peat / wetland carbon stock (Ramsar / Global Peatlands Initiative — bridges soil-carbon + forestry-mrv + biodiversity-gbf + coastal-slr)",
        "fields": [
          ("stockId", "string", True),
          ("siteName", "string", True),
          ("countryIso3", "string", True),
          ("wetlandType", "string", True, ["bog","fen","mire","mangrove","tidal_marsh","swamp_forest","seagrass","floodplain"]),
          ("areaHectares", "number", True),
          ("peatDepthM", "number", False),
          ("carbonStockTonnesHa", "number", False),
          ("ramsarListed", "boolean", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("conservationPriorityTier", "if ramsarListed = true then \"international\" else if wetlandType = \"mangrove\" or wetlandType = \"seagrass\" then \"blue_carbon\" else \"standard\"", ["standard","blue_carbon","international"]),
      },
      {
        "name": "flagDegradation",
        "desc": "Peat drainage / fire / conversion event",
        "fields": [
          ("eventId", "string", True),
          ("stockVid", "string", True, None, "bridges recordPeatStock"),
          ("driver", "string", True, ["drainage_agriculture","drainage_palm","fire","extraction","coastal_development","aquaculture","pollution"]),
          ("hectaresLost", "number", False),
          ("co2eEmittedTonnes", "number", False),
          ("forestryMrvVid", "string", False, None, "bridges open-forestry-mrv"),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "crc-children-digital",
    "app": "crcChildrenDigital",
    "methods": [
      {
        "name": "recordComplianceReport",
        "desc": "UN CRC General Comment 25 digital environment (bridges digital-identity + misinformation-observatory + icpen-consumer + ai-governance)",
        "fields": [
          ("reportId", "string", True),
          ("countryIso3", "string", True),
          ("reportingCycle", "string", True, None, "CRC periodic review cycle"),
          ("pillar", "string", True, ["access","non_discrimination","best_interests","life_survival","right_to_be_heard","privacy","protection_from_harm","education","culture","health","identity"]),
          ("indicatorScore", "integer", False),
          ("evidenceUrl", "string", False),
          ("submittedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAgeGateIncident",
        "desc": "Age verification / children's data incident (bridges data-broker-registry + digital-identity + misinformation-observatory)",
        "fields": [
          ("incidentId", "string", True),
          ("platformLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("ageGateMethod", "string", False, ["self_declaration","id_check","facial_age_estimation","biometric_match","parent_consent","zero_knowledge_proof"]),
          ("incidentKind", "string", True, ["bypass","misclassification","data_overreach","denial_of_service","discrimination","coppa_violation","gdpr_article8_violation"]),
          ("affectedMinors", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if incidentKind = \"coppa_violation\" or incidentKind = \"gdpr_article8_violation\" or incidentKind = \"data_overreach\" then \"systemic\" else if affectedMinors != null and affectedMinors >= 100000 then \"mass_impact\" else \"targeted\"", ["targeted","mass_impact","systemic"]),
      },
    ],
  },
  {
    "slug": "unfccc-gst",
    "app": "unfcccGst",
    "methods": [
      {
        "name": "recordNdcProgress",
        "desc": "UNFCCC NDC / biennial transparency report (bridges climate-carbon-market + eu-cbam + sdg-reporting + sovereign-debt)",
        "fields": [
          ("reportId", "string", True),
          ("partyIso3", "string", True),
          ("ndcCycle", "integer", True),
          ("gwpBasis", "string", False, ["ar5","ar6"]),
          ("reductionTargetPct", "number", False),
          ("baselineYear", "integer", False),
          ("sectorCoverage", "string", False, None, "comma: energy,industry,agriculture,forestry,waste,transport,buildings"),
          ("financeNeedUsdBn", "number", False),
          ("submittedAt", "string", True),
        ],
        "classify": ("ambitionTier", "if reductionTargetPct != null and reductionTargetPct >= 55 then \"high_ambition\" else if reductionTargetPct != null and reductionTargetPct >= 30 then \"moderate\" else \"low\"", ["low","moderate","high_ambition"]),
      },
      {
        "name": "flagImplementationGap",
        "desc": "GST implementation gap (bridges climate-adaptation-finance + ocha-funding + migrant-worker-welfare)",
        "fields": [
          ("gapId", "string", True),
          ("reportVid", "string", True, None, "bridges recordNdcProgress"),
          ("gapCategory", "string", True, ["finance","technology_transfer","capacity_building","adaptation","loss_damage","just_transition","carbon_markets"]),
          ("requiredActionsDescription", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "blue-economy",
    "app": "blueEconomy",
    "methods": [
      {
        "name": "recordSectorIndicator",
        "desc": "OECD Blue Economy / SDG 14 indicator (bridges fisheries-iuu + coastal-slr + bbnj-highseas + maritime-piracy)",
        "fields": [
          ("indicatorId", "string", True),
          ("countryIso3", "string", True),
          ("sector", "string", True, ["fisheries","aquaculture","shipping","tourism","offshore_energy","biotech","seabed_mining","coastal_protection"]),
          ("metricName", "string", True),
          ("valueNumeric", "number", False),
          ("unit", "string", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBlueFinanceFlow",
        "desc": "Blue bond / blue finance instrument (bridges sovereign-debt + climate-adaptation-finance + cat-bond-ils)",
        "fields": [
          ("flowId", "string", True),
          ("instrument", "string", True, ["blue_bond","blue_loan","blue_equity","parametric_reef","debt_for_ocean_swap"]),
          ("issuerLei", "string", False),
          ("principalUsd", "number", True),
          ("useOfProceeds", "string", False, None, "comma: fisheries_sustainability,coastal_resilience,mpa_management,plastic_reduction,sustainable_shipping"),
          ("sovereignIso3", "string", False),
          ("catBondVid", "string", False, None, "bridges open-cat-bond-ils"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "insurance-guarantee",
    "app": "insuranceGuarantee",
    "methods": [
      {
        "name": "recordScheme",
        "desc": "Insurance guarantee scheme / policyholder protection (bridges insurance-underwriter + cat-bond-ils + sovereign-debt)",
        "fields": [
          ("schemeId", "string", True),
          ("countryIso3", "string", True),
          ("operatorLei", "string", False),
          ("coverageLine", "string", True, ["life","nonlife","motor_compulsory","travel_compulsory","health","reinsurance","workers_comp"]),
          ("coverageCapUsd", "number", False),
          ("fundingModel", "string", False, ["ex_ante","ex_post","hybrid","pay_as_you_go"]),
          ("establishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInsolvency",
        "desc": "Insurer insolvency / resolution (bridges cat-bond-ils + sovereign-debt + migrant-worker-welfare)",
        "fields": [
          ("insolvencyId", "string", True),
          ("insurerLei", "string", True),
          ("schemeVid", "string", False, None, "bridges recordScheme"),
          ("policyCountAffected", "integer", False),
          ("unpaidClaimsUsd", "number", False),
          ("resolutionKind", "string", True, ["portfolio_transfer","run_off","liquidation","bail_in","state_aid"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if unpaidClaimsUsd != null and unpaidClaimsUsd >= 1000000000 then \"systemic\" else if policyCountAffected != null and policyCountAffected >= 100000 then \"major\" else \"limited\"", ["limited","major","systemic"]),
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
