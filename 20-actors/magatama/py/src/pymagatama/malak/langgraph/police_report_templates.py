"""police_report_templates — Japanese police internal-document markdown templates.

Source-of-truth doc set follows what 神奈川県警察 知能犯係 actually
produces / processes for SNS 投資詐欺 cases:

    - 被害届 (higai_todoke)              — citizen-submitted damage report
    - 告訴状 (kokuso_jo)                  — formal accusation (Art.230-1 CCP)
    - 捜査報告書 (sousa_houkokusho)        — police-internal investigation report
    - 捜査関係事項照会書 (shoukai_sho)     — CPL §197(2) bank / telecom inquiry
    - 証拠資料目録 (shouko_mokuroku)       — evidence inventory
    - 送致書 (souchi_sho)                  — case file referral (送検) to 検察庁

Each rendered document carries the **reporting line block** at the top so
that when a citizen-prepared draft is handed to 松村刑事 (起案), the chain
of stamps (係長 → 課長 → 副署長 → 署長 → 県警本部捜二 → 警察庁) can flow
without reformatting.

The output is intentionally markdown — easy to render to DOCX/PDF via
`pandoc`, easy to diff in git, easy for the LangGraph chain to pipe.
The header says "市民提供 — 警察様式準拠" so it is clear this is a
**citizen submission** matching police format, NOT a police-issued doc.
"""

from __future__ import annotations

import datetime
from typing import Any


# ── Reporting line SSoT ────────────────────────────────────────────────
JP_POLICE_REPORTING_LINE: list[dict[str, str]] = [
    {"step": "起案",     "rank": "警部補",   "post": "知能犯係",                      "name": "松村", "agency": "神奈川県警察 磯子警察署 刑事課"},
    {"step": "確認",     "rank": "警部補",   "post": "知能犯係長",                    "name": "",     "agency": "神奈川県警察 磯子警察署 刑事課"},
    {"step": "決裁",     "rank": "警部",     "post": "刑事課長",                      "name": "",     "agency": "神奈川県警察 磯子警察署"},
    {"step": "副署長決裁","rank": "警視",     "post": "副署長",                        "name": "",     "agency": "神奈川県警察 磯子警察署"},
    {"step": "署長決裁", "rank": "警視正",   "post": "署長",                          "name": "",     "agency": "神奈川県警察 磯子警察署"},
    {"step": "本部報告", "rank": "警視",     "post": "捜査第二課 (知能犯) 課長",      "name": "",     "agency": "神奈川県警察本部 刑事部"},
    {"step": "庁報告",   "rank": "警視正",   "post": "組織犯罪対策第二課 (特殊詐欺)", "name": "",     "agency": "警察庁 刑事局"},
    {"step": "連携",     "rank": "—",        "post": "JC3 連携窓口",                  "name": "",     "agency": "Japan Cybercrime Control Center"},
    {"step": "国際",     "rank": "警視正",   "post": "国際協力推進室 (ICPO 経由)",    "name": "",     "agency": "警察庁 長官官房"},
]


# ── Helpers ────────────────────────────────────────────────────────────
def _today_jp() -> str:
    d = datetime.date.today()
    return f"令和{d.year - 2018}年{d.month}月{d.day}日"


def _yen(n: int | float) -> str:
    return f"金 {int(n):,} 円"


def _line_block(doc_no: str, doc_type_jp: str) -> str:
    rows = ["| 段階 | 階級 | 役職 | 氏名 | 機関 | 印 |", "|---|---|---|---|---|---|"]
    for s in JP_POLICE_REPORTING_LINE:
        rows.append(f"| {s['step']} | {s['rank']} | {s['post']} | {s['name']} | {s['agency']} | ㊞ |")
    return (
        f"**文書番号**: {doc_no}\n"
        f"**文書種別**: {doc_type_jp}\n"
        f"**起案日**: {_today_jp()}\n"
        f"**取扱区分**: 取扱注意 (捜査資料)\n\n"
        f"### 報告ライン (起案→決裁→報告)\n\n"
        + "\n".join(rows)
        + "\n\n---\n\n"
    )


# ── Document renderers ─────────────────────────────────────────────────
def render_higai_todoke(facts: dict[str, Any], doc_no: str) -> str:
    v = facts.get("victim", {})
    incident = facts.get("incident", {})
    body = [
        _line_block(doc_no, "被害届"),
        "# 被害届\n",
        f"{facts.get('addressee', '神奈川県警察 磯子警察署長 殿')}\n",
        f"\n{_today_jp()}\n",
        "\n## 届出人\n",
        f"- 氏名: {v.get('name', '')}",
        f"- 住所: {v.get('address', '')}",
        f"- 電話: {v.get('phone', '')}",
        f"- 生年月日: {v.get('dob', '')}",
        f"- 職業: {v.get('occupation', '')}",
        "\n## 被害事実の要旨\n",
        incident.get("summary", "") or "(別紙のとおり)",
        "\n## 罪名 (該当条文)\n",
        "- 刑法第246条 (詐欺)",
        "- 組織的犯罪処罰法第3条1項13号 (組織的詐欺)",
        "- 組織的犯罪処罰法第10条 (犯罪収益等隠匿)",
        "- 組織的犯罪処罰法第11条 (犯罪収益等収受)",
        "\n## 被害金額\n",
        _yen(incident.get("loss_jpy", 0)),
        f" (被害期間: {incident.get('period', '')})",
        "\n## 被害発生の場所\n",
        incident.get("place", ""),
        "\n## 加害者の特定状況\n",
        facts.get("perpetrator_summary", "") or "(別紙 捜査報告書のとおり)",
        "\n## 処罰希望の有無\n",
        "**処罰を希望する。** (告訴の意思あり、別途告訴状提出)",
        "\n## 添付資料\n",
        "別紙「証拠資料目録」のとおり。",
        "\n---\n",
        f"届出人 署名: ____________________  ㊞  ({v.get('name', '')})",
    ]
    return "\n".join(body)


def render_kokuso_jo(facts: dict[str, Any], doc_no: str) -> str:
    v = facts.get("victim", {})
    actors = facts.get("actors", [])
    body = [
        _line_block(doc_no, "告訴状 (刑事訴訟法第230条)"),
        "# 告 訴 状\n",
        f"{facts.get('addressee', '神奈川県警察 磯子警察署長 殿')}\n",
        f"(横浜地方検察庁 検察官 経由)\n",
        f"\n{_today_jp()}\n",
        "\n## 告訴人\n",
        f"- 氏名: {v.get('name', '')}  ㊞",
        f"- 住所: {v.get('address', '')}",
        f"- 電話: {v.get('phone', '')}",
        "\n## 被告訴人\n",
    ]
    for a in actors or [{"role": "主犯", "name": "氏名不詳 (村上世彰を自称)"}]:
        body.append(f"- **{a.get('role', '不詳')}**: {a.get('name', '氏名不詳')}  {a.get('note', '')}")
    body += [
        "\n## 告訴の趣旨\n",
        "被告訴人らの後記所為は、刑法第246条 (詐欺)、組織的犯罪処罰法第3条1項13号 (組織的詐欺)、",
        "同法第10条 (犯罪収益等隠匿)、同法第11条 (犯罪収益等収受) に該当するので、被告訴人らを",
        "**厳重に処罰されたく告訴する**。",
        "\n## 告訴の事実\n",
        facts.get("incident", {}).get("narrative", "") or facts.get("incident", {}).get("summary", ""),
        "\n## 証拠資料\n",
        "別紙「証拠資料目録」記載のとおり。",
        "\n## 罰条\n",
        "- 刑法第246条第1項 (詐欺罪)",
        "- 組織的犯罪処罰法第3条1項13号 (組織的詐欺罪)",
        "- 組織的犯罪処罰法第10条 (犯罪収益等隠匿罪)",
        "- 組織的犯罪処罰法第11条 (犯罪収益等収受罪)",
        "\n---\n",
        f"告訴人 署名: ____________________  ㊞  ({v.get('name', '')})",
    ]
    return "\n".join(body)


def render_sousa_houkokusho(facts: dict[str, Any], doc_no: str) -> str:
    v = facts.get("victim", {})
    incident = facts.get("incident", {})
    mules = facts.get("mule_accounts", [])
    infra = facts.get("infrastructure", {})
    osint = facts.get("osint_findings", [])
    body = [
        _line_block(doc_no, "捜査報告書"),
        "# 捜査報告書\n",
        f"{facts.get('addressee', '神奈川県警察 磯子警察署長 殿')}\n",
        f"\n{_today_jp()}\n",
        f"\n刑事課 知能犯係 警部補 松村\n",
        "\n下記のとおり、捜査結果を報告する。\n",
        "\n## 記\n",
        "\n### 1 件名\n",
        f"{v.get('name', '')} に対する組織的詐欺被疑事件",
        "\n### 2 被疑者\n",
    ]
    for a in facts.get("actors", []):
        body.append(f"- **{a.get('role', '不詳')}**: {a.get('name', '氏名不詳')}  {a.get('note', '')}")
    body += [
        "\n### 3 被害者\n",
        f"- 氏名: {v.get('name', '')}",
        f"- 住所: {v.get('address', '')}",
        f"- 連絡先: {v.get('phone', '')} / {v.get('email', '')}",
        "\n### 4 認定事実\n",
        incident.get("narrative", "") or incident.get("summary", ""),
        "\n### 5 被害金額\n",
        f"**{_yen(incident.get('loss_jpy', 0))}**  (期間: {incident.get('period', '')})",
        "\n### 6 振込先口座 (受取側 mule accounts)\n",
        "| # | 日時 | 銀行 | 支店 | 種別 | 口座番号 | 名義 | 金額 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, m in enumerate(mules, 1):
        body.append(
            f"| {i} | {m.get('datetime', '')} | {m.get('bank', '')} | {m.get('branch', '')} | "
            f"{m.get('account_type', '普')} | {m.get('account_number', '')} | "
            f"{m.get('holder', '')} | {_yen(m.get('amount', 0))} |"
        )
    body += [
        "\n### 7 被疑インフラ\n",
        f"- 偽証券会社: {infra.get('fake_brokerage', '')}",
        f"- 偽サイト: {', '.join(infra.get('fake_sites', []))}",
        f"- LINE 連絡先: {', '.join(infra.get('line_handles', []))}",
        f"- 詐欺アプリ: {', '.join(infra.get('phishing_apps', []))}",
        "\n### 8 OSINT 分析結果\n",
    ]
    for o in osint or [{"finding": "(別紙 OSINT 結果参照)"}]:
        body.append(f"- {o.get('finding', '')}")
    body += [
        "\n### 9 適用法条\n",
        "- 刑法第246条 (詐欺)",
        "- 組織的犯罪処罰法第3条1項13号 (組織的詐欺)",
        "- 組織的犯罪処罰法第10条 (犯罪収益等隠匿)",
        "- 組織的犯罪処罰法第11条 (犯罪収益等収受)",
        "\n### 10 今後の捜査方針\n",
        "1. 振込先全口座への捜査関係事項照会書 (CPL §197(2)) 送付、口座凍結状況確認",
        "2. 偽サイト・詐欺アプリ運営者特定のための whois / cert.sh / 通信事業者照会",
        "3. JC3 (Japan Cybercrime Control Center) との連携、海外 LE への ICPO 経由共助要請",
        "4. 同種余罪 (テスタ事案、加藤恭兵事案、村上財団全被害者) との合一捜査",
        "5. 検察官送致時期の調整 (証拠固め完了後)",
        "\n以上",
    ]
    return "\n".join(body)


def render_shoukai_sho(facts: dict[str, Any], doc_no: str, target: dict[str, Any]) -> str:
    body = [
        _line_block(doc_no, "捜査関係事項照会書 (刑事訴訟法第197条第2項)"),
        "# 捜査関係事項照会書\n",
        f"\n{target.get('addressee', '')} 御中\n",
        f"\n{_today_jp()}\n",
        f"\n神奈川県警察 磯子警察署長  ㊞\n",
        "\n刑事訴訟法第197条第2項の規定により、下記事項について照会する。",
        "回答書を**令和__年__月__日まで**に当署刑事課 知能犯係 警部補 松村 宛て送付されたい。\n",
        "\n## 記\n",
        "\n### 1 照会対象\n",
        f"- 口座/契約: {target.get('account_or_contract', '')}",
        f"- 名義人/契約者: {target.get('holder', '')}",
        f"- 期間: {target.get('period', '')}",
        "\n### 2 照会事項\n",
    ]
    for q in target.get("queries", [
        "(1) 口座開設時の本人確認資料 (運転免許証等の写し)",
        "(2) 入出金履歴 (取引明細) 全件",
        "(3) 開設時及び現在の届出住所・電話番号",
        "(4) 関連口座 (同一名義人・同一連絡先) の有無",
        "(5) 既受理被害届との重複の有無",
        "(6) 現在の口座凍結状況",
    ]):
        body.append(f"- {q}")
    body += [
        "\n### 3 関連事件\n",
        f"- 事件番号: {facts.get('case_no', '')}",
        f"- 罪名: 組織的詐欺 (刑法246条, 組犯法3条1項13号)",
        "\n### 4 回答先\n",
        "- 神奈川県警察 磯子警察署 刑事課 知能犯係 警部補 松村",
        "- 住所: 〒235-0036 神奈川県横浜市磯子区中原1丁目1番5号",
        "- 電話: 045-(磯子署代表)",
        "\n以上",
    ]
    return "\n".join(body)


def render_shouko_mokuroku(facts: dict[str, Any], doc_no: str) -> str:
    evidence = facts.get("evidence", [])
    body = [
        _line_block(doc_no, "証拠資料目録"),
        "# 証拠資料目録\n",
        f"\n事件番号: {facts.get('case_no', '')}",
        f"\n被害者: {facts.get('victim', {}).get('name', '')}",
        f"\n作成日: {_today_jp()}",
        "\n## 物的証拠\n",
        "| 符号 | 種別 | 標題 | 出所 | 入手日 | TLP | hash (sha256) |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(evidence, 1):
        body.append(
            f"| 甲{i} | {e.get('kind', '')} | {e.get('title', '')} | "
            f"{e.get('source', '')} | {e.get('acquired_on', '')} | "
            f"{e.get('tlp', 'RED')} | {e.get('sha256', '')[:16]}... |"
        )
    body += [
        "\n## デジタル証跡 (chain-of-custody)\n",
        "- Android device からの取得: adb pull / NotificationListenerService (本人同意あり)",
        "- LINE official export 経由のテキスト履歴",
        "- PEGEL graph (vertex_malak_investigation_tick) 永続化 hash 付き",
        "\n## 注記\n",
        "全データは RisingWave (gftd graph) に append-only で保全。改竄不可。",
    ]
    return "\n".join(body)


def render_soufu_sho(facts: dict[str, Any], doc_no: str, doc_index: list[dict[str, str]]) -> str:
    """補充資料送付書 — citizen-side cover letter for supplementary evidence packet."""
    v = facts.get("victim", {})
    body = [
        _line_block(doc_no, "補充資料送付書 (届出人提出)"),
        "# 補充資料送付書\n",
        f"{facts.get('addressee', '神奈川県警察 磯子警察署長 殿')}\n",
        f"(担当: 刑事課 知能犯係 警部補 松村 刑事)\n",
        f"\n{_today_jp()}\n",
        "\n## 届出人 (本件被害者)\n",
        f"- 氏名: {v.get('name', '')}",
        f"- 住所: {v.get('address', '')}",
        f"- 電話: {v.get('phone', '')}",
        f"- 事件番号: {facts.get('case_no', '')}",
        "\n## 提出趣旨\n",
        "令和5年11月27日に貴署刑事課 知能犯係 警部補 松村 刑事へ被害相談いたしました組織的詐欺被害事件",
        "に関し、その後の追加調査 (令和8年5月12日〜13日) で得た証跡 (Android 端末の電子的証拠、",
        "OCR 抽出資料、OSINT 結果、関係法人実在性確認、ヒアリング記録) を、警察様式に準拠した形で",
        "整理いたしましたので、本職追跡担当 (gftd Japan株式会社 代表取締役 河崎純真) より提出いたします。",
        "貴職での捜査資料への組み込み、関係先 (横浜地方検察庁、神奈川県警察本部 刑事部 捜査第二課、",
        "警察庁 刑事局 組織犯罪対策第二課、JC3、ICPO) への報告にお役立てください。",
        "\n## 同封資料目録\n",
        "| 通番 | 文書種別 | 文書番号 | ファイル | sha256 (先頭16文字) |",
        "|---|---|---|---|---|",
    ]
    for i, d in enumerate(doc_index, 1):
        body.append(
            f"| {i} | {d.get('jp', '')} | {d.get('doc_no', '')} | {d.get('file', '')} | {d.get('sha256', '')[:16]}... |"
        )
    body += [
        "\n## 取扱注意\n",
        "本資料一式は被害者 PII を含む捜査資料です。**取扱注意 (RED / 第三者開示禁止)**。",
        "PEGEL audit trail (RW vertex_malak_investigation_tick) によりすべての作成・配布履歴は",
        "改竄不可能な形で保全されており、求めに応じ照合可能です。",
        "\n## 連絡先 (本職追跡担当)\n",
        "- 氏名: 河崎 純真 (gftd Japan株式会社 代表取締役 CEO)",
        "- E-mail: j.kawasaki@gftd.co.jp",
        "- 電話: (gftd Japan 代表 経由)",
        "\n---\n",
        f"届出人 署名: ____________________  ㊞  ({v.get('name', '')})",
        "本職追跡担当 署名: ____________________  ㊞  (河崎 純真)",
    ]
    return "\n".join(body)


def render_souchi_sho(facts: dict[str, Any], doc_no: str) -> str:
    v = facts.get("victim", {})
    body = [
        _line_block(doc_no, "送致書 (検察官送致一件記録 表紙)"),
        "# 送致書\n",
        "\n横浜地方検察庁 検察官 殿\n",
        f"\n{_today_jp()}\n",
        f"\n神奈川県警察 磯子警察署長  ㊞\n",
        "\n下記事件を送致する。\n",
        "\n## 記\n",
        f"\n- **事件番号**: {facts.get('case_no', '')}",
        f"- **罪名**: 組織的詐欺 (刑法246条, 組犯法3条1項13号, 同10条, 同11条)",
        f"- **被疑者**: {', '.join(a.get('name', '氏名不詳') for a in facts.get('actors', []))}",
        f"- **被害者**: {v.get('name', '')}",
        f"- **被害金額**: {_yen(facts.get('incident', {}).get('loss_jpy', 0))}",
        f"- **送致区分**: 通常送致 (被疑者氏名不詳のまま含む — 引き続き氏名特定捜査)",
        "\n## 添付書類\n",
        "1. 被害届 (告訴状を含む)",
        "2. 捜査報告書",
        "3. 振込明細写し 12 葉",
        "4. LINE 履歴写し 一式 (PDF 9 通 / DOCX 4 通)",
        "5. APK forensics 報告 (leedsil / bitnest)",
        "6. 捜査関係事項照会書 (12 件) 及び回答書",
        "7. 証拠資料目録",
        "8. PEGEL audit trail 出力 (RW graph snapshot, sha256 付き)",
        "\n## 意見\n",
        "本件は中国系犯罪組織による組織的 SNS 投資詐欺被害であり、共謀の上、被害者を欺罔して",
        "現金を交付させた組織的詐欺罪 (組犯法3条1項13号) が成立する。",
        "余罪多数の蓋然性が高いため、合一捜査の上、起訴を求める。",
        "\n以上",
    ]
    return "\n".join(body)


# ── Doc-type registry (used by LangGraph) ──────────────────────────────
DOC_RENDERERS = {
    "soufu_sho":         render_soufu_sho,
    "higai_todoke":      render_higai_todoke,
    "kokuso_jo":         render_kokuso_jo,
    "sousa_houkokusho":  render_sousa_houkokusho,
    "shoukai_sho":       render_shoukai_sho,
    "shouko_mokuroku":   render_shouko_mokuroku,
    "souchi_sho":        render_souchi_sho,
}

DOC_TYPE_JP = {
    "soufu_sho":         "補充資料送付書",
    "higai_todoke":      "被害届",
    "kokuso_jo":         "告訴状",
    "sousa_houkokusho":  "捜査報告書",
    "shoukai_sho":       "捜査関係事項照会書",
    "shouko_mokuroku":   "証拠資料目録",
    "souchi_sho":        "送致書",
}
