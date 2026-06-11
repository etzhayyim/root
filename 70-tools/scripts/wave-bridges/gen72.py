#!/usr/bin/env python3
"""Wave 72 — foia-tracker / water-stewardship / birth-registration / digital-run-risk / ftz-zones.

Bridges Wave 71:
- foia-tracker ↔ igAudit.flagRecommendationStall
- water-stewardship ↔ sbtnTarget.flagMiss
- birth-registration ↔ statelessPerson.flagGapOutcome
- digital-run-risk ↔ depositInsurance.flagCoverageRisk
- ftz-zones ↔ cumulationRule.flagExploitation
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "foia-tracker",
    "app": "foiaTracker",
    "methods": [
      {
        "name": "recordRequest",
        "desc": "FOIA / EU Reg 1049 / public records request (bridges igAudit.flagRecommendationStall + press-freedom + enforcement-action)",
        "fields": [
          ("requestId", "string", True),
          ("requesterCategory", "string", True, ["journalist","academic","nonprofit","commercial","public_interest","anonymous","industry","political","individual","government"]),
          ("regime", "string", True, ["us_foia","us_privacy_act","eu_reg_1049","uk_foia","ca_atia","au_foi","jp_joho_kokai","mex_transparency","br_lai","in_rti"]),
          ("subjectAgency", "string", False),
          ("recommendationStallVid", "string", False, None, "bridges igAudit.flagRecommendationStall"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagResponseDelay",
        "desc": "Agency response delay / redaction overreach / Glomar (bridges igAudit.flagRecommendationStall + press-freedom + whistleblower-protect)",
        "fields": [
          ("flagId", "string", True),
          ("requestVid", "string", True, None, "bridges recordRequest"),
          ("delayKind", "string", True, ["past_20_day_deadline","past_30_day","still_processing","redacted_heavily","glomar","exemption_b5","exemption_b7","rocket_docket_gaming","no_tracking","pattern_fee_waiver_denial","appeal_stall"]),
          ("daysPending", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "water-stewardship",
    "app": "waterStewardship",
    "methods": [
      {
        "name": "recordStewardshipPlan",
        "desc": "Alliance for Water Stewardship / CDP Water plan (bridges sbtnTarget.flagMiss + climate-value-chain + biodiversity-gbf)",
        "fields": [
          ("planId", "string", True),
          ("operatorLei", "string", False),
          ("regime", "string", True, ["aws_standard","cdp_water","watershed_tnc","iwa_utility","context_based_wri","20x_reduction","zero_liquid_discharge","circular_water","reuse_pathway"]),
          ("basinName", "string", False),
          ("riskBasinStressLevel", "string", False, ["low","medium_low","medium_high","high","extremely_high"]),
          ("sbtnMissVid", "string", False, None, "bridges sbtnTarget.flagMiss"),
          ("committedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBasinStress",
        "desc": "Basin stress / withdrawal exceedance / community water conflict (bridges sbtnTarget.flagMiss + water-scarcity + fpic-consent)",
        "fields": [
          ("flagId", "string", True),
          ("planVid", "string", True, None, "bridges recordStewardshipPlan"),
          ("stressKind", "string", True, ["withdrawal_exceed","groundwater_drawdown","community_conflict","indigenous_dispute","aquifer_contamination","salinization","ecosystem_collapse","dam_release_abuse","flow_regulation_bypass","prior_informed_consent"]),
          ("affectedPersons", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "birth-registration",
    "app": "birthRegistration",
    "methods": [
      {
        "name": "recordRegistration",
        "desc": "Civil birth registration (UNICEF CRVS / SDG 16.9 — bridges statelessPerson.flagGapOutcome + refugee-unhcr + land-tenure)",
        "fields": [
          ("registrationId", "string", True),
          ("countryIso3", "string", True),
          ("regimeKind", "string", True, ["crvs_digital","paper_only","hybrid","mobile_registry","late_registration","retrofit_certificates","village_officiant","cold_chain_crvs","tribal_council"]),
          ("childCategory", "string", True, ["in_hospital","home_birth","refugee_child","stateless_parent","rural_remote","urban_informal","indigenous","conflict_zone","nomadic","orphan"]),
          ("statelessGapVid", "string", False, None, "bridges statelessPerson.flagGapOutcome"),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRegistrationGap",
        "desc": "Birth registration gap / nationality denial / gender-based (bridges statelessPerson.flagGapOutcome + gender-inclusion + worker-grievance)",
        "fields": [
          ("flagId", "string", True),
          ("registrationVid", "string", True, None, "bridges recordRegistration"),
          ("gapKind", "string", True, ["no_birth_certificate","nationality_denial","gender_name_transfer","fee_barrier","language_barrier","mixed_nationality","refugee_limbo","border_dispute","missing_maternity_records","discrimination_religion","post_disaster"]),
          ("childrenEstimated", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "digital-run-risk",
    "app": "digitalRunRisk",
    "methods": [
      {
        "name": "recordOutflowEvent",
        "desc": "Digital bank run / SVB-style outflow / stablecoin depeg (bridges depositInsurance.flagCoverageRisk + banking-account + stablecoin-reserves)",
        "fields": [
          ("eventId", "string", True),
          ("institutionLei", "string", False),
          ("institutionKind", "string", True, ["regional_bank","sbl_subsidiary","fintech_neobank","crypto_exchange","stablecoin_issuer","systemic_bank","regional_gsib","dsib","msb","shadow_bank"]),
          ("outflowMechanism", "string", True, ["online_transfer","wire","stablecoin_redeem","prime_broker_move","money_market_shift","rumor_spread","social_media_panic","concentrated_industry","twitter_finance","fomc_shock"]),
          ("coverageRiskVid", "string", False, None, "bridges depositInsurance.flagCoverageRisk"),
          ("outflowBusd", "number", False),
          ("hoursTo80pctOutflow", "number", False),
          ("occurredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagContagionRisk",
        "desc": "Contagion / peer bank stress / off-exchange depeg (bridges depositInsurance.flagCoverageRisk + mica-crypto + stablecoin-reserves)",
        "fields": [
          ("flagId", "string", True),
          ("eventVid", "string", True, None, "bridges recordOutflowEvent"),
          ("contagionKind", "string", True, ["peer_bank_stress","industry_concentration","dealer_cancel","money_market_shift","fdic_sre_activation","fed_bxl_bank_liquidity","stablecoin_offexchange_depeg","global_nbfi_stress","scary_cross_border","dusd_cross_run"]),
          ("peerInstitutionCount", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ftz-zones",
    "app": "ftzZones",
    "methods": [
      {
        "name": "recordZone",
        "desc": "Foreign Trade Zone / Free Zone / SEZ (bridges cumulationRule.flagExploitation + customs-declaration + ev-supply-chain)",
        "fields": [
          ("zoneId", "string", True),
          ("hostCountryIso3", "string", True),
          ("zoneKind", "string", True, ["ftz_us","free_zone_uae","free_zone_colombia","sez_china","sez_india","special_ec_zone","maquila_mex","export_ind_zone_kr","industrial_cluster","bonded_warehouse","airport_fz","port_fz","geographic_indication_fz"]),
          ("sectorKind", "string", True, ["automotive","electronics","semiconductor","petrochemical","apparel","pharma","logistics","ecommerce","food_processing","oil_gas","mining_proc","high_tech","defense","ai_data","media_creative"]),
          ("exploitVid", "string", False, None, "bridges cumulationRule.flagExploitation"),
          ("establishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagLabourAbuse",
        "desc": "FTZ labour abuse / wage below minimum / union suppression (bridges cumulationRule.flagExploitation + worker-grievance + ilo-labor-rights)",
        "fields": [
          ("flagId", "string", True),
          ("zoneVid", "string", True, None, "bridges recordZone"),
          ("abuseKind", "string", True, ["below_minimum","union_suppression","overtime_forced","bonded_labour","migrant_worker_exploit","worker_dormitory_abuse","forced_pregnancy_test","occ_safety_gap","no_collective_bargaining","pit_pay","child_labour"]),
          ("affectedWorkers", "integer", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","children","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","institution"]):
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
    out = Path(f"/tmp/wave13/w72_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
