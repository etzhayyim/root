#!/usr/bin/env python3
"""Wave 17 — regional regulators + trade policy bridges (90 → 95 projects)."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "eu-cbam",
    "app": "euCbam",
    "methods": [
      {
        "name": "reportEmbedded",
        "desc": "EU CBAM embedded emissions report (Q1 2026→ — bridges climate-carbon-market + customs-clearance + critical-minerals)",
        "fields": [
          ("reportId", "string", True),
          ("cnCode", "string", True, None, "EU Combined Nomenclature (HS-linked)"),
          ("importerLei", "string", False),
          ("customsDeclarationVid", "string", False, None, "bridges open-customs-clearance"),
          ("criticalMineralVid", "string", False, None, "bridges open-critical-minerals"),
          ("quantityTonnes", "number", True),
          ("directEmissionsTco2e", "number", True),
          ("indirectEmissionsTco2e", "number", False),
          ("certificatePriceEur", "number", False),
          ("reportingQuarter", "string", True, None, "YYYY-QN"),
          ("submittedAt", "string", True),
        ],
        "classify": ("intensityTier", "if directEmissionsTco2e / quantityTonnes >= 3 then \"high\" else if directEmissionsTco2e / quantityTonnes >= 1 then \"moderate\" else \"low\"", ["low","moderate","high"]),
      },
      {
        "name": "surrenderCbamCertificate",
        "desc": "Surrender CBAM certificate against import declaration",
        "fields": [
          ("surrenderId", "string", True),
          ("reportVid", "string", True, None, "bridges reportEmbedded"),
          ("carbonCreditVid", "string", False, None, "bridges open-climate-carbon-market"),
          ("certificatesSurrendered", "integer", True),
          ("eurPaid", "number", True),
          ("surrenderedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "mofcom-export-control",
    "app": "mofcomExportControl",
    "methods": [
      {
        "name": "publishControl",
        "desc": "China MOFCOM/MIIT export control listing (bridges critical-minerals + ai-supply-chain)",
        "fields": [
          ("controlId", "string", True),
          ("hsCode", "string", True),
          ("materialClassificationVid", "string", False, None, "bridges open-critical-minerals"),
          ("licenseType", "string", True, ["general","targeted","prohibited","dual_use","technology"]),
          ("targetCountries", "string", False),
          ("rationale", "string", True, ["national_security","retaliatory","technology_transfer","environmental"]),
          ("publishedAt", "string", True),
          ("effectiveFrom", "string", True),
        ],
        "classify": ("severityTier", "if licenseType = \"prohibited\" then \"critical\" else if licenseType = \"targeted\" or licenseType = \"dual_use\" then \"severe\" else \"moderate\"", ["moderate","severe","critical"]),
      },
      {
        "name": "logLicenseApplication",
        "desc": "Applicant log against a MOFCOM control",
        "fields": [
          ("applicationId", "string", True),
          ("controlVid", "string", True, None, "bridges publishControl"),
          ("applicantLei", "string", False),
          ("destinationIso3", "string", True),
          ("volumeRequested", "number", False),
          ("outcome", "string", False, ["granted","denied","pending","withdrawn"]),
          ("appliedAt", "string", True),
          ("decidedAt", "string", False),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "ustr-section-301",
    "app": "ustrSection301",
    "methods": [
      {
        "name": "imposeTariff",
        "desc": "USTR §301 tariff imposition (bridges customs-clearance + commodity-trade + ai-supply-chain)",
        "fields": [
          ("actionId", "string", True),
          ("htsCode", "string", True, None, "Harmonized Tariff Schedule US"),
          ("listName", "string", True, ["list_1","list_2","list_3","list_4a","list_4b","IRA","CHIPS"]),
          ("ratePct", "number", True),
          ("rationale", "string", True, ["ip_theft","forced_tech","cyber","subsidies","overcapacity","labor_violations"]),
          ("effectiveFrom", "string", True),
          ("expiresAt", "string", False),
        ],
        "classify": ("impactTier", "if ratePct >= 50 then \"prohibitive\" else if ratePct >= 25 then \"high\" else if ratePct >= 10 then \"moderate\" else \"nuisance\"", ["nuisance","moderate","high","prohibitive"]),
      },
      {
        "name": "grantExclusion",
        "desc": "Section 301 exclusion grant for specific HTS subheadings",
        "fields": [
          ("exclusionId", "string", True),
          ("actionVid", "string", True, None, "bridges imposeTariff"),
          ("htsSubheading", "string", True),
          ("requesterLei", "string", False),
          ("customsDeclarationVid", "string", False, None, "bridges open-customs-clearance"),
          ("grantedAt", "string", True),
          ("expiresAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "wto-dispute",
    "app": "wtoDispute",
    "methods": [
      {
        "name": "fileDispute",
        "desc": "WTO DSB dispute filing (bridges ustr-301 + mofcom + eu-cbam + lei)",
        "fields": [
          ("disputeId", "string", True, None, "DS number"),
          ("complainantIso3", "string", True),
          ("respondentIso3", "string", True),
          ("subjectAgreement", "string", True, ["gatt","tbt","sps","scm","trips","agreement_on_agriculture","gats","safeguards"]),
          ("relatedUstr301Vid", "string", False, None, "bridges open-ustr-section-301"),
          ("relatedMofcomVid", "string", False, None, "bridges open-mofcom-export-control"),
          ("relatedCbamVid", "string", False, None, "bridges open-eu-cbam"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordPanelRuling",
        "desc": "DSB panel or AB ruling outcome",
        "fields": [
          ("rulingId", "string", True),
          ("disputeVid", "string", True, None, "bridges fileDispute"),
          ("rulingBody", "string", True, ["panel","appellate_body","arbitration","compliance_panel"]),
          ("outcome", "string", True, ["violation","no_violation","non_violation","mutually_agreed","withdrawn"]),
          ("ruledAt", "string", True),
        ],
        "classify": ("consequenceTier", "if outcome = \"violation\" and rulingBody = \"appellate_body\" then \"binding\" else if outcome = \"violation\" then \"recommending\" else \"neutral\"", ["neutral","recommending","binding"]),
      },
    ],
  },
  {
    "slug": "ofac-sanctions-sdn",
    "app": "ofacSanctionsSdn",
    "methods": [
      {
        "name": "listSdn",
        "desc": "OFAC SDN / Non-SDN list addition (bridges sanctions + lei + forced-labor + swift)",
        "fields": [
          ("sdnId", "string", True),
          ("entityLei", "string", False),
          ("sdnProgram", "string", True, ["SDGT","IRAN","NKOREA","RUSSIA","UKRAINE","VENEZUELA","CUBA","MYANMAR","SYRIA","CYBER2","NARCOTICS","MAGNITSKY","UFLPA"]),
          ("listType", "string", True, ["SDN","NS","SSI","FSE"]),
          ("forcedLaborFlagVid", "string", False, None, "bridges open-forced-labor"),
          ("listedAt", "string", True),
          ("delistedAt", "string", False),
        ],
        "classify": ("blockingTier", "if listType = \"SDN\" then \"full_block\" else if listType = \"SSI\" then \"sectoral\" else \"limited\"", ["limited","sectoral","full_block"]),
      },
      {
        "name": "flagTransaction",
        "desc": "SWIFT / banking transaction flagged against SDN list",
        "fields": [
          ("flagId", "string", True),
          ("sdnVid", "string", True, None, "bridges listSdn"),
          ("swiftUetr", "string", False, None, "bridges open-swift"),
          ("bankingAccountVid", "string", False, None, "bridges open-banking"),
          ("amountUsd", "number", False),
          ("action", "string", True, ["blocked","rejected","licensed","pending"]),
          ("flaggedAt", "string", True),
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
