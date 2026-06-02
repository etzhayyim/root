#!/usr/bin/env python3
"""Wave 47 bridges — ECMWF / EUDR / offshore wind / OCDS / RASFF."""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "ecmwf-forecast",
    "app": "ecmwfForecast",
    "methods": [
      {
        "name": "recordForecastSkill",
        "desc": "ECMWF IFS / GraphCast / Pangu-Weather / FourCastNet forecast skill (bridges cyclone-prepo + disaster-response + agri-food-security + extreme-weather-attribution)",
        "fields": [
          ("skillId", "string", True),
          ("model", "string", True, ["ecmwf_ifs","nwp_icon","gfs","graphcast","pangu_weather","fourcastnet","aurora","aifs"]),
          ("variable", "string", True, ["t2m","mslp","z500","t850","u10","v10","tp","sst"]),
          ("leadTimeHours", "integer", True),
          ("acc", "number", False, None, "Anomaly Correlation Coefficient"),
          ("rmse", "number", False),
          ("crps", "number", False),
          ("evaluationPeriod", "string", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("skillTier", "if acc != null and acc >= 0.9 then \"high\" else if acc != null and acc >= 0.7 then \"useful\" else \"limited\"", ["limited","useful","high"]),
      },
      {
        "name": "flagExtremeHitMiss",
        "desc": "Extreme weather hit / miss / false alarm (bridges extreme-weather-attribution + cyclone-prepo + disaster-response)",
        "fields": [
          ("eventId", "string", True),
          ("skillVid", "string", False, None, "bridges recordForecastSkill"),
          ("extremeKind", "string", True, ["heatwave","coldsnap","cyclone","flood","drought","wildfire_risk","wind_storm"]),
          ("outcome", "string", True, ["hit","miss","false_alarm","correct_negative"]),
          ("leadTimeHours", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "eudr-deforestation",
    "app": "eudrDeforestation",
    "methods": [
      {
        "name": "recordDueDiligence",
        "desc": "EUDR Reg 2023/1115 / US FOREST Act / UK Sch 17 due-diligence statement (bridges forestry-mrv + seafood-traceability + customs-clearance + textile-circularity)",
        "fields": [
          ("statementId", "string", True),
          ("operatorLei", "string", False),
          ("regime", "string", True, ["eu_eudr","us_forest_act","uk_schedule_17","kr_smdi","au_illegal_logging"]),
          ("commodityHs", "string", True),
          ("commodityName", "string", True, ["cattle","cocoa","coffee","oil_palm","rubber","soy","wood","leather","charcoal","printed_paper"]),
          ("originCountryIso3", "string", False),
          ("geolocationHectares", "number", False),
          ("deforestationFreeCertPresent", "boolean", False),
          ("submittedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMisalignment",
        "desc": "EUDR alignment breach (bridges forestry-mrv + indigenous-rights + forced-labor + ofac-sanctions)",
        "fields": [
          ("breachId", "string", True),
          ("statementVid", "string", True, None, "bridges recordDueDiligence"),
          ("issueKind", "string", True, ["cutoff_date_breach","plot_overlap","supplier_risk","human_rights","benchmarking_high_risk","false_geolocation","no_traceability"]),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if issueKind = \"cutoff_date_breach\" or issueKind = \"human_rights\" then \"severe\" else if issueKind = \"plot_overlap\" or issueKind = \"benchmarking_high_risk\" then \"significant\" else \"minor\"", ["minor","significant","severe"]),
      },
    ],
  },
  {
    "slug": "offshore-wind",
    "app": "offshoreWind",
    "methods": [
      {
        "name": "registerLease",
        "desc": "Offshore wind lease / seabed auction (BOEM / Crown Estate / TenneT — bridges power-grid-interconnect + hydrogen-economy + bbnj-highseas + mpa-effectiveness)",
        "fields": [
          ("leaseId", "string", True),
          ("lessor", "string", True, ["boem","crown_estate","tennet","4coffshore","bsh","japan_meti","kepco","stateoceanic_adm"]),
          ("leaseeLei", "string", False),
          ("countryIso3", "string", True),
          ("areaKm2", "number", False),
          ("capacityMw", "number", False),
          ("auctionPriceUsdKw", "number", False),
          ("cod", "string", False, None, "commercial operation date"),
          ("leasedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagConstructionDelay",
        "desc": "Construction delay / supply chain risk (bridges telecom-infra + critical-minerals + battery-passport + semiconductor-fab)",
        "fields": [
          ("delayId", "string", True),
          ("leaseVid", "string", True, None, "bridges registerLease"),
          ("delayKind", "string", True, ["permits","supply_chain","vessels","labor","subsea_cable","transformer","turbine_recall","foundation","grid_connection"]),
          ("monthsDelay", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if monthsDelay != null and monthsDelay >= 24 then \"major\" else if monthsDelay != null and monthsDelay >= 6 then \"moderate\" else \"minor\"", ["minor","moderate","major"]),
      },
    ],
  },
  {
    "slug": "ocds-procurement",
    "app": "ocdsProcurement",
    "methods": [
      {
        "name": "publishTender",
        "desc": "OCDS 1.2 / TED EU / WTO GPA procurement tender (bridges merger-review + cbam-extension + fair-pricing + antitrust-dma)",
        "fields": [
          ("ocid", "string", True, None, "OCDS open-contracting identifier"),
          ("buyerLei", "string", False),
          ("jurisdictionIso3", "string", True),
          ("procurementStage", "string", True, ["planning","tender","award","contract","implementation"]),
          ("estimatedValueUsd", "number", False),
          ("procurementMethod", "string", False, ["open","selective","limited","direct","framework_agreement","dynamic_purchasing"]),
          ("mainCategoryCpv", "string", False),
          ("publishedAt", "string", True),
        ],
        "classify": ("scaleTier", "if estimatedValueUsd != null and estimatedValueUsd >= 100000000 then \"mega\" else if estimatedValueUsd != null and estimatedValueUsd >= 10000000 then \"large\" else if estimatedValueUsd != null and estimatedValueUsd >= 1000000 then \"mid\" else \"small\"", ["small","mid","large","mega"]),
      },
      {
        "name": "flagRedFlag",
        "desc": "Procurement red-flag (single bid / rapid award / amendment — bridges fair-pricing + antitrust-dma + religious-freedom)",
        "fields": [
          ("flagId", "string", True),
          ("tenderVid", "string", True, None, "bridges publishTender"),
          ("redFlagKind", "string", True, ["single_bid","rapid_award","amendment_surge","pep_link","sanctions_link","price_jump","direct_award_threshold","specification_tailoring"]),
          ("auditorLei", "string", False),
          ("flaggedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "rasff-food-safety",
    "app": "rasffFoodSafety",
    "methods": [
      {
        "name": "recordAlert",
        "desc": "EU RASFF / INFOSAN / FAO IPC food safety alert (bridges chemicals-management + livestock-antibiotics + pharma-supply + icpen-consumer)",
        "fields": [
          ("alertId", "string", True),
          ("network", "string", True, ["rasff","infosan","fao_ipc","fda_imports","ciqa","mhlw_import"]),
          ("classification", "string", True, ["alert","border_rejection","information_attention","information_follow_up","news","notification"]),
          ("productCategory", "string", True),
          ("hazardCategory", "string", False, ["microbiological","pesticide","heavy_metal","mycotoxin","allergen","food_additive","foreign_body","veterinary_residue","composition"]),
          ("originCountryIso3", "string", False),
          ("notifiedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordRecallAction",
        "desc": "Recall / withdrawal action (bridges gigWorker + pharma-supply + icpen-consumer)",
        "fields": [
          ("recallId", "string", True),
          ("alertVid", "string", True, None, "bridges recordAlert"),
          ("operatorLei", "string", False),
          ("scopeCountries", "string", False, None, "ISO3 comma"),
          ("affectedUnits", "integer", False),
          ("actionClass", "string", True, ["class_i","class_ii","class_iii"], "FDA recall class"),
          ("issuedAt", "string", True),
        ],
        "classify": ("severityTier", "if actionClass = \"class_i\" then \"critical\" else if actionClass = \"class_ii\" then \"severe\" else \"minor\"", ["minor","severe","critical"]),
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
