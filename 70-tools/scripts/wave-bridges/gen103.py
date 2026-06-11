#!/usr/bin/env python3
"""Wave 103: Africa pivots + JP local (SME/university/labor) + UN agency coord
on existing tables (us_state_dept / jp_meti / jp_mext / jp_mhlw / jp_mofa). NO DDL.
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path("/Users/junkawasaki/github/etzhayyim/root")
BPMN_ROOT = ROOT / "00-contracts/bpmn/com/etzhayyim"
LEX_ROOT = ROOT / "00-contracts/lexicons/com/etzhayyim/apps"

# (slug, lex_app, method, target_table, group_col, group_val,
#  ak_col, ak_val, aid_col, iat_col, desc)
ENTRIES_NEW = [
    ("open-us-state-dept", "usStateDept", "coordinateNgRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "ngDiplomacy", "action_id", "issued_at",
     "US State: ナイジェリア (MFA-NG) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateKeRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "keDiplomacy", "action_id", "issued_at",
     "US State: ケニア (MFA-KE) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateEtRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "etDiplomacy", "action_id", "issued_at",
     "US State: エチオピア (MFA-ET) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateMaRelations",
     "vertex_open_us_state_dept", "bureau", "nearEastern",
     "action_kind", "maDiplomacy", "action_id", "issued_at",
     "US State: モロッコ (MFA-MA) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateSnRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "snDiplomacy", "action_id", "issued_at",
     "US State: セネガル (MFA-SN) 二国間関係調整"),
    ("open-jp-meti", "jpMeti", "supportSme",
     "vertex_open_jp_meti", "bureau", "manufacturing",
     "action_kind", "smeFinance", "action_id", "issued_at",
     "経産省: 中小企業庁 金融支援 (信用保証 / セーフティネット)"),
    ("open-jp-mext", "jpMext", "supportUniversity",
     "vertex_open_jp_mext", "bureau", "highered",
     "action_kind", "universityFunding", "action_id", "issued_at",
     "文科省: 国立大学法人運営費交付金 / 私学助成"),
    ("open-jp-mhlw", "jpMhlw", "regulateLaborStandard",
     "vertex_open_jp_mhlw", "bureau", "labor",
     "action_kind", "laborStandardEnforcement", "action_id", "issued_at",
     "厚労省: 労働基準監督署是正勧告"),
    ("open-jp-mofa", "jpMofa", "coordinateUnhcr",
     "vertex_open_jp_mofa", "bureau", "international",
     "action_kind", "unhcrCoord", "action_id", "issued_at",
     "外務省: UNHCR (国連難民高等弁務官) 連携 / 拠出"),
    ("open-jp-mofa", "jpMofa", "coordinateWho",
     "vertex_open_jp_mofa", "bureau", "international",
     "action_kind", "whoCoord", "action_id", "issued_at",
     "外務省: WHO (世界保健機関) 連携 / 拠出"),
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

with open("/tmp/wave13/bind103.sql", "w") as f:
    f.write("INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, nsid, bpmn_process_id, bpmn_version, status, created_at) VALUES\n")
    f.write(",\n".join(bind_lines))
    f.write(";\n")

print(f"wrote {len(ENTRIES)} entries")
