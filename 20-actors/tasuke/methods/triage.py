"""triage.py — 助 (tasuke) intake triage: scam-kind classification, severity, initial actions.

THE HEART of the membrane. Given a consenting victim's intake it produces:

  - scam-kind ∈ ontology :scam-kinds       — a KIND for routing, NEVER a legal verdict (G4, 非裁定)
  - severity  ∈ {info, elevated, urgent, critical}
  - actions   — the time-ordered initial-action checklist (証拠保全 → 凍結/組戻し → 届出 → 復旧)
  - windows   — the FREE public windows to point the victim to (G5; never a paid counsel)
  - deadlines — statutory/practical clocks the victim must not miss (cooling-off, クレカ不正利用申告 等)

Two charter invariants are enforced here (mirrors of the schema :db/allowed + lexicon :const):
  G1 — 助's support is FREE; `support_cost_jpy(...)` is hard-wired to 0. A non-zero cost raises.
  G7 — a case needs explicit consent; an intake without it raises.

This is NOT adjudication: classifying a report as `:investment-scam` says "route it like an
investment-scam victim", it does NOT find that fraud legally occurred (that is danjo/chigiri +
the police + the courts — G4). Stdlib only, deterministic at R0 (a Murakumo LLM refines the
KEYWORD match at R1, G8; it never changes the cost, the consent gate, or invents a verdict).
"""

from __future__ import annotations

from typing import Any

# ── closed vocab (mirror of the ontology :db/allowed) ───────────────────────────
SCAM_KINDS = (
    "phishing", "unauthorized-transfer", "account-takeover", "support-scam", "romance-scam",
    "investment-scam", "ransomware", "impersonation", "fake-billing", "sns-fraud", "leak-extortion",
)
SEVERITIES = ("info", "elevated", "urgent", "critical")
SUPPORT_ROLES = ("guide", "draft-assist", "self-submit")

# G1 INVARIANT — 助 is free. This is the only cost the actor can express.
SUPPORT_COST_JPY = 0

# keyword → scam-kind (deterministic R0 classifier; the Murakumo LLM refines at R1, never replaces).
_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("unauthorized-transfer", ("不正送金", "勝手に振込", "残高が減", "身に覚えのない出金", "atm", "振込",
                               "wire", "unauthorized transfer")),
    ("account-takeover", ("乗っ取り", "ログインできない", "パスワード変更された", "二段階", "takeover",
                          "hijack", "locked out")),
    ("phishing", ("フィッシング", "偽サイト", "偽メール", "sms", "ショートメール", "リンク", "phish")),
    ("support-scam", ("サポート詐欺", "警告画面", "ウイルスに感染", "電話してください", "tech support",
                      "microsoft", "遠隔操作")),
    ("romance-scam", ("ロマンス", "国際恋愛", "結婚", "投資を勧め", "romance")),
    ("investment-scam", ("投資詐欺", "必ず儲かる", "暗号資産", "fx", "未公開株", "investment", "crypto")),
    ("ransomware", ("ランサム", "暗号化された", "復号", "身代金", "ransom", "encrypted my")),
    ("impersonation", ("なりすまし", "偽アカウント", "偽プロフィール", "impersonat", "fake account")),
    ("fake-billing", ("架空請求", "未払い", "請求メール", "電子マネー", "ギフトカード", "fake bill")),
    ("leak-extortion", ("流出", "晒す", "拡散する", "脅迫", "sextortion", "leak", "extort")),
    ("sns-fraud", ("sns", "dm", "副業", "もうけ話", "x で", "instagram", "line で")),
)

# scam-kind → ordered free public windows (G5). Codes resolve in the registry (seed).
_WINDOWS: dict[str, tuple[str, ...]] = {
    "unauthorized-transfer": ("bank-direct", "no-and-bank-fund-recovery", "police-cyber-9110"),
    "account-takeover": ("platform-abuse-desk", "police-cyber-9110", "jpcert"),
    "phishing": ("antiphishing-council", "safeline", "police-cyber-9110"),
    "support-scam": ("consumer-188", "police-cyber-9110", "jpcert"),
    "romance-scam": ("police-cyber-9110", "consumer-188", "nccc"),
    "investment-scam": ("police-cyber-9110", "consumer-188", "nccc"),
    "ransomware": ("jpcert", "police-cyber-9110"),
    "impersonation": ("platform-abuse-desk", "police-cyber-9110", "safeline"),
    "fake-billing": ("consumer-188", "police-cyber-9110"),
    "leak-extortion": ("police-cyber-9110", "safeline", "jpcert"),
    "sns-fraud": ("platform-abuse-desk", "consumer-188", "police-cyber-9110"),
}


def _txt(intake: dict) -> str:
    return " ".join(str(intake.get(k, "")) for k in (":case/narrative", ":case/scam-kind", ":case/title")).lower()


def support_cost_jpy(_intake: dict | None = None) -> int:
    """G1 全て無料 INVARIANT — there is no other answer. 助's support always costs 0."""
    return SUPPORT_COST_JPY


def classify(intake: dict) -> str:
    """Return the scam KIND (G4 — for routing, not a verdict). Honors an explicit :case/scam-kind."""
    explicit = str(intake.get(":case/scam-kind", "")).lstrip(":").lower()
    if explicit in SCAM_KINDS:
        return explicit
    blob = _txt(intake)
    for kind, kws in _KEYWORDS:
        if any(kw in blob for kw in kws):
            return kind
    return "sns-fraud"  # safe generic default → still routed to a free window


def assess_severity(intake: dict, kind: str) -> str:
    loss = int(intake.get(":case/loss-jpy", 0) or 0)
    ongoing = bool(intake.get(":case/ongoing", False))
    # money-moving or extortion classes escalate fastest — the clock matters most.
    if kind in ("unauthorized-transfer",) and loss > 0:
        return "critical"
    if kind in ("ransomware", "leak-extortion") or ongoing:
        return "urgent" if loss == 0 else "critical"
    if loss >= 100_000 or kind in ("account-takeover", "investment-scam"):
        return "urgent"
    if loss > 0 or kind in ("phishing", "support-scam", "romance-scam", "fake-billing"):
        return "elevated"
    return "info"


def initial_actions(kind: str) -> list[str]:
    """The first-response checklist, evidence-first then containment then report."""
    base = ["まず証拠を保全(スクショ・URL・メール全文ヘッダ・取引履歴を保存。改変しない)"]
    by_kind = {
        "unauthorized-transfer": [
            "ただちに口座のある金融機関に電話し、不正送金の申告と口座凍結・組戻しを依頼(振り込め詐欺救済法)",
            "ネットバンキングのパスワードを変更し、追加の不正送金を止める",
            "被害届の下書きを作成して最寄りの警察署/サイバー犯罪相談窓口(#9110)へ",
        ],
        "account-takeover": [
            "他端末から該当サービスのパスワードをリセットし、攻撃者のセッションを失効",
            "二段階認証を再設定し、登録メール・電話番号が書き換えられていないか確認",
            "アカウント復旧手順に沿って復旧 → プラットフォーム abuse 窓口へ凍結/復旧依頼",
        ],
        "phishing": [
            "入力してしまった ID/パスワード/カード番号を直ちに変更・停止",
            "フィッシング対策協議会・セーフライン へ URL を通報",
        ],
        "support-scam": [
            "遠隔操作ソフトを入れた場合はネット切断のうえアンインストール、パスワード全変更",
            "電子マネー/ギフトカードで支払った場合は番号と購入レシートを保全",
        ],
        "ransomware": [
            "感染端末をネットワークから隔離(電源は切らずLAN/Wi-Fi遮断)",
            "身代金は支払わず JPCERT/CC へ相談、復号ツールの有無を確認",
        ],
        "leak-extortion": [
            "相手の要求に応じず、やり取りを保全。送金・画像送付をしない",
            "拡散先がある場合はセーフライン/各プラットフォームへ削除通報",
        ],
    }
    tail = [
        "被害状況報告書(時系列)・証拠目録・被害額算定書を作成して届出に添える",
        "無料の公的窓口(警察 #9110 / 消費者ホットライン 188 / NCCC)に相談",
    ]
    return base + by_kind.get(kind, []) + tail


def deadlines(kind: str) -> list[str]:
    """Practical/statutory clocks the victim must not miss (informational, G4 — not legal advice)."""
    d = []
    if kind in ("unauthorized-transfer", "phishing", "account-takeover"):
        d.append("クレジットカード不正利用は約款上おおむね60日以内の申告で補償対象になりやすい — 至急申告")
    if kind in ("fake-billing", "support-scam", "romance-scam", "investment-scam"):
        d.append("通信販売の契約はクーリングオフ対象外のことが多い — ただし不実告知等は取消し得る(消費生活センター 188 で確認)")
    if kind == "unauthorized-transfer":
        d.append("預金口座の凍結は早いほど組戻し成功率が上がる — 認知後ただちに銀行へ")
    return d


def triage(intake: dict) -> dict:
    """Validate (G1/G7) then classify + score + route a victim intake. Raises on a hard gate.

    Returns a triage dict. It NEVER returns a legal verdict (G4) — only a KIND + severity + the
    free public windows + the self-help action checklist.
    """
    if not intake.get(":case/consent", False):
        raise ValueError("G7: a support case is opened only with the victim's explicit consent")
    cost = int(intake.get(":case/support-cost-jpy", 0) or 0)
    if cost != SUPPORT_COST_JPY:
        raise ValueError(f"G1 全て無料: support cost must be 0 (cash≡0); got {cost}")
    if intake.get(":case/server-held-key", False):
        raise ValueError("G7/no-server-key: server-held-key must be false (ADR-2605231525)")

    kind = classify(intake)
    sev = assess_severity(intake, kind)
    return {
        ":triage/case": intake.get(":case/id", "?"),
        ":triage/scam-kind": ":" + kind,
        ":triage/severity": ":" + sev,
        ":triage/support-cost-jpy": SUPPORT_COST_JPY,   # always 0 (G1)
        ":triage/windows": [":" + w for w in _WINDOWS.get(kind, ("police-cyber-9110",))],
        ":triage/actions": initial_actions(kind),
        ":triage/deadlines": deadlines(kind),
        ":triage/paid-referral": False,                 # G5 — never a paid counsel
    }


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn

    seed = load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-cybercrime-cases.kotoba.edn")
    print("# 助 (tasuke) — triage of the :representative victim cases\n")
    print("| case | scam-kind | severity | cost | windows |")
    print("|---|---|---|---|---|")
    for c in seed[":case/batch"]:
        t = triage(c)
        ws = " ".join(w.lstrip(":") for w in t[":triage/windows"])
        print(f"| {t[':triage/case']} | {t[':triage/scam-kind']} | {t[':triage/severity']} | "
              f"¥{t[':triage/support-cost-jpy']} | {ws} |")
