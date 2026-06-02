#!/usr/bin/env python3
"""Wave 80 — kev-catalog / schrems-challenge / intangible-safeguard / bis-triennial / restatement-event.

Bridges Wave 79:
- kev-catalog ↔ cveCna.flagDisclosureGap
- schrems-challenge ↔ crossBorderTransfer.flagScaleRisk
- intangible-safeguard ↔ unescoInDanger.flagDegradationDriver
- bis-triennial ↔ fedSwapUsage.flagPolicyTradeoff
- restatement-event ↔ auditFirmOversight.flagDeficiency
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "kev-catalog",
    "app": "kevCatalog",
    "methods": [
      {
        "name": "recordEntry",
        "desc": "CISA KEV / BOD 22-01 known exploited vulnerability entry (bridges cveCna.flagDisclosureGap + cyber-vuln-cve + cyber-vuln-patch)",
        "fields": [
          ("entryId", "string", True),
          ("cveId", "string", True),
          ("productCategory", "string", True),
          ("exploitationMaturity", "string", True, ["poc_public","itw_active","targeted","widespread","ransomware_used","apt_used","criminal_campaign","botnet_worm"]),
          ("disclosureGapVid", "string", False, None, "bridges cveCna.flagDisclosureGap"),
          ("dueDate", "string", True),
          ("addedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRemediationLag",
        "desc": "Remediation lag / extension request / enterprise gap (bridges cveCna.flagDisclosureGap + cyber-compliance-isms + cyber-incident-report)",
        "fields": [
          ("flagId", "string", True),
          ("entryVid", "string", True, None, "bridges recordEntry"),
          ("lagKind", "string", True, ["beyond_due_date","extension_granted","waiver_denied","no_asset_inventory","eol_device","compensating_control","air_gap_claim","exception_policy","patch_breaks_ops","budget_cycle_delay"]),
          ("daysPastDue", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "schrems-challenge",
    "app": "schremsChallenge",
    "methods": [
      {
        "name": "recordCase",
        "desc": "GDPR / Schrems-style / Max Schrems challenge (bridges crossBorderTransfer.flagScaleRisk + data-adequacy + federal-court-docket)",
        "fields": [
          ("caseId", "string", True),
          ("respondentLei", "string", False),
          ("forum", "string", True, ["cjeu","edpb","dpa_ie","dpa_de","dpa_fr","dpa_es","dpa_at","dpa_nl","cjeu_advocate","national_high_court","ftc_enforcement","fcc_consent","commerce_dep"]),
          ("issue", "string", True, ["adequacy_decision","scc_bcr_validity","tia_quality","direct_transfers","subsequent_transfers","sub_processor","joint_controller","legitimate_interest","essential_equivalence"]),
          ("scaleRiskVid", "string", False, None, "bridges crossBorderTransfer.flagScaleRisk"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRemedy",
        "desc": "Fine / injunction / data flow cessation (bridges crossBorderTransfer.flagScaleRisk + enforcementAction + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("caseVid", "string", True, None, "bridges recordCase"),
          ("remedyKind", "string", True, ["record_fine","injunction_halt","cease_transfer","algorithm_suspension","delete_data","uhc_restriction","processing_ban","representation_obligation","public_warning","deletion_fragment","consent_reset"]),
          ("fineMusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "intangible-safeguard",
    "app": "intangibleSafeguard",
    "methods": [
      {
        "name": "recordInscription",
        "desc": "Intangible cultural heritage inscription (UNESCO 2003 Convention — bridges unescoInDanger.flagDegradationDriver + cultural-heritage + fpic-consent)",
        "fields": [
          ("inscriptionId", "string", True),
          ("elementName", "string", True),
          ("listKind", "string", True, ["representative_list","urgent_safeguarding","register_good_practice","multi_national_serial"]),
          ("domain", "string", True, ["oral_tradition","performing_arts","social_practices","knowledge_universe","craftsmanship","sports_rituals","medicinal_knowledge","linguistic"]),
          ("countriesIso3", "string", True),
          ("degradationVid", "string", False, None, "bridges unescoInDanger.flagDegradationDriver"),
          ("inscribedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSafeguardingRisk",
        "desc": "Transmission risk / bearers dying / commodification (bridges unescoInDanger.flagDegradationDriver + fpic-consent + cultural-heritage)",
        "fields": [
          ("flagId", "string", True),
          ("inscriptionVid", "string", True, None, "bridges recordInscription"),
          ("riskKind", "string", True, ["bearers_dying","language_death","commodification","misappropriation","tourism_impact","youth_disengage","modernization","armed_conflict","economic_pressure","intellectual_property_claim"]),
          ("bearersRemaining", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "bis-triennial",
    "app": "bisTriennial",
    "methods": [
      {
        "name": "recordSurveyPoint",
        "desc": "BIS Triennial Central Bank Survey data point (bridges fedSwapUsage.flagPolicyTradeoff + fx-swap-lines + commodity-trade)",
        "fields": [
          ("surveyId", "string", True),
          ("year", "integer", True),
          ("instrumentKind", "string", True, ["spot","outright_forward","fx_swap","xccy_swap","options","ndf","fx_futures","otc_ir","otc_equity","otc_commodity","otc_credit","dealer_to_dealer","dealer_to_customer"]),
          ("currencyPair", "string", True),
          ("adtvBusd", "number", False, None, "Average Daily Turnover"),
          ("swapUsageVid", "string", False, None, "bridges fedSwapUsage.flagPolicyTradeoff"),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagShift",
        "desc": "Structural shift / dedollarization / yuan rise (bridges fedSwapUsage.flagPolicyTradeoff + stablecoin-reserves + digital-euro-brics)",
        "fields": [
          ("flagId", "string", True),
          ("surveyVid", "string", True, None, "bridges recordSurveyPoint"),
          ("shiftKind", "string", True, ["dedollarization","yuan_internationalization","euro_stabilization","yen_swap_drop","offshore_cny","onshore_cny","rupee_internationalization","crypto_ramp","asian_clearing_union","gulf_settlement_diversion"]),
          ("magnitudeDeltaPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "restatement-event",
    "app": "restatementEvent",
    "methods": [
      {
        "name": "recordRestatement",
        "desc": "Financial statement restatement (Reissuance / Little-R / Big-R — bridges auditFirmOversight.flagDeficiency + enforcementAction + securities-investor)",
        "fields": [
          ("restatementId", "string", True),
          ("filerLei", "string", False),
          ("restatementKind", "string", True, ["big_r_8k_item_4_02","little_r_correction","reissuance_prior","fyzs","ipo_retracted","equity_dilution_restated","revenue_recognition","lease_accounting","crypto_accounting","sbc_backdated","segment_reporting"]),
          ("auditDeficiencyVid", "string", False, None, "bridges auditFirmOversight.flagDeficiency"),
          ("periodsRestated", "integer", False),
          ("disclosedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagStockImpact",
        "desc": "Stock price impact / class action / delisting (bridges auditFirmOversight.flagDeficiency + classSettlement + enforcementAction)",
        "fields": [
          ("flagId", "string", True),
          ("restatementVid", "string", True, None, "bridges recordRestatement"),
          ("impactKind", "string", True, ["sharp_decline","trading_halt","circuit_breaker","listing_standards","dep_concern","delisting_exchange","class_action_filed","sec_investigation","indictment","ceo_resign","cfo_resign"]),
          ("declinePct", "number", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","subjects","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence","devices","incidents","countries","detections","dark","embargo","bearers","periods"]):
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
    out = Path(f"/tmp/wave13/w80_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
