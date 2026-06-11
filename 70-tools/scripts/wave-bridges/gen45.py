#!/usr/bin/env python3
"""Wave 45 bridges — Artemis / NCMEC / ICGC / QKD / sandbox."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "artemis-lunar",
    "app": "artemisLunar",
    "methods": [
      {
        "name": "recordMissionActivity",
        "desc": "Artemis Accords / Moon Treaty / COPUOS resource activity (bridges space-traffic + orbital-debris + critical-minerals + iaea-safeguards)",
        "fields": [
          ("activityId", "string", True),
          ("signatoryIso3", "string", True),
          ("missionName", "string", True),
          ("activityKind", "string", True, ["landing","sample_return","resource_extraction","habitat","power","refueling","scientific","rover_ops","constellation_ops"]),
          ("locationBody", "string", True, ["moon","mars","asteroid","europa","titan","other"]),
          ("coordinates", "string", False),
          ("peacefulUseDeclared", "boolean", False),
          ("startedAt", "string", True),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSafetyZoneOverlap",
        "desc": "Artemis safety zone overlap / conflict (bridges space-traffic + orbital-debris + laws-autonomous-weapons)",
        "fields": [
          ("conflictId", "string", True),
          ("activityVid", "string", True, None, "bridges recordMissionActivity"),
          ("overlappingSignatoryIso3", "string", True),
          ("issueKind", "string", True, ["safety_zone_overlap","heritage_site","resource_claim","mining_dispute","traffic_management","communications_interference"]),
          ("copuosWorkingGroup", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("escalationTier", "if issueKind = \"resource_claim\" or issueKind = \"mining_dispute\" then \"critical\" else if issueKind = \"safety_zone_overlap\" or issueKind = \"heritage_site\" then \"severe\" else \"routine\"", ["routine","severe","critical"]),
      },
    ],
  },
  {
    "slug": "ncmec-csam",
    "app": "ncmecCsam",
    "methods": [
      {
        "name": "recordReportVolume",
        "desc": "NCMEC CyberTipline / INHOPE hotline report volume (bridges misinformation-observatory + crc-children-digital + uasc-protection + icpen-consumer)",
        "fields": [
          ("reportId", "string", True),
          ("platformLei", "string", False),
          ("reportingYear", "integer", True),
          ("reportType", "string", True, ["csam","csai_ai_generated","online_enticement","child_sex_trafficking","child_sexual_molestation","sextortion","misleading_domain"]),
          ("reportsCount", "integer", True),
          ("uniqueImagesCount", "integer", False),
          ("uniqueVideosCount", "integer", False),
          ("aiGeneratedPctEstimate", "number", False),
          ("submittedAt", "string", True),
        ],
        "classify": ("scaleTier", "if reportsCount >= 10000000 then \"mass\" else if reportsCount >= 1000000 then \"major\" else if reportsCount >= 10000 then \"significant\" else \"limited\"", ["limited","significant","major","mass"]),
      },
      {
        "name": "flagEnforcementGap",
        "desc": "EU CSAM regulation / UK OSA / US EARN IT enforcement gap (bridges misinformation-observatory + antitrust-dma + digital-accessibility)",
        "fields": [
          ("gapId", "string", True),
          ("reportVid", "string", False, None, "bridges recordReportVolume"),
          ("jurisdictionIso3", "string", True),
          ("regime", "string", True, ["eu_csam_reg","uk_osa","us_earn_it","us_kosa","au_osa","sg_online_safety","jp_code"]),
          ("gapKind", "string", True, ["hash_list","scanning_obligation","proactive_detection","age_gate","appeals","transparency","platform_liability"]),
          ("flaggedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "icgc-genomic",
    "app": "icgcGenomic",
    "methods": [
      {
        "name": "registerCohort",
        "desc": "ICGC-ARGO / TCGA / UK Biobank / AoU cohort (bridges precision-medicine + fhir-health-data + pandemic-treaty + vaccine-equity)",
        "fields": [
          ("cohortId", "string", True),
          ("programLei", "string", False),
          ("cohortName", "string", True),
          ("participantsCount", "integer", False),
          ("platform", "string", True, ["wgs","wes","rna_seq","methylome","proteome","single_cell","targeted_panel"]),
          ("consentModel", "string", False, ["broad","tiered","dynamic","open","indigenous_collective"]),
          ("datasetAccessModel", "string", False, ["open","controlled","federated","dac_review"]),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordClinvarSubmission",
        "desc": "ClinVar / HGVS variant submission (bridges pharma-supply + universal-health-coverage)",
        "fields": [
          ("submissionId", "string", True),
          ("cohortVid", "string", False, None, "bridges registerCohort"),
          ("variantHgvs", "string", True),
          ("clinicalSignificance", "string", True, ["benign","likely_benign","uncertain","likely_pathogenic","pathogenic","conflicting","risk_factor","drug_response"]),
          ("reviewStatus", "string", False, ["expert_panel","single_submitter","multi_submitter","no_assertion","criteria_only"]),
          ("submittedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "qkd-quantum",
    "app": "qkdQuantum",
    "methods": [
      {
        "name": "registerLink",
        "desc": "Quantum key distribution link (ETSI QKD 014 / CEN CENELEC / IEEE P1913 — bridges quantum-safe-crypto + telecom-infra + cable-repair-fleet + space-traffic)",
        "fields": [
          ("linkId", "string", True),
          ("operatorLei", "string", False),
          ("linkKind", "string", True, ["terrestrial_fiber","free_space","satellite_downlink","satellite_interlink","underwater_cable","hybrid"]),
          ("endpointACountryIso3", "string", True),
          ("endpointBCountryIso3", "string", True),
          ("distanceKm", "number", False),
          ("qberEstimatePct", "number", False, None, "Quantum Bit Error Rate"),
          ("secureKeyRateKbps", "number", False),
          ("protocolFamily", "string", False, ["bb84","e91","mdi_qkd","twin_field","cv_qkd"]),
          ("commissionedAt", "string", True),
        ],
        "classify": ("robustnessTier", "if secureKeyRateKbps != null and secureKeyRateKbps >= 10 then \"production\" else if secureKeyRateKbps != null and secureKeyRateKbps >= 1 then \"operational\" else \"experimental\"", ["experimental","operational","production"]),
      },
      {
        "name": "flagLinkIncident",
        "desc": "QKD link incident (side-channel / interception / hardware — bridges cyber-incident + quantum-safe-crypto + space-weather)",
        "fields": [
          ("incidentId", "string", True),
          ("linkVid", "string", True, None, "bridges registerLink"),
          ("incidentKind", "string", True, ["side_channel","photon_number_splitting","trojan_horse","detector_blinding","hardware_failure","geomagnetic_storm","polarization_drift"]),
          ("keyBatchCompromised", "boolean", False),
          ("spaceWxEventVid", "string", False, None, "bridges open-space-weather"),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "regulatory-sandbox",
    "app": "regulatorySandbox",
    "methods": [
      {
        "name": "registerCohort",
        "desc": "Regulatory sandbox cohort (FCA / MAS / BNM / JP FinTech / IN RBI — bridges psd3-open-finance + mica-crypto + fatf-travel-rule + ai-governance)",
        "fields": [
          ("cohortId", "string", True),
          ("regulatorLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("sandboxProgram", "string", True, ["fca_uk","mas_sg","bnm_my","ruby_jp","rbi_in","cftc_us","cnbv_mx","sbv_vn","cbiraq","globa_globalfinregsb"]),
          ("themeFocus", "string", True, ["open_finance","ai_model_risk","defi_stablecoin","digital_id","insurtech","regtech","tokenization","climate_fintech","inclusion"]),
          ("cohortSize", "integer", False),
          ("startedAt", "string", True),
          ("closedAt", "string", False),
        ],
        "classify": None,
      },
      {
        "name": "recordTestOutcome",
        "desc": "Sandbox test outcome (bridges ai-governance + cyber-resilience-stress + icpen-consumer)",
        "fields": [
          ("outcomeId", "string", True),
          ("cohortVid", "string", True, None, "bridges registerCohort"),
          ("participantLei", "string", False),
          ("product", "string", True),
          ("outcomeKind", "string", True, ["graduated","authorised","withdrawn","extended","failed","discontinued"]),
          ("consumerHarmFound", "boolean", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("valueTier", "if outcomeKind = \"authorised\" or outcomeKind = \"graduated\" then \"positive\" else if outcomeKind = \"extended\" then \"iterating\" else \"halted\"", ["halted","iterating","positive"]),
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
