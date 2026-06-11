#!/usr/bin/env python3
"""Wave 93 — gap-fill pivot: electricity-market / drug-price / higher-ed-accred / reinsurance / BEPS.

Targets coverage holes identified in the world-coverage audit.
All-string schemas. Bridges Wave 92 (where coherent) + holes.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "electricity-market",
    "app": "electricityMarket",
    "methods": [
      {
        "name": "recordMechanism",
        "desc": "Wholesale / retail electricity market mechanism (capacity market / FIT / CfD — bridges fossilStrandedAsset.flagJustTransitionGap + power-grid-interconnect + just-transition)",
        "fields": [
          ("mechanismId", "string", True),
          ("countryIso3", "string", True),
          ("mechanismKind", "string", True, ["capacity_market","feed_in_tariff","ppa_corporate","cfd_strike","auction_renewables","day_ahead","intraday","balancing","ancillary_freq","carbon_intensity_obligation","battery_aggregator","ders","virtual_pp","negative_pricing","capacity_remuneration","strategic_reserve"]),
          ("technologyKind", "string", True, ["solar_pv","onshore_wind","offshore_wind","gas_ccgt","coal_phase","nuclear_baseload","nuclear_smr","battery_storage","pumped_hydro","biomass","geothermal","hydrogen","grid_form_battery","demand_response"]),
          ("strandedVid", "string", False, None, "bridges fossilStrandedAsset.flagJustTransitionGap"),
          ("introducedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMissingMoney",
        "desc": "Missing-money / capacity adequacy / negative price abuse (bridges fossilStrandedAsset.flagJustTransitionGap + power-grid-interconnect + sovereign-debt)",
        "fields": [
          ("flagId", "string", True),
          ("mechanismVid", "string", True, None, "bridges recordMechanism"),
          ("issueKind", "string", True, ["missing_money","scarcity_pricing_inadequate","price_cap_too_tight","capacity_payment_distortion","subsidy_overlap","cross_border_distortion","loop_flow","wind_curtailment","solar_curtailment","battery_arbitrage_concern","resource_adequacy_failure","ela_event"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "drug-price-negotiation",
    "app": "drugPriceNegotiation",
    "methods": [
      {
        "name": "recordRound",
        "desc": "Drug price negotiation / HTA / formulary listing (bridges vaccineEquity.flagAccessGap + pharma-supply + universal-health-coverage)",
        "fields": [
          ("roundId", "string", True),
          ("regimeKind", "string", True, ["us_ira_negotiation","uk_nice","de_ahmg","fr_ceps","ita_aifa","jp_chuikyo","kr_hira","au_pbs","ca_pcpa","br_cmed","mx_imss","cn_nrdl","sg_aca","is_lif_pricing","tw_nhi"]),
          ("therapeuticArea", "string", True, ["oncology","rare_disease","alzheimer","diabetes","obesity","cardiovascular","respiratory","mental_health","autoimmune","gene_therapy","ovid_post","cell_therapy","crispr_therapy"]),
          ("pharmaCompanyLei", "string", False),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAccessGap",
        "desc": "Access gap / launch delay / managed-access scheme (bridges vaccineEquity.flagAccessGap + universal-health-coverage + pharma-supply)",
        "fields": [
          ("flagId", "string", True),
          ("roundVid", "string", True, None, "bridges recordRound"),
          ("gapKind", "string", True, ["launch_delay","reimbursement_denied","managed_access","conditional_reimbursement","price_volume_agreement","outcomes_based","late_inclusion","ema_lagged","fda_lagged","commission_pricing_dispute","parallel_import","lmic_excluded"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "higher-education-accred",
    "app": "higherEducationAccred",
    "methods": [
      {
        "name": "recordAccreditation",
        "desc": "University / programme accreditation event (bridges apprenticeshipReg.flagCompletionGap + credential-portability + course)",
        "fields": [
          ("accreditationId", "string", True),
          ("institutionLei", "string", False),
          ("accreditorKind", "string", True, ["us_regional","us_national","abet","aacsb","equis","amba","jabee","jab_japan","aishe_india","mufu_china","aqu_spain","mas_singapore","tequip","cti_chile","mqf_malta","aqic_iran","caebep","csgs"]),
          ("scopeKind", "string", True, ["institution","programme","engineering","business","medical","law","architecture","teacher_ed","graduate","online_degree","mba","executive_ed","new_programme","renewal","probation","withdrawal"]),
          ("completionGapVid", "string", False, None, "bridges apprenticeshipReg.flagCompletionGap"),
          ("decidedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDiplomaConcern",
        "desc": "Diploma mill / mass shutdown / cross-border recognition gap (bridges apprenticeshipReg.flagCompletionGap + credential-portability + transnational-repression)",
        "fields": [
          ("flagId", "string", True),
          ("accreditationVid", "string", True, None, "bridges recordAccreditation"),
          ("concernKind", "string", True, ["diploma_mill","mass_shutdown","fraudulent_credentials","cross_border_recognition_denied","esg_compliance","tuition_fraud","predatory_recruitment","quality_control_breach","branch_campus_collapse","accreditor_revoke","quality_assurance_drift"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "reinsurance-treaty",
    "app": "reinsuranceTreaty",
    "methods": [
      {
        "name": "recordTreaty",
        "desc": "Reinsurance treaty placement (proportional / non-proportional / catastrophe — bridges shadowFleetInsurance.flagGapOrFraud + insurance-policy + cat-bond-ils)",
        "fields": [
          ("treatyId", "string", True),
          ("cedentLei", "string", False),
          ("reinsurerLei", "string", False),
          ("treatyKind", "string", True, ["quota_share","surplus_share","working_xol","cat_xol","stop_loss","aggregate_xol","retro","ils_cat_bond","sidecar","whole_account","facultative","loss_portfolio_transfer"]),
          ("perilKind", "string", True, ["nat_cat_storm","nat_cat_quake","wildfire","flood","cyber","liability_long_tail","casualty","credit_political_risk","marine_war","aviation_war","nuclear_pool","pandemic","terror"]),
          ("shadowGapVid", "string", False, None, "bridges shadowFleetInsurance.flagGapOrFraud"),
          ("incepedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCapacityCrunch",
        "desc": "Capacity crunch / hardening cycle / climate exit (bridges shadowFleetInsurance.flagGapOrFraud + climate-adaptation-finance + cat-bond-ils)",
        "fields": [
          ("flagId", "string", True),
          ("treatyVid", "string", True, None, "bridges recordTreaty"),
          ("crunchKind", "string", True, ["hard_market_pricing","capacity_withdrawal","retro_squeeze","ils_outflow","wildfire_exit_california","flood_exit","climate_attribution","fronting_collapse","monoline_failure","s_p_bbb_drop","mga_capacity_pull"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "beps-pillar",
    "app": "bepsPillar",
    "methods": [
      {
        "name": "recordImplementation",
        "desc": "OECD BEPS Pillar 1 / Pillar 2 implementation (bridges advanceTaxRuling + global-tax + tax-transparency)",
        "fields": [
          ("implementationId", "string", True),
          ("countryIso3", "string", True),
          ("pillarKind", "string", True, ["pillar_1_amt_a","pillar_1_amt_b","pillar_2_gloBE","pillar_2_qdmtt","pillar_2_iir","pillar_2_utpr","pillar_2_pillar_2_safe","stt_substantial_test","gloBE_15pct"]),
          ("statusKind", "string", True, ["adopted","draft_law","cabinet_approved","under_consultation","legislation_pending","applies_2024","applies_2025","applies_2026","carve_out_invoked","substance_test","minimum_revenue_750_million"]),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSpilloverConcern",
        "desc": "Spillover / digital tax race / unilateral measure resurgence (bridges global-tax + advanceTaxRuling + ustr-section-301)",
        "fields": [
          ("flagId", "string", True),
          ("implementationVid", "string", True, None, "bridges recordImplementation"),
          ("concernKind", "string", True, ["unilateral_dst_resurgence","ustr_301_threat","scope_dispute_amount_a","carve_out_extractive","carve_out_financial_services","carve_out_shipping","exit_tax_shift","substance_test_loophole","switzerland_referendum","fr_dst","uk_dst","brexit_pillar2_friction","dispute_settlement_proxy"]),
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
    out = Path(f"/tmp/wave13/w93_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
