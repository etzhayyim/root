(ns lg-yukkuri.graphs.generate-visual
  "yukkuri `generateVisual` graph — 背景 + 挿絵 generation.

  NSID: com.etzhayyim.apps.yukkuri.generateVisual
  Actor: did:web:yukkuri.etzhayyim.com:actor:illustrator
  Faithful clj port of `lg/lg_yukkuri/graphs/generate_visual.py` (ADR-2606280030).

  Topology: START → fetch_scenes → generate → insert_assets → audit → END.

  The image-gen + uploadBlob is the INJECTABLE `*generate-one*` boundary fn
  (murakumo image endpoint + PDS uploadBlob); default uses babashka.http-client.
  Per-scene generation fans out via `pmap` (clj analogue of asyncio.gather).
  Copyright guardrail: a negative prompt is always attached (CLAUDE.md invariant).
  Node name `insert_assets` matches the Python `_build` wiring."
  (:require [langgraph.graph :as g]
            [lg-yukkuri.audit :as audit]
            [lg-yukkuri.store :as store]))

(def app-did         (or (System/getenv "YUKKURI_APP_DID") "did:web:yukkuri.etzhayyim.com"))
(def illustrator-did (or (System/getenv "YUKKURI_ILLUSTRATOR_DID")
                         "did:web:yukkuri.etzhayyim.com:actor:illustrator"))
(def image-url   (-> (or (System/getenv "MURAKUMO_IMAGE_URL")
                         "http://127.0.0.1:4000/v1/images/generations")
                     (clojure.string/replace #"/+$" "")))
(def pds-blob-url (or (System/getenv "PDS_BLOB_URL")
                      "https://atproto.etzhayyim.com/xrpc/com.atproto.repo.uploadBlob"))
(def negative-prompt "real person, celebrity, logo, watermark, nsfw, explicit")

(defn- as-int [v d] (cond (integer? v) v (string? v) (try (Integer/parseInt v) (catch Exception _ d)) :else d))
(defn- clip [s n] (let [s (str s)] (subs s 0 (min n (count s)))))

(defn- token-hex [n]
  (let [bs (byte-array n)] (.nextBytes (java.security.SecureRandom.) bs)
    (apply str (map #(format "%02x" %) bs))))

(defn default-generate-one
  "Default `*generate-one*`: image generation + uploadBlob for one scene."
  [scene]
  (try
    (let [post     (requiring-resolve 'babashka.http-client/post)
          generate (requiring-resolve 'cheshire.core/generate-string)
          parse    (requiring-resolve 'cheshire.core/parse-string)
          b64dec   (java.util.Base64/getDecoder)
          prompt   (str "anime style background, " (:location scene) ", " (:action scene)
                        ", soft colors, 2D illustration")
          r (post image-url {:headers {"Content-Type" "application/json"} :throw false
                             :body (generate {:model "flux-schnell" :prompt prompt
                                              :negative_prompt negative-prompt
                                              :width 1280 :height 720 :num_inference_steps 4
                                              :response_format "b64_json"})})]
      (if (>= (:status r) 400)
        {:scene_index (:scene_index scene) :error (str "image " (:status r))}
        (let [b64 (get-in (parse (:body r) true) [:data 0 :b64_json] "")]
          (if (empty? b64)
            {:scene_index (:scene_index scene) :error "empty b64"}
            (let [img (.decode b64dec ^String b64)
                  ub  (post pds-blob-url {:headers {"Content-Type" "image/png"} :throw false :body img})]
              (if (>= (:status ub) 400)
                {:scene_index (:scene_index scene) :error (str "uploadBlob " (:status ub))}
                {:scene_index (:scene_index scene)
                 :blob_key (get-in (parse (:body ub) true) [:blob :ref :$link] "")}))))))
    (catch Exception e {:scene_index (:scene_index scene) :error (clip (.getMessage e) 200)})))

(def ^:dynamic *generate-one* default-generate-one)

(defn- fetch-scenes [video-id]
  (->> (store/select-where "vertex_yukkuri_scene" "video_id" video-id 20)
       (sort-by #(as-int (:scene_index %) 0))
       (mapv (fn [r] {:scene_index (as-int (:scene_index r) 0)
                      :location (or (:location r) "") :action (or (:action r) "")}))))

(defn node-fetch-scenes [state]
  (let [video-id (or (:video_id state) "")]
    (if (= "" video-id)
      {:error "video_id required"}
      (try {:scenes (fetch-scenes video-id)}
           (catch Exception e {:error (str "fetch: " (clip (.getMessage e) 180))})))))

(defn node-generate [state]
  (if (:error state)
    {}
    (let [scenes (or (:scenes state) [])]
      (if (empty? scenes)
        {:visual_assets [] :generated_count 0}
        (let [ok (vec (remove :error (doall (pmap *generate-one* scenes))))]
          {:visual_assets ok :generated_count (count ok)})))))

(defn node-insert-assets [state]
  (if (or (:error state) (empty? (:visual_assets state)))
    {}
    (let [video-id (or (:video_id state) "")
          created  (str (java.time.OffsetDateTime/now java.time.ZoneOffset/UTC))]
      (try
        (doseq [asset (:visual_assets state)]
          (store/insert-row "vertex_yukkuri_asset"
                            {:vertex_id (str "asset-img-" video-id "-" (:scene_index asset) "-" (token-hex 3))
                             :video_id video-id :kind "image" :actor_did illustrator-did
                             :blob_key (:blob_key asset)
                             :meta_json (str "{\"sceneIndex\":" (:scene_index asset) "}")
                             :created_at created}))
        {}
        (catch Exception e {:error (str "insert: " (clip (.getMessage e) 280))})))))

(defn node-audit [state]
  (audit/emit-audit-bg {:actor illustrator-did
                        :activity "yukkuri.generateVisual"
                        :object-id (str "visual:" (or (:video_id state) "") ":" (quot (System/currentTimeMillis) 1000))
                        :object-type "yukkuri.asset"
                        :attributes {:videoId (:video_id state) :count (or (:generated_count state) 0)}})
  {})

(defn build
  "Compile the generateVisual StateGraph."
  []
  (-> (g/state-graph)
      (g/add-node :fetch_scenes node-fetch-scenes)
      (g/add-node :generate node-generate)
      (g/add-node :insert_assets node-insert-assets)
      (g/add-node :audit node-audit)
      (g/add-edge :fetch_scenes :generate)
      (g/add-edge :generate :insert_assets)
      (g/add-edge :insert_assets :audit)
      (g/set-entry-point :fetch_scenes)
      (g/set-finish-point :audit)
      (g/compile-graph)))

(def GRAPH (build))
