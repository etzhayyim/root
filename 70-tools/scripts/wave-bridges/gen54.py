#!/usr/bin/env python3
"""Wave 54 — trips-waiver / residue-mrl / ira-tax-credit / em-fx-reserves / coral-reef-bleaching.

Bridges Wave 53 open ends:
- trips-waiver ↔ vaccineEquity.flagAccessGap
- residue-mrl ↔ livestockAbx.flagGrowthPromoter
- ira-tax-credit ↔ evSupplyChain.flagFeocRisk
- em-fx-reserves ↔ fxSwapLines.flagLineStress
- coral-reef-bleaching ↔ blueCarbonMrv.flagSeaLevelReversal
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "trips-waiver",
    "app": "tripsWaiver",
    "methods": [
      {
        "name": "recordWaiverInvocation",
        "desc": "WTO TRIPS Art 31bis / Doha Declaration waiver invocation (bridges vaccineEquity.flagAccessGap + pharma-supply + ip-licensing)",
        "fields": [
          ("invocationId", "string", True),
          ("invokingCountryIso3", "string", True),
          ("productClass", "string", True, ["vaccine","therapeutic","diagnostic","ppe","medical_device","cancer_drug","antiviral","biosimilar"]),
          ("mechanism", "string", True, ["compulsory_license","government_use","parallel_import","art_31bis_export","emergency_exception","doha_flexibility"]),
          ("originPatentJurisdiction", "string", False),
          ("accessGapVid", "string", False, None, "bridges vaccineEquity.flagAccessGap"),
          ("invokedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRetaliationRisk",
        "desc": "Trade retaliation / §301 / adequacy downgrade concern (bridges vaccineEquity.flagAccessGap + ustr-section-301 + wto-dispute)",
        "fields": [
          ("flagId", "string", True),
          ("invocationVid", "string", True, None, "bridges recordWaiverInvocation"),
          ("retaliatorCountryIso3", "string", True),
          ("retaliationKind", "string", True, ["priority_watch_list","section_301_tariff","wto_dispute","bilateral_pressure","adequacy_downgrade","gsp_withdrawal","aid_conditionality"]),
          ("estimatedLossMusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "residue-mrl",
    "app": "residueMrl",
    "methods": [
      {
        "name": "recordMrlMeasurement",
        "desc": "Pesticide / veterinary drug MRL measurement (Codex CCPR / EU MRL / FDA / JECFA — bridges livestockAbx.flagGrowthPromoter + food-safety + rasff)",
        "fields": [
          ("measurementId", "string", True),
          ("compoundName", "string", True),
          ("compoundClass", "string", True, ["organophosphate","organochlorine","carbamate","pyrethroid","neonicotinoid","glyphosate","veterinary_antibiotic","hormone","anthelmintic","fungicide"]),
          ("matrix", "string", True, ["milk","egg","beef_muscle","beef_fat","pork","poultry","honey","fish","shrimp","fruit","vegetable","cereal","water"]),
          ("countryIso3", "string", True),
          ("concentrationUgKg", "number", True),
          ("codexMrlUgKg", "number", False),
          ("sampledAt", "string", True),
        ],
        "classify": ("complianceTier", "if concentrationUgKg != null and codexMrlUgKg != null and concentrationUgKg > codexMrlUgKg * 2 then \"severe\" else if concentrationUgKg != null and codexMrlUgKg != null and concentrationUgKg > codexMrlUgKg then \"exceeds\" else \"compliant\"", ["compliant","exceeds","severe"]),
      },
      {
        "name": "flagMrlBreach",
        "desc": "MRL breach / consumer exposure / trade rejection (bridges livestockAbx.flagGrowthPromoter + rasff-food-safety + wto-dispute)",
        "fields": [
          ("breachId", "string", True),
          ("measurementVid", "string", True, None, "bridges recordMrlMeasurement"),
          ("growthPromoterVid", "string", False, None, "bridges livestockAbx.flagGrowthPromoter"),
          ("breachKind", "string", True, ["codex_exceed","eu_import_block","fda_refusal","consumer_exposure","sub_chronic","acute_dietary","withdrawal_breach"]),
          ("tradeValueLossMusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ira-tax-credit",
    "app": "iraTaxCredit",
    "methods": [
      {
        "name": "recordCreditClaim",
        "desc": "IRA §45X / §45V / §45Q / §45Y / §48E tax credit claim (bridges evSupplyChain.flagFeocRisk + critical-minerals + hydrogen-economy)",
        "fields": [
          ("claimId", "string", True),
          ("claimantLei", "string", False),
          ("section", "string", True, ["45x_amp_credit","45v_hydrogen","45q_ccus","45y_clean_power","48e_clean_investment","45w_commercial_ev","30d_consumer_ev","48c_manufacturing"]),
          ("techBucket", "string", False, ["battery_cell","critical_mineral","solar_module","wind_turbine","fuel_cell","electrolyzer","nuclear_smr","ccus"]),
          ("claimedMusd", "number", True),
          ("fiscalYear", "integer", True),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFeocDisqualification",
        "desc": "FEOC / transfer of credit / recapture risk (bridges evSupplyChain.flagFeocRisk + critical-minerals.flagExportControlRisk + treasury-rulemaking)",
        "fields": [
          ("flagId", "string", True),
          ("claimVid", "string", True, None, "bridges recordCreditClaim"),
          ("feocRiskVid", "string", False, None, "bridges evSupplyChain.flagFeocRisk"),
          ("issueKind", "string", True, ["feoc_ownership","material_feoc_input","transferee_ineligible","recapture_trigger","labor_wage_shortfall","apprenticeship_shortfall","domestic_content_short"]),
          ("recaptureMusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "em-fx-reserves",
    "app": "emFxReserves",
    "methods": [
      {
        "name": "recordReserveComposition",
        "desc": "IMF COFER / ARA metric / FX reserve composition (bridges fxSwapLines.flagLineStress + sovereign-debt + imf-sdr)",
        "fields": [
          ("snapshotId", "string", True),
          ("countryIso3", "string", True),
          ("usdShareBusd", "number", False),
          ("eurShareBusd", "number", False),
          ("cnyShareBusd", "number", False),
          ("jpyShareBusd", "number", False),
          ("goldTroyOz", "number", False),
          ("sdrHoldingsBusd", "number", False),
          ("araCoverage", "number", False, None, "IMF ARA metric multiple"),
          ("asOfDate", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagReserveAdequacy",
        "desc": "Reserve adequacy / burn rate / credibility concern (bridges fxSwapLines.flagLineStress + imf-surveillance + sovereign-debt)",
        "fields": [
          ("flagId", "string", True),
          ("snapshotVid", "string", True, None, "bridges recordReserveComposition"),
          ("swapStressVid", "string", False, None, "bridges fxSwapLines.flagLineStress"),
          ("concernKind", "string", True, ["below_ara_100pct","reserve_burn","composition_concentration","gold_revaluation","sdr_mobilization_refused","capital_flight","dedollarization_stress"]),
          ("burnRateBusdMo", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("adequacyTier", "if burnRateBusdMo != null and burnRateBusdMo >= 10 then \"critical\" else if burnRateBusdMo != null and burnRateBusdMo >= 3 then \"stressed\" else \"watch\"", ["watch","stressed","critical"]),
      },
    ],
  },
  {
    "slug": "coral-reef-bleaching",
    "app": "coralReefBleaching",
    "methods": [
      {
        "name": "recordBleachingEvent",
        "desc": "Coral bleaching / DHW event (NOAA CRW / GCRMN / AIMS / CORDAP — bridges blueCarbonMrv.flagSeaLevelReversal + ocean-acidification + mpa-effectiveness)",
        "fields": [
          ("eventId", "string", True),
          ("reefSystem", "string", True, ["great_barrier","coral_triangle","mesoamerican","red_sea","western_indian","persian_gulf","caribbean","pacific_remote","andaman_nicobar"]),
          ("countryIso3", "string", True),
          ("dhwPeakC", "number", False, None, "Degree Heating Weeks peak"),
          ("bleachingAlertLevel", "string", True, ["no_stress","watch","warning","alert_1","alert_2"]),
          ("affectedAreaHectares", "number", False),
          ("observedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMortalityRisk",
        "desc": "Reef mortality / permanence reversal risk (bridges blueCarbonMrv.flagSeaLevelReversal + mpa-effectiveness + biodiversity-gbf)",
        "fields": [
          ("flagId", "string", True),
          ("eventVid", "string", True, None, "bridges recordBleachingEvent"),
          ("reversalVid", "string", False, None, "bridges blueCarbonMrv.flagSeaLevelReversal"),
          ("driverKind", "string", True, ["marine_heatwave","cyclone_damage","crown_of_thorns","land_runoff","overfishing_synergy","ocean_acidification","disease_outbreak","combined_multi_stress"]),
          ("mortalityPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if mortalityPct != null and mortalityPct >= 50 then \"catastrophic\" else if mortalityPct != null and mortalityPct >= 20 then \"significant\" else \"moderate\"", ["moderate","significant","catastrophic"]),
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
    out = Path(f"/tmp/wave13/w54_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
