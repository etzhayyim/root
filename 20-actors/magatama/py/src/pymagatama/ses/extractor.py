"""SES案件 LLM extractor — Phase 2 (ADR-2605120000).

Calls ``call_tier_json("ses-extraction", ...)`` which routes to
DeepSeek Pro V4 via llm.gftd.ai → OpenRouter.  Returns an
``AnkenExtraction`` or None on parse/confidence failure.
"""

from __future__ import annotations

from typing import Optional

from pymagatama.llm import LlmError, call_tier_json
from pymagatama.ses.state import AnkenExtraction, Jokyo

_SYSTEM = """\
あなたはSES（システムエンジニアリングサービス）案件メール解析AIです。
メール本文から案件情報を抽出し、以下のJSON形式のみで返してください。
コードブロック・説明文は一切不要です。

{
  "client_name": "クライアント担当者名（不明なら空文字）",
  "client_company": "クライアント企業名（不明なら null）",
  "skill_requirements": ["スキル1", "スキル2"],
  "jokyo": "提案中|選考中|契約|稼働中|終了|見送り|中途終了",
  "start_month": "YYYY-MM または null",
  "end_month": "YYYY-MM または null",
  "rate_lower_yen": 月額下限円（整数）または null,
  "rate_upper_yen": 月額上限円（整数）または null,
  "work_location": "勤務地（不明なら null）",
  "remote_ok": true/false/null,
  "engineer_name": "エンジニア名（不明なら null）",
  "notes": "備考200文字以内（なければ null）",
  "confidence": 0.0〜1.0（SES案件メールとしての確信度。0.6未満は破棄）,
  "rationale": "判断理由200文字以内"
}

jokyo は必ずいずれか一つを選択してください。
メールがSES案件でない場合は confidence を 0.0 以下にしてください。
"""


def extract_anken(parsed_text: str) -> Optional[AnkenExtraction]:
    """Extract structured AnkenExtraction from email text.

    Returns None if:
    - LLM call fails
    - JSON parse fails
    - Pydantic validation fails
    - confidence < 0.6
    """
    resp = call_tier_json(
        "ses-extraction",
        system=_SYSTEM,
        user=parsed_text[:4000],
        max_tokens=1024,
        temperature=0.1,
    )
    if not resp.get("ok"):
        return None

    data = resp.get("data") or {}

    # Normalise jokyo to enum value
    raw_jokyo = data.get("jokyo", "提案中")
    jokyo_map = {j.value: j for j in Jokyo}
    if raw_jokyo not in jokyo_map:
        raw_jokyo = Jokyo.TEIAN.value

    data["jokyo"] = jokyo_map[raw_jokyo]

    try:
        extraction = AnkenExtraction.model_validate(data)
    except Exception:
        return None

    if extraction.confidence < 0.6:
        return None

    return extraction


def extract_anken_with_meta(
    parsed_text: str,
) -> tuple[Optional[AnkenExtraction], str, int]:
    """Like extract_anken but also returns (model_id, tokens_total).

    Returns (None, "", 0) on failure.
    """
    try:
        resp = call_tier_json(
            "ses-extraction",
            system=_SYSTEM,
            user=parsed_text[:4000],
            max_tokens=1024,
            temperature=0.1,
        )
    except LlmError:
        return None, "", 0

    if not resp.get("ok"):
        return None, resp.get("model", ""), 0

    data = resp.get("data") or {}
    model_id: str = resp.get("model", "")
    usage = resp.get("usage") or {}
    tokens = int((usage.get("total_tokens") or usage.get("usage") or 0))

    raw_jokyo = data.get("jokyo", "提案中")
    jokyo_map = {j.value: j for j in Jokyo}
    if raw_jokyo not in jokyo_map:
        raw_jokyo = Jokyo.TEIAN.value
    data["jokyo"] = jokyo_map[raw_jokyo]

    try:
        extraction = AnkenExtraction.model_validate(data)
    except Exception:
        return None, model_id, tokens

    if extraction.confidence < 0.6:
        return None, model_id, tokens

    return extraction, model_id, tokens
