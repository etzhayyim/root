#!/usr/bin/env python3
"""Wave 96 — Gov agency cluster (2/N): JP METI / MEXT / MHLW / MLIT / MOFA.

5 Japanese ministries. All-string. Bridges to relevant existing actors.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "jp-meti",
    "app": "jpMeti",
    "methods": [
      {
        "name": "recordAction",
        "desc": "経済産業省 action / industrial policy / energy / trade (bridges criticalMinerals + evSupplyChain + ustr-section-301)",
        "fields": [
          ("actionId", "string", True),
          ("bureau", "string", True, ["honsho","keisan_economic","sangyo_industrial","seizo_manufacturing","tsusho_trade","shoshibai_smb","commerce_info_ipa","shigen_resource_energy","gns_aerospace_robotics","kei_kankoutei","jpomp","fepc_aenecog"]),
          ("actionKind", "string", True, ["industrial_policy","gx_green_transition","ai_strategy","semiconductor_strategy","jasm_tsmc","rapidus","supply_chain_act","economic_security_act","battery_strategy","hydrogen_basic_strategy","oil_kimura_emergency","nuclear_restart_review","trade_remedy","fdi_security_review","intellectual_property_grant"]),
          ("relatedActorVid", "string", False, None, "bridges criticalMinerals / evSupplyChain"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInterAgencyTension",
        "desc": "METI vs MOF / METI vs MOFA / 産業政策会議 (bridges jpMof + treasuryRulemaking + sovereignDebt)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("tensionKind", "string", True, ["mof_budget_block","mofa_diplomatic_concern","mlit_aviation_overlap","mhlw_health_industry_dual","mext_research_ip","kantei_steering","ldp_chair_pressure","ldp_seimuchoukai","fsa_bank_industrial_intersection","industry_capture","gx_finance_dispute","semiconductor_subsidy_dispute","fnsf_special_meeting"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "jp-mext",
    "app": "jpMext",
    "methods": [
      {
        "name": "recordAction",
        "desc": "文部科学省 action / education / R&D / cultural (bridges higherEducationAccred + bilingualEducation + culturalRepatriation)",
        "fields": [
          ("actionId", "string", True),
          ("bureau", "string", True, ["honsho","secondary_school","higher_ed","science_tech","sports","cultural","international_research","admin_local_ed","jiu_kotaku","gigaku_school_act","kontei_universities","sci_jiu_research","tonin_jasso","jaxa_govern","riken_govern","jamstec_govern"]),
          ("actionKind", "string", True, ["national_curriculum","school_act_amend","teacher_certification","university_funding","kakenhi_grants","jaxa_mission_approval","riken_research_priority","ai_education_strategy","heritage_designation","cultural_property","intangible_cultural","language_policy","ainu_promotion_act","stem_strategy","liberal_arts_review"]),
          ("relatedActorVid", "string", False, None, "bridges higherEducationAccred / culturalRepatriation"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPolicyShift",
        "desc": "Policy shift / cabinet override / academic freedom concern (bridges jpMof + judicialAppointment + minorityRights)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("shiftKind", "string", True, ["cabinet_override","academic_freedom","sgu_global_30","top_global_university","gakujutsu_kaigi_appointment","ldp_overreach","budget_squeeze","rebellion_research","university_governance_shift","kantei_steering","language_revival_pause","liberal_arts_pivot"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "jp-mhlw",
    "app": "jpMhlw",
    "methods": [
      {
        "name": "recordAction",
        "desc": "厚生労働省 action / health / labor / social security (bridges drugPriceNegotiation + universalHealthCoverage + socialInsuranceProcedure)",
        "fields": [
          ("actionId", "string", True),
          ("bureau", "string", True, ["honsho","health_policy","medical_safety","pharma_food","kenpoku_seikatsu_safe","health_insurance","employment","labor_standards","equal_employment","kankoku_pension","child_family","welfare_disability","emergency_disaster","hwf_health_workforce"]),
          ("actionKind", "string", True, ["pharma_approval","drug_price_revision","health_insurance_revision","oeshi_negotiation","kanri_insurance_subsidy","kosei_pension_revision","kokumin_pension","employment_law_amend","minimum_wage_revise","work_style_reform","care_insurance","child_allowance_law","heisei_disaster_response","mers_covid_imhe","oimon_health_workforce_recruit","oba_iryouho"]),
          ("relatedActorVid", "string", False, None, "bridges drugPriceNegotiation / universalHealthCoverage"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPolicyConcern",
        "desc": "Policy concern / population decline / labor shortage (bridges jpMof + reskillingFund + minorityRights)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("concernKind", "string", True, ["pension_solvency","health_insurance_solvency","labor_shortage","care_worker_shortage","tokutei_skill_law_pace","jinko_decline","aging_society_2025_problem","mof_zaisei_pressure","industry_dependence","local_health_disparity","medical_dx_gap","drug_lag","drug_loss_global"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "jp-mlit",
    "app": "jpMlit",
    "methods": [
      {
        "name": "recordAction",
        "desc": "国土交通省 action / infra / transport / aviation / housing (bridges airportHanedaOps + airlineJalOps + railLine)",
        "fields": [
          ("actionId", "string", True),
          ("bureau", "string", True, ["honsho","infra","road","river","ports","aviation","rail","public_transport","jma_meteorology","mlit_kaijou_jcg_jcga","tourism_jnto","city_planning","housing_construction","kintai_emergency"]),
          ("actionKind", "string", True, ["aviation_law_amend","slot_allocation","new_runway","port_expansion","road_act","river_basic_plan","rail_law_amend","shinkansen_extension","linear_chuo","disaster_recovery","tourism_policy","building_code_revise","energy_efficiency_building","public_transport_act","jma_alert_revise","jcga_coast_guard_strategy"]),
          ("relatedActorVid", "string", False, None, "bridges airportHanedaOps / airportNaritaOps / railLine"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInfraGap",
        "desc": "Infrastructure gap / aging / disaster vulnerability (bridges damSafety + transitDelay + railIncident)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("gapKind", "string", True, ["aging_road","aging_bridge","aging_water","aging_sewer","port_capacity","rural_transport_collapse","tunnel_collapse","tsunami_protection","earthquake_retrofit","ev_charging_lag","airport_capacity","slot_constraint","linear_overrun","metro_outage","new_disaster_norm"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "jp-mofa",
    "app": "jpMofa",
    "methods": [
      {
        "name": "recordAction",
        "desc": "外務省 action / treaty / consular / development aid (bridges sovereignDebt + extraditionTreaty + oecdDacTransparency)",
        "fields": [
          ("actionId", "string", True),
          ("bureau", "string", True, ["honsho_minister","secretariat","north_america","europe_central_asia","asia_oceania","middle_east_africa","cn_korea","latin_caribbean","economic","international_cooperation","international_legal","intelligence_analysis","press_pr","jica_govern","ngo_grantsdesk"]),
          ("actionKind", "string", True, ["bilateral_treaty","fpda_security_consultation","apec_japan_summit","g7_g20_jp_chair","tcs_korea_china_jp","oda_white_paper","oda_kibou","jica_loan","jbic_loan","economic_sanction_jp","jeita_arms_export_review","bracket_jhcl","fc_cn_friendship","tomodachi_us_alliance","quad_uomp","fpda_kicker"]),
          ("relatedActorVid", "string", False, None, "bridges sovereignDebt / extraditionTreaty"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDiplomaticTension",
        "desc": "Diplomatic tension / triangle drift / domestic backlash (bridges transnationalRepression + extraditionTreaty + universalJurisdiction)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("tensionKind", "string", True, ["us_japan_friction","cn_japan_friction","kr_japan_history","ru_japan_islands","kp_north_korea_abductee","prc_taiwan_strait","wto_dispute","uss_oss_japan_signal","arms_export_dispute","nuclear_weapons_treaty_pressure","ukraine_aid_political","oda_recipient_dispute"]),
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
    out = Path(f"/tmp/wave13/w96_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
