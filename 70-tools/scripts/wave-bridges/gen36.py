#!/usr/bin/env python3
"""Wave 36 bridges — MASS / FHIR / WADA / eVTOL / press-finance."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "mass-autonomous-ship",
    "app": "massAutonomousShip",
    "methods": [
      {
        "name": "certifyAutonomyLevel",
        "desc": "IMO MASS Code autonomy certification (bridges carrier-fleet + aviation-safety + laws-autonomous-weapons + ai-governance)",
        "fields": [
          ("certificationId", "string", True),
          ("imo", "string", True),
          ("operatorLei", "string", False),
          ("imoMassLevel", "integer", True, None, "1-4 per IMO MSC.1/Circ.1638"),
          ("autonomyDescription", "string", False),
          ("shoreControlCenterLei", "string", False),
          ("flagStateIso3", "string", True),
          ("certifyingAuthorityLei", "string", False),
          ("certifiedAt", "string", True),
          ("expiresAt", "string", False),
        ],
        "classify": ("autonomyTier", "if imoMassLevel >= 4 then \"fully_autonomous\" else if imoMassLevel = 3 then \"remote_unmanned\" else if imoMassLevel = 2 then \"remote_manned\" else \"assisted\"", ["assisted","remote_manned","remote_unmanned","fully_autonomous"]),
      },
      {
        "name": "flagCyberOtIncident",
        "desc": "MASS cyber / OT incident (bridges cyber-incident + maritime-piracy + quantum-safe-crypto)",
        "fields": [
          ("incidentId", "string", True),
          ("certificationVid", "string", True, None, "bridges certifyAutonomyLevel"),
          ("incidentKind", "string", True, ["gps_spoofing","ais_manipulation","ot_intrusion","c2_loss","ml_model_drift","sensor_tamper","ransomware"]),
          ("cyberIncidentVid", "string", False, None, "bridges open-cyber-incident"),
          ("impactDescription", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if incidentKind = \"c2_loss\" or incidentKind = \"ransomware\" then \"critical\" else if incidentKind = \"gps_spoofing\" or incidentKind = \"ot_intrusion\" then \"severe\" else \"operational\"", ["operational","severe","critical"]),
      },
    ],
  },
  {
    "slug": "fhir-health-data",
    "app": "fhirHealthData",
    "methods": [
      {
        "name": "registerTerminology",
        "desc": "FHIR R5 + ICD-11 + SNOMED CT + LOINC + RxNorm terminology (bridges universal-health-coverage + pharma-supply + amr-surveillance)",
        "fields": [
          ("terminologyId", "string", True),
          ("system", "string", True, ["fhir_r5","icd_11","icd_10_cm","snomed_ct","loinc","rxnorm","hl7_v2","omop_cdm","openehr","gs1_healthcare"]),
          ("resourceType", "string", True, None, "FHIR Patient / Observation / Condition / Procedure / MedicationRequest / Encounter / Immunization / etc"),
          ("vsVersion", "string", False),
          ("jurisdictionIso3", "string", False),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInteropIncident",
        "desc": "FHIR incident / IHE gap / privacy breach (bridges data-adequacy + cyber-incident + cyber-compliance)",
        "fields": [
          ("incidentId", "string", True),
          ("terminologyVid", "string", True, None, "bridges registerTerminology"),
          ("incidentKind", "string", True, ["mapping_error","null_flavor_leak","unsupported_extension","phi_breach","conformance_fail","performance_slow","security_ssl"]),
          ("patientRecordsAffected", "integer", False),
          ("dataAdequacyVid", "string", False, None, "bridges open-data-adequacy"),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if incidentKind = \"phi_breach\" or incidentKind = \"security_ssl\" then \"critical\" else if patientRecordsAffected != null and patientRecordsAffected >= 10000 then \"severe\" else \"moderate\"", ["moderate","severe","critical"]),
      },
    ],
  },
  {
    "slug": "wada-antidoping",
    "app": "wadaAntidoping",
    "methods": [
      {
        "name": "recordTest",
        "desc": "WADA ADAMS test / analysis result (bridges esports-integrity + pharma-supply + livestock-antibiotics)",
        "fields": [
          ("testId", "string", True),
          ("athleteOrcid", "string", False),
          ("sport", "string", True),
          ("competitionType", "string", False, ["in_competition","out_of_competition","training","remote_sample"]),
          ("sampleType", "string", True, ["urine","blood","dried_blood_spot","saliva","hair"]),
          ("testAuthority", "string", False),
          ("wadaLab", "string", False),
          ("analyzedAt", "string", True),
          ("atf", "string", False, ["negative","adverse_finding","atypical_finding"]),
        ],
        "classify": None,
      },
      {
        "name": "flagProhibitedSubstance",
        "desc": "Adverse Analytical Finding + violation flow",
        "fields": [
          ("aafId", "string", True),
          ("testVid", "string", True, None, "bridges recordTest"),
          ("substanceClass", "string", True, ["S0_non_approved","S1_anabolic","S2_peptide","S3_beta2","S4_hormone_modulator","S5_diuretic","S6_stimulant","S7_narcotic","S8_cannabinoid","S9_glucocorticoid","P1_beta_blocker","M1_enhancement","M2_manipulation","M3_gene_doping"]),
          ("concentrationNgMl", "number", False),
          ("sanctionIssued", "string", False, ["warning","3_month_ban","6_month_ban","1_year_ban","2_year_ban","4_year_ban","lifetime"]),
          ("flaggedAt", "string", True),
        ],
        "classify": ("severityTier", "if sanctionIssued = \"lifetime\" or sanctionIssued = \"4_year_ban\" then \"severe\" else if sanctionIssued = \"2_year_ban\" or sanctionIssued = \"1_year_ban\" then \"major\" else \"minor\"", ["minor","major","severe"]),
      },
    ],
  },
  {
    "slug": "urban-air-mobility",
    "app": "urbanAirMobility",
    "methods": [
      {
        "name": "registerVertiport",
        "desc": "eVTOL vertiport / UAM stop (bridges aviation-safety + uas-traffic-management + urban-mobility)",
        "fields": [
          ("vertiportId", "string", True),
          ("operatorLei", "string", False),
          ("locationIso3", "string", True),
          ("locationLat", "number", True),
          ("locationLon", "number", True),
          ("padCount", "integer", False),
          ("chargerKwMax", "number", False),
          ("certificationBody", "string", False, ["faa","easa","jcab","caac","caa_uk","dgca"]),
          ("designCategory", "string", False, ["vfr_pilot","ifr_pilot","autonomous_simplified","autonomous_complex"]),
          ("commissionedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "logOperationalMetric",
        "desc": "eVTOL operational metric (bridges power-grid-interconnect + aviation-safety)",
        "fields": [
          ("metricId", "string", True),
          ("vertiportVid", "string", True, None, "bridges registerVertiport"),
          ("periodMonth", "string", True),
          ("flightsCount", "integer", False),
          ("paxCount", "integer", False),
          ("avgTurnMinutes", "number", False),
          ("incidentRatePerMille", "number", False),
          ("avgDistanceKm", "number", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("utilizationTier", "if flightsCount != null and flightsCount >= 3000 then \"high\" else if flightsCount != null and flightsCount >= 500 then \"moderate\" else \"low\"", ["low","moderate","high"]),
      },
    ],
  },
  {
    "slug": "press-finance-coercion",
    "app": "pressFinanceCoercion",
    "methods": [
      {
        "name": "recordSlappCase",
        "desc": "SLAPP / strategic lawsuit against public participation (bridges press-freedom + climate-litigation + ofac-sanctions)",
        "fields": [
          ("caseId", "string", True),
          ("plaintiffLei", "string", False),
          ("defendantCategory", "string", True, ["journalist","ngo","academic","environmentalist","activist","whistleblower"]),
          ("jurisdictionIso3", "string", True),
          ("claimBasis", "string", True, ["defamation","privacy","ip","tortious_interference","trade_secret","contract","regulatory"]),
          ("damageClaimedUsd", "number", False),
          ("antiSlappJurisdiction", "boolean", False),
          ("filedAt", "string", True),
        ],
        "classify": ("chillingTier", "if damageClaimedUsd != null and damageClaimedUsd >= 10000000 then \"severe\" else if damageClaimedUsd != null and damageClaimedUsd >= 1000000 then \"significant\" else \"notice\"", ["notice","significant","severe"]),
      },
      {
        "name": "flagBankingCoercion",
        "desc": "Debanking / financial-service denial of journalism (bridges mica-crypto + press-freedom + antitrust-dma)",
        "fields": [
          ("flagId", "string", True),
          ("targetLei", "string", False),
          ("targetCategory", "string", True, ["independent_publisher","journalist","ngo","opposition_campaign","satirical_site"]),
          ("jurisdictionIso3", "string", True),
          ("actionKind", "string", True, ["account_closure","payment_rail_block","ads_revenue_denial","kyc_refusal","sdn_false_positive","domain_delisting"]),
          ("serviceType", "string", False, ["bank","card_network","payment_processor","ad_network","domain_registrar","cdn"]),
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


for a in ACTORS:
    bd=REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    ld=REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bd.mkdir(parents=True,exist_ok=True); ld.mkdir(parents=True,exist_ok=True)
    for m in a["methods"]:
        (ld/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bd/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    print(gen_ddl(a))
