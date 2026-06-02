#!/usr/bin/env python3
"""Wave 32 bridges — soil carbon / ITU / CRS-FATCA / livestock-abx / UPOV."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "soil-carbon",
    "app": "soilCarbon",
    "methods": [
      {
        "name": "recordStock",
        "desc": "Soil organic carbon stock (FAO GSOC / 4p1000 — bridges agri-food-security + biodiversity-gbf + climate-carbon-market)",
        "fields": [
          ("stockId", "string", True),
          ("parcelId", "string", True),
          ("countryIso3", "string", True),
          ("landUse", "string", True, ["cropland","grassland","forest","wetland","settlement","bare"]),
          ("depthCm", "integer", False),
          ("socTonnesPerHa", "number", True),
          ("measurementMethod", "string", False, ["in_situ","nir","xrf","remote_sensing","model_estimate"]),
          ("measuredYear", "integer", True),
          ("recordedAt", "string", True),
        ],
        "classify": ("fertilityTier", "if socTonnesPerHa >= 100 then \"rich\" else if socTonnesPerHa >= 50 then \"moderate\" else if socTonnesPerHa >= 20 then \"depleted\" else \"severe\"", ["severe","depleted","moderate","rich"]),
      },
      {
        "name": "issueSoilCarbonCredit",
        "desc": "Soil carbon credit issuance (Verra VM0042 / Gold Standard / ACCU)",
        "fields": [
          ("creditId", "string", True),
          ("stockVid", "string", True, None, "bridges recordStock"),
          ("carbonCreditVid", "string", False, None, "bridges open-climate-carbon-market"),
          ("methodologyCode", "string", True, ["VM0042","VM0032","CDM_AR","GS_SOC","ACCU_SCM","MRV_CIF"]),
          ("deltaSocTonnesPerHa", "number", True),
          ("tonnesCo2e", "number", True),
          ("permanenceYears", "integer", False),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "itu-spectrum",
    "app": "ituSpectrum",
    "methods": [
      {
        "name": "recordAllocation",
        "desc": "ITU WRC radio spectrum allocation (bridges telecom-infra + space-traffic + aviation-safety + uas-traffic-management)",
        "fields": [
          ("allocationId", "string", True),
          ("bandName", "string", True, None, "e.g. C-band / Ku / Ka / mmWave / 6G"),
          ("freqStartMhz", "number", True),
          ("freqEndMhz", "number", True),
          ("serviceCategory", "string", True, ["mobile","fixed","broadcasting","broadcasting_satellite","radiolocation","earth_exploration","space_operation","amateur","radionavigation","aeronautical_radionavigation","maritime_radionavigation","iss"]),
          ("wrcDecision", "string", False, None, "WRC-23 / WRC-27 agenda item"),
          ("regionItu", "string", False, ["1","2","3","worldwide"]),
          ("decidedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInterference",
        "desc": "ITU-R RR interference complaint (bridges space-weather + satellite space-traffic)",
        "fields": [
          ("complaintId", "string", True),
          ("allocationVid", "string", True, None, "bridges recordAllocation"),
          ("victimLei", "string", False),
          ("sourceCountryIso3", "string", False),
          ("interferenceKind", "string", True, ["harmful","unauthorized_emission","spillover","jamming","deorbit_debris","satellite_overlap"]),
          ("mitigationStatus", "string", False, ["pending","mediated","resolved","escalated"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if interferenceKind = \"jamming\" or interferenceKind = \"harmful\" then \"critical\" else if interferenceKind = \"unauthorized_emission\" then \"severe\" else \"routine\"", ["routine","severe","critical"]),
      },
    ],
  },
  {
    "slug": "tax-transparency",
    "app": "taxTransparency",
    "methods": [
      {
        "name": "recordAeoiExchange",
        "desc": "CRS / FATCA / CARF AEOI exchange (bridges global-tax + ofac-sanctions + mica-crypto)",
        "fields": [
          ("exchangeId", "string", True),
          ("senderIso3", "string", True),
          ("recipientIso3", "string", True),
          ("standard", "string", True, ["crs","fatca","carf","dac6","dac8","beps_13"]),
          ("reportingYear", "integer", True),
          ("accountsCount", "integer", False),
          ("balancesTotalUsd", "number", False),
          ("exchangedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDisclosureGap",
        "desc": "Non-compliance / disclosure gap finding (GFTAx / Common Transmission System)",
        "fields": [
          ("gapId", "string", True),
          ("exchangeVid", "string", False, None, "bridges recordAeoiExchange"),
          ("jurisdictionIso3", "string", True),
          ("gapKind", "string", True, ["late_filing","missing_jurisdictions","data_quality","mandatory_disclosure_rules","beneficial_owner"]),
          ("globalForumRating", "string", False, ["compliant","largely_compliant","partially_compliant","non_compliant"]),
          ("flaggedAt", "string", True),
        ],
        "classify": ("riskTier", "if globalForumRating = \"non_compliant\" then \"severe\" else if globalForumRating = \"partially_compliant\" then \"elevated\" else \"moderate\"", ["moderate","elevated","severe"]),
      },
    ],
  },
  {
    "slug": "livestock-antibiotics",
    "app": "livestockAntibiotics",
    "methods": [
      {
        "name": "reportVeterinaryUse",
        "desc": "WOAH / EU ESVAC livestock antibiotic use (bridges amr-surveillance + antimicrobial-stewardship + pharma-supply + agri-food-security)",
        "fields": [
          ("reportId", "string", True),
          ("countryIso3", "string", True),
          ("species", "string", True, ["cattle","swine","poultry","sheep","goat","aquaculture","equine","rabbit"]),
          ("antibioticClass", "string", True, ["penicillins","tetracyclines","macrolides","sulfonamides","fluoroquinolones","polymyxins","cephalosporins","aminoglycosides","amphenicols","pleuromutilins"]),
          ("pcuBiomassKg", "number", False, None, "population correction unit"),
          ("mgPerPcu", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("stewardshipTier", "if mgPerPcu != null and mgPerPcu < 50 then \"low\" else if mgPerPcu != null and mgPerPcu < 150 then \"moderate\" else \"high\"", ["low","moderate","high"]),
      },
      {
        "name": "flagHpciUse",
        "desc": "Highest Priority Critically Important use (WHO CIA list — bridges amr-surveillance + pandemic-preparedness)",
        "fields": [
          ("flagId", "string", True),
          ("reportVid", "string", True, None, "bridges reportVeterinaryUse"),
          ("hpciaClassName", "string", True),
          ("usagePurpose", "string", True, ["therapeutic","metaphylaxis","prophylaxis","growth_promotion"]),
          ("banOrRestricted", "string", False, ["banned","restricted","permitted_limited","permitted"]),
          ("flaggedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "upov-plant-breeders",
    "app": "upovPlantBreeders",
    "methods": [
      {
        "name": "grantPbr",
        "desc": "UPOV 1991 Plant Breeders Right (bridges agri-food-security + biodiversity-gbf + indigenous-rights)",
        "fields": [
          ("grantId", "string", True),
          ("varietyDenomination", "string", True),
          ("breederLei", "string", False),
          ("species", "string", True),
          ("jurisdictionIso3", "string", True),
          ("upovFiliation", "string", False, ["upov1978","upov1991"]),
          ("farmSavedSeedAllowed", "boolean", False),
          ("durationYears", "integer", False),
          ("grantedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagIpIndigenousConflict",
        "desc": "Conflict with ITPGRFA / Nagoya / indigenous FPIC (bridges indigenous-rights + biodiversity-gbf + bbnj-highseas)",
        "fields": [
          ("conflictId", "string", True),
          ("grantVid", "string", True, None, "bridges grantPbr"),
          ("territoryVid", "string", False, None, "bridges open-indigenous-rights"),
          ("issueType", "string", True, ["biopiracy","lack_fpic","absent_benefit_sharing","unauthorized_transfer","traditional_knowledge_appropriation"]),
          ("nagoyaComplaintStatus", "string", False, ["informal","formal","mediation","resolved"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if issueType = \"biopiracy\" or issueType = \"traditional_knowledge_appropriation\" then \"severe\" else if issueType = \"lack_fpic\" or issueType = \"unauthorized_transfer\" then \"strong\" else \"moderate\"", ["moderate","strong","severe"]),
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
