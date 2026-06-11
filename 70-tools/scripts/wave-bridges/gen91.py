#!/usr/bin/env python3
"""Wave 91 — frugal-four / judicial-misconduct / mass-messaging / energy-charter-exit / content-mod-appeal.

All-string. Bridges Wave 90.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "frugal-four-coalition",
    "app": "frugalFourCoalition",
    "methods": [
      {
        "name": "recordPosition",
        "desc": "Frugal Four / New Hanseatic / fiscal-rules coalition position (bridges eurogroupDecision.flagPoliticalRift + euTrilogue + euSummitConclusion)",
        "fields": [
          ("positionId", "string", True),
          ("coalition", "string", True, ["frugal_four","new_hanseatic","mediterranean","sgp_reform_block","esm_block","banking_union_block","capital_markets_block","carbon_border_pro","carbon_border_skeptic","ngeu_redirection_block","grants_to_loans_swap"]),
          ("memberStateIso3", "string", True),
          ("dossier", "string", True, ["mff_2028","sgp_reform","banking_union","capital_markets","ngeu_review","esm_treaty","tpi","fiscal_capacity","crisis_facility","financial_stability"]),
          ("riftVid", "string", False, None, "bridges eurogroupDecision.flagPoliticalRift"),
          ("expressedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSwingShift",
        "desc": "Coalition swing / member defection / external pressure (bridges eurogroupDecision.flagPoliticalRift + euSummitConclusion + euTrilogue)",
        "fields": [
          ("flagId", "string", True),
          ("positionVid", "string", True, None, "bridges recordPosition"),
          ("shiftKind", "string", True, ["member_defection","leadership_change","external_shock","commission_compromise","ep_majority_pressure","domestic_pressure","financial_stability_argument","accession_pressure","russia_threat","china_pressure","new_member_dilute"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "judicial-misconduct-board",
    "app": "judicialMisconductBoard",
    "methods": [
      {
        "name": "recordComplaint",
        "desc": "Judicial misconduct complaint / commission review (bridges barAssociationRecall.flagBaselineConcern + judicialAppointment + ethics-disclosure)",
        "fields": [
          ("complaintId", "string", True),
          ("forumKind", "string", True, ["us_federal_judiciary","us_state_jud_disc","ca_judicial_council","uk_judicial_office","csm_italy","csmj_france","kj_korea","cnnj_chile","srgj_germany","jio_japan","cmm_india_imp"]),
          ("misconductKind", "string", True, ["bias","financial","ex_parte","abuse_of_position","political_speech","disability_judiciary","pattern_demeanor","social_media","extra_judicial","gifts_undisclosed","preferential_treatment"]),
          ("baselineVid", "string", False, None, "bridges barAssociationRecall.flagBaselineConcern"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagOutcomeBias",
        "desc": "Selective outcome / impeachment threshold / appeal stall (bridges barAssociationRecall.flagBaselineConcern + judicialAppointment + civilLiability)",
        "fields": [
          ("flagId", "string", True),
          ("complaintVid", "string", True, None, "bridges recordComplaint"),
          ("outcomeKind", "string", True, ["dismissed_no_action","admonishment","censure","suspension","retirement_stipulated","impeachment_referred","appeal_stalled","sealed","public_hearing","political_immunity_invoked","peer_review_inadequate"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "mass-messaging-platform",
    "app": "massMessagingPlatform",
    "methods": [
      {
        "name": "recordModerationPolicy",
        "desc": "WhatsApp / Telegram / Signal moderation policy update (bridges deepfakeTakedown.flagDistributionVector + dsa-vlop + cross-border-transfer)",
        "fields": [
          ("policyId", "string", True),
          ("platform", "string", True, ["whatsapp","telegram","signal","wechat","kakaotalk","line","viber","threema","element","matrix_protocol","facebook_messenger","instagram_dm"]),
          ("policyKind", "string", True, ["forwarding_limit","group_size_cap","content_blur","csam_hash_match","aml_kyc_groups","government_request_cooperation","public_channel_takedown","bot_invitation","client_side_scanning","non_chat_features"]),
          ("distributionVid", "string", False, None, "bridges deepfakeTakedown.flagDistributionVector"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagEnforcementGap",
        "desc": "Enforcement gap / encrypted vs unencrypted / metadata leak (bridges deepfakeTakedown.flagDistributionVector + dsa-vlop + transnational-repression)",
        "fields": [
          ("flagId", "string", True),
          ("policyVid", "string", True, None, "bridges recordModerationPolicy"),
          ("gapKind", "string", True, ["e2e_encryption_blocker","metadata_leak","group_admin_proxy","public_channel_loophole","bot_amplification","sticker_pack_threat","forwarded_label_strip","cross_platform_hop","sim_swap_takeover","backup_unencrypted","government_backdoor_demand"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "energy-charter-exit",
    "app": "energyCharterExit",
    "methods": [
      {
        "name": "recordExitNotice",
        "desc": "Energy Charter Treaty (ECT) modernization / exit notice (bridges bilateralInvestmentTreaty.flagSurvivalClause + climate-litigation + just-transition)",
        "fields": [
          ("noticeId", "string", True),
          ("memberStateIso3", "string", True),
          ("noticeKind", "string", True, ["unilateral_withdrawal","coordinated_eu","stay_in_modernized","carve_out_negotiated","carbon_carve_out","article_47_exit","sunset_clause_concern","investor_state_clause_strip","amf_french_modify","modernised_join","amendment_only"]),
          ("survivalVid", "string", False, None, "bridges bilateralInvestmentTreaty.flagSurvivalClause"),
          ("noticedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInvestorClaimSurge",
        "desc": "Investor claim surge / sunset 20-year tail / fossil-asset litigation (bridges bilateralInvestmentTreaty.flagSurvivalClause + mineralRoyalty.flagInvestorClaim + climate-value-chain)",
        "fields": [
          ("flagId", "string", True),
          ("noticeVid", "string", True, None, "bridges recordExitNotice"),
          ("issueKind", "string", True, ["fossil_asset_loss","carbon_levy_dispute","grandfathering","unilateral_treaty_termination_litigation","arbitration_seat_change","escape_via_holding","investor_circumvention","national_court_only","umbrella_clause"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "content-moderation-appeal",
    "app": "contentModerationAppeal",
    "methods": [
      {
        "name": "recordAppeal",
        "desc": "DSA Article 17 / DSC complaint / out-of-court dispute (bridges trustedFlagger.flagAbuseConcern + dsa-vlop + dpa-authority)",
        "fields": [
          ("appealId", "string", True),
          ("platform", "string", True),
          ("forum", "string", True, ["internal_review","oversight_board_meta","court_independent","dsc_designated","article_21_dispute_body","national_court","trusted_arbitrator","ngo_mediator","oosc_oversight"]),
          ("complainantCategory", "string", True, ["user_creator","brand","political_party","ngo","journalist","lawyer_pro_bono","trade_assoc","government_entity"]),
          ("abuseConcernVid", "string", False, None, "bridges trustedFlagger.flagAbuseConcern"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagOutcomeAsymmetry",
        "desc": "Outcome asymmetry / well-resourced wins / forum-shopping (bridges trustedFlagger.flagAbuseConcern + dsa-vlop + civilLiability)",
        "fields": [
          ("flagId", "string", True),
          ("appealVid", "string", True, None, "bridges recordAppeal"),
          ("issueKind", "string", True, ["well_resourced_wins","forum_shop","corporate_lawyer_advantage","language_barrier","appeal_timeout","reinstatement_unenforceable","monetary_damages_minimal","statistical_pattern_no_redress","platform_compliance_only","disclosure_redacted","third_party_observer_block"]),
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
    out = Path(f"/tmp/wave13/w91_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
