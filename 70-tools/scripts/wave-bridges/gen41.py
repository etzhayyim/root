#!/usr/bin/env python3
"""Wave 41 bridges — FuelEU / gig-worker / CBAM / credential / FATF."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "fueleu-maritime",
    "app": "fueleuMaritime",
    "methods": [
      {
        "name": "reportGhgIntensity",
        "desc": "FuelEU Maritime + IMO NZF GHG intensity (bridges imo-emissions + hydrogen-economy + carrier-fleet + climate-carbon-market)",
        "fields": [
          ("reportId", "string", True),
          ("imo", "string", True),
          ("companyLei", "string", False),
          ("reportingYear", "integer", True),
          ("energyUsedGj", "number", False),
          ("wttIntensityGco2eMj", "number", False, None, "well-to-tank"),
          ("ttwIntensityGco2eMj", "number", False, None, "tank-to-wake"),
          ("wtwIntensityGco2eMj", "number", True, None, "well-to-wake"),
          ("onshorePowerUsageMwh", "number", False),
          ("submittedAt", "string", True),
        ],
        "classify": ("complianceTier", "if wtwIntensityGco2eMj <= 77 then \"fueleu_2026_compliant\" else if wtwIntensityGco2eMj <= 85 then \"near_compliant\" else \"non_compliant\"", ["non_compliant","near_compliant","fueleu_2026_compliant"]),
      },
      {
        "name": "recordPoolingAgreement",
        "desc": "FuelEU pooling / banking / borrowing arrangement (bridges carrier-fleet + hydrogen-economy)",
        "fields": [
          ("agreementId", "string", True),
          ("reportVid", "string", True, None, "bridges reportGhgIntensity"),
          ("mechanism", "string", True, ["pooling","banking","borrowing","penalty_payment"]),
          ("counterpartyLei", "string", False),
          ("gramsCo2eExchanged", "number", False),
          ("priceEurTonne", "number", False),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "gig-worker",
    "app": "gigWorker",
    "methods": [
      {
        "name": "recordClassificationRuling",
        "desc": "Gig-worker classification (EU Platform Work Directive / CA AB5 / UK IR35 — bridges antitrust-dma + labour-mobility + just-transition + migrant-worker-welfare)",
        "fields": [
          ("rulingId", "string", True),
          ("platformLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("regime", "string", True, ["eu_ptwd","ca_ab5","uk_ir35","es_rider_law","ca_bc_gig","ny_freelance","in_socialsec_code","au_gig_reform"]),
          ("classification", "string", True, ["employee","worker","self_employed","presumed_employee","indeterminate"]),
          ("applicableWorkers", "integer", False),
          ("decidedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAlgorithmicManagement",
        "desc": "Algorithmic management transparency / dispute (bridges ai-governance + misinformation-observatory)",
        "fields": [
          ("disputeId", "string", True),
          ("rulingVid", "string", True, None, "bridges recordClassificationRuling"),
          ("issueKind", "string", True, ["price_discrimination","deactivation_no_reason","surveillance","discriminatory_routing","opaque_scoring","override_denial","underpayment"]),
          ("affectedWorkers", "integer", False),
          ("remedyRequired", "string", False, ["human_review","algorithm_disclosure","compensation","reinstate","opt_out","ban_practice"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if issueKind = \"deactivation_no_reason\" or issueKind = \"discriminatory_routing\" then \"severe\" else if issueKind = \"price_discrimination\" or issueKind = \"surveillance\" then \"significant\" else \"moderate\"", ["moderate","significant","severe"]),
      },
    ],
  },
  {
    "slug": "cbam-extension",
    "app": "cbamExtension",
    "methods": [
      {
        "name": "registerScopeExpansion",
        "desc": "CBAM / carbon border extension scope addition (bridges eu-cbam + critical-minerals + sovereign-debt + wto-dispute)",
        "fields": [
          ("extensionId", "string", True),
          ("jurisdictionRegime", "string", True, ["eu_cbam","uk_cbam","ca_cbca","us_ccia","au_ccr","jp_mf_cba"]),
          ("sectorAddedHs", "string", True, None, "HS 2-digit range"),
          ("coveredGhgScopes", "string", False, None, "comma: direct,indirect,downstream"),
          ("defaultEmissionFactor", "number", False),
          ("defaultFactorSource", "string", False),
          ("transitionalPeriodYears", "integer", False),
          ("effectiveFrom", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDisputeNotification",
        "desc": "WTO / GATT XX dispute over CBAM or equivalent (bridges wto-dispute + sovereign-debt)",
        "fields": [
          ("disputeId", "string", True),
          ("extensionVid", "string", True, None, "bridges registerScopeExpansion"),
          ("complainantIso3", "string", True),
          ("claimBasis", "string", True, ["mfn","national_treatment","subsidy","technical_barriers","gatt_xx_exception"]),
          ("wtoDisputeVid", "string", False, None, "bridges open-wto-dispute"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "credential-portability",
    "app": "credentialPortability",
    "methods": [
      {
        "name": "registerCredentialWallet",
        "desc": "Europass / Credential Engine / EUDI wallet credential (bridges digital-identity + language-preservation + labour-mobility)",
        "fields": [
          ("walletId", "string", True),
          ("holderOrcid", "string", False),
          ("credentialKind", "string", True, ["diploma","microcredential","badge","apprenticeship","license","occupational"]),
          ("issuingBodyLei", "string", False),
          ("issuingCountryIso3", "string", True),
          ("framework", "string", False, ["eqf","nqf","isced","eqavet","escf","wqf_jp","knwq_kr"]),
          ("level", "integer", False),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordCrossBorderRecognition",
        "desc": "Cross-border recognition decision (bridges labour-mobility + refugee-unhcr + digital-identity)",
        "fields": [
          ("decisionId", "string", True),
          ("walletVid", "string", True, None, "bridges registerCredentialWallet"),
          ("recognizingIso3", "string", True),
          ("decisionKind", "string", True, ["full_recognition","partial_recognition","supplement_required","refused","professional_test_required"]),
          ("decisionMonths", "number", False),
          ("decidedAt", "string", True),
        ],
        "classify": ("portabilityTier", "if decisionKind = \"full_recognition\" then \"seamless\" else if decisionKind = \"partial_recognition\" or decisionKind = \"supplement_required\" then \"conditional\" else \"blocked\"", ["blocked","conditional","seamless"]),
      },
    ],
  },
  {
    "slug": "fatf-travel-rule",
    "app": "fatfTravelRule",
    "methods": [
      {
        "name": "recordVaspTransfer",
        "desc": "FATF Recommendation 16 travel rule VASP transfer (bridges mica-crypto + blockchain-mev + ofac-sanctions + data-adequacy)",
        "fields": [
          ("transferId", "string", True),
          ("originatorVaspLei", "string", False),
          ("beneficiaryVaspLei", "string", False),
          ("originatorJurisdictionIso3", "string", True),
          ("beneficiaryJurisdictionIso3", "string", True),
          ("amountUsd", "number", True),
          ("chain", "string", False),
          ("txHash", "string", False),
          ("messagingProtocol", "string", False, ["trp","ivms101","sumsub_travel","notabene","trust_chainalysis","shyft"]),
          ("transferredAt", "string", True),
        ],
        "classify": ("riskTier", "if amountUsd >= 1000 and beneficiaryVaspLei = null then \"unhosted_wallet\" else if amountUsd >= 100000 then \"high_value\" else \"standard\"", ["standard","high_value","unhosted_wallet"]),
      },
      {
        "name": "flagComplianceBreach",
        "desc": "Travel rule compliance breach (bridges ofac-sanctions + mica-crypto + antitrust-dma)",
        "fields": [
          ("breachId", "string", True),
          ("transferVid", "string", True, None, "bridges recordVaspTransfer"),
          ("breachKind", "string", True, ["missing_originator","missing_beneficiary","sanctions_screening_fail","data_privacy","jurisdiction_mismatch","counterparty_due_diligence"]),
          ("penaltyUsd", "number", False),
          ("enforcer", "string", False, ["fincen","fca","bafin","jfsa","masc","finma","mica_authority"]),
          ("actedAt", "string", True),
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
