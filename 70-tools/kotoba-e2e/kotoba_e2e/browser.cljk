;; ported from 70-tools/kotoba-e2e/kotoba_e2e/browser.py — real port replacing the
;; unit_refactor stage-0 "TODO: port-failed" stub. NS fixed (the doubled
;; "kotoba-e2e.kotoba-e2e.*" -> path-derived "kotoba-e2e.browser") and the file is now .cljc.
;; Self-contained; no dependency on any sibling namespace.
;;
;; NOTE ON FIDELITY: browser.py is a Playwright async driver — its essence is real
;; Chromium automation (page.goto / reload / evaluate / eval_on_selector_all). There is
;; no pure-Clojure equivalent of Playwright, so the deterministic POST-SELECTOR data and
;; the controlled-load capture ALGORITHM are ported faithfully here, while the actual
;; browser interop is isolated behind #?(:clj ...) and expressed against a small driver
;; abstraction (a map of fns) that a host wires to a real Playwright session. The pure,
;; testable layer of this harness is signals.py (the verification contract); this module
;; is the I/O edge.
(ns kotoba-e2e.browser
  "browser.py — Playwright driver, the deterministic e2e layer (no LLM required).

  Drives a real Chromium against the target, captures network / console / DOM, and
  returns a `signals` map for signals/evaluate. To verify SW-SERVED behaviour (not just
  SW-registered) it navigates, waits for the Service Worker to activate, then RELOADS so
  the SW controls the page — mirroring a repeat visit — and captures signals on that
  controlled load.")

;; Heuristic selectors for "a rendered post card" (kept permissive; the yoro feed markup
;; uses touch-manipulation cards + post permalinks). Faithful 1:1 of _POST_SELECTORS.
(def post-selectors
  ["[class*='touch-manipulation']"
   "a[href*='/post/']"
   "[data-testid*='post']"])

(defn- max-post-count
  "Port of the post-count loop: over the chosen selectors, eval els.length on the page
  and take the max (0 when none match / errors). `count-fn` = (fn [selector] -> int|nil),
  the host's eval_on_selector_all('els => els.length') bound to the live page.
  Pure given count-fn — the selection of selectors mirrors the Python:
  [post_selector] when given, else the full list(_POST_SELECTORS)."
  [count-fn post-selector]
  (let [selectors (if post-selector [post-selector] post-selectors)]
    (reduce (fn [acc sel]
              (let [n (try (count-fn sel) (catch #?(:clj Exception :default :default) _ nil))]
                (max acc (int (or n 0)))))
            0
            selectors)))

(defn capture-signals
  "Controlled-load capture against `url`, returning a signals map shaped like
  signals.Signals: {\"requests\" [...] \"console\" [...] \"sw_controller\" bool
  \"post_count\" int \"skeleton_seen\" bool \"skeleton_removed\" bool}.

  `driver` is a map of host-bound fns wiring a real Playwright (async) session — the
  #?(:clj ...) browser interop the porter must supply:
    :launch        (fn [{:keys [headless]}] -> page-ctx)   open chromium + 390x844 dark ctx + page
    :on-response   (fn [page-ctx f])   register resp -> {url,method,status,response_headers}
    :on-console    (fn [page-ctx f])   register console msg -> \"type: text\"
    :goto          (fn [page-ctx url])
    :query?        (fn [page-ctx sel] -> bool)              query_selector present?
    :evaluate      (fn [page-ctx js] -> any)
    :wait          (fn [page-ctx ms])
    :reload        (fn [page-ctx])
    :clear-requests(fn [page-ctx])  :clear-console (fn [page-ctx])
    :count         (fn [page-ctx sel] -> int)               eval_on_selector_all length
    :close         (fn [page-ctx])
  This keeps the controlled-load ALGORITHM (goto -> SW ready -> reload -> settle ->
  capture) faithful and host-agnostic; opts: :headless (default true), :settle-ms
  (default 6000), :post-selector (default nil)."
  [driver url & {:keys [headless settle-ms post-selector]
                 :or {headless true settle-ms 6000}}]
  #?(:clj
     (let [requests (atom [])
           console (atom [])
           skeleton-seen (atom false)
           {:keys [launch on-response on-console goto query? evaluate wait reload
                   clear-requests clear-console count close]} driver
           page (launch {:headless headless})]
       (on-response page (fn [resp] (swap! requests conj resp)))
       (on-console page (fn [msg] (swap! console conj msg)))
       ;; 1) First visit — registers + activates the SW (skeleton paints here).
       (goto page url)
       (try (when (query? page "#kboot") (reset! skeleton-seen true))
            (catch Exception _ nil))
       ;; Wait for the SW to be ready (registration + activation).
       (try (evaluate page "navigator.serviceWorker ? navigator.serviceWorker.ready.then(()=>true) : true")
            (catch Exception _ nil))
       (wait page 1500)
       ;; 2) Controlled reload — now the SW intercepts /xrpc/* (the real path).
       (clear-requests page) (reset! requests [])
       (clear-console page) (reset! console [])
       (reload page)
       (when-not @skeleton-seen
         (try (when (query? page "#kboot") (reset! skeleton-seen true))
              (catch Exception _ nil)))
       (wait page settle-ms)
       ;; DOM facts.
       (let [sw-controller (boolean (evaluate page "!!(navigator.serviceWorker && navigator.serviceWorker.controller)"))
             skeleton-removed (not (boolean (evaluate page "!!document.getElementById('kboot')")))
             post-count (max-post-count (fn [sel] (count page sel)) post-selector)]
         (close page)
         {"requests" @requests
          "console" @console
          "sw_controller" sw-controller
          "post_count" post-count
          "skeleton_seen" @skeleton-seen
          "skeleton_removed" skeleton-removed}))
     :default
     (throw (ex-info "capture-signals requires a host Playwright driver (clj only)"
                     {:url url}))))

(defn capture-signals-sync
  "Synchronous wrapper — Python ran asyncio.run(capture_signals(...)). Here capture-signals
  is already synchronous against the host driver, so this simply forwards."
  [driver url & kwargs]
  (apply capture-signals driver url kwargs))

;; The Python module exposes no __main__ demo; nothing to omit beyond the lazy
;; playwright import, which is folded into the injected `driver`.
