#!/usr/bin/env python3
"""Wave 97 — Gov agency cluster (3/N): China 部委 (国务院 / 外交部 / 商务部 / 工信部 / 发改委)."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "cn-state-council",
    "app": "cnStateCouncil",
    "methods": [
      {
        "name": "recordExecutiveAction",
        "desc": "国务院 (State Council) executive action / 国办 directive (bridges socialMediaInfluenceOp + transnational-repression + dataLocalization)",
        "fields": [
          ("actionId", "string", True),
          ("organKind", "string", True, ["central_committee_pbsc","politburo","state_council_premier","state_council_executive","general_office_zhongnanhai","plenary_session","third_plenum","fourth_plenum","fifth_plenum","leading_small_group","working_group","ad_hoc_committee"]),
          ("topic", "string", True, ["common_prosperity","dual_circulation","made_in_china_2025","belt_road","national_security_law_hk","data_security","outbound_investment","domestic_circulation","tech_self_reliance","carbon_dual_targets","food_security","supply_chain_resilience","platform_economy","education_reform"]),
          ("relatedActorVid", "string", False, None, "bridges socialMediaInfluenceOp / dataLocalization"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCentralLocalTension",
        "desc": "Central-local tension / provincial implementation gap (bridges socialMediaInfluenceOp + transnational-repression + civilLiability)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordExecutiveAction"),
          ("tensionKind", "string", True, ["provincial_resist","local_government_debt","mega_city_overrule","sez_pushback","autonomous_region","village_level_implementation_gap","party_state_sep","propaganda_drift","censorship_inconsistent","one_country_two_systems_drift","macau_carveout"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cn-mofa",
    "app": "cnMofa",
    "methods": [
      {
        "name": "recordDiplomatic",
        "desc": "中国外交部 (Ministry of Foreign Affairs) diplomatic action (bridges sovereignDebt + transnationalRepression + extraditionTreaty)",
        "fields": [
          ("actionId", "string", True),
          ("departmentKind", "string", True, ["minister_office","american_oceania","european_division","west_asian_north_african","african","asian","russian_central_asian","arms_control","international_economy","intl_law","consular","information","ngo","frontier_maritime","macau_hk_taiwan","embassy_office_us","embassy_office_eu"]),
          ("actionKind", "string", True, ["bilateral_summit","brics_summit_chair","sco_summit","aiib_governance","ndr_summit","fonops_protest","prc_taiwan_strait","spokesperson_briefing","strategic_dialog","embassy_protest","white_paper_publication","arms_export_position","outer_space_position","data_position","cyber_position"]),
          ("relatedActorVid", "string", False, None, "bridges sovereignDebt / transnational-repression"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagTension",
        "desc": "Diplomatic tension / wolf-warrior / consular incident (bridges transnationalRepression + universalJurisdiction + minorityRights)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordDiplomatic"),
          ("tensionKind", "string", True, ["wolf_warrior","spat_us","spat_jp","spat_in","spat_au","spat_kr","spat_eu","spat_uk","ambassador_recall","persona_non_grata","journalist_expulsion","secrecy_law_invocation","exit_ban","consular_dispute","abducted_diaspora"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cn-mofcom",
    "app": "cnMofcom",
    "methods": [
      {
        "name": "recordTradeAction",
        "desc": "中国商务部 (MOFCOM) trade action / export control / FDI (bridges criticalMinerals + tradeRemedy + customsDeclaration)",
        "fields": [
          ("actionId", "string", True),
          ("departmentKind", "string", True, ["foreign_trade","export_control","fdi_review","fta","unreliable_entity_list","investigation_review","caac_aircraft_intl","mfn_review","intellectual_property_office","domestic_trade","prc_taiwan_trade","intl_econ_coop"]),
          ("actionKind", "string", True, ["export_control_germanium","export_control_gallium","export_control_graphite","export_control_drone","export_control_ev","unreliable_entity_addition","fdi_review_extra","wto_dispute_filed","ad_cvd_initiated","ftae_amendment","one_country_one_export_license","data_export_review","outbound_review_under_security_law"]),
          ("relatedActorVid", "string", False, None, "bridges criticalMinerals / tradeRemedy"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRetaliationConcern",
        "desc": "Retaliation / counter-tariff / chokepoint signaling (bridges tradeRemedy + criticalMinerals + ustrSection301)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordTradeAction"),
          ("retaliationKind", "string", True, ["counter_tariff","critical_mineral_chokepoint","rare_earth_squeeze","graphite_squeeze","fertilizer_export_quota","food_export_quota","cabotage_lockout","data_security_audit","national_security_review_block","unreliable_entity_target","blacklist_chinese_company"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cn-miit",
    "app": "cnMiit",
    "methods": [
      {
        "name": "recordIndustrialAction",
        "desc": "工信部 (MIIT) industrial / telecom / standards action (bridges criticalMinerals + evSupplyChain + dataLocalization)",
        "fields": [
          ("actionId", "string", True),
          ("departmentKind", "string", True, ["telecom_admin","information_security","manufacturing","equipment_manuf","raw_materials","semiconductor_industry","ev_industry","aerospace","ship_industry","sme_promotion","intl_coop","standards","ev_battery_white_list","cyber_security_review","prc_dataselect"]),
          ("actionKind", "string", True, ["6g_standard_position","big_fund_iii","semiconductor_fab_aid","ev_subsidy_phaseout","battery_white_list","saic_industrial_revolution_4_0","data_security_for_industry","mlps_china_cybersec_2_0","ipv6_pol","internet_lic","app_store_review","platform_anti_monopoly","cybersecurity_review_pre_ipo"]),
          ("relatedActorVid", "string", False, None, "bridges evSupplyChain / criticalMinerals"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagIndustrialPolicyDispute",
        "desc": "Industrial policy dispute / state aid / overcapacity (bridges criticalMinerals + tradeRemedy + frugalFourCoalition)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordIndustrialAction"),
          ("disputeKind", "string", True, ["overcapacity_steel","overcapacity_solar","overcapacity_ev","wto_subsidy_complaint","scm_subsidies","pri_state_owned_subsidy","cf_critical_funding","jdf_chip_aid","ipcei_eu_compete","national_champion_protect","unfair_competition_china_filing"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cn-ndrc",
    "app": "cnNdrc",
    "methods": [
      {
        "name": "recordPlanAction",
        "desc": "发改委 (NDRC) macroeconomic plan / energy / climate / rural (bridges climateAdaptationFinance + sovereignDebt + worldBankDpf)",
        "fields": [
          ("actionId", "string", True),
          ("departmentKind", "string", True, ["energy_admin_nea","climate_change","macro_fixed_assets","industrial_dev","high_tech","rural_economy","western_dev","price_admin","price_supervision","reform_pioneer","one_belt_one_road","yangtze_protect","yellow_river","green_dev","social_development"]),
          ("actionKind", "string", True, ["five_year_plan","carbon_dual_target","energy_consumption_intensity","green_steel_pilot","ccus_subsidy","saf_blend","mid_long_term_youth_dev","ev_charging_infrastructure","high_speed_rail","hub_airport","yangtze_diversion","rural_revitalization","common_prosperity_zhejiang","data_factor_marketization"]),
          ("relatedActorVid", "string", False, None, "bridges climateAdaptationFinance / sovereignDebt"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagImplementationGap",
        "desc": "Local plan implementation gap / energy intensity overshoot (bridges climateAdaptationFinance + just-transition + euDgClima)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordPlanAction"),
          ("gapKind", "string", True, ["provincial_lag","energy_intensity_overshoot","carbon_dual_breach","rebalancing_uneven","local_govt_debt_drag","real_estate_drag","capital_outflow","yuan_pressure","steel_relapse","coal_addback","crash_program_blackout"]),
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


for i, a in enumerate(ACTORS, start=1):
    bd=REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    ld=REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bd.mkdir(parents=True,exist_ok=True); ld.mkdir(parents=True,exist_ok=True)
    for m in a["methods"]:
        (ld/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bd/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    ddl = gen_ddl(a)
    out = Path(f"/tmp/wave13/w97_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
