;; ported from 10-protocol/signal/src/transport.ts — gold reference (Fable)
;; @etzhayyim/signal の transport 注入。XRPC dispatcher を呼び出し側が配線する。
;; TS のモジュールスコープ可変スロット + throw は Clojure では atom + ex-info。
;; Signal identity は per-user (ブラウザセッションに1つ) なので単一スロットは意図的。
(ns signal.transport)

;; SignalTransport shape:
;;   {:procedure (fn [nsid body] → result)   ; AT Protocol XRPC procedure (POST)
;;    :query     (fn [nsid params] → result)} ; AT Protocol XRPC query (GET)

(defonce ^:private transport (atom nil))

(defn set-signal-transport!
  "transport を設定する。nil でリセット (テスト用)。"
  [t]
  (reset! transport t))

(defn get-signal-transport
  "設定済み transport を返す。未設定なら例外。"
  []
  (or @transport
      (throw (ex-info "@etzhayyim/signal: transport not configured. Call set-signal-transport! at startup."
                      {:type :transport-unconfigured}))))

(defn atp-agent-transport
  "@atproto/api AtpAgent 用アダプタ。get-agent は agent を返す関数 (遅延束縛/再ログイン対応)。
  agent は {:call (fn [nsid params body] → {:data …})}。"
  [get-agent]
  {:procedure (fn [nsid body]
                (:data ((:call (get-agent)) nsid nil body)))
   :query (fn [nsid params]
            (:data ((:call (get-agent)) nsid params nil)))})
