;; ported from 60-apps/etzhayyim-project-6ir/.../routes/xrpc/[...path]/+server.ts — gold reference (Fable)
;; XRPC edge BFF — nsid を受けて MCP router へ tools/call として proxy する。
;; SvelteKit の RequestHandler は Clojure では ring 風ハンドラ (request-map → response-map)。
;; fetch / uuid は host capability 注入 (副作用を境界へ押し出す)。
(ns sixir.xrpc-server
  (:require [clojure.string :as str]))

(def default-mcp-router-url "https://mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message")

(defn mcp-router-url
  "env から router URL を解決する (AGENTGATEWAY_… > MCP_ROUTER_URL > default)。末尾 / は除去。"
  [env]
  (let [pick (fn [k] (let [v (get env k)] (when (and (string? v) (seq (str/trim v))) v)))
        configured (or (pick "AGENTGATEWAY_MCP_ROUTER_URL")
                       (pick "MCP_ROUTER_URL")
                       default-mcp-router-url)]
    (str/replace configured #"/+$" "")))

(defn- no-store
  "cache-control: no-store を付けた response map。"
  ([body] (no-store body 200))
  ([body status]
   {:status status
    :headers {"cache-control" "no-store" "content-type" "application/json"}
    :body body}))

(defn- jsonrpc-envelope [nsid input request-id]
  {:jsonrpc "2.0" :id request-id :method "tools/call"
   :params {:name nsid :arguments input}})

(defn- unwrap
  "MCP router の応答から structuredContent (なければ result, なければ payload) を取り出す。"
  [payload]
  (let [result (if (and (map? payload) (contains? payload :result))
                 (:result payload) payload)]
    (if (and (map? result) (contains? result :structuredContent))
      (:structuredContent result) result)))

(defn handle-post
  "XRPC POST ハンドラ。caps = {:fetch (fn [url req]→{:ok :status :body}) :uuid (fn []→str)}。
  request = {:params {:path nsid} :body input :env env}。"
  [caps {:keys [params body env]}]
  (let [nsid (:path params)]
    (if (str/blank? (str nsid))
      (no-store {:error "Missing XRPC method"} 400)
      (let [{:keys [fetch uuid]} caps
            envelope (jsonrpc-envelope nsid (or body {}) (uuid))
            up (fetch (mcp-router-url env)
                      {:method :post
                       :headers {"content-type" "application/json"
                                 "x-etzhayyim-bff" "ring-edge-bff"
                                 "x-etzhayyim-xrpc-method" nsid}
                       :body envelope})
            payload (:body up)]
        (cond
          (not (:ok up))
          (no-store {:error "MCP router request failed" :upstream payload} (:status up))
          (and (map? payload) (contains? payload :error))
          (no-store {:error (get-in payload [:error :message] "MCP router returned an error")
                     :upstream payload} 502)
          :else
          (no-store (or (unwrap payload) {})))))))
