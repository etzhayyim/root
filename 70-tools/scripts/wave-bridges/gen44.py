#!/usr/bin/env python3
"""Wave 44 bridges — VAAC / CBDC / accessibility svc / FIATA / e-residency."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "vaac-volcanic",
    "app": "vaacVolcanic",
    "methods": [
      {
        "name": "recordEruption",
        "desc": "Volcanic eruption event (Smithsonian GVP / VAAC / USGS VDAP — bridges disaster-response + aviation-safety + cyclone-prepo + air-quality)",
        "fields": [
          ("eventId", "string", True),
          ("volcanoName", "string", True),
          ("countryIso3", "string", True),
          ("latitude", "number", False),
          ("longitude", "number", False),
          ("veiEstimate", "integer", False, None, "Volcanic Explosivity Index 0-8"),
          ("plumeAltitudeKm", "number", False),
          ("vaacIssuer", "string", False, ["anchorage","buenos_aires","darwin","london","montreal","tokyo","toulouse","washington","wellington"]),
          ("eruptionStartedAt", "string", True),
          ("recordedAt", "string", True),
        ],
        "classify": ("severityTier", "if veiEstimate != null and veiEstimate >= 5 then \"catastrophic\" else if veiEstimate != null and veiEstimate >= 3 then \"major\" else \"moderate\"", ["moderate","major","catastrophic"]),
      },
      {
        "name": "issueAirAdvisory",
        "desc": "VAA / SIGMET advisory for aviation (bridges aviation-safety + disaster-response)",
        "fields": [
          ("advisoryId", "string", True),
          ("eventVid", "string", True, None, "bridges recordEruption"),
          ("firAffected", "string", False, None, "ICAO Flight Information Region codes"),
          ("altitudeBandFl", "string", False, None, "FL0-FL100 etc"),
          ("recommendedAction", "string", False, ["close_airspace","reroute","altitude_restriction","visual_avoidance","no_restriction"]),
          ("issuedAt", "string", True),
          ("expiresAt", "string", False),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cbdc",
    "app": "cbdc",
    "methods": [
      {
        "name": "registerProject",
        "desc": "CBDC project (BIS Atlas / wholesale + retail — bridges mica-crypto + psd3-open-finance + fatf-travel-rule + sovereign-debt)",
        "fields": [
          ("projectId", "string", True),
          ("centralBankLei", "string", False),
          ("countryIso3", "string", True),
          ("cbdcKind", "string", True, ["retail","wholesale","cross_border","synthetic"]),
          ("ledgerType", "string", False, ["permissioned_dlt","centralized","hybrid","tokenized_reserves"]),
          ("phase", "string", True, ["research","proof_of_concept","pilot","live","cancelled"]),
          ("participatingBanksCount", "integer", False),
          ("announcedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordInteropTrial",
        "desc": "mBridge / Project Agora / Dunbar / Icebreaker cross-border CBDC trial (bridges mica-crypto + fatf-travel-rule + sovereign-debt)",
        "fields": [
          ("trialId", "string", True),
          ("projectVid", "string", True, None, "bridges registerProject"),
          ("initiative", "string", True, ["mbridge","agora","dunbar","icebreaker","mariana","helvetia","jura","cedar","nexus"]),
          ("corridorsIso3", "string", True, None, "comma-separated"),
          ("settlementTimeSec", "number", False),
          ("costBpsReduction", "number", False),
          ("runAt", "string", True),
        ],
        "classify": ("integrationTier", "if settlementTimeSec != null and settlementTimeSec <= 30 then \"instant\" else if settlementTimeSec != null and settlementTimeSec <= 3600 then \"rapid\" else \"standard\"", ["standard","rapid","instant"]),
      },
    ],
  },
  {
    "slug": "accessibility-services",
    "app": "accessibilityServices",
    "methods": [
      {
        "name": "registerService",
        "desc": "Accessibility service provider (sign language / braille / real-time captioning / EAS — bridges digital-accessibility + crc-children-digital + language-preservation)",
        "fields": [
          ("serviceId", "string", True),
          ("providerLei", "string", False),
          ("countryIso3", "string", True),
          ("serviceKind", "string", True, ["sign_language_relay","real_time_captioning","audio_description","braille_transcription","alt_text_generation","sensory_room","mobility_assistant","easy_read"]),
          ("languagesSupported", "string", False, None, "comma ISO 639"),
          ("aiAssisted", "boolean", False),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "reportUnmetNeed",
        "desc": "Unmet accessibility service need (bridges digital-accessibility + icpen-consumer + uhcr-health)",
        "fields": [
          ("reportId", "string", True),
          ("serviceVid", "string", False, None, "bridges registerService"),
          ("demographicSegment", "string", True, ["deaf","dhh","blind","low_vision","deafblind","motor","cognitive","speech","autistic","multiple"]),
          ("affectedPopulation", "integer", False),
          ("barrierKind", "string", True, ["cost","geography","language","training","policy","quality","availability"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if affectedPopulation != null and affectedPopulation >= 100000 then \"mass\" else if affectedPopulation != null and affectedPopulation >= 10000 then \"broad\" else \"local\"", ["local","broad","mass"]),
      },
    ],
  },
  {
    "slug": "fiata-freight",
    "app": "fiataFreight",
    "methods": [
      {
        "name": "issueFbl",
        "desc": "FIATA Multimodal Bill of Lading (FBL) / IATA e-AWB / WCO Seal Container (bridges customs-clearance + logistics-lastmile + rail-cross-border + seafood-traceability)",
        "fields": [
          ("documentId", "string", True),
          ("documentKind", "string", True, ["fbl","ffi","fiata_sdt","fcr","fct","iata_awb","iata_eawb","wco_seal"]),
          ("forwarderLei", "string", False),
          ("shipperLei", "string", False),
          ("consigneeLei", "string", False),
          ("originUnlocode", "string", False),
          ("destinationUnlocode", "string", False),
          ("hsCode", "string", False),
          ("grossWeightKg", "number", False),
          ("insuredValueUsd", "number", False),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagLiabilityClaim",
        "desc": "Forwarder liability claim (CMR/CIM/Hague-Visby/Montreal/COGSA — bridges insurance-guarantee + cat-bond-ils + customs-clearance)",
        "fields": [
          ("claimId", "string", True),
          ("documentVid", "string", True, None, "bridges issueFbl"),
          ("lossKind", "string", True, ["damage","shortage","delay","contamination","theft","mislabelling","force_majeure"]),
          ("claimAmountUsd", "number", False),
          ("conventionApplicable", "string", False, ["cmr","cim","hague_visby","hamburg","rotterdam","montreal","warsaw","cogsa"]),
          ("resolutionStatus", "string", False, ["pending","settled","denied","arbitration","court"]),
          ("filedAt", "string", True),
        ],
        "classify": ("severityTier", "if claimAmountUsd != null and claimAmountUsd >= 1000000 then \"major\" else if claimAmountUsd != null and claimAmountUsd >= 100000 then \"significant\" else \"minor\"", ["minor","significant","major"]),
      },
    ],
  },
  {
    "slug": "e-residency",
    "app": "eResidency",
    "methods": [
      {
        "name": "recordProgram",
        "desc": "e-residency / digital nomad / RBI program (EE / UAE / PRT D7 / CR / JP — bridges digital-identity + credential-portability + tax-transparency + migrant-worker-welfare)",
        "fields": [
          ("programId", "string", True),
          ("countryIso3", "string", True),
          ("programKind", "string", True, ["e_residency","digital_nomad","golden_visa","rbi","cbi","digital_nomad_family","startup_visa"]),
          ("eligibilityMinIncomeUsd", "number", False),
          ("taxTreatment", "string", False, ["territorial","residence_based","flat_rate","exempt","worldwide"]),
          ("issuingAgencyLei", "string", False),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagComplianceRisk",
        "desc": "AML / sanctions / tax risk in residency scheme (bridges ofac-sanctions + tax-transparency + fatf-travel-rule + antitrust-dma)",
        "fields": [
          ("riskId", "string", True),
          ("programVid", "string", True, None, "bridges recordProgram"),
          ("concern", "string", True, ["money_laundering","sanctions_evasion","tax_evasion","pep_exposure","security_risk","reputation"]),
          ("authorityAction", "string", False, ["review_ordered","visa_suspension","program_frozen","individual_revocation","diplomatic_downgrade"]),
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
