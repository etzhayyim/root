(ns lg-open-patent.graphs.synthesize-invention
  "open-patent `synthesize_invention` graph — open-IP generation pipeline.

  NSID: com.etzhayyim.apps.openPatent.synthesizeInvention  (weekly cron 0 3 * * 1)

  PORT NOTE (ADR-2606280030): the Python `synthesize_invention.py` re-exports
  `kotodama.langgraph_graphs.open_patent_synthesize_invention` (not vendored in
  this checkout). This is a faithful port of the documented generation pipeline
  (app CLAUDE.md `Generation Pipeline`), node-for-node:

      gather_tech_trends
        -> synthesize_seeds   (LLM, temperature 0.6, per tech_domain)
             -> search_prior_art   (TEXT search vs vertex_open_patent_patent)
                  -> assess_novelty (LLM, novelty_score 0-100)
                       -> flag_for_review (novelty_score >= 60 -> status 'review')
                            -> emit_audit -> END

  HITL boundary: seeds with novelty_score >= 60 are flagged status='review' (a
  human drafts claims + decides filing). The actor never files autonomously.

  LLM edge -> lg-open-patent.llm/*chat* (Murakumo loopback, ADR-2605215000).
  Corpus + persistence -> lg-open-patent.store/*store* (PatentStore seam).
  Both are injectable; tests rebind them to deterministic stubs (offline)."
  (:require [clojure.string :as str]
            [langgraph.graph :as g]
            [lg-open-patent.llm :as llm]
            [lg-open-patent.store :as store]))

(def novelty-threshold 60)      ;; novelty_score >= 60 -> HITL review
(def synth-temperature 0.6)     ;; per CLAUDE.md Generation Pipeline
(def max-domains 5)

(defn- ms [] #?(:clj (System/currentTimeMillis) :cljs (.now js/Date)))

;; ── nodes ─────────────────────────────────────────────────────────────────────

(defn node-gather-tech-trends
  "Extract technology trends/domains from the existing patent corpus."
  [state]
  (let [domains (or (:tech_domains state)            ;; caller may pin domains
                    (->> (store/tech-trends store/*store*)
                         (take max-domains)
                         (mapv :domain)))]
    {:tech_domains (vec domains)}))

(defn node-synthesize-seeds
  "LLM generates an invention seed per tech domain (temperature 0.6)."
  [state]
  (let [domains (or (:tech_domains state) [])]
    (if (empty? domains)
      {:seeds [] :note "no tech domains in corpus"}
      {:seeds
       (vec
        (keep-indexed
         (fn [i domain]
           (let [system "You are an R&D inventor. Propose ONE novel, non-obvious invention seed building on the given technology domain. Reply with a one-line title, then a short description."
                 user   (str "Technology domain: " domain
                             "\nPropose a patentable invention seed.")
                 res    (llm/chat system user {:temperature synth-temperature :max-tokens 512})]
             (when-not (and (map? res) (:error res))
               (let [text  (str res)
                     lines (remove str/blank? (str/split-lines text))
                     title (str/trim (or (first lines) domain))]
                 {:seedId      (str "seed-" (ms) "-" i)
                  :tech_domain domain
                  :title       (subs title 0 (min 200 (count title)))
                  :description text
                  :status      "draft"}))))
         domains))})))

(defn node-search-prior-art
  "TEXT search the patent corpus for prior art relevant to each seed."
  [state]
  {:seeds
   (mapv (fn [seed]
           (let [hits (store/search-patents store/*store* (or (:tech_domain seed) (:title seed)))
                 refs (->> hits (map #(or (:publicationNumber %) (:patentId %) (:title %)))
                           (remove nil?) vec)]
             (assoc seed :prior_art_refs refs :prior_art_count (count refs))))
         (or (:seeds state) []))})

(defn node-assess-novelty
  "LLM scores each seed's novelty against discovered prior art (0-100)."
  [state]
  {:seeds
   (mapv (fn [seed]
           (let [system "You are a patent examiner. Given an invention seed and prior-art references, output ONLY an integer novelty score 0-100 (100 = wholly novel)."
                 user   (str "Seed: " (:title seed)
                             "\nDescription: " (:description seed)
                             "\nPrior art (" (:prior_art_count seed) "): "
                             (str/join ", " (:prior_art_refs seed)))
                 res    (llm/chat system user {:temperature 0.0 :max-tokens 16})
                 score  (if (and (map? res) (:error res))
                          0
                          (let [m (re-find #"\d{1,3}" (str res))]
                            (min 100 (max 0 (if m (#?(:clj Integer/parseInt :cljs js/parseInt) m) 0)))))]
             (assoc seed :novelty_score score)))
         (or (:seeds state) []))})

(defn node-flag-for-review
  "Flag seeds with novelty_score >= 60 for human review (HITL boundary)."
  [state]
  {:seeds
   (mapv (fn [seed]
           (assoc seed :novelty_status
                  (if (>= (or (:novelty_score seed) 0) novelty-threshold) "review" "low")))
         (or (:seeds state) []))})

(defn node-emit-audit
  "Persist reviewed seeds + novelty reports and emit the run summary."
  [state]
  (let [seeds    (or (:seeds state) [])
        reviewed (filterv #(= "review" (:novelty_status %)) seeds)]
    (doseq [seed reviewed]
      (let [{:keys [seed_uri]} (store/put-seed! store/*store* seed)]
        (store/put-novelty! store/*store*
                            {:reportId  (str "novelty-" (:seedId seed))
                             :seedId    (:seedId seed)
                             :seed_uri  seed_uri
                             :noveltyScore (:novelty_score seed)
                             :priorArtRefs (:prior_art_refs seed)})))
    {:ok true
     :summary {:domains   (count (:tech_domains state))
               :seeds     (count seeds)
               :flagged   (count reviewed)
               :threshold novelty-threshold}}))

(defn build
  "Compile the synthesize_invention StateGraph (documented 6-node pipeline)."
  []
  (-> (g/state-graph)
      (g/add-node :gather_tech_trends node-gather-tech-trends)
      (g/add-node :synthesize_seeds node-synthesize-seeds)
      (g/add-node :search_prior_art node-search-prior-art)
      (g/add-node :assess_novelty node-assess-novelty)
      (g/add-node :flag_for_review node-flag-for-review)
      (g/add-node :emit_audit node-emit-audit)
      (g/add-edge :gather_tech_trends :synthesize_seeds)
      (g/add-edge :synthesize_seeds :search_prior_art)
      (g/add-edge :search_prior_art :assess_novelty)
      (g/add-edge :assess_novelty :flag_for_review)
      (g/add-edge :flag_for_review :emit_audit)
      (g/set-entry-point :gather_tech_trends)
      (g/set-finish-point :emit_audit)
      (g/compile-graph)))

(def GRAPH (build))
