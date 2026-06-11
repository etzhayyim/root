#!/usr/bin/env python3
"""Wave 82 — crypto-mixer-sanction / edpb-binding / bilingual-education / mbridge-settlement / audit-committee-oversight.

Bridges Wave 81:
- crypto-mixer-sanction ↔ ransomwarePay.flagSanctionsHit
- edpb-binding ↔ dpaAuthority.flagCrossBorderGap
- bilingual-education ↔ languageEndangerment.flagRevitalization
- mbridge-settlement ↔ offshoreRmb.flagPolicyDivergence
- audit-committee-oversight ↔ sox404Icfr.flagWeaknessRemediation
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "crypto-mixer-sanction",
    "app": "cryptoMixerSanction",
    "methods": [
      {
        "name": "recordSanction",
        "desc": "Crypto mixer / privacy protocol OFAC sanction (bridges ransomwarePay.flagSanctionsHit + ofac-sanctions-sdn + mica-crypto)",
        "fields": [
          ("sanctionId", "string", True),
          ("mixerKind", "string", True, ["tornado_cash_eth","blender_io_btc","chipmixer","sinbad","samurai_whirlpool","wasabi_btc","railgun","aztec","aleo","monero_native","zcash_native","secret_network","fixed_float"]),
          ("sanctionAuthority", "string", True, ["ofac","fincen","ukhmt","eu_restrictive","japan_mof","kr_fsc","in_fiu","sg_mas","au_austrac","ca_fintrac"]),
          ("sanctionsHitVid", "string", False, None, "bridges ransomwarePay.flagSanctionsHit"),
          ("listedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDelistingChallenge",
        "desc": "Delisting challenge / Van Loon v Treasury / Fifth Circuit (bridges ransomwarePay.flagSanctionsHit + federal-court-docket + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("sanctionVid", "string", True, None, "bridges recordSanction"),
          ("challengeKind", "string", True, ["apa_ultra_vires","code_is_speech","first_amendment","due_process","vagueness_void","non_person_sanction","immutable_code","open_source_contrib","ownership_concept","technology_neutral","fifth_circuit_van_loon"]),
          ("rulingOutcome", "string", False, ["delisted","upheld","remanded","cert_grant","cert_denied","partial_relief","preliminary_injunction"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "edpb-binding",
    "app": "edpbBinding",
    "methods": [
      {
        "name": "recordBindingDecision",
        "desc": "EDPB Art 65 binding decision / consistency (bridges dpaAuthority.flagCrossBorderGap + data-adequacy + schrems-challenge)",
        "fields": [
          ("decisionId", "string", True),
          ("lsaLead", "string", True),
          ("coSupervisors", "string", False),
          ("triggerKind", "string", True, ["art_65_1a_draft","art_65_1b_mutual_assistance","art_65_1c_representative","art_66_urgency","consistency_opinion","internal_review","complaint_redirect"]),
          ("subjectRespondent", "string", False),
          ("crossBorderGapVid", "string", False, None, "bridges dpaAuthority.flagCrossBorderGap"),
          ("adoptedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagNationalResistance",
        "desc": "Member state resistance / cjeu referral / sovereignty (bridges dpaAuthority.flagCrossBorderGap + federal-court-docket + schrems-challenge)",
        "fields": [
          ("flagId", "string", True),
          ("decisionVid", "string", True, None, "bridges recordBindingDecision"),
          ("resistanceKind", "string", True, ["cjeu_annulment","sovereign_override","dpa_non_compliance","legislative_pushback","constitutional_challenge","national_security_carveout","right_to_privacy_constitutional","home_authority_stall"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "bilingual-education",
    "app": "bilingualEducation",
    "methods": [
      {
        "name": "recordProgram",
        "desc": "Bilingual / mother-tongue education program (UNESCO / EAL / immersion — bridges languageEndangerment.flagRevitalization + module + accessibility-wcag)",
        "fields": [
          ("programId", "string", True),
          ("countryIso3", "string", True),
          ("regionName", "string", True),
          ("modelKind", "string", True, ["dual_immersion","heritage_language","maintenance_bilingual","transitional_bilingual","esl_sheltered","submersion","content_integrated_clil","total_physical","monolingual_elective","maori_kura_kaupapa","navajo_dinA","gaelic_gaeltacht","ainu_restore"]),
          ("mainLanguage", "string", True),
          ("partnerLanguage", "string", True),
          ("revitalizationVid", "string", False, None, "bridges languageEndangerment.flagRevitalization"),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagOutcomeGap",
        "desc": "Outcome gap / achievement / cultural preservation (bridges languageEndangerment.flagRevitalization + gender-inclusion + accessibility-wcag)",
        "fields": [
          ("flagId", "string", True),
          ("programVid", "string", True, None, "bridges recordProgram"),
          ("gapKind", "string", True, ["subtractive","language_gap_english","heritage_loss","parental_opt_out","teacher_shortage","material_shortage","assessment_bias","standardized_test_skew","code_switching_discouraged","semilingualism","cultural_disconnect"]),
          ("studentsImpacted", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "mbridge-settlement",
    "app": "mbridgeSettlement",
    "methods": [
      {
        "name": "recordTransaction",
        "desc": "Project mBridge / Agora multi-CBDC settlement (bridges offshoreRmb.flagPolicyDivergence + digital-euro-brics + fx-swap-lines)",
        "fields": [
          ("transactionId", "string", True),
          ("participatingCbs", "string", True),
          ("currencyPair", "string", True, ["cny_hkd","cny_aed","cny_thb","hkd_thb","aed_thb","rmb_brl","rmb_sar","rmb_inr","cny_rub","cbdc_agora","cbdc_onyx","cbdc_cedar","jade_singapore"]),
          ("settlementKind", "string", True, ["instant_atomic","two_leg","htlc","intraday_liquidity_savings","netting_pooled","corridor_specific","oil_settle_yuan","trade_finance_bank_to_bank"]),
          ("policyDivergenceVid", "string", False, None, "bridges offshoreRmb.flagPolicyDivergence"),
          ("notionalBusd", "number", False),
          ("settledAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDedollarization",
        "desc": "Dedollarization signal / Western exclusion / SWIFT replacement (bridges offshoreRmb.flagPolicyDivergence + digital-euro-brics + fx-swap-lines)",
        "fields": [
          ("flagId", "string", True),
          ("transactionVid", "string", True, None, "bridges recordTransaction"),
          ("signalKind", "string", True, ["swift_replacement","iran_sanction_workaround","russia_sanction_workaround","oil_settlement_yuan","brics_pay_route","non_dollar_invoice","rouble_invoice","bilateral_swap_scaled","non_western_ccp","dollar_exposure_drop","fx_reserves_diversification"]),
          ("estVolumeBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "audit-committee-oversight",
    "app": "auditCommitteeOversight",
    "methods": [
      {
        "name": "recordCharter",
        "desc": "Audit committee charter / composition / independence (bridges sox404Icfr.flagWeaknessRemediation + audit-firm-oversight + enforcement-action)",
        "fields": [
          ("charterId", "string", True),
          ("companyLei", "string", False),
          ("forum", "string", True, ["sox_section_301","sec_10a_3","nyse_303a","nasdaq_5605","msx_main_market","tse_corporate_governance","fsa_jp","uk_corporate","ase_jp","ifrs_audit","ias_23"]),
          ("independentMembersCount", "integer", False),
          ("financialExpertsCount", "integer", False),
          ("icfrWeaknessVid", "string", False, None, "bridges sox404Icfr.flagWeaknessRemediation"),
          ("amendedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagIndependenceGap",
        "desc": "Independence / expert gap / whistleblower oversight (bridges sox404Icfr.flagWeaknessRemediation + whistleblower-protect + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("charterVid", "string", True, None, "bridges recordCharter"),
          ("concernKind", "string", True, ["non_indep_chair","family_relation","cross_director_network","interlock","undisclosed_comp","material_relationship","expertise_gap","overboarding","non_us_exemption","passively_active","missed_meetings","rushed_pre_vote"]),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","subjects","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence","devices","incidents","countries","detections","dark","embargo","bearers","periods","speakers","programs","consecutive","students","experts"]):
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
    out = Path(f"/tmp/wave13/w82_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
