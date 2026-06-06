"""intake.py — 助 (tasuke) plain-language intake: 誰でも使える, no EDN required.

Lets a non-technical victim build their case by answering plain questions, then hands the case to
`packet.build_packet` / `packet.write_packet`. The mapping from answers → a `:case/*` dict is a
PURE FUNCTION (`build_case_from_answers`) so it is fully testable without stdin; the interactive
loop is a thin shell around it.

The charter invariants are baked into the mapping, not left to the asker:
  G1 — :case/support-cost-jpy is hard-set to 0 (the victim is never asked for, and cannot enter, a fee).
  G7 — :case/consent comes from an explicit yes/no; without a clear yes, no case is built (raises).
  G7 — :case/server-held-key is hard-set to false.

Stdlib only. The loss parser accepts 「480000」「48万」「48万円」「480,000円」 and returns yen as int.
"""

from __future__ import annotations

import hashlib
import re

# (field, prompt, kind) — shared by the interactive loop AND the tests.
QUESTIONS = [
    ("consent",     "この内容で被害対応を進めてよいですか? (はい/いいえ)",                       "yesno"),
    ("narrative",   "何が起きましたか? できるだけ具体的に教えてください",                         "text"),
    ("occurred",    "いつ起きましたか? (例: 2026-06-03 朝)",                                   "text"),
    ("loss",        "金銭被害はいくらですか? (例: 48万 / 480000 / なし)",                       "yen"),
    ("service",     "関係するサービス名は? (例: ○○銀行 / LINE / なければ空欄)",                  "text"),
    ("account_id",  "対象のアカウントID・口座・URL があれば教えてください",                       "text"),
]

_YES = ("はい", "yes", "y", "はい。", "ok", "進める", "true", "1")
_NO = ("いいえ", "no", "n", "やめる", "false", "0", "")


def parse_yesno(s: str) -> bool:
    return str(s).strip().lower() in _YES


def parse_yen(s: str) -> int:
    """「48万」「480,000円」「なし」→ int yen. Best-effort; returns 0 when none/unparseable."""
    t = str(s).strip().replace(",", "").replace("円", "")
    if not t or t in ("なし", "無し", "ない", "0"):
        return 0
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*万\s*(\d+)?\s*$", t)
    if m:
        man = float(m.group(1)) * 10000
        return int(man + int(m.group(2) or 0))
    m = re.match(r"^\s*(\d+)\s*$", t)
    return int(m.group(1)) if m else 0


def _case_id(narrative: str, occurred: str) -> str:
    h = hashlib.sha1(f"{narrative}|{occurred}".encode("utf-8")).hexdigest()[:8]
    return f"case-{h}"


def build_case_from_answers(answers: dict, subject: str = "did:web:etzhayyim.com:member:self") -> dict:
    """Map plain answers → a :case/* dict. PURE. Raises (G7) if consent is not clearly given."""
    if not parse_yesno(answers.get("consent", "")):
        raise ValueError("G7: 被害者の明確な同意がなければ case は作成しません (はい/yes が必要)")
    narrative = str(answers.get("narrative", "")).strip()
    occurred = str(answers.get("occurred", "")).strip()
    case = {
        ":case/id": answers.get("case_id") or _case_id(narrative, occurred),
        ":case/subject": subject,
        ":case/narrative": narrative,
        ":case/occurred-at-text": occurred,
        ":case/loss-jpy": parse_yen(answers.get("loss", "")),
        ":case/service": str(answers.get("service", "")).strip(),
        ":case/account-id": str(answers.get("account_id", "")).strip(),
        # ── invariants baked in, never asked ──
        ":case/consent": True,            # G7 (we got here only via an explicit yes)
        ":case/support-cost-jpy": 0,      # G1 全て無料
        ":case/server-held-key": False,   # G7 no-server-key
    }
    if case[":case/loss-jpy"] > 0:
        case[":case/loss-breakdown"] = [{":label": "被害額", ":jpy": case[":case/loss-jpy"]}]
    return case


def interactive(ask=input) -> dict:
    """Ask the questions on the console and return the built case. `ask` is injectable for tests."""
    answers = {}
    for field, prompt, _kind in QUESTIONS:
        answers[field] = ask(f"{prompt}\n> ")
        if field == "consent" and not parse_yesno(answers[field]):
            raise SystemExit("同意が得られませんでした。対応を中止します。")
    return build_case_from_answers(answers)


if __name__ == "__main__":
    import packet

    print("助 (tasuke) — サイバー犯罪 被害対応(無料)。いくつか質問します。\n")
    case = interactive()
    p = packet.build_packet(case)
    out = packet.write_packet(p)
    print("\n" + packet._cover(p))
    print(f"\n→ {len(p['documents'])} 通の書類を {out}/ に作成しました(費用: ¥{p['cost']})。")
    print("  各書類を印刷し、内容を確認・署名のうえ、ご自身で提出してください。")
