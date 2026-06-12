;; ported from 60-apps/etzhayyim-project-mangaka/lg/lg_mangaka/graphs/comfy_run.py (unit_refactor stage 0)
;; mangaka `comfy_run` — passthrough to ComfyUI for arbitrary workflows.
(ns lg.lg-mangaka.graphs.comfy-run
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare log state base-url submit poll build graph)

;; TODO: port-failed unit _log (assembled-lint error)
;; _log = logging.getLogger(__name__)
;; _DEFAULT_URL = (
;;     os.environ.get("COMFY_POD_URL")
;;     or os.environ.get("COMFYUI_POD_URL")
;;     or os.environ.get("COMFYUI_URL")
;;     or "http://192.168.1.70:8188"
;; ).rstrip("/")
(def log nil) ;; TODO: port-failed const

(def _state-keys
  {:input {:workflow nil :comfy-url nil :client-id nil :timeout-seconds nil :poll-interval-ms nil}
   :submit-output {:prompt-id nil :number nil :submit-response nil :started-at-ms nil}
   :poll-output {:status nil :images nil :raw-history nil :elapsed-ms nil :error nil}})

(defn base-url [state]
  (let [default-url "/runs"]
    ((or (get state "comfy_url") default-url)
     (clojure.string/rstrip (str "/" (or (get state "comfy_url") default-url))))))

;; TODO: port-failed unit _submit (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp39qqoxsf/scratch.clj:4:15: w)
;; async def _submit(state: _State) -> dict[str, Any]:
;;     wf = state.get("workflow")
;;     if not wf or not isinstance(wf, dict):
;;         return {"status": "error", "error": "workflow (object) required"}
;; 
;;     base = _base_url(state)
;;     body: dict[str, Any] = {"prompt": wf}
;;     if state.get("client_id"):
;;         body["client_id"] = state["client_id"]
;; 
;;     started_ms = int(time.time() * 1000)
;;     try:
;;         async with httpx.AsyncClient(timeout=30.0) as client:
;;             r = await client.post(f"{base}/prompt", json=body,
;;                                   headers={"user-agent": "studio-comfy-run/0.1"})
;;     except Exception as exc:  # noqa: BLE001
;;         return {"status": "error", "error": f"POST /prompt failed: {exc}",
;;                 "started_at_ms": started_ms}
;; 
;;     if r.status_code != 200:
;;         return {"status": "error",
;;                 "error": f"/prompt HTTP {r.status_code}: {r.text[:300]}",
;;                 "started_at_ms": started_ms}
;; 
;;     j = r.json() or {}
;;     pid = j.get("prompt_id")
;;     if not pid:
;;         return {"status": "error",
;;                 "error": f"/prompt missing prompt_id: {j}",
;;                 "started_at_ms": started_ms}
;; 
;;     return {
;;         "prompt_id": pid,
;;         "number": int(j.get("number") or 0),
;;         "submit_response": j,
;;         "started_at_ms": started_ms,
;;     }
(defn submit [& _]
  (throw (ex-info "TODO: port-failed" {:from "_submit"})))

;; TODO: port-failed unit _poll (simeon: timed out)
;; async def _poll(state: _State) -> dict[str, Any]:
;;     if state.get("status") == "error":
;;         return {
;;             "status": "error",
;;             "elapsed_ms": int(time.time() * 1000) - int(state.get("started_at_ms") or 0),
;;         }
;; 
;;     base = _base_url(state)
;;     pid = state.get("prompt_id") or ""
;;     if not pid:
;;         return {"status": "error", "error": "no prompt_id"}
;; 
;;     timeout_s = max(10, min(900, int(state.get("timeout_seconds") or 300)))
;;     interval_ms = max(250, min(10000, int(state.get("poll_interval_ms") or 1500)))
;;     deadline = time.monotonic() + timeout_s
;;     headers = {"user-agent": "studio-comfy-run/0.1"}
;;     images: list[dict[str, Any]] = []
;;     last_history: dict[str, Any] = {}
;; 
;;     async with httpx.AsyncClient(timeout=30.0) as client:
;;         while time.monotonic() < deadline:
;;             try:
;;                 hr = await client.get(f"{base}/history/{pid}", headers=headers)
;;             except Exception as exc:  # noqa: BLE001
;;                 _log.warning("history poll failed (retrying): %s", exc)
;;                 await asyncio.sleep(interval_ms / 1000.0)
;;                 continue
;;             if hr.status_code != 200:
;;                 await asyncio.sleep(interval_ms / 1000.0)
;;                 continue
;; 
;;             entry = (hr.json() or {}).get(pid)
;;             if not entry:
;;                 await asyncio.sleep(interval_ms / 1000.0)
;;                 continue
;;             last_history = entry
;; 
;;             status = (entry.get("status") or {})
;;             messages = status.get("messages") or []
;;             for m in messages:
;;                 if isinstance(m, list) and len(m) >= 2 and m[0] in (
;;                     "execution_error", "execution_interrupted",
;;                 ):
;;                     return {
;;                         "status": "error",
;;                         "error": f"{m[0]}: {str(m[1])[:400]}",
;;                         "raw_history": entry,
;;                         "elapsed_ms": int(time.time() * 1000) - int(state.get("started_at_ms") or 0),
;;                     }
;; 
;;             outputs = entry.get("outputs") or {}
;;             if not outputs:
;;                 await asyncio.sleep(interval_ms / 1000.0)
;;                 continue
;; 
;;             # Fetch every image artifact from every node that produced one.
;;             for node_id, node_out in outputs.items():
;;                 for img in (node_out.get("images") or []):
;;                     params = {
;;                         "filename": img.get("filename", ""),
;;                         "subfolder": img.get("subfolder", ""),
;;                         "type": img.get("type", "output"),
;;                     }
;;                     try:
;;                         vr = await client.get(f"{base}/view", headers=headers, params=params)
;;                     except Exception as exc:  # noqa: BLE001
;;                         return {
;;                             "status": "error",
;;                             "error": f"/view fetch failed: {exc}",
;;                             "raw_history": entry,
;;                             "elapsed_ms": int(time.time() * 1000) - int(state.get("started_at_ms") or 0),
;;                         }
;;                     if vr.status_code != 200:
;;                         continue
;;                     body = vr.content or b""
;;                     images.append({
;;                         "node": str(node_id),
;;                         "filename": params["filename"],
;;                         "type": params["type"],
;;                         "subfolder": params["subfolder"],
;;                         "imageInlineB64": base64.b64encode(body).decode("ascii"),
;;                         "imageMime": vr.headers.get("content-type", "image/png"),
;;                         "byteLen": len(body),
;;                     })
;;             return {
;;                 "status": "ok",
;;                 "images": images,
;;                 "raw_history": entry,
;;                 "elapsed_ms": int(time.time() * 1000) - int(state.get("started_at_ms") or 0),
;;             }
;; 
;;     return {
;;         "status": "timeout",
;;         "error": f"poll deadline {timeout_s}s exceeded",
;;         "raw_history": last_history,
;;         "elapsed_ms": int(time.time() * 1000) - int(state.get("started_at_ms") or 0),
;;     }
(defn poll [& _]
  (throw (ex-info "TODO: port-failed" {:from "_poll"})))

;; TODO: port-failed unit _build (assembled-lint error)
;; def _build() -> StateGraph:
;;     g: StateGraph = StateGraph(_State)
;;     g.add_node("submit", _submit, retry_policy=RetryPolicy(max_attempts=2))
;;     g.add_node("poll",   _poll)
;;     g.add_edge(START, "submit")
;;     g.add_edge("submit", "poll")
;;     g.add_edge("poll", END)
;;     return g
(defn build [& _]
  (throw (ex-info "TODO: port-failed" {:from "_build"})))

;; TODO: port-failed unit GRAPH (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp9mt099el/scratch.clj:2:13: e)
;; GRAPH = _build().compile(name="comfy_run")
(def graph nil) ;; TODO: port-failed const

