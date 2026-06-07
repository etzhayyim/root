"""lg-chat `sodai_submit` graph — 渋谷区 粗大ごみ 公式フォーム自動入力 (browser use).

チャットウィザード (SodaiWizard.svelte) が生成した「正規化済み申請JSON」を受け取り、
Playwright で公式受付フォーム (sodai.tokyokankyo.or.jp) を開いて各フィールドへ
自動入力する。**最終送信は人間ゲート** — 既定では送信せず、入力済み画面のスクショを
返すだけ。

設計上の不変条件 (安全境界):
  1. 最終送信 (irreversible) は二重ゲート:
       mode == "submit"  AND  human_approved is True  AND  env SODAI_ALLOW_SUBMIT == "1"
     のすべてが揃ったときのみ「送信」を押す。既定 (prefill) は決して送信しない。
  2. CAPTCHA / bot 認証を検知したら即中断 (captcha_detected=True)。突破は試みない。
  3. フォームのフィールドセレクタは実物未確認のため calibration 必須。
     env SODAI_FIELD_MAP (JSON) で上書きでき、mode="discover" で実フォームの
     input/select を列挙して校正を助ける。

State machine:
  START → validate → drive → END
    validate : 入力JSONの形と mode を検証
    drive    : Playwright でブラウザ操作 (discover | prefill | submit)

Input (body.input):
  {
    "application": {
      "items": [{"name": "ソファー（2人以上用）", "qty": 1}],
      "name": "渋谷　太郎", "nameKana": "シブヤ　タロウ",
      "postal": "150-8010", "address": "渋谷区宇田川町１－１",
      "building": "", "phone": "0312345678", "email": "",
      "preferredDate": ""
    },
    "mode": "prefill",            # discover | prefill | submit
    "human_approved": false,      # submit 時のみ意味を持つ
    "ward_url": "https://sodai.tokyokankyo.or.jp/Sodai/V2Main/13113/0"
  }

Output state fields:
  status          : "ok" | "captcha" | "error" | "playwright_missing"
  mode            : 実行された mode
  discovered_fields : list[dict]  (mode=discover 時)
  filled          : list[dict]    {field, selector, value, ok}
  screenshot_b64  : str           入力済みフォームの PNG (base64)
  submitted       : bool
  captcha_detected: bool
  error           : str | None
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_chat.sodai_fields import CAPTCHA_MARKERS, RECEPTION_URL, load_field_map

_log = logging.getLogger(__name__)

# 既定受付URL = shibuya actor 境界 (sodai_fields.RECEPTION_URL)。env で上書き可。
_DEFAULT_WARD_URL = os.environ.get("SODAI_WARD_URL", RECEPTION_URL)
_NAV_TIMEOUT_MS = int(os.environ.get("SODAI_NAV_TIMEOUT_MS", "30000"))
_ALLOW_SUBMIT = os.environ.get("SODAI_ALLOW_SUBMIT", "0") == "1"

# field-map / CAPTCHA マーカーは lg_chat/sodai_fields.py に集約 (SSoT)。
_CAPTCHA_MARKERS = CAPTCHA_MARKERS
_load_field_map = load_field_map


class _SodaiState(TypedDict, total=False):
    # Input
    application: dict[str, Any]
    mode: str
    human_approved: bool
    ward_url: str
    # Output
    status: str
    discovered_fields: list[dict[str, Any]]
    filled: list[dict[str, Any]]
    screenshot_b64: str
    submitted: bool
    captcha_detected: bool
    error: str | None


# ── nodes ──────────────────────────────────────────────────────────────


async def _node_validate(state: _SodaiState) -> dict[str, Any]:
    mode = str(state.get("mode") or "prefill").lower()
    if mode not in {"discover", "prefill", "submit"}:
        return {"status": "error", "error": f"unknown mode: {mode}"}
    app = state.get("application") or {}
    if mode != "discover" and not isinstance(app, dict):
        return {"status": "error", "error": "application must be an object"}
    return {"mode": mode, "submitted": False, "captcha_detected": False}


async def _node_drive(state: _SodaiState) -> dict[str, Any]:
    if state.get("status") == "error":
        return {}

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError:
        return {
            "status": "playwright_missing",
            "error": (
                "playwright がこの pod に未導入です。ブラウザ対応の lg-chat イメージ "
                "(playwright install chromium 済み) を deploy してください。"
            ),
        }

    mode = str(state.get("mode") or "prefill")
    url = str(state.get("ward_url") or _DEFAULT_WARD_URL)
    app = state.get("application") or {}
    field_map = _load_field_map()

    out: dict[str, Any] = {"filled": [], "discovered_fields": []}

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            ctx = await browser.new_context(
                locale="ja-JP",
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                ),
            )
            page = await ctx.new_page()
            try:
                await page.goto(url, timeout=_NAV_TIMEOUT_MS, wait_until="networkidle")
            except Exception as exc:  # noqa: BLE001
                await browser.close()
                return {"status": "error", "error": f"navigation failed: {type(exc).__name__}: {exc!s}"[:300]}

            # CAPTCHA 検知 → 即中断 (突破しない)。
            html = (await page.content()).lower()
            if any(m.lower() in html for m in _CAPTCHA_MARKERS):
                shot = await page.screenshot(full_page=False)
                await browser.close()
                return {
                    "status": "captcha",
                    "captcha_detected": True,
                    "screenshot_b64": base64.b64encode(shot).decode(),
                    "error": "CAPTCHA/bot認証を検知しました。自動操作を中断します（突破は行いません）。",
                }

            # discover: 実フォームの入力要素を列挙して校正を助ける。
            if mode == "discover":
                fields = await page.eval_on_selector_all(
                    "input, select, textarea",
                    """els => els.map(e => ({
                        tag: e.tagName.toLowerCase(),
                        type: e.getAttribute('type') || '',
                        name: e.getAttribute('name') || '',
                        id: e.id || '',
                        placeholder: e.getAttribute('placeholder') || '',
                        ariaLabel: e.getAttribute('aria-label') || '',
                    }))""",
                )
                shot = await page.screenshot(full_page=True)
                await browser.close()
                return {
                    "status": "ok",
                    "discovered_fields": fields,
                    "screenshot_b64": base64.b64encode(shot).decode(),
                }

            # prefill / submit: 正規化済みの値を各フィールドへ入力する。
            filled: list[dict[str, Any]] = []
            for key, selectors in field_map.items():
                value = str(app.get(key) or "").strip()
                if not value:
                    continue
                ok = False
                used = ""
                for sel in selectors:
                    try:
                        el = await page.query_selector(sel)
                        if el and await el.is_visible():
                            await el.fill(value)
                            ok, used = True, sel
                            break
                    except Exception:  # noqa: BLE001
                        continue
                filled.append({"field": key, "selector": used, "value": value, "ok": ok})
            out["filled"] = filled

            shot = await page.screenshot(full_page=True)
            out["screenshot_b64"] = base64.b64encode(shot).decode()

            # 最終送信は二重ゲート。既定 (prefill) では決して押さない。
            submitted = False
            if mode == "submit":
                human_ok = bool(state.get("human_approved"))
                if human_ok and _ALLOW_SUBMIT:
                    # 送信ボタンの候補。実フォームに合わせて要校正。
                    for sub_sel in ["button[type=submit]", "input[type=submit]",
                                    "button:has-text('申込')", "button:has-text('確定')",
                                    "button:has-text('送信')"]:
                        try:
                            btn = await page.query_selector(sub_sel)
                            if btn and await btn.is_visible():
                                await btn.click()
                                await page.wait_for_load_state("networkidle", timeout=_NAV_TIMEOUT_MS)
                                submitted = True
                                out["screenshot_b64"] = base64.b64encode(
                                    await page.screenshot(full_page=True)
                                ).decode()
                                break
                        except Exception:  # noqa: BLE001
                            continue
                else:
                    out["error"] = (
                        "送信は実行しませんでした。human_approved=true かつ "
                        "サーバ側 SODAI_ALLOW_SUBMIT=1 の両方が必要です（人間ゲート）。"
                    )
            out["submitted"] = submitted
            out["status"] = "ok"
            await browser.close()
            return out
    except Exception as exc:  # noqa: BLE001
        _log.exception("sodai_submit drive failed")
        return {"status": "error", "error": f"{type(exc).__name__}: {exc!s}"[:300]}


# ── graph ──────────────────────────────────────────────────────────────


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_SodaiState)
    g.add_node("validate", _node_validate)
    g.add_node("drive", _node_drive)
    g.add_edge(START, "validate")
    g.add_edge("validate", "drive")
    g.add_edge("drive", END)
    return g


GRAPH = _build().compile(name="sodai_submit")
