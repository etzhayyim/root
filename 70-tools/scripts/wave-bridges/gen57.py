#!/usr/bin/env python3
"""Wave 57 — worker-grievance / aquaculture-cert / enforcement-action / debt-transparency / port-state-measures.

Bridges Wave 56:
- worker-grievance ↔ iloLaborRights.flagNonCompliance
- aquaculture-cert ↔ spsNotification.flagComment
- enforcement-action ↔ federalCourtDocket.flagInjunction
- debt-transparency ↔ worldBankDpf.flagPriorActionSlippage
- port-state-measures ↔ fisheryCollapse.flagQuotaBreach
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "worker-grievance",
    "app": "workerGrievance",
    "methods": [
      {
        "name": "recordGrievance",
        "desc": "Worker grievance filing (ITUC / national labor inspectorate / OECD NCP — bridges iloLaborRights.flagNonCompliance + forced-labor + gender-pay-gap)",
        "fields": [
          ("grievanceId", "string", True),
          ("employerLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("grievanceKind", "string", True, ["wage_theft","unsafe_workplace","union_busting","retaliation","discrimination","sexual_harassment","forced_overtime","child_labor","forced_labor","migrant_exploitation","collective_barg_refusal"]),
          ("channel", "string", True, ["ituc_global_rights","oecd_ncp","national_inspectorate","company_hotline","union_complaint","ngo_report","media_investigation","whistleblower"]),
          ("iloFindingVid", "string", False, None, "bridges iloLaborRights.flagNonCompliance"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRemedyFailure",
        "desc": "Grievance remedy failure / UNGP pillar 3 gap (bridges iloLaborRights.flagNonCompliance + indigenous-rights + just-transition)",
        "fields": [
          ("flagId", "string", True),
          ("grievanceVid", "string", True, None, "bridges recordGrievance"),
          ("failureKind", "string", True, ["no_response","inadequate_remedy","retaliation_post_filing","process_delayed","non_binding_outcome","grievant_intimidation","confidentiality_breach","no_operational_change"]),
          ("affectedWorkers", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "aquaculture-cert",
    "app": "aquacultureCert",
    "methods": [
      {
        "name": "recordCertification",
        "desc": "ASC / BAP / GlobalG.A.P. aquaculture certification (bridges spsNotification.flagComment + seafood-traceability + fisheries-iuu)",
        "fields": [
          ("certId", "string", True),
          ("facilityLei", "string", False),
          ("schemeKind", "string", True, ["asc","bap_4star","bap_3star","bap_2star","globalgap","naturland","label_rouge","best_seafood","fos_friend_sea"]),
          ("speciesGroup", "string", True, ["salmon","shrimp","tilapia","pangasius","seabass","sea_bream","oyster","mussel","abalone","carp","trout","seaweed"]),
          ("countryIso3", "string", True),
          ("productionTonnesYearly", "number", False),
          ("spsCommentVid", "string", False, None, "bridges spsNotification.flagComment"),
          ("certifiedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCertificationRisk",
        "desc": "Certification suspension / sustainability concern (bridges spsNotification.flagComment + seafood-traceability + residue-mrl)",
        "fields": [
          ("flagId", "string", True),
          ("certVid", "string", True, None, "bridges recordCertification"),
          ("riskKind", "string", True, ["certification_suspended","non_conformance","feed_provenance_gap","antibiotic_use","escape_event","disease_outbreak","labor_violation","chain_of_custody_break","greenwashing_claim"]),
          ("severityTier", "string", False, ["watch","elevated","suspended","delisted"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "enforcement-action",
    "app": "enforcementAction",
    "methods": [
      {
        "name": "recordAction",
        "desc": "SEC / DOJ / FTC / CFTC / FinCEN enforcement action (bridges federalCourtDocket.flagInjunction + antitrust-dma + sanctions-screening)",
        "fields": [
          ("actionId", "string", True),
          ("agency", "string", True, ["sec","doj_fraud","doj_antitrust","ftc","cftc","fincen","occ","ofac","cfpb","federal_reserve","fdic","fbi","irs_ci"]),
          ("respondentLei", "string", False),
          ("violationKind", "string", True, ["securities_fraud","insider_trading","market_manipulation","fcpa","antitrust","consumer_protection","aml_bsa","sanctions","wire_fraud","tax_evasion","false_claims","cybersecurity_disclosure"]),
          ("dispositionKind", "string", False, ["settlement","admin_order","consent_decree","deferred_prosecution","non_prosecution","guilty_plea","conviction","dismissal","indictment"]),
          ("injunctionVid", "string", False, None, "bridges federalCourtDocket.flagInjunction"),
          ("monetaryPenaltyMusd", "number", False),
          ("announcedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCorporateResolution",
        "desc": "DPA / NPA / monitor / compliance obligation flag (bridges federalCourtDocket.flagInjunction + esg-controversy + fcpa)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("resolutionKind", "string", True, ["dpa_monitor","npa_monitor","consent_decree","compliance_monitor","disgorgement","officer_bar","industry_ban","admission_of_wrongdoing","recidivist","self_disclosure_credit"]),
          ("monitorTermYears", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "debt-transparency",
    "app": "debtTransparency",
    "methods": [
      {
        "name": "recordDebtDisclosure",
        "desc": "Sovereign debt disclosure (G20 Common Framework joint stats / IIF / Kiel — bridges worldBankDpf.flagPriorActionSlippage + sovereign-debt + imf-article-iv)",
        "fields": [
          ("disclosureId", "string", True),
          ("debtorCountryIso3", "string", True),
          ("creditorCategory", "string", True, ["paris_club","china_bilateral","gcc_bilateral","multilateral","private_bondholder","commercial_bank","resource_backed","collateralized_swap","currency_swap","hidden"]),
          ("creditorEntityLei", "string", False),
          ("principalBusd", "number", False),
          ("dpfSlippageVid", "string", False, None, "bridges worldBankDpf.flagPriorActionSlippage"),
          ("disclosedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagHiddenDebt",
        "desc": "Hidden / non-disclosed debt detection (bridges worldBankDpf.flagPriorActionSlippage + sovereign-debt + imf-article-iv)",
        "fields": [
          ("flagId", "string", True),
          ("disclosureVid", "string", True, None, "bridges recordDebtDisclosure"),
          ("hidingKind", "string", True, ["undisclosed_bilateral","resource_prepayment","collateralized_off_balance","soe_guaranteed","central_bank_swap","confidentiality_clause","revenue_assignment","escrow_arrangement"]),
          ("estimatedBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "port-state-measures",
    "app": "portStateMeasures",
    "methods": [
      {
        "name": "recordInspection",
        "desc": "FAO PSMA / IUU port inspection (bridges fisheryCollapse.flagQuotaBreach + fisheries-iuu + fisheries-subsidies)",
        "fields": [
          ("inspectionId", "string", True),
          ("portIso3", "string", True),
          ("portName", "string", True),
          ("vesselImoOrId", "string", True),
          ("flagStateIso3", "string", True),
          ("inspectionResult", "string", True, ["authorized_land","partial_denied","full_denial","vessel_listed_iuu","irregularity_reported","referral_fmo","documentation_hold","gear_inspection_only"]),
          ("quotaBreachVid", "string", False, None, "bridges fisheryCollapse.flagQuotaBreach"),
          ("catchVolumeTonnes", "number", False),
          ("inspectedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagEvasionPattern",
        "desc": "Port-hopping / flag-of-convenience evasion pattern (bridges fisheryCollapse.flagQuotaBreach + fisheries-iuu + seafood-traceability)",
        "fields": [
          ("patternId", "string", True),
          ("inspectionVid", "string", True, None, "bridges recordInspection"),
          ("evasionKind", "string", True, ["port_hopping","flag_hopping","transshipment_evasion","ais_gap","document_forgery","vessel_id_change","beneficial_owner_hidden","double_flagging","registry_lag"]),
          ("psmaStateCount", "integer", False),
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
            if ftype == "integer" and any(k in col for k in ["count","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued"]):
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
    out = Path(f"/tmp/wave13/w57_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
