(ns lg-chat.graphs.agent-chat
  "lg-chat `agent_chat` graph — general-purpose assistant (langgraph-clj port).

  Faithful port of lg_chat/graphs/agent_chat.py (ADR-2606280030). Same ReAct
  tool-calling loop, same topology, against the same Murakumo/keiei-litellm
  OpenAI-compatible endpoint (httpx → babashka.http-client, json → cheshire).

  State machine (langgraph-clj StateGraph):
    START → :prepare → :llm → route → (:execute-tools → :llm)* → END

  Input  (keyword keys): {:message :history :conv-id :owner-did}
  Output (keyword keys): {:reply :tool-results :error}

  The recursion is bounded two ways, exactly like the Python: an :iteration
  counter capped at CHAT_MAX_ITERATIONS in the router, plus the compiled
  graph's :recursion-limit safety net."
  (:require [langgraph.graph :as g]
            [babashka.http-client :as http]
            [cheshire.core :as json]
            [clojure.string :as str]
            [lg-chat.tools :as tools]))

(defn- env [k d] (or (System/getenv k) d))

(def ^:private VLLM-URL
  (str/replace (env "VLLM_URL" "http://keiei-litellm.keiei-llm.svc.cluster.local:4000/v1")
               #"/+$" ""))
(def ^:private VLLM-MODEL   (env "MURAKUMO_DEFAULT_MODEL" "gemma-4-E4B-it"))
(def ^:private VLLM-API-KEY (env "LLM_API_KEY" "dummy"))
(def ^:private VLLM-TIMEOUT (long (* 1000 (Double/parseDouble (env "VLLM_TIMEOUT_SEC" "60")))))
(def ^:private MAX-ITERATIONS (Long/parseLong (env "CHAT_MAX_ITERATIONS" "8")))
(def ^:private MAX-HISTORY (Long/parseLong (env "CHAT_MAX_HISTORY" "20")))

(def ^:private SYSTEM-PROMPT
  (str "You are Gftd Chat, a helpful AI assistant on gftd.ai. "
       "You have access to tools for code execution, web search, file saving, "
       "image generation, conversation search, and report scheduling. "
       "Use tools when they would genuinely help the user. "
       "Reply in the user's language. Be concise and accurate."))

(defn- truncate [s n] (subs s 0 (min n (count s))))

;; ── nodes ──────────────────────────────────────────────────────────────
(defn node-prepare [state]
  (let [history (take-last MAX-HISTORY (or (:history state) []))
        hist-msgs (->> history
                       (filter #(and (map? %)
                                     (#{"user" "assistant" "tool"} (or (:role %) (get % "role")))))
                       (map (fn [h]
                              {:role (or (:role h) (get h "role"))
                               :content (truncate (str (or (:content h) (get h "content") "")) 4000)})))
        user-text (str/trim (str (or (:message state) "")))
        msgs (cond-> (into [{:role "system" :content SYSTEM-PROMPT}] hist-msgs)
               (not (str/blank? user-text)) (conj {:role "user" :content user-text}))]
    {:messages msgs :iteration 0 :tool-results []}))

(defn- strip-think [s]
  (str/trim (str/replace (or s "") #"(?s)<think>.*?</think>" "")))

(defn node-llm [state]
  (if (:error state)
    {}
    (let [msgs (or (:messages state) [])
          payload {:model VLLM-MODEL :messages msgs :tools tools/TOOL-SCHEMAS
                   :tool_choice "auto" :max_tokens 2048 :temperature 0.4}
          resp (try
                 (let [r (http/post (str VLLM-URL "/chat/completions")
                                    {:headers {"Authorization" (str "Bearer " VLLM-API-KEY)
                                               "Content-Type" "application/json"}
                                     :body (json/generate-string payload)
                                     :timeout VLLM-TIMEOUT
                                     :throw false})]
                   (if (>= (:status r) 400)
                     {::error (str "vllm http " (:status r) ": " (truncate (str (:body r)) 300))}
                     (json/parse-string (:body r) true)))
                 (catch Exception exc
                   {::error (truncate (str "vllm: " (.. exc getClass getSimpleName) ": " (.getMessage exc)) 200)}))]
      (if (::error resp)
        {:error (::error resp)}
        (let [choice (first (or (:choices resp) [{}]))
              msg (or (:message choice) {})
              tool-calls (or (:tool_calls msg) [])
              updated (conj (vec msgs) msg)]
          (if (empty? tool-calls)
            {:messages updated :reply (strip-think (str (or (:content msg) "")))}
            {:messages updated :iteration (inc (or (:iteration state) 0))}))))))

(defn node-execute-tools [state]
  (let [msgs (vec (or (:messages state) []))
        last-msg (or (peek msgs) {})
        tool-calls (or (:tool_calls last-msg) [])]
    (if (empty? tool-calls)
      {}
      (let [conv-id (or (:conv-id state) "")
            owner-did (or (:owner-did state) "")
            msg-id (str "tc-" (System/currentTimeMillis))]
        (reduce
         (fn [acc tc]
           (let [fnm (or (:function tc) {})
                 nm (str (or (:name fnm) ""))
                 args (try (json/parse-string (or (:arguments fnm) "{}")) (catch Exception _ {}))
                 result (tools/dispatch-tool nm args :conv-id conv-id :msg-id msg-id :owner-did owner-did)]
             (-> acc
                 (update :tool-results conj {:name nm :args args :result result})
                 (update :messages conj {:role "tool"
                                         :tool_call_id (or (:id tc) (str "tc-" nm))
                                         :content (truncate (json/generate-string result) 4000)}))))
         {:messages msgs :tool-results (vec (or (:tool-results state) []))}
         tool-calls)))))

(defn route-after-llm [state]
  (let [msgs (or (:messages state) [])
        last-msg (or (peek (vec msgs)) {})]
    (cond
      (:error state) g/END
      (some? (:reply state)) g/END
      (>= (or (:iteration state) 0) MAX-ITERATIONS) g/END
      (seq (:tool_calls last-msg)) :execute-tools
      :else g/END)))

;; ── graph ──────────────────────────────────────────────────────────────
(defn build
  "Compile the agent_chat StateGraph. opts pass through to compile-graph
  (e.g. {:recursion-limit n :interrupt-before #{..}})."
  ([] (build {:recursion-limit (* 4 MAX-ITERATIONS)}))
  ([opts]
   (-> (g/state-graph)
       (g/add-node :prepare node-prepare)
       (g/add-node :llm node-llm)
       (g/add-node :execute-tools node-execute-tools)
       (g/add-edge :prepare :llm)
       (g/add-conditional-edges :llm route-after-llm
                                {:execute-tools :execute-tools g/END g/END})
       (g/add-edge :execute-tools :llm)
       (g/set-entry-point :prepare)
       (g/compile-graph opts))))

(def GRAPH (build))
