#!/usr/bin/env python3
"""Wave 46 bridges — housing / stablecoin / MPA / LGAF / CRPD."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "housing-affordability",
    "app": "housingAffordability",
    "methods": [
      {
        "name": "recordIndex",
        "desc": "Housing affordability index (OECD Better Life / UN Habitat / Demographia — bridges coastal-slr + urban-heat + urban-mobility + reit-transparency)",
        "fields": [
          ("indexId", "string", True),
          ("cityUnlocode", "string", True),
          ("countryIso3", "string", True),
          ("indexProvider", "string", True, ["oecd_bli","unhabitat","demographia","zillow","rightmove","eurostat","vhda"]),
          ("medianPriceToIncomeRatio", "number", False),
          ("rentToIncomePct", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("affordabilityTier", "if medianPriceToIncomeRatio != null and medianPriceToIncomeRatio >= 9 then \"severely_unaffordable\" else if medianPriceToIncomeRatio != null and medianPriceToIncomeRatio >= 5.1 then \"seriously_unaffordable\" else if medianPriceToIncomeRatio != null and medianPriceToIncomeRatio >= 4.1 then \"moderately_unaffordable\" else \"affordable\"", ["affordable","moderately_unaffordable","seriously_unaffordable","severely_unaffordable"]),
      },
      {
        "name": "flagHomelessness",
        "desc": "Homelessness point-in-time count (bridges refugee-unhcr + universal-health-coverage + migrant-worker-welfare)",
        "fields": [
          ("countId", "string", True),
          ("indexVid", "string", False, None, "bridges recordIndex"),
          ("countryIso3", "string", True),
          ("pitDate", "string", True),
          ("totalCount", "integer", True),
          ("unshelteredCount", "integer", False),
          ("chronicCount", "integer", False),
          ("familyCount", "integer", False),
          ("veteranCount", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "stablecoin-reserves",
    "app": "stablecoinReserves",
    "methods": [
      {
        "name": "recordAttestation",
        "desc": "Stablecoin reserves attestation (MiCA EMT / PBS 2500 / GENIUS Act — bridges mica-crypto + psd3-open-finance + fatf-travel-rule + sovereign-debt)",
        "fields": [
          ("attestationId", "string", True),
          ("issuerLei", "string", False),
          ("tokenSymbol", "string", True),
          ("jurisdictionIso3", "string", True),
          ("issuanceCirculatingUsd", "number", True),
          ("reserveCashPct", "number", False),
          ("reserveTbillPct", "number", False),
          ("reserveReverseRepoPct", "number", False),
          ("reserveOtherPct", "number", False),
          ("attestorLei", "string", False),
          ("attestedAt", "string", True),
        ],
        "classify": ("reserveQualityTier", "if reserveCashPct != null and reserveCashPct >= 20 and reserveTbillPct != null and reserveTbillPct >= 70 then \"high_quality\" else if reserveCashPct != null and reserveCashPct >= 5 then \"adequate\" else \"concerning\"", ["concerning","adequate","high_quality"]),
      },
      {
        "name": "flagDepegEvent",
        "desc": "Stablecoin depeg / run / redemption crisis (bridges cat-bond-ils + mica-crypto + antitrust-dma)",
        "fields": [
          ("eventId", "string", True),
          ("attestationVid", "string", True, None, "bridges recordAttestation"),
          ("minPriceUsd", "number", True),
          ("durationMinutes", "integer", False),
          ("redemptionsUsd", "number", False),
          ("triggerCause", "string", False, ["reserve_quality","bank_failure","liquidity","oracle_failure","bridge_hack","regulatory","market"]),
          ("observedAt", "string", True),
        ],
        "classify": ("severityTier", "if minPriceUsd <= 0.85 then \"failed\" else if minPriceUsd <= 0.95 then \"distressed\" else \"mild\"", ["mild","distressed","failed"]),
      },
    ],
  },
  {
    "slug": "mpa-effectiveness",
    "app": "mpaEffectiveness",
    "methods": [
      {
        "name": "recordAssessment",
        "desc": "MPA management effectiveness (MPA Guide / PAME WH MEE — bridges biodiversity-gbf + bbnj-highseas + fisheries-iuu + blue-economy)",
        "fields": [
          ("assessmentId", "string", True),
          ("mpaWdpaId", "string", True),
          ("countryIso3", "string", True),
          ("mpaGuideStage", "string", True, ["proposed","designated","implemented","actively_managed"]),
          ("mpaGuideLevelOfProtection", "string", True, ["fully_protected","highly_protected","lightly_protected","minimally_protected"]),
          ("pameScore", "number", False),
          ("assessedYear", "integer", True),
          ("recordedAt", "string", True),
        ],
        "classify": ("effectivenessTier", "if mpaGuideStage = \"actively_managed\" and mpaGuideLevelOfProtection = \"fully_protected\" then \"exemplary\" else if mpaGuideStage = \"implemented\" then \"functional\" else if mpaGuideStage = \"designated\" then \"paper_park\" else \"proposed_only\"", ["proposed_only","paper_park","functional","exemplary"]),
      },
      {
        "name": "flagEnforcementAction",
        "desc": "MPA enforcement action / IUU encounter (bridges fisheries-iuu + maritime-piracy + cites-wildlife + bbnj-highseas)",
        "fields": [
          ("actionId", "string", True),
          ("assessmentVid", "string", True, None, "bridges recordAssessment"),
          ("actionKind", "string", True, ["surveillance","warning","vessel_boarding","seizure","fine","arrest","prosecution","no_action"]),
          ("targetVesselImo", "string", False),
          ("iuuFlagVid", "string", False, None, "bridges open-fisheries-iuu"),
          ("actedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "land-tenure",
    "app": "landTenure",
    "methods": [
      {
        "name": "recordRecognition",
        "desc": "Land tenure recognition (LGAF / VGGT / IFAD Land Tenure — bridges indigenous-rights + mining-operation + agri-food-security + forestry-mrv)",
        "fields": [
          ("recognitionId", "string", True),
          ("countryIso3", "string", True),
          ("tenureType", "string", True, ["customary","collective","leasehold","freehold","squatter_rights","indigenous_community","state","private"]),
          ("areaHectares", "number", False),
          ("beneficiariesCount", "integer", False),
          ("instrumentKind", "string", False, ["formal_title","registered_custom","certificate","ccro","land_use_right","restitution"]),
          ("recognizedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagEviction",
        "desc": "Eviction / land grab flag (bridges forced-labor + indigenous-rights + climate-litigation + uasc-protection)",
        "fields": [
          ("evictionId", "string", True),
          ("recognitionVid", "string", False, None, "bridges recordRecognition"),
          ("evictingActorLei", "string", False),
          ("evictionKind", "string", True, ["state","corporate_land_grab","infrastructure","conservation_fortress","conflict_displacement","climate_risk"]),
          ("personsAffected", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if personsAffected != null and personsAffected >= 10000 then \"mass\" else if personsAffected != null and personsAffected >= 1000 then \"major\" else \"targeted\"", ["targeted","major","mass"]),
      },
    ],
  },
  {
    "slug": "crpd-disability",
    "app": "crpdDisability",
    "methods": [
      {
        "name": "recordCountryReport",
        "desc": "UN CRPD periodic report (bridges digital-accessibility + accessibility-services + universal-health-coverage + mental-health-parity)",
        "fields": [
          ("reportId", "string", True),
          ("countryIso3", "string", True),
          ("reportingCycle", "string", True),
          ("articleFocus", "string", True, ["art9_accessibility","art12_legal_capacity","art19_independent_living","art24_education","art25_health","art27_work","art29_political","art30_cultural","general"]),
          ("implementationScore", "integer", False, None, "0-10"),
          ("shadowReportsCount", "integer", False),
          ("submittedAt", "string", True),
        ],
        "classify": ("progressTier", "if implementationScore != null and implementationScore >= 7 then \"advanced\" else if implementationScore != null and implementationScore >= 4 then \"moderate\" else \"nascent\"", ["nascent","moderate","advanced"]),
      },
      {
        "name": "flagReservationWithdrawal",
        "desc": "CRPD reservation / declaration / withdrawal (bridges indigenous-rights + mental-health-parity)",
        "fields": [
          ("actionId", "string", True),
          ("reportVid", "string", False, None, "bridges recordCountryReport"),
          ("countryIso3", "string", True),
          ("actionKind", "string", True, ["reservation","interpretive_declaration","withdrawal_of_reservation","optional_protocol_accession","denunciation"]),
          ("articleAffected", "string", False),
          ("recordedAt", "string", True),
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
