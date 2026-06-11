#!/usr/bin/env python3
"""Wave 25 bridges — IAEA / IMO CII / EUDI / antitrust / fisheries subsidies."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "iaea-safeguards",
    "app": "iaeaSafeguards",
    "methods": [
      {
        "name": "recordInspection",
        "desc": "IAEA INFCIRC/153 + 540 safeguards inspection (bridges critical-minerals + disaster-response)",
        "fields": [
          ("inspectionId", "string", True),
          ("facilityCode", "string", True, None, "IAEA facility code"),
          ("stateIso3", "string", True),
          ("safeguardsAgreement", "string", True, ["csa","ap","sqp","vo","other"]),
          ("materialCategory", "string", False, ["hyperlink","heu","leu","plutonium","natural_uranium","thorium","depleted"]),
          ("finding", "string", True, ["routine","anomaly","broader_conclusion","non_compliance","material_unaccounted"]),
          ("inspectedAt", "string", True),
        ],
        "classify": ("concernTier", "if finding = \"non_compliance\" or finding = \"material_unaccounted\" then \"critical\" else if finding = \"anomaly\" then \"elevated\" else \"routine\"", ["routine","elevated","critical"]),
      },
      {
        "name": "flagProliferation",
        "desc": "Proliferation signal (NSG / Wassenaar / MTCR — bridges mofcom + ofac-sanctions)",
        "fields": [
          ("signalId", "string", True),
          ("inspectionVid", "string", False, None, "bridges recordInspection"),
          ("regimeRefers", "string", True, ["NSG","Wassenaar","MTCR","Australia_Group","UNSC_1540","CPPNM"]),
          ("concernedIso3", "string", True),
          ("indicator", "string", True, ["clandestine_enrichment","undeclared_facility","diversion","transfer_unauthorized","dual_use_equipment","weapons_design"]),
          ("ofacSdnVid", "string", False, None, "bridges open-ofac-sanctions-sdn"),
          ("flaggedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "imo-emissions",
    "app": "imoEmissions",
    "methods": [
      {
        "name": "reportCiiRating",
        "desc": "IMO CII / EEXI carbon intensity rating (bridges carrier-fleet + climate-value-chain + eu-cbam)",
        "fields": [
          ("ratingId", "string", True),
          ("imo", "string", True),
          ("carrierFleetVid", "string", False, None, "bridges open-carrier-fleet"),
          ("cursorYear", "integer", True),
          ("ciiRating", "string", True, ["A","B","C","D","E"]),
          ("ciiRequiredGramsCo2", "number", False),
          ("ciiAttainedGramsCo2", "number", False),
          ("eexiAttained", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("complianceTier", "if ciiRating = \"D\" or ciiRating = \"E\" then \"non_compliant\" else if ciiRating = \"C\" then \"marginal\" else \"compliant\"", ["compliant","marginal","non_compliant"]),
      },
      {
        "name": "recordPoseidonAlignment",
        "desc": "Poseidon Principles alignment (banks financing shipping)",
        "fields": [
          ("alignmentId", "string", True),
          ("bankLei", "string", True),
          ("portfolioImoCount", "integer", False),
          ("portfolioAlignmentDeltaPct", "number", False, None, "vs IMO trajectory"),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "digital-identity",
    "app": "digitalIdentity",
    "methods": [
      {
        "name": "registerCredentialSchema",
        "desc": "EUDI ARF / ISO 18013-5 mDL / W3C VC schema registry (bridges ai-governance + cyber-compliance)",
        "fields": [
          ("schemaId", "string", True),
          ("format", "string", True, ["mso_mdoc","sd_jwt_vc","jwt_vc","ldp_vc","hmac_vc"]),
          ("framework", "string", True, ["eudi","mdl","verifiable_credential","open_id4vc","oid4vp","dif_presentation"]),
          ("issuerLei", "string", False),
          ("governingJurisdictionIso3", "string", False),
          ("credentialType", "string", True, ["pid","mdl","residence","diploma","professional_license","health","bank_account"]),
          ("pqcReady", "boolean", False),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagVerificationIncident",
        "desc": "Wallet / verifier incident (bridges cyber-incident + misinformation)",
        "fields": [
          ("incidentId", "string", True),
          ("schemaVid", "string", False, None, "bridges registerCredentialSchema"),
          ("incidentType", "string", True, ["phishing","deepfake_challenge","credential_theft","replay","downgrade","selective_disclosure_leak","revocation_lag"]),
          ("affectedWallets", "integer", False),
          ("aiModelVid", "string", False, None, "bridges open-ai-governance"),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if incidentType = \"credential_theft\" or incidentType = \"downgrade\" then \"critical\" else if incidentType = \"deepfake_challenge\" or incidentType = \"phishing\" then \"high\" else \"moderate\"", ["moderate","high","critical"]),
      },
    ],
  },
  {
    "slug": "antitrust-dma",
    "app": "antitrustDma",
    "methods": [
      {
        "name": "designateGatekeeper",
        "desc": "EU DMA gatekeeper / UK DMCC / China SAMR platform designation (bridges ofac-sanctions + misinformation)",
        "fields": [
          ("designationId", "string", True),
          ("regime", "string", True, ["eu_dma","uk_dmcc","china_samr","us_doj","us_ftc","japan_jftc","kr_kftc"]),
          ("platformLei", "string", True),
          ("cpsCategory", "string", True, ["search","social","video","app_store","os","browser","cloud","messaging","ads","marketplace","ai_platform"]),
          ("revenueEur", "number", False),
          ("eeauserCount", "integer", False),
          ("designatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagViolation",
        "desc": "Interop / self-preferencing / tying violation + fines",
        "fields": [
          ("violationId", "string", True),
          ("designationVid", "string", True, None, "bridges designateGatekeeper"),
          ("obligationBreached", "string", True, ["interop","tying","self_preferencing","data_portability","no_moat_ads","no_auto_switch","third_party_app_store","ai_bundling"]),
          ("fineEur", "number", False),
          ("resolutionType", "string", False, ["commitment","formal_prohibition","behavioral_remedy","structural_remedy","appealed"]),
          ("issuedAt", "string", True),
        ],
        "classify": ("impactTier", "if fineEur != null and fineEur >= 1000000000 then \"record\" else if fineEur != null and fineEur >= 100000000 then \"significant\" else \"notice\"", ["notice","significant","record"]),
      },
    ],
  },
  {
    "slug": "fisheries-subsidies",
    "app": "fisheriesSubsidies",
    "methods": [
      {
        "name": "recordSubsidy",
        "desc": "WTO Fisheries Subsidies Agreement disclosure (bridges fisheries-iuu + cofog + wto-dispute)",
        "fields": [
          ("subsidyId", "string", True),
          ("memberIso3", "string", True),
          ("recipientLei", "string", False),
          ("subsidyType", "string", True, ["fuel","vessel_construction","operating_cost","gear","insurance","port_dues","processing","tax_concession"]),
          ("amountUsd", "number", True),
          ("targetsIuu", "boolean", False),
          ("targetsOverfished", "boolean", False),
          ("cofogExpenditureVid", "string", False, None, "bridges open-cofog-expenditure"),
          ("notifiedAt", "string", True),
        ],
        "classify": ("complianceTier", "if targetsIuu = true or targetsOverfished = true then \"prohibited\" else if subsidyType = \"fuel\" or subsidyType = \"vessel_construction\" or subsidyType = \"operating_cost\" then \"capacity_enhancing\" else \"neutral\"", ["neutral","capacity_enhancing","prohibited"]),
      },
      {
        "name": "flagNotificationGap",
        "desc": "Notification gap / peer review finding",
        "fields": [
          ("flagId", "string", True),
          ("memberIso3", "string", True),
          ("period", "string", True, None, "YYYY"),
          ("expectedCategories", "string", False),
          ("missingCategories", "string", True),
          ("raisedByIso3", "string", False),
          ("wtoDisputeVid", "string", False, None, "bridges open-wto-dispute"),
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
