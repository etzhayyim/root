#!/usr/bin/env python3
"""Wave 98 — Gov agency cluster (4/N): India ministries (MEA/MOF/Commerce/Home/Defence)."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "in-mea",
    "app": "inMea",
    "methods": [
      {
        "name": "recordDiplomatic",
        "desc": "India Ministry of External Affairs (MEA) action (bridges sovereignDebt + extraditionTreaty + southSouthCoop)",
        "fields": [
          ("actionId", "string", True),
          ("departmentKind", "string", True, ["minister_office_eam","secretary_west","secretary_east","secretary_economic","secretary_consular","americas_division","europe_western_division","central_asia","east_asia","south_asia","west_asia_north_africa","africa","oia_overseas_indian","p_india_quad_g20","international_economic_relations","united_nations_political","disarmament_imt"]),
          ("actionKind", "string", True, ["bilateral_treaty","g20_chair_2023","quad_summit","brics_summit","sco_summit","ibsa","oic_observer","unsc_e10","fipic_pacific","caribbean_indaba","strategic_partnership","fta_signed","caatsa_waiver","russia_arms_deal","passport_act_amend","oci_review"]),
          ("relatedActorVid", "string", False, None, "bridges sovereignDebt / extraditionTreaty / southSouthCoop"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDiplomaticTension",
        "desc": "Diplomatic tension / diaspora / khalistan / china border (bridges transnationalRepression + universalJurisdiction + interpolRedabuse)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordDiplomatic"),
          ("tensionKind", "string", True, ["pakistan_friction","china_lac","khalistan_diaspora","sikh_targeting_canada","sikh_targeting_uk","sikh_targeting_us","bangladesh_friction","sri_lanka","maldives","myanmar_junta","nepal_china_pivot","bhutan_doklam","afghanistan_taliban","russia_oil_us_pressure"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "in-mof",
    "app": "inMof",
    "methods": [
      {
        "name": "recordFiscalAction",
        "desc": "India Ministry of Finance (MOF) action (bridges sovereignDebt + bepsPillar + worldBankDpf)",
        "fields": [
          ("actionId", "string", True),
          ("departmentKind", "string", True, ["dea_economic","dor_revenue_irs","dfs_financial_services","dipam_disinvestment","dec_expenditure","dipa_public_assets","dpe_public_enterprises","sebi","rbi_govern","fema_foreign_exchange","gst_council","cbic_indirect_taxes","cbdt_direct_taxes","fiu_aml","national_payments_corp"]),
          ("actionKind", "string", True, ["union_budget","supplementary_grant","tax_amendment_finance_act","gst_council_decision","dividend_distribution","disinvestment_air_india","disinvestment_lic","npa_resolution","ibc_amendment","cbdc_e_rupee","upi_global_push","fpi_route_change","gift_city_ifsc","fema_relax","indo_us_tax_arrangement"]),
          ("relatedActorVid", "string", False, None, "bridges sovereignDebt / bepsPillar"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFiscalConcern",
        "desc": "Fiscal concern / state vs centre / GST share dispute (bridges sovereignDebt + worldBankDpf + frugalFourCoalition)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordFiscalAction"),
          ("concernKind", "string", True, ["centre_state_revenue_share","gst_compensation_extension_demand","fiscal_responsibility_breach","sovereign_rating_pressure","capex_vs_revex","disinvestment_target_miss","npa_recurrence","real_estate_overhang","msme_credit_squeeze","household_debt_rising","state_dpe_overdraw"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "in-commerce",
    "app": "inCommerce",
    "methods": [
      {
        "name": "recordTradeAction",
        "desc": "India Ministry of Commerce & Industry action (bridges tradeRemedy + criticalMinerals + customs-declaration)",
        "fields": [
          ("actionId", "string", True),
          ("departmentKind", "string", True, ["dgft","commerce_dept","dipp_industry_promotion","dpiit","exim_bank","mof_jab_traffic","sez_devp","fci_food_corp","msme_dept","invest_india","spices_board","tea_coffee","tobacco_board","apeda_agri_export","india_brand_equity"]),
          ("actionKind", "string", True, ["fta_signed_uk","fta_signed_eu","fta_signed_efta","cepa_uae","ecta_australia","sez_amendment","pli_scheme_extend","dgci_export_ban_wheat","dgci_export_ban_rice","atmanirbhar_bharat","make_in_india_2_0","sez_to_dta","semiconductor_pli","specialty_steel_pli","drone_pli","chemical_pli"]),
          ("relatedActorVid", "string", False, None, "bridges tradeRemedy / criticalMinerals"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagTradeFriction",
        "desc": "Trade friction / FTA stall / WTO dispute (bridges tradeRemedy + wtoTradeCbam + ustrSection301)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordTradeAction"),
          ("frictionKind", "string", True, ["fta_uk_stall","fta_eu_stall","fta_canada_stall","apec_join_stall","russia_oil_workaround","caatsa_concern","gsp_lapsed_us","section_301_review","poultry_dispute_us","steel_232_dispute","sugar_subsidy_wto","ip_evergreening","data_localization_dispute"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "in-home",
    "app": "inHome",
    "methods": [
      {
        "name": "recordHomeAffair",
        "desc": "India Ministry of Home Affairs (MHA) action (bridges asylumDetermination + extraditionTreaty + judicialAppointment)",
        "fields": [
          ("actionId", "string", True),
          ("departmentKind", "string", True, ["minister_office","internal_security","border_management","police_modernisation","disaster_management","jamar_kashmir","union_territories","censuses","foreigners_division","judicial_division","centre_state","official_language","fcra_div","cbi_central_bureau","nia_national_investigation","ed_enforcement_directorate","intelligence_bureau"]),
          ("actionKind", "string", True, ["fcra_amendment","caa_implementation","npr_npr","upa_act_2019","passport_act_amend","fcra_license_revoke","ngo_clamp","internet_shutdown_authorize","afspa_extension","bsf_jurisdiction_extend","crpf_deployment","cbi_consent_state","supreme_court_collegium_battle"]),
          ("relatedActorVid", "string", False, None, "bridges asylumDetermination / extraditionTreaty"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRightsConcern",
        "desc": "Rights concern / civil society squeeze / minority backlash (bridges minorityRights + transnationalRepression + pressFreedomIndex)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordHomeAffair"),
          ("concernKind", "string", True, ["fcra_targeted_ngo","muslim_minority_violence","christian_minority_violence","dalit_atrocity","tribal_displacement","journalist_jailed","activist_uapa","pegasus_targeting","internet_shutdown_pattern","manipur_violence","khalistan_response_excessive","cbi_political_use"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "in-defence",
    "app": "inDefence",
    "methods": [
      {
        "name": "recordDefenceAction",
        "desc": "India Ministry of Defence (MoD) action (bridges iaeaSafeguards + disarmamentTreaties + lawsAutonomousWeapons)",
        "fields": [
          ("actionId", "string", True),
          ("departmentKind", "string", True, ["minister_raksha","secretary_def","drdo","army_iarmy","navy_inavy","airforce_iaf","strategic_forces","integrated_defence_staff","def_acquisition_council","def_pri_div","cap_acq_dpa","def_finance","def_intelligence_agency","mod_chips","def_research_pmt","def_admin"]),
          ("actionKind", "string", True, ["s400_russia_buy","rafale_france_buy","p8i_us_buy","quad_malabar","caatsa_waiver","atmanirbhar_def_list","positive_indigenisation_list","drdo_brahmos_export","akash_export","light_combat_aircraft_lcia","tejas_export","nuclear_doctrine_review","no_first_use_review","modernization_plan","amca_design"]),
          ("relatedActorVid", "string", False, None, "bridges iaeaSafeguards / lawsAutonomousWeapons"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSecurityTension",
        "desc": "Security tension / LAC standoff / Pakistan / Indo-Pacific (bridges transnationalRepression + universalJurisdiction + criticalMinerals)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordDefenceAction"),
          ("tensionKind", "string", True, ["lac_china_galwan","arunachal_china_claim","pakistan_loc","kashmir_internal","indian_ocean_china","quad_friction","afghanistan_taliban","myanmar_border","nepal_border_strip","sri_lanka_china","caatsa_pressure","russia_oil_payments","s400_friction"]),
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
    out = Path(f"/tmp/wave13/w98_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
