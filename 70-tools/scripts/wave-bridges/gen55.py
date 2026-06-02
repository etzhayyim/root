#!/usr/bin/env python3
"""Wave 55 — gsp-eligibility / import-refusal / treasury-rulemaking / imf-article-iv / marine-heatwave.

Bridges Wave 54:
- gsp-eligibility ↔ tripsWaiver.flagRetaliationRisk
- import-refusal ↔ residueMrl.flagMrlBreach
- treasury-rulemaking ↔ iraTaxCredit.flagFeocDisqualification
- imf-article-iv ↔ emFxReserves.flagReserveAdequacy
- marine-heatwave ↔ coralReefBleaching.flagMortalityRisk
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "gsp-eligibility",
    "app": "gspEligibility",
    "methods": [
      {
        "name": "recordEligibilityReview",
        "desc": "US/EU/UK GSP trade preference eligibility review (bridges tripsWaiver.flagRetaliationRisk + ustr-section-301 + wto-dispute)",
        "fields": [
          ("reviewId", "string", True),
          ("programKind", "string", True, ["us_gsp","eu_gsp_plus","eu_ebe","uk_dcts","japan_gsp","canada_gpt","australia_dcs","china_ldc"]),
          ("beneficiaryCountryIso3", "string", True),
          ("reviewTrigger", "string", True, ["petition","self_initiated","annual","statutory_graduation","labor_rights","ip_protection","market_access"]),
          ("retaliationVid", "string", False, None, "bridges tripsWaiver.flagRetaliationRisk"),
          ("initiatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagEligibilityRemoval",
        "desc": "Preference suspension / country graduation / de-listing (bridges tripsWaiver.flagRetaliationRisk + wto-dispute + labour-mobility)",
        "fields": [
          ("flagId", "string", True),
          ("reviewVid", "string", True, None, "bridges recordEligibilityReview"),
          ("removalKind", "string", True, ["full_suspension","partial_withdrawal","product_specific","competitive_need","graduation","ip_failure","labor_failure","corruption"]),
          ("affectedTradeMusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "import-refusal",
    "app": "importRefusal",
    "methods": [
      {
        "name": "recordRefusal",
        "desc": "FDA import refusal / EU RASFF rejection / CBP hold (bridges residueMrl.flagMrlBreach + rasff-food-safety + fda-adufa)",
        "fields": [
          ("refusalId", "string", True),
          ("borderAgency", "string", True, ["fda","usda_fsis","cbp","eu_rasff","cfia_canada","jma_japan","mhlw_japan","aqsiq_china","fssai_india"]),
          ("originCountryIso3", "string", True),
          ("destinationCountryIso3", "string", True),
          ("productCategory", "string", True, ["seafood","fresh_produce","meat_poultry","dairy","dietary_supplement","spice","processed","beverage","infant_formula","medical_device"]),
          ("violationKind", "string", True, ["pesticide_residue","veterinary_residue","microbial","heavy_metal","aflatoxin","adulteration","unapproved_additive","labeling","allergen","radiological"]),
          ("mrlBreachVid", "string", False, None, "bridges residueMrl.flagMrlBreach"),
          ("shipmentValueUsd", "number", False),
          ("refusedAt", "string", True),
        ],
        "classify": ("severityTier", "if violationKind = \"microbial\" or violationKind = \"aflatoxin\" or violationKind = \"heavy_metal\" then \"high\" else if violationKind = \"pesticide_residue\" or violationKind = \"veterinary_residue\" then \"medium\" else \"low\"", ["low","medium","high"]),
      },
      {
        "name": "flagRecurringOrigin",
        "desc": "Recurring origin-country refusal pattern (bridges residueMrl.flagMrlBreach + trade-sanitary + wto-dispute)",
        "fields": [
          ("patternId", "string", True),
          ("refusalVid", "string", True, None, "bridges recordRefusal"),
          ("refusalsLast12mo", "integer", False),
          ("concernKind", "string", True, ["systemic_origin","producer_cluster","single_violator","seasonal","climate_related","emerging_compound","sanitary_phytosanitary"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "treasury-rulemaking",
    "app": "treasuryRulemaking",
    "methods": [
      {
        "name": "recordRule",
        "desc": "US Treasury / IRS Notice / NPRM / final rule (bridges iraTaxCredit.flagFeocDisqualification + IRA implementation + APA)",
        "fields": [
          ("ruleId", "string", True),
          ("agency", "string", True, ["treasury","irs","ofac","fincen","occ","fsoc","cfius","bea"]),
          ("ruleType", "string", True, ["notice","nprm","temp_final","final_rule","direct_final","guidance","revenue_procedure","private_letter"]),
          ("subjectArea", "string", True, ["ira_45x","ira_45v","ira_45q","ira_45y","cfius_review","bsa_aml","sanctions","beneficial_ownership","digital_asset","foreign_trust","cbdc"]),
          ("feocFlagVid", "string", False, None, "bridges iraTaxCredit.flagFeocDisqualification"),
          ("federalRegisterNo", "string", False),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagChallenge",
        "desc": "APA challenge / Chevron step-2 / West Virginia v EPA major questions (bridges iraTaxCredit.flagFeocDisqualification + climate-litigation + wto-dispute)",
        "fields": [
          ("flagId", "string", True),
          ("ruleVid", "string", True, None, "bridges recordRule"),
          ("challengeKind", "string", True, ["apa_arbitrary_capricious","major_questions_doctrine","chevron_overturned","statutory_ultra_vires","constitutional_takings","equal_protection","preemption","retroactivity"]),
          ("plaintiffCategory", "string", False, ["industry","state_ag","ngo","individual","foreign_entity","trade_association"]),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "imf-article-iv",
    "app": "imfArticleIv",
    "methods": [
      {
        "name": "recordConsultation",
        "desc": "IMF Article IV / WEO / FSAP surveillance (bridges emFxReserves.flagReserveAdequacy + sovereign-debt + imf-sdr)",
        "fields": [
          ("consultationId", "string", True),
          ("memberCountryIso3", "string", True),
          ("surveillanceKind", "string", True, ["article_iv","fsap","weo_update","global_financial_stability","external_sector_report","spillover_report","weo_focus"]),
          ("reserveAdequacyVid", "string", False, None, "bridges emFxReserves.flagReserveAdequacy"),
          ("staffView", "string", False, ["clean_bill","caveats","risks_elevated","risks_tilted_downside","critical_imbalance"]),
          ("concludedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagProgramRequest",
        "desc": "IMF program request (SBA/EFF/RSF/RCF/PRGT — bridges emFxReserves.flagReserveAdequacy + sovereignDebt.recordDebtRestructure)",
        "fields": [
          ("programId", "string", True),
          ("consultationVid", "string", True, None, "bridges recordConsultation"),
          ("programType", "string", True, ["sba","eff","rsf","rfi","rcf","pll","fcl","psi","prgt","scf"]),
          ("notionalBusd", "number", False),
          ("conditionalityCount", "integer", False),
          ("approvedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "marine-heatwave",
    "app": "marineHeatwave",
    "methods": [
      {
        "name": "recordMhwEvent",
        "desc": "Marine heatwave event (Hobday category / NOAA CRW / BOM / Copernicus — bridges coralReefBleaching.flagMortalityRisk + ocean-acidification + fisheries-iuu)",
        "fields": [
          ("eventId", "string", True),
          ("regionName", "string", True),
          ("latCenter", "number", False),
          ("lonCenter", "number", False),
          ("hobdayCategory", "string", True, ["cat_i_moderate","cat_ii_strong","cat_iii_severe","cat_iv_extreme","cat_v_unprecedented"]),
          ("durationDays", "integer", False),
          ("peakIntensityC", "number", False),
          ("coralBleachingVid", "string", False, None, "bridges coralReefBleaching.flagMortalityRisk"),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagEcosystemImpact",
        "desc": "Fishery collapse / seabird mortality / HAB bloom cascade (bridges coralReefBleaching.flagMortalityRisk + fisheries-iuu + biodiversity-gbf)",
        "fields": [
          ("impactId", "string", True),
          ("eventVid", "string", True, None, "bridges recordMhwEvent"),
          ("impactKind", "string", True, ["coral_bleaching","kelp_collapse","fishery_closure","harmful_algal_bloom","seabird_die_off","whale_stranding","cephalopod_range_shift","shellfish_mortality"]),
          ("biomassLossPct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if biomassLossPct != null and biomassLossPct >= 50 then \"catastrophic\" else if biomassLossPct != null and biomassLossPct >= 20 then \"significant\" else \"moderate\"", ["moderate","significant","catastrophic"]),
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
            if ftype == "integer" and any(k in col for k in ["count","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued"]):
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
    out = Path(f"/tmp/wave13/w55_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
