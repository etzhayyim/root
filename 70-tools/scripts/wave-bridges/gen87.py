#!/usr/bin/env python3
"""Wave 87 — council-presidency / ag-opinion / satellite-evidence / south-south-coop / constituency-pressure.

All-string. Bridges Wave 86.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "council-presidency",
    "app": "councilPresidency",
    "methods": [
      {
        "name": "recordPriority",
        "desc": "EU Council rotating presidency priority / programme (bridges euTrilogue.flagDeadlock + edpb-binding + sps-notification)",
        "fields": [
          ("priorityId", "string", True),
          ("memberStateIso3", "string", True),
          ("semester", "string", True, ["jan_jun","jul_dec"]),
          ("areaKind", "string", True, ["rule_of_law","competitiveness","green_deal","digital","health","migration","enlargement","defense","budget_mff","ukraine","social","trade"]),
          ("trilogueDeadlockVid", "string", False, None, "bridges euTrilogue.flagDeadlock"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPriorityShift",
        "desc": "Mid-presidency priority shift / national interest tilt (bridges euTrilogue.flagDeadlock + judicial-review-gdpr + esma-convergence)",
        "fields": [
          ("flagId", "string", True),
          ("priorityVid", "string", True, None, "bridges recordPriority"),
          ("shiftKind", "string", True, ["national_interest_tilt","emergency_diversion","external_event","ec_pushback","commission_disagreement","ep_resistance","cohesion_concern","budget_battle","summit_outcome"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ag-opinion",
    "app": "agOpinion",
    "methods": [
      {
        "name": "recordOpinion",
        "desc": "CJEU Advocate General opinion (bridges prejudicialReference.flagWithdrawal + grand-chamber-ruling + judicial-review-gdpr)",
        "fields": [
          ("opinionId", "string", True),
          ("agName", "string", True),
          ("caseNumber", "string", True),
          ("reasoningKind", "string", True, ["textual","teleological","systemic","comparative","doctrinal","principles_of_law","fundamental_rights","proportionality","subsidiarity","institutional_balance","direct_effect","retroactivity"]),
          ("withdrawalVid", "string", False, None, "bridges prejudicialReference.flagWithdrawal"),
          ("deliveredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDivergenceFromCourt",
        "desc": "AG diverges from Court / influence pattern (bridges prejudicialReference.flagWithdrawal + grand-chamber-ruling + amicus-brief)",
        "fields": [
          ("flagId", "string", True),
          ("opinionVid", "string", True, None, "bridges recordOpinion"),
          ("divergenceKind", "string", True, ["court_followed","court_diverged","partial_agreement","narrower","broader","more_restrictive","cited_in_concurrence","cited_in_dissent","ignored","textual_overruled","systemic_overruled"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "satellite-evidence",
    "app": "satelliteEvidence",
    "methods": [
      {
        "name": "recordImagery",
        "desc": "Satellite / SAR imagery for human rights documentation (bridges inquiryCommission.flagAccessDenial + ais-dark-vessel + poc-ihl)",
        "fields": [
          ("imageryId", "string", True),
          ("regionName", "string", True),
          ("sensorKind", "string", True, ["sentinel_1_sar","sentinel_2_optical","sentinel_3","planet_skysat","maxar_worldview","airbus_pleiades","capella_sar","iceye_sar","umbra_sar","cloud_optical","viirs_thermal","msl_landsat"]),
          ("evidenceKind", "string", True, ["mass_grave","destruction_residential","camp_construction","forced_displacement","crop_burning","prison_construction","extraction_mining","deforestation","oil_spill","ais_dark_vessel","blockade","factory_emission_signature"]),
          ("accessDenialVid", "string", False, None, "bridges inquiryCommission.flagAccessDenial"),
          ("acquiredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAuthenticationConcern",
        "desc": "Imagery authentication / chain-of-custody / data-poisoning (bridges inquiryCommission.flagAccessDenial + civil-liability + classification-review)",
        "fields": [
          ("flagId", "string", True),
          ("imageryVid", "string", True, None, "bridges recordImagery"),
          ("concernKind", "string", True, ["timestamp_dispute","resolution_inadequate","metadata_tampered","cloud_cover","geolocation_error","comparison_baseline","missing_imagery","sensor_calibration","data_poisoning_synthetic","classification_redaction","commercial_provider_pressure","sovereign_block"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "south-south-coop",
    "app": "southSouthCoop",
    "methods": [
      {
        "name": "recordCommitment",
        "desc": "South-South cooperation / triangular dev / India IBSA / China BRI (bridges oecdDacTransparency.flagReportingGap + brics-bank + world-bank-dpf)",
        "fields": [
          ("commitmentId", "string", True),
          ("providerCountryIso3", "string", True),
          ("partnerCountryIso3", "string", True),
          ("modalityKind", "string", True, ["bri_belt_road","global_dev_initiative","gcp_global_civilization","russia_economic","ibsa_india_brazil_sa","triangular","ali_baba_finance","csia_emerging","afdb_co_finance","aiib_co_finance","ndb_co_finance","global_south_pact"]),
          ("sectorKind", "string", True, ["infrastructure","energy","health","education","ag_food","water","trade","tech_transfer","capacity","peacekeeping","disaster_response"]),
          ("reportingGapVid", "string", False, None, "bridges oecdDacTransparency.flagReportingGap"),
          ("announcedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDebtTrap",
        "desc": "Debt trap / hidden conditionality / collateralization concern (bridges oecdDacTransparency.flagReportingGap + sovereign-debt + debt-rescheduling-contract)",
        "fields": [
          ("flagId", "string", True),
          ("commitmentVid", "string", True, None, "bridges recordCommitment"),
          ("concernKind", "string", True, ["resource_collateral","port_lease_99yr","sovereignty_concession","tied_aid","substandard_construction","local_content_breach","environmental_destruction","labor_imported","corruption","procurement_no_bid","debt_for_loan_swap","sanctions_evasion"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "constituency-pressure",
    "app": "constituencyPressure",
    "methods": [
      {
        "name": "recordCampaign",
        "desc": "Constituency advocacy / town hall / petition campaign (bridges coalitionReform.flagCollapse + lobbying-disclosure + press-freedom)",
        "fields": [
          ("campaignId", "string", True),
          ("districtName", "string", True),
          ("issueArea", "string", True),
          ("tacticKind", "string", True, ["town_hall","petition","door_knock","phone_bank","social_media","direct_mail","op_ed","letter_to_editor","rally","sit_in","vote_pledge","primary_threat","attack_ad"]),
          ("collapseVid", "string", False, None, "bridges coalitionReform.flagCollapse"),
          ("startedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAstroturf",
        "desc": "Astroturf / dark-money / coordinated inauthentic behavior (bridges coalitionReform.flagCollapse + transnational-repression + judicial-influence)",
        "fields": [
          ("flagId", "string", True),
          ("campaignVid", "string", True, None, "bridges recordCampaign"),
          ("indicatorKind", "string", True, ["dark_money","front_org","sock_puppet_accounts","repurposed_template","fake_local","captive_constituent","paid_actor","duplicate_signatures","cross_border_signatories","timing_anomaly","origin_obscured","funding_undisclosed"]),
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
    out = Path(f"/tmp/wave13/w87_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
