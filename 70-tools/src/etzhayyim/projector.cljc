;; etzhayyim.projector — JSON-RPC 2.0 MCP projector subcommands (cljc port).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/projector.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     build-mcp-headers   — build Content-Type + optional Bearer header
;;     build-mcp-request   — assemble JSON-RPC 2.0 payload map
;;     build-create-args   — assemble projector.create_project args map
;;     build-update-args   — assemble projector.update_status args map
;;     build-list-args     — assemble projector.list_projects args map
;;     build-blocker-add-args    — assemble projector.add_blocker args map
;;     build-blocker-resolve-args — assemble projector.resolve_blocker args map
;;     unwrap-mcp-response — extract content[0].text → parse JSON, else return result
;;     check-mcp-error     — detect "error" key and throw ex-info
;;
;;   IO (HTTP-shaping verified via injectable :http-fn, no live calls):
;;     mcp-call            — POST JSON-RPC 2.0 to {pds}/mcp, unwrap content[0].text
;;
;; INJECTABLE HTTP CLIENT:
;;   mcp-call accepts an optional :http-fn in opts.
;;   Default = real babashka.http-client; tests inject a fake that records calls
;;   WITHOUT touching the network.
;;
;; SECURITY:
;;   No secrets at load time.  etzhayyim_AGENT_TOKEN read lazily.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.projector)(println :ok)"

(ns etzhayyim.projector
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Constants
;; ---------------------------------------------------------------------------

(def ^:private mcp-method  "tools/call")
(def ^:private jsonrpc-ver "2.0")
(def ^:private req-id      1)

;; ---------------------------------------------------------------------------
;; Pure: header + request construction
;; ---------------------------------------------------------------------------

(defn agent-token
  "Lazy read of etzhayyim_AGENT_TOKEN — called only when making live requests."
  []
  (System/getenv "etzhayyim_AGENT_TOKEN"))

(defn build-mcp-headers
  "Build Content-Type + optional Bearer Authorization header.
  Pure: accepts token directly so tests can inject without env."
  [token]
  (cond-> {"Content-Type" "application/json"}
    (and token (seq token)) (assoc "Authorization" (str "Bearer " token))))

(defn build-mcp-request
  "Assemble a JSON-RPC 2.0 tools/call payload map.
  Pure: tool-name is a string, arguments is a map."
  [tool-name arguments]
  {:jsonrpc jsonrpc-ver
   :id      req-id
   :method  mcp-method
   :params  {:name tool-name :arguments arguments}})

(defn unwrap-mcp-response
  "Extract result from a JSON-RPC 2.0 response map.
  If content[0].text is present, parse it as JSON (fall-back to {:text text}).
  Pure: operates on an already-parsed response map."
  [data]
  (let [result  (get data "result" {})
        content (get result "content" [])]
    (if (and (seq content) (map? (first content)))
      (let [text (get (first content) "text" "")]
        (try
          (json/parse-string text)
          (catch Exception _
            {"text" text})))
      result)))

(defn check-mcp-error
  "Throw ex-info if the response contains a JSON-RPC error.
  Pure: operates on an already-parsed response map."
  [data]
  (when-let [err (get data "error")]
    (throw (ex-info (str "MCP error " (get err "code") ": " (get err "message"))
                    {:mcp-error err})))
  data)

;; ---------------------------------------------------------------------------
;; Pure: command-specific argument builders
;; ---------------------------------------------------------------------------

(defn build-create-args
  "Build projector.create_project arguments map.
  All optional keys excluded when nil/empty."
  [{:keys [name org-id description parent-id target-date]}]
  (cond-> {"name" name}
    (and org-id     (seq org-id))     (assoc "orgId"       org-id)
    (and description (seq description)) (assoc "description" description)
    (and parent-id  (seq parent-id))  (assoc "parentId"    parent-id)
    (and target-date (seq target-date)) (assoc "targetDate"  target-date)))

(defn build-status-args
  "Build projector.get_status arguments map."
  [project-id summarize]
  {"projectId" project-id "summarize" (boolean summarize)})

(defn build-update-args
  "Build projector.update_status arguments map."
  [{:keys [project-id progress state target-date]}]
  (cond-> {"projectId" project-id}
    (some? progress)                 (assoc "progressPermille" progress)
    (and state (seq state))          (assoc "lifecycleState"   state)
    (and target-date (seq target-date)) (assoc "targetDate"    target-date)))

(defn build-list-args
  "Build projector.list_projects arguments map."
  [{:keys [org-id state limit]}]
  (cond-> {"limit" (or limit 20)}
    (and org-id (seq org-id)) (assoc "orgId"          org-id)
    (and state  (seq state))  (assoc "lifecycleState" state)))

(defn build-blocker-add-args
  "Build projector.add_blocker arguments map."
  [{:keys [project-id title blocker-type severity description]}]
  (cond-> {"projectId"   project-id
           "title"       title
           "blockerType" (or blocker-type "technical")
           "severity"    (or severity     "medium")}
    (and description (seq description)) (assoc "description" description)))

(defn build-blocker-resolve-args
  "Build projector.resolve_blocker arguments map."
  [{:keys [blocker-id resolution]}]
  (cond-> {"blockerId" blocker-id}
    (and resolution (seq resolution)) (assoc "resolution" resolution)))

;; ---------------------------------------------------------------------------
;; IO: mcp-call — POST to {pds}/mcp
;; ---------------------------------------------------------------------------

(defn mcp-call
  "POST JSON-RPC 2.0 tools/call to {pds}/mcp and return the parsed result dict.
  opts:
    :pds     — PDS base URL (required)
    :token   — Bearer token (optional; falls back to etzhayyim_AGENT_TOKEN env var)
    :http-fn — injectable HTTP fn (default real babashka.http-client/post)
    :dry-run — if truthy, return {:dry-run true :request req} without calling"
  [tool-name arguments opts]
  (let [pds      (or (:pds opts) (System/getenv "etzhayyim_PDS_URL") "https://etzhayyim.com")
        token    (or (:token opts) (agent-token))
        url      (str (str/replace pds #"/$" "") "/mcp")
        req-body (build-mcp-request tool-name arguments)
        headers  (build-mcp-headers token)
        http-fn  (or (:http-fn opts)
                     #?(:bb (fn [u h b] (http/post u {:headers h :body (json/generate-string b)}))
                        :default nil))]
    (when (not http-fn)
      (throw (ex-info "http-fn required (not in bb environment)" {})))
    (if (:dry-run opts)
      {:dry-run true :url url :headers headers :request req-body}
      (let [resp (http-fn url headers req-body)
            body (json/parse-string (:body resp))]
        (check-mcp-error body)
        (unwrap-mcp-response body)))))
