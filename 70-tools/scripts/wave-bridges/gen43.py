#!/usr/bin/env python3
"""Wave 43 bridges — CDR marketplace / FoAA / PPA / wastewater / PSD3."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "cdr-marketplace",
    "app": "cdrMarketplace",
    "methods": [
      {
        "name": "listRegistry",
        "desc": "CDR registry / exchange listing (Puro Earth / Isometric / CDR.fyi / Frontier — bridges cdr-verification + climate-carbon-market + blue-carbon-mrv)",
        "fields": [
          ("registryId", "string", True),
          ("operatorLei", "string", False),
          ("registryName", "string", True),
          ("registryKind", "string", True, ["standard_body","exchange","otc_broker","advance_market_commitment","procurement_club","corp_buyer"]),
          ("methodologiesSupported", "string", False, None, "comma: DAC,BECCS,ERW,OAF,biochar,mineralization,blue_carbon,afforestation"),
          ("jurisdictionIso3", "string", False),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordDelivery",
        "desc": "CDR tonne delivery event (buyer-seller settlement — bridges cdr-verification + climate-carbon-market)",
        "fields": [
          ("deliveryId", "string", True),
          ("registryVid", "string", True, None, "bridges listRegistry"),
          ("buyerLei", "string", False),
          ("supplierLei", "string", False),
          ("methodology", "string", True),
          ("tonnesCo2e", "number", True),
          ("priceUsdTonne", "number", False),
          ("vintage", "string", False),
          ("vintageYear", "integer", False),
          ("deliveredAt", "string", True),
        ],
        "classify": ("marketTier", "if priceUsdTonne != null and priceUsdTonne >= 500 then \"engineered\" else if priceUsdTonne != null and priceUsdTonne >= 100 then \"hybrid\" else \"nature_based\"", ["nature_based","hybrid","engineered"]),
      },
    ],
  },
  {
    "slug": "artistic-freedom",
    "app": "artisticFreedom",
    "methods": [
      {
        "name": "recordAttack",
        "desc": "UN SR in the field of cultural rights / Artists at Risk / Freemuse attack (bridges press-freedom + cultural-heritage + religious-freedom + misinformation-observatory)",
        "fields": [
          ("attackId", "string", True),
          ("artistOrcid", "string", False),
          ("artForm", "string", True, ["music","visual","literature","theatre","film","dance","street_art","digital"]),
          ("jurisdictionIso3", "string", True),
          ("attackKind", "string", True, ["killed","imprisoned","detained","exiled","censored","harassed","work_destroyed","travel_ban"]),
          ("perpetratorCategory", "string", False, ["state","non_state","political_movement","religious_actor","organized_crime","platform"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if attackKind = \"killed\" or attackKind = \"imprisoned\" then \"critical\" else if attackKind = \"exiled\" or attackKind = \"detained\" or attackKind = \"work_destroyed\" then \"severe\" else \"serious\"", ["serious","severe","critical"]),
      },
      {
        "name": "flagSafeHavenGrant",
        "desc": "Artist residency / safe haven grant (bridges refugee-unhcr + uasc-protection + ocha-funding)",
        "fields": [
          ("grantId", "string", True),
          ("attackVid", "string", False, None, "bridges recordAttack"),
          ("sponsorLei", "string", False),
          ("residencyCountryIso3", "string", True),
          ("supportKind", "string", True, ["residency","visa","legal","psych","relocation","stipend","digital_safety"]),
          ("durationMonths", "integer", False),
          ("grantedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "pandemic-treaty",
    "app": "pandemicTreaty",
    "methods": [
      {
        "name": "recordCommitment",
        "desc": "WHO Pandemic Agreement / IHR 2024 commitment (bridges pandemic-preparedness + vaccine-equity + pharma-supply + tax-transparency)",
        "fields": [
          ("commitmentId", "string", True),
          ("partyIso3", "string", True),
          ("pillar", "string", True, ["prevention","preparedness","response","one_health","pabs","surge_capacity","tech_transfer","financing"]),
          ("targetValue", "number", False),
          ("targetUnit", "string", False),
          ("targetYear", "integer", False),
          ("currentProgressPct", "number", False),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPabsDispute",
        "desc": "PABS (Pathogen Access & Benefit-Sharing) dispute (bridges itpgrfa-seeds + pharma-supply + bbnj-highseas)",
        "fields": [
          ("disputeId", "string", True),
          ("commitmentVid", "string", False, None, "bridges recordCommitment"),
          ("pathogen", "string", True),
          ("originIso3", "string", True),
          ("recipientLei", "string", False),
          ("issueKind", "string", True, ["access_denial","benefit_sharing","sequencing_leak","ipr_claim","timeline_delay","data_sharing_refusal"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "wastewater-reuse",
    "app": "wastewaterReuse",
    "methods": [
      {
        "name": "registerFacility",
        "desc": "Water reuse / desalination facility (ISO 20760 / AWWA / WHO — bridges water-scarcity + chemicals-management + agri-food-security + urban-heat)",
        "fields": [
          ("facilityId", "string", True),
          ("operatorLei", "string", False),
          ("countryIso3", "string", True),
          ("treatmentTier", "string", True, ["primary","secondary","tertiary","advanced_oxidation","membrane_mbr","reverse_osmosis","uv","ozone","nature_based"]),
          ("capacityM3Day", "number", True),
          ("endUse", "string", True, ["potable_direct","potable_indirect","irrigation","industrial","environmental","groundwater_recharge"]),
          ("commissionedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordMonitoringMetric",
        "desc": "Effluent / blended-water quality metric (bridges ocean-acidification + water-scarcity + food-waste-epr)",
        "fields": [
          ("metricId", "string", True),
          ("facilityVid", "string", True, None, "bridges registerFacility"),
          ("periodMonth", "string", True),
          ("reuseVolumeM3", "number", False),
          ("bodMgL", "number", False),
          ("codMgL", "number", False),
          ("tssMgL", "number", False),
          ("ecoliPer100ml", "number", False),
          ("micropollutantExceedances", "integer", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("qualityTier", "if micropollutantExceedances != null and micropollutantExceedances >= 5 then \"non_compliant\" else if bodMgL != null and bodMgL > 20 then \"marginal\" else \"compliant\"", ["compliant","marginal","non_compliant"]),
      },
    ],
  },
  {
    "slug": "psd3-open-finance",
    "app": "psd3OpenFinance",
    "methods": [
      {
        "name": "registerApi",
        "desc": "PSD3 / FIDA / open banking API registration (bridges mica-crypto + data-adequacy + gig-worker + mergerReview)",
        "fields": [
          ("apiId", "string", True),
          ("providerLei", "string", False),
          ("regime", "string", True, ["eu_psd3","eu_fida","uk_oban","us_cfpb_1033","au_cdr","br_ofb","in_aa","jp_apis","sg_sgfinDex"]),
          ("apiKind", "string", True, ["ais","pis","cbpii","insurance","pension","investment","mortgage","sme_lending","savings"]),
          ("authMechanism", "string", False, ["strong_customer_auth","fapi","fapi2","openid_for_finance","oauth_hybrid","vrp"]),
          ("uptime99PctMs", "number", False),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInteropIncident",
        "desc": "Open finance interoperability / fraud incident (bridges cyber-incident + fatf-travel-rule + data-adequacy)",
        "fields": [
          ("incidentId", "string", True),
          ("apiVid", "string", True, None, "bridges registerApi"),
          ("incidentKind", "string", True, ["screen_scraping_block","tpp_outage","consent_revocation_failure","api_degradation","fraud_apf","account_takeover","push_payment_scam"]),
          ("affectedUsers", "integer", False),
          ("lossUsd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if incidentKind = \"push_payment_scam\" or incidentKind = \"account_takeover\" or incidentKind = \"fraud_apf\" then \"critical\" else if incidentKind = \"api_degradation\" or incidentKind = \"tpp_outage\" then \"major\" else \"moderate\"", ["moderate","major","critical"]),
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
