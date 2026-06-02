#!/usr/bin/env python3
"""Wave 50 bridges — pensions / crypto-derivatives / rural-broadband / carbon-tax / ai-worker-labor."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "pensions-dc",
    "app": "pensionsDc",
    "methods": [
      {
        "name": "recordFundMetric",
        "desc": "Defined contribution pension fund (OECD DC / EIOPA / PF IAIS — bridges sovereign-debt + esg-risk-rating + reit-transparency + insurance-guarantee)",
        "fields": [
          ("fundId", "string", True),
          ("trusteeLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("schemeType", "string", True, ["trust_based","contract_based","master_trust","gpp","sipp","us_401k","au_super","cl_afp","se_pps","nz_kiwi"]),
          ("aumUsd", "number", True),
          ("membersCount", "integer", False),
          ("defaultAssetAllocationEquityPct", "number", False),
          ("feeTerBp", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("feeTier", "if feeTerBp != null and feeTerBp <= 30 then \"low\" else if feeTerBp != null and feeTerBp <= 75 then \"moderate\" else \"high\"", ["low","moderate","high"]),
      },
      {
        "name": "flagInadequacy",
        "desc": "Replacement-rate / adequacy shortfall (bridges migrant-worker-welfare + housing-affordability + energy-poverty)",
        "fields": [
          ("reportId", "string", True),
          ("fundVid", "string", False, None, "bridges recordFundMetric"),
          ("countryIso3", "string", True),
          ("grossReplacementRatePct", "number", False),
          ("netReplacementRatePct", "number", False),
          ("oldAgePovertyRatePct", "number", False),
          ("genderGapPensionPct", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("adequacyTier", "if netReplacementRatePct != null and netReplacementRatePct >= 70 then \"adequate\" else if netReplacementRatePct != null and netReplacementRatePct >= 50 then \"marginal\" else \"inadequate\"", ["inadequate","marginal","adequate"]),
      },
    ],
  },
  {
    "slug": "crypto-derivatives",
    "app": "cryptoDerivatives",
    "methods": [
      {
        "name": "registerVenue",
        "desc": "Crypto derivative exchange / CCP (CFTC DCM / SFC ATS / FCA / MAS / ESMA MiCAR — bridges mica-crypto + fatf-travel-rule + psd3-open-finance + merger-review)",
        "fields": [
          ("venueId", "string", True),
          ("operatorLei", "string", False),
          ("regime", "string", True, ["cftc_dcm","sec_regulated","sfc_ats","fca","mas","bafin","jfsa","esma_micar","hk_vasp","abu_dhabi_fsra"]),
          ("productKinds", "string", True, None, "comma: perp,futures,options,swaps,structured,etf,spot"),
          ("ccpTier", "string", False, ["none","recognised","qualified_ccp","third_country"]),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordVolumeMetric",
        "desc": "Daily volume / OI / funding rate (bridges mica-crypto + blockchain-mev + antitrust-dma)",
        "fields": [
          ("metricId", "string", True),
          ("venueVid", "string", True, None, "bridges registerVenue"),
          ("periodDay", "string", True),
          ("notionalVolumeUsd", "number", False),
          ("openInterestUsd", "number", False),
          ("fundingRatePct", "number", False),
          ("uniqueTradersCount", "integer", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("activityTier", "if notionalVolumeUsd != null and notionalVolumeUsd >= 100000000000 then \"mega\" else if notionalVolumeUsd != null and notionalVolumeUsd >= 10000000000 then \"high\" else if notionalVolumeUsd != null and notionalVolumeUsd >= 1000000000 then \"moderate\" else \"low\"", ["low","moderate","high","mega"]),
      },
    ],
  },
  {
    "slug": "rural-broadband",
    "app": "ruralBroadband",
    "methods": [
      {
        "name": "registerDeployment",
        "desc": "Rural broadband deployment (FCC BEAD / DSIT UK / DG CNECT / MIC JP / DigitalIndia — bridges telecom-infra + energy-poverty + housing-affordability + sdg-reporting)",
        "fields": [
          ("deploymentId", "string", True),
          ("providerLei", "string", False),
          ("countryIso3", "string", True),
          ("program", "string", True, ["fcc_bead","dsit_uk","eu_gigabit","kdt_kor","mic_jp","pradhan_mantri_gramodaya","bnb_sg"]),
          ("technology", "string", True, ["ftth","fwa","leo_satellite","docsis_3_1","copper_fttc","mobile_5g_saam","mesh"]),
          ("premisesPassed", "integer", False),
          ("investmentUsd", "number", False),
          ("targetSpeedMbpsDown", "integer", False),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDigitalDivideGap",
        "desc": "Digital divide gap (affordability / adoption / gender / age — bridges digital-accessibility + crc-children-digital + mental-health-parity)",
        "fields": [
          ("gapId", "string", True),
          ("deploymentVid", "string", False, None, "bridges registerDeployment"),
          ("indicator", "string", True, ["affordability_1_2_basket","adoption_rate","gender_gap","age_gap","digital_skills","mobile_only","dark_spot_persist"]),
          ("valueNumeric", "number", False),
          ("benchmarkValue", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "carbon-tax",
    "app": "carbonTax",
    "methods": [
      {
        "name": "recordTaxInstrument",
        "desc": "Carbon tax / ETS-equivalent (World Bank CPD / OECD ETS / I4CE — bridges eu-cbam + climate-carbon-market + sovereign-debt + global-tax)",
        "fields": [
          ("instrumentId", "string", True),
          ("jurisdictionIso3", "string", True),
          ("instrumentKind", "string", True, ["carbon_tax","ets_cap_trade","fuel_tax_equiv","power_sector_carbon_charge","hybrid"]),
          ("coverageSectors", "string", False, None, "comma"),
          ("priceUsdTonneCo2e", "number", False),
          ("coverageShareGhgPct", "number", False),
          ("revenueUseCodes", "string", False, None, "comma: general_budget,climate_specific,green_fund,tax_reform,transfers_low_income,debt_reduction"),
          ("effectiveFrom", "string", True),
        ],
        "classify": ("ambitionTier", "if priceUsdTonneCo2e != null and priceUsdTonneCo2e >= 75 then \"high_ambition\" else if priceUsdTonneCo2e != null and priceUsdTonneCo2e >= 40 then \"moderate\" else \"low\"", ["low","moderate","high_ambition"]),
      },
      {
        "name": "flagCompetitivenessConcern",
        "desc": "Competitiveness / carbon leakage concern (bridges eu-cbam + wto-dispute + merger-review + green-steel)",
        "fields": [
          ("concernId", "string", True),
          ("instrumentVid", "string", True, None, "bridges recordTaxInstrument"),
          ("sectorIsic", "string", True),
          ("leakageRiskTier", "string", True, ["low","medium","high","extreme"]),
          ("eitcMeasureApplied", "string", False, ["free_allocation","rebate","border_adjustment","benchmarking","no_measure"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ai-worker-labor",
    "app": "aiWorkerLabor",
    "methods": [
      {
        "name": "recordDisplacementStudy",
        "desc": "AI-driven workforce displacement study (ILO / OECD / MIT / BLS — bridges gig-worker + just-transition + ai-governance + credential-portability)",
        "fields": [
          ("studyId", "string", True),
          ("publisherLei", "string", False),
          ("regionIso3", "string", False),
          ("occupationIsco", "string", False),
          ("exposureIndex", "number", False, None, "0-1 generative AI exposure"),
          ("automationRiskPct", "number", False),
          ("augmentationRiskPct", "number", False),
          ("jobsImpactedCount", "integer", False),
          ("timeHorizonYears", "integer", False),
          ("publishedAt", "string", True),
        ],
        "classify": ("impactTier", "if exposureIndex != null and exposureIndex >= 0.8 then \"high_exposure\" else if exposureIndex != null and exposureIndex >= 0.5 then \"moderate\" else \"limited\"", ["limited","moderate","high_exposure"]),
      },
      {
        "name": "flagCollectiveBargain",
        "desc": "Collective bargaining / AI clause / strike (bridges gig-worker + migrant-worker-welfare + antitrust-dma)",
        "fields": [
          ("actionId", "string", True),
          ("studyVid", "string", False, None, "bridges recordDisplacementStudy"),
          ("unionLei", "string", False),
          ("employerLei", "string", False),
          ("actionKind", "string", True, ["cba_ai_clause","strike","walkout","works_council","industry_framework","national_dialogue"]),
          ("aiProvisions", "string", False, None, "comma: consultation,training_fund,severance,data_rights,surveillance_limit,opt_out,right_to_human_review"),
          ("workersCovered", "integer", False),
          ("concludedAt", "string", True),
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
            if ftype == "integer" and any(k in col for k in ["count","doses_per","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises"]):
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
