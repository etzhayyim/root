#!/usr/bin/env python3
"""Wave 117: micro-states (MC/SM/AD/LI/MT) + Japan Foundation + 博物館 + 自然資源
+ TD/GN sanctions. NO DDL.
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
    ("open-us-state-dept", "usStateDept", "coordinateMcRelations",
     "vertex_open_us_state_dept", "bureau", "european",
     "action_kind", "mcDiplomacy", "action_id", "issued_at",
     "US State: モナコ (DAEC MC) 二国間 (フランス保護)"),
    ("open-us-state-dept", "usStateDept", "coordinateSmRelations",
     "vertex_open_us_state_dept", "bureau", "european",
     "action_kind", "smDiplomacy", "action_id", "issued_at",
     "US State: サンマリノ (MAE SM) 二国間"),
    ("open-us-state-dept", "usStateDept", "coordinateAdRelations",
     "vertex_open_us_state_dept", "bureau", "european",
     "action_kind", "adDiplomacy", "action_id", "issued_at",
     "US State: アンドラ (MAE AD) 二国間 (仏西共同領主)"),
    ("open-us-state-dept", "usStateDept", "coordinateLiRelations",
     "vertex_open_us_state_dept", "bureau", "european",
     "action_kind", "liDiplomacy", "action_id", "issued_at",
     "US State: リヒテンシュタイン (MAEH LI) 二国間 (EEA / 銀行)"),
    ("open-us-state-dept", "usStateDept", "coordinateMtRelations",
     "vertex_open_us_state_dept", "bureau", "european",
     "action_kind", "mtDiplomacy", "action_id", "issued_at",
     "US State: マルタ (MFEA MT) 二国間 (船籍 / EU)"),
    ("open-jp-mofa", "jpMofa", "coordinateJapanFoundation",
     "vertex_open_jp_mofa", "bureau", "international",
     "action_kind", "japanFoundation", "action_id", "issued_at",
     "外務省: 国際交流基金 (Japan Foundation) 文化外交"),
    ("open-jp-mext", "jpMext", "fundMuseum",
     "vertex_open_jp_mext", "bureau", "culture",
     "action_kind", "museumGrant", "action_id", "issued_at",
     "文科省: 博物館 (国立科博 / 国博 / 美博) 補助"),
    ("open-cn-state-council", "cnStateCouncil", "regulateNaturalResources",
     "vertex_open_cn_state_council", "organ_kind", "ministry",
     "topic", "naturalResources", "action_id", "issued_at",
     "国务院: 自然資源部 (土地 / 鉱物 / 海洋資源)"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionTdEntity",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "tdSanction", "action_id", "issued_at",
     "US Treasury OFAC: チャド entity 制裁"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionGnEntity",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "gnSanction", "action_id", "issued_at",
     "US Treasury OFAC: ギニア (CNRD junta) entity 制裁"),
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

with open("/tmp/wave13/bind117.sql", "w") as f:
    f.write("INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, nsid, bpmn_process_id, bpmn_version, status, created_at) VALUES\n")
    f.write(",\n".join(bind_lines))
    f.write(";\n")

print(f"wrote {len(ENTRIES)} entries")
