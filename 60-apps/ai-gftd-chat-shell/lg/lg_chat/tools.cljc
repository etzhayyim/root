(ns lg-chat.tools
  "6 tool implementations for the lg-chat agent-chat graph (clj port).

  Faithful port of lg_chat/tools.py (ADR-2606280030). TOOL-SCHEMAS is the
  byte-equivalent OpenAI-style tool list; `dispatch-tool` routes by name.

  Port fidelity per tool:
    code_exec      — FULL: babashka.process subprocess (python3 -I, hardened env,
                     deref-timeout). httpx not involved.
    image_gen      — FULL: babashka.http-client to ComfyUI /prompt + /history poll.
    web_search     — Brave via babashka.http-client; the RisingWave ILIKE FALLBACK
                     is NOT ported (no psycopg under bb) → degrades like the
                     no-provider path. (deviation, noted)
    schedule_report— FULL: babashka.http-client POST + HMAC-SHA256 x-internal-trust.
    file_save      — B2 S3 PUT requires SigV4; NOT ported (no aws sdk under bb) →
                     returns the same disabled shape. (deviation, noted)
    rag_search     — RisingWave/psycopg NOT ported → returns the same RW-absent
                     disabled shape. (deviation, noted)

  Tool results are clj maps with keyword keys; cheshire stringifies them when the
  graph encodes a tool message — same wire JSON as the Python string-keyed dicts."
  (:require [babashka.process :as p]
            [babashka.fs :as fs]
            [babashka.http-client :as http]
            [cheshire.core :as json]
            [clojure.string :as str])
  (:import [javax.crypto Mac]
           [javax.crypto.spec SecretKeySpec]))

;; ── env ────────────────────────────────────────────────────────────────
(def DEFAULT-CONFIG
  {:comfyui-url "" :rw-url "" :web-search-provider "brave" :web-search-key ""
   :b2-access-key "" :b2-secret-key "" :dispatcher-url "" :internal-secret ""})

(defn- config [host-config] (merge DEFAULT-CONFIG (or host-config {})))

(def TOOL-SCHEMAS
  [{:type "function"
    :function
    {:name "code_exec"
     :description (str "Execute Python 3 code in an isolated subprocess. "
                       "Returns stdout, stderr, and exit code. "
                       "No network access; timeout 30 s.")
     :parameters {:type "object"
                  :required ["code"]
                  :properties {:code {:type "string"}
                               :timeoutSec {:type "integer" :default 15 :maximum 30}}}}}
   {:type "function"
    :function
    {:name "image_gen"
     :description (str "Generate an image with ComfyUI (SDXL). "
                       "Returns a CDN URL when successful. "
                       "Disabled when no ComfyUI endpoint is configured.")
     :parameters {:type "object"
                  :required ["prompt"]
                  :properties {:prompt {:type "string" :maxLength 2000}
                               :negativePrompt {:type "string"}
                               :width {:type "integer" :default 1024}
                               :height {:type "integer" :default 1024}
                               :steps {:type "integer" :default 4}
                               :seed {:type "integer"}}}}}
   {:type "function"
    :function
    {:name "file_save"
     :description (str "Save text or binary content to B2 storage. "
                       "Returns a download URL. "
                       "Disabled when B2 credentials are absent.")
     :parameters {:type "object"
                  :required ["filename" "content"]
                  :properties {:filename {:type "string" :maxLength 256}
                               :content {:type "string"}
                               :encoding {:type "string" :enum ["utf-8" "base64"] :default "utf-8"}
                               :mimeType {:type "string" :default "text/plain"}
                               :title {:type "string"}}}}}
   {:type "function"
    :function
    {:name "rag_search"
     :description (str "Search previous conversation history stored in RisingWave. "
                       "Returns matching message snippets. "
                       "Falls back gracefully if RW is unavailable.")
     :parameters {:type "object"
                  :required ["query"]
                  :properties {:query {:type "string" :maxLength 500}
                               :topK {:type "integer" :default 6 :maximum 20}
                               :convId {:type "string"}}}}}
   {:type "function"
    :function
    {:name "web_search"
     :description (str "Search the public web via Brave Search. "
                       "Returns {title, url, snippet} hits. "
                       "Falls back to RisingWave vector search when no API key is set.")
     :parameters {:type "object"
                  :required ["query"]
                  :properties {:query {:type "string" :maxLength 500}
                               :topK {:type "integer" :default 6 :maximum 20}
                               :lang {:type "string" :default "ja"}}}}}
   {:type "function"
    :function
    {:name "schedule_report"
     :description (str "Schedule a deep-research report. "
                       "Returns immediately with a runId; the result will be posted back "
                       "to this conversation when the report is ready. "
                       "Requires BPMN dispatcher to be configured.")
     :parameters {:type "object"
                  :required ["title" "prompt"]
                  :properties {:title {:type "string" :maxLength 256}
                               :prompt {:type "string" :maxLength 4000}
                               :deliverChannel {:type "string"
                                                :enum ["chat" "email" "pds-record"]
                                                :default "chat"}
                               :deliverAt {:type "string" :format "datetime"}}}}}])

(defn- now-ms [] (System/currentTimeMillis))
(defn- ->int [v d] (try (long (Double/parseDouble (str v))) (catch Exception _ d)))
(defn- clamp [v lo hi] (max lo (min v hi)))

;; ── tool: code_exec ────────────────────────────────────────────────────
(defn tool-code-exec [args]
  (let [code (str (or (get args "code") (:code args) ""))
        timeout-sec (min (->int (or (get args "timeoutSec") (:timeoutSec args) 15) 15) 30)]
    (if (str/blank? code)
      {:ok false :error "code is required"}
      (let [started (now-ms)
            td (str (fs/create-temp-dir {:prefix "lg-chat-exec-"}))
            script (str (fs/file td "exec.py"))]
        (try
          (spit script code)
          (let [proc (p/process ["python3" "-I" script]
                                {:out :string :err :string :dir td
                                 :env {"PATH" "/usr/local/bin:/usr/bin:/bin"
                                       "HOME" td "TMPDIR" td}})
                res (deref proc (* timeout-sec 1000) ::timeout)]
            (if (= res ::timeout)
              (do (p/destroy-tree proc)
                  {:ok false :error (str "timeout after " timeout-sec "s")})
              {:ok (zero? (:exit res))
               :stdout (subs (or (:out res) "") 0 (min 8000 (count (or (:out res) ""))))
               :stderr (subs (or (:err res) "") 0 (min 2000 (count (or (:err res) ""))))
               :exitCode (:exit res)
               :durationMs (- (now-ms) started)}))
          (finally
            (try (fs/delete-tree td) (catch Exception _ nil))))))))

;; ── tool: image_gen ────────────────────────────────────────────────────
(defn tool-image-gen [args & {:keys [conv-id owner-did host-config]}]
  (let [comfyui-url (str/replace (:comfyui-url (config host-config)) #"/+$" "")]
    (if (str/blank? comfyui-url)
    {:ok false :error "image_gen is not available — no ComfyUI endpoint configured (COMFYUI_URL)"}
    (let [prompt (str/trim (str (or (get args "prompt") (:prompt args) "")))
          width  (clamp (->int (or (get args "width") (:width args) 1024) 1024) 256 1536)
          height (clamp (->int (or (get args "height") (:height args) 1024) 1024) 256 1536)
          steps  (clamp (->int (or (get args "steps") (:steps args) 4) 4) 2 30)
          seed   (->int (or (get args "seed") (:seed args) (bit-and (now-ms) 0x7FFFFFFF)) 0)
          neg    (str (or (get args "negativePrompt") (:negativePrompt args) "nsfw, lowres, blurry"))
          ua     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/129.0.0.0"
          headers {"User-Agent" ua "Accept" "application/json" "Content-Type" "application/json"}]
      (if (str/blank? prompt)
        {:ok false :error "prompt is required"}
        (let [workflow
              {:ckpt {:class_type "CheckpointLoaderSimple" :inputs {:ckpt_name "v1-5-pruned-emaonly.safetensors"}}
               :latent {:class_type "EmptyLatentImage" :inputs {:width width :height height :batch_size 1}}
               :pos {:class_type "CLIPTextEncode" :inputs {:text prompt :clip ["ckpt" 1]}}
               :neg {:class_type "CLIPTextEncode" :inputs {:text neg :clip ["ckpt" 1]}}
               :ks {:class_type "KSampler"
                    :inputs {:seed seed :steps steps :cfg 7.0
                             :sampler_name "euler_ancestral" :scheduler "normal" :denoise 1.0
                             :model ["ckpt" 0] :positive ["pos" 0] :negative ["neg" 0]
                             :latent_image ["latent" 0]}}
               :vae {:class_type "VAEDecode" :inputs {:samples ["ks" 0] :vae ["ckpt" 2]}}
               :save {:class_type "SaveImage" :inputs {:filename_prefix "gftd_chat" :images ["vae" 0]}}}
              started (now-ms)
              prompt-id
              (try
                (let [r (http/post (str comfyui-url "/prompt")
                                   {:headers headers
                                    :body (json/generate-string {:prompt workflow})
                                    :timeout 15000})
                      resp (json/parse-string (:body r) true)]
                  (:prompt_id resp))
                (catch Exception exc
                  {::err (str "comfy /prompt: " (.getMessage exc))}))]
          (cond
            (map? prompt-id) {:ok false :error (::err prompt-id)}
            (not prompt-id)  {:ok false :error "comfy no prompt_id"}
            :else
            (let [deadline (+ (now-ms) 120000)
                  entry (loop [delay 1500]
                          (let [rec (try
                                      (let [r2 (http/get (str comfyui-url "/history/" prompt-id)
                                                         {:headers headers :timeout 10000})
                                            hist (json/parse-string (:body r2) true)]
                                        (get hist (keyword prompt-id)))
                                      (catch Exception _ nil))]
                            (cond
                              (get-in rec [:status :completed]) rec
                              (> (now-ms) deadline) nil
                              :else (do (Thread/sleep (long delay))
                                        (recur (long (min (* delay 1.4) 4000)))))))]
              (if-not entry
                {:ok false :error "comfy timeout after 120s" :promptId prompt-id}
                (let [images (->> (vals (:outputs entry))
                                  (filter map?)
                                  (mapcat :images)
                                  (remove nil?))]
                  (if (empty? images)
                    {:ok false :error "comfy returned no images" :promptId prompt-id}
                    (let [img (first images)
                          enc #(java.net.URLEncoder/encode (str %) "UTF-8")
                          qs (str "filename=" (enc (:filename img))
                                  "&subfolder=" (enc (:subfolder img))
                                  "&type=" (enc (or (:type img) "output")))]
                      {:ok true
                       :imageUrl (str comfyui-url "/view?" qs)
                       :width width :height height :seed seed
                       :promptId prompt-id
                       :durationMs (- (now-ms) started)}))))))))))))

;; ── tool: file_save (B2 SigV4 not ported — disabled-shape) ──────────────
(defn tool-file-save [args & {:keys [conv-id owner-did host-config]}]
  (let [{:keys [b2-access-key b2-secret-key]} (config host-config)]
    (if (or (str/blank? b2-access-key) (str/blank? b2-secret-key))
    {:ok false :error "file_save is not available — B2 credentials not configured"}
    {:ok false
     :error "file_save not ported to clj — B2 S3 SigV4 signing unavailable under bb; use the Python tool for B2 uploads"})))

;; ── tool: rag_search (RisingWave/psycopg not ported — disabled-shape) ───
(defn tool-rag-search [args & {:keys [owner-did host-config]}]
  (let [query (str (or (get args "query") (:query args) ""))
        rw-url (:rw-url (config host-config))]
    (cond
      (str/blank? query) {:ok false :error "query is required"}
      (str/blank? rw-url) {:ok false :error "rag_search unavailable — RW_URL not configured" :hits []}
      :else {:ok false
             :error "rag_search not ported to clj — RisingWave/psycopg query unavailable under bb; use the Python tool"
             :hits []})))

;; ── tool: web_search ───────────────────────────────────────────────────
(defn tool-web-search [args & {:keys [host-config]}]
  (let [query (str (or (get args "query") (:query args) ""))
        top-k (min (->int (or (get args "topK") (:topK args) 6) 6) 20)
        {:keys [web-search-key web-search-provider]} (config host-config)]
    (if (str/blank? query)
      {:ok false :error "query is required"}
      (let [brave
            (when (and (not (str/blank? web-search-key)) (= web-search-provider "brave"))
              (try
                (let [url (str "https://api.search.brave.com/res/v1/web/search?q="
                               (java.net.URLEncoder/encode query "UTF-8") "&count=" top-k)
                      r (http/get url {:headers {"Accept" "application/json"
                                                 "X-Subscription-Token" web-search-key}
                                       :timeout 15000})
                      data (json/parse-string (:body r) true)
                      results (take top-k (get-in data [:web :results]))
                      hits (mapv (fn [h] {:title (or (:title h) "")
                                          :url (or (:url h) "")
                                          :snippet (subs (or (:description h) "")
                                                         0 (min 500 (count (or (:description h) ""))))})
                                 results)]
                  {:ok true :query query :hits hits :provider "brave"})
                (catch Exception _ nil)))]
        (or brave
            ;; RisingWave ILIKE fallback not ported (no psycopg under bb).
            {:ok false :error "web_search: no provider available" :hits []})))))

;; ── tool: schedule_report ──────────────────────────────────────────────
(defn- hmac-sha256-hex [secret message]
  (let [mac (Mac/getInstance "HmacSHA256")]
    (.init mac (SecretKeySpec. (.getBytes ^String secret "UTF-8") "HmacSHA256"))
    (->> (.doFinal mac (.getBytes ^String message "UTF-8"))
         (map #(format "%02x" (bit-and % 0xff)))
         (apply str))))

(defn tool-schedule-report [args & {:keys [conv-id msg-id owner-did host-config]}]
  (let [{:keys [dispatcher-url internal-secret]} (config host-config)
        dispatcher-url (str/replace dispatcher-url #"/+$" "")]
    (if (str/blank? dispatcher-url)
    {:ok false :error "schedule_report unavailable — BPMN_DISPATCHER_INTERNAL_URL not configured"}
    (let [title (str/trim (str (or (get args "title") (:title args) "")))
          prompt (str/trim (str (or (get args "prompt") (:prompt args) "")))]
      (if (or (str/blank? title) (str/blank? prompt))
        {:ok false :error "title and prompt are required"}
        (let [body {:convId (or conv-id "") :msgId (or msg-id "") :ownerDid (or owner-did "")
                    :title title :prompt prompt
                    :deliverAt (str (or (get args "deliverAt") (:deliverAt args) ""))
                    :deliverChannel (str (or (get args "deliverChannel") (:deliverChannel args) "chat"))}
              body-json (json/generate-string body)
              headers (cond-> {"Content-Type" "application/json"}
                        (not (str/blank? internal-secret))
                        (assoc "x-internal-trust" (hmac-sha256-hex internal-secret body-json)))]
          (try
            (let [r (http/post (str dispatcher-url "/xrpc/ai.gftd.apps.chat.scheduleReport")
                               {:headers headers :body body-json :timeout 30000})
                  resp (json/parse-string (:body r) true)]
              {:ok (boolean (:ok resp))
               :runId (or (:runId resp) "")
               :scheduledAt (or (:scheduledAt resp) "")})
            (catch Exception exc
              {:ok false :error (str "schedule_report dispatcher: " (.getMessage exc))}))))))))

;; ── dispatcher ─────────────────────────────────────────────────────────
(defn dispatch-tool [name args & {:keys [conv-id msg-id owner-did host-config]}]
  (case name
    "code_exec"       (tool-code-exec args)
    "image_gen"       (tool-image-gen args :conv-id conv-id :owner-did owner-did :host-config host-config)
    "file_save"       (tool-file-save args :conv-id conv-id :owner-did owner-did :host-config host-config)
    "rag_search"      (tool-rag-search args :owner-did owner-did :host-config host-config)
    "web_search"      (tool-web-search args :host-config host-config)
    "schedule_report" (tool-schedule-report args :conv-id conv-id :msg-id msg-id :owner-did owner-did
                                                :host-config host-config)
    {:ok false :error (str "unknown tool: " (pr-str name))}))
