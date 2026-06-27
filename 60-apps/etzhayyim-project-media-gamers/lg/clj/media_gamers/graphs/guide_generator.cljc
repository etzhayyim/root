(ns media-gamers.graphs.guide-generator
  "media-gamers `guide_generator` graph — clj twin of graphs/guide_generator.py.
  NSID: com.etzhayyim.apps.media_gamers.generateGuide

  Topology preserved:
    START → resolve → generate → evaluate
            ─(score >= 70)→ translate → commit → audit → END
            ─(score <  70)→ commit → audit → END

  Port notes: httpx → babashka.http-client; JSON → cheshire; LLM → Murakumo
  loopback (media-gamers.llm/chat). Conditional edge = langgraph-clj
  add-conditional-edges with the same `_route_after_evaluate` predicate."
  (:require [clojure.string :as str]
            [media-gamers.games :as games]
            [media-gamers.llm :as llm]
            [media-gamers.audit :as audit]
            #?(:clj [babashka.http-client :as http])
            #?(:clj [cheshire.core :as json])
            #?(:clj [langgraph.graph :as g])))

(defn- getenv [k default]
  #?(:clj (or (System/getenv k) default) :default default))

(defn app-did [] (getenv "MEDIA_GAMERS_APP_DID" "did:web:media-gamers.etzhayyim.com"))
(defn commit-guide-xrpc []
  (getenv "COMMIT_GUIDE_XRPC_URL"
          "https://media-gamers.etzhayyim.com/xrpc/com.etzhayyim.apps.media_gamers.guide.commitGuide"))

;; ── nodes ───────────────────────────────────────────────────────────────────

(defn node-resolve
  "Port of `_node_resolve` — look up game in SEED_GAMES by slug."
  [state]
  (let [game (games/seed-games-by-slug (:game-slug state ""))]
    (if-not game
      {:error (str "unknown game slug: " (pr-str (:game-slug state "")))}
      {:game-name (:name game)
       :game-genre (:genre game)
       :game-year (:releaseYear game)})))

#?(:clj
   (defn node-generate [state]
     (if (:error state)
       {}
       (let [game-name (:game-name state "")
             game-genre (:game-genre state "")
             game-year (:game-year state 2024)
             guide-type (:guide-type state "beginner-guide")
             [system user] (games/build-prompt game-name game-genre game-year guide-type)
             raw (llm/chat system user :max-tokens 1500 :temp 0.7)]
         (if (str/blank? raw)
           {:error "LLM returned empty response" :body "" :title ""}
           (let [[title body] (games/split-title-body raw game-name guide-type)]
             {:title title :body body}))))))

(defn node-evaluate [state]
  {:quality-score (games/compute-quality (:body state ""))})

#?(:clj
   (defn node-translate [state]
     (let [body (:body state "") title (:title state "")
           translations
           (reduce
            (fn [acc lang]
              (try
                (let [raw (llm/chat
                           (str "You are a professional translator. Translate the following gaming guide to "
                                lang ". Keep markdown formatting. Return JSON: "
                                "{\"title\": \"...\", \"body\": \"...\", \"social_post\": \"...\"}. "
                                "social_post: 1-2 sentences with relevant hashtags.")
                           (str "Title: " title "\n\nBody:\n" body)
                           :max-tokens 1800 :temp 0.3)
                      parsed (or (try (json/parse-string raw true) (catch Exception _ nil))
                                 {:title title :body raw :social_post ""})
                      tbody (str (or (:body parsed) ""))]
                  (conj acc {:lang lang
                             :title (str (or (:title parsed) title))
                             :body tbody
                             :quality_score (games/compute-quality tbody)
                             :social_post (str (or (:social_post parsed) ""))}))
                (catch Exception _ acc)))
            [] games/target-langs)]
       {:translations translations})))

#?(:clj
   (defn node-commit [state]
     (if (:error state)
       {:commit-result {:ok false :error (:error state)}}
       (let [payload {:gameSlug (:game-slug state "")
                      :guideType (:guide-type state "")
                      :gameName (:game-name state "")
                      :gameGenre (:game-genre state "")
                      :gameYear (:game-year state)
                      :title (:title state "")
                      :body (:body state "")
                      :qualityScore (:quality-score state 0)
                      :translations (:translations state [])}]
         (try
           (let [r (http/post (commit-guide-xrpc)
                              {:body (json/generate-string payload)
                               :headers {"Content-Type" "application/json"}
                               :timeout 30000 :throw false})]
             (if (>= (:status r) 400)
               {:commit-result {:ok false :httpStatus (:status r)
                                :body (subs (str (:body r)) 0 (min 200 (count (str (:body r)))))}}
               {:commit-result (merge {:ok true} (try (json/parse-string (:body r) true)
                                                      (catch Exception _ {})))}))
           (catch Exception exc
             {:commit-result {:ok false :error (subs (str exc) 0 (min 200 (count (str exc))))}}))))))

(defn node-audit [state]
  #?(:clj (audit/emit-audit-bg
           {:actor (app-did)
            :activity "media_gamers.guide.generate"
            :object-id (str "guide:" (:game-slug state "") ":" (:guide-type state "")
                            ":" (quot (System/currentTimeMillis) 1000))
            :object-type "media_gamers.guide"
            :attributes {:gameSlug (:game-slug state)
                         :guideType (:guide-type state)
                         :qualityScore (:quality-score state)
                         :translationCount (count (:translations state []))
                         :commitOk (get (:commit-result state) :ok)
                         :error (:error state)}}))
  {})

(defn route-after-evaluate
  "Port of `_route_after_evaluate`."
  [state]
  (if (>= (or (:quality-score state) 0) games/quality-threshold) :translate :commit))

#?(:clj
   (defn build []
     (-> (g/state-graph)
         (g/add-node :resolve node-resolve)
         (g/add-node :generate node-generate)
         (g/add-node :evaluate node-evaluate)
         (g/add-node :translate node-translate)
         (g/add-node :commit node-commit)
         (g/add-node :audit node-audit)
         (g/add-edge :resolve :generate)
         (g/add-edge :generate :evaluate)
         (g/add-conditional-edges :evaluate route-after-evaluate
                                  {:translate :translate :commit :commit})
         (g/add-edge :translate :commit)
         (g/add-edge :commit :audit)
         (g/set-entry-point :resolve)
         (g/set-finish-point :audit)
         (g/compile-graph))))

#?(:clj (def graph (delay (build))))
