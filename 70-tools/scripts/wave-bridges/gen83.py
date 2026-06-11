#!/usr/bin/env python3
"""Wave 83 — stablecoin-run / gdpr-enforcement / minority-rights / brics-bank / insider-trading.

Bridges Wave 82:
- stablecoin-run ↔ cryptoMixerSanction.flagDelistingChallenge
- gdpr-enforcement-pattern ↔ edpbBinding.flagNationalResistance
- minority-rights ↔ bilingualEducation.flagOutcomeGap
- brics-bank ↔ mbridgeSettlement.flagDedollarization
- insider-trading ↔ auditCommitteeOversight.flagIndependenceGap
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "stablecoin-run",
    "app": "stablecoinRun",
    "methods": [
      {
        "name": "recordRedemption",
        "desc": "Stablecoin redemption run / depeg event (bridges cryptoMixerSanction.flagDelistingChallenge + mica-crypto + stablecoin-reserves)",
        "fields": [
          ("eventId", "string", True),
          ("issuerLei", "string", False),
          ("stablecoin", "string", True, ["usdt","usdc","dai","frax","lusd","usdp","gusd","ustc_failed","first_digital","pax_gold","pyusd","crvusd","susd","rai","fei_discontinued"]),
          ("triggerKind", "string", True, ["bank_failure","sanctions","regulatory","exchange_delisting","collateral_concern","audit_concern","oracle_failure","governance_breakdown","whales_exit","svb_exposure","silvergate_signature","fdic_gap"]),
          ("sanctionVid", "string", False, None, "bridges cryptoMixerSanction.flagDelistingChallenge"),
          ("depegBasisPoints", "number", False),
          ("occurredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagReserveOpacity",
        "desc": "Reserve attestation / transparency gap (bridges cryptoMixerSanction.flagDelistingChallenge + stablecoin-reserves + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("eventVid", "string", True, None, "bridges recordRedemption"),
          ("concernKind", "string", True, ["attestation_gap","mhlk_commercial","bank_deposit_unclear","treasury_bills_only_claim","rehypothecation","cross_issuer_debt","protocol_owned_reserve_recursive","mmp_exposure","counterparty_credit","opaque_custodian"]),
          ("auditorName", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "gdpr-enforcement-pattern",
    "app": "gdprEnforcementPattern",
    "methods": [
      {
        "name": "recordCaseCluster",
        "desc": "GDPR enforcement pattern / repeat offender / sector sweep (bridges edpbBinding.flagNationalResistance + schrems-challenge + dpa-authority)",
        "fields": [
          ("clusterId", "string", True),
          ("dpaAuthor", "string", True),
          ("patternKind", "string", True, ["sector_sweep","big_tech_focus","health_data","children_data","ai_training","adtech_cookies","hr_workplace","police_mass_surveil","telecom_data","banking_kyc","ecommerce_personalization"]),
          ("resistanceVid", "string", False, None, "bridges edpbBinding.flagNationalResistance"),
          ("patternStartedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFinePatterns",
        "desc": "Fine escalation / global maximum / turnover cap (bridges edpbBinding.flagNationalResistance + enforcementAction + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("clusterVid", "string", True, None, "bridges recordCaseCluster"),
          ("patternKind", "string", True, ["turnover_2pct","turnover_4pct","escalating","benchmark_case","eu_wide","consolidated","company_group","symbolic_fine","delayed_enforcement","judicial_review_pending"]),
          ("totalFineMusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "minority-rights",
    "app": "minorityRights",
    "methods": [
      {
        "name": "recordReportFinding",
        "desc": "CERD / CCPR / UN minority rights report (bridges bilingualEducation.flagOutcomeGap + indigenous-rights + crpd-disability)",
        "fields": [
          ("findingId", "string", True),
          ("countryIso3", "string", True),
          ("treatyBody", "string", True, ["cerd","ccpr","cescr","cedaw","crc","crpd","cat","un_minority","undrip_mandate","oas_iachr","echr","af_commission","osce_mins"]),
          ("minorityKind", "string", True, ["ethnic","religious","linguistic","indigenous","national_minority","migrant","stateless_descendant","caste_based","lgbtqi","disability","women","children"]),
          ("outcomeGapVid", "string", False, None, "bridges bilingualEducation.flagOutcomeGap"),
          ("concludedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBacklash",
        "desc": "Backlash / anti-minority legislation / hate crime spike (bridges bilingualEducation.flagOutcomeGap + press-freedom + transnational-repression)",
        "fields": [
          ("flagId", "string", True),
          ("findingVid", "string", True, None, "bridges recordReportFinding"),
          ("backlashKind", "string", True, ["legislation_rollback","hate_crime_spike","media_campaign","language_restriction","religious_restriction","expulsion_denaturalization","resettlement_forced","cultural_ban","lgbtqi_crackdown","femicide_surge","indigenous_land_grab","caste_reservation_rollback"]),
          ("severityTier", "string", False, ["watch","moderate","severe","crisis","genocide_warning"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "brics-bank",
    "app": "bricsBank",
    "methods": [
      {
        "name": "recordProjectFinance",
        "desc": "New Development Bank / AIIB / NDB BRICS project financing (bridges mbridgeSettlement.flagDedollarization + sovereign-debt + world-bank-dpf)",
        "fields": [
          ("projectId", "string", True),
          ("institution", "string", True, ["ndb_new_dev_bank","aiib_asian_infra","crdp_russia","ciab_china","brics_pay_network","brics_grain_ex","brics_reinsurance","brics_rating_agency","brics_satellite"]),
          ("borrowerCountryIso3", "string", True),
          ("sectorKind", "string", True, ["transport","energy","water","urban","social","industrial","digital","climate","health","sovereign_bond","local_currency_bond","local_currency_swap","covid_facility","bridge_finance"]),
          ("dedollarizationVid", "string", False, None, "bridges mbridgeSettlement.flagDedollarization"),
          ("localCurrencyPct", "number", False),
          ("approvedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagGovernanceDispute",
        "desc": "Governance / veto / non-Western alignment (bridges mbridgeSettlement.flagDedollarization + sovereign-debt + imf-article-iv)",
        "fields": [
          ("flagId", "string", True),
          ("projectVid", "string", True, None, "bridges recordProjectFinance"),
          ("disputeKind", "string", True, ["veto_exercised","non_western_borrower_block","sanctions_override","ida_overlap","russian_chair","brics_plus_admission","new_member_conflict","lending_threshold","dollar_default_dispute","reserve_currency_alt"]),
          ("affectedVoteShare", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "insider-trading",
    "app": "insiderTrading",
    "methods": [
      {
        "name": "recordEnforcement",
        "desc": "Insider trading enforcement (SEC / DOJ criminal / international — bridges auditCommitteeOversight.flagIndependenceGap + enforcementAction + securities-investor)",
        "fields": [
          ("enforcementId", "string", True),
          ("respondentCategory", "string", True, ["corporate_insider","tipper","tippee","analyst","banker","hedge_fund","political_insider","spouse","friend","political_trade","bond_market_maker","arb","fixed_income_mm"]),
          ("jurisdiction", "string", True, ["us_sec","us_doj","uk_fca","jp_sesc","de_bafin","fr_amf","sg_mas","hk_sfc","kr_fss","eu_esma","au_asic","ca_osc","br_cvm","in_sebi","ch_finma"]),
          ("independenceGapVid", "string", False, None, "bridges auditCommitteeOversight.flagIndependenceGap"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFrontRunning",
        "desc": "Front-running / political-trade / shadow-trade (bridges auditCommitteeOversight.flagIndependenceGap + enforcementAction + ethicsDisclosure)",
        "fields": [
          ("flagId", "string", True),
          ("enforcementVid", "string", True, None, "bridges recordEnforcement"),
          ("frontKind", "string", True, ["pre_public_trade","congressional_stock","pelosi_trade","shadow_trading","doppelganger_security","parked_short","misappropriation","breach_of_duty","hot_hand","insider_etf_skew","nonpublic_tender_offer","merger_arb_pre"]),
          ("estProfitMusd", "number", False),
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
    out = Path(f"/tmp/wave13/w83_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
