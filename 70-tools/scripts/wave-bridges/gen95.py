#!/usr/bin/env python3
"""Wave 95 — Government agency cluster (1/N): US Treasury, US State, EU DG-COMP, EU DG-CLIMA, JP MOF.

User-directed pivot to global gov agencies. Each agency has:
- recordAction: action/policy/order issued
- flagInterAgencyConflict: turf battle, jurisdictional dispute, doctrinal inconsistency

All-string. Bridges to relevant existing actors.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "us-treasury-dept",
    "app": "usTreasuryDept",
    "methods": [
      {
        "name": "recordAction",
        "desc": "US Treasury Department action / regulation / sanction (parent of OFAC/IRS/FinCEN/OCC — bridges ofac-sanctions-sdn + treasury-rulemaking + ira-tax-credit)",
        "fields": [
          ("actionId", "string", True),
          ("subAgency", "string", True, ["ofac","fincen","irs","occ","tigta","tigtua","oig","fsoc","cfius","kleptocracy_initiative","do_office_inspector_general","wbo_whistleblower","crypto_outreach"]),
          ("actionKind", "string", True, ["sanctions_designation","sanctions_removal","license_general","license_specific","cfius_review_open","cfius_mitigation","mra_remediation","aml_pillar_audit","ira_45x_guidance","beneficial_ownership_rule","crypto_rule","exchange_stablecoin_review","fed_open_market_coordination","ofr_research"]),
          ("relatedActorVid", "string", False, None, "bridges treasury-rulemaking / ofac-sanctions-sdn / ira-tax-credit"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInterAgencyConflict",
        "desc": "Inter-agency conflict / Treasury vs Commerce / Treasury vs DOJ (bridges treasury-rulemaking + judicial-influence + cveCna)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("conflictKind", "string", True, ["doj_vs_treasury","commerce_vs_treasury","fed_vs_treasury","sec_vs_treasury","fdic_vs_occ","cfius_vs_state","ofac_vs_doj","fincen_vs_irs_ci","carve_out_dispute","general_license_dispute","sectoral_priority","stewards_role"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "us-state-dept",
    "app": "usStateDept",
    "methods": [
      {
        "name": "recordAction",
        "desc": "US Dept of State action / cable / treaty / consular (bridges extradition-treaty + interpol-redabuse + transnational-repression)",
        "fields": [
          ("actionId", "string", True),
          ("bureau", "string", True, ["s_secretary","d_deputy","p_political","r_global_affairs","t_arms_control","ds_diplo_security","cn_consular","io_intl_org","drl_dem_rights_lab","s_eep_economic_business","intl_gentech","intl_cyber","intl_climate"]),
          ("actionKind", "string", True, ["bilateral_treaty","mou_arrangement","cable_diplomatic","press_briefing","sanctions_state_dept","arms_export_review_itar","arms_sales_dscv","treaty_signature","consular_warning","travel_advisory_3_4","statement_of_concern","support_letter","mil_to_mil_engagement","strategic_dialogue"]),
          ("relatedActorVid", "string", False, None, "bridges extradition-treaty / interpol-redabuse"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInterAgencyConflict",
        "desc": "State Dept inter-agency / DOD vs State / NSC override (bridges treasury-rulemaking + transnational-repression + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("conflictKind", "string", True, ["dod_vs_state","cia_vs_state","treasury_sanctions_vs_state","nsc_override","white_house_freelance","staffer_diss","ambassador_recall","whistleblower_diss","public_servant_diss_act","witness_at_congress","unauthorized_engagement"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "eu-dg-comp",
    "app": "euDgComp",
    "methods": [
      {
        "name": "recordAction",
        "desc": "EU DG Competition action / state aid / antitrust / merger (bridges antitrust-dma + merger-review + esma-convergence)",
        "fields": [
          ("actionId", "string", True),
          ("regimeKind", "string", True, ["antitrust_101","antitrust_102","merger_eumr","state_aid_107","public_undertaking_106","cartel_leniency","sector_inquiry","commitment_decision","behavioral_remedy","structural_remedy","dma_designation","dma_compliance_report","sgei_state_aid","r_d_state_aid","ipcei"]),
          ("subjectLei", "string", False),
          ("relatedActorVid", "string", False, None, "bridges antitrust-dma / merger-review / dsa-vlop"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPoliticalPressure",
        "desc": "Political pressure / cabinet meddling / member-state lobbying (bridges antitrust-dma + euTrilogue + frugalFourCoalition)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("pressureKind", "string", True, ["member_state_lobbying","champion_protection","industrial_policy_carveout","strategic_autonomy_argument","national_security_invocation","commission_political_intervention","ep_pressure","council_request_review","dg_grow_vs_comp","dg_trade_vs_comp","sg_steering","cabinet_redraft"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "eu-dg-clima",
    "app": "euDgClima",
    "methods": [
      {
        "name": "recordAction",
        "desc": "EU DG Climate Action policy / ETS / CBAM / Fit for 55 (bridges cbam-embedded + climate-value-chain + euTrilogue)",
        "fields": [
          ("actionId", "string", True),
          ("policyKind", "string", True, ["ets_cap_review","ets_aviation","ets_maritime","cbam_phase","fit_for_55","climate_law_revision","mrv_shipping","mrv_aviation","carbon_market_buildup","accc_anti_crisis","industrial_decarb","just_transition_fund","green_taxonomy","sfdr_climate","csrd_climate"]),
          ("scopeKind", "string", True, ["sector_steel","sector_cement","sector_aluminium","sector_chemicals","sector_aviation","sector_shipping","sector_road","sector_buildings","sector_lulucf","economy_wide","cross_border","third_country"]),
          ("relatedActorVid", "string", False, None, "bridges cbam-embedded / euTrilogue / climate-value-chain"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagComplianceGap",
        "desc": "Compliance gap / national lag / leakage concern (bridges cbam-embedded + climate-value-chain + frugalFourCoalition)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("gapKind", "string", True, ["national_transposition_lag","ets_phase_4_compliance","cbam_under_reporting","carbon_leakage_evidence","industrial_carve_out_abuse","backloading","msr_intervention","frugal_block","mediterranean_block","just_transition_funding","competitiveness_relief","cross_border_loophole"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "jp-mof",
    "app": "jpMof",
    "methods": [
      {
        "name": "recordAction",
        "desc": "日本財務省 action / 予算 / 為替 / 国際金融 (bridges advanceTaxRuling + bepsPillar + sovereign-debt)",
        "fields": [
          ("actionId", "string", True),
          ("bureau", "string", True, ["honsho_minister","shukei_budget","shusha_revenue","shukan_customs_tariff","kokuyu_tax","saimu_debt_management","kokusai_intl","kanzei_customs","kokugu_treasury","fsa_jfsa_supervisory","jcps_rinkoku_jbic","nettzaisei_pension","atomori_grants"]),
          ("actionKind", "string", True, ["budget_jp","supplementary_budget","jgb_issuance","fx_intervention","fx_intervention_authorization","stamp_duty_change","ineffective_protection","insurance_finance_act","tax_treaty_signed","oecd_tax_treaty","kokueki_kankei_intl","sankei_tomoyari_aid","jbic_loan","jica_loan","emergency_fiscal"]),
          ("relatedActorVid", "string", False, None, "bridges advanceTaxRuling / bepsPillar / fxSwapLines"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInterAgencyTension",
        "desc": "MOF inter-agency tension / 内閣府 vs 財務省 / 経産省 vs 財務省 (bridges treasury-rulemaking + judicial-influence + bepsPillar)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("tensionKind", "string", True, ["naikakufu_vs_mof","meti_vs_mof","mext_vs_mof","mhlw_vs_mof","mlit_vs_mof","jdg_vs_mof","mof_vs_boj","kantei_override","fiscal_council_vote","tax_committee_kacho","ldp_zaiseichoukan","ldp_seimuchoukai","komeito_block","yatou_block"]),
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
    out = Path(f"/tmp/wave13/w95_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
