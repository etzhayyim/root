#!/usr/bin/env python3
"""Wave 58 — ungp-nap / feed-provenance / compliance-monitor / soe-balance-sheet / ais-dark-vessel.

Bridges Wave 57:
- ungp-nap ↔ workerGrievance.flagRemedyFailure
- feed-provenance ↔ aquacultureCert.flagCertificationRisk
- compliance-monitor ↔ enforcementAction.flagCorporateResolution
- soe-balance-sheet ↔ debtTransparency.flagHiddenDebt
- ais-dark-vessel ↔ portStateMeasures.flagEvasionPattern
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "ungp-nap",
    "app": "ungpNap",
    "methods": [
      {
        "name": "recordNap",
        "desc": "UN Guiding Principles National Action Plan / OECD MNE NCP (bridges workerGrievance.flagRemedyFailure + ilo-labor-rights + indigenous-rights)",
        "fields": [
          ("napId", "string", True),
          ("countryIso3", "string", True),
          ("napKind", "string", True, ["national_action_plan","oecd_ncp_framework","business_human_rights_law","mandatory_due_diligence","voluntary_code","sector_specific","indigenous_frbrco"]),
          ("scope", "string", True, ["full_business_human_rights","mhrdd_only","supply_chain","conflict_minerals","forced_labor","child_labor","indigenous","environmental"]),
          ("remedyFailureVid", "string", False, None, "bridges workerGrievance.flagRemedyFailure"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagImplementationGap",
        "desc": "UNGP implementation gap / pillar 3 weakness (bridges workerGrievance.flagRemedyFailure + indigenous-rights + just-transition)",
        "fields": [
          ("gapId", "string", True),
          ("napVid", "string", True, None, "bridges recordNap"),
          ("gapKind", "string", True, ["pillar_1_state_duty","pillar_2_corp_respect","pillar_3_remedy","no_enforcement","weak_penalty","judicial_access","non_state_judicial","operational_level"]),
          ("severityTier", "string", False, ["minor","moderate","significant","severe"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "feed-provenance",
    "app": "feedProvenance",
    "methods": [
      {
        "name": "recordFeedLot",
        "desc": "Aquaculture / livestock feed lot provenance (bridges aquacultureCert.flagCertificationRisk + eudr-deforestation + forestry-mrv)",
        "fields": [
          ("lotId", "string", True),
          ("millLei", "string", False),
          ("feedType", "string", True, ["fishmeal","fish_oil","soy_meal","soy_protein_concentrate","palm_kernel","corn_ddgs","insect_meal","algal_oil","single_cell_protein","krill_meal","plant_protein_blend"]),
          ("sourceCountryIso3", "string", True),
          ("volumeTonnes", "number", False),
          ("certificationRiskVid", "string", False, None, "bridges aquacultureCert.flagCertificationRisk"),
          ("deforestationRiskFlag", "boolean", False),
          ("producedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFeedLinkage",
        "desc": "Feed-to-deforestation / illegal fishing linkage (bridges aquacultureCert.flagCertificationRisk + eudr-deforestation + fisheries-iuu)",
        "fields": [
          ("linkageId", "string", True),
          ("lotVid", "string", True, None, "bridges recordFeedLot"),
          ("linkageKind", "string", True, ["amazon_deforestation","cerrado_clearance","indonesian_peatland","west_african_iuu","antarctic_krill_overfish","soy_moratorium_breach","labor_rights_breach","dolphin_bycatch"]),
          ("affectedHectares", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "compliance-monitor",
    "app": "complianceMonitor",
    "methods": [
      {
        "name": "recordMonitorReport",
        "desc": "DOJ / SEC / OFAC independent compliance monitor report (bridges enforcementAction.flagCorporateResolution + fcpa + sanctions-screening)",
        "fields": [
          ("reportId", "string", True),
          ("companyLei", "string", False),
          ("resolutionVid", "string", False, None, "bridges enforcementAction.flagCorporateResolution"),
          ("monitorKind", "string", True, ["doj_independent","sec_consultant","ofac_compliance","fca_uk_skilled_person","cfius_mitigation","ftc_privacy_monitor","corporate_integrity_agreement","deferred_prosecution"]),
          ("reportRound", "integer", False),
          ("findingsCount", "integer", False),
          ("submittedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBreachOfTerms",
        "desc": "Material breach of DPA / monitor-identified failure (bridges enforcementAction.flagCorporateResolution + fcpa + esg-controversy)",
        "fields": [
          ("breachId", "string", True),
          ("reportVid", "string", True, None, "bridges recordMonitorReport"),
          ("breachKind", "string", True, ["new_misconduct","cooperation_failure","record_keeping","reporting_defect","compliance_culture","tone_at_top","recidivism","cover_up","monitor_interference"]),
          ("extensionSought", "boolean", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "soe-balance-sheet",
    "app": "soeBalanceSheet",
    "methods": [
      {
        "name": "recordDisclosure",
        "desc": "State-owned enterprise balance sheet / contingent liabilities (bridges debtTransparency.flagHiddenDebt + sovereign-debt + fiscal-risk)",
        "fields": [
          ("disclosureId", "string", True),
          ("soeLei", "string", False),
          ("parentGovIso3", "string", True),
          ("sector", "string", True, ["power","oil_gas","mining","rail_transport","air_transport","shipping","telecom","banking_development","insurance","pension","agriculture","water","postal"]),
          ("totalAssetsBusd", "number", False),
          ("totalDebtBusd", "number", False),
          ("sovereignGuaranteedBusd", "number", False),
          ("hiddenDebtVid", "string", False, None, "bridges debtTransparency.flagHiddenDebt"),
          ("asOfDate", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagContingentRisk",
        "desc": "Contingent liability / sovereign guarantee call risk (bridges debtTransparency.flagHiddenDebt + sovereign-debt + imf-article-iv)",
        "fields": [
          ("flagId", "string", True),
          ("disclosureVid", "string", True, None, "bridges recordDisclosure"),
          ("riskKind", "string", True, ["guarantee_call_imminent","cross_default_trigger","quasi_fiscal_operation","off_balance_vehicle","pension_underfunded","currency_mismatch","state_aid_rule","ppp_termination"]),
          ("triggerAmountBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ais-dark-vessel",
    "app": "aisDarkVessel",
    "methods": [
      {
        "name": "recordDarkEvent",
        "desc": "Global Fishing Watch / Planet Labs AIS dark-vessel event (bridges portStateMeasures.flagEvasionPattern + fisheries-iuu + hormuz)",
        "fields": [
          ("eventId", "string", True),
          ("vesselImo", "string", False),
          ("flagStateIso3", "string", False),
          ("vesselKind", "string", True, ["fishing","cargo","tanker","bulk_carrier","reefer","transshipment","military_auxiliary","research","passenger"]),
          ("detectionSource", "string", True, ["sar_satellite","optical_satellite","vms","port_inspection","witness_report","military_tracking","bluetooth_ais_emulation"]),
          ("darkDurationHours", "integer", False),
          ("evasionVid", "string", False, None, "bridges portStateMeasures.flagEvasionPattern"),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSanctionsEvasion",
        "desc": "Sanctions / oil embargo / illicit ship-to-ship transfer (bridges portStateMeasures.flagEvasionPattern + ofac-sanctions + hormuz-sts-transfer)",
        "fields": [
          ("flagId", "string", True),
          ("eventVid", "string", True, None, "bridges recordDarkEvent"),
          ("evasionKind", "string", True, ["shadow_fleet_iran","shadow_fleet_russia","shadow_fleet_venezuela","sts_transfer","flag_hopping","ais_spoofing","document_forgery","insurance_fraud","price_cap_evasion"]),
          ("estCargoBarrels", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("riskTier", "if estCargoBarrels != null and estCargoBarrels >= 1000000 then \"severe\" else if estCargoBarrels != null and estCargoBarrels >= 100000 then \"significant\" else \"moderate\"", ["moderate","significant","severe"]),
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
            if ftype == "integer" and any(k in col for k in ["count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels"]):
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
    out = Path(f"/tmp/wave13/w58_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
