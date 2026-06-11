#!/usr/bin/env python3
"""Wave 105: LatAm (CO/CL/PE/AR) + KP/VE sanctions + JP sports/kaigo/renewable
+ CN SASAC SOE reform on existing tables. NO DDL.
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path("/Users/junkawasaki/github/etzhayyim/root")
BPMN_ROOT = ROOT / "00-contracts/bpmn/com/etzhayyim"
LEX_ROOT = ROOT / "00-contracts/lexicons/com/etzhayyim/apps"

# (slug, lex_app, method, target_table, group_col, group_val,
#  ak_col, ak_val, aid_col, iat_col, desc)
ENTRIES_NEW = [
    ("open-us-state-dept", "usStateDept", "coordinateCoRelations",
     "vertex_open_us_state_dept", "bureau", "westernHemisphere",
     "action_kind", "coDiplomacy", "action_id", "issued_at",
     "US State: コロンビア (Cancillería CO) 二国間関係 (麻薬対策)"),
    ("open-us-state-dept", "usStateDept", "coordinateClRelations",
     "vertex_open_us_state_dept", "bureau", "westernHemisphere",
     "action_kind", "clDiplomacy", "action_id", "issued_at",
     "US State: チリ (Cancillería CL) 二国間関係 (リチウム/銅)"),
    ("open-us-state-dept", "usStateDept", "coordinatePeRelations",
     "vertex_open_us_state_dept", "bureau", "westernHemisphere",
     "action_kind", "peDiplomacy", "action_id", "issued_at",
     "US State: ペルー (RREE PE) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateArRelations",
     "vertex_open_us_state_dept", "bureau", "westernHemisphere",
     "action_kind", "arDiplomacy", "action_id", "issued_at",
     "US State: アルゼンチン (MRECIC AR) 二国間関係調整"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionKpEntity",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "kpSanction", "action_id", "issued_at",
     "US Treasury OFAC: 北朝鮮 entity 制裁 (UNSC + 独自)"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionVeEntity",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "veSanction", "action_id", "issued_at",
     "US Treasury OFAC: ベネズエラ entity 制裁 (Maduro 体制)"),
    ("open-jp-mext", "jpMext", "fundSports",
     "vertex_open_jp_mext", "bureau", "sports",
     "action_kind", "sportsCho", "action_id", "issued_at",
     "文科省: スポーツ庁 (sportcho) 強化指定 / JOC 補助"),
    ("open-jp-mhlw", "jpMhlw", "regulateKaigo",
     "vertex_open_jp_mhlw", "bureau", "longTermCare",
     "action_kind", "kaigoFee", "action_id", "issued_at",
     "厚労省: 介護報酬改定 / 介護保険給付"),
    ("open-jp-meti", "jpMeti", "subsidizeRenewable",
     "vertex_open_jp_meti", "bureau", "energy",
     "action_kind", "renewableFit", "action_id", "issued_at",
     "経産省: 再エネ FIT/FIP 制度認定"),
    ("open-cn-state-council", "cnStateCouncil", "regulateSasac",
     "vertex_open_cn_state_council", "organ_kind", "ministry",
     "topic", "soeReform", "action_id", "issued_at",
     "国务院: 国资委 (SASAC) 国有企業改革"),
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

with open("/tmp/wave13/bind105.sql", "w") as f:
    f.write("INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, nsid, bpmn_process_id, bpmn_version, status, created_at) VALUES\n")
    f.write(",\n".join(bind_lines))
    f.write(";\n")

print(f"wrote {len(ENTRIES)} entries")
