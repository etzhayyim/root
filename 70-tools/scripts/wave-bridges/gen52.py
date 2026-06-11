#!/usr/bin/env python3
"""Wave 52 bridges — pandemic-prep / amr / critical-minerals / sovereign-debt / forestry-mrv.

Each bridges into a previously-disconnected Wave 51 vertex:
- pandemic-preparedness ↔ one-health.recordSurveillanceEvent
- amr-surveillance ↔ one-health.recordSurveillanceEvent, livestock-antibiotics
- critical-minerals ↔ fusion-energy.flagTritiumSupply
- sovereign-debt ↔ digital-euro-brics.recordCorridor
- forestry-mrv ↔ nature-markets.registerBiodiversityCredit
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "pandemic-prep",
    "app": "pandemicPrep",
    "methods": [
      {
        "name": "recordPrepProgram",
        "desc": "Pandemic preparedness program (WHO PPR / 100 Days Mission / CEPI — bridges one-health + fhir-health-data + vaccine-equity)",
        "fields": [
          ("programId", "string", True),
          ("leadOrgLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("programKind", "string", True, ["surveillance","vaccine_platform","therapeutic_stockpile","diagnostic_capacity","medical_countermeasure","genomic_readiness","clinical_trial_network"]),
          ("pathogenFamily", "string", False, ["coronavirus","influenza","filovirus","arenavirus","paramyxovirus","flavivirus","bunyavirus","disease_x"]),
          ("fundingMusd", "number", False),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCoverageGap",
        "desc": "Preparedness coverage gap (bridges one-health.flagSpilloverRisk + vaccine-equity + amr-surveillance)",
        "fields": [
          ("gapId", "string", True),
          ("programVid", "string", True, None, "bridges recordPrepProgram"),
          ("spilloverSignalVid", "string", False, None, "bridges one-health.flagSpilloverRisk"),
          ("gapKind", "string", True, ["lmic_access","cold_chain","workforce","genomic_sequencing","regulatory_path","countermeasure_stockpile","ppe","indigenous_reach"]),
          ("severityTier", "string", False, ["minor","moderate","significant","severe"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "amr-surveillance",
    "app": "amrSurveillance",
    "methods": [
      {
        "name": "recordResistanceSample",
        "desc": "AMR isolate surveillance (GLASS / EARS-Net / JVARM / FAO InFARM — bridges one-health + livestock-antibiotics + hospital-infection)",
        "fields": [
          ("sampleId", "string", True),
          ("pathogenSpecies", "string", True),
          ("sourceCompartment", "string", True, ["human","animal_food_producing","animal_companion","environment","food","water"]),
          ("countryIso3", "string", True),
          ("antibioticClass", "string", True, ["beta_lactam","carbapenem","fluoroquinolone","polymyxin","glycopeptide","macrolide","aminoglycoside","tetracycline","oxazolidinone"]),
          ("resistancePhenotype", "string", True, ["susceptible","intermediate","resistant","mdr","xdr","pdr"]),
          ("mlsTypeOrStLike", "string", False),
          ("collectedAt", "string", True),
        ],
        "classify": ("alertTier", "if resistancePhenotype = \"pdr\" then \"critical\" else if resistancePhenotype = \"xdr\" or resistancePhenotype = \"mdr\" then \"high\" else if resistancePhenotype = \"resistant\" then \"watch\" else \"routine\"", ["routine","watch","high","critical"]),
      },
      {
        "name": "flagStewardshipBreach",
        "desc": "Antibiotic stewardship / prescribing breach (bridges livestock-antibiotics + hospital-infection + one-health)",
        "fields": [
          ("breachId", "string", True),
          ("sampleVid", "string", False, None, "bridges recordResistanceSample"),
          ("breachKind", "string", True, ["inappropriate_prescribing","non_therapeutic_livestock_use","counterfeit_antibiotic","over_the_counter_sale","missed_source_control","unregulated_disposal"]),
          ("facilityLei", "string", False),
          ("jurisdictionIso3", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "critical-minerals",
    "app": "criticalMinerals",
    "methods": [
      {
        "name": "registerMineralFlow",
        "desc": "Critical mineral production / trade flow (USGS / IEA / EU CRMA — bridges fusion-energy.flagTritiumSupply + green-transition + ev-supply-chain)",
        "fields": [
          ("flowId", "string", True),
          ("mineral", "string", True, ["lithium","cobalt","nickel","graphite","rare_earth_ndpr","rare_earth_dyTb","platinum","palladium","copper","manganese","tellurium","germanium","gallium","indium","tungsten","beryllium","lithium6","tritium"]),
          ("stageKind", "string", True, ["mining","concentrate","refining","chemical","cathode","magnet","alloy","recycling"]),
          ("producerCountryIso3", "string", True),
          ("consumerCountryIso3", "string", False),
          ("volumeTonnes", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagExportControlRisk",
        "desc": "Export control / chokepoint risk (bridges fusion-energy.flagTritiumSupply + ofac-sanctions + wassenaar)",
        "fields": [
          ("riskId", "string", True),
          ("flowVid", "string", True, None, "bridges registerMineralFlow"),
          ("fusionFlagVid", "string", False, None, "bridges fusion-energy.flagTritiumSupply"),
          ("controlRegime", "string", True, ["wassenaar","nsg","china_export_license","us_entity_list","eu_dual_use","japan_foreign_exchange","export_quota"]),
          ("concentrationHhi", "number", False, None, "supply-side HHI"),
          ("reportedAt", "string", True),
        ],
        "classify": ("chokepointTier", "if concentrationHhi != null and concentrationHhi >= 5000 then \"extreme\" else if concentrationHhi != null and concentrationHhi >= 2500 then \"high\" else \"moderate\"", ["moderate","high","extreme"]),
      },
    ],
  },
  {
    "slug": "sovereign-debt",
    "app": "sovereignDebt",
    "methods": [
      {
        "name": "recordDebtRestructure",
        "desc": "Sovereign debt restructuring (IMF Common Framework / Paris Club / London Club — bridges digital-euro-brics.recordCorridor + fx-swap-lines + imf-sdr)",
        "fields": [
          ("restructureId", "string", True),
          ("debtorCountryIso3", "string", True),
          ("frameworkKind", "string", True, ["imf_common_framework","paris_club","london_club","brady_bond","cacs_holdout","ex_ante_suspension","hipc","private_bilateral"]),
          ("principalHaircutPct", "number", False),
          ("nominalMusd", "number", False),
          ("majorCreditors", "string", False),
          ("announcedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCreditorCoordination",
        "desc": "Creditor coordination concern (bridges digital-euro-brics.recordCorridor + ofac-sanctions + antitrust-dma)",
        "fields": [
          ("concernId", "string", True),
          ("restructureVid", "string", True, None, "bridges recordDebtRestructure"),
          ("corridorVid", "string", False, None, "bridges digital-euro-brics.recordCorridor"),
          ("issueKind", "string", True, ["holdout_creditor","comparability_of_treatment","collateralized_swap","hidden_debt","non_paris_bilateral","cross_default_trigger","transparency_gap"]),
          ("intensityTier", "string", False, ["watch","elevated","severe"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "forestry-mrv",
    "app": "forestryMrv",
    "methods": [
      {
        "name": "registerForestProject",
        "desc": "REDD+/ARR/IFM project with MRV (Verra VCS / ART-TREES / Plan Vivo / GCF — bridges nature-markets.registerBiodiversityCredit + land-tenure + blue-carbon-mrv)",
        "fields": [
          ("projectId", "string", True),
          ("registryKind", "string", True, ["verra_vcs","art_trees","gold_standard","plan_vivo","accu","jcm","gcf","national_redd"]),
          ("projectKind", "string", True, ["redd_plus","arr","ifm","wrc","agroforestry","mangrove_restore","peatland_rewetting","urban_forest"]),
          ("countryIso3", "string", True),
          ("areaHectares", "number", False),
          ("expectedTco2eYearly", "number", False),
          ("biodiversityCreditVid", "string", False, None, "bridges nature-markets.registerBiodiversityCredit"),
          ("indigenousTitleHolder", "string", False),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBaselineDrift",
        "desc": "Baseline drift / additionality / leakage concern (bridges nature-markets.flagDoubleClaim + cdr-verification + climate-value-chain)",
        "fields": [
          ("driftId", "string", True),
          ("projectVid", "string", True, None, "bridges registerForestProject"),
          ("doubleClaimVid", "string", False, None, "bridges nature-markets.flagDoubleClaim"),
          ("concernKind", "string", True, ["baseline_manipulation","no_additionality","leakage","permanence","reversal_event","monitoring_gap","jurisdictional_mismatch"]),
          ("overcreditPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if overcreditPct != null and overcreditPct >= 50 then \"severe\" else if overcreditPct != null and overcreditPct >= 20 then \"significant\" else \"moderate\"", ["moderate","significant","severe"]),
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


for i, a in enumerate(ACTORS, start=1):
    bd=REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    ld=REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bd.mkdir(parents=True,exist_ok=True); ld.mkdir(parents=True,exist_ok=True)
    for m in a["methods"]:
        (ld/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bd/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    ddl = gen_ddl(a)
    out = Path(f"/tmp/wave13/w52_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
