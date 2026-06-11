#!/usr/bin/env python3
"""Wave 69 — revolving-door / esg-sovereign / transnational-repression / subordinated-debt / transshipment-evasion.

Bridges Wave 68:
- revolving-door ↔ lobbyingDisclosure.flagFaraUnderreport
- esg-sovereign ↔ sovereignRating.flagMethodologyConcern
- transnational-repression ↔ interpolRedabuse.flagAbusivePattern
- subordinated-debt ↔ receiverBankruptcy.flagCramDown
- transshipment-evasion ↔ tradeRemedy.flagTariffOutcome
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "revolving-door",
    "app": "revolvingDoor",
    "methods": [
      {
        "name": "recordTransition",
        "desc": "Government-to-industry / industry-to-government transition (bridges lobbyingDisclosure.flagFaraUnderreport + ethics-disclosure + judicial-influence)",
        "fields": [
          ("transitionId", "string", True),
          ("personDid", "string", False),
          ("directionKind", "string", True, ["gov_to_industry","industry_to_gov","gov_to_lobby","gov_to_consulting","gov_to_nonprofit","gov_to_academia","gov_to_startup","agency_to_regulated","alumni_donor_pipe","board_revolving"]),
          ("jurisdictionIso3", "string", True),
          ("coolingOffMonths", "integer", False),
          ("faraUnderreportVid", "string", False, None, "bridges lobbyingDisclosure.flagFaraUnderreport"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCoolingBreach",
        "desc": "Cooling-off period breach / regulatory capture (bridges lobbyingDisclosure.flagFaraUnderreport + enforcement-action + judicial-influence)",
        "fields": [
          ("flagId", "string", True),
          ("transitionVid", "string", True, None, "bridges recordTransition"),
          ("breachKind", "string", True, ["contact_within_cooling","shadow_lobby","foreign_state_client","matter_substantive","recusal_failure","continued_supervision","ethics_waiver","post_employment_income","regulatory_capture","procurement_inside"]),
          ("estIncomeUsd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "esg-sovereign",
    "app": "esgSovereign",
    "methods": [
      {
        "name": "recordEsgSovereignScore",
        "desc": "ESG sovereign rating / PRI / S&P ESG (bridges sovereignRating.flagMethodologyConcern + esg-rating + sovereign-debt)",
        "fields": [
          ("scoreId", "string", True),
          ("countryIso3", "string", True),
          ("provider", "string", True, ["sp_esg","sustainalytics","moodys_esg","fitch_esg","msci_esg","robecosam_csa","verisk_maplecroft","pri_trase","fao_sdg"]),
          ("axisE", "number", False),
          ("axisS", "number", False),
          ("axisG", "number", False),
          ("methodologyConcernVid", "string", False, None, "bridges sovereignRating.flagMethodologyConcern"),
          ("asOfDate", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMaterialityDebate",
        "desc": "ESG materiality / inverse relationship / greenhushing (bridges sovereignRating.flagMethodologyConcern + esg-controversy + climate-value-chain)",
        "fields": [
          ("flagId", "string", True),
          ("scoreVid", "string", True, None, "bridges recordEsgSovereignScore"),
          ("debateKind", "string", True, ["e_vs_growth","s_vs_gdp","g_vs_democracy","inverse_e_s","window_dressing","colonial_bias","lmic_penalized","climate_adaptation_gap","just_transition_scoring","litigation_on_score"]),
          ("rangeBpsImpact", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "transnational-repression",
    "app": "transnationalRepression",
    "methods": [
      {
        "name": "recordIncident",
        "desc": "Transnational repression / diaspora targeting (bridges interpolRedabuse.flagAbusivePattern + refugee-unhcr + press-freedom)",
        "fields": [
          ("incidentId", "string", True),
          ("originCountryIso3", "string", True),
          ("hostCountryIso3", "string", True),
          ("targetCategory", "string", True, ["journalist","dissident","activist","lawyer","academic","religious","minority","ngo_worker","lgbtq","artist","family_member","double_national"]),
          ("tacticKind", "string", True, ["assassination","abduction","physical_assault","renditions","coerced_return","diaspora_surveillance","digital_harassment","family_intimidation","property_seizure","freeze_remittance","defamation","frivolous_lawsuit","asylum_revoke_demand"]),
          ("redNoticeAbuseVid", "string", False, None, "bridges interpolRedabuse.flagAbusivePattern"),
          ("occurredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagImpunity",
        "desc": "Impunity / host-state indifference / extradition-requested retaliation (bridges interpolRedabuse.flagAbusivePattern + press-freedom + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("incidentVid", "string", True, None, "bridges recordIncident"),
          ("impunityKind", "string", True, ["host_state_inaction","investigation_abandoned","prosecution_declined","visa_leverage","economic_leverage","intelligence_cooperation","diplomatic_assurances_ignored","perp_escape","family_in_origin","hostage_diplomacy"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "subordinated-debt",
    "app": "subordinatedDebt",
    "methods": [
      {
        "name": "recordInstrument",
        "desc": "Subordinated debt / AT1 / CoCo / PIK note (bridges receiverBankruptcy.flagCramDown + sovereign-debt + insurance-policy)",
        "fields": [
          ("instrumentId", "string", True),
          ("issuerLei", "string", False),
          ("subordinationTier", "string", True, ["at1","tier2","senior_non_pref","pik","mezzanine","subordinated_tlac","contingent_convertible","hybrid","perpetual","soe_hybrid","pir_subdebt"]),
          ("triggersWriteDown", "string", True, ["cet1_threshold","pon_resolution","distressed_exchange","sweetener","cram_down","mandatory_convert","statutory_bail_in","governmental_action"]),
          ("cramDownVid", "string", False, None, "bridges receiverBankruptcy.flagCramDown"),
          ("principalBusd", "number", False),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagResolution",
        "desc": "Resolution write-down / AT1 haircut / junior-senior inversion (bridges receiverBankruptcy.flagCramDown + enforcementAction + stablecoin-reserves)",
        "fields": [
          ("flagId", "string", True),
          ("instrumentVid", "string", True, None, "bridges recordInstrument"),
          ("eventKind", "string", True, ["at1_writedown","cet1_touch","junior_senior_inversion","equity_superior_to_debt","mandatory_conversion","coupon_suspension","contingent_redemption","stopped_interest","priority_rulemaking","new_waterfall"]),
          ("lossHaircut", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "transshipment-evasion",
    "app": "transshipmentEvasion",
    "methods": [
      {
        "name": "recordInvestigation",
        "desc": "AD/CVD transshipment / circumvention investigation (bridges tradeRemedy.flagTariffOutcome + customs-declaration + logistics-container)",
        "fields": [
          ("investigationId", "string", True),
          ("initiatingCountryIso3", "string", True),
          ("routingPattern", "string", True, ["direct_relabel","minor_processing","hub_country_laundering","ftz_manipulation","document_forgery","ec_commerce_split","low_value_parcel","re_classification","tariff_line_drift"]),
          ("originCountryIso3", "string", True),
          ("transshipCountryIso3", "string", True),
          ("tariffOutcomeVid", "string", False, None, "bridges tradeRemedy.flagTariffOutcome"),
          ("initiatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMaterialFinding",
        "desc": "Material alteration / substantial transformation / anti-circumvention (bridges tradeRemedy.flagTariffOutcome + ustr-section-301 + hs-classification)",
        "fields": [
          ("flagId", "string", True),
          ("investigationVid", "string", True, None, "bridges recordInvestigation"),
          ("findingKind", "string", True, ["minor_processing_insufficient","no_substantial_trans","ftz_not_insulating","first_sale_rule","material_alteration_test","non_market_economy","surrogate_value","same_class_or_kind","subs_change_in_tariff"]),
          ("dutyImposedPct", "number", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps"]):
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
    out = Path(f"/tmp/wave13/w69_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
