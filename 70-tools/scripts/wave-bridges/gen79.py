#!/usr/bin/env python3
"""Wave 79 — cve-cna / cross-border-transfer / unesco-in-danger / fed-swap-usage / audit-firm.

Bridges Wave 78:
- cve-cna ↔ zeroDayBroker.flagVendorPatchLag
- cross-border-transfer ↔ dataLocalization.flagFragmentation
- unesco-in-danger ↔ heritageAccessibility.flagConservationConflict
- fed-swap-usage ↔ xccyBasis.flagBlowout
- audit-firm-oversight ↔ spsStandardIso.flagCertificationSleight
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "cve-cna",
    "app": "cveCna",
    "methods": [
      {
        "name": "recordAssignment",
        "desc": "CVE Numbering Authority (CNA) assignment (bridges zeroDayBroker.flagVendorPatchLag + cyber-vuln-cve + cyber-vuln-patch)",
        "fields": [
          ("cveId", "string", True),
          ("cnaLei", "string", False),
          ("productCategory", "string", True, ["os_kernel","browser","email","messaging","crypto_lib","network_stack","iot_firmware","scada","medical_device","av_endpoint","cloud_runtime","auth_service","edge_router","printer","smart_tv"]),
          ("cvssBase", "number", False),
          ("assignerProcess", "string", True, ["cna_local","root_mitre","vendor_self_assign","ics_cert","jpcert_us","rootca_third","bug_bounty","researcher_coordinate","embargo"]),
          ("patchLagVid", "string", False, None, "bridges zeroDayBroker.flagVendorPatchLag"),
          ("assignedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDisclosureGap",
        "desc": "Disclosure coordination gap / embargo leakage (bridges zeroDayBroker.flagVendorPatchLag + cyber-incident-ioc + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("cveVid", "string", True, None, "bridges recordAssignment"),
          ("gapKind", "string", True, ["disputed","rej","rejected_after_assignment","embargo_leak","kev_catalog_missing","nvd_backlog","cvss_mismatch","vendor_denied","downstream_uncoordinated","severity_dispute","post_disclosure_itw"]),
          ("daysEmbargoToDisclose", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cross-border-transfer",
    "app": "crossBorderTransfer",
    "methods": [
      {
        "name": "recordTransferMechanism",
        "desc": "Cross-border data transfer mechanism (SCC / BCR / adequacy decision — bridges dataLocalization.flagFragmentation + data-adequacy + cross-border-data)",
        "fields": [
          ("mechanismId", "string", True),
          ("senderCountryIso3", "string", True),
          ("receiverCountryIso3", "string", True),
          ("mechanismKind", "string", True, ["adequacy_eu","scc_2021","bcr","codes_of_conduct","certification","tia_transfer_impact","derogation","strictly_necessary","schrems_ii_remedies","local_safeguard","apec_cbpr","global_cbpr","prc_outbound_assessment","india_dpdpa"]),
          ("fragmentationVid", "string", False, None, "bridges dataLocalization.flagFragmentation"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagScaleRisk",
        "desc": "High-risk transfer / government access concern (bridges dataLocalization.flagFragmentation + sanctions-entry + fpic-consent)",
        "fields": [
          ("flagId", "string", True),
          ("mechanismVid", "string", True, None, "bridges recordTransferMechanism"),
          ("riskKind", "string", True, ["foreign_govt_access","section_702","doj_section_215","executive_order_12333","cloud_act","subpoena_bulk","lawful_intercept","signals_intel","mass_surveillance","unresolved_tia","schrems_ii_gap","gdpr_breach_ripe"]),
          ("estDataSubjects", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "unesco-in-danger",
    "app": "unescoInDanger",
    "methods": [
      {
        "name": "recordListingChange",
        "desc": "UNESCO World Heritage In-Danger / delisting / reactive monitoring (bridges heritageAccessibility.flagConservationConflict + cultural-heritage + biodiversity-gbf)",
        "fields": [
          ("changeId", "string", True),
          ("siteId", "string", True),
          ("siteKind", "string", True, ["cultural","natural","mixed","intangible_urgent","tentative","transboundary","serial"]),
          ("actionKind", "string", True, ["added_to_in_danger","removed_from_in_danger","reactive_monitoring","delisted","world_heritage_removed","emergency_budget","advisory_mission","state_of_conservation_report"]),
          ("countryIso3", "string", True),
          ("heritageAccessVid", "string", False, None, "bridges heritageAccessibility.flagConservationConflict"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDegradationDriver",
        "desc": "Degradation driver / armed conflict / commercial pressure (bridges heritageAccessibility.flagConservationConflict + cultural-heritage + poc-ihl)",
        "fields": [
          ("flagId", "string", True),
          ("changeVid", "string", True, None, "bridges recordListingChange"),
          ("driverKind", "string", True, ["armed_conflict","looting","uncontrolled_urban","mining_extractive","tourism_overuse","climate_change","invasive_species","illegal_wildlife","lack_of_maintenance","terror_bombing","deforestation","dam_construction","inappropriate_restoration"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "fed-swap-usage",
    "app": "fedSwapUsage",
    "methods": [
      {
        "name": "recordUsage",
        "desc": "Fed central bank swap line usage (Standing/FIMA/emergency — bridges xccyBasis.flagBlowout + fx-swap-lines + treasury-market-stress)",
        "fields": [
          ("usageId", "string", True),
          ("counterpartyCb", "string", True, ["ecb","boe","boj","snb","boc","pboc_cdh","rba","sek","korea","india","mexico","brazil","fima_non_standing"]),
          ("swapKind", "string", True, ["standing_core","fima_repo","emergency_bilateral","dollar_auction_ope_market","central_bank_counterparty","non_primary_dealer_access","chiangmai","cmim_plus","swap_plus"]),
          ("notionalBusd", "number", False),
          ("basisBlowoutVid", "string", False, None, "bridges xccyBasis.flagBlowout"),
          ("drawnAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPolicyTradeoff",
        "desc": "Policy tradeoff / balance sheet footprint / treaty risk (bridges xccyBasis.flagBlowout + sovereign-debt + liquidity-facility)",
        "fields": [
          ("flagId", "string", True),
          ("usageVid", "string", True, None, "bridges recordUsage"),
          ("concernKind", "string", True, ["reserve_accumulation_vs_dollar","balance_sheet_footprint","congressional_pushback","moral_hazard_em","treaty_capacity","pragmatic_vs_legal","swap_reserves_blur","reciprocity_weak","policy_divergence","rate_arbitrage"]),
          ("usageRatePct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "audit-firm-oversight",
    "app": "auditFirmOversight",
    "methods": [
      {
        "name": "recordInspection",
        "desc": "Audit firm regulatory inspection (PCAOB / FRC / JFSA ISO) (bridges spsStandardIso.flagCertificationSleight + enforcementAction + sec-owb)",
        "fields": [
          ("inspectionId", "string", True),
          ("firmLei", "string", False),
          ("regulator", "string", True, ["pcaob","frc_uk","jfsa_mrc","acra_sg","ipab_in","cnmv_es","cssi_lu","acag_br","canadi_cpab","eu_caqeca","rospod_ru"]),
          ("inspectionKind", "string", True, ["full_firm","engagement_review","quality_control","triennial","annual","subsequent_audit","first_time","joint_with_pcaob","home_abroad","multi_firm"]),
          ("sleightVid", "string", False, None, "bridges spsStandardIso.flagCertificationSleight"),
          ("concludedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDeficiency",
        "desc": "Audit deficiency / restatement / violation (bridges spsStandardIso.flagCertificationSleight + enforcementAction + securities-investor)",
        "fields": [
          ("flagId", "string", True),
          ("inspectionVid", "string", True, None, "bridges recordInspection"),
          ("deficiencyKind", "string", True, ["engagement_partner_independence","icfr_gap","critical_matters_not_addressed","audit_trail_lost","evidence_insufficient","scope_limitation","opinion_shopping","rotation_violation","non_audit_service","overseas_referral_weak","client_pressure"]),
          ("restatementRequired", "boolean", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","subjects","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence","devices","incidents","countries","detections","dark","embargo"]):
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
    out = Path(f"/tmp/wave13/w79_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
