#!/usr/bin/env python3
"""Wave 66 — judicial-influence / bearer-share / universal-jurisdiction / sox-bounty / cbam-embedded.

Bridges Wave 65:
- judicial-influence ↔ amicusBrief.flagCitation
- bearer-share ↔ freeportRegistry.flagOpacityIssue
- universal-jurisdiction ↔ pocIhl.flagAccountabilityGap
- sox-bounty ↔ whistleblowerProtect.flagRetaliation
- cbam-embedded ↔ euDpp.flagDppInconsistency
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "judicial-influence",
    "app": "judicialInfluence",
    "methods": [
      {
        "name": "recordInfluenceNetwork",
        "desc": "Judicial influence network / confirmation bias / donor linkage (bridges amicusBrief.flagCitation + academic-integrity + press-freedom)",
        "fields": [
          ("networkId", "string", True),
          ("judgeJurisdiction", "string", True, ["scotus","us_circuit","state_supreme","uk_supreme","echr","cjeu","icj","itlos","wto","icc","arbitral_panel"]),
          ("linkageKind", "string", True, ["federalist_society","american_constitution_society","donor_club","clerkship_pipeline","law_firm_revolver","think_tank_fellow","shadow_docket_case","textualist_network","am_bar_committee","white_house_pipeline"]),
          ("citationFlagVid", "string", False, None, "bridges amicusBrief.flagCitation"),
          ("observedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagConflictOfInterest",
        "desc": "Undisclosed gift / recusal failure / campaign finance conflict (bridges amicusBrief.flagCitation + enforcementAction + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("networkVid", "string", True, None, "bridges recordInfluenceNetwork"),
          ("conflictKind", "string", True, ["undisclosed_gift","luxury_travel","real_estate","spouse_employment","child_tuition","speaking_fee","book_deal_advance","stock_ownership","campaign_donor_litigant","failure_to_recuse","post_retirement_promise"]),
          ("estValueUsd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "bearer-share",
    "app": "bearerShare",
    "methods": [
      {
        "name": "recordAbolition",
        "desc": "Bearer share / nominee director abolition (FATF R24 / G20 Sherpa — bridges freeportRegistry.flagOpacityIssue + beneficial-ownership + debarmentList)",
        "fields": [
          ("recordId", "string", True),
          ("jurisdictionIso3", "string", True),
          ("instrumentKind", "string", True, ["bearer_share","nominee_shareholder","nominee_director","custodian_bearer","opaque_trust","private_ib","partial_ibc","offshore_found","bvi_ubo_share","panama_nominee"]),
          ("status", "string", True, ["abolished","immobilized","phased_out","registered_only","stayed","grandfathered","active_still"]),
          ("opacityIssueVid", "string", False, None, "bridges freeportRegistry.flagOpacityIssue"),
          ("legislatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagLoophole",
        "desc": "Bearer share loophole / circumvention / FATF mutual eval finding (bridges freeportRegistry.flagOpacityIssue + beneficial-ownership + fatf-travel-rule)",
        "fields": [
          ("flagId", "string", True),
          ("recordVid", "string", True, None, "bridges recordAbolition"),
          ("loopholeKind", "string", True, ["electronic_bearer","cross_border_ibc","nominee_for_nominee","trust_settlor_hidden","foundation_protector","bearer_debt","participating_note","tokenized_opaque","layered_succession","grandfathered"]),
          ("fatfGrade", "string", False, ["compliant","largely_compliant","partially_compliant","non_compliant","not_applicable"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "universal-jurisdiction",
    "app": "universalJurisdiction",
    "methods": [
      {
        "name": "recordUjCase",
        "desc": "Universal jurisdiction prosecution (bridges pocIhl.flagAccountabilityGap + legal-document + federal-court-docket)",
        "fields": [
          ("caseId", "string", True),
          ("prosecutingCountryIso3", "string", True),
          ("defendantNationalityIso3", "string", False),
          ("crimeKind", "string", True, ["genocide","crimes_against_humanity","war_crimes","torture","enforced_disappearance","apartheid","aggression","piracy","hijacking","terror_financing","slave_trade"]),
          ("legalBasis", "string", True, ["absolute_uj","conditional_uj","treaty_based","domestic_transpose","icc_complementarity","aut_dedere","self_referred","flag_state_extension"]),
          ("accountabilityGapVid", "string", False, None, "bridges pocIhl.flagAccountabilityGap"),
          ("chargedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagExecutiveInterference",
        "desc": "Executive interference / immunity plea / extradition blocking (bridges pocIhl.flagAccountabilityGap + federal-court-docket + press-freedom)",
        "fields": [
          ("flagId", "string", True),
          ("caseVid", "string", True, None, "bridges recordUjCase"),
          ("interferenceKind", "string", True, ["political_pressure","statehood_immunity","diplomatic_immunity","sitting_official","extradition_block","refugee_conversion","policy_vicissitude","budget_cut","pardoning","visa_block","amnesty_by_inaction"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "sox-bounty",
    "app": "soxBounty",
    "methods": [
      {
        "name": "recordBountyProgram",
        "desc": "SEC OWB / CFTC WPO / IRS WBO / FinCEN WBP / AMLA / NHTSA bounty (bridges whistleblowerProtect.flagRetaliation + enforcementAction + securities)",
        "fields": [
          ("programId", "string", True),
          ("agency", "string", True, ["sec_owb","cftc_wpo","irs_wbo","fincen_wbp","amla_fincen","ctr_usdoj","nhtsa","ftc","consumer_fin_protect","ois_afl","fcc_wb","faa","fda"]),
          ("qualifyingViolation", "string", True, ["fraud_secur","manipulation_market","insider_trading","fcpa","aml","tax_evasion","automotive_safety","unsecured_consumer","telecom","airline_safety","drug"]),
          ("retaliationVid", "string", False, None, "bridges whistleblowerProtect.flagRetaliation"),
          ("programLaunchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAwardDispute",
        "desc": "Bounty award dispute / gag / clawback (bridges whistleblowerProtect.flagRetaliation + enforcementAction + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("programVid", "string", True, None, "bridges recordBountyProgram"),
          ("disputeKind", "string", True, ["denied_claim","gagged_by_confidentiality","award_reduction","multiple_claimant","pro_rata_split","clawback","ambush_counterclaim","tax_gross_up","nda_violation_pursued","interpleader"]),
          ("awardedMusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cbam-embedded",
    "app": "cbamEmbedded",
    "methods": [
      {
        "name": "recordEmbeddedEmission",
        "desc": "CBAM embedded emission declaration (bridges euDpp.flagDppInconsistency + climate-value-chain + imo-emissions)",
        "fields": [
          ("declarationId", "string", True),
          ("importerLei", "string", False),
          ("sectorKind", "string", True, ["cement","iron_steel","aluminium","fertilizer","electricity","hydrogen","downstream_iron","chemical_precursor","refined_steel","plastics_precursor"]),
          ("originCountryIso3", "string", True),
          ("embeddedTco2e", "number", True),
          ("benchmarkTco2e", "number", False),
          ("dppVid", "string", False, None, "bridges euDpp.flagDppInconsistency"),
          ("declaredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagLeakage",
        "desc": "Carbon leakage / resource shuffling / scope-3 gap (bridges euDpp.flagDppInconsistency + climate-value-chain + eu-cbam)",
        "fields": [
          ("flagId", "string", True),
          ("declarationVid", "string", True, None, "bridges recordEmbeddedEmission"),
          ("leakageKind", "string", True, ["resource_shuffle","renaming_origin","declared_low_grid","power_purchase_certificates","allocation_shuffle","gaming_benchmark","downstream_miss","scope3_unaccounted","transshipment_haven","rebating_country"]),
          ("estLeakedTco2e", "integer", False),
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
    out = Path(f"/tmp/wave13/w66_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
