#!/usr/bin/env python3
"""Wave 13 bridge actor generator — 5 actors × 2 NSIDs each."""
import json
from pathlib import Path

REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

# Each actor: (slug, appName, methods [...])
ACTORS = [
  {
    "slug": "commodity-trade",
    "app": "commodityTrade",
    "short": "LME/CME/SGX futures bridging refiner-product + broker-charter + hormuz-cargo",
    "methods": [
      {
        "name": "recordTrade",
        "desc": "Commodity futures trade (LME/CME/SGX bridges refiner+broker+cargo)",
        "fields": [
          ("tradeId", "string", True),
          ("exchange", "string", True, ["LME","CME","SGX","ICE","DCE","SHFE"]),
          ("contract", "string", True),
          ("productHs", "string", False, None, "HS code bridging refiner-product"),
          ("refinerYieldVid", "string", False, None, "bridges open-refiner-product"),
          ("hormuzCargoVid", "string", False, None, "bridges open-hormuz-cargo"),
          ("brokerCharterVid", "string", False, None, "bridges open-broker-charter"),
          ("side", "string", True, ["buy","sell"]),
          ("priceUsd", "number", False),
          ("qtyBbl", "number", False),
          ("counterpartyLei", "string", False),
          ("tradedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "settleContract",
        "desc": "Futures settlement linked to physical delivery",
        "fields": [
          ("settlementId", "string", True),
          ("tradeVid", "string", True, None, "bridges recordTrade"),
          ("settledAt", "string", True),
          ("settlementPriceUsd", "number", True),
          ("realizedPnlUsd", "number", False),
          ("deliveryType", "string", True, ["physical","cash"]),
          ("deliveryRefinerVid", "string", False, None, "if physical delivery to refiner"),
        ],
        "classify": ("pnlTier", "if realizedPnlUsd != null and realizedPnlUsd >= 1000000 then \"large_win\" else if realizedPnlUsd != null and realizedPnlUsd <= -1000000 then \"large_loss\" else \"neutral\"", ["large_loss","neutral","large_win"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("trade_id","varchar",""),
      ("exchange","varchar",""),
      ("contract","varchar",""),
      ("product_hs","varchar",""),
      ("refiner_yield_vid","varchar",""),
      ("hormuz_cargo_vid","varchar",""),
      ("broker_charter_vid","varchar",""),
      ("side","varchar",""),
      ("price_usd","double precision",""),
      ("qty_bbl","double precision",""),
      ("counterparty_lei","varchar",""),
      ("traded_at","varchar",""),
      ("settlement_id","varchar",""),
      ("trade_vid","varchar",""),
      ("settled_at","varchar",""),
      ("settlement_price_usd","double precision",""),
      ("realized_pnl_usd","double precision",""),
      ("delivery_type","varchar",""),
      ("delivery_refiner_vid","varchar",""),
      ("pnl_tier","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
  {
    "slug": "logistics-lastmile",
    "app": "logisticsLastmile",
    "short": "carrier-schedule → customs-clearance → final-delivery leg closure",
    "methods": [
      {
        "name": "dispatchLeg",
        "desc": "Last-mile dispatch (carrier-schedule+customs-clearance bridge)",
        "fields": [
          ("legId", "string", True),
          ("carrierScheduleVid", "string", True, None, "bridges open-carrier-schedule"),
          ("customsClearanceVid", "string", False, None, "bridges open-customs-clearance"),
          ("mode", "string", True, ["truck","rail","parcel","air"]),
          ("originPortVid", "string", False),
          ("destAddress", "string", True),
          ("plannedArrival", "string", True),
          ("slaMinutes", "integer", False),
        ],
        "classify": None,
      },
      {
        "name": "confirmDelivery",
        "desc": "Confirm last-mile delivery outcome",
        "fields": [
          ("proofId", "string", True),
          ("legVid", "string", True, None, "bridges dispatchLeg"),
          ("deliveredAt", "string", True),
          ("minutesLate", "integer", False),
          ("damageReported", "boolean", False),
          ("signatureCid", "string", False),
        ],
        "classify": ("slaTier", "if damageReported = true then \"damaged\" else if minutesLate != null and minutesLate > 60 then \"late\" else if minutesLate != null and minutesLate > 0 then \"mild_late\" else \"on_time\"", ["damaged","late","mild_late","on_time"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("leg_id","varchar",""),
      ("carrier_schedule_vid","varchar",""),
      ("customs_clearance_vid","varchar",""),
      ("mode","varchar",""),
      ("origin_port_vid","varchar",""),
      ("dest_address","varchar",""),
      ("planned_arrival","varchar",""),
      ("sla_minutes","int",""),
      ("proof_id","varchar",""),
      ("leg_vid","varchar",""),
      ("delivered_at","varchar",""),
      ("minutes_late","int",""),
      ("damage_reported","boolean",""),
      ("signature_cid","varchar",""),
      ("sla_tier","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
  {
    "slug": "supply-chain-finance",
    "app": "supplyChainFinance",
    "short": "Trade finance L/C bridging banking+swift+carrier-fleet+customs",
    "methods": [
      {
        "name": "issueLetterOfCredit",
        "desc": "L/C issuance (banking+swift+customs+carrier bridge)",
        "fields": [
          ("lcId", "string", True),
          ("bankingAccountVid", "string", False, None, "bridges open-banking"),
          ("swiftUetr", "string", False, None, "bridges open-swift"),
          ("carrierFleetVid", "string", False, None, "bridges open-carrier-fleet (vessel IMO)"),
          ("customsClearanceVid", "string", False, None, "bridges open-customs-clearance"),
          ("lcType", "string", True, ["sight","usance","standby"]),
          ("amountUsd", "number", True),
          ("buyerLei", "string", False),
          ("sellerLei", "string", False),
          ("expiryDate", "string", True),
        ],
        "classify": ("amountTier", "if amountUsd >= 10000000 then \"jumbo\" else if amountUsd >= 1000000 then \"large\" else \"standard\"", ["jumbo","large","standard"]),
      },
      {
        "name": "recordDiscrepancy",
        "desc": "Document discrepancy under L/C",
        "fields": [
          ("discrepancyId", "string", True),
          ("lcVid", "string", True, None, "bridges issueLetterOfCredit"),
          ("discrepancyType", "string", True, ["late_presentation","missing_doc","quantity_mismatch","wrong_port","other"]),
          ("resolution", "string", False, ["waived","amended","rejected","pending"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("lc_id","varchar",""),
      ("banking_account_vid","varchar",""),
      ("swift_uetr","varchar",""),
      ("carrier_fleet_vid","varchar",""),
      ("customs_clearance_vid","varchar",""),
      ("lc_type","varchar",""),
      ("amount_usd","double precision",""),
      ("buyer_lei","varchar",""),
      ("seller_lei","varchar",""),
      ("expiry_date","varchar",""),
      ("amount_tier","varchar",""),
      ("discrepancy_id","varchar",""),
      ("lc_vid","varchar",""),
      ("discrepancy_type","varchar",""),
      ("resolution","varchar",""),
      ("reported_at","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
  {
    "slug": "biosecurity",
    "app": "biosecurity",
    "short": "Port state biosecurity (ports+customs+maritime-incident bridge)",
    "methods": [
      {
        "name": "inspectVessel",
        "desc": "Biosecurity inspection at port (ballast water / hull fouling / IAS)",
        "fields": [
          ("inspectionId", "string", True),
          ("portVid", "string", True, None, "bridges open-ports"),
          ("imo", "string", True, None, "vessel IMO, bridges open-carrier-fleet"),
          ("customsClearanceVid", "string", False, None, "bridges open-customs-clearance"),
          ("ballastSource", "string", False),
          ("hullFoulingPct", "number", False),
          ("iasDetected", "boolean", False, None, "invasive alien species"),
          ("inspectedAt", "string", True),
        ],
        "classify": ("riskTier", "if iasDetected = true then \"quarantine\" else if hullFoulingPct != null and hullFoulingPct >= 15 then \"cleaning_ordered\" else \"clear\"", ["clear","cleaning_ordered","quarantine"]),
      },
      {
        "name": "issueQuarantineOrder",
        "desc": "Quarantine order bridging to maritime-incident",
        "fields": [
          ("orderId", "string", True),
          ("inspectionVid", "string", True, None, "bridges inspectVessel"),
          ("maritimeIncidentVid", "string", False, None, "bridges open-hormuz-incident"),
          ("quarantineDurationHours", "integer", True),
          ("reason", "string", True),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("inspection_id","varchar",""),
      ("port_vid","varchar",""),
      ("imo","varchar",""),
      ("customs_clearance_vid","varchar",""),
      ("ballast_source","varchar",""),
      ("hull_fouling_pct","double precision",""),
      ("ias_detected","boolean",""),
      ("inspected_at","varchar",""),
      ("risk_tier","varchar",""),
      ("order_id","varchar",""),
      ("inspection_vid","varchar",""),
      ("maritime_incident_vid","varchar",""),
      ("quarantine_duration_hours","int",""),
      ("reason","varchar",""),
      ("issued_at","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
  {
    "slug": "crew-welfare",
    "app": "crewWelfare",
    "short": "Seafarer MLC 2006 welfare (orcid+isco+carrier-fleet bridge)",
    "methods": [
      {
        "name": "registerSeafarer",
        "desc": "Seafarer MLC registration (orcid+isco+carrier bridge)",
        "fields": [
          ("seafarerId", "string", True),
          ("orcid", "string", False, None, "bridges open-orcid"),
          ("iscoCode", "string", False, None, "ISCO occupation, bridges open-isco"),
          ("carrierFleetVid", "string", False, None, "vessel IMO, bridges open-carrier-fleet"),
          ("rank", "string", True, ["master","officer","rating","cadet"]),
          ("flagState", "string", False),
          ("embarkedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "reportWelfareBreach",
        "desc": "MLC 2006 breach (wage, rest, repatriation)",
        "fields": [
          ("breachId", "string", True),
          ("seafarerVid", "string", True, None, "bridges registerSeafarer"),
          ("breachType", "string", True, ["wage_arrears","rest_hours","repatriation","medical","abandonment","harassment"]),
          ("wagesOwedUsd", "number", False),
          ("daysOverdue", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": ("severityTier", "if breachType = \"abandonment\" then \"critical\" else if breachType = \"wage_arrears\" and daysOverdue != null and daysOverdue >= 60 then \"critical\" else if breachType = \"harassment\" then \"severe\" else \"minor\"", ["minor","severe","critical"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("seafarer_id","varchar",""),
      ("orcid","varchar",""),
      ("isco_code","varchar",""),
      ("carrier_fleet_vid","varchar",""),
      ("rank","varchar",""),
      ("flag_state","varchar",""),
      ("embarked_at","varchar",""),
      ("breach_id","varchar",""),
      ("seafarer_vid","varchar",""),
      ("breach_type","varchar",""),
      ("wages_owed_usd","double precision",""),
      ("days_overdue","int",""),
      ("reported_at","varchar",""),
      ("severity_tier","varchar",""),
      ("status","varchar",""),
      ("created_at","varchar",""),
      ("owner_did","varchar",""),
      ("sensitivity_ord","int",""),
      ("org_id","varchar",""),
      ("user_id","varchar",""),
      ("actor_id","varchar",""),
    ],
  },
]


def snake(s):
    out = []
    for ch in s:
        if ch.isupper():
            out.append("_" + ch.lower())
        else:
            out.append(ch)
    return "".join(out).lstrip("_")


def gen_lexicon(actor, method):
    app = actor["app"]
    nsid = f"com.etzhayyim.apps.{app}.{method['name']}"
    props = {}
    required = []
    for f in method["fields"]:
        name, ftype, req = f[0], f[1], f[2]
        enum = f[3] if len(f) > 3 else None
        desc = f[4] if len(f) > 4 else None
        p = {"type": ftype}
        if enum:
            p["enum"] = enum
        if desc:
            p["description"] = desc
        if ftype == "string" and name.endswith("At"):
            p["format"] = "datetime"
        props[name] = p
        if req:
            required.append(name)
    out_props = {
        "ok": {"type": "boolean"},
        "vertexId": {"type": "string"},
        "instanceKey": {"type": "integer"},
        "error": {"type": "string"},
    }
    if method.get("classify"):
        col, _expr, enum = method["classify"]
        out_props[col] = {"type": "string", "enum": enum}
    return {
        "lexicon": 1,
        "id": nsid,
        "defs": {
            "main": {
                "type": "procedure",
                "description": method["desc"],
                "input": {"encoding": "application/json", "schema": {
                    "type": "object", "required": required, "properties": props}},
                "output": {"encoding": "application/json", "schema": {
                    "type": "object", "properties": out_props}},
            }
        },
    }


def gen_bpmn(actor, method):
    slug = actor["slug"]
    app = actor["app"]
    table = f"vertex_open_{slug.replace('-', '_')}"
    proc_id = f"open_{slug.replace('-','_')}_{snake(method['name'])}"
    action = f"open{slug[0].upper()}{slug[1:].replace('-','_')}.{snake(method['name']).replace('_','.')}"
    nsid_action = f"{app}.{method['name']}.saved"
    # Build values dict
    value_parts = ["vertex_id: vertexId"]
    for f in method["fields"]:
        name = f[0]
        col = snake(name)
        value_parts.append(f"{col}: {name}")
    classify = method.get("classify")
    if classify:
        col, expr, _ = classify
        value_parts.append(f"{col}: {expr}")
    value_parts.append('status: "active"')
    value_parts.append("created_at: string(now())")
    value_parts.append("owner_did: callerDid")
    value_parts.append("sensitivity_ord: 1")
    value_parts.append("org_id: callerDid")
    value_parts.append("user_id: callerDid")
    value_parts.append(f'actor_id: "sys.bpmn.open-{slug}"')
    values_feel = "{" + ", ".join(value_parts) + "}"
    # Escape for XML attribute
    values_xml = values_feel.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_{proc_id}" targetNamespace="https://etzhayyim.com/bpmn/open-{slug}" exporter="hand-written" exporterVersion="1.0">
  <bpmn:process id="{proc_id}" name="{method['name']}" isExecutable="true">
    <bpmn:startEvent id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>
    <bpmn:serviceTask id="Task_Save" name="save">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;{table}&quot;" target="table"/><zeebe:input source="={values_xml}" target="values"/><zeebe:input source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>
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
    slug = actor["slug"]
    table = f"vertex_open_{slug.replace('-', '_')}"
    cols_sql = ",\n  ".join(f"{c[0]} {c[1]}{' ' + c[2] if c[2] else ''}" for c in actor["table_cols"])
    return f"CREATE TABLE IF NOT EXISTS {table} (\n  {cols_sql}\n);\n"


# Main generation
for a in ACTORS:
    slug = a["slug"]
    app = a["app"]
    bpmn_dir = REPO / f"00-contracts/bpmn/com/etzhayyim/open-{slug}"
    lex_dir = REPO / f"00-contracts/lexicons/com/etzhayyim/apps/{app}"
    bpmn_dir.mkdir(parents=True, exist_ok=True)
    lex_dir.mkdir(parents=True, exist_ok=True)
    for m in a["methods"]:
        (lex_dir / f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a, m), indent=2, ensure_ascii=False))
        (bpmn_dir / f"{m['name']}.bpmn").write_text(gen_bpmn(a, m))
    # DDL to stdout
    print(gen_ddl(a))
