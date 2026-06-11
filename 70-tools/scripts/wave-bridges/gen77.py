#!/usr/bin/env python3
"""Wave 77 — spyware-export / internet-shutdown / universal-design / treasury-stress / codex-standard.

Bridges Wave 76:
- spyware-export ↔ pressFreedomIndex.flagDeclineFactor
- internet-shutdown ↔ cellBroadcastAlert.flagDeliveryGap
- universal-design ↔ assistiveTechProcure.flagSupplyGap
- treasury-market-stress ↔ marginCall.flagFailure
- codex-standard ↔ foodFraud.flagNetwork
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "spyware-export",
    "app": "spywareExport",
    "methods": [
      {
        "name": "recordExportLicense",
        "desc": "Commercial spyware / dual-use / Wassenaar export license (bridges pressFreedomIndex.flagDeclineFactor + ofac-sanctions-sdn + cyber-vuln-cve)",
        "fields": [
          ("licenseId", "string", True),
          ("vendorLei", "string", False),
          ("productKind", "string", True, ["nso_pegasus","intellexa_predator","cytrox","candiru","quadream","hacking_team_legacy","finfisher","darkmatter","paragon","ring_zero","macos_zero_click","android_zero_click"]),
          ("exportCountryIso3", "string", True),
          ("importCountryIso3", "string", True),
          ("endUseCert", "string", False, ["le_lawful_intercept","national_security","counter_terror","counter_narcotics","dual_use_civilian","research","ban_exceptions","none"]),
          ("pressDeclineVid", "string", False, None, "bridges pressFreedomIndex.flagDeclineFactor"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMisuse",
        "desc": "Spyware misuse / journalist target / HRD surveillance (bridges pressFreedomIndex.flagDeclineFactor + transnational-repression + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("licenseVid", "string", True, None, "bridges recordExportLicense"),
          ("misuseKind", "string", True, ["journalist_targeting","hrd_surveillance","dissident_targeting","political_opponent","pro_eu_russia_targeting","diplomatic_staff","government_official","family_member","spouse","lawyer","cross_border_targeting","autonomous_community"]),
          ("reportedDetectionCount", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "internet-shutdown",
    "app": "internetShutdown",
    "methods": [
      {
        "name": "recordShutdown",
        "desc": "Internet shutdown / blackout / throttling event (Access Now STOP / KeepItOn — bridges cellBroadcastAlert.flagDeliveryGap + press-freedom + press-finance-coercion)",
        "fields": [
          ("shutdownId", "string", True),
          ("countryIso3", "string", True),
          ("shutdownKind", "string", True, ["full_blackout","partial_regional","platform_specific","throttling","dns_blocking","bgp_route_null","mobile_suspend","sms_only","vpn_block","tor_block","bandwidth_cap","peak_time_off"]),
          ("triggerKind", "string", True, ["election","protest","exam_cheating","religious_violence","communal_riot","military_ops","state_security","visit_diplomatic","sports_event","border_dispute"]),
          ("deliveryGapVid", "string", False, None, "bridges cellBroadcastAlert.flagDeliveryGap"),
          ("hoursDark", "integer", False),
          ("beganAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagEconomicImpact",
        "desc": "Economic / social impact of shutdown (bridges cellBroadcastAlert.flagDeliveryGap + digital-public-infra + refugee-unhcr)",
        "fields": [
          ("flagId", "string", True),
          ("shutdownVid", "string", True, None, "bridges recordShutdown"),
          ("impactKind", "string", True, ["gdp_loss_pct","remittance_halt","exam_disrupt","medical_telemed","banking_halt","emergency_alerts_off","schools_online_halt","pandemic_info_halt","agri_price_info","msme_impact","tourism_hit","elections_affected"]),
          ("estBusdLoss", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "universal-design",
    "app": "universalDesign",
    "methods": [
      {
        "name": "recordStandard",
        "desc": "Universal Design / ISO 21542 / IDeA / OHB public building (bridges assistiveTechProcure.flagSupplyGap + crpd-disability + accessibility-wcag)",
        "fields": [
          ("standardId", "string", True),
          ("region", "string", True, ["global_iso","us_ada_aba","eu_fn_aabbes","jp_tokubetsu","kr_ud_act","ca_bim_a17_1","au_disability_act","in_rpwd_act","nor_ohba","se_bb_16","dk_tilgænge","br_nbr_9050"]),
          ("designDomain", "string", True, ["architectural","product","interior","transport","ict","outdoor_urban","housing","education","healthcare","workplace","cultural"]),
          ("supplyGapVid", "string", False, None, "bridges assistiveTechProcure.flagSupplyGap"),
          ("releasedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagImplementationShortfall",
        "desc": "Implementation shortfall / legacy building / accessibility retrofit (bridges assistiveTechProcure.flagSupplyGap + crpd-disability + land-tenure)",
        "fields": [
          ("flagId", "string", True),
          ("standardVid", "string", True, None, "bridges recordStandard"),
          ("shortfallKind", "string", True, ["legacy_building","retrofit_cost","historic_bldg_exemption","rural_budget","public_transit_gap","private_sector_uncovered","accessible_housing_shortage","wayfinding_absent","enforcement_weak","exemptions_abused","certification_fraud"]),
          ("coverageRatePct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "treasury-market-stress",
    "app": "treasuryMarketStress",
    "methods": [
      {
        "name": "recordStressEvent",
        "desc": "US Treasury market stress event / basis trade unwind (bridges marginCall.flagFailure + nbfi-stress + ccp-oversight)",
        "fields": [
          ("eventId", "string", True),
          ("stressKind", "string", True, ["basis_trade_unwind","swap_spread_blow","dash_for_cash","on_run_off_run_widen","srf_activation","bond_liquidity_gap","mbs_basis","bid_ask_widen","cbb_sofr_arm_spike","atr_spike","repo_mmt_spike"]),
          ("depthImpactLevel", "string", True, ["tolerable","elevated","impaired","crisis","systemic"]),
          ("marginCallVid", "string", False, None, "bridges marginCall.flagFailure"),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFedIntervention",
        "desc": "Fed intervention / standing repo / emergency dealer lending (bridges marginCall.flagFailure + liquidity-facility + bank-resolution)",
        "fields": [
          ("flagId", "string", True),
          ("eventVid", "string", True, None, "bridges recordStressEvent"),
          ("interventionKind", "string", True, ["srf","pdcf_emergency","open_market_purchases","qe_restart","dealer_lending","term_auction","money_market_guarantee","fhl_expansion","fima_repo","swap_line_activation","direct_lending_nbfi"]),
          ("notionalBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "codex-standard",
    "app": "codexStandard",
    "methods": [
      {
        "name": "recordStandardAdoption",
        "desc": "Codex Alimentarius / CCGP / CCFAC standard adoption (bridges foodFraud.flagNetwork + residue-mrl + rasff-food-safety)",
        "fields": [
          ("adoptionId", "string", True),
          ("committee", "string", True, ["cac","ccgp","ccfac","ccpr","ccrvdf","ccrol","ccmas","ccffp","ccfh","ccfl","ccnfsdu","ccgen","ccsis","ccasia","ccafrica","ccnea","ccnasma","cclac","ccexec"]),
          ("standardKind", "string", True, ["max_residue","hygiene_practice","labeling","sampling","contamination","additives","novel_food","traceability","authentication","species_id","allergen","supplement"]),
          ("foodFraudVid", "string", False, None, "bridges foodFraud.flagNetwork"),
          ("adoptedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagNonHarmonization",
        "desc": "Non-harmonization / national deviation / transition period (bridges foodFraud.flagNetwork + wto-trade-cbam + rasff-food-safety)",
        "fields": [
          ("flagId", "string", True),
          ("adoptionVid", "string", True, None, "bridges recordStandardAdoption"),
          ("issueKind", "string", True, ["stricter_national","weaker_national","transition_delay","private_standard_super","regional_divergence","eu_vs_fda","multi_sector_conflict","jurisdiction_gap","enforcement_divergence","data_gap_lmics"]),
          ("affectedCountriesCount", "integer", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence","devices","incidents","countries","detections","dark"]):
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
    out = Path(f"/tmp/wave13/w77_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
