"""Playwright driver — the deterministic e2e layer (no LLM required).

Drives a real Chromium against the target, captures network / console / DOM, and
returns a `Signals` object for signals.evaluate(). To verify SW-SERVED behaviour
(not just SW-registered) it navigates, waits for the Service Worker to activate,
then RELOADS so the SW controls the page — mirroring a repeat visit — and
captures signals on that controlled load.

Runnable as soon as `playwright` + chromium are installed; needs no Murakumo.
"""

from __future__ import annotations

import asyncio

from .signals import Request, Signals

# Heuristic selectors for "a rendered post card" (kept permissive; the yoro feed
# markup uses touch-manipulation cards + post permalinks).
_POST_SELECTORS = (
    "[class*='touch-manipulation']",
    "a[href*='/post/']",
    "[data-testid*='post']",
)


async def capture_signals(
    url: str,
    *,
    headless: bool = True,
    settle_ms: int = 6000,
    post_selector: str | None = None,
) -> Signals:
    from playwright.async_api import async_playwright

    requests: list[Request] = []
    console: list[str] = []
    skeleton_seen = False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        ctx = await browser.new_context(
            viewport={"width": 390, "height": 844}, color_scheme="dark"
        )
        page = await ctx.new_page()

        def on_response(resp):
            try:
                requests.append(Request(
                    url=resp.url, method=resp.request.method,
                    status=resp.status, response_headers=dict(resp.headers),
                ))
            except Exception:
                pass

        page.on("response", on_response)
        page.on("console", lambda m: console.append(f"{m.type}: {m.text}"))

        # 1) First visit — registers + activates the SW (skeleton paints here).
        await page.goto(url, wait_until="domcontentloaded")
        try:
            if await page.query_selector("#kboot"):
                skeleton_seen = True
        except Exception:
            pass
        # Wait for the SW to be ready (registration + activation).
        try:
            await page.evaluate(
                "navigator.serviceWorker ? navigator.serviceWorker.ready.then(()=>true) : true"
            )
        except Exception:
            pass
        await page.wait_for_timeout(1500)

        # 2) Controlled reload — now the SW intercepts /xrpc/* (the real path).
        requests.clear()
        console.clear()
        await page.reload(wait_until="domcontentloaded")
        if not skeleton_seen:
            try:
                if await page.query_selector("#kboot"):
                    skeleton_seen = True
            except Exception:
                pass
        await page.wait_for_timeout(settle_ms)

        # DOM facts.
        sw_controller = bool(await page.evaluate(
            "!!(navigator.serviceWorker && navigator.serviceWorker.controller)"
        ))
        skeleton_removed = not bool(await page.evaluate(
            "!!document.getElementById('kboot')"
        ))
        post_count = 0
        for sel in ([post_selector] if post_selector else list(_POST_SELECTORS)):
            try:
                n = await page.eval_on_selector_all(sel, "els => els.length")
                post_count = max(post_count, int(n or 0))
            except Exception:
                continue

        await browser.close()

    return Signals(
        requests=requests,
        console=console,
        sw_controller=sw_controller,
        post_count=post_count,
        skeleton_seen=skeleton_seen,
        skeleton_removed=skeleton_removed,
    )


def capture_signals_sync(url: str, **kw) -> Signals:
    return asyncio.run(capture_signals(url, **kw))
