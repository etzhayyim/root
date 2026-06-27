(ns lg-yukkuri.graphs.synthesize-voice
  "yukkuri `synthesizeVoice` graph — kokoro-ts TTS (L + R, parallel).

  NSID: com.etzhayyim.apps.yukkuri.synthesizeVoice
  Actors: voiceLeft (af_heart) / voiceRight (am_puck)
  Faithful clj port of `lg/lg_yukkuri/graphs/synthesize_voice.py` (ADR-2606280030).

  Topology: START → fetch_lines → synthesize → update_lines → audit → END.

  The TTS+uploadBlob call is the INJECTABLE `*tts-one*` boundary fn (native
  murakumo audio endpoint + PDS uploadBlob); the default uses babashka.http-client.
  The Python fans the per-line TTS out with asyncio.gather; clj runs them via
  `pmap` (a faithful parallel analogue). Line reads/writes go through the store
  seam. DEVIATION: no RetryPolicy in langgraph-clj."
  (:require [langgraph.graph :as g]
            [lg-yukkuri.audit :as audit]
            [lg-yukkuri.store :as store]))

(def app-did   (or (System/getenv "YUKKURI_APP_DID") "did:web:yukkuri.etzhayyim.com"))
(def tts-url   (-> (or (System/getenv "MURAKUMO_TTS_URL")
                       "http://127.0.0.1:4000/v1/audio/speech")
                   (clojure.string/replace #"/+$" "")))
(def pds-blob-url (or (System/getenv "PDS_BLOB_URL")
                      "https://atproto.etzhayyim.com/xrpc/com.atproto.repo.uploadBlob"))
(def voice-preset {"left"  (or (System/getenv "YUKKURI_VOICE_LEFT") "af_heart")
                   "right" (or (System/getenv "YUKKURI_VOICE_RIGHT") "am_puck")})

(defn- as-int [v d] (cond (integer? v) v (string? v) (try (Integer/parseInt v) (catch Exception _ d)) :else d))
(defn- clip [s n] (let [s (str s)] (subs s 0 (min n (count s)))))

(defn default-tts-one
  "Default `*tts-one*`: POST text to the murakumo TTS endpoint (wav), upload the
  wav to the PDS, return {:line_id :speaker :blob_key} | {:line_id :error}."
  [line]
  (try
    (let [post     (requiring-resolve 'babashka.http-client/post)
          generate (requiring-resolve 'cheshire.core/generate-string)
          parse    (requiring-resolve 'cheshire.core/parse-string)
          voice    (get voice-preset (:speaker line) "af_heart")
          r        (post tts-url {:headers {"Content-Type" "application/json"} :throw false
                                  :body (generate {:model "kokoro" :input (:text line)
                                                   :voice voice :response_format "wav"})})]
      (if (>= (:status r) 400)
        {:line_id (:line_id line) :error (str "tts " (:status r))}
        (let [ub (post pds-blob-url {:headers {"Content-Type" "audio/wav"} :throw false
                                     :body (:body r)})]
          (if (>= (:status ub) 400)
            {:line_id (:line_id line) :error (str "uploadBlob " (:status ub))}
            {:line_id (:line_id line) :speaker (:speaker line)
             :blob_key (get-in (parse (:body ub) true) [:blob :ref :$link] "")}))))
    (catch Exception e {:line_id (:line_id line) :error (clip (.getMessage e) 200)})))

(def ^:dynamic *tts-one* default-tts-one)

(defn- fetch-lines [video-id]
  (->> (store/select-where "vertex_yukkuri_line" "video_id" video-id 500)
       (remove :voice_blob_key)
       (sort-by (juxt #(as-int (:scene_index %) 0) #(as-int (:line_index %) 0)))
       (mapv (fn [r] {:line_id (:line_id r) :scene_index (as-int (:scene_index r) 0)
                      :line_index (as-int (:line_index r) 0) :speaker (:speaker r) :text (:text r)}))))

(defn node-fetch-lines [state]
  (let [video-id (or (:video_id state) "")]
    (if (= "" video-id)
      {:error "video_id required"}
      (try {:lines (fetch-lines video-id)}
           (catch Exception e {:error (str "fetch_lines: " (clip (.getMessage e) 180))})))))

(defn node-synthesize [state]
  (if (:error state)
    {}
    (let [lines (or (:lines state) [])]
      (if (empty? lines)
        {:voice_assets [] :synthesized_count 0}
        (let [results (doall (pmap *tts-one* lines))
              ok      (vec (remove :error results))]
          {:voice_assets ok :synthesized_count (count ok)})))))

(defn node-update-lines [state]
  (if (or (:error state) (empty? (:voice_assets state)))
    {}
    (try
      (doseq [asset (:voice_assets state)]
        (let [rows (store/select-where "vertex_yukkuri_line" "line_id" (:line_id asset) nil)]
          (when (seq rows)
            (store/insert-row "vertex_yukkuri_line" (assoc (first rows) :voice_blob_key (:blob_key asset))))))
      {}
      (catch Exception e {:error (str "update: " (clip (.getMessage e) 280))}))))

(defn node-audit [state]
  (audit/emit-audit-bg {:actor app-did
                        :activity "yukkuri.synthesizeVoice"
                        :object-id (str "voice:" (or (:video_id state) "") ":" (quot (System/currentTimeMillis) 1000))
                        :object-type "yukkuri.voice"
                        :attributes {:videoId (:video_id state) :synthesizedCount (or (:synthesized_count state) 0)
                                     :ok (not (boolean (:error state)))}})
  {})

(defn build
  "Compile the synthesizeVoice StateGraph."
  []
  (-> (g/state-graph)
      (g/add-node :fetch_lines node-fetch-lines)
      (g/add-node :synthesize node-synthesize)
      (g/add-node :update_lines node-update-lines)
      (g/add-node :audit node-audit)
      (g/add-edge :fetch_lines :synthesize)
      (g/add-edge :synthesize :update_lines)
      (g/add-edge :update_lines :audit)
      (g/set-entry-point :fetch_lines)
      (g/set-finish-point :audit)
      (g/compile-graph)))

(def GRAPH (build))
