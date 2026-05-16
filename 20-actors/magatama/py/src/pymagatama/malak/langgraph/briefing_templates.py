"""briefing_templates — markdown renderers for malak.surveillance agency briefings.

Each `render_*` function takes `facts: dict` + `briefing_no: str` and returns
markdown for one section. The orchestrator (briefing.py) calls them in order
and joins them with `\\n---\\n`. After rendering, the entity extractor scans
the markdown text and the structured `facts` to produce graph nodes/edges.

Mirror of police_report_templates.py pattern.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ── Section order ─────────────────────────────────────────────────────────

DEFAULT_SECTIONS: tuple[str, ...] = (
    "cover",
    "executive_summary",
    "use_case",
    "architecture",
    "data_residency",
    "warrant_gate",
    "human_review",
    "audit_retention",
    "international_scope",
    "phase_status",
    "operating_entity",
    "compliance_frameworks",
    "design_adrs",
    "next_steps",
    "faq",
    "appendix_references",
)

SECTION_TITLE_JP: Dict[str, str] = {
    "cover":               "表紙",
    "executive_summary":   "1. エグゼクティブサマリ",
    "use_case":            "2. 想定利用シーン",
    "architecture":        "3. アーキテクチャ (Edge-only / pod-only RW 分離)",
    "data_residency":      "4. データ国内拘束 (顔特徴量は murakumo on-prem)",
    "warrant_gate":        "5. 令状ゲート (queryPerson は warrant/enquiry 必須)",
    "human_review":        "6. 人間判断介在 (human_review_gate 必須)",
    "audit_retention":     "7. 監査ログ 7 年保管",
    "international_scope": "8. 国際 LEA スコープ (INTERPOL 196 加盟国対応)",
    "phase_status":        "9. Phase 状況 + マイルストーン",
    "operating_entity":    "10. 運営主体 (amanomibashira / 受託 Gftd Japan)",
    "compliance_frameworks": "11. 法令準拠 (個情法 / 警察法 / 警察庁通達 R6)",
    "design_adrs":         "12. 設計 ADR ダイジェスト",
    "next_steps":          "13. 次のステップ",
    "faq":                 "14. FAQ",
    "appendix_references": "付録: 参考文献",
}


# ── Renderers ─────────────────────────────────────────────────────────────


def render_cover(facts: Dict[str, Any], briefing_no: str) -> str:
    return (
        f"# {facts.get('title', '(no title)')}\n"
        f"## {briefing_no}\n\n"
        f"| 項目 | 値 |\n"
        f"|---|---|\n"
        f"| 運営主体 | {facts.get('operatingEntity', 'amanomibashira')} |\n"
        f"| 実装受託 | {facts.get('vendor', 'Gftd Japan株式会社')} |\n"
        f"| 対象機関 | {facts.get('targetAgencyName', facts.get('targetAgencyPath', '(unset)'))} |\n"
        f"| TLP | {facts.get('tlp', 'AMBER')} |\n"
        f"| 言語 | {facts.get('language', 'ja')} |\n"
        f"| 作成日 | {_now_iso()[:10]} |\n"
        f"| 版 | v{facts.get('version', 1)} |\n"
    )


def render_executive_summary(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["executive_summary"]
    summary = facts.get("executiveSummary", "")
    return (
        f"## {title}\n\n"
        f"{summary}\n\n"
        f"本ブリーフィングは malak.surveillance capability cluster の技術仕様 + 倫理ガード設計 + 法令遵守状況を、"
        f"{facts.get('targetAgencyName', '対象機関')} のご担当者様に向けて整理したものです。"
        f"運営主体は **{facts.get('operatingEntity', 'amanomibashira')}** で、技術実装は **{facts.get('vendor', 'Gftd Japan株式会社')}** が受託します。\n"
    )


def render_use_case(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["use_case"]
    pitch = facts.get("useCasePitch", "fraud")
    pitch_map = {
        "fraud":              "特殊詐欺受け子の同一性照合 (神奈川/大阪/福岡 等の被害多発府県を想定)",
        "missingPerson":      "行方不明者の早期発見支援 (家族同意 + 警察依頼に基づく)",
        "streetCrime":        "街頭犯罪のシーン記述検索 (色・服装・物体・行動)",
        "cyberOps":           "サイバー犯罪者 (ランサムウェアグループ等) の物理移動追跡",
        "interpolCooperation": "INTERPOL Red Notice 対象の国境横断追跡支援",
    }
    return (
        f"## {title}\n\n"
        f"主用途: **{pitch_map.get(pitch, pitch)}**\n\n"
        f"二次利用: シーン記述検索 (人物特定なし) は令状不要、街頭犯罪・事案発生時刻周辺の "
        f"クリップ抽出に使用可能。**人物再特定 (queryPerson) は別経路で令状ゲート付き**。\n"
    )


def render_architecture(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["architecture"]
    return (
        f"## {title}\n\n"
        f"ADR-2605111200 (CF Worker = Edge Layer / RW 接続は K8s pod のみ) に準拠した 2 系統推論経路:\n\n"
        f"```\n"
        f"[police LAN] ─mTLS─▶ [CF Worker malak.gftd.ai (edge)] ─XRPC─▶ [bpmn-dispatcher (k8s, JP)]\n"
        f"                                                                  │\n"
        f"                              ┌───────────────────────────────────┴─────┐\n"
        f"                              ▼                                         ▼\n"
        f"                      [LangGraph Server (Granian L3)]         [LangServer worker]\n"
        f"                              │                                         │\n"
        f"                              ▼ inference                                ▼ INSERT/SELECT\n"
        f"                      [murakumo on-prem (JP DC, NVIDIA)]       [RisingWave Vultr LAX]\n"
        f"```\n\n"
        f"- 顔特徴量・frame jpeg・OCR は murakumo on-prem (国内 GPU) のみで処理\n"
        f"- テキスト LLM (シーン記述パース / 営業 draft) は RunPod US-KS-2 (PII 非含有 text only)\n"
        f"- CF Worker は state を持たず、env.HYPERDRIVE もない (Edge-only, ADR-2605111200)\n"
    )


def render_data_residency(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["data_residency"]
    return (
        f"## {title}\n\n"
        f"{facts.get('dataResidency', '顔特徴量は murakumo on-prem (国内 GPU) で AES-256-GCM 暗号化保管。')}\n\n"
        f"| データ | 保管場所 | 暗号化 |\n"
        f"|---|---|---|\n"
        f"| Raw clip mp4 | R2 警察専用 bucket (90 日) | 転送 TLS のみ |\n"
        f"| 顔特徴量 (template) | murakumo on-prem (JP) | AES-256-GCM + wrapped key + kid |\n"
        f"| Scene CLIP embedding | murakumo on-prem (JP) | プレーン (個人識別性低) |\n"
        f"| Person ReID embedding | murakumo on-prem (JP) | プレーン (個人識別性低) |\n"
        f"| Audit log | RW + S3 archive | append-only 7 年 |\n\n"
        f"詳細: `_working/malak/surveillance/MURAKUMO-DOMESTIC-CONSTRAINT.md`\n"
    )


def render_warrant_gate(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["warrant_gate"]
    return (
        f"## {title}\n\n"
        f"`ai.gftd.apps.malak.queryPerson` (既知人物の再特定) は **edge layer + LangServer layer の二重ゲート**:\n\n"
        f"```\nrequest body MUST include legalBasis.warrantRef OR legalBasis.enquiryRef\n```\n\n"
        f"いずれも空の場合、Worker `src/app.ts` `preflightGate` が **403** を返し、"
        f"upstream (dispatcher) には forward されません。defense-in-depth で LangServer handler でも再 check。\n\n"
        f"対して `queryScene` (シーン記述検索) は人物特定情報を返さないため、令状不要 (任意捜査範囲)。\n"
    )


def render_human_review(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["human_review"]
    return (
        f"## {title}\n\n"
        f"top-1 自動採用は **設計上不可能**。LangGraph chain の `human_review_gate` ノードが "
        f"`reviewSurveillanceMatches` を待つ Conditional edge で、レビュー記録が無いと"
        f"`exportSurveillanceEvidence` に進めません。\n\n"
        f"投資判断・逮捕等の処分に繋がる判定には必ず investigator の人間判定を介在させます。\n"
    )


def render_audit_retention(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["audit_retention"]
    return (
        f"## {title}\n\n"
        f"各操作 (令状情報 / 操作者 DID / mTLS 指紋 / IP / latency) を append-only で記録。"
        f"保管期間は **7 年 (法定)**、`vertex_malak_surveillance_audit_event` で sha256 chain で改ざん検証可能。\n"
    )


def render_international_scope(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["international_scope"]
    return (
        f"## {title}\n\n"
        f"対象範囲: INTERPOL 196 加盟国の National Central Bureau (NCB) + 主要 LEA。"
        f"seed は `60-apps/ai-gftd-project-states/data/gov/{{cc}}/lea.ndjson` で管理:\n\n"
        f"- Tier 1 (52 entries): INTERPOL HQ (IPSG Lyon) + Europol + UNODC + FATF + G7 + Five Eyes\n"
        f"- Tier 2 (51 entries): G20 + 主要アジア (KOR/SGP/HKG/IND/BRA etc.)\n"
        f"- Tier 3 (169 entries): 残り加盟国 stub (Phase 1 中に enrichment)\n\n"
        f"**Cooperation status タグ付与**: CHN/RUS/IRN/SYR/BLR/MMR/LBY/YEM/AFG/SSD/SDN/IRQ は "
        f"`prohibited` / `restricted` で outreach 経路で hard-exclude。詳細: ADR-2605091400 §LEA scope.\n"
    )


def render_phase_status(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["phase_status"]
    phase_status = facts.get("phaseStatus", "Phase 0 (2026-05-13 開始, 法務クリア進行中)")
    return (
        f"## {title}\n\n"
        f"現状: **{phase_status}**\n\n"
        f"| Phase | Target | 状況 |\n"
        f"|---|---|---|\n"
        f"| Phase 0 法務・設計 | 2026-08-01 着手判断 | 進行中 (Kunal CLO triage 期限 06-01) |\n"
        f"| Phase 1 警察庁照会 + INTERPOL 接触 | 2026-08〜 | 待機 |\n"
        f"| Phase 2 パイロット県警 3 本部 | 2026-09〜 2027-03 | 待機 |\n"
        f"| Phase 3 JC3 共同調達 | 2027-Q1 | 待機 |\n"
        f"| Phase 4 47 本部 + 国際展開 | 2027-Q2〜 | 待機 |\n\n"
        f"詳細: `_working/malak/surveillance/PHASE-1-LAUNCH-READINESS.md`\n"
    )


def render_operating_entity(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["operating_entity"]
    return (
        f"## {title}\n\n"
        f"| Role | Entity |\n"
        f"|---|---|\n"
        f"| 運営主体 (operating entity) | **{facts.get('operatingEntity', 'amanomibashira')}** |\n"
        f"| 実装受託 (vendor) | **{facts.get('vendor', 'Gftd Japan株式会社')}** |\n"
        f"| 個情法上の取扱事業者 | amanomibashira |\n"
        f"| 顔特徴量管理責任者 | amanomibashira CLO |\n"
        f"| インシデント窓口 | privacy@gftd.ai (24h 受付) |\n"
        f"| 警察との契約当事者 | amanomibashira (Gftd Japan は再委託先として開示) |\n"
    )


def render_compliance_frameworks(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["compliance_frameworks"]
    frameworks: List[str] = facts.get("complianceFrameworks") or [
        "個人情報保護法 (R元/R3 改正)",
        "警察庁通達 R6 (公開草案準拠)",
        "通信の秘密 (電気通信事業法 §4) — 音声トラック ingest 時破棄",
        "刑事訴訟法 §321 (伝聞例外) — chain-of-custody",
        "特定電子メール法 §3 (営業 outreach 経路)",
        "公務員倫理規程 (招待・贈答ライン保護)",
        "個情委ガイドライン (生体識別子、要配慮個人情報相当)",
    ]
    body = "\n".join(f"- {f}" for f in frameworks)
    return (
        f"## {title}\n\n"
        f"設計は以下のフレームワークに準拠して構築されています:\n\n"
        f"{body}\n\n"
        f"確定通達公開時の 30 日以内 audit + 設計影響評価は Phase 1 中 monitoring (外部弁護士契約)。\n"
    )


def render_design_adrs(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["design_adrs"]
    adrs: List[str] = facts.get("designAdrs") or [
        "ADR-2605091400 — MCP as cell membrane (Lexicon/XRPC は内部 cytoplasmic wire)",
        "ADR-2605111200 — CF Worker = Edge-Only; RW 接続は K8s pod のみ",
        "ADR-2605010000 — RunPod 6000 Ada (LLM inference SSoT, text-only)",
        "ADR-0048 — RisingWave Vultr + B2 primary",
        "ADR-0036 — 3-Tier Write (Social / Domain / State)",
        "ADR-0095 — Simplified 3-layer identity + RW canonical columns",
        "ADR-2605080600 — LangGraph Server + Granian L3 Runtime",
    ]
    body = "\n".join(f"- {a}" for a in adrs)
    return (
        f"## {title}\n\n"
        f"本案件で参照される主要設計判断:\n\n"
        f"{body}\n"
    )


def render_next_steps(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["next_steps"]
    return (
        f"## {title}\n\n"
        f"1. ご関心がおありの場合、詳細技術説明会 (45 分 / オンライン or 対面) のお時間を頂戴できれば幸甚です。\n"
        f"2. 警察庁通達 R6 確定後の影響評価 brief (10 ページ補足) を準備中です。\n"
        f"3. パイロット採用先 (神奈川/大阪/福岡 県警) との合同実証案を Phase 2 で構成予定です。\n\n"
        f"連絡先: malak-surveillance@gftd.ai (amanomibashira 担当)\n"
    )


def render_faq(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["faq"]
    return (
        f"## {title}\n\n"
        f"### Q1. 顔特徴量はどこに保管されますか?\n"
        f"国内 GPU 拠点 (murakumo on-prem) のみ。AES-256-GCM 暗号化、master key は JP 国内拘束。"
        f"Cloudflare / 外部 LLM / 海外推論基盤への送信は protocol レベルで遮断。\n\n"
        f"### Q2. 令状なしで人物特定検索ができますか?\n"
        f"いいえ。`queryPerson` は **edge layer + LangServer layer 二重ゲート** で `legalBasis.warrantRef` "
        f"or `legalBasis.enquiryRef` の入力が必須。空の場合 403 を即返却し dispatcher にも forward されません。\n\n"
        f"### Q3. top-1 自動採用はできますか?\n"
        f"いいえ。LangGraph の `human_review_gate` Conditional edge により、"
        f"`reviewSurveillanceMatches` 記録なしには `exportSurveillanceEvidence` に進めません。\n\n"
        f"### Q4. 音声トラックは取得されますか?\n"
        f"いいえ。ffmpeg ingest 段階で音声ストリームを物理的に破棄します (通信の秘密配慮)。\n\n"
        f"### Q5. 47 都道府県警 + 国際刑事警察機関へ対応していますか?\n"
        f"はい。INTERPOL 196 加盟国 + 主要 LEA を seed として保管。"
        f"CHN/RUS/IRN/SYR/BLR/MMR/LBY/YEM/AFG/SSD/SDN/IRQ 等は `cooperation_status` で hard-exclude。\n\n"
        f"### Q6. 警察庁通達 R6 が確定したらどうなりますか?\n"
        f"Phase 1 中の外部弁護士 monthly retainer により、確定通達公開後 30 日以内に audit + "
        f"設計影響評価を実施します。抵触する場合は live deploy を停止し設計再着手。\n\n"
        f"### Q7. amanomibashira と Gftd Japan の関係は?\n"
        f"運営主体 = amanomibashira (一般財団法人格、operating entity)。"
        f"Gftd Japan株式会社 = 技術実装の vendor (再委託先として警察に開示)。"
        f"警察との契約当事者は常に amanomibashira。\n\n"
        f"### Q8. データ保管期間は?\n"
        f"Raw clip = 案件確定後 90 日 / 顔特徴量 ciphertext = 案件解決 1 年後 hard delete (soft delete 禁止) / "
        f"監査ログ = 7 年 (法定)。詳細は §7 (本ブリーフィング)。\n"
    )


def render_appendix_references(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_JP["appendix_references"]
    return (
        f"## {title}\n\n"
        f"- `_working/malak/surveillance/DESIGN.md` — 全体設計\n"
        f"- `_working/malak/surveillance/COMPLIANCE-MEMO.md` — 法令ガード + Kunal triage\n"
        f"- `_working/malak/surveillance/MURAKUMO-DOMESTIC-CONSTRAINT.md` — 国内拘束構成\n"
        f"- `_working/malak/surveillance/LEAD-PIPELINE-SEED.md` — 紹介ルート計画\n"
        f"- `_working/malak/surveillance/PHASE-1-LAUNCH-READINESS.md` — Phase 1 着手チェックリスト\n"
        f"- `30-graph/graph-schema/migrations/20260513140000_vertex_malak_surveillance_lea_org.ts` — RW schema\n"
        f"- `30-graph/graph-schema/migrations/20260513150000_vertex_malak_briefing.ts` — briefing graph schema\n"
        f"- `60-apps/ai-gftd-project-malak/CLAUDE.md` — Capability Clusters\n"
    )


DOC_RENDERERS = {
    "cover":               render_cover,
    "executive_summary":   render_executive_summary,
    "use_case":            render_use_case,
    "architecture":        render_architecture,
    "data_residency":      render_data_residency,
    "warrant_gate":        render_warrant_gate,
    "human_review":        render_human_review,
    "audit_retention":     render_audit_retention,
    "international_scope": render_international_scope,
    "phase_status":        render_phase_status,
    "operating_entity":    render_operating_entity,
    "compliance_frameworks": render_compliance_frameworks,
    "design_adrs":         render_design_adrs,
    "next_steps":          render_next_steps,
    "faq":                 render_faq,
    "appendix_references": render_appendix_references,
}
