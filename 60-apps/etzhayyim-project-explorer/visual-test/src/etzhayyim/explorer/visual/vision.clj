(ns etzhayyim.explorer.visual.vision
  "Local Ollama vision judge for the visual react loop (ADR-2606201610).

   Talks to the OpenAI-compatible Ollama endpoint (the same backend
   computer-use-clj's jvm_host uses: default gemma-4-E4B QAT, tools+vision
   capable). Takes the Anthropic image block that `computeruse.macos`'
   `-screenshot` returns ([{:type \"image\" :source {:type \"base64\" ...}}]),
   converts it to an OpenAI `image_url` data URI, and asks the model to judge a
   visual criterion — returning a parsed {:pass :saw} verdict.

   I/O is java.net.http + clojure.data.json only (no extra deps), mirroring the
   library's host-injection style."
  (:require [clojure.data.json :as json]
            [clojure.string :as str])
  (:import [java.net URI]
           [java.net.http HttpClient HttpRequest HttpRequest$BodyPublishers
            HttpResponse$BodyHandlers]
           [java.time Duration]))

(def default-url
  (or (System/getenv "OLLAMA_URL") "http://localhost:11434/v1/chat/completions"))
(def default-model
  (or (System/getenv "OLLAMA_MODEL")
      "hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL"))

(def ^:private client
  (delay (-> (HttpClient/newBuilder) (.connectTimeout (Duration/ofSeconds 10)) .build)))

(defn- post [url body]
  (let [req (-> (HttpRequest/newBuilder (URI/create url))
                (.timeout (Duration/ofSeconds 180))
                (.header "Content-Type" "application/json")
                (.POST (HttpRequest$BodyPublishers/ofString body))
                .build)
        resp (.send @client req (HttpResponse$BodyHandlers/ofString))]
    {:status (.statusCode resp) :body (.body resp)}))

(defn- image-block->data-uri
  "computeruse image block → OpenAI image_url data URI string."
  [block]
  (let [src (:source block)
        media (or (:media_type src) "image/png")
        data (:data src)]
    (str "data:" media ";base64," data)))

(defn- extract-json
  "Pull the first {...} object out of an LLM reply (it may wrap JSON in prose or
   a ```json fence). Returns a clj map or nil."
  [text]
  (let [t (-> text (str/replace #"(?s)```json" "") (str/replace #"```" ""))
        m (re-find #"(?s)\{.*\}" t)]
    (when m
      (try (json/read-str m :key-fn keyword) (catch Exception _ nil)))))

(defn judge
  "Ask the vision model whether `criterion` holds in `image-blocks` (the value
   returned by IComputer -screenshot). Returns
     {:pass bool :saw \"…\" :raw \"…\" :ok bool}
   :ok=false means the call/parse failed (treated as inconclusive by the loop)."
  [{:keys [url model] :or {url default-url model default-model}} image-blocks criterion]
  (let [data-uris (->> image-blocks
                       (filter #(= "image" (:type %)))
                       (map image-block->data-uri))
        content (into [{:type "text"
                        :text (str "You are a strict UI visual tester. Look at the "
                                   "screenshot and decide whether this is TRUE:\n\n  "
                                   criterion
                                   "\n\nReply with ONLY a JSON object: "
                                   "{\"pass\": true|false, \"saw\": \"<one short sentence of what you see>\"}.")}]
                      (map (fn [u] {:type "image_url" :image_url {:url u}}) data-uris))
        body (json/write-str
              {:model model
               :temperature 0
               :messages [{:role "user" :content content}]})
        {:keys [status body]} (post url body)]
    (if (not= 200 status)
      {:ok false :pass false :saw (str "HTTP " status) :raw body}
      (let [reply (-> (json/read-str body :key-fn keyword)
                      :choices first :message :content (or ""))
            parsed (extract-json reply)]
        (if parsed
          {:ok true :pass (boolean (:pass parsed)) :saw (str (:saw parsed)) :raw reply}
          {:ok false :pass false :saw "unparseable verdict" :raw reply})))))

(defn- get* [url]
  (let [req (-> (HttpRequest/newBuilder (URI/create url))
                (.timeout (Duration/ofSeconds 5)) (.GET) .build)]
    (.send @client req (HttpResponse$BodyHandlers/ofString))))

(defn alive?
  "Cheap reachability probe for the Ollama endpoint (GET /api/tags)."
  [{:keys [url] :or {url default-url}}]
  (try
    (let [base (str/replace url #"/v1/chat/completions$" "/api/tags")]
      (= 200 (.statusCode (get* base))))
    (catch Exception _ false)))
