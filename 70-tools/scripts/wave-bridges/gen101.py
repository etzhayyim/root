#!/usr/bin/env python3
"""Wave 101: KR/AU/CA/MX/ZA pivots + ASEAN/MRO/groundhandling/pilot-training
on existing tables (us_state_dept / jp_mofa / jp_mlit / iata_codeshare). NO DDL.
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path("/Users/junkawasaki/github/etzhayyim/root")
BPMN_ROOT = ROOT / "00-contracts/bpmn/com/etzhayyim"
LEX_ROOT = ROOT / "00-contracts/lexicons/com/etzhayyim/apps"

# (slug, lex_app, method, target_table, group_col, group_val,
#  ak_col, ak_val, aid_col, iat_col, desc)
ENTRIES_NEW = [
    ("open-us-state-dept", "usStateDept", "coordinateKrRelations",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "krDiplomacy", "action_id", "issued_at",
     "US State: 韓国 (MOFA-KR) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateAuRelations",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "auDiplomacy", "action_id", "issued_at",
     "US State: 豪州 (DFAT) 二国間関係調整 (AUKUS等)"),
    ("open-us-state-dept", "usStateDept", "coordinateCaRelations",
     "vertex_open_us_state_dept", "bureau", "westernHemisphere",
     "action_kind", "caDiplomacy", "action_id", "issued_at",
     "US State: カナダ (GAC) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateMxRelations",
     "vertex_open_us_state_dept", "bureau", "westernHemisphere",
     "action_kind", "mxDiplomacy", "action_id", "issued_at",
     "US State: メキシコ (SRE) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateZaRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "zaDiplomacy", "action_id", "issued_at",
     "US State: 南アフリカ (DIRCO) 二国間関係調整"),
    ("open-jp-mofa", "jpMofa", "handleKrSummit",
     "vertex_open_jp_mofa", "bureau", "asianOceanian",
     "action_kind", "krSummit", "action_id", "issued_at",
     "外務省: 日韓首脳会談"),
    ("open-jp-mofa", "jpMofa", "handleAseanSummit",
     "vertex_open_jp_mofa", "bureau", "asianOceanian",
     "action_kind", "aseanSummit", "action_id", "issued_at",
     "外務省: 日 ASEAN 首脳会談"),
    ("open-jp-mlit", "jpMlit", "regulateMro",
     "vertex_open_jp_mlit", "bureau", "aviation",
     "action_kind", "mroOversight", "action_id", "issued_at",
     "国土交通省: 航空機整備 (MRO) 監督 (Part-145)"),
    ("open-jp-mlit", "jpMlit", "regulateGroundhandling",
     "vertex_open_jp_mlit", "bureau", "aviation",
     "action_kind", "groundhandlingOversight", "action_id", "issued_at",
     "国土交通省: 空港地上業務 (groundhandling) 監督"),
    ("open-iata-codeshare", "iataCodeshare", "approvePilotTraining",
     "vertex_open_iata_codeshare", "scope", "training",
     "agreement_kind", "pilotTraining", "agreement_id", "agreement_at",
     "IATA: 操縦士訓練 (Type Rating / ATPL) 協定承認"),
]
ENTRIES = ENTRIES_NEW

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

with open("/tmp/wave13/bind101.sql", "w") as f:
    f.write("INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, nsid, bpmn_process_id, bpmn_version, status, created_at) VALUES\n")
    f.write(",\n".join(bind_lines))
    f.write(";\n")

print(f"wrote {len(ENTRIES)} entries")
