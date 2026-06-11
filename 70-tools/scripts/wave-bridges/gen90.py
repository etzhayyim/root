#!/usr/bin/env python3
"""Wave 90 — eurogroup-decision / bar-association-recall / deepfake-takedown / bilateral-investment-treaty / trusted-flagger.

All-string. Bridges Wave 89.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "eurogroup-decision",
    "app": "eurogroupDecision",
    "methods": [
      {
        "name": "recordDecision",
        "desc": "Eurogroup political-body decision (bridges euStabilityMechanism.flagBoardDispute + euTrilogue + euSummitConclusion)",
        "fields": [
          ("decisionId", "string", True),
          ("topic", "string", True, ["fiscal_stance","banking_union","capital_markets_union","esm_treaty","digital_euro","euro_excl_in","convergence","sgp_review","budget_recommendation","macro_imbalance","ngeu","rrf"]),
          ("formatKind", "string", True, ["plenary","inclusive","wkg","high_level","preparatory","tripartite","press_remarks","statement","conclusions","term_sheet"]),
          ("boardDisputeVid", "string", False, None, "bridges euStabilityMechanism.flagBoardDispute"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPoliticalRift",
        "desc": "Eurogroup political rift / north-south divide (bridges euStabilityMechanism.flagBoardDispute + euTrilogue + euSummitConclusion)",
        "fields": [
          ("flagId", "string", True),
          ("decisionVid", "string", True, None, "bridges recordDecision"),
          ("riftKind", "string", True, ["north_south","east_west","creditor_debtor","frugal_four","new_hanseatic","mediterranean","periphery_core","banking_union_resist","capital_markets_disagree","euro_inclusion_disagree","fiscal_capacity"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "bar-association-recall",
    "app": "barAssociationRecall",
    "methods": [
      {
        "name": "recordRecall",
        "desc": "Bar / law-society professional discipline (bridges judicialAppointment.flagPoliticization + ethics-disclosure + judge-rapporteur)",
        "fields": [
          ("recallId", "string", True),
          ("barJurisdiction", "string", True),
          ("respondentRole", "string", True, ["practicing_lawyer","judge","prosecutor","public_defender","corporate_counsel","government_lawyer","bar_committee","former_judge","retired","disbarred_seeking_reinstatement"]),
          ("violationKind", "string", True, ["misappropriation","ethics_violation","conflict_of_interest","filing_false","frivolous_litigation","abuse_of_process","client_abandon","mandatory_reporting_fail","false_advertising","gross_negligence","insurrection","pro_hac_vice"]),
          ("politicizationVid", "string", False, None, "bridges judicialAppointment.flagPoliticization"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBaselineConcern",
        "desc": "Selective enforcement / political prosecution / due process gap (bridges judicialAppointment.flagPoliticization + civilLiability + ethicsDisclosure)",
        "fields": [
          ("flagId", "string", True),
          ("recallVid", "string", True, None, "bridges recordRecall"),
          ("concernKind", "string", True, ["selective_enforcement","political_prosecution","due_process_gap","slow_walking","minor_offense_only","appeal_blocked","reinstatement_denied","no_speedy_hearing","witness_tampering","panel_packing","whistleblower_retaliation"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "deepfake-takedown",
    "app": "deepfakeTakedown",
    "methods": [
      {
        "name": "recordTakedown",
        "desc": "Deepfake / synthetic media takedown order (bridges aiWatermark.flagEvasion + dsa-vlop + transnational-repression)",
        "fields": [
          ("takedownId", "string", True),
          ("targetCategory", "string", True, ["politician","celebrity","journalist","minor_csam","financial_fraud","election_meddle","corporate_executive","ambassador","activist","scientist","public_figure","private_individual"]),
          ("modality", "string", True, ["voice_clone_video","voice_only","face_swap","talking_head","whole_body","text_to_video","real_time_avatar","puppet_video","ai_news","mash_up","audio_endorse"]),
          ("evasionVid", "string", False, None, "bridges aiWatermark.flagEvasion"),
          ("orderedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDistributionVector",
        "desc": "Distribution vector / off-platform spread (bridges aiWatermark.flagEvasion + dsa-vlop + social-media-influence-op)",
        "fields": [
          ("flagId", "string", True),
          ("takedownVid", "string", True, None, "bridges recordTakedown"),
          ("vectorKind", "string", True, ["livestream_replay","whatsapp_forward","telegram_channel","sms_blast","tiktok_loop","instagram_reel","x_repost","reddit_thread","blog_embed","podcast_clip","clipboard_share","email_phishing","encrypted_dm"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "bilateral-investment-treaty",
    "app": "bilateralInvestmentTreaty",
    "methods": [
      {
        "name": "recordEntry",
        "desc": "Bilateral Investment Treaty entry / amendment / termination (bridges mineralRoyalty.flagInvestorClaim + sovereign-debt + universal-jurisdiction)",
        "fields": [
          ("entryId", "string", True),
          ("partyAIso3", "string", True),
          ("partyBIso3", "string", True),
          ("entryKind", "string", True, ["new_treaty","amendment","ratification","provisional_application","unilateral_termination","mutual_termination","sunset_clause","substitution_modern","mit_eu_termination","carve_out","most_favored_nation"]),
          ("scopeKind", "string", True, ["full_market_access","investment_protection","investor_state_dispute","fair_equitable","most_favored_nation","national_treatment","expropriation_clause","substitution_2024","portfolio_only","green_screen_carve"]),
          ("investorClaimVid", "string", False, None, "bridges mineralRoyalty.flagInvestorClaim"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSurvivalClause",
        "desc": "Survival / sunset clause stress (bridges mineralRoyalty.flagInvestorClaim + sovereign-debt + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("entryVid", "string", True, None, "bridges recordEntry"),
          ("issueKind", "string", True, ["sunset_15yr","sunset_20yr","staggered_protection","retroactive_carveout","termination_dispute_pre_existing","survival_only_specific","interpretation_dispute","grandfathering","scope_drift","most_favored_nation_drag"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "trusted-flagger",
    "app": "trustedFlagger",
    "methods": [
      {
        "name": "recordDesignation",
        "desc": "DSA trusted flagger / DSC designation (bridges dsaVlop.flagSystemicRisk + dpa-authority + cross-border-transfer)",
        "fields": [
          ("designationId", "string", True),
          ("flaggerKind", "string", True, ["ngo","minor_protect","csam_iwf","internet_org","industry_alliance","interpol","europol","eu_law_enforce","national_csb","trade_assoc","media_council","fact_checker"]),
          ("memberStateIso3", "string", True),
          ("dscIssuingAuthority", "string", True),
          ("systemicRiskVid", "string", False, None, "bridges dsaVlop.flagSystemicRisk"),
          ("designatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAbuseConcern",
        "desc": "Trusted flagger abuse / over-flagging / cross-border (bridges dsaVlop.flagSystemicRisk + transnational-repression + press-freedom)",
        "fields": [
          ("flagId", "string", True),
          ("designationVid", "string", True, None, "bridges recordDesignation"),
          ("concernKind", "string", True, ["over_flagging","political_target","frivolous","cross_border_overreach","quality_control_gap","pattern_of_misuse","appeal_disregard","government_capture","industry_capture","spec_state_targeting","data_protection_breach"]),
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
    out = Path(f"/tmp/wave13/w90_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
