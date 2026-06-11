#!/usr/bin/env python3
"""Wave 40 bridges — blue carbon / UASC / APA / OTel / refugee livelihood."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "blue-carbon-mrv",
    "app": "blueCarbonMrv",
    "methods": [
      {
        "name": "recordStockEstimate",
        "desc": "Blue carbon stock estimate (mangrove / seagrass / saltmarsh — bridges peat-wetland + coastal-slr + climate-carbon-market + bbnj-highseas)",
        "fields": [
          ("estimateId", "string", True),
          ("habitatType", "string", True, ["mangrove","seagrass","saltmarsh","tidal_flat"]),
          ("countryIso3", "string", True),
          ("areaHectares", "number", True),
          ("organicCarbonDensityTonnesHa", "number", False),
          ("methodology", "string", False, ["ipcc_2013_wetlands","verra_vm0033","gs_blue_natural_capital","plan_vivo"]),
          ("remoteSensingPlatform", "string", False, ["landsat","sentinel","planet","drone","field"]),
          ("measuredYear", "integer", True),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "issueBlueCarbonCredit",
        "desc": "Blue carbon credit issuance (bridges climate-carbon-market + cdr-verification + indigenous-rights)",
        "fields": [
          ("creditId", "string", True),
          ("estimateVid", "string", True, None, "bridges recordStockEstimate"),
          ("methodologyCode", "string", True),
          ("tonnesCo2e", "number", True),
          ("permanenceYears", "integer", False),
          ("communityBenefitSharingPct", "number", False),
          ("indigenousTerritoryVid", "string", False, None, "bridges open-indigenous-rights"),
          ("issuedAt", "string", True),
        ],
        "classify": ("integrityTier", "if communityBenefitSharingPct != null and communityBenefitSharingPct >= 50 then \"high\" else if communityBenefitSharingPct != null and communityBenefitSharingPct >= 20 then \"moderate\" else \"low\"", ["low","moderate","high"]),
      },
    ],
  },
  {
    "slug": "uasc-protection",
    "app": "uascProtection",
    "methods": [
      {
        "name": "registerUasc",
        "desc": "Unaccompanied / Separated Child refugee registration (bridges refugee-unhcr + crc-children-digital + labour-mobility + migrant-worker-welfare)",
        "fields": [
          ("registrationId", "string", True),
          ("originIso3", "string", True),
          ("countryOfRegIso3", "string", True),
          ("category", "string", True, ["unaccompanied","separated","other_vulnerable"]),
          ("ageBand", "string", True, ["0_4","5_11","12_14","15_17"]),
          ("genderBand", "string", False, ["girl","boy","other","unknown"]),
          ("statusKind", "string", True, ["best_interest_assessment","family_tracing","interim_care","foster_care","special_protection"]),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPushbackIncident",
        "desc": "Pushback / refoulement / age-assessment abuse (bridges press-freedom + forced-labor + migrant-worker-welfare)",
        "fields": [
          ("incidentId", "string", True),
          ("registrationVid", "string", False, None, "bridges registerUasc"),
          ("borderType", "string", True, ["land","sea","air","internal"]),
          ("respondentStateIso3", "string", True),
          ("violation", "string", True, ["refoulement","disputed_age_assessment","detention","family_separation","denied_asylum_procedure","failure_to_identify"]),
          ("childrenAffected", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if violation = \"refoulement\" or violation = \"family_separation\" then \"severe\" else if violation = \"detention\" or violation = \"denied_asylum_procedure\" then \"significant\" else \"concern\"", ["concern","significant","severe"]),
      },
    ],
  },
  {
    "slug": "advance-tax-ruling",
    "app": "advanceTaxRuling",
    "methods": [
      {
        "name": "recordApa",
        "desc": "Advance Pricing Agreement / advance tax ruling (bridges global-tax + tax-transparency + merger-review)",
        "fields": [
          ("apaId", "string", True),
          ("jurisdictionsInvolved", "string", True, None, "comma ISO3"),
          ("taxpayerLei", "string", False),
          ("apaKind", "string", True, ["unilateral","bilateral","multilateral","rollback"]),
          ("subjectTransaction", "string", True, ["tangibles","services","intangibles","financial","cost_sharing","profit_split","digital"]),
          ("coveredYears", "integer", False),
          ("effectiveFrom", "string", True),
          ("expiresAt", "string", False),
        ],
        "classify": None,
      },
      {
        "name": "flagMap",
        "desc": "Mutual Agreement Procedure MAP case (bridges sovereign-debt + global-tax + tax-transparency)",
        "fields": [
          ("mapId", "string", True),
          ("apaVid", "string", False, None, "bridges recordApa"),
          ("jurisdictionsInvolved", "string", True, None, "comma ISO3"),
          ("issueCategory", "string", True, ["transfer_pricing","treaty_interpretation","dividends_interest","permanent_establishment","withholding","pillar2"]),
          ("openingDate", "string", True),
          ("closureStatus", "string", False, ["pending","agreed","withdrawn","arbitration","denied"]),
          ("resolutionMonths", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("complexityTier", "if resolutionMonths != null and resolutionMonths >= 36 then \"prolonged\" else if resolutionMonths != null and resolutionMonths >= 18 then \"standard\" else \"rapid\"", ["rapid","standard","prolonged"]),
      },
    ],
  },
  {
    "slug": "otel-observability",
    "app": "otelObservability",
    "methods": [
      {
        "name": "registerTelemetryPipeline",
        "desc": "OpenTelemetry pipeline registry (bridges oss-vuln + cyber-resilience-stress + slsa-supply-chain + ai-governance)",
        "fields": [
          ("pipelineId", "string", True),
          ("operatorLei", "string", False),
          ("signalTypes", "string", True, None, "comma: traces,metrics,logs,profiles"),
          ("collectorVersion", "string", False),
          ("exporters", "string", False, None, "comma: otlp,prometheus,jaeger,zipkin,loki,datadog,honeycomb"),
          ("protocol", "string", False, ["otlp_http","otlp_grpc","prometheus_remote_write","loki_push"]),
          ("samplingStrategy", "string", False, ["always_on","always_off","parent_based","probabilistic","tail_based","head_adaptive"]),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDataSovereigntyIncident",
        "desc": "Telemetry data sovereignty / PII leak (bridges data-adequacy + cyber-incident + ai-governance)",
        "fields": [
          ("incidentId", "string", True),
          ("pipelineVid", "string", True, None, "bridges registerTelemetryPipeline"),
          ("issueKind", "string", True, ["pii_in_logs","cross_border_leak","unauthenticated_collector","schema_drift","sampling_bias","model_inference_capture"]),
          ("affectedRecords", "integer", False),
          ("dataAdequacyVid", "string", False, None, "bridges open-data-adequacy"),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if issueKind = \"cross_border_leak\" or issueKind = \"pii_in_logs\" then \"critical\" else if issueKind = \"unauthenticated_collector\" or issueKind = \"model_inference_capture\" then \"severe\" else \"moderate\"", ["moderate","severe","critical"]),
      },
    ],
  },
  {
    "slug": "refugee-livelihood",
    "app": "refugeeLivelihood",
    "methods": [
      {
        "name": "registerFinanceProgram",
        "desc": "Refugee livelihood / financial inclusion program (bridges refugee-unhcr + ocha-funding + migrant-worker-welfare + uasc-protection)",
        "fields": [
          ("programId", "string", True),
          ("sponsorLei", "string", False),
          ("hostIso3", "string", True),
          ("financialProduct", "string", True, ["microloan","savings","remittance","cash_assistance","agriculture_voucher","cash_plus","digital_wallet","insurance"]),
          ("beneficiariesCount", "integer", False),
          ("avgLoanUsd", "number", False),
          ("digitalIdLinked", "boolean", False, None, "bridges open-digital-identity"),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "reportImpactMetric",
        "desc": "Livelihood outcome metric (bridges sdg-reporting + ocha-funding)",
        "fields": [
          ("metricId", "string", True),
          ("programVid", "string", True, None, "bridges registerFinanceProgram"),
          ("livelihoodsSustainedPct", "number", False),
          ("employmentRatePct", "number", False),
          ("businessesStartedCount", "integer", False),
          ("householdIncomeDeltaPct", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("outcomeTier", "if livelihoodsSustainedPct != null and livelihoodsSustainedPct >= 70 and employmentRatePct != null and employmentRatePct >= 50 then \"strong\" else if livelihoodsSustainedPct != null and livelihoodsSustainedPct >= 40 then \"emerging\" else \"nascent\"", ["nascent","emerging","strong"]),
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
