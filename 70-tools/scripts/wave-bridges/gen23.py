#!/usr/bin/env python3
"""Wave 23 bridges — PQC / space weather / deep-sea mining / global tax / misinformation."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "quantum-safe-crypto",
    "app": "quantumSafeCrypto",
    "methods": [
      {
        "name": "registerPqcMigration",
        "desc": "NIST PQC migration inventory (FIPS 203/204/205 — bridges cyber-compliance + ai-supply-chain + banking)",
        "fields": [
          ("migrationId", "string", True),
          ("operatorLei", "string", False),
          ("systemName", "string", True),
          ("cryptoAssetType", "string", True, ["rsa","ecdsa","ecdh","dsa","ml_kem","ml_dsa","slh_dsa","hash","hybrid"]),
          ("keyLengthBits", "integer", False),
          ("qRiskTier", "string", True, ["hnsk_critical","store_now_decrypt_later","tactical","low"]),
          ("targetPqcScheme", "string", False),
          ("targetCompletionYear", "integer", False),
          ("registeredAt", "string", True),
        ],
        "classify": ("urgencyTier", "if qRiskTier = \"hnsk_critical\" then \"immediate\" else if qRiskTier = \"store_now_decrypt_later\" then \"priority\" else if qRiskTier = \"tactical\" then \"planned\" else \"monitor\"", ["monitor","planned","priority","immediate"]),
      },
      {
        "name": "logHarvestNow",
        "desc": "Harvest-now-decrypt-later intelligence signal",
        "fields": [
          ("signalId", "string", True),
          ("migrationVid", "string", True, None, "bridges registerPqcMigration"),
          ("adversaryActorCode", "string", False, None, "MITRE ATT&CK group"),
          ("interceptionVector", "string", True, ["cable_tap","mitm","cloud_storage","routing","satellite","other"]),
          ("estimatedExposureRecords", "integer", False),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "space-weather",
    "app": "spaceWeather",
    "methods": [
      {
        "name": "reportGeomagneticStorm",
        "desc": "NOAA SWPC / ESA SSA geomagnetic storm (bridges telecom-infra + aviation-safety + space-traffic + airplane)",
        "fields": [
          ("eventId", "string", True),
          ("kpMax", "number", True, None, "planetary K-index 0-9"),
          ("gScale", "string", True, ["G1","G2","G3","G4","G5"]),
          ("sScale", "string", False, ["S1","S2","S3","S4","S5"]),
          ("rScale", "string", False, ["R1","R2","R3","R4","R5"]),
          ("startedAt", "string", True),
          ("peakedAt", "string", False),
          ("endedAt", "string", False),
        ],
        "classify": ("severityTier", "if gScale = \"G5\" or gScale = \"G4\" then \"extreme\" else if gScale = \"G3\" then \"strong\" else \"moderate\"", ["moderate","strong","extreme"]),
      },
      {
        "name": "flagInfrastructureImpact",
        "desc": "Space-weather infrastructure impact (grid / comms / GNSS / aviation)",
        "fields": [
          ("impactId", "string", True),
          ("eventVid", "string", True, None, "bridges reportGeomagneticStorm"),
          ("infraType", "string", True, ["power_grid","hf_comms","gnss","satellite","pipeline","aviation_polar","rail_signal"]),
          ("regionIso3", "string", False),
          ("outageMinutes", "integer", False),
          ("cableFaultVid", "string", False, None, "bridges open-telecom-infra flagCableFault"),
          ("airproxVid", "string", False, None, "bridges open-aviation-safety reportAirprox"),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "deep-sea-mining",
    "app": "deepSeaMining",
    "methods": [
      {
        "name": "issueIsaContract",
        "desc": "ISA exploration/exploitation contract (bridges critical-minerals + biodiversity-gbf + forced-labor)",
        "fields": [
          ("contractId", "string", True),
          ("sponsoringStateIso3", "string", True),
          ("contractorLei", "string", False),
          ("area", "string", True, ["CCZ","MAR","indian_ocean","south_atlantic","south_pacific","reserved_area","APEI"]),
          ("resource", "string", True, ["polymetallic_nodules","polymetallic_sulphides","cobalt_crusts"]),
          ("criticalMineralVid", "string", False, None, "bridges open-critical-minerals"),
          ("phase", "string", True, ["exploration","development","exploitation","suspended"]),
          ("areaKm2", "number", False),
          ("issuedAt", "string", True),
          ("expiresAt", "string", False),
        ],
        "classify": ("sensitivityTier", "if area = \"CCZ\" and resource = \"polymetallic_nodules\" then \"contested_high\" else if area = \"APEI\" or area = \"reserved_area\" then \"protected\" else \"contested\"", ["contested","contested_high","protected"]),
      },
      {
        "name": "reportEnvBaseline",
        "desc": "Environmental baseline / monitoring report (DeepCCZ / JPI Oceans)",
        "fields": [
          ("reportId", "string", True),
          ("contractVid", "string", True, None, "bridges issueIsaContract"),
          ("gbfProtectedVid", "string", False, None, "bridges open-biodiversity-gbf"),
          ("benthicDiversityIndex", "number", False),
          ("endemicSpeciesCount", "integer", False),
          ("sedimentPlumeRadiusKm", "number", False),
          ("noiseDbAt1m", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "global-tax",
    "app": "globalTax",
    "methods": [
      {
        "name": "reportPillar2Liability",
        "desc": "OECD Pillar 2 GloBE / QDMTT / IIR / UTPR (bridges lei + sovereign-debt + eu-cbam + esg-risk-rating)",
        "fields": [
          ("reportId", "string", True),
          ("ultimateParentLei", "string", True),
          ("jurisdictionIso3", "string", True),
          ("rule", "string", True, ["iir","utpr","qdmtt","gilti","btc","stss"]),
          ("effectiveTaxRatePct", "number", True),
          ("topUpTaxUsd", "number", False),
          ("revenueEur", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("coverageTier", "if effectiveTaxRatePct < 15 then \"top_up_due\" else \"compliant\"", ["compliant","top_up_due"]),
      },
      {
        "name": "flagProfitShifting",
        "desc": "BEPS profit-shifting pattern (Action 5/8-10/13 — bridges ofac-sanctions + lei)",
        "fields": [
          ("flagId", "string", True),
          ("reportVid", "string", True, None, "bridges reportPillar2Liability"),
          ("pattern", "string", True, ["harmful_preferential","tp_intangible","cost_contribution","hybrid_mismatch","digital_pe","treaty_shopping","interest_deduction"]),
          ("relatedPartyLei", "string", False),
          ("estimatedShiftedUsd", "number", False),
          ("flaggedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "misinformation-observatory",
    "app": "misinformationObservatory",
    "methods": [
      {
        "name": "logContentAssertion",
        "desc": "EU DSA / C2PA / ClaimReview content assertion (bridges ai-governance + election-integrity + cultural-heritage)",
        "fields": [
          ("assertionId", "string", True),
          ("contentUrl", "string", True),
          ("platformLei", "string", False),
          ("claimType", "string", True, ["deepfake","misleading_edit","manipulated_context","fabricated_source","satire_mislabeled","cheapfake","synthetic_text","synthetic_audio","synthetic_video"]),
          ("verdict", "string", True, ["true","mostly_true","mixture","mostly_false","false","unproven","out_of_context"]),
          ("aiModelVid", "string", False, None, "bridges open-ai-governance if AI-generated"),
          ("electionObservationVid", "string", False, None, "bridges open-election-integrity"),
          ("c2paManifest", "boolean", False),
          ("loggedAt", "string", True),
        ],
        "classify": ("harmTier", "if verdict = \"false\" and (claimType = \"deepfake\" or claimType = \"synthetic_video\") then \"severe\" else if verdict = \"false\" or verdict = \"mostly_false\" then \"elevated\" else \"monitor\"", ["monitor","elevated","severe"]),
      },
      {
        "name": "recordDsaTransparency",
        "desc": "EU DSA Article 24 transparency report (VLOP / VLOSE)",
        "fields": [
          ("reportId", "string", True),
          ("platformLei", "string", True),
          ("platformCategory", "string", True, ["vlop","vlose","regular"]),
          ("contentActionsCount", "integer", False),
          ("complaintsCount", "integer", False),
          ("appealsUpheldPct", "number", False),
          ("reportingPeriod", "string", True, None, "YYYY-HN"),
          ("publishedAt", "string", True),
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
