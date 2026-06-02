#!/usr/bin/env python3
"""Wave 48 bridges — assistive tech / FedNow UPI / permafrost / energy poverty / Sendai."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "assistive-tech",
    "app": "assistiveTech",
    "methods": [
      {
        "name": "registerProduct",
        "desc": "Assistive tech / AT2030 / WHO GATE product (bridges digital-accessibility + accessibility-services + crc-children-digital + crpd-disability)",
        "fields": [
          ("productId", "string", True),
          ("manufacturerLei", "string", False),
          ("productKind", "string", True, ["hearing_aid","eyeglasses","wheelchair_manual","wheelchair_powered","prosthetic","screen_reader","aac","braille_display","mobility_cane","pill_organiser","environmental_control","smart_home_a11y"]),
          ("who_APL_listed", "boolean", False, None, "WHO Priority Assistive Products List"),
          ("isoTaxonomy", "string", False, None, "ISO 9999"),
          ("priceUsd", "number", False),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAccessGap",
        "desc": "Access gap / procurement failure / lack of training (bridges ocds-procurement + universal-health-coverage + just-transition)",
        "fields": [
          ("gapId", "string", True),
          ("productVid", "string", True, None, "bridges registerProduct"),
          ("countryIso3", "string", True),
          ("gapKind", "string", True, ["cost","procurement","training","supply_chain","repair","cultural_acceptability","digital_divide"]),
          ("unmetNeedPersons", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if unmetNeedPersons != null and unmetNeedPersons >= 1000000 then \"mass\" else if unmetNeedPersons != null and unmetNeedPersons >= 100000 then \"broad\" else \"targeted\"", ["targeted","broad","mass"]),
      },
    ],
  },
  {
    "slug": "instant-payments",
    "app": "instantPayments",
    "methods": [
      {
        "name": "registerRail",
        "desc": "Instant payment rail (FedNow / UPI / Pix / SEPA Inst / FAST SG / Zengin NT / DuitNow — bridges psd3-open-finance + cbdc + fatf-travel-rule + antitrust-dma)",
        "fields": [
          ("railId", "string", True),
          ("operatorLei", "string", False),
          ("railName", "string", True, ["fednow","upi","pix","sepa_inst","fast_sg","zengin_nt","duitnow","rtp_us","nnss_gb","target_ips","paynow"]),
          ("countryIso3", "string", True),
          ("launchedAt", "string", True),
          ("settlementCurrency", "string", False),
          ("maxTxnAmount", "number", False),
          ("targetSlaSec", "number", False),
        ],
        "classify": None,
      },
      {
        "name": "recordVolumeMetric",
        "desc": "Volume + fraud + interop metric (bridges psd3-open-finance + fair-pricing + icpen-consumer)",
        "fields": [
          ("metricId", "string", True),
          ("railVid", "string", True, None, "bridges registerRail"),
          ("periodMonth", "string", True),
          ("txnCount", "integer", False),
          ("valueUsd", "number", False),
          ("avgSettlementSec", "number", False),
          ("fraudLossBps", "number", False),
          ("crossBorderPct", "number", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("throughputTier", "if txnCount != null and txnCount >= 1000000000 then \"mega\" else if txnCount != null and txnCount >= 100000000 then \"high\" else if txnCount != null and txnCount >= 10000000 then \"moderate\" else \"low\"", ["low","moderate","high","mega"]),
      },
    ],
  },
  {
    "slug": "permafrost-thaw",
    "app": "permafrostThaw",
    "methods": [
      {
        "name": "recordMonitoringSite",
        "desc": "Permafrost monitoring site (CALM / TSP / GTN-P — bridges coastal-slr + methane-tracker + soil-carbon + arctic-nsr)",
        "fields": [
          ("siteId", "string", True),
          ("countryIso3", "string", True),
          ("latitude", "number", False),
          ("longitude", "number", False),
          ("altDepthM", "number", False, None, "active-layer depth"),
          ("surfaceTempC", "number", False),
          ("groundTempAt10mC", "number", False),
          ("permafrostZone", "string", False, ["continuous","discontinuous","sporadic","isolated"]),
          ("measuredYear", "integer", True),
          ("recordedAt", "string", True),
        ],
        "classify": ("degradationTier", "if groundTempAt10mC != null and groundTempAt10mC >= -1 then \"degrading\" else if groundTempAt10mC != null and groundTempAt10mC >= -3 then \"warming\" else \"stable\"", ["stable","warming","degrading"]),
      },
      {
        "name": "flagInfrastructureRisk",
        "desc": "Infrastructure at-risk from thaw (bridges power-grid-interconnect + rail-cross-border + telecom-infra + disaster-response)",
        "fields": [
          ("riskId", "string", True),
          ("siteVid", "string", True, None, "bridges recordMonitoringSite"),
          ("assetKind", "string", True, ["road","rail","pipeline","building","airport","tower","powerline","fiber","port"]),
          ("countryIso3", "string", True),
          ("criticalPopulation", "integer", False),
          ("estimatedDamageUsd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "energy-poverty",
    "app": "energyPoverty",
    "methods": [
      {
        "name": "recordHouseholdMetric",
        "desc": "Energy poverty / access (SDG 7.1 / IEA Access / EU EPAH — bridges universal-health-coverage + housing-affordability + urban-heat + climate-adaptation-finance)",
        "fields": [
          ("metricId", "string", True),
          ("countryIso3", "string", True),
          ("indicator", "string", True, ["electricity_access_pct","clean_cooking_access_pct","energy_expenditure_pct_income","tier_of_access","arrears_on_utility_bills_pct","unable_to_keep_home_warm_pct","unable_to_cool_home_pct"]),
          ("valueNumeric", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSubsidyProgram",
        "desc": "Energy subsidy / tariff protection program (bridges cofog + power-grid-interconnect + ocha-funding)",
        "fields": [
          ("programId", "string", True),
          ("metricVid", "string", False, None, "bridges recordHouseholdMetric"),
          ("countryIso3", "string", True),
          ("kind", "string", True, ["lump_sum","tariff_discount","weatherization","off_grid_subsidy","fuel_voucher","ev_charging","clean_cooking","retrofit_grant"]),
          ("annualSpendUsd", "number", False),
          ("beneficiaryHouseholds", "integer", False),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "sendai-drr",
    "app": "sendaiDrr",
    "methods": [
      {
        "name": "recordIndicatorProgress",
        "desc": "Sendai Framework DRR indicator (bridges disaster-response + cyclone-prepo + climate-adaptation-finance + sdg-reporting + extreme-weather-attribution)",
        "fields": [
          ("reportId", "string", True),
          ("countryIso3", "string", True),
          ("targetSendai", "string", True, ["A","B","C","D","E","F","G"]),
          ("indicator", "string", True, None, "A-1 to G-3 etc"),
          ("valueNumeric", "number", False),
          ("baselineValue", "number", False),
          ("targetValue2030", "number", False),
          ("reportingYear", "integer", True),
          ("reportedAt", "string", True),
        ],
        "classify": ("progressTier", "if valueNumeric != null and baselineValue != null and targetValue2030 != null and targetValue2030 != baselineValue and (valueNumeric - baselineValue) / (targetValue2030 - baselineValue) >= 0.7 then \"on_track\" else if valueNumeric != null and baselineValue != null and targetValue2030 != null and targetValue2030 != baselineValue and (valueNumeric - baselineValue) / (targetValue2030 - baselineValue) >= 0.3 then \"partial\" else \"off_track\"", ["off_track","partial","on_track"]),
      },
      {
        "name": "flagPolicyCoherence",
        "desc": "Sendai-Paris-SDG coherence policy breach (bridges unfccc-gst + sdg-reporting + biodiversity-gbf)",
        "fields": [
          ("flagId", "string", True),
          ("progressVid", "string", True, None, "bridges recordIndicatorProgress"),
          ("coherenceIssue", "string", True, ["sendai_paris_gap","drr_development","adaptation_drr","sdg_drr","budget_fragmentation"]),
          ("recommendationSummary", "string", False),
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
