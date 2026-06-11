#!/usr/bin/env python3
"""Wave 31 bridges — hydrogen / cat-bond / WWA / migrant / SLSA."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "hydrogen-economy",
    "app": "hydrogenEconomy",
    "methods": [
      {
        "name": "registerProject",
        "desc": "Hydrogen production/offtake (IEA HyLaw / HyResource — bridges climate-carbon-market + critical-minerals + power-grid-interconnect)",
        "fields": [
          ("projectId", "string", True),
          ("operatorLei", "string", False),
          ("countryIso3", "string", True),
          ("productionTier", "string", True, ["green_elec","blue_ccs","grey_natgas","turquoise_methane","pink_nuclear","white_geologic"]),
          ("capacityMtPerYear", "number", True),
          ("endUses", "string", True, None, "comma: ammonia,steel,refining,heavy_transport,blending,power,export"),
          ("commissioningYear", "integer", False),
          ("fidTaken", "boolean", False),
          ("registeredAt", "string", True),
        ],
        "classify": ("carbonTier", "if productionTier = \"green_elec\" or productionTier = \"pink_nuclear\" then \"low_carbon\" else if productionTier = \"blue_ccs\" then \"mid_carbon\" else \"high_carbon\"", ["low_carbon","mid_carbon","high_carbon"]),
      },
      {
        "name": "recordOfftakeAgreement",
        "desc": "Long-term offtake contract (HPA / HOA)",
        "fields": [
          ("agreementId", "string", True),
          ("projectVid", "string", True, None, "bridges registerProject"),
          ("offtakerLei", "string", False),
          ("annualVolumeKt", "number", True),
          ("priceUsdKg", "number", False),
          ("tenorYears", "integer", True),
          ("euRed3Compliant", "boolean", False),
          ("signedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cat-bond-ils",
    "app": "catBondIls",
    "methods": [
      {
        "name": "issueCatBond",
        "desc": "Catastrophe / ILS bond (bridges disaster-response + cyclone-prepo + climate-litigation + sovereign-debt)",
        "fields": [
          ("bondId", "string", True),
          ("sponsorLei", "string", False),
          ("triggerType", "string", True, ["indemnity","parametric","industry_loss","modeled_loss","hybrid"]),
          ("peril", "string", True, ["us_hurricane","us_earthquake","us_wildfire","jp_earthquake","jp_typhoon","eu_windstorm","cyber","pandemic","flood","mortality","longevity"]),
          ("principalUsd", "number", True),
          ("couponSpreadBps", "number", False),
          ("tenorYears", "number", True),
          ("disasterVid", "string", False, None, "bridges open-disaster-response (if linked)"),
          ("issuedAt", "string", True),
          ("maturesAt", "string", True),
        ],
        "classify": ("attachmentTier", "if triggerType = \"parametric\" then \"rapid\" else if triggerType = \"modeled_loss\" then \"medium\" else \"slow\"", ["slow","medium","rapid"]),
      },
      {
        "name": "recordPayout",
        "desc": "Trigger event + payout record",
        "fields": [
          ("payoutId", "string", True),
          ("bondVid", "string", True, None, "bridges issueCatBond"),
          ("triggerEventDescription", "string", True),
          ("payoutUsd", "number", True),
          ("payoutPct", "number", False),
          ("disasterVid", "string", False, None, "bridges open-disaster-response"),
          ("triggeredAt", "string", True),
        ],
        "classify": ("outcomeTier", "if payoutPct != null and payoutPct >= 100 then \"full_loss\" else if payoutPct != null and payoutPct >= 50 then \"partial\" else \"haircut\"", ["haircut","partial","full_loss"]),
      },
    ],
  },
  {
    "slug": "extreme-weather-attribution",
    "app": "extremeWeatherAttribution",
    "methods": [
      {
        "name": "publishAttribution",
        "desc": "WWA / ClimaMeter / NCAR extreme weather attribution study (bridges coastal-slr + agri-food-security + disaster-response + climate-litigation)",
        "fields": [
          ("studyId", "string", True),
          ("eventName", "string", True),
          ("eventType", "string", True, ["heatwave","drought","flood","wildfire","cyclone","cold_spell","rain_burst","marine_heatwave"]),
          ("regionM49", "string", True),
          ("eventStartedAt", "string", True),
          ("fractionAttributableRiskPct", "number", False, None, "FAR 0-100"),
          ("intensityIncreaseRatio", "number", False),
          ("confidenceBand", "string", False, ["low","medium","high","very_high"]),
          ("publishedAt", "string", True),
        ],
        "classify": ("signalTier", "if fractionAttributableRiskPct != null and fractionAttributableRiskPct >= 80 and confidenceBand = \"very_high\" then \"unequivocal\" else if fractionAttributableRiskPct != null and fractionAttributableRiskPct >= 50 then \"strong\" else if fractionAttributableRiskPct != null and fractionAttributableRiskPct >= 20 then \"moderate\" else \"weak\"", ["weak","moderate","strong","unequivocal"]),
      },
      {
        "name": "flagClimateLitigationUse",
        "desc": "Attribution used in climate litigation / liability / adaptation-finance claim",
        "fields": [
          ("useId", "string", True),
          ("studyVid", "string", True, None, "bridges publishAttribution"),
          ("litigationVid", "string", False, None, "bridges open-climate-litigation"),
          ("disasterVid", "string", False, None, "bridges open-disaster-response"),
          ("usageCategory", "string", True, ["legal_evidence","adaptation_claim","insurance_trigger","policy_brief","journalism"]),
          ("citedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "migrant-worker-welfare",
    "app": "migrantWorkerWelfare",
    "methods": [
      {
        "name": "recordWelfareFund",
        "desc": "Migrant worker welfare fund registry (GCC Wage Protection / Kafala reform / MoU — bridges labour-mobility + forced-labor + crew-welfare)",
        "fields": [
          ("fundId", "string", True),
          ("hostIso3", "string", True),
          ("originIso3", "string", False),
          ("mechanism", "string", True, ["wps","welfare_fund","grievance_platform","bla_escrow","insurance_pool"]),
          ("annualContributionsUsd", "number", False),
          ("coveredWorkersCount", "integer", False),
          ("labourCorridorVid", "string", False, None, "bridges open-labour-mobility"),
          ("establishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagWageTheft",
        "desc": "Wage theft complaint + resolution (bridges forced-labor + ofac-sanctions)",
        "fields": [
          ("complaintId", "string", True),
          ("fundVid", "string", True, None, "bridges recordWelfareFund"),
          ("employerLei", "string", False),
          ("amountOwedUsd", "number", True),
          ("workersAffected", "integer", True),
          ("resolutionStatus", "string", True, ["reported","mediation","paid_partial","paid_full","unresolved"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if workersAffected >= 100 or amountOwedUsd >= 500000 then \"systemic\" else if resolutionStatus = \"unresolved\" then \"chronic\" else \"incident\"", ["incident","chronic","systemic"]),
      },
    ],
  },
  {
    "slug": "slsa-supply-chain",
    "app": "slsaSupplyChain",
    "methods": [
      {
        "name": "registerAttestation",
        "desc": "SLSA / in-toto / sigstore provenance attestation (bridges oss-vuln + ai-supply-chain + cyber-compliance)",
        "fields": [
          ("attestationId", "string", True),
          ("builderId", "string", True),
          ("artifactDigest", "string", True, None, "sha256:..."),
          ("predicateType", "string", True, ["slsa_provenance_v1","in_toto_spdx","in_toto_cyclonedx","vsa","vcs_compromise"]),
          ("slsaLevel", "integer", True, None, "1-4"),
          ("sigstoreBundle", "boolean", False),
          ("publisherLei", "string", False),
          ("generatedAt", "string", True),
        ],
        "classify": ("trustTier", "if slsaLevel >= 4 then \"hermetic\" else if slsaLevel >= 3 then \"hardened\" else if slsaLevel >= 2 then \"reproducible\" else \"documented\"", ["documented","reproducible","hardened","hermetic"]),
      },
      {
        "name": "flagProvenanceFailure",
        "desc": "Verification failure / tampered attestation / stolen signing key",
        "fields": [
          ("failureId", "string", True),
          ("attestationVid", "string", False, None, "bridges registerAttestation"),
          ("failureKind", "string", True, ["signature_invalid","replay","tampered_digest","stolen_key","revoked_cert","unsigned"]),
          ("advisoryVid", "string", False, None, "bridges open-oss-vuln"),
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
