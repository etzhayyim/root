#!/usr/bin/env python3
"""Wave 85 — esma-convergence / grand-chamber-ruling / srsg-coordination / debt-rescheduling-contract / stock-act-amendment.

All-string schemas (no optional number fields) to stay green on smoke.

Bridges Wave 84:
- esma-convergence ↔ micaLicense.flagPassportAbuse
- grand-chamber-ruling ↔ judicialReviewGdpr.flagRulingImpact
- srsg-coordination ↔ genocideConvention.flagProvisionalMeasure
- debt-rescheduling-contract ↔ parisClub.flagNonParisHoldout
- stock-act-amendment ↔ congressionalStock.flagLateFiling
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "esma-convergence",
    "app": "esmaConvergence",
    "methods": [
      {
        "name": "recordReview",
        "desc": "ESMA peer review / thematic review / common supervisory action (bridges micaLicense.flagPassportAbuse + dpa-authority + mica-crypto)",
        "fields": [
          ("reviewId", "string", True),
          ("workKind", "string", True, ["peer_review","csa_common","mystery_shopping","thematic","q_a","guidelines_update","opinion","breach_of_law","cpa_cross_panel","strategic_plan","mandate_review"]),
          ("topic", "string", True, ["mica_casp","mifid_ii_review","emir_3","sfdr","ucits","aifmd","psr_psd3","prospectus","csrd","benchmarks_bmr","amld","transparency"]),
          ("passportAbuseVid", "string", False, None, "bridges micaLicense.flagPassportAbuse"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDivergence",
        "desc": "Member-state divergence / gold-plating / race-to-bottom (bridges micaLicense.flagPassportAbuse + dpa-authority + cross-border-transfer)",
        "fields": [
          ("flagId", "string", True),
          ("reviewVid", "string", True, None, "bridges recordReview"),
          ("divergenceKind", "string", True, ["gold_plating","race_to_bottom","carve_out_exploit","regulator_shopping","approval_speed_wars","enforcement_intensity","fee_reduction","sandbox_gap","lex_fori","private_enforcement_gap"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "grand-chamber-ruling",
    "app": "grandChamberRuling",
    "methods": [
      {
        "name": "recordRuling",
        "desc": "CJEU Grand Chamber / ECHR Grand Chamber ruling (bridges judicialReviewGdpr.flagRulingImpact + schrems-challenge + minority-rights)",
        "fields": [
          ("rulingId", "string", True),
          ("forum", "string", True, ["cjeu_gc","cjeu_full_court","echr_gc","echr_fc","sfc_ic","supreme_court_fr_assembly","uk_supreme","brazil_stf_plenario","japan_grand_bench"]),
          ("caseKind", "string", True, ["preliminary_ref","annulment","treaty_infringement","human_rights","fundamental_rights","rule_of_law","state_aid","competition","freedom_movement","asylum","data_protection"]),
          ("rulingImpactVid", "string", False, None, "bridges judicialReviewGdpr.flagRulingImpact"),
          ("deliveredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDoctrinalShift",
        "desc": "Doctrinal shift / overruling / marketing (bridges judicialReviewGdpr.flagRulingImpact + scotus-docket + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("rulingVid", "string", True, None, "bridges recordRuling"),
          ("shiftKind", "string", True, ["overruled_precedent","narrowed","expanded","procedural_clarification","substantive_rule","constitutional_redefine","compatibility_declare","margin_of_appreciation","proportionality_test","horizontal_direct_effect","vertical_direct_effect"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "srsg-coordination",
    "app": "srsgCoordination",
    "methods": [
      {
        "name": "recordFramework",
        "desc": "UN Special Adviser on Genocide Prevention / R2P framework (bridges genocideConvention.flagProvisionalMeasure + poc-ihl + minority-rights)",
        "fields": [
          ("frameworkId", "string", True),
          ("country", "string", True),
          ("frameworkKind", "string", True, ["office_spa_prevention","oip_r2p","framework_analysis","risk_assessment","urgent_appeal","early_warning","joint_statement","mission_country","advocacy","field_mission","commission_of_inquiry"]),
          ("provisionalMeasureVid", "string", False, None, "bridges genocideConvention.flagProvisionalMeasure"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPillarGap",
        "desc": "R2P pillar gap / SC stalemate / intervention threshold (bridges genocideConvention.flagProvisionalMeasure + humanitarian-corridor + poc-ihl)",
        "fields": [
          ("flagId", "string", True),
          ("frameworkVid", "string", True, None, "bridges recordFramework"),
          ("gapKind", "string", True, ["pillar_1_state_resp","pillar_2_assistance","pillar_3_response","sc_p5_veto","general_assembly_uniting_for_peace","regional_org_reach","sanctions_tailored","sanctions_comprehensive","peacekeeping_mandate","early_action_absent","atrocity_prevention_index"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "debt-rescheduling-contract",
    "app": "debtReschedulingContract",
    "methods": [
      {
        "name": "recordContract",
        "desc": "Bilateral sovereign debt rescheduling contract (bridges parisClub.flagNonParisHoldout + sovereign-debt + debt-transparency)",
        "fields": [
          ("contractId", "string", True),
          ("debtorCountryIso3", "string", True),
          ("creditorCountryIso3", "string", True),
          ("contractKind", "string", True, ["bilateral_treaty","commercial_agreement","cacs_holdout","pari_passu","resource_backed","collateralized","currency_swap_debt","sdr_allocation","memo_of_understanding","facility_letter","amendment"]),
          ("holdoutVid", "string", False, None, "bridges parisClub.flagNonParisHoldout"),
          ("executedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSecrecyClause",
        "desc": "Secrecy / comparability / escrow clause concern (bridges parisClub.flagNonParisHoldout + debt-transparency + sovereign-debt)",
        "fields": [
          ("flagId", "string", True),
          ("contractVid", "string", True, None, "bridges recordContract"),
          ("clauseKind", "string", True, ["confidentiality_clause","pari_passu_negation","revenue_assignment","escrow_arrangement","cross_default_escape","most_favored_creditor","lock_up_pre_default","seniority_mutation","collateral_lock","sovereign_immunity_waiver"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "stock-act-amendment",
    "app": "stockActAmendment",
    "methods": [
      {
        "name": "recordProposal",
        "desc": "STOCK Act amendment / ethics reform proposal (bridges congressionalStock.flagLateFiling + ethicsDisclosure + judicialInfluence)",
        "fields": [
          ("proposalId", "string", True),
          ("chamber", "string", True, ["us_senate","us_house","joint_chamber","eu_parliament","uk_commons","uk_lords","bundestag","national_assembly_fr","diet_japan","knesset","canada_parliament"]),
          ("reformKind", "string", True, ["pelosi_act","etico_act","tradeable_ban","pre_disclosure_ban","trust_only","divestment_mandate","spouse_inclusion","cabinet_extension","judicial_extension","fed_inclusion","crypto_inclusion","blind_trust"]),
          ("lateFilingVid", "string", False, None, "bridges congressionalStock.flagLateFiling"),
          ("introducedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagStallPattern",
        "desc": "Stall pattern / committee hold / vote dodging (bridges congressionalStock.flagLateFiling + judicialInfluence + ethicsDisclosure)",
        "fields": [
          ("flagId", "string", True),
          ("proposalVid", "string", True, None, "bridges recordProposal"),
          ("stallKind", "string", True, ["committee_hold","leadership_block","markup_delay","rider_weakening","filibuster","denied_floor","discharge_petition_failed","compromise_dilution","grandfather_wide","enforcement_gutted","exempt_spouse"]),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","subjects","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence"]):
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
    out = Path(f"/tmp/wave13/w85_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
