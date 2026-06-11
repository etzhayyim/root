#!/usr/bin/env python3
"""Wave 67 — ethics-disclosure / fatf-greylist / extradition-treaty / securities-investor / wto-trade-cbam.

Bridges Wave 66:
- ethics-disclosure ↔ judicialInfluence.flagConflictOfInterest
- fatf-greylist ↔ bearerShare.flagLoophole
- extradition-treaty ↔ universalJurisdiction.flagExecutiveInterference
- securities-investor ↔ soxBounty.flagAwardDispute
- wto-trade-cbam ↔ cbamEmbedded.flagLeakage
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "ethics-disclosure",
    "app": "ethicsDisclosure",
    "methods": [
      {
        "name": "recordFiling",
        "desc": "Judicial / executive / legislative financial disclosure filing (bridges judicialInfluence.flagConflictOfInterest + enforcement-action + federal-court-docket)",
        "fields": [
          ("filingId", "string", True),
          ("officeKind", "string", True, ["scotus_justice","federal_judge","appellate_judge","magistrate","state_supreme","governor","federal_executive","cabinet","senator","rep","regulator_head","agency_ig","mtalf"]),
          ("regime", "string", True, ["ethics_government_act","28_usc_app","fed_judiciary_canons","stock_act","eu_transparency_reg","uk_ministerial_code","ca_conflict_act","fr_hatvp","jp_ethics_act","de_abghg"]),
          ("conflictVid", "string", False, None, "bridges judicialInfluence.flagConflictOfInterest"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDisclosureGap",
        "desc": "Missing disclosure / recusal failure / spouse loophole (bridges judicialInfluence.flagConflictOfInterest + enforcement-action + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("filingVid", "string", True, None, "bridges recordFiling"),
          ("gapKind", "string", True, ["missing_gift","missing_travel","missing_property","spouse_loophole","blind_trust_fake","recusal_failure","post_employment","shadow_advisor","consulting_side","opaque_foundation","incomplete_amendment"]),
          ("undeclaredValueUsd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "fatf-greylist",
    "app": "fatfGreylist",
    "methods": [
      {
        "name": "recordListingChange",
        "desc": "FATF / EU / UK greylist / blacklist listing change (bridges bearerShare.flagLoophole + sanctions-entry + aml)",
        "fields": [
          ("changeId", "string", True),
          ("jurisdictionIso3", "string", True),
          ("listKind", "string", True, ["fatf_black","fatf_grey","eu_third_high_risk","uk_amlr","us_8206","jp_msb_risk","fatf_progress","fatf_off_ramp","fatf_icrg","fatf_monitored"]),
          ("actionKind", "string", True, ["added","removed","upgraded","downgraded","partial_delist","increased_monitoring","enhanced_due_diligence","counter_measures"]),
          ("loopholeVid", "string", False, None, "bridges bearerShare.flagLoophole"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagReputationSpillover",
        "desc": "Correspondent derisking / FDI drop / cost-of-funds premium (bridges bearerShare.flagLoophole + correspondentBanking + debt-transparency)",
        "fields": [
          ("flagId", "string", True),
          ("changeVid", "string", True, None, "bridges recordListingChange"),
          ("impactKind", "string", True, ["cbr_exit","fdi_drop","yield_premium","trade_finance_tighten","mto_corridor_close","imf_warning","rating_downgrade","capital_outflow","dedollarization_push","remittance_squeeze"]),
          ("estBusdImpact", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "extradition-treaty",
    "app": "extraditionTreaty",
    "methods": [
      {
        "name": "recordRequest",
        "desc": "Bilateral / multilateral extradition request (bridges universalJurisdiction.flagExecutiveInterference + legal-document + federal-court-docket)",
        "fields": [
          ("requestId", "string", True),
          ("requestingCountryIso3", "string", True),
          ("requestedCountryIso3", "string", True),
          ("treatyBasis", "string", True, ["bilateral_treaty","european_convention","schengen_arrest","interpol_red","uncat_aut_dedere","commonwealth_london","unidroit","ad_hoc","comity"]),
          ("offenceCategory", "string", True, ["fraud","corruption","organized_crime","drug","terrorism","war_crimes","torture","sanctions","trafficking_persons","trafficking_weapons","cyber","environmental","kleptocracy"]),
          ("ujCaseVid", "string", False, None, "bridges universalJurisdiction.flagExecutiveInterference"),
          ("submittedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDenial",
        "desc": "Extradition denial / asylum grant / political offense exception (bridges universalJurisdiction.flagExecutiveInterference + refugee-unhcr + press-freedom)",
        "fields": [
          ("flagId", "string", True),
          ("requestVid", "string", True, None, "bridges recordRequest"),
          ("groundsKind", "string", True, ["political_offense","death_penalty_block","torture_risk","fair_trial_risk","nationality_bar","statute_of_limitations","dual_criminality","specialty_rule","sovereign_decree","asylum_grant","citizenship_weaponized"]),
          ("daysToDecision", "integer", False),
          ("deniedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "securities-investor",
    "app": "securitiesInvestor",
    "methods": [
      {
        "name": "recordDisbursement",
        "desc": "SEC Fair Fund / SIPC / investor recovery disbursement (bridges soxBounty.flagAwardDispute + enforcementAction + class-settlement)",
        "fields": [
          ("disbursementId", "string", True),
          ("fundKind", "string", True, ["sec_fair_fund","sec_disgorgement","sipc","fdic_receiver","occ_restitution","fca_redress","bafin_investor","jfsa_restitution","mas_investor","iosco_cross_border","private_fund_compensation"]),
          ("underlyingCaseKind", "string", True, ["ponzi","insider","market_manip","accounting_fraud","misrepresentation","unauthorized_trading","fiduciary","theft","late_trading","bitrate_trading","cybersecurity_disclosure"]),
          ("awardDisputeVid", "string", False, None, "bridges soxBounty.flagAwardDispute"),
          ("payoutMusd", "number", False),
          ("finalizedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagLowRecovery",
        "desc": "Low recovery rate / forgotten claimant / claim fatigue (bridges soxBounty.flagAwardDispute + consumer-protection + class-settlement)",
        "fields": [
          ("flagId", "string", True),
          ("disbursementVid", "string", True, None, "bridges recordDisbursement"),
          ("gapKind", "string", True, ["low_claim_rate","expired_claims","unreachable_investor","burden_docs","cy_pres_leftover","administrator_profit","gross_net_spread","plan_delayed","tax_treatment_confusion","foreign_cap"]),
          ("unrecoveredMusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "wto-trade-cbam",
    "app": "wtoTradeCbam",
    "methods": [
      {
        "name": "recordSpecificTradeConcern",
        "desc": "WTO STC / CTTE / CBAM trade-environment concern (bridges cbamEmbedded.flagLeakage + wto-dispute + eu-cbam)",
        "fields": [
          ("stcId", "string", True),
          ("raisingMemberIso3", "string", True),
          ("againstMemberIso3", "string", True),
          ("forum", "string", True, ["wto_cte","wto_cttd","wto_ctg","wto_sps","wto_tbt","wto_pmeu","g20_trade","commerce_summit","asean_trade"]),
          ("concernKind", "string", True, ["trade_disruption","discriminatory","most_favoured_nation","unilateral_standard","extraterritorial","cbam_scope","lca_methodology","default_value","least_developed_carveout","transition_period"]),
          ("leakageVid", "string", False, None, "bridges cbamEmbedded.flagLeakage"),
          ("raisedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDisputeEscalation",
        "desc": "Panel request / retaliation list / safeguard (bridges cbamEmbedded.flagLeakage + wto-dispute + ustr-section-301)",
        "fields": [
          ("flagId", "string", True),
          ("stcVid", "string", True, None, "bridges recordSpecificTradeConcern"),
          ("escalationKind", "string", True, ["panel_request","consultations","authorized_retaliation","suspension_concessions","compliance_panel","article_xxi_invocation","interim_measures","sanctions_secondary","mpia_appeal","review_22_6"]),
          ("affectedTradeBusd", "number", False),
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
            if ftype == "integer" and any(k in col for k in ["size","years","days","count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected"]):
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
    out = Path(f"/tmp/wave13/w67_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
