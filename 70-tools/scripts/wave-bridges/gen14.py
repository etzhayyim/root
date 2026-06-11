#!/usr/bin/env python3
"""Wave 14 bridge actor generator — 5 actors × 2 NSIDs each.
Tying newly-persisting Wave 12/13 bridges into deeper dependency chains.
"""
import json
from pathlib import Path

REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "commodity-physical-delivery",
    "app": "commodityPhysicalDelivery",
    "methods": [
      {
        "name": "recordDelivery",
        "desc": "Physical delivery of commodity futures (commodity-trade+refiner-product+hormuz-cargo bridge)",
        "fields": [
          ("deliveryId", "string", True),
          ("settlementVid", "string", True, None, "bridges open-commodity-trade settleContract"),
          ("refinerReceiptVid", "string", False, None, "bridges open-refiner-product / open-asia-refinery"),
          ("hormuzCargoVid", "string", False, None, "bridges open-hormuz-cargo"),
          ("customsClearanceVid", "string", False, None, "bridges open-customs-clearance"),
          ("deliveryPortVid", "string", False),
          ("volumeBbl", "number", True),
          ("deliveredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "recordStorageBalance",
        "desc": "Storage terminal balance after delivery",
        "fields": [
          ("balanceId", "string", True),
          ("deliveryVid", "string", True, None, "bridges recordDelivery"),
          ("terminalPortVid", "string", False),
          ("openingBbl", "number", False),
          ("closingBbl", "number", True),
          ("daysToCovered", "number", False),
          ("recordedAt", "string", True),
        ],
        "classify": ("inventoryTier", "if daysToCovered != null and daysToCovered < 15 then \"critical\" else if daysToCovered != null and daysToCovered < 30 then \"tight\" else \"adequate\"", ["critical","tight","adequate"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("delivery_id","varchar",""),
      ("settlement_vid","varchar",""),
      ("refiner_receipt_vid","varchar",""),
      ("hormuz_cargo_vid","varchar",""),
      ("customs_clearance_vid","varchar",""),
      ("delivery_port_vid","varchar",""),
      ("volume_bbl","double precision",""),
      ("delivered_at","varchar",""),
      ("balance_id","varchar",""),
      ("delivery_vid","varchar",""),
      ("terminal_port_vid","varchar",""),
      ("opening_bbl","double precision",""),
      ("closing_bbl","double precision",""),
      ("days_to_covered","double precision",""),
      ("recorded_at","varchar",""),
      ("inventory_tier","varchar",""),
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
    "slug": "seafarer-academy",
    "app": "seafarerAcademy",
    "methods": [
      {
        "name": "issueStcwCertificate",
        "desc": "STCW 2010 seafarer certificate (crew-welfare+isco+orcid bridge)",
        "fields": [
          ("certificateId", "string", True),
          ("seafarerVid", "string", True, None, "bridges open-crew-welfare registerSeafarer"),
          ("orcid", "string", False, None, "bridges open-orcid"),
          ("iscoCode", "string", False, None, "bridges open-isco"),
          ("stcwChapter", "string", True, ["II","III","IV","V","VI","VII"]),
          ("flagState", "string", True),
          ("issuedAt", "string", True),
          ("expiresAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "logTrainingCourse",
        "desc": "Seafarer training course completion",
        "fields": [
          ("courseId", "string", True),
          ("seafarerVid", "string", True, None, "bridges open-crew-welfare"),
          ("courseCode", "string", True),
          ("providerLei", "string", False),
          ("hoursCompleted", "integer", True),
          ("competencyLevel", "string", True, ["management","operational","support"]),
          ("completedAt", "string", True),
        ],
        "classify": ("outcomeTier", "if hoursCompleted >= 200 then \"certified\" else if hoursCompleted >= 40 then \"familiarization\" else \"orientation\"", ["orientation","familiarization","certified"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("certificate_id","varchar",""),
      ("seafarer_vid","varchar",""),
      ("orcid","varchar",""),
      ("isco_code","varchar",""),
      ("stcw_chapter","varchar",""),
      ("flag_state","varchar",""),
      ("issued_at","varchar",""),
      ("expires_at","varchar",""),
      ("course_id","varchar",""),
      ("course_code","varchar",""),
      ("provider_lei","varchar",""),
      ("hours_completed","int",""),
      ("competency_level","varchar",""),
      ("completed_at","varchar",""),
      ("outcome_tier","varchar",""),
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
    "slug": "trade-finance-factoring",
    "app": "tradeFinanceFactoring",
    "methods": [
      {
        "name": "purchaseInvoice",
        "desc": "Invoice factoring (supply-chain-finance+customs+banking bridge)",
        "fields": [
          ("factoringId", "string", True),
          ("lcVid", "string", False, None, "bridges open-supply-chain-finance L/C"),
          ("customsDeclarationVid", "string", False, None, "bridges open-customs-clearance"),
          ("bankingAccountVid", "string", False, None, "bridges open-banking"),
          ("swiftUetr", "string", False, None, "bridges open-swift"),
          ("invoiceFaceValueUsd", "number", True),
          ("advanceRatePct", "number", True),
          ("tenorDays", "integer", True),
          ("sellerLei", "string", False),
          ("buyerLei", "string", False),
          ("purchasedAt", "string", True),
        ],
        "classify": ("riskTier", "if tenorDays > 180 then \"long_tail\" else if advanceRatePct > 90 then \"high_advance\" else \"standard\"", ["standard","high_advance","long_tail"]),
      },
      {
        "name": "recordRepayment",
        "desc": "Buyer repayment against factored invoice",
        "fields": [
          ("repaymentId", "string", True),
          ("factoringVid", "string", True, None, "bridges purchaseInvoice"),
          ("amountUsd", "number", True),
          ("daysLate", "integer", False),
          ("paidAt", "string", True),
        ],
        "classify": ("performanceTier", "if daysLate != null and daysLate >= 30 then \"default\" else if daysLate != null and daysLate > 0 then \"delayed\" else \"on_time\"", ["on_time","delayed","default"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("factoring_id","varchar",""),
      ("lc_vid","varchar",""),
      ("customs_declaration_vid","varchar",""),
      ("banking_account_vid","varchar",""),
      ("swift_uetr","varchar",""),
      ("invoice_face_value_usd","double precision",""),
      ("advance_rate_pct","double precision",""),
      ("tenor_days","int",""),
      ("seller_lei","varchar",""),
      ("buyer_lei","varchar",""),
      ("purchased_at","varchar",""),
      ("risk_tier","varchar",""),
      ("repayment_id","varchar",""),
      ("factoring_vid","varchar",""),
      ("amount_usd","double precision",""),
      ("days_late","int",""),
      ("paid_at","varchar",""),
      ("performance_tier","varchar",""),
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
    "slug": "port-of-call-roster",
    "app": "portOfCallRoster",
    "methods": [
      {
        "name": "recordCall",
        "desc": "Vessel port call roster (carrier-schedule+biosecurity+customs+crew bridge)",
        "fields": [
          ("callId", "string", True),
          ("carrierScheduleVid", "string", False, None, "bridges open-carrier-schedule"),
          ("biosecurityInspectionVid", "string", False, None, "bridges open-biosecurity"),
          ("customsClearanceVid", "string", False, None, "bridges open-customs-clearance"),
          ("imo", "string", True, None, "vessel IMO"),
          ("portVid", "string", True),
          ("arrivedAt", "string", True),
          ("departedAt", "string", False),
          ("cargoOperation", "string", False, ["load","discharge","transit","bunker"]),
        ],
        "classify": None,
      },
      {
        "name": "logCrewChange",
        "desc": "Crew sign-on / sign-off at port call",
        "fields": [
          ("crewChangeId", "string", True),
          ("callVid", "string", True, None, "bridges recordCall"),
          ("seafarerVid", "string", False, None, "bridges open-crew-welfare"),
          ("direction", "string", True, ["sign_on","sign_off","transfer"]),
          ("changedAt", "string", True),
        ],
        "classify": None,
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("call_id","varchar",""),
      ("carrier_schedule_vid","varchar",""),
      ("biosecurity_inspection_vid","varchar",""),
      ("customs_clearance_vid","varchar",""),
      ("imo","varchar",""),
      ("port_vid","varchar",""),
      ("arrived_at","varchar",""),
      ("departed_at","varchar",""),
      ("cargo_operation","varchar",""),
      ("crew_change_id","varchar",""),
      ("call_vid","varchar",""),
      ("seafarer_vid","varchar",""),
      ("direction","varchar",""),
      ("changed_at","varchar",""),
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
    "slug": "biosecurity-certification",
    "app": "biosecurityCertification",
    "methods": [
      {
        "name": "issueBwmCertificate",
        "desc": "IMO BWM / AFS / ISPP certificate (biosecurity+carrier-fleet bridge)",
        "fields": [
          ("certId", "string", True),
          ("biosecurityInspectionVid", "string", False, None, "bridges open-biosecurity"),
          ("imo", "string", True),
          ("certType", "string", True, ["BWM","AFS","ISPP","SOPEP","IOPP"]),
          ("issuingAuthorityLei", "string", False),
          ("issuedAt", "string", True),
          ("expiresAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPscDetention",
        "desc": "Port State Control detention linked to biosecurity failure",
        "fields": [
          ("detentionId", "string", True),
          ("callVid", "string", False, None, "bridges open-port-of-call-roster"),
          ("imo", "string", True),
          ("pscRegimeMou", "string", False, ["tokyo","paris","viña","caribbean","mediterranean","indian_ocean","black_sea","west_central_africa","riyadh"]),
          ("deficiencyCode", "string", False),
          ("detainedHours", "integer", True),
          ("detainedAt", "string", True),
        ],
        "classify": ("severityTier", "if detainedHours >= 168 then \"prolonged\" else if detainedHours >= 48 then \"significant\" else \"brief\"", ["brief","significant","prolonged"]),
      },
    ],
    "table_cols": [
      ("vertex_id","varchar","PRIMARY KEY"),
      ("cert_id","varchar",""),
      ("biosecurity_inspection_vid","varchar",""),
      ("imo","varchar",""),
      ("cert_type","varchar",""),
      ("issuing_authority_lei","varchar",""),
      ("issued_at","varchar",""),
      ("expires_at","varchar",""),
      ("detention_id","varchar",""),
      ("call_vid","varchar",""),
      ("psc_regime_mou","varchar",""),
      ("deficiency_code","varchar",""),
      ("detained_hours","int",""),
      ("detained_at","varchar",""),
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
    nsid = f"com.etzhayyim.apps.{actor['app']}.{method['name']}"
    props = {}
    required = []
    for f in method["fields"]:
        name, ftype, req = f[0], f[1], f[2]
        enum = f[3] if len(f) > 3 else None
        desc = f[4] if len(f) > 4 else None
        p = {"type": ftype}
        if enum: p["enum"] = enum
        if desc: p["description"] = desc
        if ftype == "string" and name.endswith("At"): p["format"] = "datetime"
        props[name] = p
        if req: required.append(name)
    out_props = {"ok":{"type":"boolean"},"vertexId":{"type":"string"},"instanceKey":{"type":"integer"},"error":{"type":"string"}}
    if method.get("classify"):
        col,_,enum = method["classify"]
        out_props[col] = {"type":"string","enum":enum}
    return {"lexicon":1,"id":nsid,"defs":{"main":{"type":"procedure","description":method["desc"],
        "input":{"encoding":"application/json","schema":{"type":"object","required":required,"properties":props}},
        "output":{"encoding":"application/json","schema":{"type":"object","properties":out_props}}}}}


def gen_bpmn(actor, method):
    slug = actor["slug"]
    table = f"vertex_open_{slug.replace('-','_')}"
    proc_id = f"open_{slug.replace('-','_')}_{snake(method['name'])}"
    action = f"open.{actor['app']}.{method['name']}"
    vparts = ["vertex_id: vertexId"]
    for f in method["fields"]:
        name = f[0]; col = snake(name)
        vparts.append(f"{col}: {name}")
    if method.get("classify"):
        col, expr, _ = method["classify"]
        vparts.append(f"{col}: {expr}")
    vparts += ['status: "active"','created_at: string(now())','owner_did: callerDid','sensitivity_ord: 1','org_id: callerDid','user_id: callerDid',f'actor_id: "sys.bpmn.open-{slug}"']
    feel = "{" + ", ".join(vparts) + "}"
    xml_feel = feel.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_{proc_id}" targetNamespace="https://etzhayyim.com/bpmn/open-{slug}" exporter="hand-written" exporterVersion="1.0">
  <bpmn:process id="{proc_id}" name="{method['name']}" isExecutable="true">
    <bpmn:startEvent id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>
    <bpmn:serviceTask id="Task_Save" name="save">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;{table}&quot;" target="table"/><zeebe:input source="={xml_feel}" target="values"/><zeebe:input source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>
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
    slug = actor["slug"]; table = f"vertex_open_{slug.replace('-','_')}"
    cols = ",\n  ".join(f"{c[0]} {c[1]}{' '+c[2] if c[2] else ''}" for c in actor["table_cols"])
    return f"CREATE TABLE IF NOT EXISTS {table} (\n  {cols}\n);\n"


for a in ACTORS:
    bpmn_dir = REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    lex_dir = REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bpmn_dir.mkdir(parents=True, exist_ok=True); lex_dir.mkdir(parents=True, exist_ok=True)
    for m in a["methods"]:
        (lex_dir/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bpmn_dir/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    print(gen_ddl(a))
