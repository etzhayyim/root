;; ported from 60-apps/etzhayyim-project-mangaka/lg/lg_mangaka/graphs/mangaka_generate_page.py (unit_refactor stage 0)
;; mangaka_generate_page — character-stable page from a panel layout.
(ns lg.lg-mangaka.graphs.mangaka-generate-page
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare log merge-list state plan render-all-panels composite-blocking composite build-graph graph)

(def _log (clojure.core/with-open [logger (clojure.java.util/logging.getLogger "mangaka_generate_page")] logger))

(defn merge-list [a b]
  (concat (or a nil) (or b nil)))

(def state-keys
  [:page-rkey :page-width :page-height :gutter :border
   :reference-image-b64 :reference-image-mime :panels
   :base-denoise :refine-denoise :seed-base
   :comfy-url :timeout-seconds
   :uploaded-filename :panel-results :page-image-inline-b64 :status :elapsed-ms :error :started-at-ms])

(defn state-default []
  {:page-rkey nil
   :page-width 0
   :page-height 0
   :gutter 0
   :border 0
   :reference-image-b64 nil
   :reference-image-mime nil
   :panels nil
   :base-denoise 0.0
   :refine-denoise 0.0
   :seed-base 0
   :comfy-url nil
   :timeout-seconds 0
   :uploaded-filename nil
   :panel-results []
   :page-image-inline-b64 nil
   :status ""
   :elapsed-ms 0
   :error nil
   :started-at-ms 0})

;; TODO: port-failed unit _plan (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpoipk3inz/scratch.clj:3:3: wa)
;; async def _plan(state: _State) -> dict[str, Any]:
;;     if not state.get("reference_image_b64"):
;;         return {"status": "error", "error": "reference_image_b64 required"}
;;     panels = state.get("panels") or []
;;     if not panels:
;;         return {"status": "error", "error": "panels (list) required"}
;;     started = int(time.time() * 1000)
;; 
;;     up = await _runner.upload_image_b64(
;;         state["reference_image_b64"],
;;         comfy_url=state.get("comfy_url") or _runner.DEFAULT_URL,
;;         filename_hint=f"mangaka-page-{state.get('page_rkey') or 'page'}",
;;         image_mime=state.get("reference_image_mime") or "image/png",
;;     )
;;     if up.get("error"):
;;         return {"status": "error", "error": up["error"]}
;;     return {
;;         "uploaded_filename": up["filename"],
;;         "started_at_ms": started,
;;     }
(defn plan [& _]
  (throw (ex-info "TODO: port-failed" {:from "_plan"})))

;; TODO: port-failed unit _render_all_panels (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpdi42__0g/scratch.clj:2:1: er)
;; async def _render_all_panels(state: _State) -> dict[str, Any]:
;;     if state.get("status") == "error":
;;         return {}
;;     panels = state.get("panels") or []
;;     comfy_url = state.get("comfy_url") or _runner.DEFAULT_URL
;;     seed_base = int(state.get("seed_base") or 0) or int(time.time())
;;     panel_results: list[dict[str, Any]] = []
;; 
;;     for i, p in enumerate(panels):
;;         started = int(time.time() * 1000)
;;         wf = _wf.panel_stable_workflow(
;;             panel_rkey=str(p.get("panel_rkey") or f"p{i:02d}"),
;;             reference_image_filename=state["uploaded_filename"],
;;             framing=p.get("framing") or "medium",
;;             characters=list(p.get("characters") or []),
;;             environment=p.get("environment") or "",
;;             mood=p.get("mood") or "",
;;             action=p.get("action") or "",
;;             base_denoise=float(state.get("base_denoise") or 0.65),
;;             refine_denoise=float(state.get("refine_denoise") or 0.4),
;;             seed=(seed_base + i * 1009) & 0xFFFFFFFF,
;;         )
;;         sub = await _runner.submit_workflow(wf, comfy_url=comfy_url)
;;         if sub.get("status") == "error":
;;             panel_results.append({
;;                 "panel_rkey": p.get("panel_rkey") or f"p{i:02d}",
;;                 "ok": False, "error": sub.get("error"),
;;             })
;;             continue
;;         poll = await _runner.poll_outputs(
;;             sub["prompt_id"], comfy_url=comfy_url,
;;             started_at_ms=sub.get("started_at_ms", started),
;;             timeout_seconds=int(state.get("timeout_seconds") or 300),
;;         )
;;         # Prefer the inked output (node 13) over the composition (node 7).
;;         imgs = poll.get("images") or []
;;         inked = next((im for im in imgs if im.get("node") == "13"), None) or (imgs[-1] if imgs else None)
;;         panel_results.append({
;;             "panel_rkey": p.get("panel_rkey") or f"p{i:02d}",
;;             "x": int(p.get("x") or 0), "y": int(p.get("y") or 0),
;;             "w": int(p.get("w") or 0), "h": int(p.get("h") or 0),
;;             "ok": bool(inked),
;;             "image_b64": (inked or {}).get("imageInlineB64") or "",
;;             "image_mime": (inked or {}).get("imageMime") or "image/png",
;;             "latency_ms": poll.get("elapsed_ms") or 0,
;;             "error": poll.get("error"),
;;         })
;; 
;;     return {"panel_results": panel_results}
(defn render-all-panels [& _]
  (throw (ex-info "TODO: port-failed" {:from "_render_all_panels"})))

;; TODO: port-failed unit _composite_blocking (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpi3pwjyh8/scratch.clj:2:1: er)
;; def _composite_blocking(state: _State) -> tuple[str, str | None]:
;;     try:
;;         from PIL import Image, ImageDraw  # noqa: WPS433
;;     except Exception as exc:  # noqa: BLE001
;;         return "", f"PIL not available: {exc}"
;; 
;;     panels = state.get("panel_results") or []
;;     w = int(state.get("page_width") or 1280)
;;     h = int(state.get("page_height") or 1817)
;;     gutter = int(state.get("gutter") or 12)
;;     border = int(state.get("border") or 2)
;;     canvas = Image.new("RGB", (w, h), "white")
;;     draw = ImageDraw.Draw(canvas)
;; 
;;     for pr in panels:
;;         if not pr.get("ok") or not pr.get("image_b64"):
;;             continue
;;         try:
;;             img = Image.open(io.BytesIO(base64.b64decode(pr["image_b64"]))).convert("RGB")
;;         except Exception:  # noqa: BLE001
;;             continue
;;         bx, by, bw, bh = pr.get("x", 0), pr.get("y", 0), pr.get("w", 0), pr.get("h", 0)
;;         if bw <= 0 or bh <= 0:
;;             continue
;;         # Apply gutter padding inside the bbox.
;;         target_w = max(1, bw - gutter)
;;         target_h = max(1, bh - gutter)
;;         # Resize preserving aspect, then center-crop to (target_w, target_h)
;;         src_ratio = img.width / img.height
;;         dst_ratio = target_w / target_h
;;         if src_ratio > dst_ratio:
;;             new_h = target_h
;;             new_w = int(round(target_h * src_ratio))
;;         else:
;;             new_w = target_w
;;             new_h = int(round(target_w / src_ratio))
;;         img = img.resize((new_w, new_h), Image.LANCZOS)
;;         ox = (new_w - target_w) // 2
;;         oy = (new_h - target_h) // 2
;;         img = img.crop((ox, oy, ox + target_w, oy + target_h))
;;         canvas.paste(img, (bx + gutter // 2, by + gutter // 2))
;;         if border > 0:
;;             draw.rectangle(
;;                 [(bx + gutter // 2, by + gutter // 2),
;;                  (bx + gutter // 2 + target_w - 1, by + gutter // 2 + target_h - 1)],
;;                 outline="black", width=border,
;;             )
;; 
;;     out = io.BytesIO()
;;     canvas.save(out, format="PNG", optimize=True)
;;     return base64.b64encode(out.getvalue()).decode("ascii"), None
(defn composite-blocking [& _]
  (throw (ex-info "TODO: port-failed" {:from "_composite_blocking"})))

;; TODO: port-failed unit _composite (assembled-lint error)
;; async def _composite(state: _State) -> dict[str, Any]:
;;     if state.get("status") == "error":
;;         return {}
;;     b64, err = await asyncio.to_thread(_composite_blocking, state)
;;     elapsed = int(time.time() * 1000) - int(state.get("started_at_ms") or 0)
;;     if err:
;;         return {"status": "error", "error": err, "elapsed_ms": elapsed}
;;     return {
;;         "page_image_inline_b64": b64,
;;         "status": "ok",
;;         "elapsed_ms": elapsed,
;;     }
(defn composite [& _]
  (throw (ex-info "TODO: port-failed" {:from "_composite"})))

;; TODO: port-failed unit _build_graph (assembled-lint error)
;; def _build_graph() -> StateGraph:
;;     g: StateGraph = StateGraph(_State)
;;     g.add_node("plan",      _plan, retry_policy=RetryPolicy(max_attempts=2))
;;     g.add_node("render",    _render_all_panels)
;;     g.add_node("composite", _composite)
;;     g.add_edge(START, "plan")
;;     g.add_edge("plan", "render")
;;     g.add_edge("render", "composite")
;;     g.add_edge("composite", END)
;;     return g
(defn build-graph [& _]
  (throw (ex-info "TODO: port-failed" {:from "_build_graph"})))

;; TODO: port-failed unit GRAPH (assembled-lint error)
;; GRAPH = _build_graph().compile(name="mangaka_generate_page")
(def graph nil) ;; TODO: port-failed const

