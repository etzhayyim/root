#!/usr/bin/env python3
"""Wave 59 — csddd / soy-moratorium / debarment / sovereign-guarantee / price-cap-coalition.

Bridges Wave 58:
- csddd-directive ↔ ungpNap.flagImplementationGap
- soy-moratorium ↔ feedProvenance.flagFeedLinkage
- debarment-list ↔ complianceMonitor.flagBreachOfTerms
- sovereign-guarantee ↔ soeBalanceSheet.flagContingentRisk
- price-cap-coalition ↔ aisDarkVessel.flagSanctionsEvasion
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "csddd-directive",
    "app": "csdddDirective",
    "methods": [
      {
        "name": "recordScopeFiling",
        "desc": "EU CSDDD / UK Modern Slavery / German LkSG / French Vigilance scope filing (bridges ungpNap.flagImplementationGap + ilo-labor-rights + eudr-deforestation)",
        "fields": [
          ("filingId", "string", True),
          ("companyLei", "string", False),
          ("regime", "string", True, ["eu_csddd","eu_csrd","uk_modern_slavery","de_lksg","fr_vigilance","no_transparency","nl_child_labor","au_modern_slavery","ca_supply_chain"]),
          ("tierApplicable", "string", True, ["tier_1_gte5000","tier_2_gte3000","tier_3_gte1000","high_impact_sector","group_consolidation","upstream_entity","downstream_entity"]),
          ("implementationGapVid", "string", False, None, "bridges ungpNap.flagImplementationGap"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDueDiligenceGap",
        "desc": "Due diligence process gap / failure to act (bridges ungpNap.flagImplementationGap + worker-grievance + ilo-labor-rights)",
        "fields": [
          ("gapId", "string", True),
          ("filingVid", "string", True, None, "bridges recordScopeFiling"),
          ("gapKind", "string", True, ["identify_actual","identify_potential","prevent_mitigate","cease_activity","remediation","stakeholder_engage","reporting","integrate_policy","terminate_relationship"]),
          ("enforcementKind", "string", False, ["civil_fine","public_naming","exclude_public_procurement","injunction","directorial_liability","class_action"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "soy-moratorium",
    "app": "soyMoratorium",
    "methods": [
      {
        "name": "recordOriginTrace",
        "desc": "Amazon / Cerrado soy moratorium origin trace (bridges feedProvenance.flagFeedLinkage + eudr-deforestation + forestry-mrv)",
        "fields": [
          ("traceId", "string", True),
          ("lotCode", "string", True),
          ("originMuniIbge", "string", False, None, "IBGE municipality code"),
          ("biome", "string", True, ["amazon","cerrado","atlantic_forest","pantanal","caatinga","pampa","chaco_argentine","chaco_paraguay","gran_chaco_bolivia"]),
          ("complianceKind", "string", True, ["compliant_pre_2008","compliant_pre_2020","non_compliant","in_review","unmapped","embargo_ibama","pra_pending"]),
          ("feedLinkageVid", "string", False, None, "bridges feedProvenance.flagFeedLinkage"),
          ("volumeTonnes", "number", False),
          ("tracedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMoratoriumBreach",
        "desc": "Soy moratorium / forest code breach (bridges feedProvenance.flagFeedLinkage + eudr-deforestation + climate-value-chain)",
        "fields": [
          ("breachId", "string", True),
          ("traceVid", "string", True, None, "bridges recordOriginTrace"),
          ("breachKind", "string", True, ["post_cutoff_clearance","illegal_embargo_area","indigenous_overlap","conservation_unit","legal_reserve_deficit","permanent_preservation_area","laundering_cattle_soy","undocumented"]),
          ("affectedHectares", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "debarment-list",
    "app": "debarmentList",
    "methods": [
      {
        "name": "recordDebarment",
        "desc": "Multilateral debarment listing (World Bank / IDB / ADB / AfDB / EBRD cross-debarment — bridges complianceMonitor.flagBreachOfTerms + enforcement-action + antitrust-dma)",
        "fields": [
          ("debarmentId", "string", True),
          ("respondentLei", "string", False),
          ("mdb", "string", True, ["world_bank","idb","adb","afdb","ebrd","iadb_invest","wbg_cross_debar","imf","eib","iib"]),
          ("sanctionKind", "string", True, ["debarment","debarment_with_conditional_release","conditional_non_debarment","letter_of_reprimand","restitution","cross_debarment_honored"]),
          ("monitorReportVid", "string", False, None, "bridges complianceMonitor.flagBreachOfTerms"),
          ("debarmentDurationMo", "integer", False),
          ("imposedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPhoenixEntity",
        "desc": "Phoenix / successor-entity detection (bridges complianceMonitor.flagBreachOfTerms + ofac-sanctions-sdn + beneficial-ownership)",
        "fields": [
          ("flagId", "string", True),
          ("debarmentVid", "string", True, None, "bridges recordDebarment"),
          ("phoenixKind", "string", True, ["same_principals","same_address","successor_beneficial_owner","asset_transfer","staff_migration","contract_assignment","subcontractor_veil","sister_entity"]),
          ("relatedEntityLei", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "sovereign-guarantee",
    "app": "sovereignGuarantee",
    "methods": [
      {
        "name": "recordGuarantee",
        "desc": "Explicit sovereign guarantee / letter of comfort / SOE backstop (bridges soeBalanceSheet.flagContingentRisk + sovereign-debt + debt-transparency)",
        "fields": [
          ("guaranteeId", "string", True),
          ("guarantorIso3", "string", True),
          ("beneficiaryLei", "string", False),
          ("instrumentKind", "string", True, ["explicit_guarantee","letter_of_comfort","cross_default_support","keep_well","credit_wrap","pri_multilateral","export_credit","central_bank_put","fiscal_agency"]),
          ("principalBusd", "number", True),
          ("soeRiskVid", "string", False, None, "bridges soeBalanceSheet.flagContingentRisk"),
          ("disclosedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCallEvent",
        "desc": "Guarantee call / trigger event / cross-default (bridges soeBalanceSheet.flagContingentRisk + sovereign-debt + imf-article-iv)",
        "fields": [
          ("flagId", "string", True),
          ("guaranteeVid", "string", True, None, "bridges recordGuarantee"),
          ("triggerKind", "string", True, ["default_beneficiary","acceleration","rating_downgrade","material_adverse_change","covenant_breach","insolvency_event","currency_event","political_event"]),
          ("calledBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "price-cap-coalition",
    "app": "priceCapCoalition",
    "methods": [
      {
        "name": "recordAttestation",
        "desc": "G7 Price Cap Coalition attestation / maritime service (bridges aisDarkVessel.flagSanctionsEvasion + ofac-sanctions-sdn + commodity-trade)",
        "fields": [
          ("attestationId", "string", True),
          ("tier", "string", True, ["tier_1_trader","tier_2_service","tier_3_port","crude_cap","petroleum_product_cap","diesel_cap","gasoline_cap"]),
          ("serviceProviderLei", "string", False),
          ("attestationKind", "string", True, ["price_below_cap","itinerary_compliant","no_sts_with_shadow","insurance_compliant","flag_registry_check","vessel_owner_check"]),
          ("vesselImo", "string", False),
          ("darkVesselVid", "string", False, None, "bridges aisDarkVessel.flagSanctionsEvasion"),
          ("attestedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCapBreach",
        "desc": "Price cap violation / attestation fraud / fronting (bridges aisDarkVessel.flagSanctionsEvasion + ofac-sanctions-sdn + commodity-trade)",
        "fields": [
          ("flagId", "string", True),
          ("attestationVid", "string", True, None, "bridges recordAttestation"),
          ("breachKind", "string", True, ["above_cap_sale","back_dated_invoice","attestation_forgery","fronting_entity","insurance_gap","stsless_traceable","uae_hub_routing","india_refining_loophole","hidden_profit_tranche"]),
          ("estPremiumUsd", "number", False),
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
            if ftype == "integer" and any(k in col for k in ["count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels"]):
                sql_t = "bigint"
            else:
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


for i, a in enumerate(ACTORS, start=1):
    bd=REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    ld=REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bd.mkdir(parents=True,exist_ok=True); ld.mkdir(parents=True,exist_ok=True)
    for m in a["methods"]:
        (ld/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bd/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    ddl = gen_ddl(a)
    out = Path(f"/tmp/wave13/w59_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
