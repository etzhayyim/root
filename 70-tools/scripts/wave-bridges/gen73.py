#!/usr/bin/env python3
"""Wave 73 — classification-review / transboundary-river / digital-public-infra / liquidity-facility / modern-slavery.

Bridges Wave 72:
- classification-review ↔ foiaTracker.flagResponseDelay
- transboundary-river ↔ waterStewardship.flagBasinStress
- digital-public-infra ↔ birthRegistration.flagRegistrationGap
- liquidity-facility ↔ digitalRunRisk.flagContagionRisk
- modern-slavery ↔ ftzZones.flagLabourAbuse
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "classification-review",
    "app": "classificationReview",
    "methods": [
      {
        "name": "recordMdrRequest",
        "desc": "Mandatory Declassification Review / ISCAP / FRUS (bridges foiaTracker.flagResponseDelay + ig-audit + press-freedom)",
        "fields": [
          ("requestId", "string", True),
          ("agency", "string", True, ["cia","doe","dia","dod","state","fbi","nga","nro","nsa","doj","white_house","nsc","oig","archives_nara"]),
          ("classificationLevel", "string", True, ["top_secret","secret","confidential","cui","sci","sap","nato_secret","rdy_eyes_only"]),
          ("reviewKind", "string", True, ["mdr","iscap_appeal","automatic_25_year","foia_exempt_b1","eo_13526","public_interest_declass","congressional_request","historical"]),
          ("responseDelayVid", "string", False, None, "bridges foiaTracker.flagResponseDelay"),
          ("requestedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagOverClassification",
        "desc": "Over-classification / sources-and-methods over-redaction (bridges foiaTracker.flagResponseDelay + ig-audit + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("requestVid", "string", True, None, "bridges recordMdrRequest"),
          ("issueKind", "string", True, ["over_classification","blanket_redaction","sources_methods_abuse","eo_13526_violation","b1_overreach","ambiguity_b5","post_disclosure_retro","excessive_review_queue","declassification_denied","congressional_gag"]),
          ("pagesRedacted", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "transboundary-river",
    "app": "transboundaryRiver",
    "methods": [
      {
        "name": "recordCommission",
        "desc": "Transboundary river / UN Watercourses Conv 1997 / treaty commission (bridges waterStewardship.flagBasinStress + land-tenure + biodiversity-gbf)",
        "fields": [
          ("commissionId", "string", True),
          ("basinName", "string", True),
          ("riparianCountriesIso3", "string", True),
          ("regimeKind", "string", True, ["un_watercourses_1997","helsinki_rules_1966","berlin_rules_2004","bilateral_treaty","commission_standing","icj_jurisdiction","coop_framework","mekong_1995","nile_cfa","indus_iwt","rhine_stephen"]),
          ("basinStressVid", "string", False, None, "bridges waterStewardship.flagBasinStress"),
          ("establishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRiparianDispute",
        "desc": "Upstream-downstream dispute / dam / withdrawal (bridges waterStewardship.flagBasinStress + civil-liability + disaster-response)",
        "fields": [
          ("flagId", "string", True),
          ("commissionVid", "string", True, None, "bridges recordCommission"),
          ("disputeKind", "string", True, ["upstream_dam","diversion","flow_below_minimum","data_sharing_refused","flood_release","navigation_blocked","sediment_blocked","pollution_upstream","colossal_withdrawal","aquifer_transnational","climate_scarcity"]),
          ("affectedPersons", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "digital-public-infra",
    "app": "digitalPublicInfra",
    "methods": [
      {
        "name": "recordDpiSystem",
        "desc": "Digital Public Infrastructure (MOSIP / Aadhaar / India Stack / EU Wallet / DIGIT — bridges birthRegistration.flagRegistrationGap + digital-identity + digital-public-goods)",
        "fields": [
          ("dpiId", "string", True),
          ("countryIso3", "string", True),
          ("systemKind", "string", True, ["mosip","aadhaar","india_stack_upi","eu_digital_wallet","modul_ua","digit_egov","code_dpi","brazil_lex","indonesia_osim","philippines_philid","sg_singpass","estonia_x_road"]),
          ("scope", "string", True, ["national_id","payments","data_exchange","consent_manager","health","tax","education","social_protection","property","elections","agriculture","msme","civil_registry"]),
          ("registrationGapVid", "string", False, None, "bridges birthRegistration.flagRegistrationGap"),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagExclusionRisk",
        "desc": "Exclusion / biometric failure / surveillance concern (bridges birthRegistration.flagRegistrationGap + consumer-protection + crpd-disability)",
        "fields": [
          ("flagId", "string", True),
          ("dpiVid", "string", True, None, "bridges recordDpiSystem"),
          ("riskKind", "string", True, ["biometric_failure","digital_divide","aadhaar_not_mandatory_but_is","single_point_of_failure","function_creep","surveillance","linkage_without_consent","disability_exclusion","elderly_exclusion","minority_language","rural_connectivity"]),
          ("personsExcluded", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "liquidity-facility",
    "app": "liquidityFacility",
    "methods": [
      {
        "name": "recordFacility",
        "desc": "Central bank liquidity facility / LOLR (bridges digitalRunRisk.flagContagionRisk + bankResolution + fx-swap-lines)",
        "fields": [
          ("facilityId", "string", True),
          ("centralBank", "string", True, ["fed","ecb","boj","boe","pboc","snb","boc_ca","rbi","rba","sebank","ringsnet","bcb","banxico","bsp","cbj"]),
          ("facilityKind", "string", True, ["discount_window","standing_lending","fhl_bank","bxl","bank_term_funding","emergency_authority","repo_operations","fx_swap","dollar_swap","targeted_ltro","special_liquidity"]),
          ("collateralKind", "string", False, ["high_quality_liquid_assets","agency_mbs","investment_grade_corporate","mortgage_loans","commercial_loans","sovereign","supranationals","gold","fx_receivables"]),
          ("contagionVid", "string", False, None, "bridges digitalRunRisk.flagContagionRisk"),
          ("openedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagStigmaEffect",
        "desc": "Stigma / counterparty risk / signal contamination (bridges digitalRunRisk.flagContagionRisk + bank-resolution + sovereign-debt)",
        "fields": [
          ("flagId", "string", True),
          ("facilityVid", "string", True, None, "bridges recordFacility"),
          ("concernKind", "string", True, ["stigma","too_narrow_haircuts","eligibility_too_restricted","daily_report_chilling","misreporting_access","interest_penal","withdrawal_run_on_access","counterparty_credit_risk","balance_sheet_footprint","moral_hazard"]),
          ("usagePremiumBps", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "modern-slavery",
    "app": "modernSlavery",
    "methods": [
      {
        "name": "recordDisclosure",
        "desc": "Modern slavery / forced labor disclosure (UK MSA / AU MSA / CA S-211 — bridges ftzZones.flagLabourAbuse + forced-labor + ilo-labor-rights)",
        "fields": [
          ("disclosureId", "string", True),
          ("entityLei", "string", False),
          ("regime", "string", True, ["uk_msa_s54","au_msa","ca_s211","nl_child_labor_due_dil","fr_vigilance","de_lksg","no_transparency","us_uflpa","us_cust_border_withhold","thailand_anti_trafficking","peru_vigilance"]),
          ("supplyChainScope", "string", True, ["tier_1_only","tier_2","tier_3","entire_value_chain","material_imports","high_risk_geographies","specific_commodity","finance_investments"]),
          ("labourAbuseVid", "string", False, None, "bridges ftzZones.flagLabourAbuse"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagInadequateDisclosure",
        "desc": "Statement inadequacy / tick-box / failure to act (bridges ftzZones.flagLabourAbuse + worker-grievance + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("disclosureVid", "string", True, None, "bridges recordDisclosure"),
          ("concernKind", "string", True, ["tick_box","no_victim_access","failure_to_act","risk_mapping_absent","no_remediation","no_enforcement","no_penalty","reactive_only","weak_supplier_engagement","audit_weakness","media_driven_only"]),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages"]):
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
    out = Path(f"/tmp/wave13/w73_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
