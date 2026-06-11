#!/usr/bin/env python3
"""Wave 86 — eu-trilogue / prejudicial-reference / inquiry-commission / oecd-dac-transparency / coalition-reform.

All-string schemas. Bridges Wave 85.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "eu-trilogue",
    "app": "euTrilogue",
    "methods": [
      {
        "name": "recordSession",
        "desc": "EU trilogue / ordinary legislative procedure session (bridges esmaConvergence.flagDivergence + eu-dpp + cbam-embedded)",
        "fields": [
          ("sessionId", "string", True),
          ("dossier", "string", True),
          ("stage", "string", True, ["first_reading","second_reading","conciliation","informal","political_agreement","technical_meeting","codecision","cooling_off","council_common_position","parliament_reading","final_act","corrigendum"]),
          ("institutionalConfig", "string", True, ["ep_council_com","ep_council","com_council","trilateral","bilateral_ep_council","inter_institutional"]),
          ("divergenceVid", "string", False, None, "bridges esmaConvergence.flagDivergence"),
          ("convenedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDeadlock",
        "desc": "Trilogue deadlock / political compromise / opt-out (bridges esmaConvergence.flagDivergence + judicial-review-gdpr + schrems-challenge)",
        "fields": [
          ("flagId", "string", True),
          ("sessionVid", "string", True, None, "bridges recordSession"),
          ("deadlockKind", "string", True, ["presidency_impasse","blocking_minority","qualified_majority_fail","ep_rapporteur_divergence","inter_group_block","national_reservation","parliament_referendum","council_veto","member_state_opt_out","ireland_poland_etc_opt","review_clause","sunset_debate"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "prejudicial-reference",
    "app": "prejudicialReference",
    "methods": [
      {
        "name": "recordReference",
        "desc": "Preliminary reference to CJEU (Art 267 TFEU) (bridges grandChamberRuling.flagDoctrinalShift + judicial-review-gdpr + schrems-challenge)",
        "fields": [
          ("referenceId", "string", True),
          ("referringCourtCountry", "string", True),
          ("courtLevel", "string", True, ["court_of_last_instance","intermediate","first_instance","constitutional","competition","administrative","labor","tax","tribunale","audiencia"]),
          ("questionKind", "string", True, ["interpretation","validity","procedural","interplay_instruments","prior_ruling_scope","temporal_effect","application_methodology","direct_effect","consistency","reasonableness","charter_compatibility"]),
          ("doctrinalShiftVid", "string", False, None, "bridges grandChamberRuling.flagDoctrinalShift"),
          ("submittedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagWithdrawal",
        "desc": "Withdrawal / inadmissibility / acte clair challenge (bridges grandChamberRuling.flagDoctrinalShift + judicial-review-gdpr + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("referenceVid", "string", True, None, "bridges recordReference"),
          ("issueKind", "string", True, ["national_court_withdrew","inadmissible","hypothetical","no_bearing","acte_clair","acte_eclaire","fraudulent","collusive","procedural_defect","broadening_accepted","nuance_reformulated"]),
          ("ruledAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "inquiry-commission",
    "app": "inquiryCommission",
    "methods": [
      {
        "name": "recordMandate",
        "desc": "UN / OHCHR / regional inquiry commission mandate (bridges srsgCoordination.flagPillarGap + poc-ihl + universal-jurisdiction)",
        "fields": [
          ("commissionId", "string", True),
          ("mandatingBody", "string", True, ["hrc_resolution","ga_resolution","sc_resolution","sg_discretion","regional_body","ohchr_field","treaty_body","joint_investigative","ad_hoc"]),
          ("country", "string", True),
          ("mandateKind", "string", True, ["fact_finding","investigative","commission_of_inquiry","panel_of_experts","monitoring_mechanism","documentation_mechanism","impartial_independent","special_advisor","accountability"]),
          ("pillarGapVid", "string", False, None, "bridges srsgCoordination.flagPillarGap"),
          ("establishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAccessDenial",
        "desc": "Access denial / cooperation refusal / report suppression (bridges srsgCoordination.flagPillarGap + humanitarian-corridor + transnational-repression)",
        "fields": [
          ("flagId", "string", True),
          ("commissionVid", "string", True, None, "bridges recordMandate"),
          ("issueKind", "string", True, ["visa_denied","territory_access_refused","witness_intimidation","document_unfit","funding_stripped","mandate_truncated","report_suppressed","staff_threatened","remote_only","state_obstruction","follow_up_denied"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "oecd-dac-transparency",
    "app": "oecdDacTransparency",
    "methods": [
      {
        "name": "recordReport",
        "desc": "OECD DAC / IATI / aid-flow transparency report (bridges debtReschedulingContract.flagSecrecyClause + debt-transparency + sovereign-debt)",
        "fields": [
          ("reportId", "string", True),
          ("donorCountryIso3", "string", True),
          ("recipientCountryIso3", "string", False),
          ("reportKind", "string", True, ["dac_annual","crs_report","iati_publisher","publish_what_you_fund","tosss","total_officials_sustainable","non_core_multilateral","new_dac_member","emerging_donor","brics_aid","south_south"]),
          ("secrecyClauseVid", "string", False, None, "bridges debtReschedulingContract.flagSecrecyClause"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagReportingGap",
        "desc": "Reporting gap / misclassification / vertical fund (bridges debtReschedulingContract.flagSecrecyClause + debt-transparency + just-transition)",
        "fields": [
          ("flagId", "string", True),
          ("reportVid", "string", True, None, "bridges recordReport"),
          ("gapKind", "string", True, ["in_donor_expenditure","refugee_costs_domestic","emerging_donor_gap","ppp_misclass","climate_branding_only","double_counting","vertical_fund","non_oda","tied_aid","guarantee_misuse","concessional_claim_weak"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "coalition-reform",
    "app": "coalitionReform",
    "methods": [
      {
        "name": "recordCoalition",
        "desc": "Bipartisan ethics / governance reform coalition (bridges stockActAmendment.flagStallPattern + judicialInfluence + ethicsDisclosure)",
        "fields": [
          ("coalitionId", "string", True),
          ("jurisdiction", "string", True, ["us_congress","eu_parliament","uk_parliament","canada_parliament","australian_parliament","japan_diet","brazil_congress","india_parliament","state_legislature"]),
          ("coalitionKind", "string", True, ["bipartisan","cross_party","issue_specific","back_bench","constituent_driven","advocacy_led","media_exposure","caucus_task_force","commission_royal","cso_led"]),
          ("subject", "string", True, ["stock_act","election_law","campaign_finance","lobbying","judicial_ethics","post_emp_cooling","whistleblower_protect","pension_rules","redistricting","ai_disclosure_ban","crypto_officials"]),
          ("stallVid", "string", False, None, "bridges stockActAmendment.flagStallPattern"),
          ("formedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCollapse",
        "desc": "Coalition collapse / whip-tarnishing / tokenism (bridges stockActAmendment.flagStallPattern + press-freedom + judicialInfluence)",
        "fields": [
          ("flagId", "string", True),
          ("coalitionVid", "string", True, None, "bridges recordCoalition"),
          ("collapseKind", "string", True, ["leadership_quit","whip_opposed","member_defect","scandal_undermine","election_displace","redistricting_kill","bill_watered","sunset_compromise","superficial_reform","non_self_executing","report_not_bill"]),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","hours","persons","members","workers","cases","pages"]):
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
    out = Path(f"/tmp/wave13/w86_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
