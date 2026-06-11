#!/usr/bin/env python3
"""Wave 71 — ig-audit / sbtn-target / stateless-person / deposit-insurance / cumulation-rule.

Bridges Wave 70:
- ig-audit ↔ ethicsWaiver.flagConflictWaived
- sbtn-target ↔ tnfdDisclosure.flagGreenwash
- stateless-person ↔ asylumDetermination.flagProtectionGap
- deposit-insurance ↔ bankResolution.flagBailInDispute
- cumulation-rule ↔ rulesOfOrigin.flagRooFraud
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "ig-audit",
    "app": "igAudit",
    "methods": [
      {
        "name": "recordReport",
        "desc": "Inspector General audit / GAO / OMB A-123 report (bridges ethicsWaiver.flagConflictWaived + enforcement-action + ethics-disclosure)",
        "fields": [
          ("reportId", "string", True),
          ("agency", "string", True, ["dod_ig","state_ig","hhs_ig","dhs_oig","ed_ig","treasury_ig","usaid_ig","gao","oig_ep","nsa_ig","cia_ig","tigta","sigar","sigir","sigtarp"]),
          ("auditKind", "string", True, ["financial","performance","inspection","evaluation","criminal_referral","quicklook","cross_agency","whistleblower_investigation","management_alert","programmatic"]),
          ("waiverVid", "string", False, None, "bridges ethicsWaiver.flagConflictWaived"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRecommendationStall",
        "desc": "Recommendation stall / agency disagreement / retaliation (bridges ethicsWaiver.flagConflictWaived + enforcement-action + whistleblower-protect)",
        "fields": [
          ("flagId", "string", True),
          ("reportVid", "string", True, None, "bridges recordReport"),
          ("stallKind", "string", True, ["recommendations_ignored","agency_disagreement","redaction_excess","ig_removed","shadow_investigation","budget_defunded","staff_retaliation","classification_misused","legal_hold_abused","congressional_gag"]),
          ("openRecommendations", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "sbtn-target",
    "app": "sbtnTarget",
    "methods": [
      {
        "name": "recordTarget",
        "desc": "Science-Based Targets for Nature target (bridges tnfdDisclosure.flagGreenwash + biodiversity-gbf + climate-value-chain)",
        "fields": [
          ("targetId", "string", True),
          ("companyLei", "string", False),
          ("realm", "string", True, ["freshwater","land","ocean","biodiversity_integrated","climate","pollution"]),
          ("pressureKind", "string", True, ["water_withdrawal","water_pollution","land_footprint","deforestation","ocean_use","noise_pollution","light","agri_chemical","plastic"]),
          ("baselineYear", "integer", False),
          ("targetYear", "integer", False),
          ("greenwashVid", "string", False, None, "bridges tnfdDisclosure.flagGreenwash"),
          ("validatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMiss",
        "desc": "SBTN miss / withdrawal / boundary violation (bridges tnfdDisclosure.flagGreenwash + climate-value-chain + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("targetVid", "string", True, None, "bridges recordTarget"),
          ("missKind", "string", True, ["target_withdrawn","behind_trajectory","baseline_revised","scope_3_excluded","absolute_cap_breach","ar5_ar6_drift","water_basin_exceed","scenario_inconsistent","offset_reliance","renewed_non_committed"]),
          ("deltaPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "stateless-person",
    "app": "statelessPerson",
    "methods": [
      {
        "name": "recordProtection",
        "desc": "Statelessness protection / 1954/1961 UN Convention (bridges asylumDetermination.flagProtectionGap + refugee-unhcr + labour-mobility)",
        "fields": [
          ("protectionId", "string", True),
          ("hostCountryIso3", "string", True),
          ("originDescriptor", "string", True, ["de_jure","de_facto","inter_generation","post_soviet_succession","rohingya","bidun","kurds","nubia","haitian_dr","dominican_bateyes","nepal_madhesi","north_koreans_usa","discrimination_gender","discrimination_religion"]),
          ("regime", "string", True, ["1954_convention","1961_convention","eu_directive","national_proof","unhcr_mandate","admin_determination","host_sop","observed_status"]),
          ("protectionGapVid", "string", False, None, "bridges asylumDetermination.flagProtectionGap"),
          ("recognizedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagGapOutcome",
        "desc": "Unresolved / gender-based / birth registration gap (bridges asylumDetermination.flagProtectionGap + worker-grievance + gender-inclusion)",
        "fields": [
          ("flagId", "string", True),
          ("protectionVid", "string", True, None, "bridges recordProtection"),
          ("gapKind", "string", True, ["gender_national_transfer","birth_unregistered","ethnic_majority_rule","religion_bar","succession_gap","documentation_destroyed","deportation_limbo","access_to_education","healthcare_bar","marriage_annulled","property_bar"]),
          ("personsEstimated", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "deposit-insurance",
    "app": "depositInsurance",
    "methods": [
      {
        "name": "recordScheme",
        "desc": "Deposit insurance scheme (FDIC / DGS / IADI — bridges bankResolution.flagBailInDispute + banking-account + sovereign-guarantee)",
        "fields": [
          ("schemeId", "string", True),
          ("schemeKind", "string", True, ["fdic","fslic_legacy","eu_dgsd","uk_fscs","jp_dic","ca_cdic","au_fcs","mx_ipab","br_fgc","cn_dis","ru_asv","sg_sdic","kr_kdic","in_dicgc"]),
          ("countryIso3", "string", True),
          ("coverageLimitUsd", "number", False),
          ("bailInVid", "string", False, None, "bridges bankResolution.flagBailInDispute"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCoverageRisk",
        "desc": "Coverage inadequacy / systemic bank expansion / FDIC SRE (bridges bankResolution.flagBailInDispute + sovereign-debt + subordinated-debt)",
        "fields": [
          ("flagId", "string", True),
          ("schemeVid", "string", True, None, "bridges recordScheme"),
          ("issueKind", "string", True, ["limit_too_low_given_inflation","uninsured_concentration","systemic_exception","recapitalization_needed","cross_border_double","foreign_branches","shadow_banking_deposit","sbl_subsidiary","fintech_non_member","digital_fast_outflow"]),
          ("estExposureBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cumulation-rule",
    "app": "cumulationRule",
    "methods": [
      {
        "name": "recordCumulationScheme",
        "desc": "FTA cumulation scheme (bilateral / diagonal / full — bridges rulesOfOrigin.flagRooFraud + customs-declaration + trade-remedy)",
        "fields": [
          ("schemeId", "string", True),
          ("cumulationKind", "string", True, ["bilateral","diagonal","full","extended","pem_convention","sadc_tripartite","asean_plus_one","cptpp_cum","ftaap","across_agreements","regional_value"]),
          ("partnersIso3", "string", True),
          ("eligibleSectors", "string", False),
          ("rooFraudVid", "string", False, None, "bridges rulesOfOrigin.flagRooFraud"),
          ("enteredForceAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagExploitation",
        "desc": "Cumulation exploitation / backdoor origin (bridges rulesOfOrigin.flagRooFraud + transshipment-evasion + trade-remedy)",
        "fields": [
          ("flagId", "string", True),
          ("schemeVid", "string", True, None, "bridges recordCumulationScheme"),
          ("exploitKind", "string", True, ["backdoor_origin","tariff_line_jump","min_processing_exploit","labour_fragmentation","cost_allocation_gaming","de_minimis_trick","hub_hosting","third_country_laundering","sanitary_circumvention","unclear_full_vs_bilateral"]),
          ("estEvadedDutyMusd", "number", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps"]):
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
    out = Path(f"/tmp/wave13/w71_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
