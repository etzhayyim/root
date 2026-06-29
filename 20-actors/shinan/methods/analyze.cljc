#!/usr/bin/env bb
;; shinan 指南 — open-learning supply/demand → coverage map (clj-native, pure stdlib).
(ns shinan.methods.analyze
  "analyze.cljc — shinan 指南 学習支援 core, 学習解放 framing (ADR-2606291501).

  Maps the OPEN-learning supply (resources) against the demand (topics) and surfaces
  WHERE open learning exists and WHERE the gap is — the 学習解放 value. It never scores,
  ranks, or predicts any learner; there is no learner in the model at all (the charter
  heart — see kotoba/ontology.shinan.edn :unrepresentable).

    topic route ∈ {:covered :needs-localization :coverage-gap}
      :covered            — ∃ open resource covering it in the topic's country language
      :needs-localization — covered, but no resource in the country language (→ translate)
      :coverage-gap       — no open resource covers it (→ create open material)
    resource route ∈ {:offer :monitor}
      :offer    — openness ≥ 0.6 → freely offer as commons
      :monitor  — low availability → observe (still open-license by construction)

  `datoms` emits disclosed topic/resource facts + the DERIVED route as EAVT, each flagged
  :shinan/derived + :shinan/sourcing. None of the unrepresentable score/rank/gate/predict
  attributes can be emitted — they have no code path."
  (:require [clojure.string :as str]))

(def offer-openness-min 0.6)
(def country-language {:cn :zh :kr :ko :jp :ja})

(defn- covers? [resource topic-id]
  (some #(= % topic-id) (:covers resource)))

(defn resource-route
  "Pure: :offer if openness ≥ 0.6, else :monitor."
  [resource]
  (if (>= (double (:openness resource)) offer-openness-min) :offer :monitor))

(defn topic-route
  "Pure (given the resource set): coverage route for one topic."
  [topic resources]
  (let [covering (filter #(covers? % (:id topic)) resources)
        lang (country-language (:country topic))]
    (cond
      (empty? covering)
      {:route :coverage-gap :reason :no-open-resource}
      (some #(some #{lang} (:languages %)) covering)
      {:route :covered :reason :localized}
      :else
      {:route :needs-localization :reason :unlocalized})))

(defn assess
  "Assess topics (vs resources) + resources. Returns
   {\"topics\" [{:topic … :route … :reason …} …]
    \"resources\" [{:resource … :route …} …]
    \"topic-tally\" {route→count} \"resource-tally\" {route→count}
    \"by-country\" {country→{route→count}} \"worklist\" [gap+localization topic rows]}."
  [topics resources]
  (let [t-rows (mapv (fn [t] (merge {:topic t} (topic-route t resources))) topics)
        r-rows (mapv (fn [r] {:resource r :route (resource-route r)}) resources)
        worklist (vec (filter #(#{:coverage-gap :needs-localization} (:route %)) t-rows))
        by-country (reduce (fn [m {:keys [topic route]}]
                             (update-in m [(:country topic) route] (fnil inc 0)))
                           {} t-rows)]
    {"topics" t-rows "resources" r-rows
     "topic-tally" (frequencies (map :route t-rows))
     "resource-tally" (frequencies (map :route r-rows))
     "by-country" by-country
     "worklist" worklist}))

;; ── EAVT datom emit ──────────────────────────────────────────────────────────
(defn datoms
  "Emit disclosed topic/resource facts + DERIVED routes as EAVT [:db/add e a v]."
  [assessment]
  (let [sourcing ":synthetic"]
    (vec
     (concat
      (mapcat
       (fn [{:keys [topic route reason]}]
         (let [e (:id topic)]
           [[":db/add" e ":shinan.topic/name" (:name topic)]
            [":db/add" e ":shinan.topic/subject" (str (:subject topic))]
            [":db/add" e ":shinan.topic/country" (str (:country topic))]
            [":db/add" e ":shinan.topic/exam" (:exam topic)]
            [":db/add" e ":shinan.topic/priority" (str (:priority topic))]
            [":db/add" e ":shinan.rem/route" (str route)]
            [":db/add" e ":shinan.rem/reason" (str reason)]
            [":db/add" e ":shinan/derived" true]
            [":db/add" e ":shinan/sourcing" sourcing]]))
       (get assessment "topics"))
      (mapcat
       (fn [{:keys [resource route]}]
         (let [e (:id resource)]
           [[":db/add" e ":shinan.resource/name" (:name resource)]
            [":db/add" e ":shinan.resource/license" (str (:license resource))]
            [":db/add" e ":shinan.resource/openness" (double (:openness resource))]
            [":db/add" e ":shinan.resource/languages" (mapv str (:languages resource))]
            [":db/add" e ":shinan.resource/modality" (str (:modality resource))]
            [":db/add" e ":shinan.rem/route" (str route)]
            [":db/add" e ":shinan/derived" true]
            [":db/add" e ":shinan/sourcing" sourcing]]))
       (get assessment "resources"))))))

;; ── human-readable report ────────────────────────────────────────────────────
(defn report [assessment]
  (let [t-rows (get assessment "topics")
        worklist (get assessment "worklist")]
    (str/join
     "\n"
     (concat
      ["# shinan 指南 — open-learning coverage map (学習解放, ADR-2606291501)"
       (str "topics: " (count t-rows)
            "  topic-routes: " (pr-str (get assessment "topic-tally"))
            "  resource-routes: " (pr-str (get assessment "resource-tally")))
       "(no learner is modelled — shinan never scores, ranks, or predicts; it maps open scaffolds)"
       ""
       "## coverage by topic"]
      (for [{:keys [topic route reason]} t-rows]
        (str (format "%-18s" (:id topic))
             "  → " (name route) " (" (name reason) ")"
             "  [" (name (:country topic)) "] " (:name topic)))
      [""
       "## 学習解放 worklist — where open learning is missing"]
      (if (seq worklist)
        (for [{:keys [topic route]} worklist]
          (str "  - " (name route) ": " (:name topic) " [" (name (:country topic)) "]"))
        ["  (none — every topic has a localized open resource)"])))))

#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/shinan/kotoba/seed.edn")
           rows (clojure.edn/read-string (slurp seed))
           topics (vec (filter #(= (:type %) :topic) rows))
           resources (vec (filter #(= (:type %) :resource) rows))
           a (assess topics resources)]
       (println (report a)))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
