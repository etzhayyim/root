(ns tests.test-smoke
  "clj twin of tests/test_smoke.py — asserts the registry/NSID/parity invariants
  the python smoke tests check, plus that every clj-ported graph compiles and is
  invocable under bb, plus the pure helper ports (quality / prompt / post-text /
  parse-entries / datoms / camel->snake)."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [cheshire.core :as json]
            [clojure.java.io :as io]
            [media-gamers.server :as server]
            [media-gamers.games :as games]
            [media-gamers.audit :as audit]
            [media-gamers.llm :as llm]
            [media-gamers.graphs.guide-generator :as guide]
            [media-gamers.graphs.autopilot :as auto]
            [media-gamers.graphs.ingest-charts :as charts]
            [media-gamers.graphs.health :as health]
            [langgraph.graph :as g]))

(deftest host-effects-are-explicit-capabilities
  (testing "portable LLM cannot perform HTTP when unconfigured"
    (binding [llm/*http-post* nil]
      (is (= "" (llm/chat "system" "user")))))
  (testing "explicit LLM capability preserves the Murakumo wire path"
    (let [seen (atom nil)]
      (binding [llm/*http-post* (fn [url _]
                                  (reset! seen url)
                                  {:status 200
                                   :body "{\"choices\":[{\"message\":{\"content\":\"ok\"}}]}"})]
        (is (= "ok" (llm/chat "system" "user")))
        (is (= "http://127.0.0.1:4000/v1/chat/completions" @seen)))))
  (testing "audit secret is purpose-bound config"
    (let [wire (atom nil)]
      (binding [audit/*config* {:url "http://audit.internal" :disabled? false
                                :timeout-ms 1000 :secret "purpose-bound"}
                audit/*http-post* (fn [url opts] (reset! wire [url opts]) {:status 200})]
        (audit/emit-audit {:actor "did:test" :activity "test"})
        (is (= "purpose-bound" (get-in @wire [1 :headers "x-internal-trust"]))))))
  (testing "SteamSpy fetch requires an explicit HTTP capability"
    (binding [charts/*http-get* nil]
      (is (false? (:ok (charts/node-fetch {})))))))

(def expected-graphs #{"health" "ingest_charts" "guide_generator" "autopilot" "pokopia_research"})

(def expected-nsid-map
  {"com.etzhayyim.apps.media_gamers.health"          "health"
   "com.etzhayyim.apps.media_gamers.ingestCharts"    "ingest_charts"
   "com.etzhayyim.apps.media_gamers.generateGuide"   "guide_generator"
   "com.etzhayyim.apps.media_gamers.autopilot"       "autopilot"
   "com.etzhayyim.apps.media_gamers.researchPokopia" "pokopia_research"})

;; ── registry / NSID parity (mirrors test_smoke.py) ───────────────────────────

(deftest graph-names-match-expected-set
  (is (= server/graph-names expected-graphs)))

(deftest nsid-map-completeness
  (is (= server/nsid->assistant expected-nsid-map)))

(deftest nsid-map-references-known-graphs
  (doseq [[nsid gname] server/nsid->assistant]
    (is (contains? server/graph-names gname) (str nsid " → " gname " not in graph-names"))))

(deftest langgraph-json-graphs-match-server
  (let [cfg (json/parse-string (slurp (io/file ".." "langgraph.json")) true)
        declared (set (map name (keys (:graphs cfg))))]
    (is (= declared server/graph-names)
        (str "drift: langgraph.json=" declared " server=" server/graph-names))))

(deftest langgraph-json-has-crons-for-scheduled-graphs
  (let [cfg (json/parse-string (slurp (io/file ".." "langgraph.json")) true)
        cron-graphs (set (map :graph (:crons cfg)))]
    (is (contains? cron-graphs "autopilot"))
    (is (contains? cron-graphs "ingest_charts"))))

(deftest unknown-nsid-throws-404
  (is (thrown-with-msg? clojure.lang.ExceptionInfo #"unknown NSID"
                        (server/xrpc "com.etzhayyim.apps.media_gamers.unknownMethod" {}))))

;; ── graphs compile + are invocable ──────────────────────────────────────────

(deftest all-clj-graphs-compile
  (doseq [[gname cg] @server/graphs]
    (is (some? cg) (str gname " compiled"))
    (is (fn? g/invoke))))

(deftest health-graph-runs
  ;; health node is pure (no LLM/HTTP) — fully runnable under bb offline.
  (let [out (g/invoke @health/graph {})]
    (is (true? (:ok out)))
    (is (= "lg-media-gamers" (:service out)))
    (is (= "0.1.0" (:version out)))))

;; ── XRPC body transform ──────────────────────────────────────────────────────

(deftest camel-to-snake-port
  (is (= "game_slug" (server/camel->snake "gameSlug")))
  (is (= "guide_type" (server/camel->snake "guideType")))
  (is (= "health" (server/camel->snake "health"))))

(deftest xrpc-input-transform
  (is (= {:game-slug "elden-ring" :guide-type "boss-guide"}
         (server/xrpc-input->graph-input {"gameSlug" "elden-ring" "guideType" "boss-guide"}))))

;; ── pure helper ports ────────────────────────────────────────────────────────

(deftest quality-port-matches-python
  (testing "empty body — heading 0.4 + checklist 0.5 → 24.5 (matches python)"
    (is (= 24.5 (games/compute-quality ""))))
  (testing "heading + checklist body scores higher"
    (let [s (games/compute-quality "## Intro\n- one\n- two")]
      (is (> s 24.5))
      (is (<= s 100.0)))))

(deftest build-prompt-port
  (let [[system user] (games/build-prompt "Elden Ring" "action-rpg" 2022 "boss-guide")]
    (is (str/includes? system "expert gaming guide writer"))
    (is (str/includes? user "Boss Guide"))
    (is (str/includes? user "Elden Ring"))))

(deftest split-title-body-port
  (let [[title body] (games/split-title-body "# My Title\nline one\nline two" "X" "boss-guide")]
    (is (= "My Title" title))
    (is (= "line one\nline two" body))))

(deftest seed-catalog-port
  (is (= 11 (count games/seed-games)))
  (is (= "Elden Ring" (:name (games/seed-games-by-slug "elden-ring"))))
  (is (= ["ja" "zh" "es" "ar" "hi" "ko"] games/target-langs))
  (is (= 70 games/quality-threshold)))

(deftest route-predicates
  (is (= :translate (guide/route-after-evaluate {:quality-score 80})))
  (is (= :commit (guide/route-after-evaluate {:quality-score 40})))
  (is (= :translate (auto/route-after-evaluate {:quality-score 70})))
  (is (= :commit (auto/route-after-evaluate {:quality-score 0}))))

(deftest autopilot-mood-rotation
  (is (= 5 (count games/moods)))
  (is (contains? (set (vals games/mood->games)) ["elden-ring" "black-myth-wukong"])))

(deftest autopilot-post-text-port
  (let [t (auto/post-text {:title "Guide" :body (apply str (repeat 400 "x"))
                           :game-genre "action-rpg" :guide-type "boss-guide"
                           :game-slug "elden-ring"})]
    (is (<= (count t) 300))
    (is (str/includes? t "#actionrpg"))
    (is (str/includes? t "#bossguide"))))

;; ── ingest_charts pure ports (RW INSERT → kotoba datoms) ─────────────────────

(deftest parse-entries-port
  (let [data {:a {:name "A" :players_2weeks 100 :genre "rpg"}
              :b {:name "B" :players_2weeks 500 :genre "fps"}
              :c "not-a-map"}
        out (charts/parse-entries data)]
    (is (= 2 (count out)))
    (is (= "B" (:name (first out))))               ;; sorted desc by players_2weeks
    (is (= 500 (:players_2weeks (first out))))))

(deftest entries->datoms-port
  (let [ds (charts/entries->datoms
            [{:appid "1" :name "A" :players_2weeks 5 :positive 1 :negative 0 :genre "rpg"}]
            "2026-06-27")]
    (is (seq ds))
    (is (every? #(= :db/add (first %)) ds))
    (is (some #(= :media_gamers.chart/players-2weeks (nth % 2)) ds))))

(deftest ingest-persist-node-counts
  (is (= 0 (:snapshot-count (charts/node-persist {:entries []}))))
  (let [r (charts/node-persist {:entries [{:appid "1" :name "A" :players_2weeks 5
                                           :positive 0 :negative 0 :genre "x"}]
                                :week-start "2026-06-27"})]
    (is (= 1 (:snapshot-count r)))
    (is (seq (:chart-datoms r)))))
