#!/usr/bin/env python3
"""Wave 94 — Airlines + airports pivot: JAL / ANA / Haneda / Narita / IATA codeshare.

All-string. Pivots into aviation industry detail per user directive.
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "airline-jal-ops",
    "app": "airlineJalOps",
    "methods": [
      {
        "name": "recordFlightSchedule",
        "desc": "JAL group flight schedule / fleet utilization / codeshare entry (bridges aviation-safety + airplane-flight + iata-codeshare)",
        "fields": [
          ("scheduleId", "string", True),
          ("entityKind", "string", True, ["jal_main_jl","jal_japan_air_commuter_jc","jal_japan_transocean_jta","jal_zipair_zg","jal_jcommuter_3x","jal_spring_japan_ij","jal_jair_xm","jal_express_jc","jal_codeshare_oneworld","jal_codeshare_qf","jal_codeshare_ba","jal_codeshare_aa"]),
          ("routeKind", "string", True, ["domestic_trunk","domestic_local","int_americas","int_europe","int_asia","int_oceania","int_china_hkt","cargo_freighter","int_codeshare","virtual_codeshare","seasonal","crisis_repat","jet_charter"]),
          ("aircraftFamily", "string", True, ["b787_family","b777_family","b737_family","a350_family","a330_family","e170_family","atr72_family","mrj_replaced","saf_blend","cargo_b777f","retired_b747","drone_lupin"]),
          ("flightNumberPrefix", "string", False),
          ("flightVid", "string", False, None, "bridges airplane-flight"),
          ("scheduledAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagOperationalIssue",
        "desc": "JAL operational issue / aircraft swap / safety event (bridges aviation-safety + airplane-incident + airplane-flight)",
        "fields": [
          ("flagId", "string", True),
          ("scheduleVid", "string", True, None, "bridges recordFlightSchedule"),
          ("issueKind", "string", True, ["aircraft_swap","crew_shortage","ata_delay","weather_div","atc_constraint","etops_loss","fuel_anomaly","cabin_safety_event","runway_incursion","bird_strike","tailstrike","cracked_windshield","engine_replacement","hard_landing","skipped_segment","cancellation_cascade"]),
          ("severityTier", "string", False, ["incident","serious","accident_2018_canon","report_published","investigation_open","investigation_closed"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "airline-ana-ops",
    "app": "airlineAnaOps",
    "methods": [
      {
        "name": "recordFlightSchedule",
        "desc": "ANA group flight schedule (Star Alliance) (bridges aviation-safety + airplane-flight + iata-codeshare)",
        "fields": [
          ("scheduleId", "string", True),
          ("entityKind", "string", True, ["ana_main_nh","ana_wings_ek","peach_mm","airdo_hd","solaseed_air_6j","star_flyer_7g","ana_cargo_nh","ibex_fw","ana_codeshare_star","ana_codeshare_ua","ana_codeshare_lh","ana_codeshare_sq","ana_codeshare_oz","ana_codeshare_th"]),
          ("routeKind", "string", True, ["dom_trunk","dom_local","int_north_america","int_europe","int_asia","int_oceania","int_india","cargo_freighter","star_alliance_codeshare","atlantic_jv_with_united","mexico_jv_with_aeromexico","seasonal","int_japan_taiwan_jv"]),
          ("aircraftFamily", "string", True, ["b787_family","b777_family","b737_family","a380_family_pikachu","a380_family_orange","a320_family","a321_family","mrj_replaced","saf_blend","cargo_b767f","retired_b747","drone_logistics"]),
          ("flightNumberPrefix", "string", False),
          ("flightVid", "string", False, None, "bridges airplane-flight"),
          ("scheduledAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagOperationalIssue",
        "desc": "ANA operational issue / star alliance disruption / safety event (bridges aviation-safety + airplane-incident + airplane-flight)",
        "fields": [
          ("flagId", "string", True),
          ("scheduleVid", "string", True, None, "bridges recordFlightSchedule"),
          ("issueKind", "string", True, ["aircraft_swap","crew_shortage","weather_div","atc_constraint","ata_disruption","etops_loss","engine_repair_pwa","gtf_grounded","bird_strike","fuel_quality","tail_strike","go_around","compressor_stall","atlantic_jv_break","star_alliance_disruption"]),
          ("severityTier", "string", False, ["incident","serious","report_published","investigation_open","investigation_closed","atsb_jasc_report","trent_pwa_recall"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "airport-haneda-ops",
    "app": "airportHanedaOps",
    "methods": [
      {
        "name": "recordSlotAllocation",
        "desc": "Haneda HND slot allocation / runway / curfew (bridges airplane-airport + iata-codeshare + ports-port)",
        "fields": [
          ("allocationId", "string", True),
          ("runwayKind", "string", True, ["a_runway_16r_34l","b_runway_04_22","c_runway_16l_34r","d_runway_05_23","new_runway_2030_proposed","cross_a_b_dependency","conflict_b_c","apron_only","go_around_alternate"]),
          ("slotKind", "string", True, ["domestic_slot","int_slot","mctd_morning","mctd_evening","new_route_slot","seasonal_summer","seasonal_winter","early_curfew","late_curfew","emergency_extension","cargo_only","ga_general_aviation"]),
          ("carrierLei", "string", False),
          ("flightVid", "string", False, None, "bridges airplane-flight"),
          ("allocatedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSlotConstraint",
        "desc": "Slot constraint / capacity / curfew exception (bridges airplane-airport + ports-port + airline-jal-ops)",
        "fields": [
          ("flagId", "string", True),
          ("allocationVid", "string", True, None, "bridges recordSlotAllocation"),
          ("constraintKind", "string", True, ["full_capacity","peak_hour_max","mctd_overshoot","go_around_chain","atc_holding","wind_runway_change","noise_complaint","curfew_breach_extra","emergency_landing","disabled_aircraft","wildlife_strike","drone_intrusion","apron_conflict","mass_diversion"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "airport-narita-ops",
    "app": "airportNaritaOps",
    "methods": [
      {
        "name": "recordTerminalOps",
        "desc": "Narita NRT terminal operations / cargo / cross-border (bridges airplane-airport + customs-declaration + iata-codeshare)",
        "fields": [
          ("opsId", "string", True),
          ("terminalKind", "string", True, ["t1_north","t1_south","t2","t3_lcc","cargo_north","cargo_south","sat_a","sat_b","general_aviation_apron","disabled_apron","fuel_apron","fence_perimeter"]),
          ("opsKind", "string", True, ["cargo_freighter","int_pax","lcc_dom","int_codeshare","customs_inbound","customs_outbound","customs_quarantine","afis_passport","biometric_face","slot_full","seasonal_charter","crisis_evacuation"]),
          ("carrierLei", "string", False),
          ("flightVid", "string", False, None, "bridges airplane-flight"),
          ("recordedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBottleneck",
        "desc": "Bottleneck / cargo bridge collapse / customs queue / slot waste (bridges airplane-airport + customs-declaration + airline-jal-ops)",
        "fields": [
          ("flagId", "string", True),
          ("opsVid", "string", True, None, "bridges recordTerminalOps"),
          ("bottleneckKind", "string", True, ["customs_queue","cargo_bridge","baggage_belt","passport_slow","biometric_offline","apron_full","fuel_pipeline","ground_handling_strike","cargo_perishable_delay","arrival_late_evening","departure_early_morning","slot_waste","aircraft_disabled_blocking","atc_radar_outage"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "iata-codeshare",
    "app": "iataCodeshare",
    "methods": [
      {
        "name": "recordAgreement",
        "desc": "IATA codeshare / interline / SPA / IT (Industry Traffic) agreement (bridges airline-jal-ops + airline-ana-ops + airplane-flight)",
        "fields": [
          ("agreementId", "string", True),
          ("agreementKind", "string", True, ["codeshare_block_seat","codeshare_free_sale","interline_e_ticket","interline_baggage","spa_special_prorate","ssim_industry_traffic","mitt_minimum_interline","virtual_codeshare","franchise","wet_lease_codeshare","mctd_minimum_connect","sla_redirect","mvp_min_volume","jba_joint_business"]),
          ("operatingCarrier", "string", True),
          ("marketingCarrier", "string", True),
          ("scope", "string", True, ["bilateral","multilateral_alliance","oneworld","star_alliance","skyteam","value_alliance","independent","specific_route","seasonal","cargo","jba_atlantic","jba_pacific","jba_japan_us"]),
          ("agreementAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAntitrustReview",
        "desc": "Antitrust / immunity grant / slot remedy review (bridges antitrust-dma + merger-review + airline-jal-ops)",
        "fields": [
          ("flagId", "string", True),
          ("agreementVid", "string", True, None, "bridges recordAgreement"),
          ("reviewKind", "string", True, ["dot_immunity_grant","ec_dg_comp_review","jftc_review","cma_review","prc_samr","mexico_cofece","slot_remedy_block","slot_handover_required","price_cap_temp","carve_out_origin_destination","interim_measure","cooperation_termination","monitor_appointed"]),
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
    out = Path(f"/tmp/wave13/w94_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
