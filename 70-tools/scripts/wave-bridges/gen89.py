#!/usr/bin/env python3
"""Wave 89 — eu-stability-mechanism / judicial-appointment / ai-watermark / mineral-royalty / dsa-vlop.

All-string. Bridges Wave 88.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "eu-stability-mechanism",
    "app": "euStabilityMechanism",
    "methods": [
      {
        "name": "recordIntervention",
        "desc": "ESM / SRM banking resolution / treaty intervention (bridges euSummitConclusion.flagDilution + bank-resolution + sovereign-guarantee)",
        "fields": [
          ("interventionId", "string", True),
          ("instrumentKind", "string", True, ["esm_loan","precautionary_facility","direct_recap","srm_resolution_fund","emergency_liquidity_assistance","bridge_finance","ela_eurosystem","tpi_transmission_protection","backstop","accc_anti_crisis","srm_capital_call"]),
          ("memberStateIso3", "string", True),
          ("dilutionVid", "string", False, None, "bridges euSummitConclusion.flagDilution"),
          ("activatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBoardDispute",
        "desc": "Board of Governors dispute / national veto / conditionality fight (bridges euSummitConclusion.flagDilution + sovereign-debt + imf-article-iv)",
        "fields": [
          ("flagId", "string", True),
          ("interventionVid", "string", True, None, "bridges recordIntervention"),
          ("disputeKind", "string", True, ["national_veto","mou_conditionality","reform_pace","privatisation_demand","politicization_concern","seniority_dispute","loss_absorption","esm_treaty_amendment","cdq_creditor_quasi","creditor_committee_split"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "judicial-appointment",
    "app": "judicialAppointment",
    "methods": [
      {
        "name": "recordNomination",
        "desc": "Judicial appointment / nomination / vetting (bridges judgeRapporteur.flagBiasConcern + ethics-disclosure + scotus-docket)",
        "fields": [
          ("nominationId", "string", True),
          ("courtLevel", "string", True, ["scotus","federal_circuit","federal_district","us_state","cjeu","echr","supreme_uk","constitutional_de","constitutional_fr","apex_in","apex_jp","apex_br","apex_za","arbitrator_pcca"]),
          ("processKind", "string", True, ["executive_appoint","legislative_confirm","judicial_council","peer_election","mixed_ja_chk","constitutional_commission","kj_korea_judicial","gcb_brazil","csm_italy","cnnj_chile","crpc"]),
          ("biasConcernVid", "string", False, None, "bridges judgeRapporteur.flagBiasConcern"),
          ("nominatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPoliticization",
        "desc": "Politicization / packing / minority block (bridges judgeRapporteur.flagBiasConcern + judicialInfluence + transnational-repression)",
        "fields": [
          ("flagId", "string", True),
          ("nominationVid", "string", True, None, "bridges recordNomination"),
          ("concernKind", "string", True, ["court_packing","filibuster_change","blue_slip_skip","fast_track","ideological_screen","retirement_engineering","forced_recusal","precedent_signaling","family_relation","financial_disclosure_skip","prior_advocacy"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ai-watermark",
    "app": "aiWatermark",
    "methods": [
      {
        "name": "recordWatermarkScheme",
        "desc": "AI content watermark / SynthID / steganographic detection (bridges c2paContentCred.flagTampering + ai-governance + zero-day-broker)",
        "fields": [
          ("schemeId", "string", True),
          ("vendorLei", "string", False),
          ("schemeKind", "string", True, ["google_synthid_text","google_synthid_image","openai_meta","ms_microsoft","adobe_cm","stability_intel","invisible_pixel","spread_spectrum","sbm_softmax_bias","cyclical_pattern","weak_strong_robust"]),
          ("modality", "string", True, ["text","image","video","audio","multimodal","3d_scene","speech","music"]),
          ("tamperingVid", "string", False, None, "bridges c2paContentCred.flagTampering"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagEvasion",
        "desc": "Watermark stripping / paraphrase attack / regeneration laundering (bridges c2paContentCred.flagTampering + cyber-vuln-cve + ai-governance)",
        "fields": [
          ("flagId", "string", True),
          ("schemeVid", "string", True, None, "bridges recordWatermarkScheme"),
          ("attackKind", "string", True, ["paraphrase","translation_round_trip","summarization_then_expand","gpt_filter","stenographic_recompress","format_conversion","repeat_extraction","statistical_test_failure","collision_with_natural","robust_compression","adversarial_perturbation"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "mineral-royalty",
    "app": "mineralRoyalty",
    "methods": [
      {
        "name": "recordRegime",
        "desc": "Mineral royalty / production-share / fiscal-regime (bridges resourceBackedLoan.flagPledgeStress + critical-minerals + sovereign-debt)",
        "fields": [
          ("regimeId", "string", True),
          ("hostCountryIso3", "string", True),
          ("regimeKind", "string", True, ["royalty_unit","royalty_advalorem","sliding_scale","windfall_tax","resource_rent_tax","equity_share","production_sharing","tax_concession","carry_interest","gold_special_concentrate","oil_psa","gas_concession","mining_code_2024"]),
          ("mineralCategory", "string", True, ["copper","cobalt","lithium","nickel","gold","tin","tungsten","graphite","rare_earth","iron_ore","coal","oil","gas","diamond","uranium","manganese","bauxite"]),
          ("pledgeStressVid", "string", False, None, "bridges resourceBackedLoan.flagPledgeStress"),
          ("introducedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInvestorClaim",
        "desc": "Investor-state arbitration / windfall tax claim (bridges resourceBackedLoan.flagPledgeStress + sovereign-debt + universal-jurisdiction)",
        "fields": [
          ("flagId", "string", True),
          ("regimeVid", "string", True, None, "bridges recordRegime"),
          ("claimKind", "string", True, ["icsid_arbitration","uncitral","stockholm_chamber","ecourts","local_admin","fair_equitable","expropriation_indirect","stabilization_clause_breach","most_favored_nation","umbrella_clause","national_treatment"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "dsa-vlop",
    "app": "dsaVlop",
    "methods": [
      {
        "name": "recordDesignation",
        "desc": "DSA VLOP / VLOSE designation (bridges socialMediaInfluenceOp.flagPlatformResponse + cross-border-transfer + consumer-protection)",
        "fields": [
          ("designationId", "string", True),
          ("platformLei", "string", False),
          ("platformKind", "string", True, ["vlop_45m","vlose_45m","platform_intermediary","host","cloud_iaas","marketplace","gig","short_video","livestream","encrypted","dating","review","payment_within_platform"]),
          ("scope", "string", True, ["search","social","short_video","marketplace","app_store","cloud","ride_sharing","food_delivery","ecommerce","music","gaming","short_form_streaming","live_commerce"]),
          ("platformResponseVid", "string", False, None, "bridges socialMediaInfluenceOp.flagPlatformResponse"),
          ("designatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSystemicRisk",
        "desc": "Systemic risk / amplification / electoral integrity (bridges socialMediaInfluenceOp.flagPlatformResponse + transnational-repression + press-freedom)",
        "fields": [
          ("flagId", "string", True),
          ("designationVid", "string", True, None, "bridges recordDesignation"),
          ("riskKind", "string", True, ["fundamental_rights","civic_discourse","electoral","gender_violence","minor_protect","mental_health","public_health","human_dignity","disinfo_amplify","crisis_response","crisis_protocol_failure","commission_request","article_36_request"]),
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
    out = Path(f"/tmp/wave13/w89_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
