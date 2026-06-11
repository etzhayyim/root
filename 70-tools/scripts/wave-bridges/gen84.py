#!/usr/bin/env python3
"""Wave 84 — mica-license / judicial-review-gdpr / genocide-convention / paris-club / congressional-stock.

All-string field schemas to avoid the kotodama smoke-payload number-cast bug.

Bridges Wave 83:
- mica-license ↔ stablecoinRun.flagReserveOpacity
- judicial-review-gdpr ↔ gdprEnforcementPattern.flagFinePatterns
- genocide-convention ↔ minorityRights.flagBacklash
- paris-club ↔ bricsBank.flagGovernanceDispute
- congressional-stock ↔ insiderTrading.flagFrontRunning
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "mica-license",
    "app": "micaLicense",
    "methods": [
      {
        "name": "recordAuthorization",
        "desc": "MiCA CASP / EMT / ART authorization (bridges stablecoinRun.flagReserveOpacity + mica-crypto + dpa-authority)",
        "fields": [
          ("authId", "string", True),
          ("issuerLei", "string", False),
          ("serviceKind", "string", True, ["casp_custody","casp_exchange","casp_oft","emt_issuance","art_issuance","portfolio_mgmt","advice","transfer","onchain_op","white_label","trading_platform","passport_in_out"]),
          ("memberStateIso3", "string", True),
          ("homeCompetentAuth", "string", True, ["bafin_de","cssf_lu","fcmc_lv","acpr_fr","cmvm_pt","consob_it","gfsc_gi","cnmv_es","cssi_lu","fma_at","fma_li"]),
          ("reserveOpacityVid", "string", False, None, "bridges stablecoinRun.flagReserveOpacity"),
          ("authorizedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPassportAbuse",
        "desc": "Passport abuse / letterbox / host-state concern (bridges stablecoinRun.flagReserveOpacity + dpa-authority + eu-dpp)",
        "fields": [
          ("flagId", "string", True),
          ("authVid", "string", True, None, "bridges recordAuthorization"),
          ("concernKind", "string", True, ["letterbox","home_weak_supervision","host_pushback","esma_peer_review","withdrawal_threat","substance_gap","aml_weak","retail_distribution_unauth","misleading_communication","white_label_scheme"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "judicial-review-gdpr",
    "app": "judicialReviewGdpr",
    "methods": [
      {
        "name": "recordReview",
        "desc": "National court / CJEU judicial review of GDPR action (bridges gdprEnforcementPattern.flagFinePatterns + federal-court-docket + schrems-challenge)",
        "fields": [
          ("reviewId", "string", True),
          ("forum", "string", True, ["cjeu","general_court_eu","advocate_general","bundesverfassungsgericht","oberlandesgericht","bverwg","conseil_deta","council_of_state_it","audiencia_nacional_es","supreme_ie","tribunal_suisse","uk_high_court"]),
          ("appellantCategory", "string", True, ["dpa","data_subject","controller","processor","joint_controller","ngo","government","industry_association"]),
          ("groundsKind", "string", True, ["procedural_violation","proportionality","misinterpretation","legitimate_interest","transfer_validity","adequacy_proportionality","erasure_limits","right_to_be_forgotten","ai_training_gap","opt_out_mechanism"]),
          ("patternVid", "string", False, None, "bridges gdprEnforcementPattern.flagFinePatterns"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRulingImpact",
        "desc": "Ruling impact / pattern shift / preliminary reference (bridges gdprEnforcementPattern.flagFinePatterns + schrems-challenge + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("reviewVid", "string", True, None, "bridges recordReview"),
          ("rulingKind", "string", True, ["annulled","upheld","referred_to_cjeu","partial_annul","interpretive_guidance","doctrinal_shift","public_body_liable","private_body_liable","remedy_expanded","remedy_narrowed","damages_quantified"]),
          ("rulingAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "genocide-convention",
    "app": "genocideConvention",
    "methods": [
      {
        "name": "recordProcedure",
        "desc": "Genocide Convention Art I/II/III procedure (bridges minorityRights.flagBacklash + poc-ihl + universal-jurisdiction)",
        "fields": [
          ("procedureId", "string", True),
          ("situationCountryIso3", "string", True),
          ("procedureKind", "string", True, ["icj_contentious","icj_advisory","ucc_article_iii","national_prosecution","eccc_khmer","ictr_rwanda_legacy","icty_yugo_legacy","icc_referral","universal_jurisdiction","commission_inquiry","fact_finding"]),
          ("primaryRespondent", "string", False),
          ("backlashVid", "string", False, None, "bridges minorityRights.flagBacklash"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagProvisionalMeasure",
        "desc": "Provisional measures / irreparable harm / non-compliance (bridges minorityRights.flagBacklash + poc-ihl + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("procedureVid", "string", True, None, "bridges recordProcedure"),
          ("measureKind", "string", True, ["prevent_genocide","halt_military","allow_humanitarian","preserve_evidence","protect_witnesses","stop_destruction","inform_court","reporting_obligation","ordered_compliance","non_compliance"]),
          ("orderedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "paris-club",
    "app": "parisClub",
    "methods": [
      {
        "name": "recordTreatment",
        "desc": "Paris Club debt treatment (bridges bricsBank.flagGovernanceDispute + sovereign-debt + imf-article-iv)",
        "fields": [
          ("treatmentId", "string", True),
          ("debtorCountryIso3", "string", True),
          ("treatmentKind", "string", True, ["classic_terms","houston_terms","naples_terms","cologne_terms","evian_approach","ex_ante","common_framework_cf","suspension_dsss","reprofiling","debt_for_nature","debt_for_climate","post_cutoff"]),
          ("governanceVid", "string", False, None, "bridges bricsBank.flagGovernanceDispute"),
          ("signedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagNonParisHoldout",
        "desc": "Non-Paris creditor / holdout / comparability concern (bridges bricsBank.flagGovernanceDispute + sovereign-debt + debt-transparency)",
        "fields": [
          ("flagId", "string", True),
          ("treatmentVid", "string", True, None, "bridges recordTreatment"),
          ("holdoutKind", "string", True, ["china_exim","china_dev_bank","gcc_bilateral","resource_backed_holdout","private_bond","commercial_bank","lira_hedgefund","ccac_cuba","debt_buyback","lone_wolf","pari_passu_litigation"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "congressional-stock",
    "app": "congressionalStock",
    "methods": [
      {
        "name": "recordStockTransaction",
        "desc": "Member of Congress / senior official stock transaction (STOCK Act / PTRs — bridges insiderTrading.flagFrontRunning + ethics-disclosure + judicial-influence)",
        "fields": [
          ("transactionId", "string", True),
          ("memberCategory", "string", True, ["sitting_sen","sitting_rep","spouse","dependent_child","senior_staff","cabinet","fed_reserve","justice_scotus","fed_judge","whistleblower_protect"]),
          ("transactionKind", "string", True, ["buy","sell","exchange","purchase_option","sell_option","convert","margin_call","crypto_purchase","brokerage_consolidate","retirement_rebalance","immediate_family","trust_transaction"]),
          ("issuerTicker", "string", False),
          ("frontRunningVid", "string", False, None, "bridges insiderTrading.flagFrontRunning"),
          ("filedPtrAt", "string", True),
          ("executedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagLateFiling",
        "desc": "Late PTR filing / 45-day window breach (bridges insiderTrading.flagFrontRunning + ethicsDisclosure + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("transactionVid", "string", True, None, "bridges recordStockTransaction"),
          ("lateKind", "string", True, ["past_45_day","past_30_day","undisclosed_spouse","undisclosed_child","grouped_disclosure","rounded_amount","error_amended","no_filing","hearing_day_trade","pattern_repeat","committee_chair_self","markup_trade"]),
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
    out = Path(f"/tmp/wave13/w84_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
