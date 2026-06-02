#!/usr/bin/env python3
"""Wave 99: binding-extension only (no DDL) — extend existing aviation/JP-gov tables.

Each entry adds one new BPMN+lexicon+binding that inserts into an EXISTING vertex_open_*
table using its action-skeleton columns. RW DDL is not exercised; only metastore writes.
"""
from __future__ import annotations
import json, os, pathlib, textwrap

ROOT = pathlib.Path("/Users/junkawasaki/github/etzhayyim/root")
BPMN_ROOT = ROOT / "00-contracts/bpmn/com/etzhayyim"
LEX_ROOT = ROOT / "00-contracts/lexicons/com/etzhayyim/apps"

# Each entry: (bpmn_dir_slug, lex_app_camel, method, target_table, group_col, group_val,
#             action_kind_col, action_kind_val, action_id_col, issued_at_col, description)
ENTRIES = [
    ("open-jp-mlit", "jpMlit", "registerAirportSlot",
     "vertex_open_jp_mlit", "bureau", "aviation",
     "action_kind", "airportSlot", "action_id", "issued_at",
     "国土交通省: KIX/ITM/CTS/NRT/HND の空港 SLOT 配分登録"),
    ("open-jp-mlit", "jpMlit", "superviseAirline",
     "vertex_open_jp_mlit", "bureau", "aviation",
     "action_kind", "airlineSupervision", "action_id", "issued_at",
     "国土交通省: JAL/ANA 等本邦航空運送事業者監督"),
    ("open-jp-mlit", "jpMlit", "reportRunwayIncursion",
     "vertex_open_jp_mlit", "bureau", "aviation",
     "action_kind", "runwayIncursion", "action_id", "issued_at",
     "国土交通省: 滑走路侵入 (Runway Incursion) 報告"),
    ("open-iata-codeshare", "iataCodeshare", "approveSlotPair",
     "vertex_open_iata_codeshare", "scope", "slotPair",
     "agreement_kind", "slotPair", "agreement_id", "agreement_at",
     "IATA: 空港 SLOT pair codeshare 承認"),
    ("open-jp-meti", "jpMeti", "supportAviationManufacturing",
     "vertex_open_jp_meti", "bureau", "manufacturing",
     "action_kind", "aviationSubsidy", "action_id", "issued_at",
     "経産省: 航空機産業 (MRJ/SpaceJet/MHI/IHI/KHI) 支援"),
    ("open-jp-mofa", "jpMofa", "negotiateAirRights",
     "vertex_open_jp_mofa", "bureau", "treaty",
     "action_kind", "bilateralAirAgreement", "action_id", "issued_at",
     "外務省: 二国間航空協定 (Bermuda II / open skies) 交渉"),
    ("open-cn-state-council", "cnStateCouncil", "regulateAirCarrier",
     "vertex_open_cn_state_council", "organ_kind", "civilAviation",
     "topic", "airCarrierRegulation", "action_id", "issued_at",
     "国务院: 民航总局経由の航空運送事業者規制"),
    ("open-us-state-dept", "usStateDept", "coordinateAviationDiplomacy",
     "vertex_open_us_state_dept", "bureau", "transport",
     "action_kind", "aviationDiplomacy", "action_id", "issued_at",
     "US State: 航空外交 (open skies / sanctions / overflight) 調整"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionAirCarrier",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "airCarrierSanction", "action_id", "issued_at",
     "US Treasury OFAC: 航空運送事業者制裁"),
    ("open-cn-mofa", "cnMofa", "addressAirSovereignty",
     "vertex_open_cn_mofa", "department_kind", "treaty",
     "action_kind", "airSovereignty", "action_id", "issued_at",
     "中国外交部: 領空主権 (ADIZ / overflight) 対応"),
]

BPMN_TMPL = '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_{proc}" targetNamespace="https://etzhayyim.com/bpmn/{slug}" exporter="hand-written" exporterVersion="1.0">
  <bpmn:process id="{proc}" name="{method}" isExecutable="true">
    <bpmn:startEvent id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>
    <bpmn:serviceTask id="Task_Save" name="save">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;{table}&quot;" target="table"/><zeebe:input source="={values_expr}" target="values"/><zeebe:input source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" targetRef="Task_Audit"/>
    <bpmn:serviceTask id="Task_Audit" name="audit">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;did:web:{slug}.etzhayyim.com&quot;" target="actor"/><zeebe:input source="=&quot;open.{lex_app}.{method}&quot;" target="action"/><zeebe:input source="={{vertexId: vertexId}}" target="payload"/></zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>
    <bpmn:endEvent id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
'''

bind_lines = []

for (slug, lex_app, method, table, group_col, group_val,
     ak_col, ak_val, aid_col, iat_col, desc) in ENTRIES:
    method_snake = ''.join(['_' + c.lower() if c.isupper() else c for c in method]).lstrip('_')
    proc = f"{slug.replace('-', '_')}_{method_snake}"
    # build values FEEL expression
    parts = [
        ("vertex_id", "vertexId"),
        (aid_col, "actionId"),
    ]
    if group_val is not None:
        parts.append((group_col, f'"{group_val}"'))
    else:
        parts.append((group_col, "callerCountry"))
    parts.append((ak_col, f'"{ak_val}"'))
    parts.append(("related_actor_vid", "relatedActorVid"))
    parts.append((iat_col, "issuedAt"))
    parts.append(("status", '"active"'))
    parts.append(("created_at", "string(now())"))
    parts.append(("owner_did", "callerDid"))
    parts.append(("sensitivity_ord", "1"))
    parts.append(("org_id", "callerDid"))
    parts.append(("user_id", "callerDid"))
    parts.append(("actor_id", f'"sys.bpmn.{slug}"'))
    values_expr = "{" + ", ".join(f"{c}: {v}" for c, v in parts) + "}"
    # XML-escape quotes
    values_expr_xml = values_expr.replace('"', '&quot;')

    bpmn = BPMN_TMPL.format(
        proc=proc, slug=slug, method=method, table=table,
        values_expr=values_expr_xml, lex_app=lex_app,
    )
    out_dir = BPMN_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{method}.bpmn").write_text(bpmn)

    # lexicon
    lex_props = {
        "actionId": {"type": "string"},
        "relatedActorVid": {"type": "string"},
        "issuedAt": {"type": "string"},
        "vertexId": {"type": "string"},
    }
    lex = {
        "lexicon": 1,
        "id": f"com.etzhayyim.apps.{lex_app}.{method}",
        "defs": {
            "main": {
                "type": "procedure",
                "description": desc,
                "input": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "required": ["actionId", "issuedAt", "vertexId"],
                        "properties": lex_props,
                    },
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "required": ["vertexId"],
                        "properties": {"vertexId": {"type": "string"}},
                    },
                },
            }
        },
    }
    lex_dir = LEX_ROOT / lex_app
    lex_dir.mkdir(parents=True, exist_ok=True)
    (lex_dir / f"{method}.json").write_text(json.dumps(lex, indent=2, ensure_ascii=False))

    nsid = f"com.etzhayyim.apps.{lex_app}.{method}"
    bind_lines.append(
        f"('binding:{nsid}','{nsid}','{proc}',1,'active',now())"
    )

with open("/tmp/wave13/bind99.sql", "w") as f:
    f.write("INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, nsid, bpmn_process_id, bpmn_version, status, created_at) VALUES\n")
    f.write(",\n".join(bind_lines))
    f.write(";\n")

print(f"wrote {len(ENTRIES)} entries")
