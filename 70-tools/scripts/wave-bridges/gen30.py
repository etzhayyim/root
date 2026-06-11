#!/usr/bin/env python3
"""Wave 30 bridges — OSS CVE / urban heat / MiCA / gender pay / CITES."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "oss-vuln",
    "app": "ossVuln",
    "methods": [
      {
        "name": "registerAdvisory",
        "desc": "OSS advisory / CVE (MITRE NVD + GHSA + BSI + JVN — bridges cyber-incident + cyber-resilience-stress + ai-supply-chain)",
        "fields": [
          ("advisoryId", "string", True, None, "CVE / GHSA / BSI / JVN ID"),
          ("scheme", "string", True, ["cve","ghsa","bsi","jvn","rustsec","osv","pysec"]),
          ("cvss3Score", "number", False),
          ("cvss4Score", "number", False),
          ("epssPct", "number", False, None, "EPSS exploitation probability 0-1"),
          ("cweId", "string", False),
          ("affectedEcosystem", "string", True, ["npm","pypi","maven","nuget","rubygems","go","crates","composer","swift","pub","hex","cran","cpan","github","linux_kernel","firmware"]),
          ("affectedPackage", "string", True),
          ("versionRanges", "string", False),
          ("kevTagged", "boolean", False, None, "CISA KEV catalog"),
          ("publishedAt", "string", True),
        ],
        "classify": ("riskTier", "if kevTagged = true or (cvss4Score != null and cvss4Score >= 9) or (cvss3Score != null and cvss3Score >= 9) then \"critical\" else if (cvss4Score != null and cvss4Score >= 7) or (cvss3Score != null and cvss3Score >= 7) then \"high\" else if (cvss4Score != null and cvss4Score >= 4) or (cvss3Score != null and cvss3Score >= 4) then \"medium\" else \"low\"", ["low","medium","high","critical"]),
      },
      {
        "name": "recordSbomMatch",
        "desc": "SBOM ↔ advisory match (bridges cyber-compliance + ai-supply-chain + telecom-infra)",
        "fields": [
          ("matchId", "string", True),
          ("advisoryVid", "string", True, None, "bridges registerAdvisory"),
          ("operatorLei", "string", False),
          ("productName", "string", True),
          ("sbomFormat", "string", False, ["spdx","cyclonedx","swid"]),
          ("componentCount", "integer", False),
          ("affectedComponents", "integer", True),
          ("remediationStatus", "string", False, ["patched","mitigated","accepted_risk","unpatched","out_of_scope"]),
          ("matchedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "urban-heat",
    "app": "urbanHeat",
    "methods": [
      {
        "name": "recordUhiMetric",
        "desc": "Urban Heat Island metric (WMO UHI study + Copernicus C3S + LST — bridges coastal-slr + air-quality + disaster-response)",
        "fields": [
          ("metricId", "string", True),
          ("cityUnlocode", "string", True),
          ("measurementType", "string", True, ["lst_day","lst_night","air_temp","wetbulb","heatindex"]),
          ("uhiDeltaC", "number", True, None, "urban-rural delta"),
          ("meanTempC", "number", False),
          ("populationExposed", "integer", False),
          ("peakDay", "string", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("exposureTier", "if uhiDeltaC >= 5 then \"severe\" else if uhiDeltaC >= 3 then \"significant\" else if uhiDeltaC >= 1 then \"moderate\" else \"mild\"", ["mild","moderate","significant","severe"]),
      },
      {
        "name": "declareCoolingAction",
        "desc": "Urban cooling action plan (green infra / white roof / shade — bridges climate-adaptation-finance + cofog)",
        "fields": [
          ("planId", "string", True),
          ("metricVid", "string", False, None, "bridges recordUhiMetric"),
          ("actionType", "string", True, ["green_roof","white_roof","urban_forest","shade_structure","cool_pavement","mist_station","cooling_center"]),
          ("coverageHectares", "number", False),
          ("financeProjectVid", "string", False, None, "bridges open-climate-adaptation-finance"),
          ("budgetUsd", "number", False),
          ("effectiveFrom", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "mica-crypto",
    "app": "micaCrypto",
    "methods": [
      {
        "name": "registerCasp",
        "desc": "MiCA CASP authorization / UK FSMA Part 5A / SG DPT / JP FSA CASP (bridges ofac-sanctions + blockchain-mev + antitrust-dma)",
        "fields": [
          ("registrationId", "string", True),
          ("caspLei", "string", True),
          ("regime", "string", True, ["eu_mica","uk_fsma","sg_dpt","jp_fsa","us_msb","kr_kosa","ca_vcp"]),
          ("servicesAuthorized", "string", True, None, "comma: custody,operation,exchange,execution,placement,reception,advice,portfolio_mgmt"),
          ("tokenCategories", "string", False, None, "comma: emt,art,crypto_asset"),
          ("amlLevel", "string", False, ["enhanced","standard","sanctions_sensitive"]),
          ("authorizedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagTokenIssuance",
        "desc": "ART/EMT issuance whitepaper + reserve event (bridges sovereign-debt + misinformation-observatory)",
        "fields": [
          ("issuanceId", "string", True),
          ("caspVid", "string", True, None, "bridges registerCasp"),
          ("tokenKind", "string", True, ["emt_fiat","art","utility","nft","security","governance"]),
          ("underlyingCurrency", "string", False, None, "ISO 4217 if EMT"),
          ("reserveRatio", "number", False),
          ("reserveCustodyLei", "string", False),
          ("capMcapUsd", "number", False),
          ("issuedAt", "string", True),
        ],
        "classify": ("riskTier", "if tokenKind = \"art\" or (tokenKind = \"emt_fiat\" and reserveRatio != null and reserveRatio < 1) then \"systemic\" else if reserveRatio != null and reserveRatio < 0.95 then \"undercollateralized\" else \"standard\"", ["standard","undercollateralized","systemic"]),
      },
    ],
  },
  {
    "slug": "gender-pay-gap",
    "app": "genderPayGap",
    "methods": [
      {
        "name": "reportEmployerMetric",
        "desc": "Pay transparency metric (EU Pay Transparency Directive / UK GPG / DE EntgTranspG / AU WGEA — bridges esg-risk-rating + forced-labor)",
        "fields": [
          ("reportId", "string", True),
          ("employerLei", "string", False),
          ("regime", "string", True, ["eu_ptd","uk_gpg","de_entgttranspg","au_wgea","fr_regulation","is_equal_pay"]),
          ("reportingYear", "integer", True),
          ("hourlyMeanGapPct", "number", False),
          ("hourlyMedianGapPct", "number", False),
          ("bonusMeanGapPct", "number", False),
          ("womenUpperQuartilePct", "number", False),
          ("womenLowerQuartilePct", "number", False),
          ("employeeCount", "integer", False),
          ("submittedAt", "string", True),
        ],
        "classify": ("gapTier", "if hourlyMeanGapPct != null and hourlyMeanGapPct >= 20 then \"severe\" else if hourlyMeanGapPct != null and hourlyMeanGapPct >= 10 then \"significant\" else if hourlyMeanGapPct != null and hourlyMeanGapPct >= 5 then \"moderate\" else \"parity\"", ["parity","moderate","significant","severe"]),
      },
      {
        "name": "recordJointAssessment",
        "desc": "Joint pay assessment (EU PTD Art 10) / remediation plan",
        "fields": [
          ("assessmentId", "string", True),
          ("reportVid", "string", True, None, "bridges reportEmployerMetric"),
          ("unjustifiedGapFound", "boolean", True),
          ("remediationMeasures", "string", False),
          ("timelineMonths", "integer", False),
          ("conductedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cites-wildlife",
    "app": "citesWildlife",
    "methods": [
      {
        "name": "listSpecies",
        "desc": "CITES appendix listing (bridges biodiversity-gbf + fisheries-iuu + asfis)",
        "fields": [
          ("listingId", "string", True),
          ("scientificName", "string", True),
          ("asfisCode", "string", False),
          ("appendix", "string", True, ["I","II","III"]),
          ("sourceCountryIso3", "string", False),
          ("annotationKey", "string", False),
          ("effectiveFrom", "string", True),
        ],
        "classify": ("endangermentTier", "if appendix = \"I\" then \"most_endangered\" else if appendix = \"II\" then \"regulated\" else \"cooperative\"", ["cooperative","regulated","most_endangered"]),
      },
      {
        "name": "recordSeizure",
        "desc": "Wildlife seizure record (WCO + Interpol Mercator + UNODC — bridges customs-clearance + maritime-piracy + ofac-sanctions)",
        "fields": [
          ("seizureId", "string", True),
          ("listingVid", "string", False, None, "bridges listSpecies"),
          ("portVid", "string", False, None, "bridges open-ports"),
          ("customsDeclarationVid", "string", False, None, "bridges open-customs-clearance"),
          ("quantityUnits", "integer", False),
          ("weightKg", "number", False),
          ("estimatedValueUsd", "number", False),
          ("partsRoute", "string", False, None, "comma: origin,transit,destination iso3"),
          ("seizedAt", "string", True),
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
