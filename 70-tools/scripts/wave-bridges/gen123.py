#!/usr/bin/env python3
"""Wave 123: Africa (BI/CM/GW/ST/KM) + CTBT + 海洋政策 + 生涯学習
+ cn Pacific + RU shadow fleet. NO DDL.
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path("/Users/junkawasaki/github/etzhayyim/root")
BPMN_ROOT = ROOT / "00-contracts/bpmn/com/etzhayyim"
LEX_ROOT = ROOT / "00-contracts/lexicons/com/etzhayyim/apps"

# (slug, lex_app, method, target_table, group_col, group_val,
#  ak_col, ak_val, aid_col, iat_col, desc)
ENTRIES_OLD_106 = [
    ("open-us-state-dept", "usStateDept", "coordinateKzRelations",
     "vertex_open_us_state_dept", "bureau", "southCentralAsian",
     "action_kind", "kzDiplomacy", "action_id", "issued_at",
     "US State: カザフスタン (MFA-KZ) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateUzRelations",
     "vertex_open_us_state_dept", "bureau", "southCentralAsian",
     "action_kind", "uzDiplomacy", "action_id", "issued_at",
     "US State: ウズベキスタン (MFA-UZ) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateTmRelations",
     "vertex_open_us_state_dept", "bureau", "southCentralAsian",
     "action_kind", "tmDiplomacy", "action_id", "issued_at",
     "US State: トルクメニスタン (MFA-TM) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateKgRelations",
     "vertex_open_us_state_dept", "bureau", "southCentralAsian",
     "action_kind", "kgDiplomacy", "action_id", "issued_at",
     "US State: キルギス (MFA-KG) 二国間関係調整"),
    ("open-us-state-dept", "usStateDept", "coordinateTjRelations",
     "vertex_open_us_state_dept", "bureau", "southCentralAsian",
     "action_kind", "tjDiplomacy", "action_id", "issued_at",
     "US State: タジキスタン (MFA-TJ) 二国間関係調整"),
    ("open-jp-mofa", "jpMofa", "coordinateQuad",
     "vertex_open_jp_mofa", "bureau", "asianOceanian",
     "action_kind", "quadSummit", "action_id", "issued_at",
     "外務省: Quad (US-AU-IN-JP) 首脳・閣僚会議"),
    ("open-jp-mofa", "jpMofa", "coordinateIpef",
     "vertex_open_jp_mofa", "bureau", "international",
     "action_kind", "ipefFramework", "action_id", "issued_at",
     "外務省: IPEF (Indo-Pacific Economic Framework)"),
    ("open-jp-mlit", "jpMlit", "regulateMaritime",
     "vertex_open_jp_mlit", "bureau", "ports",
     "action_kind", "maritimeBureauOversight", "action_id", "issued_at",
     "国土交通省: 海事局 (MLIT-Maritime) 船員 / 船舶 / 内航"),
    ("open-cn-mofa", "cnMofa", "assertSouthChinaSea",
     "vertex_open_cn_mofa", "department_kind", "treaty",
     "action_kind", "southChinaSeaAssertion", "action_id", "issued_at",
     "中国外交部: 南シナ海主権主張 (九段線 / 仲裁判断対応)"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionCuEntity",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "cuSanction", "action_id", "issued_at",
     "US Treasury OFAC: キューバ entity 制裁 (CACR)"),
]
ENTRIES_NEW = [
    ("open-us-state-dept", "usStateDept", "coordinateBiRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "biDiplomacy", "action_id", "issued_at",
     "US State: ブルンジ (MAE BI) 二国間"),
    ("open-us-state-dept", "usStateDept", "coordinateCmRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "cmDiplomacy", "action_id", "issued_at",
     "US State: カメルーン (MINREX CM) 二国間 (Anglo-Crisis)"),
    ("open-us-state-dept", "usStateDept", "coordinateGwRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "gwDiplomacy", "action_id", "issued_at",
     "US State: ギニアビサウ (MFA GW) 二国間 (narco)"),
    ("open-us-state-dept", "usStateDept", "coordinateStRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "stDiplomacy", "action_id", "issued_at",
     "US State: サントメ・プリンシペ (MNEC ST) 二国間"),
    ("open-us-state-dept", "usStateDept", "coordinateKmRelations",
     "vertex_open_us_state_dept", "bureau", "africa",
     "action_kind", "kmDiplomacy", "action_id", "issued_at",
     "US State: コモロ (MAE KM) 二国間"),
    ("open-jp-mofa", "jpMofa", "coordinateCtbt",
     "vertex_open_jp_mofa", "bureau", "international",
     "action_kind", "ctbtTreaty", "action_id", "issued_at",
     "外務省: CTBT 包括的核実験禁止条約 (CTBTO 監視)"),
    ("open-jp-mlit", "jpMlit", "coordinateOceanPolicy",
     "vertex_open_jp_mlit", "bureau", "ports",
     "action_kind", "oceanPolicy", "action_id", "issued_at",
     "国土交通省: 海洋政策 (大陸棚 / 排他的経済水域)"),
    ("open-jp-mext", "jpMext", "fundLifelongLearning",
     "vertex_open_jp_mext", "bureau", "highered",
     "action_kind", "lifelongLearning", "action_id", "issued_at",
     "文科省: 生涯学習 (公民館 / 社会教育士)"),
    ("open-cn-mofa", "cnMofa", "engagePacificStates",
     "vertex_open_cn_mofa", "department_kind", "treaty",
     "action_kind", "pacificEngage", "action_id", "issued_at",
     "中国外交部: 太平洋島嶼国 engagement (Solomon / Kiribati)"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionShadowFleet",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "ruShadowFleet", "action_id", "issued_at",
     "US Treasury OFAC: ロシア shadow fleet (oil price cap evasion) 制裁"),
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

with open("/tmp/wave13/bind123.sql", "w") as f:
    f.write("INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, nsid, bpmn_process_id, bpmn_version, status, created_at) VALUES\n")
    f.write(",\n".join(bind_lines))
    f.write(";\n")

print(f"wrote {len(ENTRIES)} entries")
