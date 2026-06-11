#!/usr/bin/env python3
"""Wave 65 — amicus-brief / freeport-registry / poc-ihl / whistleblower-protect / eu-dpp.

Bridges Wave 64:
- amicus-brief ↔ scotusDocket.flagDoctrinalShift
- freeport-registry ↔ artMarketAml.flagMoneyLaundering
- poc-ihl ↔ humanitarianCorridor.flagAccessDenial
- whistleblower-protect ↔ genderInclusion.flagHarassment
- eu-dpp ↔ recycledContentVerify.flagFraud
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "amicus-brief",
    "app": "amicusBrief",
    "methods": [
      {
        "name": "recordBriefFiling",
        "desc": "Amicus curiae brief filing (bridges scotusDocket.flagDoctrinalShift + federal-court-docket + civil-liability)",
        "fields": [
          ("briefId", "string", True),
          ("courtLevel", "string", True, ["scotus","ca_circuit","district","state_supreme","appellate_state","intl_tribunal","echr","cjeu","icj","iccpr"]),
          ("caseNumber", "string", True),
          ("amicusKind", "string", True, ["industry_coalition","state_ag","academic","ngo_civil_rights","ngo_environmental","religious","former_officials","bar_association","trade_association","scholars_intl_law"]),
          ("doctrinalShiftVid", "string", False, None, "bridges scotusDocket.flagDoctrinalShift"),
          ("supportsParty", "string", False, ["petitioner","respondent","neither","partial","cross"]),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCitation",
        "desc": "Court citation of amicus / influence flag (bridges scotusDocket.flagDoctrinalShift + academic-integrity + federal-court-docket)",
        "fields": [
          ("citationId", "string", True),
          ("briefVid", "string", True, None, "bridges recordBriefFiling"),
          ("citationKind", "string", True, ["majority_cite","concurrence","dissent","footnote_only","framing_adoption","no_cite","adverse_distinguish","factual_reliance","judicial_notice","pattern_shift"]),
          ("influenceTier", "string", False, ["minor","noted","persuasive","dispositive"]),
          ("ruledAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "freeport-registry",
    "app": "freeportRegistry",
    "methods": [
      {
        "name": "recordFreeportEntry",
        "desc": "Freeport / bonded warehouse / art storage entry (bridges artMarketAml.flagMoneyLaundering + beneficial-ownership + customs-declaration)",
        "fields": [
          ("entryId", "string", True),
          ("freeportKind", "string", True, ["geneva_freeport","lefebvre_lux","le_freeport_singapore","delaware_warehouse","newark_ports","hk_airport","beijing_art","delaware_freeport","basel_bonded","freeport_mia"]),
          ("holderKind", "string", True, ["trust","foundation","shell_hnwi","gallery","estate","fund","sovereign","custodial"]),
          ("objectCategory", "string", True, ["art","jewelry","precious_metals","whisky_vintages","classic_cars","bonds_paper","digital_wallet_cold","rare_books","numismatics"]),
          ("amlFlagVid", "string", False, None, "bridges artMarketAml.flagMoneyLaundering"),
          ("enteredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagOpacityIssue",
        "desc": "Disclosure gap / AML tipping off / indefinite storage (bridges artMarketAml.flagMoneyLaundering + beneficial-ownership + sanctions-entry)",
        "fields": [
          ("flagId", "string", True),
          ("entryVid", "string", True, None, "bridges recordFreeportEntry"),
          ("issueKind", "string", True, ["no_ubo_disclosed","tipping_off_concern","indefinite_storage","export_without_cites","sanctions_party_link","insurance_valuation_variance","custodian_unregulated","sale_inside_freeport","art_secured_lending","off_chain_swap"]),
          ("daysStored", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "poc-ihl",
    "app": "pocIhl",
    "methods": [
      {
        "name": "recordIncident",
        "desc": "Protection of Civilians / IHL incident (bridges humanitarianCorridor.flagAccessDenial + laws-autonomous-weapons + disarmament-treaties)",
        "fields": [
          ("incidentId", "string", True),
          ("countryIso3", "string", True),
          ("incidentKind", "string", True, ["indiscriminate_attack","protected_site_strike","ambulance_hospital","aid_worker_targeting","sexual_violence_war","forced_displacement","siege_starvation","civilian_detain","school_attack","water_infra_strike","communications_blackout"]),
          ("reportingAuthority", "string", True, ["un_cohchr","icrc","save_the_children","msf","hrw","amnesty","un_poc","ijm","airwars","ua_ombudsman"]),
          ("accessDenialVid", "string", False, None, "bridges humanitarianCorridor.flagAccessDenial"),
          ("civilianCasualties", "integer", False),
          ("occurredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAccountabilityGap",
        "desc": "Accountability gap / ICC referral / universal jurisdiction (bridges humanitarianCorridor.flagAccessDenial + federal-court-docket + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("incidentVid", "string", True, None, "bridges recordIncident"),
          ("gapKind", "string", True, ["icc_non_party","security_council_veto","domestic_immunity","universal_jurisdiction_declined","military_justice_cover","amnesty_law","evidence_destroyed","witness_intimidation","command_responsibility_dispute","statute_barred"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "whistleblower-protect",
    "app": "whistleblowerProtect",
    "methods": [
      {
        "name": "recordDisclosure",
        "desc": "Whistleblower protected disclosure (EU Directive 2019/1937 / Dodd-Frank / Sarbanes-Oxley — bridges genderInclusion.flagHarassment + enforcementAction + ilo-labor-rights)",
        "fields": [
          ("disclosureId", "string", True),
          ("jurisdictionIso3", "string", True),
          ("regime", "string", True, ["eu_2019_1937","us_dodd_frank","us_sarbanes_oxley","uk_pida","au_pid","fr_sapin2","de_hinschg","jp_whistleblower_act","ca_wpaa","brazil_lei_da_delacao"]),
          ("disclosureTopic", "string", True, ["fraud","financial_misconduct","bribery_corruption","environmental","occupational_safety","sexual_harassment","sanctions_violation","antitrust","data_privacy","consumer_protection","money_laundering"]),
          ("harassmentVid", "string", False, None, "bridges genderInclusion.flagHarassment"),
          ("disclosedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRetaliation",
        "desc": "Retaliation / reprisal against whistleblower (bridges genderInclusion.flagHarassment + worker-grievance + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("disclosureVid", "string", True, None, "bridges recordDisclosure"),
          ("retaliationKind", "string", True, ["termination","demotion","pay_cut","blacklisting","threats","smear_campaign","counterclaim_suit","criminal_charge","visa_cancellation","nda_weaponized","immigration_pressure","professional_license"]),
          ("remedySought", "string", False, ["reinstatement","double_back_pay","bounty","injunction","protective_order","asylum","passport"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "eu-dpp",
    "app": "euDpp",
    "methods": [
      {
        "name": "recordPassport",
        "desc": "EU Digital Product Passport (ESPR / battery / textile / construction — bridges recycledContentVerify.flagFraud + eudr-deforestation + eu-cbam)",
        "fields": [
          ("passportId", "string", True),
          ("productCategory", "string", True, ["battery_industrial","battery_ev","textile_apparel","construction_product","electronics_consumer","toy","iron_steel","chemicals","footwear","tyres","furniture","ict_electronics"]),
          ("producerLei", "string", False),
          ("dataModel", "string", True, ["ce_rfid","ce_qr","ce_nfc","ce_watermark","ce_multi_carrier"]),
          ("recycledContentVid", "string", False, None, "bridges recycledContentVerify.flagFraud"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDppInconsistency",
        "desc": "DPP inconsistency / tamper / LCA misalignment (bridges recycledContentVerify.flagFraud + eudr-deforestation + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("passportVid", "string", True, None, "bridges recordPassport"),
          ("issueKind", "string", True, ["tamper_carrier","off_chain_edit","lca_misalignment","recycled_content_fraud","cbam_double_count","sku_identity_drift","expired_passport","missing_downstream","greenwash_claim","non_machine_readable","data_wallet_breach"]),
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
            if ftype == "integer" and any(k in col for k in ["size","years","days","count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","affected"]):
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
    out = Path(f"/tmp/wave13/w65_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
