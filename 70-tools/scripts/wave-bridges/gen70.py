#!/usr/bin/env python3
"""Wave 70 — ethics-waiver / tnfd-disclosure / asylum-determination / bank-resolution / rules-of-origin.

Bridges Wave 69:
- ethics-waiver ↔ revolvingDoor.flagCoolingBreach
- tnfd-disclosure ↔ esgSovereign.flagMaterialityDebate
- asylum-determination ↔ transnationalRepression.flagImpunity
- bank-resolution ↔ subordinatedDebt.flagResolution
- rules-of-origin ↔ transshipmentEvasion.flagMaterialFinding
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "ethics-waiver",
    "app": "ethicsWaiver",
    "methods": [
      {
        "name": "recordWaiver",
        "desc": "Ethics waiver / 207(c) / agency-level exception (bridges revolvingDoor.flagCoolingBreach + ethics-disclosure + lobbying-disclosure)",
        "fields": [
          ("waiverId", "string", True),
          ("agency", "string", True, ["oge","omb","white_house","doj_crm","irs","sec","cftc","dod","state","ofac","fincen","epa","fda","nih","dot","treasury","dhs"]),
          ("waiverKind", "string", True, ["208_financial_interest","207_c","matter_specific","general_waiver","de_minimis","impartiality","post_employment","alternative_remuneration","ghost_advisor","emergency"]),
          ("coolingBreachVid", "string", False, None, "bridges revolvingDoor.flagCoolingBreach"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagConflictWaived",
        "desc": "Waiver issued for active conflict / retroactive justification (bridges revolvingDoor.flagCoolingBreach + judicial-influence + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("waiverVid", "string", True, None, "bridges recordWaiver"),
          ("concernKind", "string", True, ["retroactive_justification","prior_concealment","insufficient_scope","matter_specific_loophole","ex_parte_communication","family_conflict","blind_trust_failure","ignored_advice","cumulative_gifts"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "tnfd-disclosure",
    "app": "tnfdDisclosure",
    "methods": [
      {
        "name": "recordDisclosure",
        "desc": "TNFD nature-related financial disclosure (bridges esgSovereign.flagMaterialityDebate + biodiversity-gbf + climate-value-chain)",
        "fields": [
          ("disclosureId", "string", True),
          ("filerLei", "string", False),
          ("pillarKind", "string", True, ["governance","strategy","risk_impact","metrics_targets","location_specific","leap_framework","sector_prototype","financial_sector"]),
          ("dependencyKind", "string", False, ["water_supply","soil_health","pollination","climate_regulation","genetic_resources","flood_protection","waste_degradation"]),
          ("impactKind", "string", False, ["land_use_change","water_withdrawal","pollution","invasive_species","direct_exploit","climate"]),
          ("materialityVid", "string", False, None, "bridges esgSovereign.flagMaterialityDebate"),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagGreenwash",
        "desc": "Nature greenwashing / SBTN / CSRD gap (bridges esgSovereign.flagMaterialityDebate + climate-value-chain + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("disclosureVid", "string", True, None, "bridges recordDisclosure"),
          ("greenwashKind", "string", True, ["metric_omission","offset_reliance","baseline_gaming","selective_reporting","forward_looking","avoided_footprint","no_location_data","single_site_gen","outdated_science","tiered_targets","no_reckoning_with_drivers"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "asylum-determination",
    "app": "asylumDetermination",
    "methods": [
      {
        "name": "recordRsd",
        "desc": "Refugee status determination / Convention grounds adjudication (bridges transnationalRepression.flagImpunity + refugee-unhcr + fpic-consent)",
        "fields": [
          ("determinationId", "string", True),
          ("hostCountryIso3", "string", True),
          ("originCountryIso3", "string", True),
          ("forum", "string", True, ["unhcr","national_ria","uk_home_office","us_uscis","eu_ejus","ca_irb","au_rrt","de_bamf","fr_ofpra","jp_moj","mex_comar","safeguard_aboriginal"]),
          ("convGrounds", "string", True, ["race","religion","nationality","political","social_group","gender","sexual_orientation","humanitarian_stay","subsidiary_protection","complementary","bilateral_prima_facie"]),
          ("repressionVid", "string", False, None, "bridges transnationalRepression.flagImpunity"),
          ("decidedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagProtectionGap",
        "desc": "Non-refoulement breach / detention / third-country agreement (bridges transnationalRepression.flagImpunity + refugee-unhcr + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("determinationVid", "string", True, None, "bridges recordRsd"),
          ("gapKind", "string", True, ["refoulement","detention_arbitrary","third_country_transfer","safe_country_ill","family_separation","undue_delay","legal_aid_gap","interpretation_failure","credibility_bias","culture_of_disbelief","protection_screening_dropped"]),
          ("daysInLimbo", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "bank-resolution",
    "app": "bankResolution",
    "methods": [
      {
        "name": "recordResolutionAction",
        "desc": "FSB TLAC / SPE / MPE bank resolution action (bridges subordinatedDebt.flagResolution + enforcement-action + sovereign-guarantee)",
        "fields": [
          ("actionId", "string", True),
          ("bankLei", "string", False),
          ("authorityKind", "string", True, ["fdic","fsb","srb","boe","pra","bafin","autocat_fr","fsa_jp","cnbv_mx","apra_au","rbi_in","pboc_cbirc","cbirc"]),
          ("strategy", "string", True, ["spe","mpe","bridge","liquidation","write_off","bail_in","bail_out","purchase_assumption","asset_transfer","gone_concern","scheme_of_arrangement"]),
          ("resolutionVid", "string", False, None, "bridges subordinatedDebt.flagResolution"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBailInDispute",
        "desc": "Bail-in / NCWO / creditor priority litigation (bridges subordinatedDebt.flagResolution + civil-liability + federal-court-docket)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordResolutionAction"),
          ("disputeKind", "string", True, ["ncwo_breach","creditor_pari_passu","hybrid_treatment","cross_border_recognition","statutory_bail_in","conversion_rate_manipulated","lender_information_gap","credit_event_trigger","isda_determination"]),
          ("estClaimBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "rules-of-origin",
    "app": "rulesOfOrigin",
    "methods": [
      {
        "name": "recordOriginCertificate",
        "desc": "FTA rules of origin certificate (CPTPP / USMCA / EU-GSP — bridges transshipmentEvasion.flagMaterialFinding + customs-declaration + ev-supply-chain)",
        "fields": [
          ("certId", "string", True),
          ("ftaKind", "string", True, ["usmca","cptpp","rcep","eu_gsp","eu_fta","mercosur","afcfta","asean_atiga","pacer_plus","china_asean","korea_fta","japan_epa","cptpp_extension"]),
          ("productHs6", "string", True),
          ("exportingCountryIso3", "string", True),
          ("importingCountryIso3", "string", True),
          ("rooKind", "string", True, ["pse","rvc","cth_ctsh","de_minimis","wholly_obtained","substantial_trans","accumulation","outward_processing","roo_origin_blend"]),
          ("materialFindingVid", "string", False, None, "bridges transshipmentEvasion.flagMaterialFinding"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRooFraud",
        "desc": "Rules-of-origin fraud / origin washing (bridges transshipmentEvasion.flagMaterialFinding + enforcementAction + tradeRemedy)",
        "fields": [
          ("flagId", "string", True),
          ("certVid", "string", True, None, "bridges recordOriginCertificate"),
          ("fraudKind", "string", True, ["forgery","false_declaration","undervaluation","regional_value_misstated","cost_allocation_fraud","ftz_gaming","third_country_re_export","mislabelled_origin","shell_producer","unrecorded_value_add"]),
          ("dutyEvadedMusd", "number", False),
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
    out = Path(f"/tmp/wave13/w70_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
