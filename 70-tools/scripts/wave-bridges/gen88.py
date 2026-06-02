#!/usr/bin/env python3
"""Wave 88 — eu-summit-conclusion / judge-rapporteur / c2pa-content-cred / resource-backed-loan / social-media-influence-op.

All-string. Bridges Wave 87.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "eu-summit-conclusion",
    "app": "euSummitConclusion",
    "methods": [
      {
        "name": "recordConclusion",
        "desc": "European Council summit conclusions / position (bridges councilPresidency.flagPriorityShift + eu-trilogue + cbam-embedded)",
        "fields": [
          ("conclusionId", "string", True),
          ("summitKind", "string", True, ["regular","extraordinary","informal","euro_summit","tripartite_social","strategic_agenda","mff_negotiation","jumbo_council"]),
          ("topic", "string", True, ["enlargement","ukraine","mff","strategic_autonomy","competitiveness","security_defense","middle_east","trade","green_deal","energy","health","social"]),
          ("priorityShiftVid", "string", False, None, "bridges councilPresidency.flagPriorityShift"),
          ("adoptedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDilution",
        "desc": "Conclusion text dilution / footnote / member-state opt-out (bridges councilPresidency.flagPriorityShift + eu-trilogue + judicial-review-gdpr)",
        "fields": [
          ("flagId", "string", True),
          ("conclusionVid", "string", True, None, "bridges recordConclusion"),
          ("dilutionKind", "string", True, ["last_minute_redraft","footnote","square_brackets_remain","language_softened","commitments_dropped","review_clause","funding_postponed","compromise_text","veto_threat","national_reservation","absentee_member"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "judge-rapporteur",
    "app": "judgeRapporteur",
    "methods": [
      {
        "name": "recordAssignment",
        "desc": "CJEU / national supreme court judge-rapporteur assignment (bridges agOpinion.flagDivergenceFromCourt + grand-chamber-ruling + amicus-brief)",
        "fields": [
          ("assignmentId", "string", True),
          ("courtName", "string", True),
          ("rapporteurName", "string", True),
          ("caseClass", "string", True, ["c_t","c_p","c_advocate_general","action_for_annulment","appeal","preliminary_ref","direct_action","staff_dispute","cross_appeal"]),
          ("specialization", "string", True, ["competition","ip","tax","public_procurement","data_prot","environment","social_security","competition_law","trade_remedy","external_relations"]),
          ("agDivergenceVid", "string", False, None, "bridges agOpinion.flagDivergenceFromCourt"),
          ("assignedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBiasConcern",
        "desc": "Rapporteur recusal / bias / nationality concern (bridges agOpinion.flagDivergenceFromCourt + judicial-influence + ethics-disclosure)",
        "fields": [
          ("flagId", "string", True),
          ("assignmentVid", "string", True, None, "bridges recordAssignment"),
          ("concernKind", "string", True, ["nationality_bias","prior_employment","family_relation","public_statement","political_affiliation","conflict_of_interest","specialization_mismatch","over_assignment","backlog_distortion","language_skew"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "c2pa-content-cred",
    "app": "c2paContentCred",
    "methods": [
      {
        "name": "recordManifest",
        "desc": "C2PA Content Credentials manifest (bridges satelliteEvidence.flagAuthenticationConcern + cyber-vuln-cve + ai-governance)",
        "fields": [
          ("manifestId", "string", True),
          ("assetKind", "string", True, ["news_image","journalism_video","forensic_imagery","generative_image","generative_video","scientific","political_ad","commercial_ad","stock","ux_screenshot","corporate"]),
          ("publisherLei", "string", False),
          ("manifestKind", "string", True, ["origin_action","ai_action","placement_action","produced_action","redacted_action","metadata_only","training_data_attestation","provenance_chain","derivation"]),
          ("authConcernVid", "string", False, None, "bridges satelliteEvidence.flagAuthenticationConcern"),
          ("signedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagTampering",
        "desc": "Manifest tampering / chain break / spoofed signer (bridges satelliteEvidence.flagAuthenticationConcern + classification-review + zero-day-broker)",
        "fields": [
          ("flagId", "string", True),
          ("manifestVid", "string", True, None, "bridges recordManifest"),
          ("tamperKind", "string", True, ["chain_break","signature_invalid","trust_anchor_revoked","timestamp_anomaly","derivation_missing","ai_use_undisclosed","origin_swapped","training_data_uncited","redaction_overzealous","public_key_compromise","platform_strip"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "resource-backed-loan",
    "app": "resourceBackedLoan",
    "methods": [
      {
        "name": "recordLoan",
        "desc": "Resource / commodity-collateralized sovereign loan (bridges southSouthCoop.flagDebtTrap + sovereign-debt + debt-rescheduling-contract)",
        "fields": [
          ("loanId", "string", True),
          ("debtorCountryIso3", "string", True),
          ("creditorEntityKind", "string", True, ["china_dev_bank","china_exim","gcc_sovereign_fund","commodity_trader","mining_company","specific_lender","russia_finance","trafigura","glencore","vitol","oil_major","dev_bank_local"]),
          ("collateralKind", "string", True, ["oil","copper","cobalt","iron_ore","nickel","gold","gas","port_revenue","airport_revenue","mining_royalty","diamonds","uranium","timber","food_rights"]),
          ("debtTrapVid", "string", False, None, "bridges southSouthCoop.flagDebtTrap"),
          ("originatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPledgeStress",
        "desc": "Pledge / royalty stream stress / sovereignty leak (bridges southSouthCoop.flagDebtTrap + sovereign-debt + debt-rescheduling-contract)",
        "fields": [
          ("flagId", "string", True),
          ("loanVid", "string", True, None, "bridges recordLoan"),
          ("stressKind", "string", True, ["price_collapse","production_disruption","force_majeure","asset_seizure","arbitration","escrow_drained","cross_default","seniority_dispute","local_court_block","sanctions","political_takeover","creditor_takeover_op"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "social-media-influence-op",
    "app": "socialMediaInfluenceOp",
    "methods": [
      {
        "name": "recordOperation",
        "desc": "Social media influence operation / CIB takedown (bridges constituencyPressure.flagAstroturf + transnational-repression + press-freedom)",
        "fields": [
          ("operationId", "string", True),
          ("attribution", "string", True, ["state_actor","commercial_pr","spamouflage","doppelganger","secondary_infektion","internet_research_agency","front_org","politically_motivated","crime_for_hire","extremist_movement","unknown"]),
          ("targetCountryIso3", "string", True),
          ("methodKind", "string", True, ["bot_amplification","fake_accounts","ai_generated_personas","deepfake_video","cloned_news","cross_platform","payment_to_influencers","ad_targeting","narrative_seeding","brigading","coordinated_review_fraud","mass_reporting"]),
          ("astroturfVid", "string", False, None, "bridges constituencyPressure.flagAstroturf"),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPlatformResponse",
        "desc": "Platform takedown / regulatory pressure / unmasking (bridges constituencyPressure.flagAstroturf + dataLocalization + transnational-repression)",
        "fields": [
          ("flagId", "string", True),
          ("operationVid", "string", True, None, "bridges recordOperation"),
          ("responseKind", "string", True, ["mass_takedown","reach_throttle","label_state_media","disclosure_published","attribution_named","dsa_fine","dsa_audit","political_ad_cap","fact_check_added","platform_ban","appeal_pending","reinstated"]),
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
    out = Path(f"/tmp/wave13/w88_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
