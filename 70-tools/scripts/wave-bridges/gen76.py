#!/usr/bin/env python3
"""Wave 76 — press-freedom-index / cell-broadcast-alert / assistive-tech-procure / margin-call / food-fraud.

Bridges Wave 75:
- press-freedom-index ↔ sourceShieldLaw.flagCompulsoryProcess
- cell-broadcast-alert ↔ floodEarlyWarning.flagMissedWarning
- assistive-tech-procure ↔ accessibilityWcag.flagDigitalExclusion
- margin-call ↔ ccpOversight.flagProcyclicality
- food-fraud ↔ isotopeTraceability.flagOriginMismatch
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "press-freedom-index",
    "app": "pressFreedomIndex",
    "methods": [
      {
        "name": "recordIndexPoint",
        "desc": "Press Freedom Index / V-Dem / CPJ / IFJ ranking (bridges sourceShieldLaw.flagCompulsoryProcess + press-freedom + enforcement-action)",
        "fields": [
          ("pointId", "string", True),
          ("countryIso3", "string", True),
          ("indexKind", "string", True, ["rsf_world","cpj_press_freedom","ifj","freedom_house","article_19","vdem","reporters_borders","eu_media_pluralism","crpd_disability","rsf_digital"]),
          ("scoreTier", "string", True, ["good","satisfactory","problematic","difficult","very_serious"]),
          ("compulsoryProcessVid", "string", False, None, "bridges sourceShieldLaw.flagCompulsoryProcess"),
          ("scoreNumeric", "number", False),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDeclineFactor",
        "desc": "Decline factor / harassment / license revocation (bridges sourceShieldLaw.flagCompulsoryProcess + transnational-repression + federal-court-docket)",
        "fields": [
          ("flagId", "string", True),
          ("pointVid", "string", True, None, "bridges recordIndexPoint"),
          ("factorKind", "string", True, ["journalist_killed","imprisoned","detained","harassed_online","license_revoked","state_takeover","defamation_laws","foreign_agent_laws","spyware_targeting","surveillance_legal","newsroom_raided","internet_shutdown","opensrc_seized"]),
          ("incidentsCount", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cell-broadcast-alert",
    "app": "cellBroadcastAlert",
    "methods": [
      {
        "name": "recordBroadcast",
        "desc": "Cell broadcast / WEA / EU-Alert / J-Alert / SMS-CB alert (bridges floodEarlyWarning.flagMissedWarning + disaster-response + refugee-unhcr)",
        "fields": [
          ("broadcastId", "string", True),
          ("regionName", "string", True),
          ("regime", "string", True, ["us_wea","eu_alert_reversal","j_alert_jp","cbc_korea","brazil_sac","mexico_scnr","india_nda","gb_bt_emergency","uk_cell_alert","mx_mexico_alerta","cb112"]),
          ("messageKind", "string", True, ["amber_alert","imminent_threat","national_emergency","test","opt_in_promo","extreme_weather","terrorist_attack","infrastructure_attack","civil_defense","radiation","public_health"]),
          ("missedWarningVid", "string", False, None, "bridges floodEarlyWarning.flagMissedWarning"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDeliveryGap",
        "desc": "Delivery gap / carrier outage / device compat (bridges floodEarlyWarning.flagMissedWarning + network-change + digital-divide)",
        "fields": [
          ("flagId", "string", True),
          ("broadcastVid", "string", True, None, "bridges recordBroadcast"),
          ("gapKind", "string", True, ["carrier_outage","device_incompat","language_locale_gap","false_alarm","opt_out_mass","roaming_failure","disabled_user","pre_4g_device","msisdn_unhoused","tv_radio_backup_fail"]),
          ("affectedDevices", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "assistive-tech-procure",
    "app": "assistiveTechProcure",
    "methods": [
      {
        "name": "recordProcurement",
        "desc": "Assistive technology public procurement (WHO GLIAT / AT 2030 — bridges accessibilityWcag.flagDigitalExclusion + crpd-disability + digital-public-goods)",
        "fields": [
          ("procurementId", "string", True),
          ("buyingAgencyCountryIso3", "string", True),
          ("assistiveTechKind", "string", True, ["mobility_wheelchair","prosthetic","cochlear","hearing_aid","vision_aid","ocr_reading","aac_communication","spatial_navig","switch_control","cognitive_assist","sensory_substitution","brain_computer","wearable_health"]),
          ("fundingSource", "string", True, ["national_gov","health_insurance","private_philanthropic","donor_international","mdb_multilateral","ngo_partnership","school_allocation","workplace_accommodation"]),
          ("exclusionGapVid", "string", False, None, "bridges accessibilityWcag.flagDigitalExclusion"),
          ("awardedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSupplyGap",
        "desc": "Supply gap / repairability / spare parts (bridges accessibilityWcag.flagDigitalExclusion + crpd-disability + right-to-repair)",
        "fields": [
          ("flagId", "string", True),
          ("procurementVid", "string", True, None, "bridges recordProcurement"),
          ("gapKind", "string", True, ["supply_monopoly","repair_denied","spare_parts_unavailable","training_inadequate","ip_lock_in","e_waste_ban","custom_fit_cost","prosthetic_socket","software_proprietary","battery_locked","right_to_repair_denied"]),
          ("coverageRatePct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "margin-call",
    "app": "marginCall",
    "methods": [
      {
        "name": "recordMarginCall",
        "desc": "Counterparty margin call / treasury liquidity demand (bridges ccpOversight.flagProcyclicality + banking-ledger-entry + liquidity-facility)",
        "fields": [
          ("callId", "string", True),
          ("debtorLei", "string", False),
          ("creditorLei", "string", False),
          ("callKind", "string", True, ["variation_margin","initial_margin","intraday","end_of_day","stress_call","pfe_add_on","csa_driven","exchange_forced","dispute_pending","lci_facility","terminated_netting"]),
          ("procyclicalityVid", "string", False, None, "bridges ccpOversight.flagProcyclicality"),
          ("amountBusd", "number", False),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFailure",
        "desc": "Margin call failure / default / treasury sale fire (bridges ccpOversight.flagProcyclicality + bank-resolution + nbfi-stress)",
        "fields": [
          ("flagId", "string", True),
          ("callVid", "string", True, None, "bridges recordMarginCall"),
          ("failureKind", "string", True, ["failure_to_meet","collateral_shortage","liquidity_gap","treasury_fire_sale","basel_iii_repo","dispute_blanket","trade_refusal","nbfi_default","loss_mutualization","compression_trade_failed","cds_triggered","bilateral_cleared"]),
          ("lossMusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "food-fraud",
    "app": "foodFraud",
    "methods": [
      {
        "name": "recordIncident",
        "desc": "Food fraud / adulteration / mislabelling incident (bridges isotopeTraceability.flagOriginMismatch + rasff-food-safety + residue-mrl)",
        "fields": [
          ("incidentId", "string", True),
          ("productCategory", "string", True, ["olive_oil","honey","seafood","spice","dairy","meat","juice","coffee","cocoa","fish_oil","baby_formula","tea","wine","alcohol"]),
          ("fraudKind", "string", True, ["dilution","substitution","concealment","unapproved_additive","mislabelling","counterfeit","overstating_origin","overstating_organic","species_swap","off_spec_blending","gray_market","past_shelflife"]),
          ("countryDetectedIso3", "string", True),
          ("mismatchVid", "string", False, None, "bridges isotopeTraceability.flagOriginMismatch"),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagNetwork",
        "desc": "Fraud network / organized adulteration / cross-border (bridges isotopeTraceability.flagOriginMismatch + enforcement-action + fatf-travel-rule)",
        "fields": [
          ("flagId", "string", True),
          ("incidentVid", "string", True, None, "bridges recordIncident"),
          ("networkKind", "string", True, ["organized_crime","cross_border","corporate_insider","rogue_trader","mafia_family","counterfeit_ring","nsa_reidentified","iuu_fisheries_linked","adulterant_supplier_chain","shell_repackager"]),
          ("estMarketValueMusd", "number", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence","devices","incidents"]):
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
    out = Path(f"/tmp/wave13/w76_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
