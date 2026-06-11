#!/usr/bin/env python3
"""Wave 100: binding-extension only — UK/DE/FR/BR/IN pivots on existing aggregator
tables (us_state_dept / us_treasury_dept / cn_state_council / jp_mofa / jp_mlit /
iata_codeshare). NO DDL.
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path("/Users/junkawasaki/github/etzhayyim/root")
BPMN_ROOT = ROOT / "00-contracts/bpmn/com/etzhayyim"
LEX_ROOT = ROOT / "00-contracts/lexicons/com/etzhayyim/apps"

# (slug, lex_app, method, target_table, group_col, group_val,
#  ak_col, ak_val, aid_col, iat_col, desc)
ENTRIES = [
    ("open-us-state-dept", "usStateDept", "coordinateUkRelations",
     "vertex_open_us_state_dept", "bureau", "european",
     "action_kind", "ukDiplomacy", "action_id", "issued_at",
     "US State: 英国 (UK FCDO) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateDeRelations",
     "vertex_open_us_state_dept", "bureau", "european",
     "action_kind", "deDiplomacy", "action_id", "issued_at",
     "US State: ドイツ (Auswärtiges Amt) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateFrRelations",
     "vertex_open_us_state_dept", "bureau", "european",
     "action_kind", "frDiplomacy", "action_id", "issued_at",
     "US State: フランス (Quai d'Orsay) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateBrRelations",
     "vertex_open_us_state_dept", "bureau", "westernHemisphere",
     "action_kind", "brDiplomacy", "action_id", "issued_at",
     "US State: ブラジル (Itamaraty) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateInRelations",
     "vertex_open_us_state_dept", "bureau", "southCentralAsian",
     "action_kind", "inDiplomacy", "action_id", "issued_at",
     "US State: インド (MEA) 二国間関係調整"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionDeEntity",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "deSanction", "action_id", "issued_at",
     "US Treasury OFAC: ドイツ entity 制裁"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionInEntity",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "inSanction", "action_id", "issued_at",
     "US Treasury OFAC: インド entity 制裁"),
    ("open-cn-state-council", "cnStateCouncil", "coordinateBeltAndRoad",
     "vertex_open_cn_state_council", "organ_kind", "mfa",
     "topic", "beltAndRoad", "action_id", "issued_at",
     "国务院: 一帯一路 (BRI) 重大政策調整"),
    ("open-jp-mlit", "jpMlit", "regulateCargoAirline",
     "vertex_open_jp_mlit", "bureau", "aviation",
     "action_kind", "cargoAirline", "action_id", "issued_at",
     "国土交通省: 貨物航空運送事業者規制 (NCA等)"),
    ("open-iata-codeshare", "iataCodeshare", "approveCargoCodeshare",
     "vertex_open_iata_codeshare", "scope", "cargo",
     "agreement_kind", "cargoCodeshare", "agreement_id", "agreement_at",
     "IATA: 貨物 codeshare 協定承認"),
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
    parts = [
        ("vertex_id", "vertexId"),
        (aid_col, "actionId"),
        (group_col, f'"{group_val}"'),
        (ak_col, f'"{ak_val}"'),
        ("related_actor_vid", "relatedActorVid"),
        (iat_col, "issuedAt"),
        ("status", '"active"'),
        ("created_at", "string(now())"),
        ("owner_did", "callerDid"),
        ("sensitivity_ord", "1"),
        ("org_id", "callerDid"),
        ("user_id", "callerDid"),
        ("actor_id", f'"sys.bpmn.{slug}"'),
    ]
    values_expr = "{" + ", ".join(f"{c}: {v}" for c, v in parts) + "}"
    values_expr_xml = values_expr.replace('"', '&quot;')
    bpmn = BPMN_TMPL.format(
        proc=proc, slug=slug, method=method, table=table,
        values_expr=values_expr_xml, lex_app=lex_app,
    )
    out_dir = BPMN_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{method}.bpmn").write_text(bpmn)

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
                        "properties": {
                            "actionId": {"type": "string"},
                            "relatedActorVid": {"type": "string"},
                            "issuedAt": {"type": "string"},
                            "vertexId": {"type": "string"},
                        },
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
    bind_lines.append(f"('binding:{nsid}','{nsid}','{proc}',1,'active',now())")

with open("/tmp/wave13/bind100.sql", "w") as f:
    f.write("INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, nsid, bpmn_process_id, bpmn_version, status, created_at) VALUES\n")
    f.write(",\n".join(bind_lines))
    f.write(";\n")

print(f"wrote {len(ENTRIES)} entries")
