;; etzhayyim.vitals — per-actor "life activity" vitals over the kotoba Datom log.
;;
;; The roster question is not "how mature is the codebase" (evaluate_maturity.py,
;; now stale — it assumes the dead *-compat / src/main.py / *.kotoba layout) but
;; "is each actor ALIVE as an organism cell". An actor metabolizes on three axes:
;;
;;   clj      内部代謝 / autopoiesis  — does its own code run (cljc ported off
;;                                       Python, run_tests.sh green) — the cell's
;;                                       interior metabolism.
;;   actor    細胞間シグナリング / symbiosis — does it signal other cells
;;                                       (manifest :integrates edges, Pregel cells)
;;                                       — its place in the multicellular body.
;;   atproto  外界代謝 / social metabolism — does it exchange with the outside
;;                                       world (app.bsky.feed.post projection,
;;                                       fresh out/ artifacts) — in-vivo vs in-vitro.
;;
;; This walks every manifest-bearing actor, optionally RUNS its suite (real green
;; reflex, not a static guess), scores the three axes, classifies 生/休眠/死, and
;; TRANSACTS the vitals as Datoms into the kotoba engine (content-addressed,
;; as-of history — re-run shows the organism's trajectory over time).
;;
;; CLI:  bb vitals:report                 ; full run, suites executed
;;       bb vitals:report --no-tests       ; static signs only (fast)
;;       bb vitals:report --limit 5        ; first N actors (smoke)
;;       bb vitals:report --actors tsumugi,shionome,keizu
;;       bb vitals:report --timeout-ms 90000

(ns etzhayyim.vitals
  (:require [clojure.string :as str]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [babashka.process :as p]
            [cheshire.core :as json]
            [etzhayyim.kotoba.engine :as kt]))

(def ^:private actors-root "20-actors")
(def ^:private journal "80-data/vitals/journal.edn")
(def ^:private bsky-re #"app\.bsky\.feed\.post|feed-post|feed_post")

;; ── discovery ───────────────────────────────────────────────────────────────

(defn actor-dirs
  "Every actor dir under 20-actors that carries a manifest — the named organism cells (Tier-B
   religious-corp actors), not the mass-scaffold mirrors. Recognizes BOTH the legacy
   manifest.jsonld AND the Gen-3 kotoba-native manifest.edn (the jsonld→edn migration the
   tier-b-actors generator already follows); without this, edn-native actors read as 0 cells."
  []
  (->> (.listFiles (io/file actors-root))
       (filter #(.isDirectory ^java.io.File %))
       (filter #(or (.exists (io/file % "manifest.jsonld"))
                    (.exists (io/file % "manifest.edn"))))
       (sort-by #(.getName ^java.io.File %))
       vec))

(defn- files-in
  "Regular files directly under `dir` whose name matches `re` (dir may be absent)."
  [dir re]
  (let [d (io/file dir)]
    (if (.isDirectory d)
      (filter #(and (.isFile ^java.io.File %) (re-find re (.getName ^java.io.File %)))
              (.listFiles d))
      [])))

(defn- subdirs [dir]
  (let [d (io/file dir)]
    (if (.isDirectory d) (filter #(.isDirectory ^java.io.File %) (.listFiles d)) [])))

(defn- edn->manifest-view
  "Translate a Gen-3 kotoba-native manifest.edn into the string-keyed view this tool reads from the
   legacy jsonld manifest (`integrates` / `tier` / `status` / `name` / `glyph` / `displayName`).

   Some jsonld-retirement-wave manifests (e.g. keizu, shionome, toritsugi — the
   :actor/manifest-nested set) keep the VERBATIM legacy jsonld map nested under
   :actor/manifest instead of promoting its fields to the top level. Reading only the
   top-level :actor/integrates silently read these actors' real, already-authored
   `integrates`/`status`/etc as absent (0 out-degree, status \"unknown\") even though the
   data exists one level down — fall back to the nested legacy map for each field."
  [e]
  (let [tier   (:actor/tier e)
        legacy (:actor/manifest e)]
    {"integrates"  (vec (or (:actor/integrates e) (get legacy "integrates")))
     "tier"        (cond (= tier :tier-b) "Tier-B" (keyword? tier) (name tier) :else (or tier "unknown"))
     "status"      (or (:actor/status e) (get legacy "status") "unknown")
     "name"        (or (:actor/id e) (get legacy "name"))
     "glyph"       (or (:actor/glyph e) (get legacy "glyph"))
     "displayName" (or (:actor/display-name e) (get legacy "displayName"))}))

(defn- read-manifest [actor-dir]
  (let [jf (io/file actor-dir "manifest.jsonld")
        ef (io/file actor-dir "manifest.edn")]
    (cond
      (.exists jf) (try (json/parse-string (slurp jf)) (catch Exception _ {}))
      (.exists ef) (try (edn->manifest-view (edn/read-string (slurp ef))) (catch Exception _ {}))
      :else {})))

;; ── axis signals ────────────────────────────────────────────────────────────

(defn- clj-signs
  "内部代謝: cljc-vs-Python port ratio in methods/, and the cells substrate.
   Counts BOTH `.cljc` and plain `.clj` as ported (a `.clj` file is fully
   Clojure, not Python — the port-ratio denominator only cares about
   language, not cross-platform reader-conditional shape). Before this fix
   an actor whose methods/ held only `.clj` files scored port-ratio=0.0,
   the same as an actor with zero Clojure code at all (confirmed on
   madomori/soma/kudamori/kuramori, 2026-07-14 vitals audit)."
  [actor-dir]
  (let [methods (io/file actor-dir "methods")
        prod    (fn [re] (remove #(str/starts-with? (.getName ^java.io.File %) "test_")
                                 (files-in methods re)))
        cljc    (count (prod #"\.cljc?$"))
        py      (count (prod #"\.py$"))
        cells   (subdirs (io/file actor-dir "cells"))
        cell-cljc (count (filter #(seq (files-in % #"\.cljc?$")) cells))]
    {:clj/methods-cljc cljc
     :clj/methods-py   py
     :clj/port-ratio   (if (pos? (+ cljc py)) (double (/ cljc (+ cljc py))) 0.0)
     :clj/cells        (count cells)
     :clj/cells-cljc   cell-cljc}))

(defn integrates-of
  "Normalized out-edge target names (strips the `actor:` prefix)."
  [manifest]
  (let [v (get manifest "integrates")
        v (cond (sequential? v) v (string? v) [v] :else [])]
    (mapv #(str/replace (str %) #"^actor:" "") v)))

(defn in-degree-map
  "Body-wide in-degree: how many cells signal INTO each cell (細胞が体にどれだけ
   必要とされているか). One global pass over every manifest's :integrates."
  [actor-dirs]
  (->> actor-dirs
       (mapcat #(integrates-of (read-manifest %)))
       frequencies))

(defn- actor-signs
  "細胞間シグナリング: out-degree (:integrates) + in-degree (被参照) + Pregel cells."
  [manifest actor-dir indeg]
  (let [out (integrates-of manifest)]
    {:actor/integrates (count out)
     :actor/integrate-names (vec out)
     :actor/in-degree (get indeg (.getName ^java.io.File actor-dir) 0)
     :actor/cells (count (subdirs (io/file actor-dir "cells")))}))

(defn- bio-signs
  "心拍 / heartbeat: days since the cell last metabolized (newest mtime across
   methods/ data/ out/) — a stale cell may be green yet not actually living."
  [actor-dir]
  (let [newest (->> ["methods" "data" "out"]
                    (map #(io/file actor-dir %))
                    (filter #(.isDirectory ^java.io.File %))
                    (mapcat file-seq)
                    (filter #(.isFile ^java.io.File %))
                    (map #(.lastModified ^java.io.File %))
                    (reduce max 0))]
    {:bio/heartbeat-mtime newest
     :bio/heartbeat-days (if (pos? newest)
                           (quot (- (System/currentTimeMillis) newest) 86400000)
                           9999)}))

(defn- atproto-signs
  "外界代謝: does it project app.bsky.feed.post, and has it recently excreted?"
  [actor-dir]
  (let [methods (io/file actor-dir "methods")
        bsky?   (boolean (some #(re-find bsky-re (slurp %))
                               (files-in methods #"\.(cljc|clj|py)$")))
        social? (.exists (io/file methods "social.cljc"))
        out     (io/file actor-dir "out")
        out-mtime (when (.isDirectory out)
                    (->> (file-seq out) (filter #(.isFile ^java.io.File %))
                         (map #(.lastModified ^java.io.File %))
                         (reduce max 0)))]
    {:atproto/bsky-post bsky?
     :atproto/social-method social?
     :atproto/out-mtime (or out-mtime 0)}))

;; ── vital reflex: actually run the suite ─────────────────────────────────────

(defn- nbb-cmd
  "Bare `nbb` is not on PATH in every environment (repo-local npm install
   only) — resolve node_modules/.bin/nbb relative to the repo root first,
   falling back to `npx nbb` (which works off the npx cache even without a
   PATH entry; confirmed 2026-07-14: `nbb` bare fails, `npx --no-install
   nbb --version` succeeds)."
  []
  (let [local (io/file "node_modules" ".bin" "nbb")]
    (if (.exists local) [(.getPath local)] ["npx" "nbb"])))

(defn- run-suite
  "Execute the actor's reflex test with a wall-clock budget. PREFERS the bb-native
   run_tests.clj (repo clj/bb rule, ADR-2606072802 enforce-forward), falls back to the
   legacy run_tests.sh, and also recognizes run_tests.cljs (nbb-run, e.g. akashi) — before
   this fix a `.cljs`-only runner was invisible to the scanner and scored :absent even
   though a real suite existed (2026-07-14 vitals audit). :green | :red | :absent | :timeout | :error."
  [actor-dir timeout-ms]
  (let [clj-runner  (io/file actor-dir "run_tests.clj")
        sh-runner   (io/file actor-dir "run_tests.sh")
        cljs-runner (io/file actor-dir "run_tests.cljs")
        [cmd-vec path] (cond
                         (.exists clj-runner)  [["bb"] (.getPath clj-runner)]
                         (.exists sh-runner)   [["bash"] (.getPath sh-runner)]
                         (.exists cljs-runner) [(nbb-cmd) (.getPath cljs-runner)]
                         :else nil)
        cmd (when cmd-vec (into cmd-vec [path]))]
    (if-not path
      {:reflex :absent}
      (let [proc (apply p/process {:dir "." :out :string :err :string} cmd)
            res  (deref (future @proc) timeout-ms ::timeout)]
        (if (= res ::timeout)
          (do (try (p/destroy-tree proc) (catch Exception _ nil)) {:reflex :timeout})
          (try {:reflex (if (zero? (:exit res)) :green :red) :exit (:exit res)}
               (catch Exception e {:reflex :error :msg (.getMessage e)})))))))

(def ^:private reflex-timeout-overrides
  "Per-cell reflex budget overrides (ms) for suites that legitimately exceed the default 60s.
   EMPIRICAL NOTE (#5, UPDATED 2026-07-17): the run_tests.sh this note originally described
   (18 LIVE-I/O suites, live-network flakiness) no longer exists — ibuki's sole runner is now
   run_tests.clj. Its real bottleneck was algorithmic, not I/O: satiated-producers/heartbeat-
   replay each re-scanned + re-folded the WHOLE log per entity per beat (O(entities*datoms)
   per call inside a per-beat loop, compounding to O(n^3) across n beats) — fixed via
   datoms/fold-entities (single O(datoms) pass). Measured solo: >480s (unfixed, exceeded even
   that budget) -> ~53-55s (fixed, 278 tests/1129 assertions, 0 failures). That's inside the
   60s default but with little margin under the resident daemon's concurrent sweep load — a
   modest override, not a 'losing battle' bump against flaky I/O like the old note described.
   noroshi's run_tests.sh is CPU-bound and deterministic (no I/O), unlike ibuki once was, so a fixed
   bump reliably works here. Measured 248.5s wall-clock end-to-end (2026-07-16), dominated by
   isac_sim.cljc's periodogram (O(n_sub^2*n_sym^2) DSP, byte-identical-to-Python by design,
   ~2.7s/call at production 64x16 grid) invoked ~80x across test-isac-sim (85s),
   test-kami-isac-bridge (154s), and test-governance (54s, calls isac-sim/report +
   kami-isac-bridge/report). 400s gives ~1.6x headroom over measured.
   kanjo's methods/test_pipeline_cid.clj runs the whole offline financial-disclosure pipeline
   over the EDGAR-merged graph (146,949 datoms/cycle — deliberately 'the heaviest determinism
   stress' per ADR-2606152000) 5 times per suite run. Fully deterministic/offline (no network)
   — unlike ibuki this is a reliable win from a bump, not flaky variance. Measured STILL
   :timeout at a 600s budget (523s of continuous ~87% CPU-busy work, not a hang) even after
   fixing a 3x redundant log re-parse in kotoba.cljc's head-cid/verify-chain (see
   head-cid-of-txs/verify-chain-of-txs); a single cycle alone took ~131s under concurrent
   sweep load. 1500000 (25min) gives real margin; re-tune down once measured post-fix."
  {"noroshi" 400000
   "kanjo" 1500000
   "ibuki" 120000})

;; ── scoring & classification ─────────────────────────────────────────────────

(defn- score
  "Vitality 0-100 across the three axes (clj 40 / actor 30 / atproto 30).
   clj    = port-ratio(15) + reflex(green 20/red 5) + heartbeat-fresh(5, ≤30d)
   actor  = out-degree(10) + in-degree(10) + cells(10)
   atproto= bsky(20) + social-method(5) + recent-out(5)"
  [v]
  (let [clj (+ (* 15 (:clj/port-ratio v))
               ;; :timeout = inconclusive (suite too slow to finish in budget), NOT a
               ;; confirmed failure — so it must never score BELOW :red. (co-scientist #5)
               (case (:reflex v) :green 20 :red 5 :timeout 5 0)
               (if (<= (:bio/heartbeat-days v) 30) 5 0))
        act (+ (* 10 (min 1.0 (/ (:actor/integrates v) 5.0)))
               (* 10 (min 1.0 (/ (:actor/in-degree v) 5.0)))
               (* 10 (min 1.0 (/ (:actor/cells v) 5.0))))
        atp (+ (if (:atproto/bsky-post v) 20 0)
               (if (:atproto/social-method v) 5 0)
               (if (pos? (:atproto/out-mtime v)) 5 0))]
    {:score/clj (Math/round (double clj))
     :score/actor (Math/round (double act))
     :score/atproto (Math/round (double atp))
     :score (Math/round (double (+ clj act atp)))}))

(defn- classify
  "生 in-vivo: runs green, signals peers, AND metabolizes outward (bsky).
   休眠 in-vitro: has interior metabolism but no outward exchange (R0-design-only).
   死 stub: no running code and no port."
  [v]
  (cond
    (and (= :green (:reflex v)) (pos? (:actor/integrates v)) (:atproto/bsky-post v)) :alive
    (or (= :green (:reflex v)) (pos? (:clj/port-ratio v)))                           :dormant
    :else                                                                            :stub))

(def ^:private class-glyph {:alive "生" :dormant "休眠" :stub "死"})

(defn vitals-for [actor-dir indeg run-tests? timeout-ms]
  (let [name     (.getName ^java.io.File actor-dir)
        manifest (read-manifest actor-dir)
        base     (merge {:actor name
                         :status (or (get manifest "status") "unknown")
                         :tier   (or (get manifest "tier") "unknown")}
                        (clj-signs actor-dir)
                        (actor-signs manifest actor-dir indeg)
                        (bio-signs actor-dir)
                        (atproto-signs actor-dir)
                        (if run-tests?
                          (run-suite actor-dir (max timeout-ms (get reflex-timeout-overrides name 0)))
                          {:reflex :skipped}))
        scored   (merge base (score base))]
    (assoc scored :class (classify scored))))

;; ── persistence: transact vitals into the kotoba Datom log ───────────────────

(defn- ->entity [run v]
  {:db/id (str "vitals/" run "/" (:actor v))
   :vitals/run             run
   :vitals.actor/name      (:actor v)
   :vitals.actor/status    (:status v)
   :vitals.clj/port-ratio  (:clj/port-ratio v)
   :vitals.clj/methods-cljc (:clj/methods-cljc v)
   :vitals.clj/methods-py  (:clj/methods-py v)
   :vitals.clj/reflex      (clojure.core/name (:reflex v))
   :vitals.actor/integrates (:actor/integrates v)
   :vitals.actor/integrate-name (vec (:actor/integrate-names v))  ;; edges IN the log (card-many)
   :vitals.actor/in-degree (:actor/in-degree v)
   :vitals.actor/cells     (:actor/cells v)
   :vitals.bio/heartbeat-days (:bio/heartbeat-days v)
   :vitals.atproto/bsky-post (:atproto/bsky-post v)
   :vitals.atproto/out-mtime (:atproto/out-mtime v)
   :vitals.score/clj       (:score/clj v)
   :vitals.score/actor     (:score/actor v)
   :vitals.score/atproto   (:score/atproto v)
   :vitals/score           (:score v)
   :vitals/class           (clojure.core/name (:class v))})

(defn persist!
  "Transact one observation per actor, keyed by `run`, into the kotoba engine;
   returns the head CID. Append-only — every run leaves a distinct as-of cohort
   so the organism's evolution (生命進化) is queryable across runs."
  [run vitals]
  (let [conn (kt/connect {:journal journal})]
    ;; ONE batched transact for the whole cohort (transact takes a seq of entity maps).
    ;; Was a per-actor doseq: each of the ~104 transacts re-hashed the ENTIRE growing log
    ;; for its head-cid (~545ms each ⇒ ~56s/sweep, worsening every run). One tx = one append
    ;; + one head recompute. Same datoms (db/id is unique per run+actor). (co-scientist #3)
    ;; transact already computes the new head — take it from the result instead of a second
    ;; full-log re-hash (the prior (kt/head-cid conn) doubled the O(log) cost). (co-scientist regrade)
    (:head (kt/transact conn (mapv #(->entity run %) vitals)))))

;; ── report ───────────────────────────────────────────────────────────────────

(defn report->md [vitals head]
  (let [by-class (frequencies (map :class vitals))]
    (str "# etzhayyim — actor vitals (per-cell life activity)\n\n"
         (format "**%d cells** — 生 %d · 休眠 %d · 死 %d   ·   Datom head `%s…`\n\n"
                 (count vitals) (:alive by-class 0) (:dormant by-class 0)
                 (:stub by-class 0) (subs head 0 (min 16 (count head))))
         "| actor | class | score | clj | actor | atproto | reflex | port | →out | ←in | ♥days | bsky |\n"
         "|---|:--:|--:|--:|--:|--:|:--:|--:|--:|--:|--:|:--:|\n"
         (str/join "\n"
           (for [v (sort-by (juxt (comp - :score)) vitals)]
             (format "| %s | %s | %d | %d | %d | %d | %s | %.2f | %d | %d | %d | %s |"
                     (:actor v) (class-glyph (:class v)) (:score v)
                     (:score/clj v) (:score/actor v) (:score/atproto v)
                     (clojure.core/name (:reflex v)) (:clj/port-ratio v)
                     (:actor/integrates v) (:actor/in-degree v) (:bio/heartbeat-days v)
                     (if (:atproto/bsky-post v) "✅" "·"))))
         "\n")))

(def ^:private viz-data "60-apps/etzhayyim-project-organism/public/organism.json")
(def ^:private viz-data-mirror "50-infra/etzhayyim-did-web/public/organism/organism.json")

;; ── kotoba Datom log is the SoT for ALL organism feeds (no KV; ADR-2606172200). Each feed
;;    transacts to its journal, then materializes a content-addressed `.kotoba.edn` snapshot —
;;    THAT is the canonical artifact served (like public/kotoba/blocks); the JSON is a projection.
(def ^:private snapshot-dirs
  ["60-apps/etzhayyim-project-organism/public" "50-infra/etzhayyim-did-web/public/organism"])

(defn- snapshot-to!
  "Materialize a kotoba log's live state to a content-addressed `.kotoba.edn` under every served
   dir, and return the head CID. The kotoba-Datomic artifact, not KV."
  [conn filename]
  (doseq [d snapshot-dirs]
    (io/make-parents (str d "/" filename))
    (kt/snapshot! conn (str d "/" filename)))
  (kt/head-cid conn))

(defn export-json!
  "Emit the organism snapshot the /organism ClojureScript view renders:
   nodes (one per cell, with axis scores + class + in/out degree) + edges
   (the :integrates signalling graph) + run cohort summary. Written to the
   project public dir and mirrored into the apex worker's static tree."
  [run vitals]
  (let [names (set (map :actor vitals))
        nodes (for [v vitals]
                {:id (:actor v) :class (clojure.core/name (:class v))
                 :score (:score v) :status (:status v)
                 :clj (:score/clj v) :actor (:score/actor v) :atproto (:score/atproto v)
                 :reflex (clojure.core/name (:reflex v))
                 :port (:clj/port-ratio v) :inDeg (:actor/in-degree v)
                 :outDeg (:actor/integrates v) :cells (:actor/cells v)
                 :heartbeatDays (:bio/heartbeat-days v) :bsky (:atproto/bsky-post v)})
        edges (for [v vitals, t (:actor/integrate-names v)
                    :when (names t)] {:from (:actor v) :to t})
        fq (frequencies (map :class vitals))
        payload {:run run :generatedAt (str (java.time.Instant/ofEpochMilli run))
                 :summary {:cells (count vitals) :alive (:alive fq 0)
                           :dormant (:dormant fq 0) :stub (:stub fq 0)}
                 :nodes (vec nodes) :edges (vec edges)}
        out (json/generate-string payload {:pretty true})]
    (doseq [p [viz-data viz-data-mirror]]
      (io/make-parents p)
      (spit p out))
    payload))

;; ── pulse: the organism's live activity (息遣い・生産・呼吸) ──────────────────
;; A cheap, frequently-regenerable feed (no test runs) the /organism page polls
;; to animate cells in realtime. 生産 = git commits per actor (what it shipped),
;; 息遣い = working-tree files being edited right now, 呼吸 = Datom-log head.

(def ^:private pulse-paths
  ["60-apps/etzhayyim-project-organism/public/pulse.json"
   "50-infra/etzhayyim-did-web/public/organism/pulse.json"])

;; ── kotoba Datom log is the SoT for ALL organism feeds (no KV; substrate boundary,
;;    CLAUDE.md). Each feed transacts to its own append-only journal, then materializes a
;;    content-addressed `.kotoba.edn` snapshot — THAT is the canonical artifact served
;;    (like public/kotoba/blocks). The JSON is a derived read-model/projection of the log.
(def ^:private pulse-journal  "80-data/organism/pulse.journal.edn")
(def ^:private joucho-journal "80-data/organism/joucho.journal.edn")
(def ^:private trajectory-journal "80-data/organism/trajectory.journal.edn")  ; joucho reads it (#1)
(declare load-trajectory)

(defn- git-out [& args]
  (try (:out (apply p/sh args)) (catch Exception _ "")))

(defn pulse->datoms
  "Turn one pulse observation into kotoba datoms: a per-actor live-state entity + the recent
   commit stream as events. Append-only, content-addressed — the organism's activity on the log."
  [run d]
  (let [actors (for [[a m] (get d "actors")]
                 {:db/id (str "pulse/" run "/" a)
                  :pulse/run run :pulse.actor/name a
                  :pulse.actor/commits (get m "commits" 0)
                  :pulse.actor/dirty (get m "dirty" 0)
                  :pulse.actor/last-at (get m "lastAt" 0)
                  :pulse.actor/last-subject (or (get m "lastSubject") "")})
        stream (map-indexed
                (fn [i e] {:db/id (str "pev/" run "/" i)
                           :pulse.event/run run :pulse.event/idx i
                           :pulse.event/at (get e "at") :pulse.event/actor (or (get e "actor") "")
                           :pulse.event/subj (get e "subj")})
                (get d "stream"))]
    (vec (concat actors stream))))

(defn pulse-data
  "Per-actor live activity over the last `hours`: commit production (newest-first
   in git log → first occurrence is latest), plus working-tree dirty counts."
  [hours]
  (let [now   (System/currentTimeMillis)
        lines (str/split-lines
               (git-out "git" "log" (str "--since=" hours " hours ago")
                        "--name-only" "--pretty=format:C|%ct|%s" "--" actors-root))
        commits (loop [ls lines, cur nil, acc []]
                  (if-let [ln (first ls)]
                    (cond
                      (str/starts-with? ln "C|")
                      (let [[_ ct subj] (str/split ln #"\|" 3)]
                        (recur (rest ls) {:ct (Long/parseLong ct) :subj subj :actors #{}}
                               (if cur (conj acc cur) acc)))
                      (str/blank? ln) (recur (rest ls) cur acc)
                      :else
                      (let [m (re-find #"^20-actors/([^/]+)/" ln)]
                        (recur (rest ls) (if (and cur m) (update cur :actors conj (second m)) cur) acc)))
                    (if cur (conj acc cur) acc)))
        per (reduce (fn [m c]
                      (reduce (fn [m a]
                                (cond-> (update-in m [a "commits"] (fnil inc 0))
                                  (not (get-in m [a "lastAt"]))
                                  (-> (assoc-in [a "lastAt"] (* 1000 (:ct c)))
                                      (assoc-in [a "lastSubject"] (:subj c)))))
                              m (:actors c)))
                    {} commits)
        dirty (->> (str/split-lines (git-out "git" "status" "--porcelain" "--" actors-root))
                   (keep #(second (re-find #"20-actors/([^/]+)/" %)))
                   frequencies)
        per (reduce (fn [m [a n]] (assoc-in m [a "dirty"] n)) per dirty)
        stream (->> commits (take 20)
                    (map (fn [c] {"at" (* 1000 (:ct c)) "actor" (first (:actors c)) "subj" (:subj c)})))]
    {"generatedAt" (str (java.time.Instant/ofEpochMilli now)) "now" now
     "sinceHours" hours "actors" per "stream" (vec stream)
     "working" (vec (sort (keys dirty)))
     ;; placeholder: -pulse overwrites "head" with the pulse-journal snapshot CID. Connecting to
     ;; the large, ever-growing vitals journal here cost ~1.25s on EVERY 6s 脈 tick (connect
     ;; read-log + full-log head-cid) to produce a value that was immediately discarded.
     "head" ""}))

(defn -pulse
  "Persist the live pulse into the kotoba Datom log (SoT), snapshot it content-addressed, and
   emit pulse.json as the projection. Args: [hours]. Live state → fresh journal each run (the
   activity HISTORY lives in git + the vitals/joucho logs; pulse is current-state, bounded)."
  [& args]
  (let [hours (if (seq args) (Long/parseLong (first args)) 48)
        d (pulse-data hours)
        run (get d "now")]
    (io/delete-file pulse-journal true)                 ;; live state: bounded, not append-history
    (let [conn (kt/connect {:journal pulse-journal})]
      (kt/transact conn (pulse->datoms run d))
      (let [head (snapshot-to! conn "pulse.kotoba.edn")
            d (assoc d "head" head "store" "kotoba-datom-log" "snapshot" "pulse.kotoba.edn")
            out (json/generate-string d {:pretty true})]
        (doseq [p pulse-paths] (io/make-parents p) (spit p out))
        (binding [*out* *err*]
          (println (format "[pulse] kotoba head=%s · %d working"
                           (subs head 0 (min 16 (count head)))
                           (count (re-seq #"\"dirty\"" out)))))))))

;; ── joucho 情緒: the organism's mood + Wellbecoming trajectory (ADR-2606171500) ─
;; Replays ibuki's representative life (perception pattern + the charter-clean reciprocal
;; event) into a 5-axis mood trajectory + Wellbecoming MOVEMENT, for the /organism 情緒 layer.

(def ^:private joucho-paths
  ["60-apps/etzhayyim-project-organism/public/joucho.json"
   "50-infra/etzhayyim-did-web/public/organism/joucho.json"])

(defn- beat-events
  "The representative life at beat i — an organism that FEELS the world's reward (ADR-2606171800):
   a post each beat, reactions felt every 2nd, mail exchanged every 4th, warmth every 6th, a
   follower every 3rd, inbox-pressure every 5th, a reciprocated dialogue every 7th, idle otherwise.
   Rewards are small + bounded; the objective the loop maximizes stays the wellbecoming gradient."
  [i]
  (cond-> [":event/post-emitted"]
    (zero? (mod i 2)) (conj ":event/reaction-received")
    (zero? (mod i 3)) (conj ":event/follower-gained")
    (zero? (mod i 4)) (conj ":event/message-exchanged")
    (zero? (mod i 5)) (conj ":event/inbox-pressure")
    (zero? (mod i 6)) (conj ":event/sentiment-warmth")
    (zero? (mod i 7)) (conj ":event/dialogue-reciprocated")
    (and (pos? (mod i 2)) (pos? (mod i 3)) (pos? (mod i 5)) (pos? (mod i 7))) (conj ":event/idle")))

(defn- real-beat-events
  "The organism's ACTUAL recent life as a beat stream (#1): each beat = one trajectory run's
   delta vs the prior run. Gaining alive cells / vitality folds reward events (the body
   connecting, healing); losing them folds stress (deaths, decline). A STABLE organism emits
   only :idle and drifts to its baseline temperament — so a flat, mostly-dormant body no longer
   fabricates an ever-climbing 'improving'; a declining body actually feels it.
   `runs` = trajectory cohort maps {:alive :dormant :stub :sum}, oldest→newest."
  [runs]
  (vec
    (for [[prev cur] (map vector runs (rest runs))]
      (let [d-alive (- (:alive cur) (:alive prev))
            d-sum   (- (:sum cur) (:sum prev))
            d-stub  (- (:stub cur) (:stub prev))
            evs (cond-> []
                  (pos? d-alive) (into (repeat (min 3 d-alive) ":event/dialogue-reciprocated"))
                  (neg? d-alive) (conj ":event/inbox-pressure")
                  (pos? d-sum)   (conj ":event/kaizen-merged")     ; body got healthier
                  (neg? d-sum)   (conj ":event/kaizen-rejected")   ; body declined
                  (pos? d-stub)  (conj ":event/inbox-pressure")    ; cells died
                  (neg? d-stub)  (conj ":event/follower-gained"))] ; revived from death
        (if (seq evs) evs [":event/idle"])))))

(defn joucho-data [of n]
  (let [baseline ((requiring-resolve 'ibuki.methods.joucho/personality-baseline) of)
        fold     (requiring-resolve 'ibuki.methods.joucho/fold-event)
        mood-of  (requiring-resolve 'ibuki.methods.joucho/determine-mood)
        readout  (requiring-resolve 'ibuki.methods.wellbecoming/readout)
        vocab    @(requiring-resolve 'ibuki.methods.joucho/event-deltas)  ;; the loaded closed vocab
        known?   (fn [e] (contains? vocab e))
        ;; #1: fold the organism's REAL recent trajectory (not a synthetic (mod i k) schedule).
        ;; Fail-open to the synthetic stream if the trajectory log isn't readable / has <2 runs.
        runs     (try (vec (take-last (inc n) (load-trajectory (kt/connect {:journal trajectory-journal}))))
                      (catch Throwable _ nil))
        real-evs (when (>= (count runs) 2) (real-beat-events runs))
        n-beats  (if (seq real-evs) (count real-evs) n)
        evs-at   (fn [i] (or (when real-evs (filter known? (nth real-evs (dec i))))
                             (filter known? (beat-events i))))
        beats (loop [i 1, sc baseline, acc []]
                (if (> i n-beats) acc
                  (let [evs (or (seq (evs-at i)) [":event/idle"])
                        sc' (reduce (fn [s e] (fold s e baseline)) sc evs)]
                    (recur (inc i) sc' (conj acc (assoc sc' :beat i :mood (mood-of sc')))))))
        final (last beats)
        wb (readout of (map #(select-keys % [:joy :calm :stress :gratitude :focus]) beats))]
    {:generatedAt (str (java.time.Instant/now)) :of of
     :mood (:mood final) :baseline baseline
     :axes (select-keys final [:joy :calm :stress :gratitude :focus])
     :beats beats
     :wellbecoming {:direction (name (:direction wb)) :net (:net wb) :trajectory (:trajectory wb)}}))

(defn joucho->datoms
  "Per-beat :joucho/* mood entities + a final :wellbecoming/* MOVEMENT entity (engine-native
   maps — the organism's mood history on the kotoba log, as-of replayable, 縁起). Edge-primary:
   :wellbecoming/* carries direction + net (movement), never a per-soul score/level."
  [of d]
  (let [beats (:beats d)
        per-beat (map (fn [b]
                        {:db/id (str "joucho/" of "/" (:beat b))
                         :joucho/of of :joucho/beat (:beat b) :joucho/mood (:mood b)
                         :joucho/joy (:joy b) :joucho/calm (:calm b) :joucho/stress (:stress b)
                         :joucho/gratitude (:gratitude b) :joucho/focus (:focus b)})
                      beats)
        wb (:wellbecoming d)
        wb-ent {:db/id (str "wellbecoming/" of "/" (count beats))
                :wellbecoming/of of :wellbecoming/beats (count beats)
                :wellbecoming/direction (:direction wb) :wellbecoming/net (:net wb)}]
    (vec (conj (vec per-beat) wb-ent))))

(defn -joucho
  "Persist the 情緒 mood + Wellbecoming trajectory into the kotoba Datom log (SoT), snapshot it
   content-addressed, and emit joucho.json as the projection. Args: [of=ibuki] [beats=24]."
  [& args]
  (let [of (or (first args) "ibuki")
        n  (if (second args) (Long/parseLong (second args)) 24)
        d  (joucho-data of n)]
    (io/delete-file joucho-journal true)               ;; deterministic replay → fresh each run
    (let [conn (kt/connect {:journal joucho-journal})]
      (kt/transact conn (joucho->datoms of d))
      (let [head (snapshot-to! conn "joucho.kotoba.edn")
            d (assoc d :head head :store "kotoba-datom-log" :snapshot "joucho.kotoba.edn")
            out (json/generate-string d {:pretty true})]
        (doseq [p joucho-paths] (io/make-parents p) (spit p out))
        (binding [*out* *err*]
          (println (format "[joucho] kotoba head=%s · %s mood=%s wellbecoming=%s net=%d"
                           (subs head 0 (min 16 (count head)))
                           of (:mood d) (get-in d [:wellbecoming :direction])
                           (get-in d [:wellbecoming :net]))))))))

;; ── CLI ──────────────────────────────────────────────────────────────────────

(defn- parse-args [args]
  (loop [a args, o {:run-tests? true :timeout-ms 120000 :limit nil :only nil}]
    (if-let [x (first a)]
      (case x
        "--no-tests" (recur (rest a) (assoc o :run-tests? false))
        "--limit"    (recur (drop 2 a) (assoc o :limit (Long/parseLong (second a))))
        "--actors"   (recur (drop 2 a) (assoc o :only (set (str/split (second a) #","))))
        "--timeout-ms" (recur (drop 2 a) (assoc o :timeout-ms (Long/parseLong (second a))))
        (recur (rest a) o))
      o)))

(declare record-trajectory! export-trajectory!)   ;; trajectory section is defined below

(defn -main [& args]
  (let [{:keys [run-tests? timeout-ms limit only]} (parse-args args)
        all   (actor-dirs)
        indeg (in-degree-map all)                       ; body-wide, over all cells
        dirs (cond->> all
               only  (filter #(only (.getName ^java.io.File %)))
               limit (take limit))
        _ (binding [*out* *err*]
            (println (format "[vitals] %d cells, suites=%s, timeout=%dms"
                             (count dirs) run-tests? timeout-ms)))
        vitals (vec (for [d dirs]
                      (let [v (vitals-for d indeg run-tests? timeout-ms)]
                        (binding [*out* *err*]
                          (println (format "  %-14s %-6s score=%d reflex=%s"
                                           (:actor v) (class-glyph (:class v))
                                           (:score v) (clojure.core/name (:reflex v)))))
                        v)))
        run    (System/currentTimeMillis)
        head   (persist! run vitals)]
    (export-json! run vitals)
    ;; content-addressed snapshot of THIS run's cells only (no KV; D2 of ADR-2606172200).
    ;; The full as-of history stays in the journal (canonical) + trajectory.kotoba.edn
    ;; (evolution); the page only needs current cells. A full-journal snapshot had grown to
    ;; ~9MB and was parsed on the browser main thread every load — snapshot just the run
    ;; (~2k datoms ≈ <100KB) via a throwaway conn. (co-scientist viz: boot-parse)
    (let [snap-journal (str journal ".latest")]
      (io/delete-file snap-journal true)
      (let [tmp (kt/connect {:journal snap-journal})]
        (kt/transact tmp (mapv #(->entity run %) vitals))
        (snapshot-to! tmp "vitals.kotoba.edn"))
      (io/delete-file snap-journal true))
    ;; evolution: append this run's cohort summary + materialize trajectory.kotoba.edn (+ .json)
    (record-trajectory! run vitals)
    (export-trajectory!)
    (println (report->md vitals head))))

;; ── trajectory: the organism's evolution across runs (生命進化) ──────────────
;; A DEDICATED, summary-grain Datom log — ONE cohort datom per vitals run — so the
;; cross-run evolution is its own content-addressed `.kotoba.edn` snapshot, exactly
;; like pulse/joucho/narration/vitals. Deriving the series from the full vitals
;; journal (per-actor × per-run join) is O(runs×cells) and timed out once the log
;; grew past a few dozen runs; the right grain for a cross-run series is one datom
;; per run, which stays instant. Still kotoba Datom log, no KV (ADR-2606172200).
;; trajectory-journal is defined up with the other journal paths (joucho reads it for #1)

(defn- iso [ms] (str (java.time.Instant/ofEpochMilli ms)))

(defn- ->traj-entity
  "One cohort-summary datom for a finished vitals run. Keyed :db/id ⇒ idempotent."
  [run vitals]
  (let [fq (frequencies (map :class vitals))]
    {:db/id        (str "traj/" run)
     :traj/run     run
     :traj/at      (iso run)
     :traj/cells   (count vitals)
     :traj/alive   (get fq :alive 0)
     :traj/dormant (get fq :dormant 0)
     :traj/stub    (get fq :stub 0)
     :traj/sum     (reduce + (map :score vitals))}))

(defn record-trajectory!
  "Append this run's cohort summary to the trajectory journal; returns the head CID."
  [run vitals]
  (let [conn (kt/connect {:journal trajectory-journal})]
    (kt/transact conn [(->traj-entity run vitals)])
    (kt/head-cid conn)))

(defn load-trajectory
  "Every recorded run summary, sorted by run — instant (summary-grain journal)."
  [conn]
  (->> (kt/q conn '{:find [?run ?at ?cells ?alive ?dormant ?stub ?sum]
                    :where [[?e :traj/run ?run] [?e :traj/at ?at]
                            [?e :traj/cells ?cells] [?e :traj/alive ?alive]
                            [?e :traj/dormant ?dormant] [?e :traj/stub ?stub]
                            [?e :traj/sum ?sum]]})
       (map (fn [[run at cells alive dormant stub sum]]
              {:run run :at at :cells cells :alive alive
               :dormant dormant :stub stub :sum sum}))
       (sort-by :run)
       vec))

(defn export-trajectory!
  "Materialize the trajectory journal to a content-addressed `trajectory.kotoba.edn`
   under every served dir, and project `trajectory.json` from it. Returns {:head :runs}."
  []
  (let [conn (kt/connect {:journal trajectory-journal})
        head (snapshot-to! conn "trajectory.kotoba.edn")
        runs (load-trajectory conn)
        out  (json/generate-string {:runs runs :head head :store "kotoba-datom-log"
                                    :snapshot "trajectory.kotoba.edn"} {:pretty true})]
    (doseq [p ["60-apps/etzhayyim-project-organism/public/trajectory.json"
               "50-infra/etzhayyim-did-web/public/organism/trajectory.json"]]
      (io/make-parents p)
      (spit p out))
    {:head head :runs (count runs)}))

(defn- trajectory->md [runs]
  (let [rows (map-indexed
               (fn [i r]
                 (let [d (when (pos? i) (- (:sum r) (:sum (nth runs (dec i)))))]
                   (format "| %d | %s | %d | %d | %d | %d | %d | %s |"
                           (:run r) (:at r) (:cells r) (:alive r)
                           (:dormant r) (:stub r) (:sum r)
                           (if d (format "%+d" d) "—"))))
               runs)]
    (str "# etzhayyim — organism evolution (生命進化)\n\n"
         (format "**%d runs** recorded · trajectory.kotoba.edn\n\n" (count runs))
         "| run | at | cells | 生 | 休眠 | 死 | Σscore | Δ |\n"
         "|--:|---|--:|--:|--:|--:|--:|--:|\n"
         (str/join "\n" rows) "\n")))

(defn -trajectory [& _]
  (let [{:keys [head runs]} (export-trajectory!)
        conn (kt/connect {:journal trajectory-journal})]
    (binding [*out* *err*]
      (println (format "[trajectory] %d runs · head %s…" runs (subs head 0 (min 16 (count head))))))
    (println (trajectory->md (load-trajectory conn)))))
