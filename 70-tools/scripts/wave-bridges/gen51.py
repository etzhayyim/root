#!/usr/bin/env python3
"""Wave 51 bridges — digital-euro / PET / one-health / nature-markets / fusion."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "digital-euro-brics",
    "app": "digitalEuroBrics",
    "methods": [
      {
        "name": "recordCorridor",
        "desc": "Cross-border CBDC corridor (digital euro / BRICS Pay / mBridge — bridges cbdc + fatf-travel-rule + instant-payments + sovereign-debt)",
        "fields": [
          ("corridorId", "string", True),
          ("senderCountryIso3", "string", True),
          ("receiverCountryIso3", "string", True),
          ("scheme", "string", True, ["digital_euro","brics_pay","mbridge","agora","sibos_jade","pix_pace"]),
          ("bridgeProtocol", "string", False, ["iso_20022_enhanced","cbdc_native","hashed_tlock","atomic_swap"]),
          ("settlementTimeSec", "number", False),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSovereigntyConcern",
        "desc": "Monetary sovereignty / cybersecurity concern (bridges sovereign-debt + ofac-sanctions + antitrust-dma)",
        "fields": [
          ("concernId", "string", True),
          ("corridorVid", "string", True, None, "bridges recordCorridor"),
          ("concernKind", "string", True, ["monetary_sovereignty","sanctions_evasion","privacy","cyber","geopolitical_fragmentation","intermediation_risk"]),
          ("regulatorsInvolved", "string", False),
          ("flaggedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "pet-privacy",
    "app": "petPrivacy",
    "methods": [
      {
        "name": "registerDeployment",
        "desc": "Privacy-enhancing technology deployment (ENISA PETs / UKICO / NIST — bridges data-adequacy + precision-medicine + fhir-health-data + quantum-safe-crypto)",
        "fields": [
          ("deploymentId", "string", True),
          ("operatorLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("petFamily", "string", True, ["differential_privacy","federated_learning","homomorphic_encryption","secure_multiparty_computation","zero_knowledge_proof","trusted_execution","k_anonymity","synthetic_data"]),
          ("useCase", "string", False, ["health","finance","advertising","census","government","telecom","cross_border"]),
          ("epsilonBudget", "number", False, None, "DP epsilon"),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAccuracyPrivacyTradeoff",
        "desc": "Accuracy-vs-privacy tradeoff / re-identification incident (bridges cyber-incident + ai-governance + data-adequacy)",
        "fields": [
          ("tradeoffId", "string", True),
          ("deploymentVid", "string", True, None, "bridges registerDeployment"),
          ("accuracyDeltaPct", "number", False),
          ("reidentificationRiskTier", "string", False, ["negligible","low","medium","high","breached"]),
          ("remedyRequired", "string", False, ["tighten_epsilon","federated","aggregate","suppress","algorithmic_audit","k_anon_bump"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "one-health",
    "app": "oneHealth",
    "methods": [
      {
        "name": "recordSurveillanceEvent",
        "desc": "One Health surveillance event (Quadripartite FAO/WHO/WOAH/UNEP — bridges pandemic-preparedness + amr-surveillance + biodiversity-gbf + livestock-antibiotics)",
        "fields": [
          ("eventId", "string", True),
          ("pathogenName", "string", True),
          ("interface", "string", True, ["human_animal_domestic","human_animal_wildlife","human_environment","animal_environment","vector_multi_host","food_chain"]),
          ("countryIso3", "string", True),
          ("reportedBy", "string", False, ["fao","who","woah","unep","cdc","ecdc","aquis_mu"]),
          ("zoonoticConfirmed", "boolean", False),
          ("casesCount", "integer", False),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSpilloverRisk",
        "desc": "Spillover risk signal (SpilloverAI / Global Virome Project — bridges pandemic-preparedness + cites-wildlife + biodiversity-gbf)",
        "fields": [
          ("signalId", "string", True),
          ("eventVid", "string", False, None, "bridges recordSurveillanceEvent"),
          ("hostTaxonomy", "string", True),
          ("geoClusterIso3", "string", False),
          ("driverKind", "string", False, ["deforestation","wildlife_trade","livestock_intensification","climate","urban_peri_urban","migration"]),
          ("reservoirConfidence", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("riskTier", "if reservoirConfidence != null and reservoirConfidence >= 0.8 then \"imminent\" else if reservoirConfidence != null and reservoirConfidence >= 0.5 then \"elevated\" else \"monitor\"", ["monitor","elevated","imminent"]),
      },
    ],
  },
  {
    "slug": "nature-markets",
    "app": "natureMarkets",
    "methods": [
      {
        "name": "registerBiodiversityCredit",
        "desc": "Biodiversity / nature credit issuance (IAPB / Verra Nature Framework / Plan Vivo — bridges biodiversity-gbf + forestry-mrv + blue-carbon-mrv + land-tenure)",
        "fields": [
          ("creditId", "string", True),
          ("issuerLei", "string", False),
          ("methodology", "string", True, ["iapb_framework","verra_nature_framework","plan_vivo","gef_2030","mangrove_carbon_plus","accu_biodiversity"]),
          ("metricBasis", "string", True, ["mean_species_abundance","habitat_hectares","condition","extinction_risk","cop15_indicator"]),
          ("unitsIssued", "integer", True),
          ("indigenousBenefitSharingPct", "number", False),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDoubleClaim",
        "desc": "Double-claim / greenwashing / stacking concern (bridges climate-value-chain + cdr-verification + esg-risk-rating)",
        "fields": [
          ("flagId", "string", True),
          ("creditVid", "string", True, None, "bridges registerBiodiversityCredit"),
          ("issueKind", "string", True, ["double_claim","carbon_nature_stack","no_additionality","baseline_manipulation","leakage","permanence"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if issueKind = \"double_claim\" or issueKind = \"no_additionality\" then \"severe\" else if issueKind = \"baseline_manipulation\" or issueKind = \"leakage\" then \"significant\" else \"moderate\"", ["moderate","significant","severe"]),
      },
    ],
  },
  {
    "slug": "fusion-energy",
    "app": "fusionEnergy",
    "methods": [
      {
        "name": "registerProject",
        "desc": "Fusion energy project (ITER / SPARC / STEP / KSTAR / EAST / CFETR — bridges iaea-safeguards + hydrogen-economy + critical-minerals + power-grid-interconnect)",
        "fields": [
          ("projectId", "string", True),
          ("operatorLei", "string", False),
          ("projectName", "string", True),
          ("approach", "string", True, ["tokamak","stellarator","inertial","magneto_inertial","field_reversed","spheromak","z_pinch"]),
          ("countryIso3", "string", True),
          ("targetQ", "number", False, None, "target gain"),
          ("targetNetMw", "number", False),
          ("milestoneYear", "integer", False),
          ("announcedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagTritiumSupply",
        "desc": "Tritium supply / lithium supply constraint (bridges critical-minerals + iaea-safeguards + hydrogen-economy)",
        "fields": [
          ("flagId", "string", True),
          ("projectVid", "string", True, None, "bridges registerProject"),
          ("material", "string", True, ["tritium","li6_enriched","beryllium","tungsten","high_temperature_superconductor","neodymium"]),
          ("supplyShortKg", "number", False),
          ("bottleneckKind", "string", False, ["cansl_production","enrichment","mining","processing","sanctions","dual_use"]),
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
            if ftype == "integer" and any(k in col for k in ["count","doses_per","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued"]):
                sql_t = "bigint"
            else:
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
