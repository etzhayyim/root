(ns etzhayyim.murakumo
  "kotoba-genome — the shared Murakumo inference helper (ADR-2605215000: the fleet
  ONLY). Round-robins the tribe-named Mac minis over Tailscale, runs gemma4 with
  think:false, and returns the text — or nil (the caller fails open to a template,
  ibuki G6). Read-only inference, nothing signed (no-server-key). Extracted so the
  organism narrate AND actor/converse share one fleet path (the kotoba-lang
  behavior-lib, ADR-2606302205 D3). bb-only (babashka.http-client/process)."
  (:require [clojure.string :as str]
            [cheshire.core :as json]
            [babashka.process :as p]
            [babashka.http-client :as http]))

(def ^:private fleet
  ["asher" "benjamin" "dan" "issachar" "joseph"
   "judah" "levi" "naphtali" "simeon" "zebulun"])
(def ^:private model "gemma4:e4b-it-qat")
(def ^:private fallback-model "gemma4:e4b")
(def ^:private ollama-port 11434)

;; Murakumo-only allowlist (ibuki G6): the resolved fleet host, nothing else.
(defn murakumo-host? [h] (boolean (some #{h} fleet)))

(defn- tailscale-ip [host]
  (try (let [out (-> (p/sh "tailscale" "ip" "-4" host) :out str/trim)]
         (when (seq out) (first (str/split-lines out))))
       (catch Exception _ nil)))

(defn- node-models [ip]
  (try (let [r (http/get (format "http://%s:%d/api/tags" ip ollama-port) {:timeout 2000})]
         (when (= 200 (:status r))
           (set (map #(get % "name") (get (json/parse-string (:body r)) "models")))))
       (catch Exception _ nil)))

(defn pick-node
  "First healthy fleet node serving our model, or nil (fleet unreachable → template)."
  []
  (loop [k 0]
    (if (>= k (count fleet))
      nil
      (let [host (nth fleet k)
            ip (tailscale-ip host)
            models (when ip (node-models ip))
            m (cond (nil? models) nil (models model) model
                    (models fallback-model) fallback-model :else nil)]
        (if (and m (murakumo-host? host)) {:host host :ip ip :model m} (recur (inc k)))))))

(defn infer-text
  "Run one chat completion on the fleet for `messages` (a vector of {:role :content}).
  Returns the trimmed one-line text, or nil on any failure / unreachable fleet
  (the caller uses its template). think:false; Murakumo-only; read-only."
  ([messages] (infer-text messages (pick-node)))
  ([messages node]
   (when node
     (try
       (let [body (json/generate-string
                   {:model (:model node) :think false :messages messages :stream false
                    :options {:temperature 0.6 :num_predict 160}})
             r (http/post (format "http://%s:%d/api/chat" (:ip node) ollama-port)
                          {:headers {"Content-Type" "application/json"} :body body :timeout 30000})
             txt (-> (json/parse-string (:body r)) (get-in ["message" "content"]) (or "")
                     str/trim (str/replace #"^[*「\s]+|[*」\s]+$" ""))]
         (when (seq txt) txt))
       (catch Exception _ nil)))))
