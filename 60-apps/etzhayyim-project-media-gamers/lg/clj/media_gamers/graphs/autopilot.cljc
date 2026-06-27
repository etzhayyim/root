(ns media-gamers.graphs.autopilot
  "media-gamers `autopilot` graph — clj twin of graphs/autopilot.py.
  NSID: com.etzhayyim.apps.media_gamers.autopilot
  Cron: */30 * * * * (every 30 minutes).

  Topology preserved:
    START → resolve_mood → select_game → generate → evaluate
            ─(score >= 70)→ translate → commit → post → audit → END
            ─(score <  70)→ commit → post → audit → END

  Port notes: httpx → babashka.http-client; JSON → cheshire; LLM → Murakumo
  loopback. Social post → PDS com.atproto.repo.createRecord (same wire as python).
  Deterministic mood/game/guide selection by epoch buckets is preserved."
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
(defn repo-did [] (getenv "MEDIA_GAMERS_REPO_DID" "did:web:a7m8oocs.etzhayyim.com"))
(defn pds-base [] (getenv "PDS_URL" "https://atproto.etzhayyim.com"))
(defn commit-guide-xrpc []
  (getenv "COMMIT_GUIDE_XRPC_URL"
          "https://media-gamers.etzhayyim.com/xrpc/com.etzhayyim.apps.media_gamers.guide.commitGuide"))

(defn- epoch [] (quot #?(:clj (System/currentTimeMillis) :default 0) 1000))

;; ── nodes ───────────────────────────────────────────────────────────────────

(defn node-resolve-mood
  "Port of `_node_resolve_mood` — rotate 5 moods every 30 min via epoch."
  [_state]
  {:mood (nth games/moods (mod (quot (epoch) 1800) 5))})

(defn node-select-game
  "Port of `_node_select_game`."
  [state]
  (let [mood (:mood state "reflective")
        game-slugs (get games/mood->games mood ["monster-hunter-wilds" "metaphor-refantazio"])
        game-slug (nth game-slugs (mod (quot (epoch) 1800) (count game-slugs)))
        guide-type (nth games/guide-types (mod (quot (epoch) 900) (count games/guide-types)))]
    {:game-slug game-slug :guide-type guide-type}))

#?(:clj
   (defn node-generate [state]
     (if (:error state)
       {}
       (let [game (games/seed-games-by-slug (:game-slug state ""))]
         (if-not game
           {:error (str "unknown game slug: " (pr-str (:game-slug state "")))}
           (let [[system user] (games/build-prompt (:name game) (:genre game) (:releaseYear game)
                                                   (:guide-type state "beginner-guide"))
                 raw (llm/chat system user :max-tokens 1500 :temp 0.7)]
             (if (str/blank? raw)
               {:error "LLM returned empty response" :body "" :title ""}
               (let [[title body] (games/split-title-body raw (:name game) (:guide-type state ""))]
                 {:game-name (:name game) :game-genre (:genre game) :game-year (:releaseYear game)
                  :title title :body body}))))))))

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
                  (conj acc {:lang lang :title (str (or (:title parsed) title)) :body tbody
                             :quality_score (games/compute-quality tbody)
                             :social_post (str (or (:social_post parsed) ""))}))
                (catch Exception _ acc)))
            [] games/target-langs)]
       {:translations translations})))

#?(:clj
   (defn node-commit [state]
     (when-not (:error state)
       (let [payload {:gameSlug (:game-slug state "") :guideType (:guide-type state "")
                      :gameName (:game-name state "") :gameGenre (:game-genre state "")
                      :gameYear (:game-year state) :title (:title state "") :body (:body state "")
                      :qualityScore (:quality-score state 0) :translations (:translations state [])}]
         (try
           (http/post (commit-guide-xrpc)
                      {:body (json/generate-string payload)
                       :headers {"Content-Type" "application/json"} :timeout 30000 :throw false})
           (catch Exception _ nil))))
     {}))

(defn now-iso-z []
  #?(:clj (.format (java.time.format.DateTimeFormatter/ofPattern "yyyy-MM-dd'T'HH:mm:ss'Z'")
                   (java.time.ZonedDateTime/now (java.time.ZoneOffset/UTC)))
     :default ""))

(defn post-text
  "Pure: build the 300-char social-post text. Port of `_node_post` formatting."
  [{:keys [title body game-genre guide-type game-slug]}]
  (let [hashtag-genre (-> (str (or game-genre "gaming")) (str/replace "-" "") (str/replace " " ""))
        hashtag-guide (-> (str (or guide-type "guide")) (str/replace "-" "") (str/replace " " ""))
        guide-url (str "https://media-gamers.etzhayyim.com/en/game/" game-slug "/" guide-type)
        text (str title "\n\n" (subs (str body) 0 (min 200 (count (str body)))) "...\n\n"
                  "#" hashtag-genre " #gaming #" hashtag-guide "\n" guide-url)]
    (subs text 0 (min 300 (count text)))))

#?(:clj
   (defn node-post [state]
     (if (:error state)
       {:post-status "skipped"}
       (let [text (post-text {:title (:title state "") :body (:body state "")
                              :game-genre (:game-genre state "gaming")
                              :guide-type (:guide-type state "guide")
                              :game-slug (:game-slug state "")})
             record {"$type" "app.bsky.feed.post" :text text :createdAt (now-iso-z)}]
         (try
           (let [r (http/post (str (pds-base) "/xrpc/com.atproto.repo.createRecord")
                              {:body (json/generate-string
                                      {:repo (repo-did) :collection "app.bsky.feed.post" :record record})
                               :headers {"Content-Type" "application/json"
                                         "x-kotodama-verified" "true"
                                         "x-etzhayyim-org-id" "anon"}
                               :timeout 15000 :throw false})]
             (if (< (:status r) 400)
               {:post-status "posted" :ok true}
               {:post-status "error" :ok (boolean (seq (:body state "")))}))
           (catch Exception _
             {:post-status "error" :ok (boolean (seq (:body state "")))}))))))

(defn node-audit [state]
  #?(:clj (audit/emit-audit-bg
           {:actor (app-did)
            :activity "media_gamers.autopilot"
            :object-id (str "autopilot:" (:game-slug state "") ":" (:guide-type state "")
                            ":" (quot (System/currentTimeMillis) 1000))
            :object-type "media_gamers.guide"
            :attributes {:mood (:mood state) :gameSlug (:game-slug state)
                         :guideType (:guide-type state) :qualityScore (:quality-score state)
                         :translationCount (count (:translations state []))
                         :postStatus (:post-status state) :ok (:ok state true)
                         :error (:error state)}}))
  {})

(defn route-after-evaluate [state]
  (if (>= (or (:quality-score state) 0) games/quality-threshold) :translate :commit))

#?(:clj
   (defn build []
     (-> (g/state-graph)
         (g/add-node :resolve-mood node-resolve-mood)
         (g/add-node :select-game node-select-game)
         (g/add-node :generate node-generate)
         (g/add-node :evaluate node-evaluate)
         (g/add-node :translate node-translate)
         (g/add-node :commit node-commit)
         (g/add-node :post node-post)
         (g/add-node :audit node-audit)
         (g/add-edge :resolve-mood :select-game)
         (g/add-edge :select-game :generate)
         (g/add-edge :generate :evaluate)
         (g/add-conditional-edges :evaluate route-after-evaluate
                                  {:translate :translate :commit :commit})
         (g/add-edge :translate :commit)
         (g/add-edge :commit :post)
         (g/add-edge :post :audit)
         (g/set-entry-point :resolve-mood)
         (g/set-finish-point :audit)
         (g/compile-graph))))

#?(:clj (def graph (delay (build))))
