"""report_gen.py — 助 (tasuke) document generation: ready-to-use, member-authored filings.

Generates the documents a cybercrime victim brings to the police / their bank / a platform — so
complete that an officer or a bank desk can work straight from them. The LOAD-BEARING invariant
(G3): every generated document is authored BY THE MEMBER (本人作成の申告書類), addressed TO the
authority — never authored AS the police. `_doc(...)` hard-wires `:doc/authored-by :member`,
`:doc/needs-member-signature true`, `:doc/support-cost-jpy 0`, `:doc/published false`. There is no
parameter that lets a caller mint a police-authored 公文書 (公文書偽造 is unrepresentable), submit
on the member's behalf (G2 — 本人提出), or charge for it (G1).

Generators (all free, all member-authored, all draft-only at R0):
  damage_report          被害届 (下書き)
  incident_statement     被害状況報告書 (時系列)
  evidence_index_doc     証拠目録
  damage_calculation     被害額算定書
  bank_freeze_request    銀行 不正送金 組戻し・口座凍結依頼 (振り込め詐欺救済法)
  platform_request       プラットフォーム凍結/復旧/開示依頼
  recovery_plan          アカウント復旧手順書

Stdlib only. The body text is deterministic Japanese boilerplate at R0; a Murakumo-only LLM
polishes wording at R1 (G8) but can never change the author, the signature requirement, or the cost.
"""

from __future__ import annotations

from typing import Any

from evidence import index as evidence_index
from triage import classify

POLICE_DOC_KINDS = ("damage-report", "incident-statement", "evidence-index", "damage-calculation")
REQUEST_DOC_KINDS = ("platform-request", "bank-freeze-request")


def _doc(case: str, kind: str, body: str, addressed_to: str, **extra) -> dict:
    """Build a document record with the G1/G2/G3/G7/G9 invariants baked in. Not overridable."""
    d = {
        ":doc/id": extra.pop("doc_id", f"{case}:{kind}"),
        ":doc/case": case,
        ":doc/kind": ":" + kind,
        ":doc/authored-by": ":member",          # G3 — never :police / :official / :server
        ":doc/addressed-to": addressed_to,
        ":doc/body": body,
        ":doc/needs-member-signature": True,     # G2/G7 — member reviews + signs before use
        ":doc/support-cost-jpy": 0,              # G1 — free
        ":doc/published": False,                 # G9 — draft-only at R0
    }
    d.update(extra)
    return d


def _hdr(case: dict, title: str) -> str:
    subj = case.get(":case/subject", "（被害者氏名）")
    return f"{title}\n\n申告者: {subj}（本人作成・要署名）\n作成日: （提出日を記入）\n"


def damage_report(case: dict, station: str = "（管轄）警察署長 殿") -> dict:
    """被害届(下書き). 本人が署名・提出する申告書類。警察官作成の公文書ではない(G3)。"""
    kind = classify(case)
    loss = int(case.get(":case/loss-jpy", 0) or 0)
    body = (
        _hdr(case, "被 害 届（下書き）")
        + f"\n宛先: {station}\n\n"
        "下記のとおり被害を受けましたので届け出ます。\n\n"
        f"1. 被害の種類: サイバー犯罪（{_ja_kind(kind)}）\n"
        f"2. 被害日時: {case.get(':case/occurred-at-text', '（年月日時を記入）')}\n"
        f"3. 被害の概要:\n   {case.get(':case/narrative', '（事実を時系列で記入。別紙「被害状況報告書」参照）')}\n"
        f"4. 被害額: 金 {loss:,} 円\n"
        "5. 証拠資料: 別紙「証拠目録」のとおり\n"
        "6. 相手方に関する情報: （判明している口座番号・URL・連絡先等を記入。別紙参照）\n\n"
        "上記に相違ありません。\n\n"
        "                          申告者署名 ____________________ 印\n\n"
        "※ これは被害者本人が提出するための下書きです。警察での受理・聴取の際に内容を確認・補正してください。"
    )
    return _doc(case.get(":case/id", "?"), "damage-report", body, station)


def incident_statement(case: dict) -> dict:
    """被害状況報告書(時系列). 供述の整理 — 本人作成、聴取の参考資料。"""
    timeline = case.get(":case/timeline") or ["（出来事を起きた順に記入）"]
    lines = "\n".join(f"  {i + 1}. {t}" for i, t in enumerate(timeline))
    body = (
        _hdr(case, "被害状況報告書")
        + "\n■ 経緯（時系列）\n" + lines
        + "\n\n■ 気づいた契機\n  " + str(case.get(":case/discovery", "（どのように被害に気づいたか）"))
        + "\n\n■ 現在の状況\n  " + str(case.get(":case/current", "（口座凍結依頼済/パスワード変更済 等）"))
        + "\n\n※ 本書面は被害者本人が事実を整理したものです。"
    )
    return _doc(case.get(":case/id", "?"), "incident-statement", body, "（警察・金融機関 提出用）")


def evidence_index_doc(case: dict, items: list[dict]) -> dict:
    """証拠目録. evidence.py の chain-of-custody hash を一覧化。"""
    rows = evidence_index(items)
    lines = "\n".join(
        f"  {i + 1}. [{r[':evidence/kind'].lstrip(':')}] "
        f"sha256={r[':evidence/sha256'][:16]}… ref={r[':evidence/envelope-ref']}"
        for i, r in enumerate(rows)
    ) or "  （証拠なし）"
    body = (
        _hdr(case, "証 拠 目 録")
        + "\n各証拠は暗号化保管され、下記 sha256 により改変のないことを確認できます。\n\n"
        + lines
        + "\n\n※ 原本（暗号化）は被害者本人が保持します。"
    )
    return _doc(case.get(":case/id", "?"), "evidence-index", body, "（届出添付用）", evidence_count=len(rows))


def damage_calculation(case: dict) -> dict:
    """被害額算定書. 内訳を明細化。"""
    items = case.get(":case/loss-breakdown") or [{":label": "被害額", ":jpy": case.get(":case/loss-jpy", 0)}]
    total = 0
    lines = []
    for it in items:
        jpy = int(it.get(":jpy", 0) or 0)
        total += jpy
        lines.append(f"  ・{it.get(':label', '項目')}: 金 {jpy:,} 円")
    body = (
        _hdr(case, "被害額算定書")
        + "\n■ 内訳\n" + "\n".join(lines)
        + f"\n\n■ 合計: 金 {total:,} 円\n\n※ 領収書・取引明細は証拠目録に対応します。"
    )
    return _doc(case.get(":case/id", "?"), "damage-calculation", body, "（届出添付用）", total_jpy=total)


def bank_freeze_request(case: dict, bank: str = "（金融機関名）御中") -> dict:
    """銀行 不正送金 組戻し・口座凍結依頼 (振り込め詐欺救済法). 本人が送付する依頼書(G2)。"""
    body = (
        _hdr(case, "不正送金に関する組戻し・口座凍結のご依頼")
        + f"\n宛先: {bank}\n\n"
        "私の口座から、身に覚えのない送金（不正送金）が行われました。つきましては、\n"
        "振り込め詐欺救済法に基づき、振込先口座の凍結および組戻し手続きをお願いいたします。\n\n"
        f"・被害日時: {case.get(':case/occurred-at-text', '（記入）')}\n"
        f"・送金額: 金 {int(case.get(':case/loss-jpy', 0) or 0):,} 円\n"
        f"・振込先（判明分）: {case.get(':case/counterparty', '（口座番号・名義）')}\n"
        "・警察への被害届: （提出予定/受理番号を記入）\n\n"
        "                          依頼人署名 ____________________ 印\n\n"
        "※ 本依頼書は被害者本人が金融機関へ提出するものです。"
    )
    return _doc(case.get(":case/id", "?"), "bank-freeze-request", body, bank,
                legal_basis="振り込め詐欺救済法（:representative）")


def platform_request(case: dict, platform: str = "（プラットフォーム）abuse 窓口", purpose: str = "凍結・復旧") -> dict:
    """プラットフォーム凍結/復旧/開示依頼. 本人が送付(G2)。"""
    body = (
        _hdr(case, f"アカウントに関する{purpose}のご依頼")
        + f"\n宛先: {platform}\n\n"
        f"私の利用するアカウントが {_ja_kind(classify(case))} の被害に遭いました。\n"
        f"利用規約の不正利用条項に基づき、{purpose} の対応をお願いいたします。\n\n"
        f"・対象アカウント: {case.get(':case/account-id', '（ID/URL を記入）')}\n"
        f"・被害日時: {case.get(':case/occurred-at-text', '（記入）')}\n"
        "・添付: 被害状況報告書・証拠目録\n\n"
        "                          利用者署名 ____________________\n\n"
        "※ 本依頼書は利用者本人が送付するものです。"
    )
    return _doc(case.get(":case/id", "?"), "platform-request", body, platform,
                legal_basis="各社利用規約 abuse 条項（:representative）")


def recovery_plan(case: dict, service: str = "（サービス名）") -> dict:
    """アカウント復旧手順書. 本人が実行する self-help 手順(G2 :self-submit)。"""
    steps = [
        "別の安全な端末・ネットワークから対象サービスのパスワードをリセットする",
        "ログイン中の全セッションを失効（「すべてのデバイスからログアウト」）させる",
        "二段階認証を再設定し、認証アプリ/バックアップコードを更新する",
        "登録メールアドレス・電話番号・復旧用情報が改ざんされていないか確認し戻す",
        "連携アプリ・API トークンを見直し、見覚えのない連携を解除する",
        "同じパスワードを使い回した他サービスもすべて変更する",
        "復旧後、プラットフォーム abuse 窓口へ被害を報告し、再発防止設定を有効化する",
    ]
    body = (
        _hdr(case, f"アカウント復旧手順書（{service}）")
        + "\n■ 手順（上から順に本人が実行）\n"
        + "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(steps))
        + "\n\n※ 復旧操作は本人が行ってください（助 は手順を提供するのみ、代理ログインはしません）。"
    )
    return _doc(case.get(":case/id", "?"), "recovery-plan", body, "（本人実行）",
                service=service, steps=steps, support_role=":self-submit")


# ── helpers ─────────────────────────────────────────────────────────────────────
_JA = {
    "phishing": "フィッシング", "unauthorized-transfer": "不正送金",
    "account-takeover": "アカウント乗っ取り", "support-scam": "サポート詐欺",
    "romance-scam": "ロマンス詐欺", "investment-scam": "投資詐欺", "ransomware": "ランサムウェア",
    "impersonation": "なりすまし", "fake-billing": "架空請求", "sns-fraud": "SNS型詐欺",
    "leak-extortion": "情報流出・脅迫",
}


def _ja_kind(kind: str) -> str:
    return _JA.get(kind, kind)


def assert_member_authored(doc: dict) -> None:
    """G3 guard usable by callers/tests: a generated doc MUST be member-authored, signed, free, unpublished."""
    if doc.get(":doc/authored-by") != ":member":
        raise ValueError("G3: a generated document must be authored by :member (公文書偽造を排除)")
    if doc.get(":doc/needs-member-signature") is not True:
        raise ValueError("G2/G7: a generated document must require the member's signature")
    if doc.get(":doc/support-cost-jpy", 0) != 0:
        raise ValueError("G1: a generated document is free (cost 0)")
    if doc.get(":doc/published") is not False:
        raise ValueError("G9: a generated document is draft-only at R0 (published false)")
