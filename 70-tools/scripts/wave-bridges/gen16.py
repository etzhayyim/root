#!/usr/bin/env python3
"""Wave 16 — 2nd-order aggregator/chain bridges (85 → 90 projects)."""
import json
from pathlib import Path

REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "commodity-flow-aggregate",
    "app": "commodityFlowAggregate",
    "methods": [
      {
        "name": "rollupTradeWindow",
        "desc": "Rollup commodity-trade + physical-delivery + critical-minerals per window",
        "fields": [
          ("rollupId", "string", True),
          ("windowStart", "string", True),
          ("windowEnd", "string", True),
          ("hsCode", "string", False, None, "bridges open-hs"),
          ("materialClassificationVid", "string", False, None, "bridges open-critical-minerals"),
          ("tradeCount", "integer", True),
          ("physicalDeliveredBbl", "number", False),
          ("totalValueUsd", "number", False),
        ],
        "classify": ("volumeTier", "if totalValueUsd != null and totalValueUsd >= 1000000000 then \"mega\" else if totalValueUsd != null and totalValueUsd >= 100000000 then \"large\" else \"normal\"", ["normal","large","mega"]),
      },
      {
        "name": "flagDivergence",
        "desc": "Paper vs physical divergence (commodity-trade vs commodity-physical-delivery)",
        "fields": [
          ("divergenceId", "string", True),
          ("rollupVid", "string", True, None, "bridges rollupTradeWindow"),
          ("paperVolumeBbl", "number", True),
          ("physicalVolumeBbl", "number", True),
          ("divergenceRatio", "number", True, None, "paper/physical"),
          ("flaggedAt", "string", True),
        ],
        "classify": ("anomalyTier", "if divergenceRatio >= 100 then \"extreme\" else if divergenceRatio >= 20 then \"significant\" else \"normal\"", ["normal","significant","extreme"]),
      },
    ],
  },
  {
    "slug": "maritime-compliance-dashboard",
    "app": "maritimeComplianceDashboard",
    "methods": [
      {
        "name": "scoreVessel",
        "desc": "Per-vessel compliance score (port-of-call + biosec-cert + crew-welfare + forced-labor)",
        "fields": [
          ("scoreId", "string", True),
          ("imo", "string", True),
          ("pscDetentionCount", "integer", False),
          ("welfareBreachCount", "integer", False),
          ("forcedLaborFlagCount", "integer", False),
          ("bwmCertValid", "boolean", False),
          ("cursorMonth", "string", True, None, "YYYY-MM"),
        ],
        "classify": ("complianceTier", "if forcedLaborFlagCount != null and forcedLaborFlagCount >= 1 then \"sanction_risk\" else if pscDetentionCount != null and pscDetentionCount >= 2 then \"watchlist\" else if welfareBreachCount != null and welfareBreachCount >= 1 then \"monitoring\" else \"clear\"", ["clear","monitoring","watchlist","sanction_risk"]),
      },
      {
        "name": "issueChartererAlert",
        "desc": "Alert chartering party (broker-charter) re vessel compliance",
        "fields": [
          ("alertId", "string", True),
          ("scoreVid", "string", True, None, "bridges scoreVessel"),
          ("charterVid", "string", False, None, "bridges open-broker-charter"),
          ("chartererLei", "string", False),
          ("alertReason", "string", True, ["detention","welfare","forced_labor","cert_expiry","multi"]),
          ("alertedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "climate-value-chain",
    "app": "climateValueChain",
    "methods": [
      {
        "name": "linkScope3Emission",
        "desc": "Scope 3 emissions trace (commodity-trade → asia-refinery → carbon-market)",
        "fields": [
          ("linkId", "string", True),
          ("commodityTradeVid", "string", False, None, "bridges open-commodity-trade"),
          ("refineryReceiptVid", "string", False, None, "bridges open-asia-refinery"),
          ("carbonCreditVid", "string", False, None, "bridges open-climate-carbon-market"),
          ("reportingLei", "string", False),
          ("tonnesCo2eGross", "number", True),
          ("tonnesCo2eOffset", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("mitigationTier", "if tonnesCo2eOffset != null and tonnesCo2eOffset >= tonnesCo2eGross then \"net_zero\" else if tonnesCo2eOffset != null and tonnesCo2eOffset >= tonnesCo2eGross * 0.5 then \"partial_offset\" else \"unoffset\"", ["unoffset","partial_offset","net_zero"]),
      },
      {
        "name": "flagGreenwashing",
        "desc": "Flag potential greenwashing (offset quality mismatch)",
        "fields": [
          ("flagId", "string", True),
          ("linkVid", "string", True, None, "bridges linkScope3Emission"),
          ("esgRatingVid", "string", False, None, "bridges open-esg-risk-rating"),
          ("creditQualityTier", "string", False, ["tier_1","tier_2","tier_3"]),
          ("claimedNeutrality", "boolean", True),
          ("flaggedAt", "string", True),
        ],
        "classify": ("riskTier", "if claimedNeutrality = true and creditQualityTier = \"tier_3\" then \"high\" else if claimedNeutrality = true and creditQualityTier = \"tier_2\" then \"moderate\" else \"low\"", ["low","moderate","high"]),
      },
    ],
  },
  {
    "slug": "ai-supply-chain",
    "app": "aiSupplyChain",
    "methods": [
      {
        "name": "traceCompute",
        "desc": "AI compute infra trace (critical-minerals → semiconductor → ai-governance)",
        "fields": [
          ("traceId", "string", True),
          ("modelVid", "string", False, None, "bridges open-ai-governance registerModel"),
          ("mineralClassificationVid", "string", False, None, "bridges open-critical-minerals"),
          ("gpuVendorLei", "string", False),
          ("gpuModel", "string", False),
          ("trainingPetaflopDays", "number", False),
          ("datacenterIso3", "string", False),
          ("tracedAt", "string", True),
        ],
        "classify": ("dependencyTier", "if trainingPetaflopDays != null and trainingPetaflopDays >= 10000 then \"frontier\" else if trainingPetaflopDays != null and trainingPetaflopDays >= 100 then \"production\" else \"research\"", ["research","production","frontier"]),
      },
      {
        "name": "flagSupplyRisk",
        "desc": "Flag AI supply-chain risk (critical-mineral concentration + cyber-incident at chip fab)",
        "fields": [
          ("flagId", "string", True),
          ("traceVid", "string", True, None, "bridges traceCompute"),
          ("cyberIncidentVid", "string", False, None, "bridges open-cyber-incident"),
          ("concentrationVid", "string", False, None, "bridges open-critical-minerals recordConcentration"),
          ("affectedModelsCount", "integer", False),
          ("flaggedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "arctic-traffic-forecast",
    "app": "arcticTrafficForecast",
    "methods": [
      {
        "name": "forecastSeason",
        "desc": "NSR/NWP season forecast (arctic-nsr + carrier-schedule + freight-rate + climate)",
        "fields": [
          ("forecastId", "string", True),
          ("route", "string", True, ["NSR","NWP","TRANSPOLAR"]),
          ("forecastYear", "integer", True),
          ("iceExtentKm2", "number", False),
          ("expectedTransitCount", "integer", False),
          ("avgFreightRateUsdTeu", "number", False),
          ("co2ReductionVsSuezPct", "number", False),
          ("publishedAt", "string", True),
        ],
        "classify": ("demandTier", "if expectedTransitCount != null and expectedTransitCount >= 100 then \"high\" else if expectedTransitCount != null and expectedTransitCount >= 30 then \"moderate\" else \"low\"", ["low","moderate","high"]),
      },
      {
        "name": "recordPilotSubsidy",
        "desc": "Government pilot subsidy for NSR / NWP (cofog expenditure bridge)",
        "fields": [
          ("subsidyId", "string", True),
          ("forecastVid", "string", True, None, "bridges forecastSeason"),
          ("cofogExpenditureVid", "string", False, None, "bridges open-cofog"),
          ("jurisdictionIso3", "string", True),
          ("subsidyUsd", "number", True),
          ("recipientLei", "string", False),
          ("effectiveFrom", "string", True),
          ("effectiveUntil", "string", False),
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
    """Assemble column list from method fields + classify outputs."""
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
                seen.add(col)
                cols.append((col, "varchar", ""))
    # tail cols
    for c in [("status","varchar",""),("created_at","varchar",""),("owner_did","varchar",""),("sensitivity_ord","int",""),("org_id","varchar",""),("user_id","varchar",""),("actor_id","varchar","")]:
        if c[0] not in seen:
            cols.append(c); seen.add(c[0])
    return cols


def gen_lexicon(actor, method):
    nsid = f"com.etzhayyim.apps.{actor['app']}.{method['name']}"
    props = {}; required = []
    for f in method["fields"]:
        name, ftype, req = f[0], f[1], f[2]
        enum = f[3] if len(f)>3 else None
        desc = f[4] if len(f)>4 else None
        p = {"type": ftype}
        if enum: p["enum"] = enum
        if desc: p["description"] = desc
        if ftype=="string" and name.endswith("At"): p["format"]="datetime"
        props[name] = p
        if req: required.append(name)
    out_props = {"ok":{"type":"boolean"},"vertexId":{"type":"string"},"instanceKey":{"type":"integer"},"error":{"type":"string"}}
    if method.get("classify"):
        col,_,enum = method["classify"]
        out_props[col] = {"type":"string","enum":enum}
    return {"lexicon":1,"id":nsid,"defs":{"main":{"type":"procedure","description":method["desc"],
        "input":{"encoding":"application/json","schema":{"type":"object","required":required,"properties":props}},
        "output":{"encoding":"application/json","schema":{"type":"object","properties":out_props}}}}}


def gen_bpmn(actor, method):
    slug = actor["slug"]
    table = f"vertex_open_{slug.replace('-','_')}"
    proc_id = f"open_{slug.replace('-','_')}_{snake(method['name'])}"
    action = f"open.{actor['app']}.{method['name']}"
    vparts = ["vertex_id: vertexId"]
    for f in method["fields"]:
        name = f[0]; col = snake(name)
        vparts.append(f"{col}: {name}")
    if method.get("classify"):
        col, expr, _ = method["classify"]
        snake_col = snake(col) if any(c.isupper() for c in col) else col
        vparts.append(f"{snake_col}: {expr}")
    vparts += ['status: "active"','created_at: string(now())','owner_did: callerDid','sensitivity_ord: 1','org_id: callerDid','user_id: callerDid',f'actor_id: "sys.bpmn.open-{slug}"']
    feel = "{" + ", ".join(vparts) + "}"
    xml_feel = feel.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_{proc_id}" targetNamespace="https://etzhayyim.com/bpmn/open-{slug}" exporter="hand-written" exporterVersion="1.0">
  <bpmn:process id="{proc_id}" name="{method['name']}" isExecutable="true">
    <bpmn:startEvent id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>
    <bpmn:serviceTask id="Task_Save" name="save">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;{table}&quot;" target="table"/><zeebe:input source="={xml_feel}" target="values"/><zeebe:input source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>
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
    slug = actor["slug"]; table = f"vertex_open_{slug.replace('-','_')}"
    cols = build_ddl_cols(actor["methods"])
    body = ",\n  ".join(f"{c[0]} {c[1]}{' '+c[2] if c[2] else ''}" for c in cols)
    return f"CREATE TABLE IF NOT EXISTS {table} (\n  {body}\n);\n"


for a in ACTORS:
    bpmn_dir = REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    lex_dir = REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bpmn_dir.mkdir(parents=True, exist_ok=True); lex_dir.mkdir(parents=True, exist_ok=True)
    for m in a["methods"]:
        (lex_dir/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bpmn_dir/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    print(gen_ddl(a))
