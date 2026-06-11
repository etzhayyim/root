#!/usr/bin/env python3
"""Wave 127: city/multilateral diplomacy (sister cities/Mayors Climate/IPA/JICA)
+ 私学助成 + 文化和旅游部 + piracy/CT EOs. NO DDL.
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
ENTRIES_OLD_125 = [
    ("open-us-state-dept", "usStateDept", "coordinateLaRelations",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "laDiplomacy", "action_id", "issued_at",
     "US State: ラオス (MoFA LA) 二国間 (UXO / dam)"),
    ("open-us-state-dept", "usStateDept", "coordinateKhRelations",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "khDiplomacy", "action_id", "issued_at",
     "US State: カンボジア (MoFAIC KH) 二国間 (Ream基地)"),
    ("open-us-state-dept", "usStateDept", "coordinateMmDialog",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "mmNugDialog", "action_id", "issued_at",
     "US State: ミャンマー NUG (Tatmadaw 非対話) 国民統一政府"),
    ("open-us-state-dept", "usStateDept", "coordinateBnRelations",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "bnDiplomacy", "action_id", "issued_at",
     "US State: ブルネイ (MFA BN) 二国間 (oil)"),
    ("open-us-state-dept", "usStateDept", "coordinateTlRelations",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "tlDiplomacy", "action_id", "issued_at",
     "US State: 東ティモール (MNEC TL) 二国間 (ASEAN obs)"),
    ("open-jp-mofa", "jpMofa", "coordinateDavosWef",
     "vertex_open_jp_mofa", "bureau", "international",
     "action_kind", "davosWef", "action_id", "issued_at",
     "外務省: Davos / WEF (世界経済フォーラム) 年次総会"),
    ("open-jp-mlit", "jpMlit", "regulateRivers",
     "vertex_open_jp_mlit", "bureau", "river",
     "action_kind", "riverBureauOversight", "action_id", "issued_at",
     "国土交通省: 河川局 (一級河川 / ダム / 治水)"),
    ("open-jp-mext", "jpMext", "fundUniversityScheme",
     "vertex_open_jp_mext", "bureau", "highered",
     "action_kind", "universityScheme", "action_id", "issued_at",
     "文科省: 高等教育 (大学院 / 国際卓越研究大学)"),
    ("open-cn-state-council", "cnStateCouncil", "regulatePublicSecurity",
     "vertex_open_cn_state_council", "organ_kind", "ministry",
     "topic", "publicSecurity", "action_id", "issued_at",
     "国务院: 公安部 (出入境管理 / 戸籍 / 治安)"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionRuIndustrial",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "ruIndustrial", "action_id", "issued_at",
     "US Treasury OFAC: ロシア工業 (defense / dual-use) entity 制裁"),
]
ENTRIES_OLD_126 = [
    ("open-us-state-dept", "usStateDept", "coordinateTwTra",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "twTraLink", "action_id", "issued_at",
     "US State: 台湾 (TRA / AIT) 関係 (one China policy / TRA)"),
    ("open-us-state-dept", "usStateDept", "coordinateHkLink",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "hkSarLink", "action_id", "issued_at",
     "US State: 香港 SAR (NSL post-2020) 関係"),
    ("open-us-state-dept", "usStateDept", "coordinateMoLink",
     "vertex_open_us_state_dept", "bureau", "eastAsianPacific",
     "action_kind", "moSarLink", "action_id", "issued_at",
     "US State: マカオ SAR (Basic Law 2049) 関係"),
    ("open-us-state-dept", "usStateDept", "coordinatePrLink",
     "vertex_open_us_state_dept", "bureau", "westernHemisphere",
     "action_kind", "prTerritoryLink", "action_id", "issued_at",
     "US State: プエルトリコ (US territory / Commonwealth) 統治"),
    ("open-us-state-dept", "usStateDept", "coordinateGiLink",
     "vertex_open_us_state_dept", "bureau", "european",
     "action_kind", "giOverseasLink", "action_id", "issued_at",
     "US State: ジブラルタル (UK overseas territory) 関係"),
    ("open-jp-mofa", "jpMofa", "coordinateJCelac",
     "vertex_open_jp_mofa", "bureau", "asianOceanian",
     "action_kind", "jCelacForum", "action_id", "issued_at",
     "外務省: 日 CELAC ラテンアメリカ・カリブ協力"),
    ("open-jp-mlit", "jpMlit", "coordinateDisasterRecovery",
     "vertex_open_jp_mlit", "bureau", "city_planning",
     "action_kind", "disasterRecovery", "action_id", "issued_at",
     "国土交通省: 災害復旧 (激甚災害 / 復興庁連携)"),
    ("open-jp-meti", "jpMeti", "regulatePiProtection",
     "vertex_open_jp_meti", "bureau", "manufacturing",
     "action_kind", "piProtection", "action_id", "issued_at",
     "経産省: 個人情報保護 (個情委連携 / EU GDPR adequacy)"),
    ("open-cn-state-council", "cnStateCouncil", "regulateJustice",
     "vertex_open_cn_state_council", "organ_kind", "ministry",
     "topic", "justice", "action_id", "issued_at",
     "国务院: 司法部 (法律援助 / 司法行政 / 監獄)"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionIrgc",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "irgcDepth", "action_id", "issued_at",
     "US Treasury OFAC: IRGC (革命防衛隊 / Quds Force) 制裁深堀"),
]
ENTRIES_NEW = [
    ("open-us-state-dept", "usStateDept", "coordinateSisterCities",
     "vertex_open_us_state_dept", "bureau", "westernHemisphere",
     "action_kind", "sisterCityProgram", "action_id", "issued_at",
     "US State: Sister Cities Intl 都市間交流 (cultural diplomacy)"),
    ("open-us-state-dept", "usStateDept", "coordinateMayorsClimate",
     "vertex_open_us_state_dept", "bureau", "europe",
     "action_kind", "mayorsClimate", "action_id", "issued_at",
     "US State: Climate Mayors / C40 Cities (sub-national気候)"),
    ("open-jp-mofa", "jpMofa", "coordinateSpecialAdvisor",
     "vertex_open_jp_mofa", "bureau", "international",
     "action_kind", "specialAdvisor", "action_id", "issued_at",
     "外務省: 内閣総理大臣補佐官 / 特別代表 (PMの外交特使)"),
    ("open-jp-mofa", "jpMofa", "coordinateMetropolisNetwork",
     "vertex_open_jp_mofa", "bureau", "asianOceanian",
     "action_kind", "metropolisNetwork", "action_id", "issued_at",
     "外務省: Metropolis (世界大都市協会) / Asia City"),
    ("open-jp-mofa", "jpMofa", "coordinateAseanRf",
     "vertex_open_jp_mofa", "bureau", "asianOceanian",
     "action_kind", "aseanRf", "action_id", "issued_at",
     "外務省: ARF (ASEAN Regional Forum) 安全保障対話"),
    ("open-jp-mlit", "jpMlit", "coordinateJicaInfra",
     "vertex_open_jp_mlit", "bureau", "city_planning",
     "action_kind", "jicaInfra", "action_id", "issued_at",
     "国土交通省: JICA インフラ協力 (infra ODA)"),
    ("open-jp-mext", "jpMext", "fundPrivateSchool",
     "vertex_open_jp_mext", "bureau", "highered",
     "action_kind", "privateSchoolGrant", "action_id", "issued_at",
     "文科省: 私学助成 (経常費補助 / 学校法人助成)"),
    ("open-cn-state-council", "cnStateCouncil", "regulateCultureTourism",
     "vertex_open_cn_state_council", "organ_kind", "ministry",
     "topic", "cultureTourism", "action_id", "issued_at",
     "国务院: 文化和旅游部 (文物 / 旅游 / 出版)"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionPiracyEo",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "piracyEo", "action_id", "issued_at",
     "US Treasury OFAC: 海賊・武装襲撃 entity 制裁 (EO 13536)"),
    ("open-us-treasury-dept", "usTreasuryDept", "sanctionCt13224",
     "vertex_open_us_treasury_dept", "sub_agency", "ofac",
     "action_kind", "ctEo13224", "action_id", "issued_at",
     "US Treasury OFAC: テロリスト関連 entity (EO 13224 SDGT)"),
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

with open(str(pathlib.Path(__file__).parent / "bind127.sql"), "w") as f:
    f.write("INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, nsid, bpmn_process_id, bpmn_version, status, created_at) VALUES\n")
    f.write(",\n".join(bind_lines))
    f.write(";\n")

print(f"wrote {len(ENTRIES)} entries")
