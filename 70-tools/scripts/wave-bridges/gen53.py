#!/usr/bin/env python3
"""Wave 53 bridges — vaccine-equity / livestock-abx / ev-supply-chain / fx-swap-lines / blue-carbon-mrv.

Bridges Wave 52 open ends:
- vaccine-equity ↔ pandemicPrep.flagCoverageGap
- livestock-antibiotics ↔ amrSurveillance.flagStewardshipBreach
- ev-supply-chain ↔ criticalMinerals.registerMineralFlow + flagExportControlRisk
- fx-swap-lines ↔ sovereignDebt.recordDebtRestructure + digitalEuroBrics.recordCorridor
- blue-carbon-mrv ↔ forestryMrv.registerForestProject + natureMarkets.registerBiodiversityCredit
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "vaccine-equity",
    "app": "vaccineEquity",
    "methods": [
      {
        "name": "recordAllocation",
        "desc": "Vaccine / medical countermeasure allocation (COVAX / Gavi / CEPI / PAHO Revolving — bridges pandemicPrep.flagCoverageGap + lmic-access + cold-chain)",
        "fields": [
          ("allocationId", "string", True),
          ("mechanism", "string", True, ["covax","gavi","afro_avat","paho_revolving","bilateral","national_buy","donation","swap"]),
          ("recipientCountryIso3", "string", True),
          ("manufacturerLei", "string", False),
          ("productClass", "string", True, ["mrna","viral_vector","protein_subunit","inactivated","live_attenuated","monoclonal_ab","antiviral","diagnostic"]),
          ("dosesAllocated", "integer", True),
          ("deliveredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAccessGap",
        "desc": "LMIC access / dose sharing / IP waiver concern (bridges pandemicPrep.flagCoverageGap + trips-waiver + cold-chain)",
        "fields": [
          ("gapId", "string", True),
          ("allocationVid", "string", False, None, "bridges recordAllocation"),
          ("coverageGapVid", "string", False, None, "bridges pandemicPrep.flagCoverageGap"),
          ("concernKind", "string", True, ["lmic_shortfall","hoarding","ip_waiver_blocked","price_gouging","cold_chain_failure","tech_transfer_gap","wasted_doses"]),
          ("shortfallDoses", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "livestock-abx",
    "app": "livestockAbx",
    "methods": [
      {
        "name": "recordVeterinaryUse",
        "desc": "Veterinary antibiotic use (WOAH annual report / EMA ESVAC / FDA ADUFA — bridges amrSurveillance.flagStewardshipBreach + one-health + food-safety)",
        "fields": [
          ("reportId", "string", True),
          ("countryIso3", "string", True),
          ("animalCategory", "string", True, ["cattle_dairy","cattle_beef","swine","poultry_broiler","poultry_layer","aquaculture_salmon","aquaculture_shrimp","companion","sheep_goat"]),
          ("antibioticClass", "string", True, ["tetracycline","penicillin","macrolide","sulfonamide","aminoglycoside","fluoroquinolone","colistin","cephalosporin"]),
          ("indicationKind", "string", False, ["therapeutic","metaphylaxis","prophylactic","growth_promotion_banned"]),
          ("mgPerPcu", "number", False, None, "ESVAC PCU denominator"),
          ("reportedAt", "string", True),
        ],
        "classify": ("priorityTier", "if antibioticClass = \"colistin\" or antibioticClass = \"fluoroquinolone\" then \"hp_cia\" else if antibioticClass = \"cephalosporin\" or antibioticClass = \"macrolide\" then \"cia\" else \"standard\"", ["standard","cia","hp_cia"]),
      },
      {
        "name": "flagGrowthPromoter",
        "desc": "Banned / misused growth promoter signal (bridges amrSurveillance.flagStewardshipBreach + food-safety + trade-sanitary)",
        "fields": [
          ("flagId", "string", True),
          ("reportVid", "string", True, None, "bridges recordVeterinaryUse"),
          ("stewardshipBreachVid", "string", False, None, "bridges amrSurveillance.flagStewardshipBreach"),
          ("compoundName", "string", True),
          ("misuseKind", "string", True, ["banned_growth_promoter","off_label","unregulated_import","counterfeit","residue_violation","withdrawal_breach"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ev-supply-chain",
    "app": "evSupplyChain",
    "methods": [
      {
        "name": "registerBatteryCell",
        "desc": "EV battery cell / pack production (EU Battery Passport / IRA FEOC / chemistries — bridges criticalMinerals.registerMineralFlow + green-transition)",
        "fields": [
          ("cellId", "string", True),
          ("manufacturerLei", "string", False),
          ("chemistry", "string", True, ["ncm_811","ncm_622","ncm_532","nca","lfp","lmfp","lto","sodium_ion","solid_state","lithium_sulfur"]),
          ("capacityKwh", "number", False),
          ("factoryCountryIso3", "string", True),
          ("mineralFlowVid", "string", False, None, "bridges criticalMinerals.registerMineralFlow"),
          ("passportId", "string", False, None, "EU Battery Passport"),
          ("manufacturedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFeocRisk",
        "desc": "Foreign Entity of Concern (FEOC) / IRA §45X disqualification risk (bridges criticalMinerals.flagExportControlRisk + ira-tax-credit)",
        "fields": [
          ("riskId", "string", True),
          ("cellVid", "string", True, None, "bridges registerBatteryCell"),
          ("mineralRiskVid", "string", False, None, "bridges criticalMinerals.flagExportControlRisk"),
          ("feocJurisdictionIso3", "string", True),
          ("upstreamStage", "string", True, ["mining","refining","cathode_precursor","anode_graphite","cell_components","recycling","licensing_ip"]),
          ("equityPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("disqTier", "if equityPct != null and equityPct >= 25 then \"disqualifying\" else if equityPct != null and equityPct >= 10 then \"reviewable\" else \"monitor\"", ["monitor","reviewable","disqualifying"]),
      },
    ],
  },
  {
    "slug": "fx-swap-lines",
    "app": "fxSwapLines",
    "methods": [
      {
        "name": "recordSwapLine",
        "desc": "Central bank FX swap / repo line (Fed FIMA / ECB / BoJ / PBoC yuan swaps / ChiangMai — bridges sovereignDebt.recordDebtRestructure + digitalEuroBrics.recordCorridor)",
        "fields": [
          ("lineId", "string", True),
          ("providerCb", "string", True, ["fed","ecb","boj","boe","pboc","snb","rbi","cmim","imf_fcl","imf_psi"]),
          ("recipientCountryIso3", "string", True),
          ("currency", "string", True, ["usd","eur","jpy","cny","gbp","chf","inr","krw","sdr"]),
          ("notionalBusd", "number", False),
          ("termDays", "integer", False),
          ("activatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagLineStress",
        "desc": "Swap line drawdown / stigma / rollover concern (bridges sovereignDebt.flagCreditorCoordination + digitalEuroBrics.flagSovereigntyConcern)",
        "fields": [
          ("stressId", "string", True),
          ("lineVid", "string", True, None, "bridges recordSwapLine"),
          ("restructureVid", "string", False, None, "bridges sovereignDebt.recordDebtRestructure"),
          ("stressKind", "string", True, ["heavy_drawdown","stigma","rollover_risk","counterparty_credit","basis_widening","collateral_quality","unwind_order"]),
          ("intensityTier", "string", False, ["watch","elevated","acute"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "blue-carbon-mrv",
    "app": "blueCarbonMrv",
    "methods": [
      {
        "name": "registerBlueCarbonProject",
        "desc": "Mangrove / seagrass / saltmarsh blue carbon project (Verra VM0033 / Plan Vivo / GEF Blue Economy — bridges forestryMrv.registerForestProject + natureMarkets.registerBiodiversityCredit)",
        "fields": [
          ("projectId", "string", True),
          ("registryKind", "string", True, ["verra_vm0033","verra_vm0007","plan_vivo","gold_standard","art_trees","ocean_based","gcf_blue"]),
          ("ecosystem", "string", True, ["mangrove","seagrass","saltmarsh","kelp","macroalgae","tidal_flat","estuary"]),
          ("countryIso3", "string", True),
          ("areaHectares", "number", False),
          ("sequestrationTco2eYearly", "number", False),
          ("forestProjectVid", "string", False, None, "bridges forestryMrv.registerForestProject"),
          ("indigenousTenurePct", "number", False),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSeaLevelReversal",
        "desc": "Sea-level-rise / storm surge permanence risk (bridges forestryMrv.flagBaselineDrift + climate-adaptation)",
        "fields": [
          ("flagId", "string", True),
          ("projectVid", "string", True, None, "bridges registerBlueCarbonProject"),
          ("baselineDriftVid", "string", False, None, "bridges forestryMrv.flagBaselineDrift"),
          ("driverKind", "string", True, ["slr_submergence","storm_surge","cyclone","coastal_squeeze","dieback_disease","upstream_sediment_loss","aquaculture_conversion","oil_spill"]),
          ("reversalTco2e", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if reversalTco2e != null and reversalTco2e >= 100000 then \"catastrophic\" else if reversalTco2e != null and reversalTco2e >= 10000 then \"significant\" else \"moderate\"", ["moderate","significant","catastrophic"]),
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
            if ftype == "integer" and any(k in col for k in ["count","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued"]):
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
    out = Path(f"/tmp/wave13/w53_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
