#!/usr/bin/env python3
"""Wave 74 — espionage-act / dam-safety / biometric-standards / nbfi-stress / uflpa-enforcement.

Bridges Wave 73:
- espionage-act ↔ classificationReview.flagOverClassification
- dam-safety ↔ transboundaryRiver.flagRiparianDispute
- biometric-standards ↔ digitalPublicInfra.flagExclusionRisk
- nbfi-stress ↔ liquidityFacility.flagStigmaEffect
- uflpa-enforcement ↔ modernSlavery.flagInadequateDisclosure
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "espionage-act",
    "app": "espionageAct",
    "methods": [
      {
        "name": "recordProsecution",
        "desc": "Espionage Act / OSA / national security leak prosecution (bridges classificationReview.flagOverClassification + federal-court-docket + press-freedom)",
        "fields": [
          ("prosecutionId", "string", True),
          ("jurisdiction", "string", True, ["us_espionage","uk_osa","fr_code_penal","de_stgb","jp_special_secrets","cn_national_security","ru_ugol_kodex","in_osa","au_foreign_interference","za_rica"]),
          ("subjectCategory", "string", True, ["whistleblower","journalist","contractor","government_employee","foreign_agent","dual_national","academic","activist","ngo_worker","leaker"]),
          ("classifiedMaterial", "string", False, ["tech","signals","human_intel","diplomatic","military_ops","nuclear","financial","economic","commercial_secret","constitutional"]),
          ("overClassifyVid", "string", False, None, "bridges classificationReview.flagOverClassification"),
          ("chargedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagChillingEffect",
        "desc": "Press chill / source closure / sentence severity (bridges classificationReview.flagOverClassification + press-freedom + whistleblower-protect)",
        "fields": [
          ("flagId", "string", True),
          ("prosecutionVid", "string", True, None, "bridges recordProsecution"),
          ("concernKind", "string", True, ["disproportionate_sentence","source_dried_up","journalist_conspiracy","press_cert_subpoena","extradition_chill","no_public_interest_defense","electronic_communications_act","broad_definition","routine_classification","newsgathering_criminalized","iron_on_journalism"]),
          ("sentenceYears", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "dam-safety",
    "app": "damSafety",
    "methods": [
      {
        "name": "recordInspection",
        "desc": "ICOLD / USACE / state dam safety inspection (bridges transboundaryRiver.flagRiparianDispute + infra-file + coastal-slr)",
        "fields": [
          ("inspectionId", "string", True),
          ("damId", "string", True),
          ("jurisdiction", "string", True, ["usace","ferc","state_dso","icold_bulletin","icold_q99","bnaf_bureau_reclamation","eu_directive","china_mwr","in_dsa","br_ana","egy_egyptian_res","intl_rcc"]),
          ("damKind", "string", True, ["concrete_gravity","concrete_arch","earth_fill","rock_fill","buttress","hydropower","irrigation","flood_control","tailings","levee","offstream_storage","pumped_storage"]),
          ("riparianDisputeVid", "string", False, None, "bridges transboundaryRiver.flagRiparianDispute"),
          ("inspectedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCriticalRisk",
        "desc": "Critical risk / break imminent / tailings dam failure (bridges transboundaryRiver.flagRiparianDispute + disaster-response + cyclone-prepo)",
        "fields": [
          ("flagId", "string", True),
          ("inspectionVid", "string", True, None, "bridges recordInspection"),
          ("riskKind", "string", True, ["seepage","piping","overtopping","foundation_failure","tailings_liquefaction","cracks_propagating","freeboard_inadequate","spillway_capacity","emergency_plan_missing","inundation_zone","seismic","terrorism_threat"]),
          ("populationDownstream", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "biometric-standards",
    "app": "biometricStandards",
    "methods": [
      {
        "name": "recordStandard",
        "desc": "Biometric standard (ICAO 9303 / ISO/IEC 39794 / FIDO2 — bridges digitalPublicInfra.flagExclusionRisk + digital-identity + crpd-disability)",
        "fields": [
          ("standardId", "string", True),
          ("body", "string", True, ["icao_9303","iso_iec_39794","iso_iec_17839","nist_fips","fido2","eu_eidas2","bsp_india","cic_china","enisa","oasis_saml"]),
          ("modality", "string", True, ["facial","fingerprint","iris","voice","gait","palm_vein","signature","dna_forensic","vein","behavioral","multimodal","passive_liveness"]),
          ("accuracyTier", "string", False, ["ultra_high","high","medium","low","acceptable_with_caveats"]),
          ("exclusionVid", "string", False, None, "bridges digitalPublicInfra.flagExclusionRisk"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInclusionGap",
        "desc": "Disability / dark skin / elderly failure (bridges digitalPublicInfra.flagExclusionRisk + crpd-disability + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("standardVid", "string", True, None, "bridges recordStandard"),
          ("gapKind", "string", True, ["dark_skin_far","elderly_fingerprint_wear","vein_too_low","acquired_disability","amputation","worn_palmprint","occluded_iris","religious_cover","trans_presentation","extreme_humidity","data_set_bias"]),
          ("enrollmentFailureRate", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "nbfi-stress",
    "app": "nbfiStress",
    "methods": [
      {
        "name": "recordStressTest",
        "desc": "Non-bank financial intermediary stress test (FSB NBFI / ESRB / SEC — bridges liquidityFacility.flagStigmaEffect + bank-resolution + sovereign-debt)",
        "fields": [
          ("testId", "string", True),
          ("nbfiKind", "string", True, ["money_market","hedge_fund","open_ended_fund","pe_fund","insurer_life","pension_db","ccp","broker_dealer","finance_company","fintech_neobank","crypto_exchange","commodity_fund","securitizer","uk_ltlip","repoer"]),
          ("stressScenario", "string", True, ["dash_for_cash","redemption_run","margin_spiral","ltcm_like","covid_march_2020","gilt_crisis","arm_spike","dollar_shortage","commodity_spike","sovereign_stress","stablecoin_run","crypto_meltdown","repo_spike"]),
          ("stigmaVid", "string", False, None, "bridges liquidityFacility.flagStigmaEffect"),
          ("testedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagResolutionGap",
        "desc": "NBFI resolution / transparent unwinding gap (bridges liquidityFacility.flagStigmaEffect + bank-resolution + sovereign-debt)",
        "fields": [
          ("flagId", "string", True),
          ("testVid", "string", True, None, "bridges recordStressTest"),
          ("gapKind", "string", True, ["no_lolr","resolution_framework_missing","collateral_taker_unclear","margin_asymmetry","intermediary_chains","central_clearing_risk","prime_broker_concentration","daily_liquidity_mismatch","gating_enforcement","swing_pricing_weak","reporting_opacity"]),
          ("potentialLossBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "uflpa-enforcement",
    "app": "uflpaEnforcement",
    "methods": [
      {
        "name": "recordWroDetention",
        "desc": "UFLPA / Withhold Release Order / CBP detention (bridges modernSlavery.flagInadequateDisclosure + forced-labor + customs-declaration)",
        "fields": [
          ("actionId", "string", True),
          ("agency", "string", True, ["us_cbp","us_dhs_uflpa_task_force","us_doc","eu_commission","uk_border_force","ca_cbsa","au_border_force","nl_customs","thb_dutch_ftc","jp_customs"]),
          ("actionKind", "string", True, ["wro","finding","detention_notice","exclusion_entity","summary_rebuttal","seizure","forced_reexport","auto_exclude_ppp","entity_list","reclassification"]),
          ("commodity", "string", True, ["cotton_textile","polysilicon_solar","tomato","batch_processing","aluminum","electronics","apparel","fish_seafood","rubber_glove","timber","down_feather","mica","silver"]),
          ("modernSlaveryVid", "string", False, None, "bridges modernSlavery.flagInadequateDisclosure"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRebuttalFailure",
        "desc": "Rebuttable presumption failure / supply chain opacity (bridges modernSlavery.flagInadequateDisclosure + supply-chain-finance + forced-labor)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordWroDetention"),
          ("failureKind", "string", True, ["no_isotope_trace","third_country_laundering","falsified_origin","linked_entity_no_audit","prc_exception_case","compliance_audit_blocked","due_diligence_superficial","shell_subsidiary","repackaging","relabeling_operation"]),
          ("detainedValueUsd", "number", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence"]):
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
    out = Path(f"/tmp/wave13/w74_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
