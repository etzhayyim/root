#!/usr/bin/env python3
"""Wave 75 — source-shield / flood-early / wcag / ccp-oversight / isotope-trace.

Bridges Wave 74:
- source-shield-law ↔ espionageAct.flagChillingEffect
- flood-early-warning ↔ damSafety.flagCriticalRisk
- accessibility-wcag ↔ biometricStandards.flagInclusionGap
- ccp-oversight ↔ nbfiStress.flagResolutionGap
- isotope-traceability ↔ uflpaEnforcement.flagRebuttalFailure
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "source-shield-law",
    "app": "sourceShieldLaw",
    "methods": [
      {
        "name": "recordShield",
        "desc": "Journalist source shield law / reporter's privilege (bridges espionageAct.flagChillingEffect + press-freedom + federal-court-docket)",
        "fields": [
          ("shieldId", "string", True),
          ("jurisdictionIso3", "string", True),
          ("regime", "string", True, ["press_act_us","branzburg","journalist_shield_state","eu_media_freedom","uk_contempt_act","fr_art_2","de_press_law","jp_press_privilege","ca_protection_journalistic_sources","au_shield_act","br_lei_acesso"]),
          ("scope", "string", True, ["criminal_only","civil_only","both","qualified_privilege","absolute","subpoena","warrant","search","surveillance","national_security_carveout"]),
          ("chillingEffectVid", "string", False, None, "bridges espionageAct.flagChillingEffect"),
          ("enactedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCompulsoryProcess",
        "desc": "Subpoena / grand jury / surveillance of journalists (bridges espionageAct.flagChillingEffect + federal-court-docket + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("shieldVid", "string", True, None, "bridges recordShield"),
          ("processKind", "string", True, ["grand_jury_subpoena","nsl","surveillance_order","warrant_newsroom","contempt_citation","cipa_judge_only","trial_subpoena","email_subpoena","cellphone_warrant","international_mlat","privilege_waiver"]),
          ("resolutionOutcome", "string", False, ["quashed","complied","journalist_jailed","settled","agreement","attorney_general_decline"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "flood-early-warning",
    "app": "floodEarlyWarning",
    "methods": [
      {
        "name": "recordAlert",
        "desc": "Flood early warning alert (GDACS / EFAS / GloFAS / JMA / NOAA / JRC — bridges damSafety.flagCriticalRisk + ecmwf-forecast + disaster-response)",
        "fields": [
          ("alertId", "string", True),
          ("regionName", "string", True),
          ("floodKind", "string", True, ["river_riverine","flash","urban","coastal","glacial_outburst","dam_break","mudflow","storm_surge","snowmelt_ice_jam","compound"]),
          ("warningLevel", "string", True, ["advisory","watch","warning","emergency","imminent","ongoing_recession","post_event_review"]),
          ("sourceSystem", "string", True, ["gdacs","efas_europe","glofas","jma_japan","noaa_nws","bmkg_indonesia","imd_india","shkp_shanghai","cwc_india","gfas_asean"]),
          ("damRiskVid", "string", False, None, "bridges damSafety.flagCriticalRisk"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMissedWarning",
        "desc": "False negative / missed evacuation / last-mile failure (bridges damSafety.flagCriticalRisk + refugee-unhcr + disaster-response)",
        "fields": [
          ("flagId", "string", True),
          ("alertVid", "string", True, None, "bridges recordAlert"),
          ("missKind", "string", True, ["false_negative","last_mile","language_gap","telecoms_down","issuing_too_late","wrong_precision","cellbroadcast_failure","literacy_barrier","disabled_warning","nomadic_unreachable","border_language"]),
          ("affectedPersons", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "accessibility-wcag",
    "app": "accessibilityWcag",
    "methods": [
      {
        "name": "recordConformance",
        "desc": "Web / app accessibility conformance (WCAG 2.2 / EN 301 549 / ADA / §508 — bridges biometricStandards.flagInclusionGap + digital-accessibility + crpd-disability)",
        "fields": [
          ("auditId", "string", True),
          ("productCategory", "string", True, ["government_web","banking_app","social_media","streaming","ecommerce","job_portal","education_lms","healthcare_app","transit_app","voting_system","gig_app"]),
          ("conformanceLevel", "string", True, ["a","aa","aaa","partial","non_conformant","tentative","under_review","eaa_compliant","ada_tested","wcag_22_new_criteria"]),
          ("standard", "string", True, ["wcag_22","wcag_21","en_301_549","ada_title_iii","section_508","tgsi_jp","bv_br","jis_x_8341","dac_canada","prodigal_asia"]),
          ("inclusionGapVid", "string", False, None, "bridges biometricStandards.flagInclusionGap"),
          ("auditedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDigitalExclusion",
        "desc": "Digital exclusion / no-keyboard / cognitive load / dark mode (bridges biometricStandards.flagInclusionGap + crpd-disability + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("auditVid", "string", True, None, "bridges recordConformance"),
          ("gapKind", "string", True, ["no_keyboard","cognitive_load","captcha_fails","screen_reader_broken","low_contrast","autoplay_video","small_touch","timeout_short","focus_lost","dark_mode_fails","ttf_tab"]),
          ("criticalFlowFail", "boolean", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ccp-oversight",
    "app": "ccpOversight",
    "methods": [
      {
        "name": "recordExposure",
        "desc": "Central Counterparty (CCP) default fund / initial margin / PFMI (bridges nbfiStress.flagResolutionGap + bank-resolution + enforcement-action)",
        "fields": [
          ("exposureId", "string", True),
          ("ccpLei", "string", False),
          ("productClass", "string", True, ["interest_rate","equity","commodity","fx","crypto","credit_default","securitized","repo","trapizoid_crypto","ft_clearing"]),
          ("metricKind", "string", True, ["initial_margin","default_fund","skin_in_game","recovery_tools","pre_default_waterfall","post_default_waterfall","cover_two_standard","concentration_risk","wrong_way_risk","port_complexity"]),
          ("resolutionGapVid", "string", False, None, "bridges nbfiStress.flagResolutionGap"),
          ("asOfDate", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagProcyclicality",
        "desc": "Margin procyclicality / dash for collateral (bridges nbfiStress.flagResolutionGap + liquidity-facility + stablecoin-reserves)",
        "fields": [
          ("flagId", "string", True),
          ("exposureVid", "string", True, None, "bridges recordExposure"),
          ("issueKind", "string", True, ["margin_spike","stress_based_margin_lag","add_on_surge","concentration_margin","wrong_way_mtm","novation_breakdown","default_fund_fill","sa_cva_spike","pre_fmi_insolvent","collateral_silo","repo_leverage"]),
          ("affectedLcrPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "isotope-traceability",
    "app": "isotopeTraceability",
    "methods": [
      {
        "name": "recordAssay",
        "desc": "Isotope / trace-element provenance assay (bridges uflpaEnforcement.flagRebuttalFailure + seafood-traceability + residue-mrl)",
        "fields": [
          ("assayId", "string", True),
          ("commodity", "string", True, ["polysilicon","cotton","tuna","shrimp","timber","rare_earth","coffee","cocoa","vanilla","tea","cashew","cobalt","lithium","tobacco","fish_oil"]),
          ("technique", "string", True, ["irms","icpms","xrf","pixe","sr_isotope","ftir","aas","gc_ms","dna_forensic","genome_assay","sims","laser_ablation"]),
          ("declaredOriginIso3", "string", True),
          ("measuredMatchPct", "number", False),
          ("uflpaVid", "string", False, None, "bridges uflpaEnforcement.flagRebuttalFailure"),
          ("assayedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagOriginMismatch",
        "desc": "Origin mismatch / adulteration / laundering detection (bridges uflpaEnforcement.flagRebuttalFailure + rules-of-origin + residue-mrl)",
        "fields": [
          ("flagId", "string", True),
          ("assayVid", "string", True, None, "bridges recordAssay"),
          ("mismatchKind", "string", True, ["claimed_vs_measured","dilution","substitution_with_cheap","blending","intentional_adulteration","unintentional_cross","mislabelled","transshipment_identified","sampling_bias","matrix_interference"]),
          ("dilutionPct", "number", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence"]):
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
    out = Path(f"/tmp/wave13/w75_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
