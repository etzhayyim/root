#!/usr/bin/env python3
"""Wave 92 — eu-mff-2028 / impeachment-trial / encryption-debate / fossil-stranded-asset / meta-oversight-board.

All-string. Bridges Wave 91.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "eu-mff-2028",
    "app": "euMff2028",
    "methods": [
      {
        "name": "recordHeading",
        "desc": "EU Multiannual Financial Framework 2028+ heading proposal (bridges frugalFourCoalition.flagSwingShift + euTrilogue + euSummitConclusion)",
        "fields": [
          ("headingId", "string", True),
          ("headingKind", "string", True, ["heading_1_single_market","heading_2_cohesion","heading_3_natural_resources","heading_4_migration","heading_5_security","heading_6_neighbourhood","heading_7_admin","ngeu_successor","competitiveness_fund","ukraine_facility","defence","crisis","new_own_resources"]),
          ("budgetSizeKind", "string", True, ["below_1pct_gni","at_1pct_gni","above_1pct_gni","headroom_increase","accc_anti_crisis"]),
          ("swingShiftVid", "string", False, None, "bridges frugalFourCoalition.flagSwingShift"),
          ("proposedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAccessionPressure",
        "desc": "Accession-driven MFF strain (Ukraine, Western Balkans) (bridges frugalFourCoalition.flagSwingShift + euSummitConclusion + sovereign-debt)",
        "fields": [
          ("flagId", "string", True),
          ("headingVid", "string", True, None, "bridges recordHeading"),
          ("strainKind", "string", True, ["ukraine_accession","wb6_accession","moldova","cap_recipient_dilution","cohesion_recipient_dilution","budget_neutrality_demand","headroom_unrealistic","crisis_facility_demand","resource_own_block","gravity_capacity"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "impeachment-trial",
    "app": "impeachmentTrial",
    "methods": [
      {
        "name": "recordTrial",
        "desc": "Impeachment / removal trial (executive / judicial) (bridges judicialMisconductBoard.flagOutcomeBias + scotusDocket + transnational-repression)",
        "fields": [
          ("trialId", "string", True),
          ("subjectRole", "string", True, ["president","prime_minister","cabinet_minister","governor","judge","constitutional_judge","senator","mp","ag_attorney_general","central_bank_chief","ig"]),
          ("forum", "string", True, ["us_senate","us_house_inquiry","uk_recall","de_constitutional","kr_constitutional","br_senate","peru_congress","sa_supreme","mx_constitutional","ph_senate","arg_senate"]),
          ("groundsKind", "string", True, ["high_crimes","abuse_of_power","obstruction","corruption","betrayal_of_trust","violation_of_constitution","treason","misuse_of_funds","perjury","contempt_of_court","incitement"]),
          ("outcomeBiasVid", "string", False, None, "bridges judicialMisconductBoard.flagOutcomeBias"),
          ("commencedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPartisanVote",
        "desc": "Partisan vote pattern / threshold gaming (bridges judicialMisconductBoard.flagOutcomeBias + transnational-repression + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("trialVid", "string", True, None, "bridges recordTrial"),
          ("votePatternKind", "string", True, ["near_unanimous","strict_party_line","threshold_2_3","threshold_3_4","absent_strategic","cross_party_few","resignation_pre_vote","censure_only","witness_blocked","subpoena_quashed","public_hearing_denied"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "encryption-debate",
    "app": "encryptionDebate",
    "methods": [
      {
        "name": "recordPolicyMove",
        "desc": "Encryption policy / Going-Dark / CSAM-regulation move (bridges massMessagingPlatform.flagEnforcementGap + dpa-authority + cross-border-transfer)",
        "fields": [
          ("moveId", "string", True),
          ("jurisdiction", "string", True),
          ("moveKind", "string", True, ["csam_scanning_proposal","mandatory_backdoor","ghost_protocol","key_escrow_revival","encrypted_dns_block","metadata_retention","client_side_scanning_law","duty_to_report","investigatory_powers_act_amendment","online_safety_act_amend","france_ssi_law","jp_revisions"]),
          ("enforcementGapVid", "string", False, None, "bridges massMessagingPlatform.flagEnforcementGap"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCivilSocietyResistance",
        "desc": "Civil society resistance / signal pushback / e2ee community alert (bridges massMessagingPlatform.flagEnforcementGap + press-freedom + transnational-repression)",
        "fields": [
          ("flagId", "string", True),
          ("moveVid", "string", True, None, "bridges recordPolicyMove"),
          ("resistanceKind", "string", True, ["technical_open_letter","ngo_coalition","provider_threat_exit","apple_signal_exit","whatsapp_threaten","matrix_decentralize","tor_response","privacy_int_letter","unsr_warning","echr_concern","cjeu_pending"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "fossil-stranded-asset",
    "app": "fossilStrandedAsset",
    "methods": [
      {
        "name": "recordImpairment",
        "desc": "Fossil-fuel stranded asset impairment / write-down (bridges energyCharterExit.flagInvestorClaimSurge + climate-value-chain + just-transition)",
        "fields": [
          ("impairmentId", "string", True),
          ("assetClass", "string", True, ["upstream_oil","upstream_gas","downstream_refinery","midstream_pipeline","midstream_lng","coal_thermal","coal_metallurgical","power_unabated","reserves_e_p","copa_uneconomic","tar_sands"]),
          ("operatorLei", "string", False),
          ("triggerKind", "string", True, ["regulatory_phase_out","carbon_price","demand_destruction","financing_unavailable","insurance_withdrawn","pension_divest","sovereign_wealth_divest","renewables_displace","ev_displace","heat_pump_displace","just_transition_close"]),
          ("investorSurgeVid", "string", False, None, "bridges energyCharterExit.flagInvestorClaimSurge"),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagJustTransitionGap",
        "desc": "Just transition gap / community impact / orphan asset (bridges energyCharterExit.flagInvestorClaimSurge + just-transition + worker-grievance)",
        "fields": [
          ("flagId", "string", True),
          ("impairmentVid", "string", True, None, "bridges recordImpairment"),
          ("gapKind", "string", True, ["worker_unsupported","community_revenue","tax_base_collapse","abandonment_liability","orphan_well_clean_up","environmental_legacy","health_impact_residual","social_license_lost","pension_underfunded","plug_abandon_unfunded","supply_chain_void"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "meta-oversight-board",
    "app": "metaOversightBoard",
    "methods": [
      {
        "name": "recordRuling",
        "desc": "Meta Oversight Board ruling / policy advisory (bridges contentModerationAppeal.flagOutcomeAsymmetry + dsa-vlop + dpa-authority)",
        "fields": [
          ("rulingId", "string", True),
          ("caseCategory", "string", True, ["public_figure","misinformation","csam","violence_glorify","hate_speech","terrorism","political_ad","election_manipulation","historical_image","gender","minor_protect","platform_advertising"]),
          ("rulingKind", "string", True, ["overturn","uphold","partial","standard_clarification","policy_advisory","reinstate","remove","metricize_appeal","systemic_recommendation","summary_decision","standard_iss"]),
          ("outcomeAsymmetryVid", "string", False, None, "bridges contentModerationAppeal.flagOutcomeAsymmetry"),
          ("ruledAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagComplianceGap",
        "desc": "Meta non-implementation / partial compliance / scope drift (bridges contentModerationAppeal.flagOutcomeAsymmetry + dsa-vlop + transparency-action)",
        "fields": [
          ("flagId", "string", True),
          ("rulingVid", "string", True, None, "bridges recordRuling"),
          ("gapKind", "string", True, ["non_implementation","partial_implementation","narrowed_scope","insufficient_metric","feedback_loop_broken","mass_review_unactionable","commercial_concern","global_apply_narrow","selectively_enforced","new_policy_not_communicated","sunset_policy_lapsed"]),
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
    out = Path(f"/tmp/wave13/w92_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
