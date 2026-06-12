;; ported from 70-tools/kotoba-e2e/kotoba_e2e/browser.py (unit_refactor stage 0)
;; Playwright driver — the deterministic e2e layer (no LLM required).
(ns kotoba-e2e.kotoba-e2e.browser
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare post-selectors capture-signals capture-signals-sync)

;; TODO: port-failed unit _POST_SELECTORS (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpvx1juekp/scratch.clj:2:1: er)
;; _POST_SELECTORS = (
;;     "[class*='touch-manipulation']",
;;     "a[href*='/post/']",
;;     "[data-testid*='post']",
;; )
(def post-selectors nil) ;; TODO: port-failed const

;; TODO: port-failed unit capture_signals (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp1dbqp4s1/scratch.clj:2:24: w)
;; async def capture_signals(
;;     url: str,
;;     *,
;;     headless: bool = True,
;;     settle_ms: int = 6000,
;;     post_selector: str | None = None,
;; ) -> Signals:
;;     from playwright.async_api import async_playwright
;; 
;;     requests: list[Request] = []
;;     console: list[str] = []
;;     skeleton_seen = False
;; 
;;     async with async_playwright() as p:
;;         browser = await p.chromium.launch(headless=headless)
;;         ctx = await browser.new_context(
;;             viewport={"width": 390, "height": 844}, color_scheme="dark"
;;         )
;;         page = await ctx.new_page()
;; 
;;         def on_response(resp):
;;             try:
;;                 requests.append(Request(
;;                     url=resp.url, method=resp.request.method,
;;                     status=resp.status, response_headers=dict(resp.headers),
;;                 ))
;;             except Exception:
;;                 pass
;; 
;;         page.on("response", on_response)
;;         page.on("console", lambda m: console.append(f"{m.type}: {m.text}"))
;; 
;;         # 1) First visit — registers + activates the SW (skeleton paints here).
;;         await page.goto(url, wait_until="domcontentloaded")
;;         try:
;;             if await page.query_selector("#kboot"):
;;                 skeleton_seen = True
;;         except Exception:
;;             pass
;;         # Wait for the SW to be ready (registration + activation).
;;         try:
;;             await page.evaluate(
;;                 "navigator.serviceWorker ? navigator.serviceWorker.ready.then(()=>true) : true"
;;             )
;;         except Exception:
;;             pass
;;         await page.wait_for_timeout(1500)
;; 
;;         # 2) Controlled reload — now the SW intercepts /xrpc/* (the real path).
;;         requests.clear()
;;         console.clear()
;;         await page.reload(wait_until="domcontentloaded")
;;         if not skeleton_seen:
;;             try:
;;                 if await page.query_selector("#kboot"):
;;                     skeleton_seen = True
;;             except Exception:
;;                 pass
;;         await page.wait_for_timeout(settle_ms)
;; 
;;         # DOM facts.
;;         sw_controller = bool(await page.evaluate(
;;             "!!(navigator.serviceWorker && navigator.serviceWorker.controller)"
;;         ))
;;         skeleton_removed = not bool(await page.evaluate(
;;             "!!document.getElementById('kboot')"
;;         ))
;;         post_count = 0
;;         for sel in ([post_selector] if post_selector else list(_POST_SELECTORS)):
;;             try:
;;                 n = await page.eval_on_selector_all(sel, "els => els.length")
;;                 post_count = max(post_count, int(n or 0))
;;             except Exception:
;;                 continue
;; 
;;         await browser.close()
;; 
;;     return Signals(
;;         requests=requests,
;;         console=console,
;;         sw_controller=sw_controller,
;;         post_count=post_count,
;;         skeleton_seen=skeleton_seen,
;;         skeleton_removed=skeleton_removed,
;;     )
(defn capture-signals [& _]
  (throw (ex-info "TODO: port-failed" {:from "capture_signals"})))

(defn capture-signals-sync [url & kwargs]
  (let [async-result (future (capture-signals url kwargs))]
    (.get async-result)))

