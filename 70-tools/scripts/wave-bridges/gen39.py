#!/usr/bin/env python3
"""Wave 39 bridges — precision med / industrial safety / fair pricing / Kigali / repair."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "precision-medicine",
    "app": "precisionMedicine",
    "methods": [
      {
        "name": "registerDataTrust",
        "desc": "GA4GH / H3Africa / AoU precision-medicine data trust (bridges fhir-health-data + indigenous-rights + data-adequacy + crc-children-digital)",
        "fields": [
          ("trustId", "string", True),
          ("stewardLei", "string", False),
          ("countryIso3", "string", True),
          ("participantCount", "integer", False),
          ("cohortDescription", "string", False),
          ("consentModel", "string", True, ["broad","tiered","dynamic","meta_consent","open_consent","indigenous_collective"]),
          ("passportCompliant", "boolean", False, None, "GA4GH passport"),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSecondaryUse",
        "desc": "Secondary-use request / denial / misuse (bridges data-adequacy + itpgrfa-seeds + cyber-compliance)",
        "fields": [
          ("requestId", "string", True),
          ("trustVid", "string", True, None, "bridges registerDataTrust"),
          ("requesterLei", "string", False),
          ("intendedUse", "string", True, ["research","commercial","insurance","law_enforcement","population_screening","ancestry","ml_training"]),
          ("decision", "string", True, ["approved","approved_with_conditions","denied","withdrawn","under_review"]),
          ("reviewBody", "string", False, ["irb","data_access_committee","ethics_board","indigenous_council","regulator"]),
          ("decidedAt", "string", True),
        ],
        "classify": ("sensitivityTier", "if intendedUse = \"insurance\" or intendedUse = \"law_enforcement\" or intendedUse = \"ml_training\" then \"high\" else if intendedUse = \"commercial\" then \"elevated\" else \"standard\"", ["standard","elevated","high"]),
      },
    ],
  },
  {
    "slug": "industrial-safety",
    "app": "industrialSafety",
    "methods": [
      {
        "name": "recordSafetyAssessment",
        "desc": "ISO 45001 + ILO OSH + Seveso III / IV assessment (bridges chemicals-management + forced-labor + labour-mobility + disaster-response)",
        "fields": [
          ("assessmentId", "string", True),
          ("facilityLei", "string", False),
          ("locationIso3", "string", True),
          ("scheme", "string", True, ["iso_45001","ilo_iso_lg_189","seveso_iii","seveso_iv","ohsas_18001","cs_code","osha_vpp"]),
          ("hazardTier", "string", False, ["lower","upper","none"], "Seveso hazard tier"),
          ("surveillanceFindings", "integer", False),
          ("conductedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMajorAccident",
        "desc": "Seveso major accident / ILO occupational incident (bridges chemicals-management + disaster-response + ocha-funding)",
        "fields": [
          ("accidentId", "string", True),
          ("assessmentVid", "string", False, None, "bridges recordSafetyAssessment"),
          ("accidentKind", "string", True, ["chemical_release","explosion","fire","radioactive","dust","biological","fall_from_height","crush","confined_space"]),
          ("fatalities", "integer", False),
          ("injuries", "integer", False),
          ("tonnesReleased", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if fatalities != null and fatalities >= 5 then \"catastrophic\" else if fatalities != null and fatalities >= 1 then \"fatal\" else if injuries != null and injuries >= 10 then \"major\" else \"minor\"", ["minor","major","fatal","catastrophic"]),
      },
    ],
  },
  {
    "slug": "fair-pricing",
    "app": "fairPricing",
    "methods": [
      {
        "name": "recordPriceMonitor",
        "desc": "Competition authority price monitor (CMA / SAMR / CADE / ACCC — bridges antitrust-dma + agri-food-security + pharma-supply + icpen-consumer)",
        "fields": [
          ("monitorId", "string", True),
          ("jurisdictionIso3", "string", True),
          ("authority", "string", True, ["cma","samr","cade","accc","ftc","dg_comp","jftc","kftc"]),
          ("sector", "string", True, ["grocery","fuel","electricity","pharma","telecoms","airlines","banking","digital_ads"]),
          ("marginPctYoy", "number", False),
          ("priceChangePctYoy", "number", False),
          ("inputCostChangePctYoy", "number", False),
          ("windowMonth", "string", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("marginTier", "if marginPctYoy != null and marginPctYoy >= 50 then \"excess\" else if marginPctYoy != null and marginPctYoy >= 20 then \"elevated\" else \"benchmark\"", ["benchmark","elevated","excess"]),
      },
      {
        "name": "flagCartelConduct",
        "desc": "Cartel / RPM / hub-and-spoke / algorithmic collusion (bridges antitrust-dma + misinformation-observatory + blockchain-mev)",
        "fields": [
          ("conductId", "string", True),
          ("monitorVid", "string", True, None, "bridges recordPriceMonitor"),
          ("firmsInvolved", "integer", False),
          ("practiceKind", "string", True, ["price_fixing","bid_rigging","market_allocation","rpm","hub_spoke","algorithmic","tying","refusal_to_deal"]),
          ("fineEur", "number", False),
          ("leniencyAppliedBy", "integer", False),
          ("detectedAt", "string", True),
        ],
        "classify": ("severityTier", "if practiceKind = \"price_fixing\" or practiceKind = \"bid_rigging\" or practiceKind = \"market_allocation\" then \"hardcore\" else if practiceKind = \"rpm\" or practiceKind = \"hub_spoke\" then \"vertical\" else \"other\"", ["other","vertical","hardcore"]),
      },
    ],
  },
  {
    "slug": "kigali-hfc",
    "app": "kigaliHfc",
    "methods": [
      {
        "name": "recordHfcPhasedown",
        "desc": "Kigali HFC phasedown schedule (Montreal Protocol — bridges climate-carbon-market + chemicals-management + hydrogen-economy)",
        "fields": [
          ("reportId", "string", True),
          ("partyIso3", "string", True),
          ("groupA1OrA2OrA3", "string", True, ["A1","A2","A3","developed"]),
          ("baselineCo2eTonnes", "number", False),
          ("currentCo2eTonnes", "number", True),
          ("freezeYear", "integer", False),
          ("phasedownStepYear", "integer", True),
          ("reductionFromBaselinePct", "number", False),
          ("reportingYear", "integer", True),
          ("submittedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagIllegalTrade",
        "desc": "Illegal HFC / ODS trade (bridges customs-clearance + chemicals-management + ofac-sanctions)",
        "fields": [
          ("tradeId", "string", True),
          ("originIso3", "string", True),
          ("destinationIso3", "string", True),
          ("chemicalCode", "string", True, None, "HFC-134a / R-410A / HCFC-22 / etc"),
          ("tonnesSeized", "number", False),
          ("seizureAuthority", "string", False),
          ("detectedAt", "string", True),
        ],
        "classify": ("severityTier", "if tonnesSeized != null and tonnesSeized >= 10 then \"major\" else if tonnesSeized != null and tonnesSeized >= 1 then \"moderate\" else \"minor\"", ["minor","moderate","major"]),
      },
    ],
  },
  {
    "slug": "right-to-repair",
    "app": "rightToRepair",
    "methods": [
      {
        "name": "recordRegulation",
        "desc": "Right to Repair law / standard (EU ESPR / US 50-state / IN / JP — bridges textile-circularity + ev-charging-ocpp + antitrust-dma + oss-vuln)",
        "fields": [
          ("regulationId", "string", True),
          ("jurisdictionIso3", "string", True),
          ("scopeCategories", "string", True, None, "comma: smartphones,tablets,washers,dryers,dishwashers,televisions,monitors,vacuum,ev_bat,industrial,agricultural"),
          ("mandatesPartsAvailability", "boolean", False),
          ("mandatesSoftwareUpdates", "boolean", False),
          ("mandatesDocumentation", "boolean", False),
          ("effectiveFrom", "string", True),
        ],
        "classify": ("strengthTier", "if mandatesPartsAvailability = true and mandatesSoftwareUpdates = true and mandatesDocumentation = true then \"comprehensive\" else if mandatesPartsAvailability = true then \"moderate\" else \"narrow\"", ["narrow","moderate","comprehensive"]),
      },
      {
        "name": "flagRepairabilityIndex",
        "desc": "Repairability Index filing (FR AGEC / ESPR DPP — bridges textile-circularity + battery-passport + antitrust-dma)",
        "fields": [
          ("indexId", "string", True),
          ("productLei", "string", False),
          ("productCategory", "string", True),
          ("regulationVid", "string", False, None, "bridges recordRegulation"),
          ("indexValue", "number", True, None, "0-10 repairability index"),
          ("disassemblyScore", "number", False),
          ("partsAvailabilityScore", "number", False),
          ("priceOfPartsPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("repairabilityTier", "if indexValue >= 8 then \"high\" else if indexValue >= 6 then \"moderate\" else if indexValue >= 4 then \"low\" else \"very_low\"", ["very_low","low","moderate","high"]),
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
