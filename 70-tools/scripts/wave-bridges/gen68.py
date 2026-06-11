#!/usr/bin/env python3
"""Wave 68 — lobbying-disclosure / sovereign-rating / interpol-redabuse / receiver-bankruptcy / trade-remedy.

Bridges Wave 67:
- lobbying-disclosure ↔ ethicsDisclosure.flagDisclosureGap
- sovereign-rating ↔ fatfGreylist.flagReputationSpillover
- interpol-redabuse ↔ extraditionTreaty.flagDenial
- receiver-bankruptcy ↔ securitiesInvestor.flagLowRecovery
- trade-remedy ↔ wtoTradeCbam.flagDisputeEscalation
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "lobbying-disclosure",
    "app": "lobbyingDisclosure",
    "methods": [
      {
        "name": "recordFiling",
        "desc": "Lobbying disclosure (LDA LD-1/LD-2 / EU Transparency / UK ORCL / FARA — bridges ethicsDisclosure.flagDisclosureGap + judicial-influence + press-freedom)",
        "fields": [
          ("filingId", "string", True),
          ("registrantLei", "string", False),
          ("regime", "string", True, ["us_lda","us_fara","eu_transparency_reg","uk_orcl","ca_lobbying_act","fr_hatvp","de_lobbyregister","au_federal_register","jp_lobby_code","in_rti_lobby"]),
          ("issueArea", "string", True, ["tax","budget","healthcare","defense","energy_climate","trade","immigration","judicial","antitrust","labor","education","securities","ai_tech","crypto","agriculture","pharma","telecom"]),
          ("disclosureGapVid", "string", False, None, "bridges ethicsDisclosure.flagDisclosureGap"),
          ("amountUsd", "number", False),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFaraUnderreport",
        "desc": "FARA / foreign agent / shadow lobby gap (bridges ethicsDisclosure.flagDisclosureGap + enforcement-action + judicial-influence)",
        "fields": [
          ("flagId", "string", True),
          ("filingVid", "string", True, None, "bridges recordFiling"),
          ("gapKind", "string", True, ["fara_non_registration","lda_vs_fara","pr_shadow_work","think_tank_pipeline","shell_consultancy","dual_hat","below_threshold_gaming","covert_op","foreign_principal_hidden","domestic_subsidiary"]),
          ("estimatedValueUsd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "sovereign-rating",
    "app": "sovereignRating",
    "methods": [
      {
        "name": "recordRatingAction",
        "desc": "S&P / Moody's / Fitch / Scope / DBRS sovereign rating action (bridges fatfGreylist.flagReputationSpillover + sovereign-debt + imf-article-iv)",
        "fields": [
          ("actionId", "string", True),
          ("cra", "string", True, ["sp","moody","fitch","scope","dbrs","cci","rating_ru","dagong","arc","jcr","pra_china"]),
          ("countryIso3", "string", True),
          ("ratingScale", "string", True, ["aaa","aa_plus","aa","aa_minus","a_plus","a","a_minus","bbb_plus","bbb","bbb_minus","bb_plus","bb","bb_minus","b_plus","b","b_minus","ccc_plus","ccc","ccc_minus","cc","c","sd_d"]),
          ("outlook", "string", True, ["positive","stable","negative","developing","watch_positive","watch_negative","watch_developing"]),
          ("greylistVid", "string", False, None, "bridges fatfGreylist.flagReputationSpillover"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMethodologyConcern",
        "desc": "Rating methodology / conflict-of-interest / split-rating concern (bridges fatfGreylist.flagReputationSpillover + judicial-influence + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordRatingAction"),
          ("concernKind", "string", True, ["split_rating","methodology_opacity","conflict_issuer_pays","cra_oligopoly","esg_methodology","geopolitical_bias","non_transparent_stress","inconsistent_migration","procyclicality","rating_shopping","shadow_rating"]),
          ("notchDivergence", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "interpol-redabuse",
    "app": "interpolRedabuse",
    "methods": [
      {
        "name": "recordRedNotice",
        "desc": "INTERPOL Red Notice / Diffusion issuance (bridges extraditionTreaty.flagDenial + press-freedom + refugee-unhcr)",
        "fields": [
          ("noticeId", "string", True),
          ("issuingCountryIso3", "string", True),
          ("subjectNationalityIso3", "string", False),
          ("noticeKind", "string", True, ["red_notice","diffusion","blue","green","yellow","orange","purple","infra_red"]),
          ("basisOffence", "string", True, ["economic_fraud","terrorism","drug","corruption","cyber","sanctions","political","religious","human_rights_defender","journalist_critic","dissident","dual_national"]),
          ("denialVid", "string", False, None, "bridges extraditionTreaty.flagDenial"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAbusivePattern",
        "desc": "Abusive Red Notice / Article 3 challenge / CCF request (bridges extraditionTreaty.flagDenial + refugee-unhcr + press-freedom)",
        "fields": [
          ("flagId", "string", True),
          ("noticeVid", "string", True, None, "bridges recordRedNotice"),
          ("abuseKind", "string", True, ["article_3_politic","pattern_targeting_diaspora","in_absentia_trial","refugee_status_ignored","article_2_universal_decl","hamilton_kenya_ruling","ccf_deletion","repeated_targeting","intimidation_family","visa_weaponized","diffusion_parallel"]),
          ("ccfFiled", "boolean", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "receiver-bankruptcy",
    "app": "receiverBankruptcy",
    "methods": [
      {
        "name": "recordProceeding",
        "desc": "Bankruptcy / insolvency / liquidation / administration proceeding (bridges securitiesInvestor.flagLowRecovery + enforcement-action + class-settlement)",
        "fields": [
          ("proceedingId", "string", True),
          ("debtorLei", "string", False),
          ("forum", "string", True, ["us_ch7","us_ch11","us_ch15","uk_admin","uk_liquidation","uk_cva","ca_ccaa","ca_bia","de_insolvenz","de_scheme","fr_sauvegarde","jp_corporate_reorganization","jp_civil_rehab","sg_scheme","in_ibc","kr_insolvency","sapin_2"]),
          ("totalLiabilitiesBusd", "number", False),
          ("lowRecoveryVid", "string", False, None, "bridges securitiesInvestor.flagLowRecovery"),
          ("petitionedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCramDown",
        "desc": "Cramdown / equity conversion / avoidance / preference (bridges securitiesInvestor.flagLowRecovery + enforcement-action + sovereign-debt)",
        "fields": [
          ("flagId", "string", True),
          ("proceedingVid", "string", True, None, "bridges recordProceeding"),
          ("issueKind", "string", True, ["cramdown_dissent","unfair_discrimination","preference_payment","fraudulent_transfer","veil_pierce","non_consensual_plan","gifting_doctrine","absolute_priority","new_value","non_debtor_release","third_party_release"]),
          ("affectedClaimBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "trade-remedy",
    "app": "tradeRemedy",
    "methods": [
      {
        "name": "recordInvestigation",
        "desc": "Antidumping (AD) / countervailing duty (CVD) / safeguard investigation (bridges wtoTradeCbam.flagDisputeEscalation + commodity-trade + ustr-section-301)",
        "fields": [
          ("investigationId", "string", True),
          ("initiatingCountryIso3", "string", True),
          ("subjectCountryIso3", "string", True),
          ("remedyKind", "string", True, ["ad","cvd","safeguard","circumvention","sunset_review","scope_ruling","evasion","article_xix","special_china_sg","public_interest"]),
          ("productCategory", "string", True, ["steel","aluminium","solar_module","ev","chemicals","textile","lumber","agriculture","semiconductor","wind_turbine","lithium_battery","cap_factoring","pharma_api","glass","seafood"]),
          ("disputeVid", "string", False, None, "bridges wtoTradeCbam.flagDisputeEscalation"),
          ("initiatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagTariffOutcome",
        "desc": "Final tariff / injury determination / retroactive / revocation (bridges wtoTradeCbam.flagDisputeEscalation + ustr-section-301 + customs-declaration)",
        "fields": [
          ("flagId", "string", True),
          ("investigationVid", "string", True, None, "bridges recordInvestigation"),
          ("outcomeKind", "string", True, ["final_ad_duty","final_cvd_duty","preliminary_injury","no_injury","revocation","critical_circumstances","negative_suspension","sunset_extended","scope_narrowed","scope_broadened","individual_rate"]),
          ("dutyPctWeighted", "number", False),
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
            if ftype == "integer" and any(k in col for k in ["size","years","days","count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch"]):
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
    out = Path(f"/tmp/wave13/w68_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
