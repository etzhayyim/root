#!/usr/bin/env python3
"""Wave 49 bridges — semi-IP / green-steel / mRNA / judiciary / smart-grid."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "semi-ip-licensing",
    "app": "semiIpLicensing",
    "methods": [
      {
        "name": "recordLicense",
        "desc": "Semiconductor IP licensing (Arm / RISC-V / synopsys / cadence — bridges semiconductor-fab + ai-supply-chain + merger-review + mofcom-export-control)",
        "fields": [
          ("licenseId", "string", True),
          ("licensorLei", "string", False),
          ("licenseeLei", "string", False),
          ("ipCategory", "string", True, ["cpu_isa","gpu_ip","dsp","fpga","memory_controller","pcie","usb","display","analog","eda_tool","mixed_signal"]),
          ("feeStructure", "string", False, ["royalty_per_unit","lump_sum","subscription","hybrid"]),
          ("upfrontFeeUsd", "number", False),
          ("royaltyPct", "number", False),
          ("signedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagLitigation",
        "desc": "Semi IP litigation (bridges antitrust-dma + merger-review + mofcom-export-control + ustr-section-301)",
        "fields": [
          ("caseId", "string", True),
          ("licenseVid", "string", False, None, "bridges recordLicense"),
          ("venue", "string", False, ["itc_337","d_delaware","txsd","uk_patents","epo","upc","japan_ipdivision"]),
          ("claimKind", "string", True, ["patent_infringement","trade_secret","breach_of_license","fradua_on_patent_office","standard_essential"]),
          ("damagesSoughtUsd", "number", False),
          ("filedAt", "string", True),
        ],
        "classify": ("severityTier", "if damagesSoughtUsd != null and damagesSoughtUsd >= 1000000000 then \"bet_the_company\" else if damagesSoughtUsd != null and damagesSoughtUsd >= 100000000 then \"major\" else \"commercial\"", ["commercial","major","bet_the_company"]),
      },
    ],
  },
  {
    "slug": "green-steel",
    "app": "greenSteel",
    "methods": [
      {
        "name": "recordProductionMetric",
        "desc": "Green steel production metric (ResponsibleSteel / GSC / Breakthrough Agenda — bridges hydrogen-economy + climate-carbon-market + eu-cbam + critical-minerals)",
        "fields": [
          ("metricId", "string", True),
          ("plantLei", "string", False),
          ("countryIso3", "string", True),
          ("route", "string", True, ["bf_bof","eaf_scrap","dri_ng","dri_h2","hisarna","ulcored","molten_oxide_electrolysis"]),
          ("annualOutputTonnes", "number", True),
          ("scope1IntensityTco2eT", "number", False),
          ("scope2IntensityTco2eT", "number", False),
          ("recycledContentPct", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("greenTier", "if route = \"dri_h2\" or route = \"molten_oxide_electrolysis\" then \"near_zero\" else if route = \"eaf_scrap\" then \"low_carbon\" else if route = \"dri_ng\" or route = \"hisarna\" then \"transitional\" else \"legacy\"", ["legacy","transitional","low_carbon","near_zero"]),
      },
      {
        "name": "registerOfftake",
        "desc": "Green steel offtake agreement (auto / construction / renewables)",
        "fields": [
          ("agreementId", "string", True),
          ("metricVid", "string", True, None, "bridges recordProductionMetric"),
          ("offtakerLei", "string", False),
          ("sector", "string", True, ["automotive","construction","wind_tower","rail","shipping","consumer_goods","appliances"]),
          ("annualVolumeTonnes", "number", True),
          ("premiumUsdTonne", "number", False),
          ("signedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "mrna-vaccine-hub",
    "app": "mrnaVaccineHub",
    "methods": [
      {
        "name": "registerHub",
        "desc": "mRNA vaccine technology transfer hub (WHO / Afrigen / BioNTainer — bridges vaccine-equity + pandemic-preparedness + pharma-supply + pandemic-treaty)",
        "fields": [
          ("hubId", "string", True),
          ("operatorLei", "string", False),
          ("countryIso3", "string", True),
          ("hostInstitution", "string", True),
          ("spokeCountriesIso3", "string", False, None, "comma"),
          ("capacityDosesPerYear", "integer", False),
          ("technologyBasis", "string", False, ["afrigen","biontainer","cureVac","selfamplifying"]),
          ("commissionedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagTechnologyTransferGap",
        "desc": "Tech transfer gap / IP barrier (bridges itpgrfa-seeds + pandemic-treaty + global-tax)",
        "fields": [
          ("gapId", "string", True),
          ("hubVid", "string", True, None, "bridges registerHub"),
          ("gapKind", "string", True, ["ip_barrier","know_how","facility","regulatory","workforce","raw_materials","cold_chain"]),
          ("bilateralRelationship", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "judiciary-independence",
    "app": "judiciaryIndependence",
    "methods": [
      {
        "name": "recordIndex",
        "desc": "Judicial independence index (WJP Rule of Law / V-Dem / Freedom House — bridges press-freedom + religious-freedom + climate-litigation + election-integrity)",
        "fields": [
          ("recordId", "string", True),
          ("countryIso3", "string", True),
          ("indexProvider", "string", True, ["wjp_roli","v_dem","freedom_house","bertelsmann_bti","world_bank_ctrl_corruption"]),
          ("dimensionScore", "number", False),
          ("cursorYear", "integer", True),
          ("rankGlobal", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("independenceTier", "if dimensionScore != null and dimensionScore >= 0.8 then \"strong\" else if dimensionScore != null and dimensionScore >= 0.5 then \"moderate\" else \"weak\"", ["weak","moderate","strong"]),
      },
      {
        "name": "flagCourtPackingEvent",
        "desc": "Court packing / judge removal / constitutional reform (bridges religious-freedom + press-freedom + climate-litigation)",
        "fields": [
          ("eventId", "string", True),
          ("indexVid", "string", False, None, "bridges recordIndex"),
          ("countryIso3", "string", True),
          ("eventKind", "string", True, ["court_packing","mandatory_retirement","judge_dismissal","jurisdiction_stripping","amnesty_law","extraordinary_court"]),
          ("affectedJudges", "integer", False),
          ("occurredAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "smart-grid-cyber",
    "app": "smartGridCyber",
    "methods": [
      {
        "name": "recordSecurityPosture",
        "desc": "Smart grid security posture (NERC CIP / ENISA / EN IEC 62443 — bridges cyber-resilience-stress + power-grid-interconnect + digital-twin-city + quantum-safe-crypto)",
        "fields": [
          ("postureId", "string", True),
          ("operatorLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("framework", "string", True, ["nerc_cip","enisa_nis2_energy","iec_62443","iec_62351","ieee_1686","german_it_sig","jp_cip"]),
          ("assetCategory", "string", False, ["transmission","distribution","generation","scada","ami","der_aggregator","ev_chargers"]),
          ("maturityLevel", "integer", False, None, "1-5"),
          ("audiencedAt", "string", True),
        ],
        "classify": ("maturityTier", "if maturityLevel != null and maturityLevel >= 4 then \"hardened\" else if maturityLevel != null and maturityLevel >= 3 then \"managed\" else \"reactive\"", ["reactive","managed","hardened"]),
      },
      {
        "name": "flagOtIncident",
        "desc": "OT / SCADA grid incident (bridges cyber-incident + telecom-infra + ai-governance)",
        "fields": [
          ("incidentId", "string", True),
          ("postureVid", "string", True, None, "bridges recordSecurityPosture"),
          ("incidentKind", "string", True, ["ransomware","wiper","sabotage","misconfiguration","insider","supply_chain","physical","nation_state_apt"]),
          ("affectedCustomers", "integer", False),
          ("durationHours", "number", False),
          ("attributionSuspected", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if affectedCustomers != null and affectedCustomers >= 1000000 then \"critical\" else if affectedCustomers != null and affectedCustomers >= 100000 then \"severe\" else if affectedCustomers != null and affectedCustomers >= 10000 then \"major\" else \"minor\"", ["minor","major","severe","critical"]),
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
            # Use bigint for count-style fields to avoid int32 overflow (Wave 48 lesson)
            if ftype == "integer" and any(k in col for k in ["count","doses_per","customers","beneficiar","units","tonnes","volume","persons","capacity"]):
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


for a in ACTORS:
    bd=REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    ld=REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bd.mkdir(parents=True,exist_ok=True); ld.mkdir(parents=True,exist_ok=True)
    for m in a["methods"]:
        (ld/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bd/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    print(gen_ddl(a))
