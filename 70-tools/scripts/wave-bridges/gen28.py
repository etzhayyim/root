#!/usr/bin/env python3
"""Wave 28 bridges — BBNJ / UAS UTM / food waste / labour mobility / blockchain MEV."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "bbnj-highseas",
    "app": "bbnjHighseas",
    "methods": [
      {
        "name": "registerMpa",
        "desc": "BBNJ / high-seas MPA area designation (bridges biodiversity-gbf + fisheries-iuu + deep-sea-mining)",
        "fields": [
          ("mpaId", "string", True),
          ("areaName", "string", True),
          ("governanceBody", "string", True, ["bbnj_cop","cbd","ospar","ccamlr","nafo","iotc","regional"]),
          ("abnJurisdictionType", "string", True, ["abnJ","eez_high_seas_interface","area","ccamlr_area"]),
          ("areaKm2", "number", True),
          ("protectionLevel", "string", True, ["no_take","partial","restricted_fishing","navigational_only"]),
          ("establishedAt", "string", True),
          ("reviewDueAt", "string", False),
        ],
        "classify": ("conservationTier", "if protectionLevel = \"no_take\" then \"strict\" else if protectionLevel = \"partial\" then \"mixed\" else \"minimal\"", ["minimal","mixed","strict"]),
      },
      {
        "name": "recordDsmBjniLink",
        "desc": "BBNJ digital sequence information / genetic resources benefit-sharing",
        "fields": [
          ("linkId", "string", True),
          ("mpaVid", "string", False, None, "bridges registerMpa"),
          ("dsiIdentifier", "string", True, None, "GenBank / BOLD / INSDC accession"),
          ("taxonAsfisOrCas", "string", False),
          ("benefitSharingMechanism", "string", True, ["mat","national_levy","global_fund","traditional_knowledge"]),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "uas-traffic-management",
    "app": "uasTrafficManagement",
    "methods": [
      {
        "name": "registerFlightAuthorization",
        "desc": "UAS/drone flight authorization (FAA LAANC / EASA U-space / JCAB — bridges aviation-safety + urban-mobility)",
        "fields": [
          ("authorizationId", "string", True),
          ("operatorLei", "string", False),
          ("regime", "string", True, ["faa_laanc","easa_uspace","jcab","caac","isac","dgca"]),
          ("uasRegistrationId", "string", False),
          ("flightCategory", "string", True, ["open","specific","certified","part_107","sora"]),
          ("maxAltitudeMeters", "integer", False),
          ("airspaceClass", "string", False, ["A","B","C","D","E","G","UTM_reserved"]),
          ("authorizedAt", "string", True),
          ("expiresAt", "string", False),
        ],
        "classify": ("riskTier", "if flightCategory = \"certified\" then \"high\" else if flightCategory = \"specific\" or flightCategory = \"sora\" then \"medium\" else \"low\"", ["low","medium","high"]),
      },
      {
        "name": "reportBvlosIncident",
        "desc": "BVLOS / swarm / drone-to-drone incident (bridges aviation-safety + cyber-incident)",
        "fields": [
          ("incidentId", "string", True),
          ("authorizationVid", "string", False, None, "bridges registerFlightAuthorization"),
          ("eventType", "string", True, ["loss_of_c2","swarm_desync","gps_spoofing","airprox","crash","unauthorized_entry","battery_fire","cyber_intrusion"]),
          ("airproxVid", "string", False, None, "bridges open-aviation-safety reportAirprox"),
          ("cyberIncidentVid", "string", False, None, "bridges open-cyber-incident"),
          ("injuries", "integer", False),
          ("fatalities", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if fatalities != null and fatalities >= 1 then \"fatal\" else if injuries != null and injuries >= 1 then \"injury\" else if eventType = \"gps_spoofing\" or eventType = \"cyber_intrusion\" then \"cyber_severe\" else \"operational\"", ["operational","cyber_severe","injury","fatal"]),
      },
    ],
  },
  {
    "slug": "food-waste-epr",
    "app": "foodWasteEpr",
    "methods": [
      {
        "name": "reportFoodLoss",
        "desc": "SDG 12.3 food loss & waste report (bridges agri-food-security + sdg-reporting + plastic-treaty)",
        "fields": [
          ("reportId", "string", True),
          ("countryIso3", "string", True),
          ("sector", "string", True, ["production","post_harvest","processing","distribution","retail","household","food_service"]),
          ("stage", "string", True, ["loss","waste"]),
          ("tonnesPerYear", "number", True),
          ("percapitaKg", "number", False),
          ("methodology", "string", False, ["ghg_fl_index","fl_calculator","fwp_fao","household_diary"]),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("intensityTier", "if percapitaKg != null and percapitaKg >= 100 then \"high\" else if percapitaKg != null and percapitaKg >= 50 then \"moderate\" else \"low\"", ["low","moderate","high"]),
      },
      {
        "name": "recordEprScheme",
        "desc": "Extended Producer Responsibility scheme for packaging/food (bridges plastic-treaty + chemicals-management)",
        "fields": [
          ("schemeId", "string", True),
          ("countryIso3", "string", True),
          ("scope", "string", True, ["packaging","food_waste","electronics","batteries","textiles","tyres","plastic_bottles"]),
          ("feeBasisDescription", "string", False),
          ("annualFeesUsd", "number", False),
          ("collectionTargetPct", "number", False),
          ("recyclingTargetPct", "number", False),
          ("effectiveFrom", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "labour-mobility",
    "app": "labourMobility",
    "methods": [
      {
        "name": "registerCorridor",
        "desc": "Labour mobility corridor (GCM / BLAs — bridges refugee-unhcr + forced-labor + just-transition + crew-welfare)",
        "fields": [
          ("corridorId", "string", True),
          ("originIso3", "string", True),
          ("destinationIso3", "string", True),
          ("instrument", "string", True, ["bla","mou","gcm_compact","eu_blue_card","caricom","asean","ecowas"]),
          ("sectorIsic", "string", False, None, "bridges open-isic"),
          ("annualQuota", "integer", False),
          ("durationMonths", "integer", False),
          ("pathwayToResidence", "boolean", False),
          ("effectiveFrom", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRecruitmentAbuse",
        "desc": "Recruitment abuse / Fair Recruitment Principles violation",
        "fields": [
          ("abuseId", "string", True),
          ("corridorVid", "string", True, None, "bridges registerCorridor"),
          ("recruiterLei", "string", False),
          ("abuseType", "string", True, ["recruitment_fees","deception","contract_substitution","passport_confiscation","wage_theft","debt_bondage","forced_overtime"]),
          ("workersAffected", "integer", False),
          ("forcedLaborVid", "string", False, None, "bridges open-forced-labor"),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if abuseType = \"debt_bondage\" or abuseType = \"passport_confiscation\" then \"severe\" else if abuseType = \"contract_substitution\" or abuseType = \"wage_theft\" then \"strong\" else \"moderate\"", ["moderate","strong","severe"]),
      },
    ],
  },
  {
    "slug": "blockchain-mev",
    "app": "blockchainMev",
    "methods": [
      {
        "name": "recordMevEvent",
        "desc": "Blockchain MEV / front-running event (bridges cyber-incident + antitrust-dma + ofac-sanctions)",
        "fields": [
          ("eventId", "string", True),
          ("chain", "string", True, ["ethereum","arbitrum","optimism","base","polygon","solana","bnb","avalanche","cosmos"]),
          ("blockNumber", "integer", False),
          ("txHash", "string", True),
          ("mevKind", "string", True, ["sandwich","front_running","back_running","arbitrage","liquidation","just_in_time","time_bandit"]),
          ("extractedUsd", "number", False),
          ("builderId", "string", False),
          ("relayLei", "string", False),
          ("victimAddress", "string", False),
          ("occurredAt", "string", True),
        ],
        "classify": ("harmTier", "if mevKind = \"sandwich\" or mevKind = \"front_running\" then \"toxic\" else if mevKind = \"arbitrage\" or mevKind = \"back_running\" then \"benign\" else \"mixed\"", ["benign","mixed","toxic"]),
      },
      {
        "name": "flagOfacMixing",
        "desc": "OFAC-sanctioned address interaction on-chain (bridges ofac-sanctions-sdn)",
        "fields": [
          ("flagId", "string", True),
          ("txHash", "string", True),
          ("chain", "string", True),
          ("sanctionedAddress", "string", True),
          ("mixerProtocol", "string", False, ["tornado","samourai","blender","chipmixer","mixer_generic"]),
          ("amountUsd", "number", False),
          ("ofacSdnVid", "string", False, None, "bridges open-ofac-sanctions-sdn"),
          ("detectedAt", "string", True),
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
