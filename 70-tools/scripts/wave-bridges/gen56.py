#!/usr/bin/env python3
"""Wave 56 — ilo-labor-rights / sps-notification / federal-court-docket / world-bank-dpf / fishery-collapse.

Bridges Wave 55:
- ilo-labor-rights ↔ gspEligibility.flagEligibilityRemoval
- sps-notification ↔ importRefusal.flagRecurringOrigin
- federal-court-docket ↔ treasuryRulemaking.flagChallenge
- world-bank-dpf ↔ imfArticleIv.flagProgramRequest
- fishery-collapse ↔ marineHeatwave.flagEcosystemImpact
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "ilo-labor-rights",
    "app": "iloLaborRights",
    "methods": [
      {
        "name": "recordRatification",
        "desc": "ILO fundamental convention ratification / non-compliance finding (bridges gspEligibility.flagEligibilityRemoval + forced-labor + gender-pay-gap)",
        "fields": [
          ("recordId", "string", True),
          ("countryIso3", "string", True),
          ("conventionNo", "string", True, ["c029_forced_labor","c087_freedom_assoc","c098_collective_barg","c100_equal_remun","c105_abolition_forced","c111_discrimination","c138_minimum_age","c155_ohs","c182_child_labor","c190_violence_harass","protocol_29"]),
          ("status", "string", True, ["ratified","denounced","pending","non_ratified","core_gap"]),
          ("eligibilityRemovalVid", "string", False, None, "bridges gspEligibility.flagEligibilityRemoval"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagNonCompliance",
        "desc": "CEACR / Committee on the Application of Standards finding (bridges gspEligibility.flagEligibilityRemoval + forced-labor + indigenous-rights)",
        "fields": [
          ("flagId", "string", True),
          ("recordVid", "string", True, None, "bridges recordRatification"),
          ("findingKind", "string", True, ["special_paragraph","individual_case","direct_request","observation","urgent_appeal","double_footnote","technical_assistance"]),
          ("severityTier", "string", False, ["watch","serious","grave","special_session"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "sps-notification",
    "app": "spsNotification",
    "methods": [
      {
        "name": "recordNotification",
        "desc": "WTO SPS notification (emergency / regular / addendum — bridges importRefusal.flagRecurringOrigin + rasff-food-safety + codex)",
        "fields": [
          ("notificationId", "string", True),
          ("notifyingMemberIso3", "string", True),
          ("notificationKind", "string", True, ["regular","emergency","addendum","corrigendum","revision","supplement"]),
          ("productScope", "string", True, ["animal_health","plant_health","food_safety","human_health","veterinary_drugs","pesticide_mrl","gmo_food","microbial","allergen","feed","all_food"]),
          ("recurringOriginVid", "string", False, None, "bridges importRefusal.flagRecurringOrigin"),
          ("standardReference", "string", False, ["oie","ippc","codex","iso","national","none_international"]),
          ("notifiedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagComment",
        "desc": "SPS Committee concern / specific trade concern (STC — bridges importRefusal.flagRecurringOrigin + wto-dispute + trade-sanitary)",
        "fields": [
          ("commentId", "string", True),
          ("notificationVid", "string", True, None, "bridges recordNotification"),
          ("commentingMemberIso3", "string", True),
          ("concernKind", "string", True, ["lack_of_scientific_basis","unjustified_restriction","insufficient_comment_period","procedural","discriminatory","non_risk_based","disproportionate","non_notification"]),
          ("stcNumber", "string", False),
          ("raisedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "federal-court-docket",
    "app": "federalCourtDocket",
    "methods": [
      {
        "name": "recordDocketEntry",
        "desc": "US federal court docket entry (PACER / CourtListener — bridges treasuryRulemaking.flagChallenge + climate-litigation + apa)",
        "fields": [
          ("docketId", "string", True),
          ("court", "string", True, ["scotus","ca_fed","ca_1","ca_2","ca_3","ca_4","ca_5","ca_6","ca_7","ca_8","ca_9","ca_10","ca_11","ca_dc","dc_dc","ed_tx","ed_va","nd_ca","sd_ny","other_district"]),
          ("caseNumber", "string", True),
          ("caseCategory", "string", True, ["apa_review","antitrust","ip","tax","immigration","environmental","labor","constitutional","criminal","bankruptcy","financial"]),
          ("ruleChallengeVid", "string", False, None, "bridges treasuryRulemaking.flagChallenge"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInjunction",
        "desc": "TRO / preliminary injunction / stay pending appeal (bridges treasuryRulemaking.flagChallenge + climate-litigation + ira-tax-credit)",
        "fields": [
          ("injunctionId", "string", True),
          ("docketVid", "string", True, None, "bridges recordDocketEntry"),
          ("injunctionKind", "string", True, ["tro","preliminary_injunction","permanent_injunction","nationwide_injunction","stay_pending_appeal","vacatur","writ_mandamus","cert_grant","cert_denied"]),
          ("scopeTier", "string", False, ["parties_only","statewide","nationwide","global"]),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "world-bank-dpf",
    "app": "worldBankDpf",
    "methods": [
      {
        "name": "recordOperation",
        "desc": "World Bank Development Policy Financing / prior actions (bridges imfArticleIv.flagProgramRequest + sovereign-debt + just-transition)",
        "fields": [
          ("operationId", "string", True),
          ("borrowerCountryIso3", "string", True),
          ("instrumentKind", "string", True, ["dpf","ipf","pforr","gfu","rsa","cpf","esg_dpf","climate_dpf","crisis_response","surcharge"]),
          ("thematicArea", "string", True, ["fiscal_macro","climate","governance","human_capital","financial_sector","energy","trade","health_pandemic","just_transition","digital","crisis_preparedness"]),
          ("programRequestVid", "string", False, None, "bridges imfArticleIv.flagProgramRequest"),
          ("amountBusd", "number", False),
          ("approvedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPriorActionSlippage",
        "desc": "Prior action slippage / waiver request / reform reversal (bridges imfArticleIv.flagProgramRequest + sovereign-debt)",
        "fields": [
          ("flagId", "string", True),
          ("operationVid", "string", True, None, "bridges recordOperation"),
          ("issueKind", "string", True, ["prior_action_missed","waiver_requested","reform_reversal","conditionality_stretch","disbursement_delay","next_tranche_blocked","program_off_track"]),
          ("affectedTrancheBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "fishery-collapse",
    "app": "fisheryCollapse",
    "methods": [
      {
        "name": "recordStockAssessment",
        "desc": "FAO SOFIA / ICES / RAM Legacy stock assessment (bridges marineHeatwave.flagEcosystemImpact + fisheries-iuu + bbnj-highseas)",
        "fields": [
          ("assessmentId", "string", True),
          ("stockId", "string", True),
          ("species", "string", True),
          ("oceanBasin", "string", True, ["ne_atlantic","sw_atlantic","ne_pacific","nw_pacific","sw_pacific","indian","southern","mediterranean","caribbean","bering"]),
          ("status", "string", True, ["underfished","fully_fished","overfished","collapsed","rebuilding","unknown"]),
          ("bbmsy", "number", False, None, "B/Bmsy"),
          ("ecosystemImpactVid", "string", False, None, "bridges marineHeatwave.flagEcosystemImpact"),
          ("assessedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagQuotaBreach",
        "desc": "TAC / quota breach / RFMO non-compliance (bridges fisheries-iuu + fisheries-subsidies + marineHeatwave)",
        "fields": [
          ("flagId", "string", True),
          ("assessmentVid", "string", True, None, "bridges recordStockAssessment"),
          ("rfmo", "string", True, ["iccat","iotc","wcpfc","iattc","sprfmo","ccamlr","napfc","nasco","nafo","siofa"]),
          ("breachKind", "string", True, ["tac_exceed","unreported_landing","iuu_vessel","misreporting","discard_ban_violation","transshipment","bycatch_excess","observer_coverage_fail"]),
          ("breachVolumeTonnes", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if breachVolumeTonnes != null and breachVolumeTonnes >= 10000 then \"severe\" else if breachVolumeTonnes != null and breachVolumeTonnes >= 1000 then \"significant\" else \"moderate\"", ["moderate","significant","severe"]),
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
            if ftype == "integer" and any(k in col for k in ["count","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued"]):
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
    out = Path(f"/tmp/wave13/w56_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
