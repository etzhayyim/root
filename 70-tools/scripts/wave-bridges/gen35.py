#!/usr/bin/env python3
"""Wave 35 bridges — DPG / vaccine equity / forestry MRV / ITPGRFA / ICPEN."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "digital-public-goods",
    "app": "digitalPublicGoods",
    "methods": [
      {
        "name": "certifyStandard",
        "desc": "DPGA / GovStack / DIAL DPG certification (bridges digital-accessibility + ai-governance + digital-identity)",
        "fields": [
          ("certificationId", "string", True),
          ("productName", "string", True),
          ("stewardLei", "string", False),
          ("dpgIndicator", "string", True, None, "comma: relevance,open_license,clear_ownership,platform_independence,documentation,non_pii,privacy_laws,standards_best_practices,do_no_harm"),
          ("category", "string", True, ["open_software","open_data","open_ai_model","open_content","open_standard"]),
          ("licenseSpdx", "string", False),
          ("sdgAlignment", "string", False, None, "comma: SDG1..SDG17"),
          ("certifiedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordCountryImplementation",
        "desc": "Country-level DPG / GovStack implementation (bridges sdg-reporting + digital-identity + universal-health-coverage)",
        "fields": [
          ("implementationId", "string", True),
          ("certificationVid", "string", True, None, "bridges certifyStandard"),
          ("countryIso3", "string", True),
          ("sectors", "string", True, None, "comma: identity,payments,data_exchange,health,education,agriculture,justice"),
          ("deploymentPhase", "string", True, ["scoping","pilot","scaled","national","cross_border"]),
          ("beneficiariesReached", "integer", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("maturityTier", "if deploymentPhase = \"cross_border\" or deploymentPhase = \"national\" then \"systemic\" else if deploymentPhase = \"scaled\" then \"scaling\" else \"exploratory\"", ["exploratory","scaling","systemic"]),
      },
    ],
  },
  {
    "slug": "vaccine-equity",
    "app": "vaccineEquity",
    "methods": [
      {
        "name": "recordAllocation",
        "desc": "COVAX / Gavi / PAHO RF vaccine allocation (bridges pandemic-preparedness + pharma-supply + cofog + ocha-funding)",
        "fields": [
          ("allocationId", "string", True),
          ("mechanism", "string", True, ["covax_amc","gavi","paho_rf","unicef_sd","bilateral","prequalification"]),
          ("productName", "string", True, None, "vaccine product / antigen"),
          ("atcCode", "string", False, None, "bridges open-atc"),
          ("destinationIso3", "string", True),
          ("dosesAllocated", "integer", True),
          ("platform", "string", False, ["mrna","viral_vector","protein_subunit","inactivated","dna","conjugate","polysaccharide"]),
          ("priceUsdDose", "number", False),
          ("deliveredDoses", "integer", False),
          ("allocatedAt", "string", True),
        ],
        "classify": ("equityTier", "if priceUsdDose != null and priceUsdDose <= 0.5 then \"amc_equitable\" else if priceUsdDose != null and priceUsdDose <= 3 then \"subsidized\" else \"market\"", ["market","subsidized","amc_equitable"]),
      },
      {
        "name": "flagCoverageGap",
        "desc": "WHO/UNICEF Immunization Coverage Estimate gap (bridges amr-surveillance + pandemic-preparedness)",
        "fields": [
          ("gapId", "string", True),
          ("countryIso3", "string", True),
          ("antigen", "string", True),
          ("coveragePct", "number", True),
          ("targetPct", "number", False),
          ("zeroDoseChildren", "integer", False),
          ("reportingYear", "integer", True),
          ("flaggedAt", "string", True),
        ],
        "classify": ("coverageTier", "if coveragePct < 50 then \"critical\" else if coveragePct < 75 then \"elevated\" else if coveragePct < 90 then \"approaching\" else \"on_target\"", ["on_target","approaching","elevated","critical"]),
      },
    ],
  },
  {
    "slug": "forestry-mrv",
    "app": "forestryMrv",
    "methods": [
      {
        "name": "recordCoverChange",
        "desc": "Global Forest Watch / FAO FRA / CTrees forest-cover change (bridges climate-carbon-market + biodiversity-gbf + indigenous-rights + soil-carbon)",
        "fields": [
          ("measurementId", "string", True),
          ("countryIso3", "string", True),
          ("adminRegion", "string", False),
          ("hectaresLost", "number", False),
          ("hectaresGained", "number", False),
          ("primaryForestHaLost", "number", False),
          ("driverDominant", "string", False, ["commodity_permanent","commodity_shifting","forestry","wildfire","urbanization","other"]),
          ("measurementYear", "integer", True),
          ("dataSource", "string", False, ["hansen","jaxa_alos","sentinel","planet","modis_vcf","ctrees_jurisdictional"]),
          ("recordedAt", "string", True),
        ],
        "classify": ("degradationTier", "if primaryForestHaLost != null and primaryForestHaLost >= 100000 then \"severe\" else if hectaresLost != null and hectaresLost >= 10000 then \"significant\" else \"moderate\"", ["moderate","significant","severe"]),
      },
      {
        "name": "issueRedDPlusCredit",
        "desc": "REDD+ / JREDD / ART TREES jurisdictional credit (bridges climate-carbon-market + indigenous-rights + sovereign-debt)",
        "fields": [
          ("creditId", "string", True),
          ("measurementVid", "string", False, None, "bridges recordCoverChange"),
          ("jurisdictionIso3", "string", True),
          ("methodology", "string", True, ["art_trees","jreddplus","vm0048","vm0007","vcs_redd","verra_redd"]),
          ("tonnesCo2e", "number", True),
          ("indigenousBenefitSharingPct", "number", False),
          ("vintage", "string", True),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "itpgrfa-seeds",
    "app": "itpgrfaSeeds",
    "methods": [
      {
        "name": "recordAccession",
        "desc": "ITPGRFA / CGIAR / Svalbard accession (bridges biodiversity-gbf + upov-plant-breeders + bbnj-highseas)",
        "fields": [
          ("accessionId", "string", True),
          ("genebankLei", "string", False),
          ("genusSpecies", "string", True),
          ("originIso3", "string", False),
          ("collectionMethod", "string", False, ["farmer_variety","wild_collected","breeders_line","landrace","mutant","hybrid"]),
          ("storageTier", "string", True, ["base","active","working","field"]),
          ("underMlsAnnexI", "boolean", False, None, "ITPGRFA multilateral system Annex I"),
          ("collectedAt", "string", False),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "logSmtaTransfer",
        "desc": "Standard Material Transfer Agreement (benefit-sharing monetary + non-monetary)",
        "fields": [
          ("transferId", "string", True),
          ("accessionVid", "string", True, None, "bridges recordAccession"),
          ("providerLei", "string", False),
          ("recipientLei", "string", False),
          ("recipientCountryIso3", "string", True),
          ("intendedUse", "string", True, ["research","breeding","training","commercial_variety"]),
          ("benefitSharingCommitmentPct", "number", False),
          ("transferredAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "icpen-consumer",
    "app": "icpenConsumer",
    "methods": [
      {
        "name": "launchSweep",
        "desc": "ICPEN consumer protection sweep (bridges antitrust-dma + misinformation-observatory + ai-governance + data-broker-registry)",
        "fields": [
          ("sweepId", "string", True),
          ("leadAuthority", "string", True),
          ("participatingJurisdictions", "string", True, None, "comma ISO3"),
          ("theme", "string", True, ["dark_patterns","greenwashing","health_claims","fake_reviews","subscription_traps","influencer_disclosure","ai_chatbots","kids_apps","crypto_ads","sustainability_claims"]),
          ("urlsScanned", "integer", False),
          ("violationsFoundPct", "number", False),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordEnforcement",
        "desc": "Enforcement outcome (fine / cease-and-desist / undertaking)",
        "fields": [
          ("enforcementId", "string", True),
          ("sweepVid", "string", True, None, "bridges launchSweep"),
          ("targetLei", "string", False),
          ("violationCategory", "string", True),
          ("remedy", "string", False, ["fine","cease_and_desist","refund","undertaking","public_warning","product_recall"]),
          ("fineUsd", "number", False),
          ("consumersAffected", "integer", False),
          ("resolvedAt", "string", True),
        ],
        "classify": ("scaleTier", "if consumersAffected != null and consumersAffected >= 1000000 then \"mass_market\" else if consumersAffected != null and consumersAffected >= 10000 then \"broad\" else \"targeted\"", ["targeted","broad","mass_market"]),
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
